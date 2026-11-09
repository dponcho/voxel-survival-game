extends RefCounted

const X = preload("res://scripts/m1_cycle_exact.gd")
const VERSION: String = "m1-shipping-cpu-cycles-1"
const POLICY: String = "m1-shipping-diagnostics-2"

static func dose_request(reference: String) -> String: return X.divide_small(reference, 216000, true)

static func observation_ok(o: Dictionary) -> bool:
	if o.get("schema", "") != "cairn-cpu-cycle-observation-1" or o.get("status", "") != "measured" or o.get("platform", "") != "windows" or o.get("process_api", "") != "QueryProcessCycleTime" or o.get("thread_api", "") != "QueryThreadCycleTime" or not X.canonical(o.get("thread_id"), true): return false
	var reads: Array = o.get("reads", [])
	if reads.size() != 4: return false
	var previous: String = "0"
	for i: int in range(4):
		var r: Dictionary = reads[i]
		if r.get("kind", "") != ["process_lo", "thread_lo", "thread_hi", "process_hi"][i] or r.get("available") != true or r.get("success") != true or r.get("error", -1) != 0: return false
		for key: String in ["cycles", "wall_before_usec", "wall_after_usec"]:
			if not X.canonical(r.get(key), true) or X.cmp(r[key], "18446744073709551615") > 0: return false
		if X.cmp(previous, r.wall_before_usec) > 0 or X.cmp(r.wall_before_usec, r.wall_after_usec) > 0: return false
		previous = r.wall_after_usec
	return X.cmp(reads[0].cycles, reads[3].cycles) <= 0 and X.cmp(reads[1].cycles, reads[2].cycles) <= 0

static func sequential(a: Dictionary, b: Dictionary) -> bool:
	return observation_ok(a) and observation_ok(b) and a.thread_id == b.thread_id and X.cmp(a.reads[3].cycles, b.reads[0].cycles) <= 0 and X.cmp(a.reads[2].cycles, b.reads[1].cycles) <= 0 and X.cmp(a.reads[3].wall_after_usec, b.reads[0].wall_before_usec) <= 0

static func boundary_bounds(a: Dictionary, b: Dictionary) -> Array:
	return [a.reads[0].cycles, b.reads[3].cycles] if sequential(a, b) else []

static func process_demand(a: Dictionary, b: Dictionary) -> Array:
	return difference([a.reads[0].cycles, a.reads[3].cycles], [b.reads[0].cycles, b.reads[3].cycles]) if sequential(a, b) else []

static func thread_demand(a: Dictionary, b: Dictionary) -> Array:
	return difference([a.reads[1].cycles, a.reads[2].cycles], [b.reads[1].cycles, b.reads[2].cycles]) if sequential(a, b) else []

static func difference(a: Array, b: Array) -> Array:
	return [X.high("0", X.sub(b[0], a[1])), X.sub(b[1], a[0])]

static func partition(boundaries: Array) -> Dictionary:
	if boundaries.size() != 6: return {}
	var labels: Array = ["start", "prepared", "+X", "-X", "+Z", "complete-after-report-flush"]
	var sections: Array = []
	var midpoints: Array = []
	for i: int in range(6):
		var b: Dictionary = boundaries[i]
		if b.label != labels[i] or b.bounds != boundary_bounds(b.before, b.after) or not interval(b.bounds): return {}
		if i > 0:
			var a: Dictionary = boundaries[i - 1]
			if not sequential(a.after, b.before) or a.wall_usec > b.wall_usec: return {}
			sections.append(difference(a.bounds, b.bounds))
			midpoints.append(X.sub(X.midpoint(b.bounds), X.midpoint(a.bounds)))
	var first: Array = boundaries[0].bounds
	var last: Array = boundaries[-1].bounds
	return {"complete": difference(first, last), "midpoint": X.sub(X.midpoint(last), X.midpoint(first)),
		"sections": sections, "section_midpoints": midpoints}

static func interval(value: Variant) -> bool:
	return value is Array and value.size() == 2 and X.canonical(value[0], true) and X.canonical(value[1], true) and X.cmp(value[0], value[1]) <= 0

static func usable(t: Dictionary) -> bool:
	if not bool(t.get("valid", false)): return false
	var c: Dictionary = t.get("cycle", {})
	if not interval(c.get("complete")) or not interval(c.get("marker")) or X.cmp(c.complete[0], "0") <= 0: return false
	if c.get("sections", []).size() != 5 or c.get("section_midpoints", []).size() != 5: return false
	var total: String = "0"
	for i: int in range(5):
		if not interval(c.sections[i]) or not X.canonical(c.section_midpoints[i], true): return false
		total = X.add(total, c.section_midpoints[i])
	return total == c.get("midpoint", "") and X.cmp(c.midpoint, c.complete[0]) >= 0 and X.cmp(c.midpoint, c.complete[1]) <= 0

static func envelope(trials: Array) -> Dictionary:
	if trials.size() != 4: return {}
	for t: Dictionary in trials:
		if not usable(t): return {}
	var a_lo: String = X.low(trials[0].cycle.complete[0], trials[3].cycle.complete[0])
	var a_hi: String = X.high(trials[0].cycle.complete[1], trials[3].cycle.complete[1])
	var b_lo: String = X.low(trials[1].cycle.complete[0], trials[2].cycle.complete[0])
	var b_hi: String = X.high(trials[1].cycle.complete[1], trials[2].cycle.complete[1])
	var drift: String = "0"
	for pair: Array in [[0, 3], [1, 2]]:
		var difference: String = "0"
		for i: int in range(5):
			var a: Array = trials[pair[0]].cycle.sections[i]
			var b: Array = trials[pair[1]].cycle.sections[i]
			difference = X.add(difference, X.high(X.absolute(X.sub(a[0], b[1])), X.absolute(X.sub(a[1], b[0]))))
		drift = X.high(drift, difference)
	var marker: String = "0"
	for ai: int in [0, 3]:
		for bi: int in [1, 2]: marker = X.high(marker, X.add(trials[ai].cycle.marker[1], trials[bi].cycle.marker[1]))
	var expansion: Dictionary = X.ratio(X.add(drift, marker), a_lo)
	var a_mid: String = X.add(trials[0].cycle.midpoint, trials[3].cycle.midpoint)
	var b_mid: String = X.add(trials[1].cycle.midpoint, trials[2].cycle.midpoint)
	return {"lower": X.rsub(X.ratio(X.sub(b_lo, a_hi), a_hi), expansion),
		"upper": X.radd(X.ratio(X.sub(b_hi, a_lo), a_lo), expansion),
		"point": X.ratio(X.sub(b_mid, a_mid), a_mid),
		"matching_section_drift": X.ratio(drift, a_lo), "terminal_marker_uncertainty": X.ratio(marker, a_lo)}

static func null_usable(n: Dictionary) -> bool:
	return not n.is_empty() and X.rcmp(n.lower, X.ratio("0")) <= 0 and X.rcmp(n.upper, X.ratio("0")) >= 0 and X.rcmp(X.rsub(n.upper, n.lower), X.ratio("1", "100")) < 0 and X.rcmp(n.matching_section_drift, X.ratio("1", "100")) < 0

static func controls(trials: Array) -> Dictionary:
	var result: Dictionary = {"valid": false, "null_valid": false, "positive_valid": false, "null": {}, "positive": {}, "dose_fractions": []}
	if trials.size() < 5: return result
	for i: int in range(mini(9, trials.size())):
		if not usable(trials[i]): return result
	result["null"] = envelope(trials.slice(1, 5))
	result.null_valid = null_usable(result["null"])
	if trials.size() < 9: return result
	result.positive = envelope(trials.slice(5, 9))
	if result.positive.is_empty(): return result
	var a_lo: String = X.low(trials[5].cycle.complete[0], trials[8].cycle.complete[0])
	var a_hi: String = X.high(trials[5].cycle.complete[1], trials[8].cycle.complete[1])
	var positive_ok: bool = X.rcmp(result.positive.lower, X.ratio("1", "100")) >= 0 and X.rcmp(result.positive.matching_section_drift, X.ratio("1", "100")) < 0
	for i: int in [6, 7]:
		var d: Dictionary = trials[i].dose
		if not bool(d.get("valid", false)) or d.get("ticks", 0) != 4320 or d.get("reference_cycles", "") != trials[5].cycle.midpoint or d.get("requested_tick_cycles", "") != dose_request(trials[5].cycle.midpoint) or not interval(d.get("cycles")) or X.cmp(d.get("requested_tick_cycles", "0"), "0") <= 0: return result
		if X.cmp(d.cycles[0], X.mul(d.requested_tick_cycles, "4320")) < 0: return result
		var lo: Dictionary = X.ratio(d.cycles[0], a_hi)
		var hi: Dictionary = X.ratio(d.cycles[1], a_lo)
		result.dose_fractions.append([lo, hi])
		positive_ok = positive_ok and X.rcmp(lo, X.ratio("1", "100")) > 0 and X.rcmp(hi, X.ratio("3", "100")) <= 0 and X.rcmp(result.positive.upper, lo) >= 0 and X.rcmp(result.positive.lower, hi) <= 0
	result.positive_valid = positive_ok
	result.valid = result.null_valid and positive_ok
	return result

static func evaluate(trials: Array) -> Dictionary:
	var c: Dictionary = controls(trials)
	var result: Dictionary = {"policy": POLICY, "method": VERSION, "qualified": false,
		"outcome": "inconclusive", "controls": c, "shipping": {}, "threshold": X.ratio("1", "100"),
		"scope": "incremental whole-process raw cycles conditional on common observers; no cycles-to-time conversion"}
	for t: Dictionary in trials:
		if not usable(t): return result
	if not c.valid or trials.size() != 13: return result
	var e: Dictionary = envelope(trials.slice(9, 13))
	result.shipping = e
	if e.is_empty() or X.rcmp(e.matching_section_drift, X.ratio("1", "100")) >= 0 or X.rcmp(e.point, X.ratio("0")) < 0: return result
	if X.rcmp(e.upper, X.ratio("1", "100")) < 0: result.outcome = "passed"
	elif X.rcmp(e.lower, X.ratio("1", "100")) >= 0: result.outcome = "failed"
	return result
