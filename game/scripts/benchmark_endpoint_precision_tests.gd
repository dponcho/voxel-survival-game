extends SceneTree

# Cloud-only injected clocks. No sleep, terrain run, target parameters or policy change.
const Calibration = preload("res://scripts/benchmark_calibration.gd")
const Cases = preload("res://scripts/benchmark_heavy_ab_tests.gd")
const Diagnostics = preload("res://scripts/benchmark_diagnostics.gd")
const Frontier = preload("res://scripts/benchmark_frontier.gd")
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")
const LABELS: Array[String] = ["null", "positive", "endpoint", "ack-duration", "count-mask", "count-drift", "missing", "reordered", "stall", "failed-workload", "failed-operation", "unavailable", "io-failed", "dose-overlap"]
const HEADER: String = "frame,tick,interval_usec,entry_usec,callback_begin_usec,callback_end_usec,previous_frame,previous_callback_usec,previous_shared_usec,previous_switched_usec,callback_write_usec,ledger_tail_usec\n"

func _initialize() -> void:
	call_deferred("_run")

func _phase(workload: String, label: String, index: int, directory: String, failures: Array[String]) -> Dictionary:
	var phase: Dictionary = Cases._phases(workload)[index]
	phase["id"] = "CAL-" + workload + "-" + Calibration.ORDER[index]
	phase["frontier_enabled"] = false
	phase["fog_frontier"] = Frontier.new().snapshot(true, false)
	var ledger := Calibration.new()
	var timing := Diagnostics.new()
	timing.start(1000000)
	var filename: String = workload + "-" + label + "-" + str(index) + ".csv"
	var file := FileAccess.open(directory.path_join(filename), FileAccess.WRITE)
	if file == null:
		failures.append("Cannot create raw precision evidence")
		return {}
	file.store_string(HEADER)
	var entry: int = 1000200
	var elapsed: int = 0
	var frame: int = 0
	var endpoint: Variant = null
	var ack_begin: Variant = null
	var extra: int = 5 if (label == "count-mask" and index in [1, 2]) or (label == "count-drift" and index == 3) else 0
	for section: int in range(7):
		var count: int = 250 + extra if section < 6 else (0 if label == "unavailable" else 4)
		var duration: int = 5000000 if section < 6 else 20000
		if label == "endpoint" and index in [2, 3]:
			if section == 5: duration -= 500
			if section == 6: duration += 500
		if label == "ack-duration" and index in [2, 3] and section == 6: duration += 500
		if label == "stall" and index == 1 and section == 0: duration += 300000
		for position: int in range(count):
			# Integer quotient/remainder preserves each main section's exact duration.
			var interval: int = int(duration / count) + (1 if position < duration % count else 0)
			if section == 6:
				interval = 5000
				if label == "endpoint" and index in [2, 3] and position == 0: interval += 500
				if label == "ack-duration" and index in [2, 3] and position == 3: interval += 500
			var tick: int = 1800 if section == 6 else section * 300 + mini(299 if section == 5 else 300, 1 + int(position * 300 / count))
			entry += interval
			elapsed += interval
			frame += 1
			var cost: int = 30 + frame % 7
			file.store_string("%d,%d,%d,%d,%d,%d,%d,%d,%d,0,8,2\n" % [frame, tick, interval, entry, entry + 7, entry + 7 + cost, frame - 1, timing.last_callback_usec, timing.last_shared_usec])
			ledger.record_interval(tick, interval)
			timing.record_interval(interval)
			timing.record_callback(entry + 7, entry + 7 + cost)
			ledger.record_callback(cost)
			ledger.harness_usec += 2
			if section == 6 and position == 0:
				endpoint = entry
				ack_begin = timing.last_callback_end_usec + 2
	file.flush()
	if file.get_error() != OK: failures.append("Raw precision write failed")
	file.close()
	var measured_end: int = timing.last_callback_end_usec + 2
	var dose: int = 0 if label == "null" or index not in [1, 2] else Calibration.DOSE_USEC
	var drain_begin: int = measured_end + 200
	var dose_begin: int = drain_begin + 400 + 100
	var end: int = measured_end + 1000 + dose
	if index in [1, 2]:
		ledger.dose = {"requested_usec": Calibration.DOSE_USEC, "start_usec": measured_end - 1 if label == "dose-overlap" and index == 1 else dose_begin,
			"end_usec": dose_begin + dose, "elapsed_usec": dose}
	phase["samples"] = frame
	phase["wall_seconds"] = float(elapsed) / 1000000.0
	phase["measurement_end_usec"] = measured_end
	phase["diagnostic_accounting"] = timing.snapshot(end, 400)
	phase["route_calibration"] = ledger.snapshot()
	phase["raw_frames"] = filename
	phase["precision_clock"] = {"scope": "modeled wall clocks; not terrain, disk or CPU measurements", "interval_begin_usec": 1000200,
		"endpoint_entry_usec": endpoint, "ack_begin_usec": ack_begin, "ack_end_usec": measured_end if ack_begin != null else null,
		"dose_begin_usec": dose_begin if index in [1, 2] else null, "dose_end_usec": dose_begin + dose if index in [1, 2] else null,
		"native_phase_close_usec": measured_end + 100, "writer_drain_begin_usec": drain_begin, "writer_drain_end_usec": drain_begin + 400,
		"callback_write_usec": frame * 8, "file_io_causal_usec": null,
		"phases": [{"phase": "preparation", "begin_usec": 998000, "end_usec": 1000000},
			{"phase": "overhead_diagnostic", "begin_usec": 1000000, "end_usec": measured_end + 100},
			{"phase": "retirement", "begin_usec": end, "end_usec": end + 2000}],
		"native_operations": "unavailable: clock-only controls"}
	if label == "failed-workload" and index == 1: phase["actor_ticks"] -= 1
	if label == "failed-operation" and index == 1:
		var operation: Dictionary = {"upload": {"max_usec": 751}, "deletion": {"max_usec": 0}, "dropped_frames": 0}
		phase["modeled_operation"] = operation
		var reasons: Array[String] = Evaluation.operation_failures(operation)
		phase["evaluation"] = Evaluation.scenario_result(true, not reasons.is_empty(), reasons)["evaluation"]
	return phase

func _run() -> void:
	var directory: String = ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--precision-output="): directory = argument.trim_prefix("--precision-output=")
	var failures: Array[String] = []
	if directory.is_empty():
		print("Missing --precision-output (precreated cloud directory)")
		quit(1)
		return
	var controls: Array[Dictionary] = []
	for workload: String in ["H1", "H2"]:
		for label: String in LABELS:
			var phases: Array[Dictionary] = []
			for index: int in range(4):
				var phase: Dictionary = _phase(workload, label, index, directory, failures)
				if phase.is_empty():
					quit(1)
					return
				phases.append(phase)
			var omitted: Array[Dictionary] = []
			if label == "missing": omitted.append(phases.pop_back())
			if label == "reordered": phases.reverse()
			var assessment: Dictionary = Calibration.evaluate(phases, false, label == "io-failed")
			var expected: String = "controls_resolved" if label == "positive" else "inconclusive"
			if assessment["workloads"][workload]["status"] != expected: failures.append(workload + "/" + label + " changed authoritative status")
			var decoded: Array[Dictionary] = []
			for phase: Dictionary in JSON.parse_string(JSON.stringify(phases)): decoded.append(phase)
			if Calibration.evaluate(decoded, false, label == "io-failed") != assessment: failures.append("Precision verdict changed after serialization")
			controls.append({"name": workload + "/" + label, "workload": workload, "io_failed": label == "io-failed", "expected": expected,
				"phases": phases, "omitted_phases": omitted, "assessment": assessment})
	print("CAIRN_ENDPOINT_PRECISION=" + JSON.stringify({"schema": 1, "scope": "software endpoint/count precision; no policy or hardware qualification", "passed": failures.is_empty(), "failures": failures, "controls": controls}))
	quit(0 if failures.is_empty() else 1)
