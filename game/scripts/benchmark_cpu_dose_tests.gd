extends SceneTree

const CPU = preload("res://scripts/benchmark_cpu_dose.gd")
const Cases = preload("res://scripts/benchmark_heavy_ab_tests.gd")
const Diagnostics = preload("res://scripts/benchmark_diagnostics.gd")
const Calibration = preload("res://scripts/benchmark_calibration.gd")
const Frontier = preload("res://scripts/benchmark_frontier.gd")
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")
const LABELS: Array[String] = ["null", "below", "at", "above", "threshold-overlap", "wait-masked", "count-mask", "count-drift", "count-route-mix", "endpoint", "ack-duration", "incomplete", "missing", "reordered", "stall", "failed-workload", "failed-operation", "missing-dose", "dose-overlap", "missing-body", "phase-invalid", "window-drift", "route-drift", "io-failed", "short", "body-drift", "main-body-drift"]
const HEADER: String = "frame,tick,interval_usec,entry_usec,body_begin_usec,body_end_usec,dose_begin_usec,dose_end_usec,requested_usec,callback_end_usec,previous_frame,previous_callback_usec,ledger_tail_usec\n"

func _initialize() -> void: call_deferred("_run")

static func requested(label: String) -> int:
	if label == "null": return 0
	if label == "below": return 5
	if label == "at": return 10
	if label == "threshold-overlap": return 9
	return 20

static func expected(label: String) -> String:
	if label == "null": return "null_observed"
	return "cpu_span_sensitivity_observed" if label in ["below", "at", "above", "wait-masked", "count-mask", "count-drift", "endpoint", "ack-duration"] else "inconclusive"

static func phase(workload: String, label: String, index: int, directory: String, failures: Array[String]) -> Dictionary:
	var p: Dictionary = Cases._phases(workload)[index]
	p["id"] = "CAL-" + workload + "-" + Calibration.ORDER[index]
	p["frontier_enabled"] = false
	p["fog_frontier"] = Frontier.new().snapshot(true, false)
	var cpu := CPU.new()
	var timing := Diagnostics.new()
	var route := Calibration.new()
	timing.start(1000000)
	var name: String = workload + "-" + label + "-" + str(index) + ".csv"
	var file := FileAccess.open(directory.path_join(name), FileAccess.WRITE)
	if file == null:
		failures.append("Cannot create CPU clock CSV")
		return {}
	file.store_string(HEADER)
	var entry: int = 1000200
	var elapsed: int = 0
	var frame: int = 0
	var prev_dose: int = 0
	var ack: int = 0
	var ask: int = requested(label) if index in [1, 2] else 0
	var injected: int = 11 if label == "threshold-overlap" and index == 2 else ask
	for section: int in range(7):
		var count: int = 250 if section < 6 else 4
		if section < 6 and ((label == "count-mask" and index in [1, 2]) or (label == "count-drift" and index == 3)): count += 5
		if section < 6 and section % 2 == 0 and label == "count-route-mix" and index in [1, 2]: count += 200
		var duration: int = 5000000 if section < 6 else 20000
		if label == "stall" and index == 1 and section == 0: duration += 300000
		if label == "route-drift" and index == 3:
			if section == 0: duration += 100000
			if section == 1: duration -= 100000
		if label == "endpoint" and index in [2, 3]:
			if section == 5: duration -= 500
			if section == 6: duration += 500
		if label == "ack-duration" and index in [2, 3] and section == 6: duration += 500
		for position: int in range(count):
			var interval: int = int(duration / count) + (1 if position < duration % count else 0)
			if label != "wait-masked": interval += prev_dose
			var baseline: int = (800 if section % 2 == 0 else 1200) if section < 6 else 1000
			if label == "body-drift" and index == 3: baseline += 30
			if label == "main-body-drift" and index == 3 and section < 6: baseline += 20 if section % 2 == 0 else -20
			var tick: int = 1800 if section == 6 else section * 300 + 1
			entry += interval
			elapsed += interval
			frame += 1
			var begin: int = entry + 7
			var end: int = begin + baseline + injected
			var ds: Variant = begin + 200 if ask > 0 else null
			var de: Variant = int(ds) + injected if ds != null else null
			if label == "missing-dose" and index == 1: ds = null
			if label == "dose-overlap" and index == 1: de = end + 1
			file.store_string("%d,%d,%d,%d,%d,%d,%s,%s,%d,%d,%d,%d,2\n" % [frame, tick, interval, entry, begin, end,
				str(ds) if ds != null else "", str(de) if de != null else "", ask, end + 8, frame - 1, timing.last_callback_usec])
			cpu.record(tick, begin, end, ds, de, ask)
			route.record_interval(tick, interval)
			route.record_callback(end + 8 - begin)
			route.harness_usec += 2
			timing.record_interval(interval)
			timing.record_callback(begin, end + 8)
			prev_dose = injected
			if section == 6 and position == 0: ack = end + 10
	file.flush()
	if file.get_error() != OK: failures.append("CPU clock CSV write failed")
	file.close()
	var measured: int = timing.last_callback_end_usec + 2
	var end: int = measured + 1055 + (450000 if label == "window-drift" and index == 3 else 0)
	p.merge({"samples": frame, "wall_seconds": float(elapsed) / 1000000.0, "measurement_end_usec": measured,
		"diagnostic_accounting": timing.snapshot(end, 400), "route_calibration": route.snapshot(), "raw_frames": name,
		"cpu_dose_accounting": cpu.snapshot(), "edit_acknowledgement": {"start_usec": ack, "end_usec": measured},
		"fixed_work_boundaries": {"native_phase_closed_usec": measured + 100, "writer_drain_begin_usec": measured + 200, "writer_drain_end_usec": measured + 600},
		"cpu_clock": {"scope": "modeled clocks; hypothetical eligible workload, no CPU/GPU/terrain measurement", "interval_begin_usec": 1000200,
			"phases": [{"phase": "preparation", "begin_usec": 998000, "end_usec": 1000000},
				{"phase": "overhead_diagnostic", "begin_usec": 1000000, "end_usec": measured + 100},
				{"phase": "retirement", "begin_usec": end, "end_usec": end + 2000}], "file_io_causal_usec": null}}, true)
	if label == "incomplete" and index == 1: p["completed"] = false
	if label == "failed-workload" and index == 1: p["actor_ticks"] -= 1
	if label == "failed-operation" and index == 1:
		p["modeled_operation"] = {"upload": {"max_usec": 751}, "deletion": {"max_usec": 0}, "dropped_frames": 0}
		var reasons: Array[String] = Evaluation.operation_failures(p["modeled_operation"])
		p["evaluation"] = Evaluation.scenario_result(true, not reasons.is_empty(), reasons)["evaluation"]
	if label == "missing-body" and index == 1: p["cpu_dose_accounting"]["bins"][6].erase("body_usec")
	if label == "phase-invalid" and index == 1: p["fixed_work_boundaries"]["native_phase_closed_usec"] = measured + 601
	return p

func _run() -> void:
	var directory: String = ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--cpu-output="): directory = argument.trim_prefix("--cpu-output=")
	if directory.is_empty():
		quit(1)
		return
	var failures: Array[String] = []
	var controls: Array[Dictionary] = []
	for workload: String in ["H1", "H2"]:
		for label: String in LABELS:
			var phases: Array[Dictionary] = []
			for index: int in range(4):
				var p: Dictionary = phase(workload, label, index, directory, failures)
				if p.is_empty():
					quit(1)
					return
				phases.append(p)
			var omitted: Array[Dictionary] = []
			if label == "missing": omitted.append(phases.pop_back())
			if label == "reordered": phases.reverse()
			var assessment: Dictionary = CPU.evaluate(phases, label == "short", label == "io-failed", requested(label))
			if assessment["workloads"][workload]["status"] != expected(label): failures.append(workload + "/" + label + " CPU status differs")
			var decoded: Array[Dictionary] = []
			for p: Dictionary in JSON.parse_string(JSON.stringify(phases)): decoded.append(p)
			if CPU.evaluate(decoded, label == "short", label == "io-failed", requested(label)) != assessment: failures.append("CPU saved classification changed")
			controls.append({"name": workload + "/" + label, "workload": workload, "expected": expected(label), "short_run": label == "short",
				"io_failed": label == "io-failed", "declared_per_callback_usec": requested(label), "phases": phases,
				"omitted_phases": omitted, "assessment": assessment})
	print("CAIRN_CPU_DOSE_CONTROLS=" + JSON.stringify({"schema": 1, "passed": failures.is_empty(), "failures": failures,
		"scope": "synthetic per-callback CPU span sensitivity; no qualification", "controls": controls}))
	quit(0 if failures.is_empty() else 1)
