extends SceneTree

const Method = preload("res://scripts/m1_shipping_method.gd")

func fixture(cost: int = 500000) -> Array:
	var values: Array = []
	for i: int in range(13):
		var positive: bool = i in [6, 7]
		var addition: int = 2000160 if positive else (cost if i in [10, 11] else 0)
		var sections: Array = [5000000, 20000000, 25000000, 27000000, 23000000]
		if positive:
			for j: int in [1, 2, 3]: sections[j] += addition / 3
		else: sections[4] += addition
		values.append({"valid": true, "duration_usec": 100000000 + addition, "sections_usec": sections,
			"marker_usec": 0, "callback_count": 40000 if i % 2 else 70000,
			"dose": {"valid": true, "reference_usec": 100000000 if positive else 0,
				"requested_tick_usec": 463 if positive else 0, "actual_usec": addition if positive else 0,
				"ticks": 4320 if positive else 0}})
	return values

func _initialize() -> void:
	var runtime: Node = load("res://scripts/m1_shipping_runtime.gd").new()
	runtime._configure_experiment()
	var dispatch_ok: bool = runtime.scenarios.size() == 9
	for scenario: Dictionary in runtime.scenarios:
		dispatch_ok = dispatch_ok and load("res://scripts/benchmark_heavy_ab.gd").active(scenario)
	runtime.free()
	var cases: Array = []
	for cost: int in [-1, 0, 500000, 999999, 1000000, 1500000]:
		cases.append({"name": "shipping-" + str(cost), "trials": fixture(cost)})
	var masked: Array = fixture()
	for i: int in [6, 7]:
		masked[i]["duration_usec"] = 100000000
		masked[i]["sections_usec"] = masked[5]["sections_usec"].duplicate()
	cases.append({"name": "real-dose-absorbed-in-idle", "trials": masked})
	var drift: Array = fixture()
	drift[4]["sections_usec"][1] += 600000
	drift[4]["sections_usec"][2] -= 600000
	cases.append({"name": "same-total-cancelled-route-drift", "trials": drift})
	var overlap: Array = fixture(990000)
	overlap[10]["marker_usec"] = 20000
	cases.append({"name": "terminal-uncertainty-overlap", "trials": overlap})
	var count: Array = fixture()
	for i: int in range(count.size()): count[i]["callback_count"] = 1 << i
	cases.append({"name": "callback-count-is-not-denominator", "trials": count})
	var varying: Array = fixture()
	for t: Dictionary in varying:
		t["sections_usec"][0] += 17000000
		t["sections_usec"][2] -= 17000000
	cases.append({"name": "repeatable-nonflat-route", "trials": varying})
	for i: int in range(13):
		var bad: Array = fixture()
		bad[i]["valid"] = false
		cases.append({"name": "invalid-trial-" + str(i), "trials": bad})
	for item: Dictionary in cases: item["assessment"] = Method.evaluate(item["trials"], false)
	print("CAIRN_SHIPPING_METHOD=" + JSON.stringify({"passed": dispatch_ok, "qualified": false, "fixed_work_dispatch": dispatch_ok, "cases": cases}))
	quit(0 if dispatch_ok else 1)
