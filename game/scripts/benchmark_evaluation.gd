extends RefCounted

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
