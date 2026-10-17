extends RefCounted

# A bounded cost experiment, separate from the unchanged four-minute H1/H2 gates.
# Only the required-region scan/analytic/model ledger is switched. All other
# diagnostics, edit settlement and native admission/safety work stay enabled.
const ORDER: Array[String] = ["off-1", "on-1", "on-2", "off-2"]
const SECONDS: float = 30.0
const TICKS: int = 1800

static func scenarios(warmup: Dictionary) -> Array[Dictionary]:
	var result: Array[Dictionary] = [warmup.duplicate(true)]
	for workload: String in ["H1", "H2"]:
		for repetition: String in ORDER:
			result.append({"id": "AB-" + workload + "-" + repetition, "workload": workload,
				"seconds": SECONDS, "fixture": 1, "actors": 24 if workload == "H2" else 12,
				"rate": 4.0 if workload == "H2" else 0.0,
				"frontier_enabled": repetition.begins_with("on-")})
	return result

static func active(scenario: Dictionary) -> bool:
	return str(scenario.get("id", "")).begins_with("AB-H") or str(scenario.get("id", "")).begins_with("CAL-H")

static func workload(scenario: Dictionary) -> String:
	return str(scenario.get("workload", scenario["id"]))

static func frontier_enabled(scenario: Dictionary) -> bool:
	return bool(scenario.get("frontier_enabled", true))
