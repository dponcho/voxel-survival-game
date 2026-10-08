extends RefCounted

# Owned callback-entry -> successor-entry cycles, not CPU service or scanout.
const CPU = preload("res://scripts/benchmark_cpu_dose.gd")
const Fixed = preload("res://scripts/benchmark_fixed_work.gd")
const VERSION: String = "m1-frame-slack-1"
const TOTALS: Array[String] = ["cycle_usec", "body_usec", "dose_usec", "callback_usec", "callback_overhead_usec", "outside_callback_usec"]
var bins: Array[Dictionary] = []
var invalid: bool = false
var stalled: bool = false
var previous_next: int = -1
var previous_tick: int = 0
var last: Dictionary = {}

func _init() -> void:
	for j: int in range(7):
		var b: Dictionary = {"samples": 0}
		for key: String in TOTALS: b[key] = 0
		bins.append(b)

func record(row: Dictionary) -> void:
	var entry: int = Fixed.integer(row, "entry_usec")
	var begin: int = Fixed.integer(row, "body_begin_usec")
	var end: int = Fixed.integer(row, "body_end_usec")
	var complete: int = Fixed.integer(row, "complete_callback_end_usec")
	var next: int = Fixed.integer(row, "next_entry_usec")
	var tick: int = Fixed.integer(row, "tick")
	var request: int = Fixed.integer(row, "requested_usec")
	var dose: int = 0
	if entry < 0 or not (entry <= begin and begin < end and end <= complete and complete <= next) or (previous_next >= 0 and entry != previous_next) or tick < previous_tick or tick < 0 or tick > 1800 or request < 0: invalid = true
	if request == 0:
		if row.get("dose_begin_usec") != null or row.get("dose_end_usec") != null: invalid = true
	else:
		var ds: int = Fixed.integer(row, "dose_begin_usec")
		var de: int = Fixed.integer(row, "dose_end_usec")
		if ds < 0 or de < 0: invalid = true
		else:
			dose = de - ds
			if ds < begin or de > end or dose < request: invalid = true
	var j: int = 6 if tick == 1800 else mini(5, int(maxi(0, tick - 1) / 300))
	var b: Dictionary = bins[j]
	b["samples"] += 1
	var values: Array[int] = [next - entry, end - begin, dose, complete - entry, complete - entry - (end - begin), next - complete]
	for k: int in range(TOTALS.size()): b[TOTALS[k]] += maxi(0, values[k])
	if next - entry > 250000: stalled = true
	if b["samples"] > 2000000 or b["cycle_usec"] > 600000000: invalid = true
	previous_next = next
	previous_tick = tick
	last = row.duplicate(true)

func snapshot() -> Dictionary:
	return {"version": VERSION, "invalid": invalid, "stalled": stalled, "bins": bins.duplicate(true), "last_cycle": last.duplicate(true)}

static func not_run() -> Dictionary:
	return {"version": VERSION, "experimental": true, "status": "not_run", "qualified": false,
		"legacy_authoritative": true, "threshold": 0.01, "hardware_noise_calibrated": false,
		"estimand": "mean owned process-callback entry through successor entry wall span at matching positions; includes waits and scheduling",
		"cpu_service_usec": null, "gpu_cost": null, "physical_presentation": null, "causal_probe_cost": null, "shared_causal_overhead": null,
		"scope": "cloud software frame/slack instrument; ordinary workloads unchanged", "workloads": {}}

static func observation(p: Dictionary) -> Dictionary:
	var unavailable: Dictionary = {"status": "unavailable", "callbacks": null, "cycle_usec": null, "body_usec": null,
		"dose_usec": null, "callback_usec": null, "callback_overhead_usec": null, "outside_callback_usec": null,
		"complete_duration_usec": null, "closing_anchor_usec": null, "last_cycle_usec": null}
	var l: Dictionary = p.get("frame_slack_accounting", {})
	var a: Dictionary = p.get("diagnostic_accounting", {})
	var b: Dictionary = p.get("phase_boundaries", {})
	var anchor: Dictionary = p.get("closing_anchor", {})
	var sections: Array = l.get("bins", [])
	if l.get("version") != VERSION or l.get("invalid", true) or sections.size() != 7 or a.get("invalid_partition", true) or a.get("overflow", true): return unavailable
	var out: Dictionary = {"status": "measured", "callbacks": 0}
	for key: String in TOTALS: out[key] = 0
	for section: Dictionary in sections:
		var n: int = Fixed.integer(section, "samples")
		if n <= 0: return unavailable
		out["callbacks"] += n
		for key: String in TOTALS:
			var value: int = Fixed.integer(section, key)
			if value < 0: return unavailable
			out[key] += value
		if section["body_usec"] <= 0 or section["body_usec"] + section["callback_overhead_usec"] != section["callback_usec"] or section["callback_usec"] + section["outside_callback_usec"] != section["cycle_usec"] or section["dose_usec"] > section["body_usec"]: return unavailable
	var start: int = Fixed.integer(a, "start_usec")
	var end: int = Fixed.integer(a, "end_usec")
	var first: int = Fixed.integer(p, "first_entry_usec")
	var ae: int = Fixed.integer(anchor, "entry_usec")
	var ac: int = Fixed.integer(anchor, "complete_callback_end_usec")
	var last: Dictionary = l.get("last_cycle", {})
	var le: int = Fixed.integer(last, "entry_usec")
	var ln: int = Fixed.integer(last, "next_entry_usec")
	var lc: int = Fixed.integer(last, "complete_callback_end_usec")
	var native_end: int = Fixed.integer(b, "native_phase_closed_usec")
	var db: int = Fixed.integer(b, "writer_drain_begin_usec")
	var de: int = Fixed.integer(b, "writer_drain_end_usec")
	if not (0 <= start and start <= first and first <= le and le < ln and ln == ae and ae < ac and ac <= native_end and native_end <= db and db <= de and de <= end) or end - start != Fixed.integer(a, "elapsed_usec") or end - start > 600000000 or out["cycle_usec"] != ae - first: return unavailable
	if out["callbacks"] != Fixed.integer(p, "samples") or out["callbacks"] != Fixed.integer(a, "callbacks") or out["callback_usec"] != Fixed.integer(a, "callback_usec") or a.get("shared_usec") != out["callback_usec"] or a.get("switched_usec") != 0 or a.get("switched_calls") != 0 or lc != Fixed.integer(a, "last_callback_end_usec") or end - lc != Fixed.integer(a, "finalization_usec") or de - db != Fixed.integer(a, "writer_drain_usec"): return unavailable
	if not (le <= Fixed.integer(last, "body_begin_usec") and Fixed.integer(last, "body_begin_usec") < Fixed.integer(last, "body_end_usec") and Fixed.integer(last, "body_end_usec") <= lc and lc <= ln): return unavailable
	var requested: int = Fixed.integer(last, "requested_usec")
	if requested < 0: return unavailable
	if requested == 0:
		if last.get("dose_begin_usec") != null or last.get("dose_end_usec") != null: return unavailable
	else:
		var ds: int = Fixed.integer(last, "dose_begin_usec")
		var de: int = Fixed.integer(last, "dose_end_usec")
		if ds < Fixed.integer(last, "body_begin_usec") or de > Fixed.integer(last, "body_end_usec") or de - ds < requested: return unavailable
	if Fixed.integer(b, "measurement_begin_usec") != start or Fixed.integer(b, "preparation_begin_usec") < 0 or Fixed.integer(b, "preparation_begin_usec") > start or Fixed.integer(b, "retirement_begin_usec") != end or Fixed.integer(b, "retirement_end_usec") < end or Fixed.integer(p, "acknowledgement_usec") < 0 or Fixed.integer(p, "acknowledgement_usec") > end - start or Fixed.integer(anchor, "previous_callback_usec") != Fixed.integer(a, "last_callback_usec") or lc - le != Fixed.integer(a, "last_callback_usec"): return unavailable
	out.merge({"complete_duration_usec": end - start, "closing_anchor_usec": ac - ae, "last_cycle_usec": ln - le})
	return out

static func effects(observations: Array) -> Dictionary:
	var frame: Array[Dictionary] = []
	for o: Dictionary in observations: frame.append({"body_usec": o["cycle_usec"], "callbacks": o["callbacks"]})
	return {"cycle_effect": CPU.effect(frame), "body_effect": CPU.effect(observations)}

static func evaluate(phases: Array[Dictionary], declared: int, final_only: bool = false, io_failed: bool = false) -> Dictionary:
	var root: Dictionary = not_run()
	root["status"] = "not_run" if phases.is_empty() else "inconclusive"
	root.merge({"observations": [], "cycle_effect": {"classification": "unavailable", "lower_fraction": null, "upper_fraction": null},
		"body_effect": {"classification": "unavailable", "lower_fraction": null, "upper_fraction": null}, "reasons": [], "same_mode_pairs": []})
	if phases.size() != 4: return root
	var reasons: Array[String] = []
	root["reasons"] = reasons
	for index: int in range(4):
		var p: Dictionary = phases[index]
		var o: Dictionary = observation(p)
		root["observations"].append(o)
		if p.get("index") != index or not p.get("completed", false) or p.get("work_units_valid") != true or p.get("operation_evaluation") == "failed" or p.get("samples") != 32 or p.get("frame_slack_accounting", {}).get("stalled", true): reasons.append("Incomplete, reordered, changed, stalled or failed work")
		if o["status"] != "measured": reasons.append("Unavailable cycle/endpoint/phase evidence")
	if io_failed: reasons.append("Failed saved evidence")
	for o: Dictionary in root["observations"]:
		if o["status"] != "measured": return root
	root.merge(effects(root["observations"]))
	for index: int in range(4):
		var o: Dictionary = root["observations"][index]
		var request: int = declared if index in [1, 2] else 0
		if request < 0 or o["dose_usec"] < request * (1 if final_only else o["callbacks"]) or (request == 0 and o["dose_usec"] != 0): reasons.append("Missing or unexpected dose")
		for j: int in range(7):
			if phases[index]["frame_slack_accounting"]["bins"][j]["samples"] != phases[0]["frame_slack_accounting"]["bins"][j]["samples"]: reasons.append("Callback count/composition drift")
	for pair: Array in [[0, 3], [1, 2]]:
		var left: Dictionary = root["observations"][pair[0]]
		var right: Dictionary = root["observations"][pair[1]]
		var values: Array[float] = []
		for key: String in ["complete_duration_usec", "cycle_usec", "body_usec"]:
			var x: int = left[key]
			var y: int = right[key]
			values.append(float(2 * absi(x - y)) / float(x + y))
			if 200 * absi(x - y) >= x + y: reasons.append("Complete/cycle/body repeat instability")
		for j: int in range(6):
			for key: String in ["cycle_usec", "body_usec"]:
				var x: int = phases[pair[0]]["frame_slack_accounting"]["bins"][j][key]
				var y: int = phases[pair[1]]["frame_slack_accounting"]["bins"][j][key]
				if 200 * absi(x - y) >= x + y: reasons.append("Matching main section instability")
		var td: int = phases[pair[1]]["frame_slack_accounting"]["bins"][6]["cycle_usec"] - phases[pair[0]]["frame_slack_accounting"]["bins"][6]["cycle_usec"]
		var ad: int = phases[pair[1]]["acknowledgement_usec"] - phases[pair[0]]["acknowledgement_usec"]
		var uncertainty: int = maxi(absi(td), absi(ad))
		if 200 * uncertainty >= left["complete_duration_usec"] + right["complete_duration_usec"]: reasons.append("Endpoint uncertainty reaches 1% of complete trial")
		root["same_mode_pairs"].append({"variations": values, "terminal_delta_usec": td, "acknowledgement_delta_usec": ad, "endpoint_uncertainty_usec": uncertainty,
			"endpoint_uncertainty_fraction": float(2 * uncertainty) / float(left["complete_duration_usec"] + right["complete_duration_usec"])})
	if root["cycle_effect"]["classification"] == "inconclusive": reasons.append("Cycle envelope overlap or apparent speedup")
	if declared > 0 and float(root["body_effect"]["lower_fraction"]) <= 0: reasons.append("Native work not identifiable in body")
	if reasons.is_empty(): root["status"] = "null_observed" if declared == 0 else ("slack_observed" if root["cycle_effect"]["upper_fraction"] == 0.0 else "frame_sensitivity_observed")
	return root
