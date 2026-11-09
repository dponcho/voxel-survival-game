extends Node


func _ready() -> void:
	var probe: RefCounted = ClassDB.instantiate(&"CairnProbe")
	var report: Dictionary = probe.call("cpu_cycle_capability_smoke")
	# Round-trip native decimal strings through the actual engine JSON codec.
	report["decimal_roundtrip"] = JSON.parse_string(JSON.stringify(report.get("decimal_controls", [])))
	report["build"] = JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json"))
	report["identity"] = ClassDB.instantiate(&"SandboxWorld").call("get_build_identity")
	var saved := false
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--cpu-cycle-output="):
			var output := FileAccess.open(argument.trim_prefix("--cpu-cycle-output="), FileAccess.WRITE)
			if output != null:
				output.store_string(JSON.stringify(report, "\t") + "\n")
				output.flush()
				saved = output.get_error() == OK
				output.close()
	report["saved"] = saved
	print("CAIRN_CPU_CYCLE_CAPABILITY=" + JSON.stringify(report))
	get_tree().quit(0 if report.get("passed", false) and saved else 1)
