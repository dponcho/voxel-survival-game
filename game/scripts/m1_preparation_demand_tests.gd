extends Node

func _ready() -> void:
	var output: String = ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--preparation-demand-output="):
			output = argument.trim_prefix("--preparation-demand-output=")
	var library := VoxelBlockyLibrary.new()
	var cube := VoxelBlockyModelCube.new()
	cube.set_material_override(0, StandardMaterial3D.new())
	library.models = [VoxelBlockyModelEmpty.new(), cube]
	library.bake()
	var mesher := CairnMesher.new()
	mesher.library = library
	for side: int in range(6): mesher.set_shadow_occluder_side(side, false)
	var probe := CairnProbe.new()
	var native: Dictionary = probe.preparation_controls(output + ".bin", mesher)
	var passed: bool = bool(native.get("passed", false))
	for fault: Dictionary in native.get("faults", []):
		passed = passed and not bool(fault.ledger.passed) and bool(fault.release.disposed)
	passed = passed and native.get("faults", []).size() == 5
	var report: Dictionary = {"schema": "cairn-preparation-demand-controls-1",
		"build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")),
		"passed": passed, "qualified": false, "target_performance": "not_run", "native": native}
	var file := FileAccess.open(output, FileAccess.WRITE)
	var saved: bool = file != null
	if file != null:
		file.store_string(JSON.stringify(report, "  "))
		file.flush()
		saved = file.get_error() == OK
		file.close()
	print("CAIRN_PREPARATION_DEMAND=" + JSON.stringify({"passed": passed and saved, "output": output}))
	get_tree().quit(0 if passed and saved else 1)
