extends SceneTree

var failures: Array[String] = []

func _initialize() -> void:
	var library := VoxelBlockyLibrary.new()
	var cube := VoxelBlockyModelCube.new()
	var material := StandardMaterial3D.new()
	cube.set_material_override(0, material)
	library.models = [VoxelBlockyModelEmpty.new(), cube]
	library.bake()
	var mesher := CairnMesher.new()
	mesher.library = library
	for side: int in range(6): mesher.set_shadow_occluder_side(side, false)
	var buffer := VoxelBuffer.new()
	buffer.create(18,18,18)
	buffer.set_voxel(1, 1, 1, 1, VoxelBuffer.CHANNEL_TYPE)
	_check_mesh(mesher, buffer, material, 12, "single cube")
	buffer.set_voxel(1, 2, 1, 1, VoxelBuffer.CHANNEL_TYPE)
	_check_mesh(mesher, buffer, material, 20, "shared face culled")
	buffer.set_voxel(1, 0, 1, 1, VoxelBuffer.CHANNEL_TYPE)
	_check_mesh(mesher, buffer, material, 18, "negative border halo")
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
		if vertices.size() * 64 > 256 * 1024: failures.append(label + ": oversized upload")
		if normals.size() != vertices.size(): failures.append(label + ": lost normal data")
	if triangles != expected: failures.append(label + ": face coverage changed")
