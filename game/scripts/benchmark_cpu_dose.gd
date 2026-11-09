extends RefCounted

# Experimental synchronous callback wall spans, never OS CPU service or GPU time.
const Fixed = preload("res://scripts/benchmark_fixed_work.gd")
const Calibration = preload("res://scripts/benchmark_calibration.gd")
const VERSION: String = "m1-cpu-dose-span-1"
var bins: Array[Dictionary] = []
var invalid: bool = false
var previous_tick: int = 0
var previous_end: int = -1
var request: int = -1
var last: Dictionary = {}

func _init() -> void:
	for section: int in range(7): bins.append({"samples": 0, "body_usec": 0, "dose_usec": 0})

func record(tick: int, begin: int, end: int, dose_begin: Variant, dose_end: Variant, requested: int) -> void:
	if tick < previous_tick or tick < 0 or tick > 1800 or begin < previous_end or end <= begin or requested < 0: invalid = true
	if request == -1: request = requested
	if request != requested: invalid = true
	var dose: int = 0
	if requested == 0:
		if dose_begin != null or dose_end != null: invalid = true
	elif not (dose_begin is int and dose_end is int): invalid = true
	else:
		dose = int(dose_end) - int(dose_begin)
		if int(dose_begin) < begin or int(dose_end) > end or dose < requested: invalid = true
	var section: int = 6 if tick == 1800 else mini(5, int(maxi(0, tick - 1) / 300))
	var b: Dictionary = bins[section]
	b["samples"] += 1
	b["body_usec"] += maxi(0, end - begin)
	b["dose_usec"] += maxi(0, dose)
	if b["samples"] > 2000000 or b["body_usec"] > 600000000: invalid = true
	previous_tick = tick
	previous_end = end
	last = {"begin_usec": begin, "end_usec": end, "body_usec": end - begin,
		"dose_begin_usec": dose_begin, "dose_end_usec": dose_end, "requested_usec": requested}

func snapshot() -> Dictionary:
	return {"version": VERSION, "invalid": invalid, "requested_per_callback_usec": request if request >= 0 else null,
		"bins": bins.duplicate(true), "last_callback": last.duplicate(true),
		"scope": "synchronous callback body wall span; includes injected native CPU work and scheduling; excludes subsequent ledger bookkeeping"}

static func not_run() -> Dictionary:
	return {"version": VERSION, "experimental": true, "qualified": false, "legacy_authoritative": true,
		"status": "not_run", "threshold": 0.01, "hardware_noise_calibrated": false,
		"estimand": "mean synchronous callback body wall span per observed callback at matched route positions; not total frame CPU service",
		"causal_frontier_probe_cost": null, "cpu_service_usec": null, "gpu_cost": null, "shared_causal_overhead": null,
		"scope": "cloud-only software CPU-dose instrument validation; no dose in ordinary gameplay or calibration", "workloads": {}}

static func observation(p: Dictionary) -> Dictionary:
	var unavailable: Dictionary = {"status": "unavailable", "callbacks": null, "body_usec": null,
		"mean_body_usec": null, "dose_usec": null, "mean_dose_usec": null, "complete_duration_usec": null,
		"entry_interval_usec": null, "complete_callback_usec": null, "ledger_remainder_usec": null, "last_body_usec": null}
	var window: Dictionary = Fixed.observation(p)
	var a: Dictionary = p.get("cpu_dose_accounting", {})
	if window["status"] != "measured" or a.get("version") != VERSION or a.get("invalid", true): return unavailable
	var sections: Array = a.get("bins", [])
	var route: Array = p.get("route_calibration", {}).get("bins", [])
	var request: int = Fixed.integer(a, "requested_per_callback_usec")
	if sections.size() != 7 or request < 0: return unavailable
	var n: int = 0
	var body: int = 0
	var dose: int = 0
	for j: int in range(7):
		var b: Dictionary = sections[j]
		var count: int = Fixed.integer(b, "samples")
		var cost: int = Fixed.integer(b, "body_usec")
		var added: int = Fixed.integer(b, "dose_usec")
		if count <= 0 or count != Fixed.integer(route[j], "samples") or cost <= 0 or cost > Fixed.integer(route[j], "callback_usec") or added < request * count or added > cost or (request == 0 and added != 0): return unavailable
		n += count
		body += cost
		dose += added
	var last: Dictionary = a.get("last_callback", {})
	var begin: int = Fixed.integer(last, "begin_usec")
	var end: int = Fixed.integer(last, "end_usec")
	if n != window["callbacks"] or body > window["callback_usec"] or body > window["elapsed_usec"] or end <= begin or begin < Fixed.integer(p["diagnostic_accounting"], "start_usec") or end > Fixed.integer(p["diagnostic_accounting"], "last_callback_end_usec") or end - begin != Fixed.integer(last, "body_usec") or end - begin > Fixed.integer(p["diagnostic_accounting"], "last_callback_usec") or Fixed.integer(last, "requested_usec") != request: return unavailable
	if request == 0:
		if last.get("dose_begin_usec") != null or last.get("dose_end_usec") != null: return unavailable
	else:
		var ds: int = Fixed.integer(last, "dose_begin_usec")
		var de: int = Fixed.integer(last, "dose_end_usec")
		if ds < begin or de > end or de - ds < request: return unavailable
	return {"status": "measured", "callbacks": n, "body_usec": body, "mean_body_usec": float(body) / float(n),
		"dose_usec": dose, "mean_dose_usec": float(dose) / float(n), "complete_duration_usec": window["elapsed_usec"],
		"entry_interval_usec": window["main_interval_usec"] + window["terminal_interval_usec"],
		"complete_callback_usec": window["callback_usec"], "ledger_remainder_usec": window["callback_usec"] - body,
		"last_body_usec": end - begin}

static func effect(observations: Array) -> Dictionary:
	var low_ref: int = 0
	var high_ref: int = 0
	var low_pos: int = 1
	var high_pos: int = 1
	for index: int in [3]:
		if observations[index]["body_usec"] * observations[low_ref]["callbacks"] < observations[low_ref]["body_usec"] * observations[index]["callbacks"]: low_ref = index
		else: high_ref = index
	for index: int in [2]:
		if observations[index]["body_usec"] * observations[low_pos]["callbacks"] < observations[low_pos]["body_usec"] * observations[index]["callbacks"]: low_pos = index
		else: high_pos = index
	var lb: int = observations[low_pos]["body_usec"] * observations[high_ref]["callbacks"]
	var ld: int = observations[high_ref]["body_usec"] * observations[low_pos]["callbacks"]
	var ub: int = observations[high_pos]["body_usec"] * observations[low_ref]["callbacks"]
	var ud: int = observations[low_ref]["body_usec"] * observations[high_pos]["callbacks"]
	var classification: String = "inconclusive"
	if 100 * (lb - ld) >= ld: classification = "above_limit"
	elif lb >= ld and 100 * (ub - ud) < ud: classification = "below_limit"
	return {"classification": classification, "lower_fraction": float(lb - ld) / float(ld), "upper_fraction": float(ub - ud) / float(ud)}

static func evaluate(phases: Array[Dictionary], short_run: bool, io_failed: bool, declared: int) -> Dictionary:
	var root: Dictionary = not_run()
	root["status"] = "experimental_controls"
	root["declared_per_callback_usec"] = declared
	var whole: Dictionary = Fixed.evaluate(phases, short_run, io_failed, 0)
	for workload: String in ["H1", "H2"]:
		var selected: Array[Dictionary] = []
		for p: Dictionary in phases:
			if str(p.get("id", "")).begins_with("CAL-" + workload + "-"): selected.append(p)
		var out: Dictionary = {"status": "not_run" if selected.is_empty() else "inconclusive", "qualified": false,
			"body_effect": {"classification": "unavailable", "lower_fraction": null, "upper_fraction": null},
			"entry_interval_effect": {"classification": "unavailable", "lower_fraction": null, "upper_fraction": null},
			"observations": [], "same_mode_body_variation": [], "main_body_variation": [],
			"complete_window": whole["workloads"][workload], "reasons": []}
		root["workloads"][workload] = out
		if selected.is_empty(): continue
		var reasons: Array[String] = []
		out["reasons"] = reasons
		if selected.size() != 4:
			reasons.append("Incomplete CPU-dose quartet")
			continue
		reasons.append_array(whole["workloads"][workload]["reasons"])
		for i: int in range(4):
			var o: Dictionary = observation(selected[i])
			out["observations"].append(o)
			if o["status"] != "measured": reasons.append("Missing or invalid CPU body/dose evidence")
			if Fixed.integer(selected[i].get("cpu_dose_accounting", {}), "requested_per_callback_usec") != (declared if i in [1, 2] else 0) or declared < 0: reasons.append("CPU dose differs from declaration")
		var obs: Array = out["observations"]
		var missing: bool = false
		for o: Dictionary in obs:
			if o["status"] != "measured": missing = true
		if missing: continue
		out["body_effect"] = effect(obs)
		var intervals: Array[Dictionary] = []
		for o: Dictionary in obs: intervals.append({"body_usec": o["entry_interval_usec"], "callbacks": o["callbacks"]})
		out["entry_interval_effect"] = effect(intervals)
		for pair: Array in [[0, 3], [1, 2]]:
			var a: Dictionary = obs[pair[0]]
			var b: Dictionary = obs[pair[1]]
			var x: int = a["body_usec"] * b["callbacks"]
			var y: int = b["body_usec"] * a["callbacks"]
			out["same_mode_body_variation"].append(float(2 * absi(x - y)) / float(x + y))
			if 200 * absi(x - y) >= x + y: reasons.append("Same-mode callback body instability")
			var variations: Array[float] = []
			for j: int in range(6):
				var c: Dictionary = selected[pair[0]]["cpu_dose_accounting"]["bins"][j]
				var d: Dictionary = selected[pair[1]]["cpu_dose_accounting"]["bins"][j]
				x = c["body_usec"] * d["samples"]
				y = d["body_usec"] * c["samples"]
				variations.append(float(2 * absi(x - y)) / float(x + y))
				if 200 * absi(x - y) >= x + y: reasons.append("Matching main callback body instability")
			out["main_body_variation"].append(variations)
		# A changed route mix can dilute a pooled per-callback mean. Retain the
		# observations but refuse attribution; do not reweight or discard rows.
		for p: Dictionary in selected:
			for j: int in range(6):
				if p["cpu_dose_accounting"]["bins"][j]["samples"] * selected[0]["cpu_dose_accounting"]["bins"][0]["samples"] != selected[0]["cpu_dose_accounting"]["bins"][j]["samples"] * p["cpu_dose_accounting"]["bins"][0]["samples"]: reasons.append("Callback route composition changed")
		if out["body_effect"]["classification"] == "inconclusive": reasons.append("Body envelope overlaps threshold or apparent speedup")
		if declared > 0 and float(out["body_effect"]["lower_fraction"]) <= 0: reasons.append("CPU dose not identifiable in pooled body observation")
		if reasons.is_empty(): out["status"] = "null_observed" if declared == 0 else "cpu_span_sensitivity_observed"
	return root
