extends SceneTree

const Calibration = preload("res://scripts/benchmark_calibration.gd")
const Cases = preload("res://scripts/benchmark_heavy_ab_tests.gd")
const Diagnostics = preload("res://scripts/benchmark_diagnostics.gd")
const Frontier = preload("res://scripts/benchmark_frontier.gd")
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")

func _initialize() -> void:
	call_deferred("_run")

static func phases(workload: String, varying: bool = true) -> Array[Dictionary]:
	var result: Array[Dictionary] = Cases._phases(workload)
	for index: int in range(4):
		var phase: Dictionary = result[index]
		phase["id"] = "CAL-" + workload + "-" + Calibration.ORDER[index]
		phase["frontier_enabled"] = false
		phase["fog_frontier"] = Frontier.new().snapshot(true, false)
		var ledger := Calibration.new()
		var timing := Diagnostics.new()
		timing.start(1000000)
		var elapsed: int = 0
		for section: int in range(6):
			var interval: int = (4000 if section % 2 == 0 else 6000) if varying else 5000
			for frame: int in range(1000):
				elapsed += interval
				ledger.record_interval(section * 300 + 1, interval)
				ledger.record_callback(20)
				timing.record_interval(interval)
				timing.record_callback(1000200 + elapsed - 20, 1000200 + elapsed)
		elapsed += 1000
		ledger.record_interval(1800, 1000)
		ledger.record_callback(20)
		timing.record_interval(1000)
		timing.record_callback(1000200 + elapsed - 20, 1000200 + elapsed)
		var closure: int = 600000 if index in [1, 2] else 0
		var end: int = 1000200 + elapsed + 1000 + closure
		if closure > 0:
			ledger.dose = {"requested_usec": closure, "start_usec": end - closure, "end_usec": end, "elapsed_usec": closure}
		phase["route_calibration"] = ledger.snapshot()
		phase["samples"] = timing.callbacks
		phase["wall_seconds"] = float(elapsed) / 1000000.0
		phase["measurement_end_usec"] = timing.last_callback_end_usec
		phase["diagnostic_accounting"] = timing.snapshot(end, 400)
	return result

func _runtime(failures: Array[String]) -> void:
	var fixture := Cases.Harness.new()
	root.add_child(fixture)
	fixture.set_process(false)
	fixture.set_physics_process(false)
	fixture._make_scene()
	fixture.status_label = Label.new()
	fixture.detail_label = Label.new()
	fixture.add_child(fixture.status_label)
	fixture.add_child(fixture.detail_label)
	fixture.scenarios = Calibration.scenarios({"id": "warmup", "seconds": 180.0, "fixture": 0, "actors": 12, "rate": 0.0})
	for index: int in range(1, 9):
		fixture.scenario_index = index
		fixture._start_scenario()
		if not fixture.heavy_budget or fixture.phase_label != "preparation" or fixture.terrain.generator.fixture != 1 or fixture.actor_instances.multimesh.visible_instance_count != (24 if index >= 5 else 12) or fixture.rain.visible != (index >= 5):
			failures.append("Calibration changed the heavy preparation workload")
		var scans: int = fixture.scans
		if fixture._frontier_sample()["status"] != "unavailable" or fixture.scans != scans:
			failures.append("Calibration null/closure controls ran the switched probe")
		for seconds: float in [0.0, 15.0, 30.0]:
			fixture.scenario_elapsed = seconds
			fixture._sync_pose()
			if absf(fixture._route_target().x - (10.0 + 6.5 * seconds)) > 0.00001 or not is_equal_approx(fixture.camera.rotation.y, PI * 0.5 if seconds == 15.0 else -PI * 0.5):
				failures.append("Calibration changed the route/reversal")
		fixture.state = "running"
		fixture.simulation_ticks = 1800
		fixture._physics_step(1.0 / 60.0)
		if fixture.simulation_ticks != 1800: failures.append("Calibration added endpoint commands")
	fixture.free()

func _run() -> void:
	var failures: Array[String] = []
	_runtime(failures)
	var ledger := Calibration.new()
	for tick: int in [0, 300, 301, 600, 601, 900, 901, 1200, 1201, 1500, 1501, 1799, 1800]:
		ledger.record_interval(tick, 1000)
		ledger.record_callback(10)
	var counts: Array[int] = []
	for section: Dictionary in ledger.bins: counts.append(section["samples"])
	if counts != [2, 2, 2, 2, 2, 2, 1]: failures.append("Route or terminal boundaries changed")
	ledger.record_interval(1799, 1000)
	if not ledger.invalid: failures.append("Reordered route clock was accepted")
	for control: Dictionary in [
		{"off": [1000.0, 1000.0], "on": [1005.0, 1005.0], "expected": "below_limit"},
		{"off": [1000.0, 1000.0], "on": [1010.0, 1010.0], "expected": "above_limit"},
		{"off": [1000.0, 1000.0], "on": [1009.0, 1011.0], "expected": "inconclusive"},
		{"off": [1000.0, 1000.0], "on": [990.0, 990.0], "expected": "inconclusive"}]:
		var off: Array[float] = []
		var on: Array[float] = []
		for value: float in control["off"]: off.append(value)
		for value: float in control["on"]: on.append(value)
		if Calibration.compare(off, on)["classification"] != control["expected"]: failures.append("Calibration changed the 1% or speedup boundary")
	var controls: Array[Dictionary] = []
	for workload: String in ["H1", "H2"]:
		for label: String in ["stationary", "varying", "missing", "reordered", "stall", "route-drift", "failed", "dose-overlap", "dose-missing", "unavailable-bin", "contract", "short", "io-failed"]:
			var records: Array[Dictionary] = phases(workload, label != "stationary")
			match label:
				"missing": records.pop_back()
				"reordered": records.reverse()
				"stall": records[1]["wall_seconds"] = 31.0
				"route-drift":
					# Keep total duration unchanged: drift lives at matching positions.
					records[3]["route_calibration"]["bins"][0]["usec"] += 100000
					records[3]["route_calibration"]["bins"][1]["usec"] -= 100000
				"failed": records[1]["evaluation"] = "failed"
				"dose-overlap": records[1]["route_calibration"]["closure_dose"]["start_usec"] = records[1]["measurement_end_usec"] - 1
				"dose-missing": records[1]["route_calibration"]["closure_dose"]["requested_usec"] = 0
				"unavailable-bin": records[1]["route_calibration"]["bins"][6]["samples"] = 0
				"contract": records[1]["workload_contract"]["visual_radius"] = 80
			var evaluated: Dictionary = Calibration.evaluate(records, label == "short", label == "io-failed")
			var expected: String = "controls_resolved" if label in ["stationary", "varying"] else "inconclusive"
			if evaluated["workloads"][workload]["status"] != expected: failures.append(workload + "/" + label + " unexpected control status")
			var decoded: Array[Dictionary] = []
			for phase: Dictionary in JSON.parse_string(JSON.stringify(records)): decoded.append(phase)
			if Calibration.evaluate(decoded, label == "short", label == "io-failed") != evaluated: failures.append("Saved calibration changes after JSON round trip")
			if evaluated["qualified"] or evaluated["shared_overhead"]["added_fraction"] != null: failures.append("Calibration qualified total overhead")
			controls.append({"name": workload + "/" + label, "workload": workload, "short_run": label == "short", "io_failed": label == "io-failed", "expected": expected,
				"phases": records, "assessment": evaluated})
	print("CAIRN_ROUTE_CONTROLS=" + JSON.stringify({"schema": 1, "passed": failures.is_empty(), "failures": failures,
		"scope": "software route/closure controls; physical hardware precision unverified", "controls": controls}))
	quit(0 if failures.is_empty() else 1)
