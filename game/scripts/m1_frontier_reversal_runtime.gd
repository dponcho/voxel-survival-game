extends "res://scripts/m1_frontier_admission_runtime.gd"

# Preserve the production H2 route: outward motion, camera reversal at tick 900.
# Added fields are bounded observation; they do not retain native resources.
func _travel_ticks() -> int:
	return 1200

func _travel_id() -> String:
	return "AB-H2-reversal"

func _boundary_ticks() -> Array[int]:
	return [56, 204, 351, 499, 647, 794, 900, 942, 1090]

func _extra_observation() -> Dictionary:
	return {"edit_tail": probe.sample_mesh_blocks(terrain, [Vector3i(5, 0, 0),
		Vector3i(6, 0, 0), Vector3i(7, 0, 0), Vector3i(8, 0, 0)]),
		"camera_reversed": simulation_ticks >= 900}
