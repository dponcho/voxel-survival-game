extends RefCounted

const HeavyAB = preload("res://scripts/benchmark_heavy_ab.gd")
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")
const Diagnostics = preload("res://scripts/benchmark_diagnostics.gd")
const Frontier = preload("res://scripts/benchmark_frontier.gd")

# Observe actual runtime dispatch and preparation; do not infer a switch from
# report labels. The export smoke separately exercises real terrain/physics/I/O.
class Harness extends "res://scripts/benchmark.gd":
	var scans: int = 0
	var heavy_budget: bool = false
	var phase_label: String = ""
	func _ready() -> void: pass
	func _open_reports(_suffix: String = "") -> void: pass
	func _begin_phase(label: String, _trace: bool = true) -> void: phase_label = label
	func _configure_terrain_budget(heavy: bool) -> void: heavy_budget = heavy
	func _create_terrain(fixture: int) -> void:
		if terrain == null:
			terrain = VoxelTerrain.new()
			viewer = VoxelViewer.new()
			data_viewer = VoxelViewer.new()
			add_child(terrain)
			add_child(viewer)
			add_child(data_viewer)
		var generator := CairnFixture.new()
		generator.fixture = fixture
		terrain.generator = generator
	func _scan_frontier() -> Dictionary:
		scans += 1
		return {"status": "measured", "candidate_regions": 4, "checked_regions": 4,
			"ready_regions": 3, "empty_regions": 1, "unready_regions": 1,
			"frontier_distance_m": 95.0, "probe_usec": 0}

static func verify_runtime(tree: SceneTree) -> Array[String]:
	var failures: Array[String] = []
	var fixture := Harness.new()
	tree.root.add_child(fixture)
	fixture.set_process(false)
	fixture.set_physics_process(false)
	fixture._make_scene()
	fixture.status_label = Label.new()
	fixture.detail_label = Label.new()
	fixture.add_child(fixture.status_label)
	fixture.add_child(fixture.detail_label)
	fixture.scenarios = HeavyAB.scenarios({"id": "warmup", "seconds": 180.0, "fixture": 0, "actors": 12, "rate": 0.0})
	for index: int in range(1, 9):
		fixture.scenario_index = index
		fixture._start_scenario()
		var h2: bool = index >= 5
		if not fixture.heavy_budget or fixture.phase_label != "preparation" or fixture.terrain.generator.fixture != 1 or fixture.rain.visible != h2 or fixture.actor_instances.multimesh.visible_instance_count != (24 if h2 else 12):
			failures.append("Matched preparation changed fixture/rain/actors/heavy admission")
		for seconds: float in [0.0, 15.0, 30.0]:
			fixture.scenario_elapsed = seconds
			fixture._sync_pose()
			var target: Vector3 = fixture._route_target()
			var expected_x: float = 10.0 if seconds == 0.0 else (107.5 if seconds == 15.0 else 205.0)
			if target != Vector3(expected_x, 8, 10) or not is_equal_approx(fixture.camera.rotation.y, PI * 0.5 if seconds == 15.0 else -PI * 0.5):
				failures.append("Matched runtime used the flat route or lost the 15-second reversal")
		fixture.diagnostics = Diagnostics.new()
		fixture.frontier = Frontier.new()
		var calls: int = fixture.scans
		var sample: Dictionary = fixture._frontier_sample()
		var enabled: bool = index in [2, 3, 6, 7]
		if fixture.scans - calls != (1 if enabled else 0) or fixture.diagnostics.switched_calls != (1 if enabled else 0):
			failures.append("Disabled baseline still dispatched the frontier scan")
		if enabled and sample["evaluation"] != "failed": failures.append("Switched scan concealed existing analytic coverage failure")
		if not enabled and (sample["status"] != "unavailable" or Frontier.csv_fields(sample)[6] != "unavailable"):
			failures.append("Disabled probe fabricated coverage distance")
		fixture.state = "running"
		fixture.simulation_ticks = 1800
		fixture.scenario_elapsed = 30.0
		fixture._physics_step(1.0 / 60.0)
		if fixture.simulation_ticks != 1800 or fixture.scenario_elapsed != 30.0:
			failures.append("Matched endpoint added extra physics ticks")
	fixture.free()
	return failures

static func _phases(workload: String, enabled_usec: int = 30150000) -> Array[Dictionary]:
	var phases: Array[Dictionary] = []
	var actors: int = 24 if workload == "H2" else 12
	var contract: Dictionary = {"workload": workload, "fixture": 1, "actors": actors,
		"edit_rate": 4.0 if workload == "H2" else 0.0, "rain_instances": 256 if workload == "H2" else 0,
		"physics_hz": 60, "max_physics_steps": 4, "edit_trace": workload == "H2", "resolution": [1280, 720], "render_scale": 1.0,
		"visual_radius": 96, "data_radius": 128, "triangle_colliders": false, "render_block": 32, "workers": 1,
		"native_policy": {"frame_usec": 2000, "frame_upload_bytes": 1048576, "single_upload_bytes": 262144,
			"terrain_jobs": 64, "mesh_results": 16, "mesh_result_bytes": 33554432}}
	for repetition: String in ["off-1", "on-1", "on-2", "off-2"]:
		var enabled: bool = repetition.begins_with("on")
		var blocks: Array[Dictionary] = []
		for i: int in range(6): blocks.append({"samples": 1000, "usec": 5000000})
		phases.append({"id": "AB-" + workload + "-" + repetition, "workload": workload,
			"frontier_enabled": enabled, "completed": true, "samples": 6000, "simulated_seconds": 30.0,
			"wall_seconds": 30.0, "readiness_stops": 0, "actor_ticks": actors * 1800, "simulation_ticks": 1800,
			"travelled_distance_m": 195.0, "accepted_proxy_edits": 120 if workload == "H2" else 0,
			"rejected_proxy_edits": 0, "proxy_autosaves": 30 if workload == "H2" else 0,
			"workload_contract": contract.duplicate(true), "workload_evidence": {"command_hash": 123, "route_checkpoints": []},
			"operation_phase": {"tracing": true}, "edit_visibility": {"enabled": false, "accepted": 120 if workload == "H2" else 0},
			"fog_frontier": {"samples": 6000, "invalid_samples": 0} if enabled else Frontier.new().snapshot(true, false),
			"evaluation": "inconclusive", "diagnostic_accounting": {"callbacks": 6000, "overflow": false,
				"switched_calls": 6000 if enabled else 0, "switched_usec": 6000 if enabled else 0, "invalid_partition": false,
				"elapsed_usec": enabled_usec if enabled else 30000000, "blocks": blocks}})
	return phases

static func verify() -> Array[String]:
	var failures: Array[String] = []
	var ledger := Diagnostics.new()
	ledger.start(100)
	ledger.record_callback(120, 180, 10)
	ledger.record_callback(200, 300, 25)
	var accounting: Dictionary = ledger.snapshot(450, 80)
	if accounting["switched_usec"] != 35 or accounting["shared_usec"] != 125 or accounting["last_shared_usec"] != 75 or accounting["finalization_usec"] != 150 or accounting["invalid_partition"]:
		failures.append("Nested probe/shared callback/finalization costs were added or lost")
	ledger.record_callback(500, 510, 11)
	if not ledger.snapshot(600, 0)["invalid_partition"]: failures.append("Impossible nested timing partition was accepted")
	for workload: String in ["H1", "H2"]:
		# Independent arithmetic: 150000 / 30000000 = 0.5%; 600000 = 2%.
		for test: Dictionary in [{"usec": 30150000, "outcome": "passed"}, {"usec": 30600000, "outcome": "failed"},
			{"usec": 30300000, "outcome": "failed"}, {"usec": 29400000, "outcome": "inconclusive"}]:
			var result: Dictionary = Evaluation.heavy_diagnostic_ab(_phases(workload, test["usec"]), false, false)
			if result["workloads"][workload]["outcome"] != test["outcome"] or result["qualified"] or result["total_overhead"]["outcome"] != "inconclusive" or result["total_overhead"]["added_fraction"] != null:
				failures.append("Heavy cost classification or shared-overhead scope is incorrect")
		var decoded: Array[Dictionary] = []
		for report: Dictionary in JSON.parse_string(JSON.stringify(_phases(workload))): decoded.append(report)
		if Evaluation.heavy_diagnostic_ab(decoded, false, false)["workloads"][workload]["outcome"] != "passed":
			failures.append("JSON numeric types changed heavy comparison eligibility")
		for label: String in ["missing", "reordered", "fixture", "radius", "workers", "cap", "ticks", "actors", "route", "probe off", "probe on", "unavailable", "zero coverage", "coverage failure", "operation failure", "stall", "block drift", "repeat drift", "threshold overlap", "overflow", "storage", "edits", "shared edit trace"]:
			var phases: Array[Dictionary] = _phases(workload)
			match label:
				"missing": phases.pop_back()
				"reordered": phases.reverse()
				"fixture": phases[2]["workload_contract"]["fixture"] = 0
				"radius": phases[2]["workload_contract"]["visual_radius"] = 80
				"workers": phases[2]["workload_contract"]["workers"] = 2
				"cap": phases[2]["workload_contract"]["native_policy"]["frame_usec"] = 1000
				"ticks": phases[2]["simulation_ticks"] = 1801
				"actors": phases[2]["actor_ticks"] -= 1
				"route": phases[2]["workload_evidence"]["command_hash"] += 1
				"probe off": phases[0]["diagnostic_accounting"]["switched_calls"] = 1
				"probe on": phases[1]["diagnostic_accounting"]["switched_calls"] = 0
				"unavailable": phases[1]["fog_frontier"]["invalid_samples"] = 1
				"zero coverage": phases[0]["fog_frontier"]["minimum_frontier_distance_m"] = 0.0
				"coverage failure", "operation failure": phases[1]["evaluation"] = "failed"
				"stall": phases[1]["wall_seconds"] = 31.0
				"block drift": phases[1]["diagnostic_accounting"]["blocks"][0]["usec"] = 5100000
				"repeat drift": phases[3]["diagnostic_accounting"]["elapsed_usec"] = 31000000
				"threshold overlap":
					phases[1]["diagnostic_accounting"]["elapsed_usec"] = 30270000
					phases[2]["diagnostic_accounting"]["elapsed_usec"] = 30330000
				"overflow": phases[1]["diagnostic_accounting"]["overflow"] = true
				"storage": phases[2]["proxy_autosaves"] += 1
				"edits": phases[2]["rejected_proxy_edits"] = 1
				"shared edit trace": phases[2]["operation_phase"]["tracing"] = false
			if Evaluation.heavy_diagnostic_ab(phases, false, false)["workloads"][workload]["outcome"] != "inconclusive":
				failures.append("Invalid matched comparison accepted: " + workload + " " + label)
		if Evaluation.heavy_diagnostic_ab(_phases(workload), true, false)["workloads"][workload]["outcome"] != "inconclusive" or Evaluation.heavy_diagnostic_ab(_phases(workload), false, true)["workloads"][workload]["outcome"] != "inconclusive":
			failures.append("Smoke or failed I/O qualified heavy overhead")
	return failures

# Read the actual persisted summary, not only its in-memory predecessor. Existing
# CSV verifiers reconcile phase/lifetime counts, coverage and final callback sums.
static func verify_saved(directory: String) -> Array[String]:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("summary.json")))
	if not parsed is Dictionary: return ["Missing saved diagnostic summary"]
	var saved: Dictionary = parsed
	var reports: Array[Dictionary] = []
	var phases: Array[Dictionary] = []
	for report: Dictionary in saved["scenarios"]: reports.append(report)
	for phase: Dictionary in saved["operation_phases"]: phases.append(phase)
	var failures: Array[String] = load("res://scripts/benchmark_trace_tests.gd").verify(directory, phases, reports)
	if saved["benchmark_mode"] != "heavy-ab": return failures
	if reports.size() != 9 or phases.size() != 27: failures.append("Heavy preparation/measurement/retirement evidence is incomplete")
	for workload: String in ["H1", "H2"]:
		var selected: Array[Dictionary] = []
		for report: Dictionary in reports:
			if report["workload"] == workload: selected.append(report)
		failures.append_array(Evaluation.heavy_workload_failures(selected, workload, true))
		var comparison: Dictionary = saved["diagnostic_heavy_ab"]["workloads"][workload]
		if comparison["outcome"] != "inconclusive": failures.append("Saved heavy smoke comparison qualified overhead")
		for report: Dictionary in selected:
			var id: String = report["id"]
			var labels: Array[String] = []
			for phase: Dictionary in phases:
				if phase["scenario"] == id: labels.append(phase["phase"])
			if labels != ["preparation", "overhead_diagnostic", "retirement"]: failures.append("Heavy phases were merged or omitted")
			var points: Array = report["workload_evidence"]["route_checkpoints"]
			if points.size() != 2 or int(points[0]["tick"]) != 1 or int(points[1]["tick"]) != 60 or absf(float(points[1]["target_x"]) - 16.5) > 0.00001:
				failures.append("Saved heavy commands used a shortened/flat route")
			var accounting: Dictionary = report["diagnostic_accounting"]
			if int(accounting["last_callback_end_usec"]) > int(report["measurement_end_usec"]) or int(accounting["end_usec"]) < int(report["measurement_end_usec"]):
				failures.append("Final callback/report assembly crossed the measured boundary")
	return failures
