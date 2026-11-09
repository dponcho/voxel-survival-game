extends Node

func _ready() -> void:
	var output: String = ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--observer-disposal-output="):
			output = argument.trim_prefix("--observer-disposal-output=")
	var probe := CairnProbe.new()
	var native: Dictionary = probe.observer_disposal_controls(output + ".bin")
	var passed: bool = bool(native.get("passed", false))
	for fault: Dictionary in native.get("faults", []):
		passed = passed and not bool(fault.ledger.passed) and bool(fault.release.disposed)
	var report: Dictionary = {"schema": "cairn-observer-disposal-controls-1",
		"build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")),
		"passed": passed, "qualified": false, "target_performance": "not_run", "native": native}
	var file := FileAccess.open(output, FileAccess.WRITE)
	var saved: bool = file != null
	if file != null:
		file.store_string(JSON.stringify(report, "  "))
		file.flush()
		saved = file.get_error() == OK
		file.close()
	print("CAIRN_OBSERVER_DISPOSAL=" + JSON.stringify({"passed": passed and saved, "output": output}))
	get_tree().quit(0 if passed and saved else 1)
