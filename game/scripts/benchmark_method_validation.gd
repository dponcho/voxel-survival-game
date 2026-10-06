extends SceneTree

# Cloud-only evaluator controls. These injected clocks are not hardware A/A
# measurements, executed gameplay, or evidence of actual diagnostic overhead.
# Generate consistent frame counts/intervals instead of editing report means.
const Cases = preload("res://scripts/benchmark_heavy_ab_tests.gd")
const Diagnostics = preload("res://scripts/benchmark_diagnostics.gd")
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")
const START_USEC: int = 1000000
const DURATION_USEC: int = 30000000
const BLOCK_USEC: int = 5000000
const SETUP_USEC: int = 200
const CLOSURE_USEC: int = 1000

func _initialize() -> void:
	var failures: Array[String] = []
	var controls: Array[Dictionary] = []
	for workload: String in ["H1", "H2"]:
		for varying: bool in [false, true]:
			for effect: Dictionary in [
				{"name": "null", "permille": 0, "closure": 0, "stationary": "passed"},
				{"name": "below-limit", "permille": 5, "closure": 0, "stationary": "passed"},
				{"name": "above-limit", "permille": 20, "closure": 0, "stationary": "failed"},
				{"name": "closure-cost", "permille": 0, "closure": 600000, "stationary": "failed"}]:
				# A conditional expression produces an untyped Array in the pinned
				# engine; initialize the typed literal directly, then change values.
				var profile: Array[int] = [5000, 5000, 5000, 5000, 5000, 5000]
				if varying:
					for section: int in [0, 2, 4]: profile[section] = 4000
				var phases: Array[Dictionary] = _phases(workload, profile, effect["permille"], effect["closure"])
				var evaluated: Dictionary = Evaluation.heavy_diagnostic_ab(phases, false, false)
				var comparison: Dictionary = evaluated["workloads"][workload]
				var expected: String = "inconclusive" if varying else str(effect["stationary"])
				var name: String = workload + "/" + ("varying/" if varying else "stationary/") + str(effect["name"])
				if comparison["outcome"] != expected:
					failures.append(name + ": unexpected classification")
				if comparison["workload_equivalence"] != "verified" or comparison["probe_switch"] != "verified":
					failures.append(name + ": control prerequisites differ")
				if varying and not "Within-phase timing is unstable" in comparison["reasons"]:
					failures.append(name + ": varying route did not exercise stationarity gate")
				var decoded: Array[Dictionary] = []
				for phase: Dictionary in JSON.parse_string(JSON.stringify(phases)): decoded.append(phase)
				var saved: Dictionary = Evaluation.heavy_diagnostic_ab(decoded, false, false)
				if saved["workloads"][workload] != comparison or saved["total_overhead"] != evaluated["total_overhead"]:
					failures.append(name + ": JSON round trip changed the decision")
				controls.append({"name": name, "workload": workload, "profile_usec": profile,
					"frame_scale_permille": effect["permille"], "enabled_closure_delta_usec": effect["closure"],
					"expected": expected, "phases": phases, "comparison": comparison,
					"total_overhead": evaluated["total_overhead"]})
	var report: Dictionary = {"schema": 1, "passed": failures.is_empty(), "failures": failures,
		"scope": "synthetic-clock evaluator controls; not physical A/A or target qualification",
		"hardware_noise_calibrated": false, "shared_control_present": false,
		"start_usec": START_USEC, "duration_usec": DURATION_USEC,
		"setup_usec": SETUP_USEC, "closure_usec": CLOSURE_USEC, "controls": controls}
	print("CAIRN_DIAGNOSTIC_METHOD=" + JSON.stringify(report))
	quit(0 if failures.is_empty() else 1)

static func _phases(workload: String, profile: Array[int], permille: int, extra_closure: int) -> Array[Dictionary]:
	# Reuse only the existing valid heavy report contract. All timing, callback,
	# dispatch and coverage sample counts below come from the injected clock.
	var phases: Array[Dictionary] = Cases._phases(workload)
	for phase: Dictionary in phases:
		var enabled: bool = phase["frontier_enabled"]
		var ledger := Diagnostics.new()
		ledger.start(START_USEC)
		var elapsed: int = 0
		while elapsed < DURATION_USEC:
			var section: int = mini(int(float(elapsed) / float(BLOCK_USEC)), 5)
			var interval: int = profile[section]
			if enabled: interval = int(interval * (1000 + permille) / 1000)
			interval = mini(interval, DURATION_USEC - elapsed)
			elapsed += interval
			var now: int = START_USEC + SETUP_USEC + elapsed
			ledger.record_interval(interval)
			ledger.record_callback(now - (100 if enabled else 20), now, 80 if enabled else 0)
			if enabled: ledger.switched_calls += 1
		var end: int = START_USEC + SETUP_USEC + elapsed + CLOSURE_USEC + (extra_closure if enabled else 0)
		phase["samples"] = ledger.callbacks
		phase["diagnostic_accounting"] = ledger.snapshot(end, 400)
		phase["measurement_end_usec"] = ledger.last_callback_end_usec
		if enabled:
			phase["fog_frontier"]["samples"] = ledger.callbacks
	return phases
