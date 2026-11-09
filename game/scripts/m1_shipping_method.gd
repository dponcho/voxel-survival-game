extends RefCounted

# Prospective deterministic repeat envelope, NOT a confidence interval. Whole
# elapsed duration is the denominator; callback counts never enter this method.
const VERSION: String = "m1-shipping-complete-trial-1"
const LIMIT: float = 0.01

static func dose_request(reference_usec: int) -> int:
	# Integer ceiling avoids rounding a whole-microsecond request upward.
	return (reference_usec + 216000 - 1) / 216000

static func envelope(trials: Array) -> Dictionary:
	var result: Dictionary = {"valid": false, "lower": null, "upper": null, "point": null,
		"matching_section_drift": null, "terminal_marker_uncertainty": null, "reason": "incomplete quartet"}
	if trials.size() != 4: return result
	for trial: Dictionary in trials:
		if not bool(trial.get("valid", false)) or int(trial.get("duration_usec", 0)) <= 0:
			result["reason"] = "missing work, operation, I/O or complete-boundary evidence"
			return result
		if int(trial.get("marker_usec", -1)) < 0: return result
		var sections: Array = trial.get("sections_usec", [])
		if sections.size() != 5: return result
		var total: int = 0
		for section: int in sections:
			if section < 0: return result
			total += section
		if total != int(trial["duration_usec"]): return result
	var a0: float = float(trials[0]["duration_usec"])
	var a3: float = float(trials[3]["duration_usec"])
	var b1: float = float(trials[1]["duration_usec"])
	var b2: float = float(trials[2]["duration_usec"])
	var denominator: float = minf(a0, a3)
	var drift: float = 0.0
	for pair: Array in [[0, 3], [1, 2]]:
		var difference: int = 0
		for index: int in range(5):
			difference += absi(int(trials[pair[0]]["sections_usec"][index]) - int(trials[pair[1]]["sections_usec"][index]))
		drift = maxf(drift, float(difference) / denominator)
	var marker: int = 0
	for ai: int in [0, 3]:
		for bi: int in [1, 2]:
			marker = maxi(marker, int(trials[ai].get("marker_usec", 0)) + int(trials[bi].get("marker_usec", 0)))
	var terminal: float = float(marker) / denominator
	# Durations are integer microseconds exactly representable here. Subtract
	# before division: ratio-minus-one can spuriously miss an exact dose overlap.
	result.merge({"valid": true, "lower": (minf(b1, b2) - maxf(a0, a3)) / maxf(a0, a3) - drift - terminal,
		"upper": (maxf(b1, b2) - denominator) / denominator + drift + terminal,
		"point": (b1 + b2 - a0 - a3) / (a0 + a3), "matching_section_drift": drift,
		"terminal_marker_uncertainty": terminal, "reason": "conservative complete-trial repeat envelope"}, true)
	return result

static func controls(trials: Array) -> Dictionary:
	var result: Dictionary = {"valid": false, "null": {}, "positive": {}, "reason": "controls not complete"}
	if trials.size() < 9: return result
	for index: int in range(9):
		if not bool(trials[index].get("valid", false)): return result
	var null_range: Dictionary = envelope(trials.slice(1, 5))
	var positive_range: Dictionary = envelope(trials.slice(5, 9))
	result["null"] = null_range
	result["positive"] = positive_range
	if not null_range["valid"] or not positive_range["valid"]: return result
	var null_ok: bool = null_range["lower"] <= 0.0 and null_range["upper"] >= 0.0 and null_range["upper"] - null_range["lower"] < LIMIT and null_range["matching_section_drift"] < LIMIT
	var dose_low: float = INF
	var dose_high: float = 0.0
	var doses_ok: bool = true
	for index: int in [6, 7]:
		var dose: Dictionary = trials[index]["dose"]
		var reference: int = int(trials[5]["duration_usec"])
		var actual: int = int(dose.get("actual_usec", 0))
		var requested: int = dose_request(reference)
		doses_ok = doses_ok and int(dose.get("reference_usec", 0)) == reference and int(dose.get("requested_tick_usec", 0)) == requested and actual >= requested * 4320 and int(dose.get("ticks", 0)) == 4320 and bool(dose.get("valid", false))
		dose_low = minf(dose_low, float(actual) / maxf(float(trials[5]["duration_usec"]), float(trials[8]["duration_usec"])))
		dose_high = maxf(dose_high, float(actual) / minf(float(trials[5]["duration_usec"]), float(trials[8]["duration_usec"])))
	var positive_ok: bool = doses_ok and dose_low > LIMIT and positive_range["lower"] >= LIMIT and positive_range["matching_section_drift"] < LIMIT and positive_range["upper"] >= dose_low and positive_range["lower"] <= dose_high
	result.merge({"valid": null_ok and positive_ok, "dose_fraction": [dose_low, dose_high],
		"null_valid": null_ok, "positive_valid": positive_ok,
		"reason": "controls usable" if null_ok and positive_ok else "resolution/drift or masked/invalid in-route positive; stop and choose policy"}, true)
	return result

static func evaluate(trials: Array, target: bool) -> Dictionary:
	var control: Dictionary = controls(trials)
	var result: Dictionary = {"policy": "m1-shipping-diagnostics-1", "method": VERSION,
		"qualified": false, "target_hardware": target, "threshold": LIMIT, "outcome": "inconclusive",
		"controls": control, "shipping": {}, "added_fraction": null,
		"stop_decision": "Stop. Keep shipping optional diagnostics unqualified; choose an explicit supported measurement, repetition or threshold policy before another pilot."}
	for trial: Dictionary in trials:
		if not bool(trial.get("valid", false)): return result
	if not control["valid"]: return result
	if trials.size() != 13:
		result["outcome"] = "not_run"
		return result
	var effect: Dictionary = envelope(trials.slice(9, 13))
	result["shipping"] = effect
	if not effect["valid"] or effect["matching_section_drift"] >= LIMIT or effect["point"] < 0.0: return result
	if effect["upper"] < LIMIT: result["outcome"] = "passed"
	elif effect["lower"] >= LIMIT: result["outcome"] = "failed"
	result["added_fraction"] = effect["point"]
	result["target_gate_eligible_for_review"] = result["outcome"] == "passed" and target
	if result["outcome"] == "passed": result["stop_decision"] = "Complete. Retain the exact-build reports for independent target review; M1 remains unqualified."
	elif result["outcome"] == "failed": result["stop_decision"] = "Stop. Reduce the declared optional shipping inventory before another candidate; the 1% limit is unchanged."
	return result
