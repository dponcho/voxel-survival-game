extends RefCounted

const Frontier = preload("res://scripts/benchmark_frontier.gd")

static func verify() -> Array[String]:
	var failures: Array[String] = []
	var sample: Dictionary = {"status": "measured", "candidate_regions": 4, "checked_regions": 3, "ready_regions": 2,
		"empty_regions": 1, "unready_regions": 1, "frontier_distance_m": 96.0, "block": [-1, -1, 0], "mesh_state": "missing"}
	var fog: Dictionary = {"enabled": true, "mode": "exponential", "density": 0.025, "height_density": 0.0}
	var result: Dictionary = Frontier.evaluate(sample, fog)
	if result["evaluation"] != "failed" or result["fog_boundary_m"] != null or result["fog_clearance_m"] != null or absf(float(result["fog_transmittance"]) - 0.090717953289) > 0.000001:
		failures.append("Exponential fog manufactured an opaque boundary or concealed a gap")
	var complete: Dictionary = sample.duplicate(true)
	complete["unready_regions"] = 0
	complete["ready_regions"] = 3
	if Frontier.evaluate(complete, fog)["evaluation"] != "inconclusive": failures.append("Missing fog boundary passed")
	fog.merge({"mode": "depth", "density": 1.0, "begin_m": 16.0, "end_m": 64.0, "curve": 1.0}, true)
	for distance: float in [63.0, 64.0, 65.0]:
		sample["frontier_distance_m"] = distance
		result = Frontier.evaluate(sample, fog)
		if result["evaluation"] != ("failed" if distance < 64.0 else "passed") or float(result["fog_clearance_m"]) != distance - 64.0:
			failures.append("Fog crossing or exact-boundary classification is wrong")
	complete["frontier_distance_m"] = 32.0
	if Frontier.evaluate(complete, fog)["evaluation"] != "inconclusive": failures.append("Clipped scan passed an unobserved fog boundary")
	for key: String in ["density", "height_density", "begin_m", "end_m", "curve"]:
		var invalid_fog: Dictionary = fog.duplicate(true)
		invalid_fog[key] = NAN
		if Frontier.evaluate(sample, invalid_fog)["status"] != "unavailable": failures.append("Non-finite fog sample passed: " + key)
	for change: Dictionary in [{"status": "unavailable"}, {"checked_regions": 0}, {"candidate_regions": 1025}, {"ready_regions": 0}, {"empty_regions": 4}, {"frontier_distance_m": NAN}, {"frontier_distance_m": -1.0}]:
		var invalid_sample: Dictionary = sample.duplicate(true)
		invalid_sample.merge(change, true)
		if Frontier.evaluate(invalid_sample, fog)["status"] != "unavailable": failures.append("Invalid native coverage passed")
	var ledger := Frontier.new()
	sample["frontier_distance_m"] = 63.0
	ledger.record(sample, fog)
	ledger.record({"status": "unavailable", "reason": "bounded scan unavailable"}, fog)
	var summary: Dictionary = ledger.snapshot(true)
	if summary["samples"] != 2 or summary["measured_samples"] != 1 or summary["invalid_samples"] != 1 or summary["exposed_samples"] != 1 or summary["evaluation"] != "failed" or summary["minimum_fog_clearance_m"] != -1.0:
		failures.append("Frontier ledger lost failed or unavailable evidence")
	if Frontier.csv_fields({}).size() != Frontier.COLUMNS.size() or Frontier.csv_fields(ledger.worst).size() != Frontier.COLUMNS.size() or Frontier.csv_fields(ledger.worst)[8] != "-1;-1;0":
		failures.append("Frontier CSV lost fields or negative coordinates")
	if ledger.snapshot(false)["evaluation"] != "not_run": failures.append("Other scenarios claimed frontier evidence")
	return failures
