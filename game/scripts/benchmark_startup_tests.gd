extends RefCounted

const Startup = preload("res://scripts/benchmark_startup.gd")

# Independent endpoint sweep: classify each disjoint segment instead of merging ranges.
static func _oracle(begin: int, end: int, spans: Array) -> Dictionary:
	var points: Array[int] = [begin, end]
	for span: Dictionary in spans:
		points.append(clampi(int(span["start_usec"]), begin, end))
		points.append(clampi(int(span["end_usec"]), begin, end))
	points.sort()
	var union: int = 0
	var stages: Dictionary = {"process": 0, "physics": 0, "render": 0}
	for i: int in range(1, points.size()):
		var left: int = points[i - 1]
		var right: int = points[i]
		var seen: Dictionary = {}
		for span: Dictionary in spans:
			if int(span["start_usec"]) <= left and int(span["end_usec"]) >= right and right > left:
				seen[span["kind"]] = true
		if not seen.is_empty(): union += right - left
		for kind: String in seen: stages[kind] += right - left
	return {"union": union, "stages": stages,
		"overlap": int(stages["process"]) + int(stages["physics"]) + int(stages["render"]) - union,
		"outside": end - begin - union}

static func _verify_interval(row: Dictionary) -> Array[String]:
	var failures: Array[String] = []
	var begin: int = int(row["start_usec"])
	var end: int = int(row["end_usec"])
	if end < begin or int(row["interval_usec"]) != end - begin: return ["Startup interval clock mismatch"]
	var spans: Array = row["stage_spans"]
	if spans.size() > Startup.SPAN_CAP: failures.append("Unbounded retained startup spans")
	for span: Dictionary in spans:
		if span["kind"] not in ["process", "physics", "render"] or int(span["start_usec"]) < begin or int(span["end_usec"]) > end or int(span["end_usec"]) <= int(span["start_usec"]):
			return ["Invalid clipped startup span"]
	var expected: Dictionary = _oracle(begin, end, spans)
	if int(row["observed_union_usec"]) != int(expected["union"]) or int(row["overlap_usec"]) != int(expected["overlap"]) or int(row["outside_observed_stages_usec"]) != int(expected["outside"]):
		failures.append("Startup stage partition disagrees with independent endpoint sweep")
	# Godot JSON numbers decode as floats; dictionary equality requires exact types.
	for kind: String in ["process", "physics", "render"]:
		if int(row["stage_wall_usec"][kind]) != int(expected["stages"][kind]):
			failures.append("Startup stage duration disagrees with independent endpoint sweep")
	if int(row["observed_union_usec"]) + int(row["outside_observed_stages_usec"]) != end - begin:
		failures.append("Startup timing partition lost elapsed time")
	if row["causal_attribution"] != "inconclusive" or row["background_activity"] != "unverified":
		failures.append("Startup timestamps invented a cause")
	var has_render: bool = int(expected["stages"]["render"]) > 0
	if row["render_span_status"] != ("measured" if has_render else "unavailable"):
		failures.append("Missing render bracket presented as measured")
	if (int(row["dropped_spans"]) > 0 or row["open_render_start_usec"] != null or bool(row.get("terminal", false))) and bool(row["stage_evidence_complete"]):
		failures.append("Partial startup evidence reported complete")
	return failures

static func verify() -> Array[String]:
	var failures: Array[String] = []
	var events: Array[Dictionary] = [
		{"kind": "process", "start_usec": 90, "end_usec": 115},
		{"kind": "process", "start_usec": 112, "end_usec": 120},
		{"kind": "physics", "start_usec": 130, "end_usec": 150},
		{"kind": "render", "start_usec": 140, "end_usec": 180},
		{"kind": "render", "start_usec": 200, "end_usec": 220}]
	var row: Dictionary = Startup.interval_sample(100, 200, events)
	failures.append_array(_verify_interval(row))
	failures.append_array(_verify_interval(JSON.parse_string(JSON.stringify(row))))
	if row["observed_union_usec"] != 70 or row["overlap_usec"] != 10 or row["outside_observed_stages_usec"] != 30:
		failures.append("Overlapping/clipped wall spans were added or omitted")
	row = Startup.interval_sample(100, 2000000, events, 1, 190)
	failures.append_array(_verify_interval(row))
	if row["stage_evidence_complete"] or int(row["outside_observed_stages_usec"]) < 1000000:
		failures.append("Large unattributed gap or open/dropped spans were concealed")
	var ledger := Startup.new()
	ledger.begin_phase(0, "warmup", "initialization", 0)
	ledger.begin_process(0, null, null)
	ledger.record_span("process", 0, 10)
	ledger.begin_phase(1, "warmup", "preparation", 20)
	ledger.begin_process(100, 1, 17)
	ledger.stop(110, "cancelled fixture")
	var result: Dictionary = ledger.snapshot()
	row = result["phases"][0]["first_intervals"][0]
	if not row["crossed_phase_boundary"] or row["start_phase_id"] != 0 or row["end_phase_id"] != 1 or row["previous_diagnostic_usec"] != null:
		failures.append("Phase transition incorrectly attached a diagnostic callback")
	row = result["phases"][1]["first_intervals"][0]
	if not row["terminal"] or row["stage_evidence_complete"]: failures.append("Cancellation lost its partial terminal interval")
	ledger = Startup.new()
	ledger.begin_phase(5, "N1", "gameplay", 0)
	ledger.begin_process(0, 1, 0)
	for i: int in range(1, 65): ledger.begin_process(i * 10, i + 1, 2)
	result = ledger.snapshot()
	if ledger.active or result["phases"][0]["intervals"] != 64 or result["phases"][0]["first_intervals"].size() != 64 or result["phases"][0]["first_intervals"][-1]["end_usec"] != 640:
		failures.append("Gameplay window duplicated the final interval or exceeded its bound")
	ledger = Startup.new()
	ledger.begin_phase(0, "warmup", "initialization", 0)
	ledger.begin_process(0, null, null)
	for i: int in range(Startup.SPAN_CAP + 5): ledger.record_span("physics", i, i + 1)
	ledger.record_span("unknown", 0, 1)
	ledger.begin_process(100, null, null)
	ledger.render_finished(101)
	ledger.render_started(102)
	ledger.render_started(103)
	ledger.render_finished(104)
	for i: int in range(70): ledger.observe_renderer(1000000 + i, i, 1.0, 0.0, "unavailable")
	ledger.observe_renderer(2000000, 71, 50.0, 2.0, "valid")
	ledger.begin_process(3000000, null, null)
	for i: int in range(1, Startup.PHASE_CAP + 1): ledger.begin_phase(i, "warmup", "fixture", 3000000 + i)
	result = ledger.snapshot()
	if result["dropped_spans"] != 5 or result["invalid_spans"] != 1 or result["unpaired_render_signals"] != 2 or not result["phase_overflow"] or result["phases"].size() != Startup.PHASE_CAP:
		failures.append("Startup cap or invalid/unmatched evidence was hidden")
	var phase: Dictionary = result["phases"][0]
	if phase["renderer_observations"].size() != 64 or phase["worst_renderer_observation"]["cpu_elapsed_ms"] != 50.0 or phase["worst_renderer_observation"]["origin_frame"] != null:
		failures.append("Delayed renderer result storage/origin is incorrect")
	for saved_phase: Dictionary in result["phases"]:
		for saved: Dictionary in saved_phase["first_intervals"]: failures.append_array(_verify_interval(saved))
	return failures

# Reconcile the JSON-round-tripped retained payload with the independently saved CSV.
static func verify_saved(snapshot: Dictionary, directory: String, native_phases: Array[Dictionary], reports: Array[Dictionary]) -> Array[String]:
	var failures: Array[String] = []
	var saved: Dictionary = JSON.parse_string(JSON.stringify(snapshot))
	if saved["qualified"] or saved["evaluation"] != "inconclusive" or saved["phase_overflow"] or int(saved["invalid_spans"]) != 0 or int(saved["dropped_spans"]) != 0:
		failures.append("Startup smoke evidence overflowed, was invalid or claimed qualification")
	var phases: Array = saved["phases"]
	if phases.size() != 6: failures.append("Startup trace omitted initialization, preparation, warmup, retirement or N1")
	var native: Dictionary = {}
	for phase: Dictionary in native_phases: native[int(phase["id"])] = phase
	var scenario_reports: Dictionary = {}
	for report: Dictionary in reports: scenario_reports[report["id"]] = report
	for phase: Dictionary in phases:
		var id: int = int(phase["id"])
		if id != 0 and (not native.has(id) or native[id]["scenario"] != phase["scenario"] or native[id]["phase"] != phase["phase"]):
			failures.append("Startup and native phase identities disagree")
		var first: Array = phase["first_intervals"]
		if first.size() != mini(Startup.PREFIX_CAP, int(phase["intervals"])): failures.append("Startup prefix was lost or unbounded")
		var rows: Array = first.duplicate()
		var worst: Dictionary = phase["worst_interval"]
		if not worst.is_empty():
			rows.append(worst)
			if int(worst["interval_usec"]) != int(phase["maximum_interval_usec"]): failures.append("Incorrect retained startup maximum")
		var prior_end: int = -1
		for row: Dictionary in first:
			if prior_end >= 0 and int(row["start_usec"]) != prior_end: failures.append("Startup prefix is discontinuous")
			prior_end = int(row["end_usec"])
		var joins: Dictionary = {}
		for row: Dictionary in rows:
			failures.append_array(_verify_interval(row))
			if int(row["start_phase_id"]) != id or bool(row["crossed_phase_boundary"]) != (id != int(row["end_phase_id"])):
				failures.append("Startup interval phase boundary mismatch")
			if not row["terminal"] and not row["crossed_phase_boundary"] and row["ending_measured_frame"] != null and int(row["ending_measured_frame"]) > 1:
				joins[int(row["ending_measured_frame"])] = row
		if not joins.is_empty():
			if not scenario_reports.has(phase["scenario"]):
				failures.append("Missing measured startup scenario")
				continue
			var name: String = scenario_reports[phase["scenario"]]["raw_frames"]
			var file := FileAccess.open(directory.path_join(name), FileAccess.READ)
			if file == null:
				failures.append("Missing startup frame CSV")
				continue
			file.get_csv_line()
			var previous_usec: int = -1
			while not file.eof_reached() and not joins.is_empty():
				var fields: PackedStringArray = file.get_csv_line()
				if fields.size() != 40: continue
				var frame: int = int(fields[0])
				if joins.has(frame):
					var row: Dictionary = joins[frame]
					if int(row["end_usec"]) != int(fields[15]) or int(row["start_usec"]) != previous_usec or absf(float(row["interval_usec"]) - float(fields[3]) * 1000.0) > 0.01 or int(row["previous_diagnostic_usec"]) != int(fields[18]):
						failures.append("Startup interval/diagnostic clocks do not reconcile to saved frame CSV")
					joins.erase(frame)
				previous_usec = int(fields[15])
			file.close()
			if not joins.is_empty(): failures.append("Retained startup interval has no saved measured frame")
		var observations: Array = phase["renderer_observations"]
		if observations.size() > Startup.PREFIX_CAP: failures.append("Unbounded asynchronous renderer observations")
		for observation: Dictionary in observations:
			if observation["origin_frame"] != null or (observation["cpu_status"] == "unavailable" and observation["cpu_elapsed_ms"] != null) or (observation["gpu_status"] != "valid" and observation["gpu_ms"] != null):
				failures.append("Unavailable or delayed renderer sample fabricated an origin or time")
	return failures
