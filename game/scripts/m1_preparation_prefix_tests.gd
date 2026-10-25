extends Node

func _ready() -> void:
	var output: String = ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--preparation-prefix-output="):
			output = argument.trim_prefix("--preparation-prefix-output=")
	var begin: int = Time.get_ticks_usec()
	var cases: Array[Dictionary] = []
	var passed: bool = not output.is_empty()
	var before_folder: String = output.get_base_dir().path_join("before")
	passed = DirAccess.make_dir_recursive_absolute(before_folder) == OK and passed
	var rejected = load("res://scripts/m1_preparation_prefix_before.gd").new()
	rejected.set_process(false)
	rejected.set_physics_process(false)
	add_child(rejected)
	var before: Dictionary = await rejected.exercise(before_folder, 0, true, true)
	passed = before.setup_calls == 1 and before.injected_open_error > 0 and passed
	rejected.free()
	# Normal handover; failed warm-up; failed middle/last prefix; failed trial;
	# ordinary five-trial termination. No route work is manufactured or launched.
	for parameters: Array in [[0, true, false], [0, true, true], [2, true, true],
			[4, true, true], [0, false, false], [4, true, false], [0, false, true]]:
		var folder: String = output.get_base_dir().path_join("case-%d" % cases.size())
		passed = DirAccess.make_dir_recursive_absolute(folder) == OK and passed
		var fixture = load("res://scripts/m1_preparation_prefix_fixture.gd").new()
		fixture.set_process(false)
		fixture.set_physics_process(false)
		add_child(fixture)
		var result: Dictionary = await fixture.exercise(folder, int(parameters[0]), bool(parameters[1]), bool(parameters[2]))
		passed = bool(result.fixture_io_ok) and bool(result.immutable_preserved) and passed
		cases.append(result)
		fixture.free()
	var elapsed: int = Time.get_ticks_usec() - begin
	passed = elapsed <= 5000000 and cases.size() == 7 and passed
	var report: Dictionary = {"schema": "cairn-preparation-prefix-controls-1", "build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")),
		"passed": passed, "qualified": false, "target_performance": "not_run", "synthetic_completions": true,
		"route_executed": false, "fixture_limit_usec": 5000000, "fixture_usec": elapsed, "before": before, "cases": cases}
	var file := FileAccess.open(output, FileAccess.WRITE)
	var saved: bool = file != null
	if file != null:
		file.store_string(JSON.stringify(report, "  "))
		file.flush()
		saved = file.get_error() == OK
		file.close()
	print("CAIRN_PREPARATION_PREFIX=" + JSON.stringify({"passed": passed and saved, "output": output}))
	get_tree().quit(0 if passed and saved else 1)
