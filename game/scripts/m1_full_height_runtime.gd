extends "res://scripts/benchmark.gd"

# A separate full-height experiment; legacy H1/H2 commands/fixtures are unchanged.
const FULL_ORIGIN := Vector3(10, 72, 10)
const FULL_ID: String = "AB-H2-full-height"
const TICKS: int = 4320
const OBSERVATION_CAP: int = 4322
const OBSERVATION_BYTES: int = 16777216
var preparation_enabled: bool = false
var preparation: VoxelViewer
var previous_pose := FULL_ORIGIN
var previous_tick: int = 0
var source_pose := FULL_ORIGIN
var source_tick: int = 0
var preparation_direction: int = 0
var preparation_decision_tick: int = 0
var phase_guards: Array[Dictionary] = []
var observations: FileAccess
var observation_rows: int = 0
var observation_bytes: int = 0
var observation_failed: bool = false
var policy_failed: bool = false
var full_command_hash: int = 0

func _ready() -> void:
	test_mode = true
	mode = "full-height"
	render_size = 32
	preparation_enabled = "--directional-preparation" in OS.get_cmdline_user_args()
	scenarios = [{"id": FULL_ID, "workload": "H2", "seconds": 72.0,
		"fixture": 3, "actors": 24, "rate": 4.0, "frontier_enabled": true}]
	super._ready()
	startup.stop(Time.get_ticks_usec(), "separate full-height movement experiment")
	_disconnect_startup_signals()
	observations = FileAccess.open(report_dir.path_join("full-height-observations.jsonl"), FileAccess.WRITE)
	if observations == null: observation_failed = true
	if render_size != 32 or workers != 1: integration_failures.append("Full-height proof requires 32-cube / one worker")

func _terrain_bounds() -> AABB:
	return AABB(Vector3(-4096, -64, -4096), Vector3(8192, 256, 8192))

func _duration() -> float:
	return 72.0

func _leg(tick: int) -> int:
	return mini(2, maxi(0, tick - 1) / 1440)

func _direction(leg: int) -> Vector3:
	return [Vector3.RIGHT, Vector3.LEFT, Vector3.BACK][leg]

func _create_terrain(fixture: int) -> void:
	route_origin = FULL_ORIGIN
	player = route_origin
	super._create_terrain(fixture)
	if preparation_enabled:
		preparation = VoxelViewer.new()
		preparation.view_distance = 96
		preparation.requires_collisions = false
		preparation.position = player + Vector3.RIGHT * 32.0
		add_child(preparation)

func _route_target() -> Vector3:
	if simulation_ticks <= 1440:
		return FULL_ORIGIN + Vector3(6.5 * scenario_elapsed, 0, 0)
	if simulation_ticks <= 2880:
		return FULL_ORIGIN + Vector3(156.0 - 6.5 * (scenario_elapsed - 24.0), 0, 0)
	return FULL_ORIGIN + Vector3(0, 0, 6.5 * (scenario_elapsed - 48.0))

func _sync_pose(reset_angles: bool = false) -> void:
	super._sync_pose(reset_angles)
	camera.rotation.y = [-PI * 0.5, PI * 0.5, PI][_leg(simulation_ticks)]

func _policy(enabled: bool) -> void:
	if is_instance_valid(terrain) and not probe.set_mesh_admission(terrain, enabled, camera.position, false):
		policy_failed = true

func _begin_phase(label: String, trace: bool = true) -> void:
	super._begin_phase(label, trace)
	_policy(label == "overhead_diagnostic")
	if label == "overhead_diagnostic": _observe("prepared")
	if label == "retirement" and is_instance_valid(preparation): preparation.queue_free()

func _scan_frontier() -> Dictionary:
	return probe.sample_frontier(terrain, camera, _terrain_bounds())

func _capture_workload_contract() -> Dictionary:
	var result: Dictionary = super._capture_workload_contract()
	result["version"] = "m1-full-height-1"
	result["route"] = "+X 156 m; -X 156 m; +Z 156 m; 6.5 m/s; 1440 ticks per leg"
	result["admission_policy"] = "priority"
	result["admission_trace"] = false
	result["full_height_observation"] = true
	result["frontier_preparation"] = {"version": "m1-directional-32-1", "enabled": preparation_enabled,
		"viewer_count": 1 if preparation_enabled else 0, "viewer_radius_m": 96,
		"lead_m": 32, "required_visual_radius_m": 96, "data_radius_m": 128,
		"handover": "previous process pose; next movement leg", "resident_mesh_bound": 448 if preparation_enabled else 343,
		"data_scope": "128 m base data viewer plus measured mesh halo/preparation union"}
	return result

func _physics_step(delta: float) -> void:
	var before: int = simulation_ticks
	super._physics_step(delta)
	if simulation_ticks == before: return
	_policy(true)
	var target: Vector3 = _route_target()
	full_command_hash = (full_command_hash * 65599 + simulation_ticks + int(round(target.x * 1000.0)) +
		int(round(target.z * 1000.0)) * 31 + _leg(simulation_ticks) * 17) & 0x7fffffff
	if player.y < 63.99 or player.y > 72.01:
		integration_failures.append("Full-height player left the supported surface")
	_observe("physics")

func _process_frame(now: int) -> void:
	if state in ["running", "acknowledging"]:
		if is_instance_valid(preparation):
			# One process opportunity retains old ownership until the base viewer moves.
			source_pose = previous_pose
			source_tick = previous_tick
			preparation_direction = _leg(mini(TICKS, simulation_ticks + 1))
			preparation_decision_tick = simulation_ticks
			preparation.position = source_pose + _direction(preparation_direction) * 32.0
			previous_pose = player
			previous_tick = simulation_ticks
		_policy(true)
	super._process_frame(now)

func _edit_border(tool: VoxelTool) -> bool:
	# Eleven distinct coordinates cover both travel axes without raising the 64-edit overlay cap.
	var position_value := Vector3i(int(round(player.x / 32.0)) * 32, 70, int(round(player.z / 32.0)) * 32 + 13)
	if not tool.is_area_editable(AABB(Vector3(position_value) - Vector3.ONE, Vector3.ONE * 3.0)):
		rejected_edits += 1
		return false
	tool.channel = VoxelBuffer.CHANNEL_TYPE
	var old: int = tool.get_voxel(position_value)
	if edit_positions.size() >= 64 and not position_value in edit_positions:
		rejected_edits += 1
		return false
	if not position_value in edit_positions:
		edit_positions.append(position_value)
		edit_originals.append(old)
	var generator: CairnFixture = terrain.generator
	var value: int = 2 if old == 0 else 0
	if generator.try_edit(terrain, position_value, value):
		accepted_edits += 1
		expected_edits[position_value] = value
		return true
	rejected_edits += 1
	return false

func _area(pose: Vector3, radius: float) -> AABB:
	return AABB(pose - Vector3.ONE * radius, Vector3.ONE * radius * 2.0).intersection(_terrain_bounds())

func _observe(stage: String) -> void:
	if observation_failed: return
	var tool: VoxelTool = terrain.get_voxel_tool()
	tool.channel = VoxelBuffer.CHANNEL_TYPE
	var origin_ready: bool = tool.is_area_editable(AABB(Vector3(0,70,13), Vector3.ONE))
	var target: Vector3 = _route_target()
	var row: Dictionary = {"row": observation_rows + 1, "stage": stage, "usec": Time.get_ticks_usec(),
		"tick": simulation_ticks, "leg": _leg(simulation_ticks), "player": [player.x, player.y, player.z],
		"target": [target.x, target.y, target.z], "camera": [camera.position.x,camera.position.y,camera.position.z],
		"yaw": camera.rotation.y, "actors": actor_ticks, "accepted": accepted_edits, "rejected": rejected_edits,
		"saves": proxy_saves, "command_hash": full_command_hash, "readiness_stops": readiness_stops,
		"native": probe.snapshot(), "terrain": terrain.get_statistics(),
		"origin_data_ready": origin_ready, "origin_value": tool.get_voxel(Vector3i(0,70,13)) if origin_ready else null,
		"meshes": probe.sample_mesh_blocks(terrain, [Vector3i(0,1,0), Vector3i(0,2,0), Vector3i(5,1,0), Vector3i(0,1,5)]),
		"preparation": {"positions": [[preparation.position.x,preparation.position.y,preparation.position.z]] if is_instance_valid(preparation) else [],
			"source_tick": source_tick, "decision_tick": preparation_decision_tick,
			"source_player": [source_pose.x,source_pose.y,source_pose.z], "direction": preparation_direction}}
	if stage == "prepared":
		row["visual_area_ready"] = terrain.is_area_meshed(_area(player,96))
		row["data_area_ready"] = tool.is_area_editable(_area(player,128))
		row["preparation_area_ready"] = terrain.is_area_meshed(_area(preparation.position,96)) if is_instance_valid(preparation) else null
		row["vertical_voxels"] = []
		for y: int in [-64,-32,40,63,64,191]: row["vertical_voxels"].append([y,tool.get_voxel(Vector3i(10,y,10))])
	var encoded: String = JSON.stringify(row) + "\n"
	var size: int = encoded.to_utf8_buffer().size()
	if observations == null or size > 16384 or observation_rows >= OBSERVATION_CAP or observation_bytes + size > OBSERVATION_BYTES:
		observation_failed = true
		return
	observations.store_string(encoded)
	observation_rows += 1
	observation_bytes += size
	if observations.get_error() != OK: observation_failed = true

func _end_scenario() -> void:
	_observe("terminal")
	super._end_scenario()

func _close_phase() -> Dictionary:
	_policy(false)
	var before: int = Time.get_ticks_usec()
	var result: Dictionary = super._close_phase()
	if not result.is_empty():
		phase_guards.append({"id": result["id"], "phase": result["phase"], "close_before_usec": before,
			"close_after_usec": Time.get_ticks_usec(), "failures": Evaluation.operation_failures(result)})
	return result

func _finish_report(outcome: String, message: String) -> void:
	var finalize_begin: int = Time.get_ticks_usec()
	if observations != null:
		observations.flush()
		observation_failed = observation_failed or observations.get_error() != OK
		observations.close()
	var finalize_end: int = Time.get_ticks_usec()
	if observation_failed: integration_failures.append("Full-height observation I/O or bound failed")
	if policy_failed: integration_failures.append("Full-height native priority policy rejected")
	await super._finish_report(outcome, message)
	var final_native: Dictionary = probe.snapshot()
	var drained: bool = true
	for key: String in ["generation_jobs", "mesh_jobs", "result_jobs", "main_jobs", "retired_meshes"]:
		if int(final_native[key]) != 0: drained = false
	var result: Dictionary = {"version": "m1-full-height-1", "build": build_info,
		"passed": outcome == "completed" and integration_failures.is_empty() and drained, "qualified": false,
		"target_performance": "not_run", "preparation_enabled": preparation_enabled, "priority": true,
		"phase_guards": phase_guards, "drained": drained, "final_native": final_native,
		"native_trace_state": probe.mesh_admission_snapshot(), "distinct_edit_positions": edit_positions.size(),
		"rows": observation_rows, "bytes": observation_bytes, "row_cap": OBSERVATION_CAP, "byte_cap": OBSERVATION_BYTES,
		"observer_finalization": {"start_usec": finalize_begin, "end_usec": finalize_end},
		"scope": "full-height/directional cloud experiment; observer perturbs timing; no target or overhead qualification"}
	var file := FileAccess.open(report_dir.path_join("full-height-summary.json"), FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(result, "  "))
		file.flush()
		if file.get_error() != OK: integration_failures.append("Full-height summary write failed")
		file.close()
	else: integration_failures.append("Full-height summary unavailable")
	result["passed"] = bool(result["passed"]) and integration_failures.is_empty()
	print("CAIRN_FULL_HEIGHT=" + JSON.stringify(result))
