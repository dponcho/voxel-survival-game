extends Node

const Method = preload("res://scripts/m1_shipping_cycles_method.gd")
const X = preload("res://scripts/m1_cycle_exact.gd")

func fake_observation(wall: int, process: String, thread: String) -> Dictionary:
	var reads: Array = []
	var values: Array = [process, thread, X.add(thread, "1"), X.add(process, "1")]
	for i: int in range(4):
		reads.append({"kind": ["process_lo", "thread_lo", "thread_hi", "process_hi"][i],
			"available": true, "success": true, "error": 0, "cycles": values[i],
			"wall_before_usec": str(wall + i * 2), "wall_after_usec": str(wall + i * 2 + 1)})
	return {"schema": "cairn-cpu-cycle-observation-1", "status": "measured", "platform": "windows",
		"process_api": "QueryProcessCycleTime", "thread_api": "QueryThreadCycleTime", "thread_id": "1", "reads": reads}

func fixture(cost: int = 500000) -> Array:
	var values: Array = []
	for i: int in range(13):
		var positive: bool = i in [6, 7]
		var addition: int = 2000160 if positive else (cost if i in [10, 11] else 0)
		var sections: Array = ["5000000", "20000000", "25000000", "27000000", str(23000000 + addition)]
		values.append({"valid": true, "duration_usec": 100000000, "sections_usec": [5000000,20000000,25000000,27000000,23000000], "marker_usec": 0,
			"callback_count": 1 << i, "cycle": {"complete": [str(100000000 + addition), str(100000000 + addition)],
				"midpoint": str(100000000 + addition), "sections": sections.map(func(v: String) -> Array: return [v, v]),
				"section_midpoints": sections, "marker": ["0", "0"]},
			"dose": {"valid": true, "reference_cycles": "100000000" if positive else "0",
				"requested_tick_cycles": "463" if positive else "0", "cycles": [str(addition), str(addition)] if positive else ["0", "0"], "ticks": 4320 if positive else 0}})
	return values

func _ready() -> void:
	var cases: Array = []
	for cost: int in [-1,0,500000,999999,1000000,1500000]:
		cases.append({"name": "shipping-" + str(cost), "trials": fixture(cost)})
	var drift: Array = fixture()
	drift[4].cycle.sections[1] = ["20600000", "20600000"]
	drift[4].cycle.sections[2] = ["24400000", "24400000"]
	drift[4].cycle.section_midpoints[1] = "20600000"
	drift[4].cycle.section_midpoints[2] = "24400000"
	cases.append({"name": "same-total-section-drift", "trials": drift})
	var marker: Array = fixture(990000)
	marker[10].cycle.marker = ["0", "20000"]
	cases.append({"name": "terminal-uncertainty", "trials": marker})
	var masked: Array = fixture()
	for i: int in [6, 7]: masked[i].cycle = masked[5].cycle.duplicate(true)
	cases.append({"name": "masked-positive", "trials": masked})
	for bound: Array in [["1000000", "1000000"], ["3000000", "3000000"], ["3000001", "3000001"], ["999999", "2000000"]]:
		var band: Array = fixture()
		for i: int in [6, 7]: band[i].dose.cycles = bound.duplicate()
		cases.append({"name": "dose-band-" + bound[0] + "-" + bound[1], "trials": band})
	for i: int in range(13):
		var bad: Array = fixture()
		bad[i].valid = false
		cases.append({"name": "invalid-trial-" + str(i), "trials": bad})
	var wide: Array = fixture()
	for i: int in [1, 2, 3, 4]: wide[i].cycle.complete = ["99500000", "100500000"]
	cases.append({"name": "uncertain-boundaries", "trials": wide})
	var broken: Array = fixture()
	broken[2].cycle.section_midpoints[0] = "4999999"
	cases.append({"name": "midpoint-partition-loss", "trials": broken})
	for item: Dictionary in cases: item["assessment"] = Method.evaluate(item.trials)
	var requests: Array = []
	for v: String in ["0","1","215999","216000","216001","9007199254740993","9223372036854775808","18446744073709551615"]:
		requests.append([v, Method.dose_request(v)])
	var exact: Dictionary = {"above_signed": X.add("9223372036854775808", "9007199254740993"),
		"max_midpoint": X.midpoint(["18446744073709551613", "18446744073709551615"]),
		"negative": X.sub("9007199254740993", "9223372036854775808"),
		"cross_product": X.mul("18446744073709551615", "18446744073709551615")}
	var boundaries: Array = []
	for i: int in range(6):
		var before: Dictionary = fake_observation(i * 100, X.add("9223372036854775808", str(i * 1000)), str(i * 1000))
		var after: Dictionary = fake_observation(i * 100 + 20, X.add("9223372036854775808", str(i * 1000 + 500)), str(i * 1000 + 500))
		boundaries.append({"label": ["start", "prepared", "+X", "-X", "+Z", "complete-after-report-flush"][i],
			"before": before, "snapshot": {"generation_jobs": 0}, "after": after,
			"bounds": Method.boundary_bounds(before, after), "wall_usec": i * 100 + 30})
	var boundary_cases: Array = [{"name": "above-signed-domain", "boundaries": boundaries, "partition": Method.partition(boundaries)}]
	for label: String in ["numeric", "failed", "reversed", "missing"]:
		var bad: Array = boundaries.duplicate(true)
		if label == "numeric": bad[0].before.reads[0].cycles = 9007199254740993
		elif label == "failed":
			bad[0].before.status = "failed"
			bad[0].before.reads[0].success = false
			bad[0].before.reads[0].error = 6
			bad[0].before.reads[0].cycles = null
		elif label == "reversed": bad[2].after.reads[3].cycles = "1"
		else: bad.remove_at(2)
		boundary_cases.append({"name": label, "boundaries": bad, "partition": Method.partition(bad)})
	var runtime: Node = load("res://scripts/m1_shipping_cycles_runtime.gd").new()
	runtime._configure_experiment()
	var dispatch: bool = runtime.scenarios.size() == 5 and runtime.workers == 1 and runtime.render_size == 32
	for scenario: Dictionary in runtime.scenarios: dispatch = dispatch and load("res://scripts/benchmark_heavy_ab.gd").active(scenario)
	runtime.free()
	var probe := CairnProbe.new()
	var zero: Dictionary = probe.cpu_cycle_dose("0")
	var positive: Dictionary = probe.cpu_cycle_dose("1")
	var rejected: Array = []
	for v: String in ["", "00", "-1", "18446744073709551616"]: rejected.append(probe.cpu_cycle_dose(v))
	var report: Dictionary = {"schema": "cairn-shipping-cycles-controls-1", "policy": Method.POLICY,
		"method": Method.VERSION, "qualified": false, "build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")),
		"passed": dispatch and bool(zero.get("passed", false)) and bool(positive.get("passed", false)),
		"fixed_work_dispatch": dispatch, "cases": cases, "request_vectors": requests, "exact_vectors": exact, "boundary_cases": boundary_cases,
		"native_zero": zero, "native_positive": positive, "native_rejected": rejected,
		"scope": "pure method/failure controls and bounded native API checks; no route or sensitivity claim"}
	var output: String = ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--shipping-cycles-output="): output = argument.trim_prefix("--shipping-cycles-output=")
	var file := FileAccess.open(output, FileAccess.WRITE)
	var saved: bool = file != null
	if file != null:
		file.store_string(JSON.stringify(report, "  "))
		file.flush()
		saved = file.get_error() == OK
		file.close()
	print("CAIRN_SHIPPING_CYCLES_CONTROLS=" + JSON.stringify({"passed": bool(report.passed) and saved, "output": output}))
	get_tree().quit(0 if bool(report.passed) and saved else 1)
