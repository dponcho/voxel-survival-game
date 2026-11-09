extends Node

func _ready() -> void:
	var output: String = ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--shipping-observer-output="): output = argument.trim_prefix("--shipping-observer-output=")
	var runtime: Node = load("res://scripts/m1_shipping_observer_runtime.gd").new()
	runtime._configure_experiment()
	var dispatch: bool = runtime.scenarios.size() == 5 and runtime.workers == 1 and runtime.render_size == 32
	for scenario: Dictionary in runtime.scenarios:
		dispatch = dispatch and scenario.diagnostic_mode == "bare" and not scenario.dose and load("res://scripts/benchmark_heavy_ab.gd").active(scenario)
	runtime.free()
	var probe := CairnProbe.new()
	var native: Dictionary = probe.observer_controls(output + ".bin")
	var faults: Array[Dictionary] = []
	for label: String in ["invalid-slot", "wrong-token", "unclosed-span"]:
		var bad := CairnProbe.new()
		var started: bool = bad.observer_start(output + "-" + label + ".bin")
		if label == "invalid-slot": bad.observer_begin(0)
		else:
			var token: int = bad.observer_begin(2)
			if label == "wrong-token": bad.observer_end(token + 1)
		var ledger: Dictionary = bad.observer_finish()
		faults.append({"name": label, "started": started, "ledger": ledger})
	var report: Dictionary = {"schema": "cairn-shipping-observer-controls-1", "method": "m1-shipping-observer-attribution-1",
		"build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")),
		"passed": dispatch and bool(native.get("passed", false)), "qualified": false,
		"fixed_work_dispatch": dispatch, "native": native, "faults": faults}
	for fault: Dictionary in faults: report.passed = report.passed and fault.started and not bool(fault.ledger.get("passed", true)) and int(fault.ledger.get("failure_code", 0)) > 0
	var file := FileAccess.open(output, FileAccess.WRITE)
	var saved: bool = file != null
	if file != null:
		file.store_string(JSON.stringify(report, "  "))
		file.flush()
		saved = file.get_error() == OK
		file.close()
	print("CAIRN_SHIPPING_OBSERVER_CONTROLS=" + JSON.stringify({"passed": bool(report.passed) and saved, "output": output}))
	get_tree().quit(0 if bool(report.passed) and saved else 1)
