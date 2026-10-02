extends RefCounted

static func gpu_sample_status(milliseconds: float, now_usec: int) -> String:
	if milliseconds == 0.0: return "unavailable"
	# An asynchronous elapsed query cannot predate this process's clock origin.
	# Keep impossible/overflowed raw values; do not let them certify a GPU peak.
	if not is_finite(milliseconds) or milliseconds < 0.0 or milliseconds > float(now_usec) / 1000.0: return "invalid"
	return "valid"

# Accept only explicitly scoped measurements. Lifetime maxima remain context.
static func operation_failures(phase: Dictionary) -> Array[String]:
	var failures: Array[String] = []
	if int(phase["upload"]["max_usec"]) > 750: failures.append("Individual upload exceeded 0.75 ms")
	if int(phase["deletion"]["max_usec"]) > 750: failures.append("Individual deletion exceeded 0.75 ms")
	if int(phase["dropped_frames"]) > 0: failures.append("Native operation trace dropped frames")
	return failures

static func scenario_result(completed: bool, hard_failure: bool, reasons: Array[String]) -> Dictionary:
	# A clean measured subset still lacks the other mandatory M1 observations.
	var evaluation: String = "failed" if hard_failure else ("inconclusive" if not reasons.is_empty() else "passed")
	return {"completed": completed, "qualified": false, "evaluation": evaluation,
		"qualification": "unverified: outstanding M1 measurements and exact-build target review",
		"outcome": evaluation}

static func diagnostic_ab(reports: Array[Dictionary], short_run: bool, io_failed: bool) -> Dictionary:
	var result: Dictionary = {"outcome": "not_run", "qualified": false,
		"scope": "switched diagnostics: setup, callback/UI/formatting, worker I/O through drain and scenario report assembly",
		"method": "fixed off/on/on/off; conservative range of repeat means, not a statistical confidence interval",
		"threshold": 0.01, "reasons": []}
	var selected: Array[Dictionary] = []
	for report: Dictionary in reports:
		if str(report["id"]).begins_with("AB-"): selected.append(report)
	if selected.is_empty(): return result
	result["outcome"] = "inconclusive"
	var expected: Array[String] = ["AB-off-1", "AB-on-1", "AB-on-2", "AB-off-2"]
	if selected.size() != 4:
		result["reasons"].append("Incomplete or duplicate A/B phases")
		return result
	var off: Array[float] = []
	var on: Array[float] = []
	var block_variation: Array[float] = []
	for i: int in range(4):
		var report: Dictionary = selected[i]
		var accounting: Dictionary = report.get("diagnostic_accounting", {})
		var samples: int = int(report.get("samples", 0))
		if report["id"] != expected[i] or not report.get("completed", false) or samples <= 0 or accounting.is_empty():
			result["reasons"].append("Missing, reordered or invalid A/B evidence")
			return result
		var elapsed: float = float(accounting.get("elapsed_usec", 0))
		if not is_finite(elapsed) or elapsed <= 0.0:
			result["reasons"].append("Invalid A/B elapsed time")
			return result
		var mean_ms: float = elapsed / float(samples) / 1000.0
		if i == 0 or i == 3: off.append(mean_ms)
		else: on.append(mean_ms)
		if accounting.get("overflow", true) or int(accounting.get("callbacks", 0)) != samples:
			result["reasons"].append("Incomplete callback evidence")
		if int(report.get("readiness_stops", -1)) != 0 or report.get("evaluation", "failed") == "failed":
			result["reasons"].append("A/B workload failed")
		if float(report.get("simulated_seconds", 0)) < 30.0 or absf(float(report.get("wall_seconds", 0)) - float(report.get("simulated_seconds", 0))) > 0.25:
			result["reasons"].append("Short or stalled A/B simulation")
		if int(report.get("actor_ticks", 0)) != int(report.get("simulation_ticks", 0)) * 12 or int(report.get("simulation_ticks", 0)) < 1800:
			result["reasons"].append("Incomplete A/B actor workload")
		var blocks: Array = accounting.get("blocks", [])
		var means: Array[float] = []
		for block: Dictionary in blocks:
			if int(block.get("samples", 0)) <= 0 or int(block.get("usec", 0)) < 5000000:
				result["reasons"].append("Invalid timing block")
				continue
			means.append(float(block["usec"]) / float(block["samples"]))
		if means.size() < 4:
			result["reasons"].append("Insufficient five-second timing blocks")
		else:
			var variation: float = (means.max() - means.min()) / (means.reduce(func(a: float, b: float) -> float: return a + b, 0.0) / means.size())
			block_variation.append(variation)
			if variation >= 0.01: result["reasons"].append("Within-phase timing is unstable")
	var off_mean: float = (off[0] + off[1]) * 0.5
	var on_mean: float = (on[0] + on[1]) * 0.5
	var baseline_variation: float = absf(off[0] - off[1]) / off_mean
	var enabled_variation: float = absf(on[0] - on[1]) / on_mean
	var lower: float = on.min() / off.max() - 1.0
	var upper: float = on.max() / off.min() - 1.0
	result.merge({"off_mean_ms": off, "on_mean_ms": on,
		"added_fraction": on_mean / off_mean - 1.0, "baseline_variation": baseline_variation,
		"enabled_variation": enabled_variation, "within_phase_variation": block_variation,
		"lower_fraction": lower, "upper_fraction": upper})
	if short_run: result["reasons"].append("Smoke mode cannot measure overhead")
	if io_failed: result["reasons"].append("Run has incomplete or failed evidence")
	if baseline_variation >= 0.01 or enabled_variation >= 0.01: result["reasons"].append("A/B repeats are unstable")
	if upper < 0.0: result["reasons"].append("Enabled diagnostics consistently ran faster; attribution unresolved")
	if not result["reasons"].is_empty(): return result
	if lower >= 0.01: result["outcome"] = "failed"
	elif upper < 0.01: result["outcome"] = "passed"
	else: result["reasons"].append("Repeat range crosses the 1% limit")
	return result
