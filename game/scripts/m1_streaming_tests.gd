extends SceneTree

# Cloud integration: actual native generation, collision, edit eviction/reload,
# cancellation and worker changes. Headless results do not qualify rendering.
var failures: Array[String] = []
var probe := CairnProbe.new()
var terrain: VoxelTerrain
var viewer: VoxelViewer

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for configuration: Vector2i in [Vector2i(32,1), Vector2i(16,1), Vector2i(32,2), Vector2i(16,2)]:
		probe.configure(configuration.y, false)
		terrain = VoxelTerrain.new()
		terrain.mesh_block_size = configuration.x
		terrain.generate_collisions = false
		terrain.bounds = AABB(Vector3(-1024,-16,-1024), Vector3(2048,48,2048))
		var generator := CairnFixture.new()
		terrain.generator = generator
		var library := VoxelBlockyLibrary.new()
		var cube := VoxelBlockyModelCube.new()
		cube.set_material_override(0, StandardMaterial3D.new())
		library.models = [VoxelBlockyModelEmpty.new(), cube, cube]
		library.bake()
		var mesher := CairnMesher.new()
		mesher.library = library
		for side: int in range(6): mesher.set_shadow_occluder_side(side, false)
		terrain.mesher = mesher
		root.add_child(terrain)
		viewer = VoxelViewer.new()
		viewer.view_distance = 48
		viewer.requires_collisions = false
		viewer.position = Vector3(0,2,0)
		root.add_child(viewer)
		var camera := Camera3D.new()
		camera.current = true
		camera.far = 32.0
		camera.position = Vector3(1,2,1)
		camera.rotation = Vector3(-0.18, -PI * 0.5, 0)
		root.add_child(camera)
		var surface_bounds := AABB(Vector3(-1024,-16,-1024), Vector3(2048,17,2048))
		var frontier: Dictionary = probe.sample_frontier(terrain, camera, surface_bounds)
		if frontier.get("status") != "measured" or int(frontier.get("unready_regions", 0)) == 0:
			failures.append("Unsubmitted terrain was reported ready")
		if not await _settle(): break
		for heading: float in [-PI * 0.5, PI * 0.5]:
			camera.rotation.y = heading
			frontier = probe.sample_frontier(terrain, camera, surface_bounds)
			if frontier.get("status") != "measured" or int(frontier.get("unready_regions", -1)) != 0 or int(frontier.get("empty_regions", 0)) == 0:
				failures.append("Submitted and confirmed-empty coverage failed across a camera reversal")
		camera.far = 2048.0
		if probe.sample_frontier(terrain, camera, surface_bounds)["status"] != "unavailable": failures.append("Frontier scan bound was not enforced")
		camera.far = 32.0
		if probe.sample_frontier(null, null, AABB())["status"] != "unavailable": failures.append("Missing frontier inputs became valid measurements")
		probe.start_edit_trace(true)
		var tool: VoxelTool = terrain.get_voxel_tool()
		tool.channel = VoxelBuffer.CHANNEL_TYPE
		var mover := VoxelBoxMover.new()
		var box := AABB(Vector3(-0.3,0,-0.3), Vector3(0.6,1.8,0.6))
		var motion: Vector3 = mover.get_motion(Vector3(1,2,1), Vector3(0,-4,0), box, terrain)
		if motion.y < -2.01 or motion.y > -1.9: failures.append("Voxel collision missed flat ground")
		# Coordinates touch both negative data/render seams and positive borders.
		var positions: Array[Vector3i] = [Vector3i(-1,0,0), Vector3i(0,0,0), Vector3i(31,0,0), Vector3i(32,0,0)]
		for position_value: Vector3i in positions:
			var accepted: bool = false
			for attempt: int in range(120):
				if generator.try_edit(terrain, position_value, 2):
					accepted = true
					break
				await process_frame
			if not accepted: failures.append("Border edit was not admitted")
			if not await _settle(): break
		probe.finish_edit_trace()
		var trace: Dictionary = probe.edit_trace_snapshot()
		var events: Array = probe.take_edit_events()
		if int(trace["accepted"]) != 4 or int(trace["submitted"]) != 4 or int(trace["overflow"]) != 0 or events.size() != 4:
			failures.append("Border edit mesh submissions were not completely observed")
		for event: Dictionary in events:
			if event["outcome"] != "submitted": failures.append("Border edit had no current mesh submission")
			var targets: Array = event["targets"]
			if targets.size() < 2: failures.append("Border edit did not update adjacent render meshes")
			for target: Dictionary in targets:
				if not target["submitted"] or int(target["revision"]) <= 0:
					failures.append("Border edit accepted a stale mesh revision")
		viewer.position = Vector3(400,2,0)
		if not await _settle(): break
		frontier = probe.sample_frontier(terrain, camera, surface_bounds)
		if frontier.get("status") != "measured" or int(frontier.get("unready_regions", 0)) == 0: failures.append("Evicted mesh coverage was reported ready")
		if tool.is_area_editable(AABB(Vector3(-1,0,0), Vector3(34,1,1))):
			failures.append("Eviction test did not unload edited data")
		viewer.position = Vector3(0,2,0)
		if not await _settle(): break
		for position_value: Vector3i in positions:
			if tool.get_voxel(position_value) != 2: failures.append("Edited data changed across eviction/reload")
		if not await _check_world_space_demand(configuration): break
		# Cancel with newly admitted generation outstanding, then drain before
		# changing the global worker count or creating the next world.
		viewer.position = Vector3(-400,2,0)
		await process_frame
		terrain.queue_free()
		viewer.queue_free()
		camera.queue_free()
		await process_frame
		if not await _drain(): break
		print("CAIRN_M1_STREAMING_PROFILE=" + str(configuration))
	if is_instance_valid(terrain): terrain.queue_free()
	if is_instance_valid(viewer): viewer.queue_free()
	await process_frame
	await _drain()
	print("CAIRN_M1_STREAMING=" + JSON.stringify({"passed": failures.is_empty(), "failures": failures}))
	quit(0 if failures.is_empty() else 1)

func _settle() -> bool:
	# Always advance engine processing after a viewer move before testing queues.
	for frame: int in range(3): await process_frame
	var start: int = Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 60000:
		var stats: Dictionary = terrain.get_statistics()
		var native_stats: Dictionary = probe.snapshot()
		if int(stats.get("resident_mesh", 0)) > 512 or int(stats.get("resident_data", 0)) > 8192 or int(native_stats["retired_meshes"]) > 768:
			failures.append("Viewer demand exceeded the existing resident/retirement caps")
			return false
		if int(native_stats["overloads"]) > 0:
			failures.append("Permitted fixture rejected by native admission")
			return false
		if int(stats.get("resident_data",0)) > 0 and int(stats.get("pending_data",1)) + int(stats.get("pending_mesh",1)) + int(stats.get("loading_data",1)) + int(native_stats["generation_jobs"]) + int(native_stats["mesh_jobs"]) + int(native_stats["result_jobs"]) + int(native_stats["main_jobs"]) == 0:
			return true
		await process_frame
	failures.append("Streaming did not settle within its timeout")
	return false

func _view_area(position_value: Vector3, distance: float) -> AABB:
	var area: AABB = AABB(position_value - Vector3.ONE * distance, Vector3.ONE * distance * 2.0).intersection(terrain.bounds)
	var first: Vector3 = area.position.floor()
	return AABB(first, area.end.ceil() - first)

func _mesh_cells(area: AABB, side: int) -> Array[Vector3i]:
	# Independent geometric oracle: enumerate a generous candidate range and
	# intersect each actual block box with the required world-space envelope.
	var first := Vector3i((area.position / float(side)).floor()) - Vector3i.ONE
	var last := Vector3i((area.end / float(side)).ceil()) + Vector3i.ONE
	var result: Array[Vector3i] = []
	for z: int in range(first.z, last.z):
		for y: int in range(first.y, last.y):
			for x: int in range(first.x, last.x):
				var cell := Vector3i(x, y, z)
				if AABB(Vector3(cell * side), Vector3.ONE * side).intersects(area): result.append(cell)
	return result

func _check_world_space_demand(configuration: Vector2i) -> bool:
	viewer.view_distance = 96
	var data_viewer := VoxelViewer.new()
	data_viewer.view_distance = 128
	data_viewer.requires_visuals = false
	data_viewer.requires_collisions = false
	data_viewer.position = viewer.position
	root.add_child(data_viewer)
	var passed: bool = true
	var tool: VoxelTool = terrain.get_voxel_tool()
	for pose: Vector3 in [Vector3(10.125,2,10.125), Vector3(31.875,2,31.875),
			Vector3(32,2,32), Vector3(-0.125,2,-0.125), Vector3(-1023.75,2,-1023.75)]:
		viewer.position = pose
		data_viewer.position = pose
		if not await _settle():
			passed = false
			break
		var visual_area: AABB = _view_area(pose, 96.0)
		var cells: Array[Vector3i] = _mesh_cells(visual_area, configuration.x)
		var stats: Dictionary = terrain.get_statistics()
		if not terrain.is_area_meshed(visual_area) or int(stats["resident_mesh"]) != cells.size():
			failures.append("World-space visual envelope was under-requested or retained extra blocks: " + str(configuration) + " " + str(pose))
			passed = false
		if not tool.is_area_editable(_view_area(pose, 128.0)):
			failures.append("Data-only viewer did not cover its world-space prefetch envelope")
			passed = false
		if pose == Vector3(10.125,2,10.125) and cells.size() != (507 if configuration.x == 16 else 98):
			failures.append("Fixture clipping or independent visual-demand oracle changed")
			passed = false
		print("CAIRN_M1_DEMAND=" + JSON.stringify({"profile": [configuration.x, configuration.y],
			"pose": [pose.x, pose.y, pose.z], "required_regions": cells.size(),
			"resident_mesh": stats["resident_mesh"], "resident_data": stats["resident_data"], "passed": passed}))
		if not passed: break
	data_viewer.queue_free()
	await process_frame
	if not passed: return false
	# Fresh demand with no data-only viewer proves the actual native meshing halo
	# is sufficient, rather than relying on the wider prefetch viewer to hide it.
	viewer.position = Vector3(400.125,2,400.125)
	if not await _settle(): return false
	var visual_area: AABB = _view_area(viewer.position, 96.0)
	var cells: Array[Vector3i] = _mesh_cells(visual_area, configuration.x)
	var first: Vector3i = cells[0]
	var last: Vector3i = first + Vector3i.ONE
	for cell: Vector3i in cells:
		first = first.min(cell)
		last = last.max(cell + Vector3i.ONE)
	var halo: AABB = AABB(Vector3(first * configuration.x) - Vector3.ONE * 16,
		Vector3((last - first) * configuration.x) + Vector3.ONE * 32).intersection(terrain.bounds)
	if not terrain.is_area_meshed(visual_area) or not tool.is_area_editable(halo):
		failures.append("Mesh-only demand did not load its complete clipped data halo")
		return false
	print("CAIRN_M1_DEMAND_HALO=" + str(configuration))
	return true

func _drain() -> bool:
	var start: int = Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 60000:
		var stats: Dictionary = probe.snapshot()
		if int(stats["generation_jobs"]) + int(stats["mesh_jobs"]) + int(stats["main_jobs"]) + int(stats["retired_meshes"]) == 0: return true
		await process_frame
	failures.append("Cancelled world did not drain")
	return false
