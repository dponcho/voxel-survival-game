extends RefCounted

const Frontier = preload("res://scripts/benchmark_frontier.gd")
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")

# Runs only in the existing cloud smoke route, after the shared writer drains.
static func verify(directory: String, phases: Array[Dictionary], reports: Array[Dictionary]) -> Array[String]:
	var failures: Array[String] = []
	var expected: Dictionary = {}
	var files: Dictionary = {}
	for phase: Dictionary in phases:
		var id: int = int(phase["id"])
		expected[id] = {"frames": 0, "upload_count": 0, "upload_bytes": 0, "upload_usec": 0, "upload_max_usec": 0,
			"deletion_count": 0, "deletion_bytes": 0, "deletion_usec": 0, "deletion_max_usec": 0}
		if phase["tracing"]: files[str(phase["raw_operations"])] = true
		for kind: String in ["upload", "deletion"]:
			if int(phase[kind]["usec"]) != int(phase["native_end"][kind + "_usec"]) - int(phase["native_start"][kind + "_usec"]):
				failures.append("Phase totals disagree with additive lifetime counters")
			if int(phase[kind]["max_usec"]) > int(phase["native_end"][kind + "_max_usec"]):
				failures.append("Phase maximum exceeds lifetime maximum")
	for name: String in files:
		var file := FileAccess.open(directory.path_join(name), FileAccess.READ)
		if file == null:
			failures.append("Missing operation CSV: " + name)
			continue
		var header: PackedStringArray = file.get_csv_line()
		var previous_frame: int = -1
		var previous_end: int = -1
		while not file.eof_reached():
			var fields: PackedStringArray = file.get_csv_line()
			if fields.size() == 1 and fields[0].is_empty(): continue
			if fields.size() != 18 or header.size() != 18:
				failures.append("Malformed operation CSV row")
				break
			var row: Dictionary = {}
			for i: int in range(header.size()): row[header[i]] = int(fields[i])
			if not expected.has(row["phase"]):
				failures.append("Unknown operation phase")
				break
			if int(row["native_frame"]) < previous_frame or int(row["start_usec"]) < previous_end or int(row["end_usec"]) < int(row["start_usec"]):
				failures.append("Operation intervals reordered or overlapping")
			previous_frame = int(row["native_frame"])
			previous_end = int(row["end_usec"])
			var total: Dictionary = expected[row["phase"]]
			total["frames"] += 1
			for kind: String in ["upload", "deletion"]:
				for field: String in ["count", "bytes", "usec"]: total[kind + "_" + field] += row[kind + "_" + field]
				total[kind + "_max_usec"] = maxi(int(total[kind + "_max_usec"]), int(row[kind + "_max_usec"]))
				if int(row[kind + "_count"]) > 0:
					var start: int = int(row[kind + "_max_start_usec"])
					if start < int(row["start_usec"]) or start + int(row[kind + "_max_usec"]) > int(row["end_usec"]):
						failures.append("Slowest operation lies outside its frame segment")
		file.close()
	for phase: Dictionary in phases:
		var total: Dictionary = expected[int(phase["id"])]
		if not phase["tracing"]:
			if int(total["frames"]) != 0: failures.append("A/B baseline unexpectedly emitted operation frames")
			continue
		if int(phase["dropped_frames"]) != 0 or int(total["frames"]) != int(phase["frames"]): failures.append("Operation frame evidence is incomplete")
		for kind: String in ["upload", "deletion"]:
			for field: String in ["count", "bytes", "usec", "max_usec"]:
				if int(total[kind + "_" + field]) != int(phase[kind][field]): failures.append("CSV and phase " + kind + " " + field + " disagree")
	for report: Dictionary in reports:
		failures.append_array(_verify_diagnostics(directory, report))
		failures.append_array(_verify_edit_visibility(directory, report))
		failures.append_array(_verify_frontier(directory, report))
		if not report["completed"] or report["qualified"]: failures.append("Scenario completion and qualification were conflated")
		var phase: Dictionary = report["operation_phase"]
		for kind: String in ["upload", "deletion"]:
			var reason: String = "Individual " + kind + " exceeded 0.75 ms"
			if (int(phase[kind]["max_usec"]) > 750) != (reason in report["reasons"]): failures.append("Scenario used an incorrect operation maximum")
	return failures

static func _verify_frontier(directory: String, report: Dictionary) -> Array[String]:
	var failures: Array[String] = []
	var active: bool = report["id"] == "H1" or report["id"] == "H2"
	if active:
		var fog: Dictionary = report["fog_frontier"]["fog"]
		if fog != {"enabled": true, "mode": "depth", "density": 1.0, "height_density": 0.0, "begin_m": 16.0, "end_m": 96.0, "curve": 1.0}:
			failures.append("Saved heavy scenario did not use the finite 96 m M1 fog profile")
	var file := FileAccess.open(directory.path_join(str(report["id"]) + "-frames.csv"), FileAccess.READ)
	if file == null: return ["Missing frontier frame CSV"]
	var header: PackedStringArray = file.get_csv_line()
	if header.size() != 38: return ["Missing frontier CSV columns"]
	for i: int in range(Frontier.COLUMNS.size()):
		if header[20 + i] != Frontier.COLUMNS[i]: failures.append("Incorrect frontier column mapping")
	var ledger := Frontier.new()
	if active: ledger.configure_renderer_model(report["fog_frontier"]["renderer_model"]["context"])
	while not file.eof_reached():
		var fields: PackedStringArray = file.get_csv_line()
		if fields.size() == 1 and fields[0].is_empty(): continue
		if fields.size() != 38:
			failures.append("Malformed frontier CSV row")
			break
		if not active:
			for i: int in range(20, 38):
				if fields[i] != "not_run": failures.append("Frontier probes ran outside H1/H2")
			continue
		var sample: Dictionary = {"status": fields[20]}
		if fields[20] == "measured":
			var keys: Array[String] = ["candidate_regions", "checked_regions", "ready_regions", "empty_regions", "unready_regions"]
			for i: int in range(5): sample[keys[i]] = int(fields[21 + i])
			sample["frontier_distance_m"] = float(fields[26])
			sample["frontier_kind"] = fields[27]
			var unready: bool = int(sample["unready_regions"]) > 0
			if unready and (fields[28].split(";").size() != 3 or not fields[29] in ["missing", "pending", "hidden"]): failures.append("Missing frontier region identity")
			if sample["frontier_kind"] != ("unready_region_lower_bound" if unready else "far_clip_lower_bound"): failures.append("Incorrect frontier distance scope")
		var evaluated: Dictionary = ledger.record(sample, report["fog_frontier"]["fog"])
		for i: int in range(3):
			var key: String = ["fog_boundary_m", "fog_clearance_m", "fog_transmittance"][i]
			if evaluated[key] == null:
				if fields[30 + i] != "unavailable": failures.append("Unavailable fog metric became a numeric sample")
			elif not fields[30 + i].is_valid_float() or absf(float(fields[30 + i]) - float(evaluated[key])) > 0.0001:
				failures.append("Fog equation and CSV disagree")
	file.close()
	var expected: Dictionary = ledger.snapshot(active)
	var actual: Dictionary = report["fog_frontier"]
	for key: String in ["evaluation", "samples"]:
		if expected[key] != actual[key]: failures.append("Frontier summary and CSV disagree: " + key)
	var expected_model: Dictionary = expected["renderer_model"]
	var actual_model: Dictionary = actual["renderer_model"]
	for key: String in ["evaluation", "samples", "qualified"]:
		if expected_model[key] != actual_model[key]: failures.append("Shader model summary and CSV disagree: " + key)
	if active:
		for key: String in ["model", "measured_samples", "exposed_samples", "inconclusive_samples", "pixel_visibility"]:
			if expected_model[key] != actual_model[key]: failures.append("Shader model counts or scope disagree: " + key)
		for key: String in ["status", "evaluation", "packed_alpha_bits", "packed_opacity", "packed_transmittance"]:
			if expected_model["worst_sample"].get(key) != actual_model["worst_sample"].get(key): failures.append("Shader model worst sample and CSV disagree: " + key)
		if actual_model["context"].get("display") == "headless" and (actual_model["evaluation"] != "inconclusive" or actual_model["measured_samples"] != 0):
			failures.append("Headless scenario claimed supported shader evidence")
		if int(expected["samples"]) != int(report["samples"]): failures.append("Frontier trace omitted measured frames")
		for key: String in ["measured_samples", "invalid_samples", "exposed_samples", "inconclusive_samples"]:
			if expected[key] != actual[key]: failures.append("Frontier counts and CSV disagree: " + key)
		for key: String in ["minimum_frontier_distance_m", "minimum_fog_clearance_m"]:
			if expected[key] == null or actual[key] == null:
				if expected[key] != actual[key]: failures.append("Missing frontier minimum became zero")
			elif absf(float(expected[key]) - float(actual[key])) > 0.0001: failures.append("Frontier minimum and CSV disagree")
		var reason: String = "Required mesh coverage is unready before fog obscures it"
		if (actual["evaluation"] == "failed") != (reason in report["reasons"]): failures.append("Scenario ignored exposed mesh coverage")
		if actual["evaluation"] == "failed" and report["evaluation"] != "failed": failures.append("Fog crossing did not fail the scenario")
	return failures

static func _verify_edit_visibility(directory: String, report: Dictionary) -> Array[String]:
	var failures: Array[String] = []
	var id: String = report["id"]
	if id != "N2" and id != "H2": return failures
	var metrics: Dictionary = report["edit_visibility"]
	var file := FileAccess.open(directory.path_join(report["edit_visibility_events"]), FileAccess.READ)
	if file == null: return ["Missing edit visibility event file"]
	var counts: Dictionary = {"submitted": 0, "superseded": 0, "cancelled": 0, "timeout": 0, "unavailable": 0}
	var latencies: Array[int] = []
	var seen_ids: Dictionary = {}
	while not file.eof_reached():
		var line: String = file.get_line()
		if line.is_empty(): continue
		var parsed: Variant = JSON.parse_string(line)
		if not parsed is Dictionary:
			failures.append("Malformed edit visibility event")
			break
		var event: Dictionary = parsed
		if int(event["accepted_usec"]) < int(report["diagnostic_accounting"]["start_usec"]) or int(event["end_usec"]) > int(report["measurement_end_usec"]):
			failures.append("Accepted edit settled outside the measured gameplay phase")
		var outcome: String = str(event.get("outcome", ""))
		if not counts.has(outcome):
			failures.append("Unknown edit visibility outcome")
			break
		counts[outcome] += 1
		if int(event["id"]) <= 0 or seen_ids.has(int(event["id"])): failures.append("Duplicate or invalid edit visibility ID")
		seen_ids[int(event["id"])] = true
		if int(event["end_usec"]) < int(event["accepted_usec"]) or int(event["latency_usec"]) != int(event["end_usec"]) - int(event["accepted_usec"]):
			failures.append("Edit visibility latency clock disagrees")
		var targets: Array = event["targets"]
		if targets.size() > 8: failures.append("Edit visibility target bound exceeded")
		if outcome == "submitted":
			if targets.is_empty(): failures.append("Submitted edit has no mesh targets")
			for target: Dictionary in targets:
				if not target["submitted"] or int(target["revision"]) <= 0: failures.append("Submitted edit has unconfirmed mesh revision")
			latencies.append(int(event["latency_usec"]))
	file.close()
	var total: int = 0
	for outcome: String in counts:
		total += int(counts[outcome])
		if int(counts[outcome]) != int(metrics[outcome]): failures.append("Edit visibility summary and events disagree")
	if total != int(report["accepted_proxy_edits"]) or int(metrics["accepted"]) != total or int(metrics["pending"]) != 0 or int(metrics["queued"]) != 0 or int(metrics["overflow"]) != 0:
		failures.append("Edit visibility evidence is incomplete")
	if not latencies.is_empty():
		latencies.sort()
		var p95_index: int = int(ceil(float(latencies.size()) * 0.95)) - 1
		var upper: int = latencies.back() if latencies[p95_index] >= 1000000 else (latencies[p95_index] / 1000 + 1) * 1000
		if upper != int(metrics["p95_upper_usec"]) or latencies.back() != int(metrics["max_usec"]):
			failures.append("Edit visibility percentile or maximum disagrees")
	return failures

static func _verify_diagnostics(directory: String, report: Dictionary) -> Array[String]:
	var failures: Array[String] = []
	var accounting: Dictionary = report["diagnostic_accounting"]
	var samples: int = int(report["samples"])
	if int(accounting["callbacks"]) != samples or int(accounting["end_usec"]) - int(accounting["start_usec"]) != int(accounting["elapsed_usec"]):
		failures.append("Diagnostic callback/window accounting disagrees")
	if int(accounting["writer_drain_usec"]) > int(accounting["finalization_usec"]) or int(accounting["finalization_usec"]) < 0 or int(accounting["callback_usec"]) > int(accounting["elapsed_usec"]):
		failures.append("Diagnostic finalization/drain lies outside its window")
	var block_samples: int = int(accounting["partial_block"]["samples"])
	var block_usec: int = int(accounting["partial_block"]["usec"])
	for block: Dictionary in accounting["blocks"]:
		block_samples += int(block["samples"])
		block_usec += int(block["usec"])
	if accounting["overflow"] or block_samples != samples or absf(float(block_usec) - float(report["wall_seconds"]) * 1000000.0) > 1.0:
		failures.append("Timing blocks lost intervals")
	var id: String = report["id"]
	if id.begins_with("AB-"):
		var histogram_samples: int = 0
		for bin: Array in report["interval_histogram_10usec"]: histogram_samples += int(bin[1])
		if histogram_samples != samples: failures.append("A/B histogram lost samples")
	var file := FileAccess.open(directory.path_join(id + "-frames.csv"), FileAccess.READ)
	if file == null: return ["Missing frame CSV"]
	var header: PackedStringArray = file.get_csv_line()
	var rows: int = 0
	var callback_sum: int = int(accounting["last_callback_usec"])
	var previous_stamp: int = 0
	var acknowledgement: Dictionary = report["edit_acknowledgement"]
	var acknowledgement_rows: int = 0
	var invalid_gpu_rows: int = 0
	var valid_gpu_peak: float = 0.0
	while not file.eof_reached():
		var fields: PackedStringArray = file.get_csv_line()
		if fields.size() == 1 and fields[0].is_empty(): continue
		if fields.size() != 38 or header.size() != 38:
			failures.append("Malformed frame CSV")
			break
		rows += 1
		if int(fields[0]) != rows or int(fields[19]) != rows - 1: failures.append("Diagnostic callback CSV is shifted incorrectly")
		callback_sum += int(fields[18])
		var stamp: int = int(fields[15])
		if stamp > int(report["measurement_end_usec"]): failures.append("Measured frame lies after gameplay closure")
		if int(acknowledgement["start_usec"]) > 0 and stamp >= int(acknowledgement["start_usec"]):
			acknowledgement_rows += 1
			if absf(float(fields[2]) - float(report["simulated_seconds"])) > 0.000001 or int(fields[13]) != int(report["accepted_proxy_edits"]):
				failures.append("Acknowledgement frames changed the route clock or edit workload")
		var gpu_status: String = Evaluation.gpu_sample_status(float(fields[17]), stamp) if fields[17].is_valid_float() else "invalid"
		if gpu_status == "invalid": invalid_gpu_rows += 1
		elif gpu_status == "valid": valid_gpu_peak = maxf(valid_gpu_peak, float(fields[17]))
		if previous_stamp > 0 and absf(float(stamp - previous_stamp) - float(fields[3]) * 1000.0) > 1.0:
			failures.append("Frame interval has mismatched callback boundaries")
		previous_stamp = stamp
	file.close()
	if id.begins_with("AB-off-"):
		if rows != 0: failures.append("Baseline emitted detailed frame probes")
	elif rows != samples or callback_sum != int(accounting["callback_usec"]):
		failures.append("CSV omits callback/format/flush/UI time or final sample")
	if acknowledgement_rows != int(acknowledgement["samples"]): failures.append("Final edit acknowledgement samples disagree with CSV")
	if invalid_gpu_rows != int(report["invalid_gpu_samples"]) or absf(valid_gpu_peak - float(report["peaks"].get("render_gpu_ms", 0.0))) > 0.00001:
		failures.append("Raw GPU validity/peak and summary disagree")
	return failures
