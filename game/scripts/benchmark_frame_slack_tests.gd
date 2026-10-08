extends SceneTree

const Frame = preload("res://scripts/benchmark_frame_slack.gd")
const Diagnostics = preload("res://scripts/benchmark_diagnostics.gd")
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")
const LABELS: Array[String] = ["null", "below", "at", "above", "threshold-overlap", "slack", "final-dose", "count-drift", "count-route-mix", "endpoint", "ack-duration", "incomplete", "missing", "reordered", "stall", "failed-workload", "failed-operation", "missing-dose", "dose-overlap", "missing-body", "phase-invalid", "window-drift", "io-failed", "short", "body-drift", "main-body-drift", "missing-successor", "cycle-overlap", "cycle-drift", "main-cycle-drift"]
const HEADER: String = "frame,tick,entry_usec,body_begin_usec,body_end_usec,dose_begin_usec,dose_end_usec,requested_usec,complete_callback_end_usec,next_entry_usec,previous_callback_usec,baseline_updates\n"

func _initialize() -> void: call_deferred("_run")

static func requested(label: String) -> int:
	if label == "null": return 0
	if label == "below": return 100
	if label == "at": return 200
	if label == "threshold-overlap": return 199
	if label == "slack": return 500
	return 400

static func expected(label: String) -> String:
	if label == "null": return "null_observed"
	if label == "slack": return "slack_observed"
	return "frame_sensitivity_observed" if label in ["below", "at", "above", "final-dose", "endpoint", "ack-duration"] else "inconclusive"

static func phase(label: String, index: int, directory: String, failures: Array[String]) -> Dictionary:
	var ledger := Frame.new()
	var timing := Diagnostics.new()
	timing.start(1000000)
	var counts: Array[int] = [4, 5, 5, 4, 5, 5, 4]
	if label == "count-drift" and index == 3: counts[6] += 4
	if label == "count-route-mix" and index in [1, 2]: counts[0] += 8
	if label == "short": counts[6] -= 1
	var name: String = label + "-" + str(index) + ".csv"
	var file := FileAccess.open(directory.path_join(name), FileAccess.WRITE)
	if file == null:
		failures.append("Frame clock file open failed")
		return {}
	file.store_string(HEADER)
	var entry: int = 1000200
	var frame: int = 0
	var ack: int = 0
	for j: int in range(7):
		for position: int in range(counts[j]):
			frame += 1
			var ask: int = requested(label) if index in [1, 2] else 0
			if label == "final-dose" and not (j == 6 and position == counts[j] - 1): ask = 0
			var dose: int = 201 if label == "threshold-overlap" and index == 2 else ask
			var base: int = (800 if j % 2 == 0 else 1200) if j < 6 else 1000
			if label == "body-drift" and index == 3: base += 30
			if label == "main-body-drift" and index == 3 and j < 6: base += 25 if j % 2 == 0 else -25
			var cycle: int = 20000
			if label == "count-route-mix" and j < 6: cycle = 16000 if j % 2 == 0 else 24000
			if label != "slack": cycle += dose
			if label == "cycle-drift" and index == 3: cycle += 500
			if label == "main-cycle-drift" and index == 3:
				if j == 0: cycle += 300
				if j == 1: cycle -= 240
			if label == "endpoint" and index in [2, 3]:
				if j == 5 and position == counts[j] - 1: cycle -= 500
				if j == 6 and position == 0: cycle += 500
			if label == "ack-duration" and index in [2, 3] and j == 6 and position == counts[j] - 1: cycle += 500
			if label == "stall" and index == 1 and frame == 1: cycle += 300000
			var begin: int = entry + 7
			var end: int = begin + base + dose
			var ds: Variant = begin + 200 if ask > 0 else null
			var de: Variant = int(ds) + dose if ds != null else null
			if label == "missing-dose" and index == 1: ds = null
			if label == "dose-overlap" and index == 1: de = end + 1
			var next: Variant = entry + cycle
			if label == "cycle-overlap" and index == 1 and frame == 1: next = end + 7
			if label == "missing-successor" and index == 1 and j == 6 and position == counts[j] - 1: next = null
			var row: Dictionary = {"frame": frame, "tick": 1800 if j == 6 else j * 300 + 1, "entry_usec": entry,
				"body_begin_usec": begin, "body_end_usec": end, "dose_begin_usec": ds, "dose_end_usec": de, "requested_usec": ask,
				"complete_callback_end_usec": end + 8, "next_entry_usec": next, "previous_callback_usec": timing.last_callback_usec,
				"baseline_updates": 7 if label == "failed-workload" and index == 1 and frame == 1 else 8}
			file.store_string("%d,%d,%d,%d,%d,%s,%s,%d,%d,%s,%d,%d\n" % [frame, row["tick"], entry, begin, end,
				str(ds) if ds != null else "", str(de) if de != null else "", ask, end + 8, str(next) if next != null else "", timing.last_callback_usec, row["baseline_updates"]])
			ledger.record(row)
			timing.record_interval(cycle)
			timing.record_callback(entry, end + 8)
			if j == 6 and position == 0: ack = end + 8
			entry += cycle
	file.flush()
	if file.get_error() != OK: failures.append("Frame clock CSV write failed")
	file.close()
	var anchor: Dictionary = {"entry_usec": entry, "complete_callback_end_usec": entry + 15, "previous_callback_usec": timing.last_callback_usec}
	var closed: int = entry + 15
	var end: int = closed + 1055 + (20000 if label == "window-drift" and index == 3 else 0)
	var p: Dictionary = {"index": index, "samples": frame, "completed": not (label == "incomplete" and index == 1),
		"work_units_valid": not (label == "failed-workload" and index == 1), "operation_evaluation": "inconclusive", "raw_file": name,
		"first_entry_usec": 1000200, "closing_anchor": anchor, "acknowledgement_usec": closed - ack,
		"frame_slack_accounting": ledger.snapshot(), "diagnostic_accounting": timing.snapshot(end, 400),
		"phase_boundaries": {"preparation_begin_usec": 998000, "measurement_begin_usec": 1000000,
			"native_phase_closed_usec": closed + 100, "writer_drain_begin_usec": closed + 200, "writer_drain_end_usec": closed + 600,
			"retirement_begin_usec": end, "retirement_end_usec": end + 2000},
		"render_signals": null, "wait_service_usec": null, "native_operation_evidence": "modeled phase boundaries, no executed terrain"}
	if label == "failed-operation" and index == 1:
		p["modeled_operation"] = {"upload": {"max_usec": 751}, "deletion": {"max_usec": 0}, "dropped_frames": 0}
		var reasons: Array[String] = Evaluation.operation_failures(p["modeled_operation"])
		p["operation_evaluation"] = Evaluation.scenario_result(true, not reasons.is_empty(), reasons)["evaluation"]
	if label == "missing-body" and index == 1: p["frame_slack_accounting"]["bins"][6].erase("body_usec")
	if label == "phase-invalid" and index == 1: p["phase_boundaries"]["native_phase_closed_usec"] = closed + 601
	return p

func _run() -> void:
	var directory: String = ""
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--frame-output="): directory = arg.trim_prefix("--frame-output=")
	if directory.is_empty():
		quit(1)
		return
	var failures: Array[String] = []
	var controls: Array[Dictionary] = []
	for label: String in LABELS:
		var phases: Array[Dictionary] = []
		for index: int in range(4): phases.append(phase(label, index, directory, failures))
		var omitted: Array[Dictionary] = []
		if label == "missing": omitted.append(phases.pop_back())
		if label == "reordered": phases.reverse()
		var result: Dictionary = Frame.evaluate(phases, requested(label), label == "final-dose", label == "io-failed")
		if result["status"] != expected(label): failures.append(label + " frame sensitivity result differs")
		var decoded: Array[Dictionary] = []
		for p: Dictionary in JSON.parse_string(JSON.stringify(phases)): decoded.append(p)
		if Frame.evaluate(decoded, requested(label), label == "final-dose", label == "io-failed") != result: failures.append("Frame saved classification differs")
		controls.append({"name": label, "expected": expected(label), "declared_usec": requested(label), "phases": phases, "omitted_phases": omitted, "assessment": result})
	print("CAIRN_FRAME_SLACK_CONTROLS=" + JSON.stringify({"schema": 1, "passed": failures.is_empty(), "failures": failures,
		"scope": "modeled callback cycles; no terrain, CPU service, GPU or target qualification", "controls": controls}))
	quit(0 if failures.is_empty() else 1)
