extends "res://scripts/benchmark.gd"

# Cloud-only observation of the production H2 commands, never a target profile.
const TRAVEL_TICKS: int = 600
const OBSERVATION_CAP: int = 4096
const OBSERVATION_BYTES: int = 33554432
var observations: FileAccess
var observation_rows: int = 0
var observation_bytes: int = 0
var observed_tick: int = -1
var edit_attempt: Dictionary = {}
var phase_guards: Array[Dictionary] = []
var observation_failure: bool = false

func _ready() -> void:
	test_mode = true
	mode = "travel-replay"
	render_size = 16
	scenarios = [{"id": "AB-H2-travel", "workload": "H2", "seconds": 10.0,
		"fixture": 1, "actors": 24, "rate": 4.0, "frontier_enabled": true}]
	super._ready()
	startup.stop(Time.get_ticks_usec(), "separate continuous H2 cloud replay")
	_disconnect_startup_signals()
	observations = FileAccess.open(report_dir.path_join("travel-observations.jsonl"), FileAccess.WRITE)
	if observations == null: observation_failure = true

func _duration() -> float:
	return float(TRAVEL_TICKS) / 60.0

func _edit_border(tool: VoxelTool) -> bool:
	var position_value := Vector3i(int(round(player.x / 32.0)) * 32, 6, int(floor(player.z)) + 3)
	var coordinates: Array = [Vector3i(position_value.x / 16 - 1, 0, 0), Vector3i(position_value.x / 16, 0, 0)]
	var before: Dictionary = probe.sample_mesh_blocks(terrain, coordinates)
	var begin: int = Time.get_ticks_usec()
	var accepted: bool = super._edit_border(tool)
	var end: int = Time.get_ticks_usec()
	edit_attempt = {"voxel": [position_value.x, position_value.y, position_value.z],
		"accepted": accepted, "begin_usec": begin, "end_usec": end,
		"before": before, "after": probe.sample_mesh_blocks(terrain, coordinates)}
	return accepted

func _physics_step(delta: float) -> void:
	var before: int = simulation_ticks
	edit_attempt = {}
	super._physics_step(delta)
	if simulation_ticks != before: _observe("physics")

func _process_frame(now: int) -> void:
	# Observe before the production callback can begin asynchronous closure.
	if state in ["running", "acknowledging"]:
		var boundary: bool = false
		for tick: int in [56, 204, 351, 499]:
			if absi(simulation_ticks - tick) <= 4: boundary = true
		if observed_tick != simulation_ticks or boundary or state == "acknowledging":
			_observe("process")
			observed_tick = simulation_ticks
	super._process_frame(now)

func _observe(stage: String) -> void:
	if observation_failure: return
	var current: Array[Vector3i] = FrontierPreparation.cells(player)
	var coordinates: Array = []
	for cell: Vector3i in current: coordinates.append(cell - Vector3i(1, 0, 0))
	coordinates.append_array(current)
	# All three production border-edit positions stay inside the data/visual halo.
	for x: int in [-1, 0, 1, 2, 3, 4]: coordinates.append(Vector3i(x, 0, 0))
	coordinates.append(Vector3i(0, 1, 0))
	var preparations: Array = []
	for owner: VoxelViewer in frontier_preparation.viewers:
		preparations.append([owner.position.x, owner.position.y, owner.position.z])
	var row: Dictionary = {"row": observation_rows + 1, "stage": stage, "state": state,
		"usec": Time.get_ticks_usec(), "engine_frame": Engine.get_process_frames(),
		"tick": simulation_ticks, "player": [player.x, player.y, player.z],
		"camera": [camera.position.x, camera.position.y, camera.position.z], "yaw": camera.rotation.y,
		"target": [_route_target().x, _route_target().y, _route_target().z],
		"actors": actor_ticks, "actor_phase": actor_phase, "rain": rain.multimesh.instance_count,
		"accepted": accepted_edits, "rejected": rejected_edits, "next_edit": next_edit,
		"saves": proxy_saves, "next_save": next_proxy_save, "command_hash": command_hash,
		"readiness_stops": readiness_stops, "preparation_positions": preparations,
		"native": probe.snapshot(), "terrain": terrain.get_statistics(),
		"trace": probe.edit_trace_snapshot(), "meshes": probe.sample_mesh_blocks(terrain, coordinates),
		"edit_attempt": edit_attempt if stage == "physics" else {}}
	var encoded: String = JSON.stringify(row) + "\n"
	var size: int = encoded.to_utf8_buffer().size()
	if observations == null or observation_rows >= OBSERVATION_CAP or observation_bytes + size > OBSERVATION_BYTES:
		observation_failure = true
		return
	observations.store_string(encoded)
	observation_rows += 1
	observation_bytes += size
	if observations.get_error() != OK: observation_failure = true

func _close_phase() -> Dictionary:
	var before: int = Time.get_ticks_usec()
	var result: Dictionary = super._close_phase()
	if not result.is_empty():
		phase_guards.append({"id": result["id"], "phase": result["phase"],
			"close_before_usec": before, "close_after_usec": Time.get_ticks_usec(),
			"failures": Evaluation.operation_failures(result)})
	return result

func _finish_report(outcome: String, message: String) -> void:
	if observations != null:
		observations.flush()
		observation_failure = observation_failure or observations.get_error() != OK
		observations.close()
	if observation_failure: integration_failures.append("Continuous travel observation I/O or bound failed")
	await super._finish_report(outcome, message)
	var final_native: Dictionary = probe.snapshot()
	var drained: bool = true
	for key: String in ["generation_jobs", "mesh_jobs", "result_jobs", "main_jobs", "retired_meshes"]:
		if int(final_native[key]) != 0: drained = false
	if not drained: integration_failures.append("Continuous travel native retirement did not drain")
	var result: Dictionary = {"version": "m1-frontier-travel-1", "build": build_info,
		"passed": outcome == "completed" and integration_failures.is_empty(), "qualified": false,
		"target_performance": "not_run", "failures": integration_failures,
		"ticks": TRAVEL_TICKS, "row_cap": OBSERVATION_CAP, "byte_cap": OBSERVATION_BYTES,
		"rows": observation_rows, "bytes": observation_bytes, "phase_guards": phase_guards,
		"drained": drained, "final_native": final_native,
		"scope": "continuous production H2 commands; synchronous cloud observations perturb timing; no overhead/target qualification"}
	var file := FileAccess.open(report_dir.path_join("travel-summary.json"), FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(result, "  "))
		file.flush()
		if file.get_error() != OK: integration_failures.append("Travel summary write failed")
		file.close()
	else: integration_failures.append("Travel summary unavailable")
	print("CAIRN_FRONTIER_TRAVEL=" + JSON.stringify(result))
