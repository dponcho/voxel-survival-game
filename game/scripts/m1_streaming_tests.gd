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
		if not await _settle(): break
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
		viewer.position = Vector3(400,2,0)
		if not await _settle(): break
		if tool.is_area_editable(AABB(Vector3(-1,0,0), Vector3(34,1,1))):
			failures.append("Eviction test did not unload edited data")
		viewer.position = Vector3(0,2,0)
		if not await _settle(): break
		for position_value: Vector3i in positions:
			if tool.get_voxel(position_value) != 2: failures.append("Edited data changed across eviction/reload")
		# Cancel with newly admitted generation outstanding, then drain before
		# changing the global worker count or creating the next world.
		viewer.position = Vector3(-400,2,0)
		await process_frame
		terrain.queue_free()
		viewer.queue_free()
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
		if int(native_stats["overloads"]) > 0:
			failures.append("Permitted fixture rejected by native admission")
			return false
		if int(stats.get("resident_data",0)) > 0 and int(stats.get("pending_data",1)) + int(stats.get("pending_mesh",1)) + int(stats.get("loading_data",1)) + int(native_stats["generation_jobs"]) + int(native_stats["mesh_jobs"]) + int(native_stats["main_jobs"]) == 0:
			return true
		await process_frame
	failures.append("Streaming did not settle within its timeout")
	return false

func _drain() -> bool:
	var start: int = Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 60000:
		var stats: Dictionary = probe.snapshot()
		if int(stats["generation_jobs"]) + int(stats["mesh_jobs"]) + int(stats["main_jobs"]) + int(stats["retired_meshes"]) == 0: return true
		await process_frame
	failures.append("Cancelled world did not drain")
	return false
