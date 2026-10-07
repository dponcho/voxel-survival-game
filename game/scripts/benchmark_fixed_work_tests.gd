extends SceneTree

const Fixed = preload("res://scripts/benchmark_fixed_work.gd")
const Precision = preload("res://scripts/benchmark_endpoint_precision_tests.gd")
const Calibration = preload("res://scripts/benchmark_calibration.gd")
const LABELS: Array[String] = ["null", "below", "at", "above", "threshold-overlap", "endpoint", "ack-duration", "count-mask", "count-drift", "incomplete", "missing", "reordered", "stall", "failed-workload", "failed-operation", "unavailable", "io-failed", "dose-overlap", "window-drift", "route-drift", "phase-invalid", "missing-window"]

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var directory: String = ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--fixed-output="): directory = argument.trim_prefix("--fixed-output=")
	if directory.is_empty():
		quit(1)
		return
	var failures: Array[String] = []
	var controls: Array[Dictionary] = []
	for workload: String in ["H1", "H2"]:
		for label: String in LABELS:
			var requested: int = 600000
			if label == "null": requested = 0
			if label == "below": requested = 150106
			if label == "at": requested = 300213
			if label == "threshold-overlap": requested = 299000
			var phases: Array[Dictionary] = []
			for index: int in range(4):
				var injected: int = 301000 if label == "threshold-overlap" and index == 2 else requested
				var closure: int = 1055 + (450000 if label == "window-drift" and index == 3 else 0)
				var p: Dictionary = Precision._phase(workload, label, index, directory, failures, closure, injected)
				if p.is_empty():
					quit(1)
					return
				if index in [1, 2] and requested > 0: p["route_calibration"]["closure_dose"]["requested_usec"] = requested
				var c: Dictionary = p["precision_clock"]
				p["fixed_work_boundaries"] = {"native_phase_closed_usec": c["native_phase_close_usec"],
					"writer_drain_begin_usec": c["writer_drain_begin_usec"], "writer_drain_end_usec": c["writer_drain_end_usec"]}
				p["edit_acknowledgement"] = {"start_usec": c["ack_begin_usec"] if c["ack_begin_usec"] != null else 0, "end_usec": p["measurement_end_usec"]}
				if label == "incomplete" and index == 1: p["completed"] = false
				if label == "phase-invalid" and index == 1: p["fixed_work_boundaries"]["native_phase_closed_usec"] = c["writer_drain_end_usec"] + 1
				if label == "missing-window" and index == 1: p["diagnostic_accounting"].erase("elapsed_usec")
				phases.append(p)
			var omitted: Array[Dictionary] = []
			if label == "missing": omitted.append(phases.pop_back())
			if label == "reordered": phases.reverse()
			var assessment: Dictionary = Fixed.evaluate(phases, false, label == "io-failed", requested)
			var expected: String = "sensitivity_observed" if label in ["below", "at", "above", "endpoint", "ack-duration", "count-mask", "count-drift"] else ("null_observed" if label == "null" else "inconclusive")
			if assessment["workloads"][workload]["status"] != expected: failures.append(workload + "/" + label + " fixed-work status differs")
			var decoded: Array[Dictionary] = []
			for p: Dictionary in JSON.parse_string(JSON.stringify(phases)): decoded.append(p)
			if Fixed.evaluate(decoded, false, label == "io-failed", requested) != assessment: failures.append("Fixed-work saved decision changed")
			controls.append({"name": workload + "/" + label, "workload": workload, "io_failed": label == "io-failed",
				"declared_dose_usec": requested, "expected": expected, "phases": phases, "omitted_phases": omitted,
				"assessment": assessment, "legacy_assessment": Calibration.evaluate(phases, false, label == "io-failed")})
	print("CAIRN_FIXED_WORK=" + JSON.stringify({"schema": 1, "scope": "synthetic fixed-work closure controls; no target qualification", "passed": failures.is_empty(), "failures": failures, "controls": controls}))
	quit(0 if failures.is_empty() else 1)
