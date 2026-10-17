extends Node3D

# Actual submitted native meshes, not mocked frontier results. Isolates the
# public first boundary: not a full H1/H2 route or a performance observation.
const Preparation = preload("res://scripts/m1_frontier_preparation.gd")
const Frontier = preload("res://scripts/benchmark_frontier.gd")
const BEFORE := Vector3(15.9583473205566, 1.94999694824219, 10.0)
const CROSSED := Vector3(16.0666809082031, 1.66999685764313, 10.0)
const SURFACE := AABB(Vector3(-4096, -16, -4096), Vector3(8192, 23, 8192))
var directory: String = ""
var failures: Array[String] = []
var cases: Array[Dictionary] = []
var probe := CairnProbe.new()
var terrain: VoxelTerrain
var base: VoxelViewer
var data: VoxelViewer
var camera: Camera3D
var preparation: RefCounted
var peaks: Dictionary = {}
var environment := Environment.new()

func _ready() -> void: call_deferred("_run")

func fail(message: String) -> void:
	if not failures.has(message): failures.append(message)

func pose(value: Vector3) -> void:
	camera.position = value
	base.position = value - Vector3(0, 1.65, 0)
	data.position = base.position

func area(cell: Vector3i) -> AABB:
	return AABB(Vector3(cell * 16) + Vector3.ONE, Vector3.ONE * 14.0)

func observe(stage: String) -> Dictionary:
	var native: Dictionary = probe.snapshot()
	var stats: Dictionary = terrain.get_statistics()
	for key: String in ["resident_mesh", "resident_data", "pending_mesh", "pending_data", "loading_data"]:
		peaks[key] = maxi(int(peaks.get(key, 0)), int(stats.get(key, 0)))
	for key: String in ["generation_jobs", "mesh_jobs", "result_jobs", "main_jobs", "retired_meshes", "overloads"]:
		peaks[key] = maxi(int(peaks.get(key, 0)), int(native[key]))
	if int(stats["resident_mesh"]) > 512 or int(stats["resident_data"]) > 8192 or int(native["retired_meshes"]) > 768 or int(native["overloads"]) > 0:
		fail("Replay exceeded existing resident/retirement/admission bounds")
	var sample: Dictionary = probe.sample_frontier(terrain, camera, SURFACE)
	var assessment: Dictionary = Frontier.evaluate(sample, Frontier.fog_configuration(environment, camera.far))
	var ready: Array[bool] = []
	for cell: Vector3i in Preparation.cells(BEFORE - Vector3(0, 1.65, 0)):
		ready.append(terrain.is_area_meshed(area(cell)))
	return {"stage": stage, "usec": Time.get_ticks_usec(), "engine_frame": Engine.get_process_frames(),
		"camera": [camera.position.x, camera.position.y, camera.position.z], "yaw": camera.rotation.y,
		"base_pose": [base.position.x, base.position.y, base.position.z], "sample": sample,
		"assessment": assessment, "original_targets_submitted": ready,
		"preparation_cells": _preparation_cells(), "native": native, "terrain": stats}

func _preparation_cells() -> Array:
	var result: Array = []
	if preparation != null:
		for viewer: VoxelViewer in preparation.viewers:
			var cell := Vector3i((viewer.position / 16.0).floor())
			result.append([cell.x, cell.y, cell.z])
	return result

func settle() -> bool:
	for frame: int in range(3): await get_tree().process_frame
	var begin: int = Time.get_ticks_msec()
	while Time.get_ticks_msec() - begin < 60000:
		var row: Dictionary = observe("settlement-bound-check")
		var s: Dictionary = row["terrain"]
		var n: Dictionary = row["native"]
		if int(s["resident_data"]) > 0 and int(s["pending_data"]) + int(s["pending_mesh"]) + int(s["loading_data"]) + int(n["generation_jobs"]) + int(n["mesh_jobs"]) + int(n["result_jobs"]) + int(n["main_jobs"]) == 0: return true
		await get_tree().process_frame
	fail("Replay settlement timed out")
	return false

func drain() -> bool:
	for frame: int in range(3): await get_tree().process_frame
	var begin: int = Time.get_ticks_msec()
	while Time.get_ticks_msec() - begin < 60000:
		var n: Dictionary = probe.snapshot()
		if int(n["generation_jobs"]) + int(n["mesh_jobs"]) + int(n["result_jobs"]) + int(n["main_jobs"]) + int(n["retired_meshes"]) == 0: return true
		await get_tree().process_frame
	fail("Replay retirement timed out")
	return false

func create(enabled: bool, workers: int) -> void:
	probe.configure(workers, true)
	peaks.clear()
	terrain = VoxelTerrain.new()
	terrain.mesh_block_size = 16
	terrain.generate_collisions = false
	terrain.bounds = AABB(Vector3(-4096, -16, -4096), Vector3(8192, 48, 8192))
	terrain.max_view_distance = 128
	var generator := CairnFixture.new()
	generator.fixture = 1
	terrain.generator = generator
	var library := VoxelBlockyLibrary.new()
	var stone := VoxelBlockyModelCube.new()
	var grass := VoxelBlockyModelCube.new()
	var material := StandardMaterial3D.new()
	material.vertex_color_use_as_albedo = true
	stone.color = Color("78828b")
	grass.color = Color("90a86b")
	stone.set_material_override(0, material)
	grass.set_material_override(0, material)
	library.models = [VoxelBlockyModelEmpty.new(), stone, grass]
	library.bake()
	var mesher := CairnMesher.new()
	mesher.library = library
	for side: int in range(6): mesher.set_shadow_occluder_side(side, false)
	terrain.mesher = mesher
	add_child(terrain)
	base = VoxelViewer.new()
	base.view_distance = 96
	base.requires_collisions = false
	add_child(base)
	data = VoxelViewer.new()
	data.view_distance = 128
	data.requires_visuals = false
	data.requires_collisions = false
	add_child(data)
	camera = Camera3D.new()
	camera.current = true
	camera.far = 96.0
	camera.rotation = Vector3(-0.18, -1.57079637050629, 0)
	add_child(camera)
	pose(BEFORE)
	if enabled:
		preparation = Preparation.new()
		preparation.start(self, base.position)

func run_case(enabled: bool, workers: int) -> void:
	create(enabled, workers)
	var begin: int = Time.get_ticks_usec()
	var settled: bool = await settle()
	var rows: Array[Dictionary] = []
	rows.append(observe("prepared"))
	if not settled: fail("Replay did not prepare")
	if int(rows[0]["sample"].get("empty_regions", 0)) <= 0: fail("Confirmed-empty coverage was not exercised")
	pose(CROSSED)
	# No engine processing between this pose change and the first observation:
	# baseline has no target mesh; corrected has a truly submitted mesh already.
	rows.append(observe("crossed-before-engine"))
	var first: Dictionary = rows[-1]
	if enabled:
		if first["assessment"]["evaluation"] != "passed" or first["original_targets_submitted"].has(false): fail("Prepared boundary remained unready")
	else:
		if first["assessment"]["evaluation"] != "failed" or first["sample"].get("mesh_state") != "missing" or first["sample"].get("block") != [7, 0, 0]: fail("Baseline did not reproduce the missing boundary")
	for frame: int in range(16):
		if enabled: preparation.advance_process(base.position)
		await get_tree().process_frame
		rows.append(observe("handover-" + str(frame)))
		if enabled and (rows[-1]["original_targets_submitted"].has(false) or rows[-1]["assessment"]["evaluation"] != "passed"): fail("Base handover lost submitted coverage")
	if not await settle(): fail("Crossed boundary did not settle")
	rows.append(observe("crossed-settled"))
	if rows[-1]["assessment"]["evaluation"] != "passed" or rows[-1]["original_targets_submitted"].has(false): fail("Actual base demand never submitted the boundary")
	# Identical scan must still expose a new, deliberately unprepared column.
	pose(Vector3(48.5, CROSSED.y, 10.0))
	rows.append(observe("unprepared-failure-control"))
	if rows[-1]["assessment"]["evaluation"] != "failed": fail("Unprepared gap was hidden")
	# Give the newly moved base viewer an engine processing opportunity before
	# cancellation. Drain actual native work and renderer retirement, not only
	# script references; the existing streaming suite also cancels queued jobs.
	await get_tree().process_frame
	var cancellation_native: Dictionary = probe.snapshot()
	var cleanup_begin: int = Time.get_ticks_usec()
	var node_count: int = 0
	if preparation != null:
		node_count = preparation.viewers.size()
		preparation.dispose()
		if not preparation.viewers.is_empty(): fail("Preparation viewers not released")
		preparation = null
	terrain.queue_free()
	base.queue_free()
	data.queue_free()
	camera.queue_free()
	var drained: bool = await drain()
	cases.append({"name": ("corrected-" if enabled else "baseline-") + str(workers), "workers": workers,
		"enabled": enabled, "settled": settled, "drained": drained, "released_preparation_viewers": node_count,
		"policy": Preparation.metadata(enabled), "rows": rows, "peaks": peaks.duplicate(),
		"begin_usec": begin, "cleanup_begin_usec": cleanup_begin, "end_usec": Time.get_ticks_usec(),
		"cancellation_native": cancellation_native, "final_native": probe.snapshot(), "operation_evaluation": "unavailable: correctness replay; no operation performance qualification"})

func _run() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--frontier-output="): directory = arg.trim_prefix("--frontier-output=")
	if directory.is_empty():
		get_tree().quit(1)
		return
	Frontier.configure_m1_fog(environment)
	for side: int in [16, 32]:
		for workload: String in ["H1", "H2", "N1", "N2"]:
			for mode: String in ["full", "heavy-ab", "calibration", "explore"]:
				if Preparation.supported(side, workload, mode) != (side == 16 and workload in ["H1", "H2"] and mode != "explore"):
					fail("Preparation changed unsupported workloads")
	for workers: int in [1, 2]:
		await run_case(false, workers)
		await run_case(true, workers)
	var missing: Dictionary = Frontier.evaluate(probe.sample_frontier(null, null, AABB()), Frontier.fog_configuration(environment, 96.0))
	if missing["evaluation"] != "inconclusive" or missing["fog_clearance_m"] != null: fail("Unavailable frontier became a passing zero")
	var report: Dictionary = {"schema": 1, "version": Preparation.VERSION, "passed": failures.is_empty(), "failures": failures,
		"build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")), "qualified": false,
		"target_performance": "not_run", "cases": cases, "missing_input": missing,
		"fog": Frontier.fog_configuration(environment, 96.0), "row_cap": 128, "file_cap_bytes": 1048576,
		"scope": "public first 16³ +X boundary; native meshes and reference handover; no full route or GPU/target qualification"}
	var encoded: String = JSON.stringify(report)
	if encoded.to_utf8_buffer().size() > 1048576: fail("Replay file cap exceeded")
	else:
		var file := FileAccess.open(directory.path_join("summary.json"), FileAccess.WRITE)
		if file == null: fail("Replay report open failed")
		else:
			file.store_string(encoded)
			file.flush()
			if file.get_error() != OK: fail("Replay report write failed")
			file.close()
	print("CAIRN_FRONTIER_BOUNDARY=" + encoded)
	get_tree().quit(0 if failures.is_empty() else 1)
