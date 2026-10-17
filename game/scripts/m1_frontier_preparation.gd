extends RefCounted

# Bounded preparation for the demonstrated +X 16³ heavy-route boundary only.
# Not a new required envelope, readiness shortcut, or general coverage policy.
const VERSION: String = "m1-forward-four-1"
var viewers: Array[VoxelViewer] = []
var previous_process_pose := Vector3.ZERO

static func supported(side: int, workload: String, mode: String) -> bool:
	return side == 16 and workload in ["H1", "H2"] and mode != "explore"

static func cells(pose: Vector3) -> Array[Vector3i]:
	var x: int = int(ceilf((pose.x + 96.0) / 16.0))
	var z: int = int(floorf(pose.z / 16.0))
	var adjacent: int = z + (1 if fposmod(pose.z, 16.0) >= 8.0 else -1)
	return [Vector3i(x, -1, z), Vector3i(x, 0, z),
		Vector3i(x, -1, adjacent), Vector3i(x, 0, adjacent)]

func start(parent: Node, pose: Vector3) -> void:
	assert(viewers.is_empty())
	previous_process_pose = pose
	for cell: Vector3i in cells(pose):
		var viewer := VoxelViewer.new()
		viewer.view_distance = 1
		viewer.requires_visuals = true
		viewer.requires_collisions = false
		viewer.position = Vector3(cell * 16) + Vector3.ONE * 8.0
		viewers.append(viewer)
		parent.add_child(viewer)

func advance_process(pose: Vector3) -> void:
	# Keep the old preparation column for one whole process opportunity after
	# the base viewer moves. VoxelTerrain applies each viewer's unview/view diff
	# sequentially; do not drop its last reference before the base handover.
	var targets: Array[Vector3i] = cells(previous_process_pose)
	for index: int in range(viewers.size()):
		viewers[index].position = Vector3(targets[index] * 16) + Vector3.ONE * 8.0
	previous_process_pose = pose

func dispose() -> void:
	for viewer: VoxelViewer in viewers:
		if is_instance_valid(viewer): viewer.queue_free()
	viewers.clear()

static func metadata(enabled: bool) -> Dictionary:
	return {"version": VERSION, "enabled": enabled, "viewer_count": 4 if enabled else 0,
		"viewer_radius_m": 1 if enabled else null, "required_visual_radius_m": 96,
		"data_radius_m": 128, "scope": "next +X column; fixture surface rows -1/0; nearest two Z cells",
		"handover": "previous process pose; base viewer retains old column before retarget",
		"resident_mesh_bound": 511 if enabled else null,
		"qualification": "unverified; neither complete-route coverage nor target timing"}
