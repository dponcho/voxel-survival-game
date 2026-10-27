extends Node

func _ready() -> void:
	var output: String = ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--mesh-retirement-output="):
			output = argument.trim_prefix("--mesh-retirement-output=")
	var probe = ClassDB.instantiate("CairnProbe")
	var native: Dictionary = probe.retirement_controls()
	var passed: bool = not output.is_empty() and bool(native.get("passed", false))
	var report: Dictionary = {"schema": "cairn-mesh-retirement-proof-1", "build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")),
		"native": native, "passed": passed, "qualified": false, "target_performance": "not_run", "route_executed": false,
		"scope": "Bounded synchronous last-owner lifetime control; no GPU/deferred-cost or operation-performance qualification."}
	var file := FileAccess.open(output, FileAccess.WRITE)
	var saved: bool = file != null
	if file != null:
		file.store_string(JSON.stringify(report, "  "))
		file.flush()
		saved = file.get_error() == OK
		file.close()
	print("CAIRN_MESH_RETIREMENT=" + JSON.stringify({"passed": passed and saved, "output": output}))
	get_tree().quit(0 if passed and saved else 1)
