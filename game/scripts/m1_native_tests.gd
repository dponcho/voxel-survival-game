extends SceneTree

var failures: Array[String] = []
var reference := VoxelMesherBlocky.new()

func _initialize() -> void:
	_check_evaluation()
	failures.append_array(await load("res://scripts/benchmark_diagnostic_tests.gd").verify_flush(process_frame))
	failures.append_array(await load("res://scripts/benchmark_lifecycle_tests.gd").verify(self))
	var library := VoxelBlockyLibrary.new()
	var cube := VoxelBlockyModelCube.new()
	var material := StandardMaterial3D.new()
	cube.set_material_override(0, material)
	var colored_cube := VoxelBlockyModelCube.new()
	colored_cube.color = Color(0.2, 0.6, 0.9)
	colored_cube.set_material_override(0, material)
	library.models = [VoxelBlockyModelEmpty.new(), cube, colored_cube]
	library.bake()
	var mesher := CairnMesher.new()
	mesher.library = library
	reference.library = library
	for side: int in range(6): mesher.set_shadow_occluder_side(side, false)
	for side: int in range(6): reference.set_shadow_occluder_side(side, false)
	var buffer := VoxelBuffer.new()
	buffer.create(18,18,18)
	var empty: Mesh = mesher.build_mesh(buffer, [material])
	if empty != null and empty.get_surface_count() > 0: failures.append("Empty region emitted geometry")
	buffer.set_voxel(1, 1, 1, 1, VoxelBuffer.CHANNEL_TYPE)
	_check_mesh(mesher, buffer, material, 12, "single cube")
	buffer.set_voxel(1, 2, 1, 1, VoxelBuffer.CHANNEL_TYPE)
	_check_mesh(mesher, buffer, material, 20, "shared face culled")
	buffer.set_voxel(1, 0, 1, 1, VoxelBuffer.CHANNEL_TYPE)
	_check_mesh(mesher, buffer, material, 18, "negative border halo")
	buffer.create(18,18,18)
	buffer.set_voxel(1, 1, 1, 1, VoxelBuffer.CHANNEL_TYPE)
	buffer.set_voxel(2, 2, 1, 1, VoxelBuffer.CHANNEL_TYPE)
	_check_mesh(mesher, buffer, material, 20, "mixed block colors")
	buffer.create(18,18,18)
	buffer.fill_area(1, Vector3i.ONE, Vector3i(17,17,17), VoxelBuffer.CHANNEL_TYPE)
	_check_mesh(mesher, buffer, material, 6 * 16 * 16 * 2, "solid region split without dropped faces")
	# Beyond-envelope case: it must reject before building large renderer payloads.
	buffer.create(34,34,34)
	for z: int in range(1,33):
		for x: int in range(1,33):
			for y: int in range(1,33):
				if (x + y + z) % 2 == 0: buffer.set_voxel(1,x,y,z,VoxelBuffer.CHANNEL_TYPE)
	var rejected: Mesh = mesher.build_mesh(buffer, [material])
	if rejected != null and rejected.get_surface_count() > 0: failures.append("Checkerboard was not rejected")
	if int(CairnProbe.new().snapshot()["overloads"]) != 1: failures.append("Overload was not reported")
	print("CAIRN_M1_NATIVE=" + JSON.stringify({"passed": failures.is_empty(), "failures": failures}))
	quit(0 if failures.is_empty() else 1)

func _check_evaluation() -> void:
	failures.append_array(load("res://scripts/benchmark_diagnostic_tests.gd").verify())
	failures.append_array(load("res://scripts/benchmark_frontier_tests.gd").verify())
	var evaluation = load("res://scripts/benchmark_evaluation.gd")
	var probe := CairnProbe.new()
	var lifetime: Dictionary = probe.snapshot()
	probe.begin_phase(10, true)
	var phase: Dictionary = probe.end_phase()
	if phase["upload"]["count"] != 0 or phase["deletion"]["max_usec"] != 0:
		failures.append("Empty measurement inherited earlier operations")
	if probe.snapshot()["upload_max_usec"] != lifetime["upload_max_usec"] or probe.snapshot()["deletion_max_usec"] != lifetime["deletion_max_usec"]:
		failures.append("Phase boundary reset lifetime maxima")
	probe.take_operation_frames()
	# Deliberately large lifetime values cannot affect a quiet measured phase.
	phase["native_start"] = {"upload_max_usec": 5000, "deletion_max_usec": 4000}
	phase["native_end"] = phase["native_start"].duplicate()
	phase["upload"]["max_usec"] = 750
	phase["deletion"]["max_usec"] = 750
	if not evaluation.operation_failures(phase).is_empty(): failures.append("Lifetime maximum contaminated phase evaluation")
	phase["upload"]["max_usec"] = 900
	phase["deletion"]["max_usec"] = 800
	var reasons: Array[String] = evaluation.operation_failures(phase)
	if reasons.size() != 2: failures.append("Later over-budget operations below the lifetime maximum were missed")
	var result: Dictionary = evaluation.scenario_result(true, true, reasons)
	if not result["completed"] or result["qualified"] or result["evaluation"] != "failed": failures.append("Completion hid a failed evaluation")
	var empty: Array[String] = []
	result = evaluation.scenario_result(true, false, empty)
	if result["qualified"] or result["evaluation"] != "passed": failures.append("Passing measured subset falsely qualified M1")
	phase["dropped_frames"] = 1
	if evaluation.operation_failures(phase).size() != 3: failures.append("Dropped evidence was hidden")

func _check_mesh(mesher: CairnMesher, buffer: VoxelBuffer, material: Material, expected: int, label: String) -> void:
	var mesh: Mesh = mesher.build_mesh(buffer, [material])
	if mesh == null:
		failures.append(label + ": no mesh")
		return
	var triangles: int = 0
	for i: int in range(mesh.get_surface_count()):
		var arrays: Array = mesh.surface_get_arrays(i)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		triangles += vertices.size() / 3
		if vertices.size() * 68 > 256 * 1024: failures.append(label + ": oversized upload")
		if normals.size() != vertices.size(): failures.append(label + ": lost normal data")
	if triangles != expected: failures.append(label + ": face coverage changed")
	var original: Mesh = reference.build_mesh(buffer, [material])
	if original == null or _triangle_records(mesh) != _triangle_records(original):
		failures.append(label + ": split changed triangle winding or vertex attributes")

func _triangle_records(mesh: Mesh) -> Dictionary:
	# Compare ordered triangle vertices, independent of surface splitting/index
	# reuse. Repeated triangles remain counted, so duplicates cannot hide a loss.
	var records: Dictionary = {}
	for surface: int in range(mesh.get_surface_count()):
		var arrays: Array = mesh.surface_get_arrays(surface)
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		for triangle: int in range(0, indices.size(), 3):
			var record: Array = []
			for corner: int in range(3):
				var index: int = indices[triangle + corner]
				for channel: int in [Mesh.ARRAY_VERTEX, Mesh.ARRAY_NORMAL, Mesh.ARRAY_TEX_UV, Mesh.ARRAY_COLOR]:
					record.append(arrays[channel][index])
				var tangents: PackedFloat32Array = arrays[Mesh.ARRAY_TANGENT]
				if not tangents.is_empty():
					for component: int in range(4): record.append(tangents[index * 4 + component])
			var key: String = var_to_str(record)
			records[key] = int(records.get(key, 0)) + 1
	return records

