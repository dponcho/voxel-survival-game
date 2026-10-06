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

static func diagnostic_ab(reports: Array[Dictionary], short_run: bool, io_failed: bool, prefix: String = "AB", actor_count: int = 12) -> Dictionary:
	var result: Dictionary = {"outcome": "not_run", "qualified": false,
		"scope": "switched diagnostics: setup, callback/UI/formatting, worker I/O through drain and scenario report assembly",
		"method": "fixed off/on/on/off; conservative range of repeat means, not a statistical confidence interval",
		"threshold": 0.01, "reasons": []}
	var selected: Array[Dictionary] = []
	for report: Dictionary in reports:
		if str(report["id"]).begins_with(prefix + "-off-") or str(report["id"]).begins_with(prefix + "-on-"): selected.append(report)
	if selected.is_empty(): return result
	result["outcome"] = "inconclusive"
	var expected: Array[String] = [prefix + "-off-1", prefix + "-on-1", prefix + "-on-2", prefix + "-off-2"]
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
		if int(report.get("actor_ticks", 0)) != int(report.get("simulation_ticks", 0)) * actor_count or int(report.get("simulation_ticks", 0)) < 1800:
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

# Keep each family separate; unlike the legacy flat control, heavy A/B retains
# all detailed probes except the frontier scan. A cost pass cannot qualify M1.
static func heavy_diagnostic_ab(reports: Array[Dictionary], short_run: bool, io_failed: bool) -> Dictionary:
	var result: Dictionary = {"qualified": false, "method_version": "m1-heavy-frontier-ab-1", "workloads": {},
		"scope": "switched native frontier scan, analytic/shader-model ledger and changed CSV payload; full setup/callback/worker I/O/drain/report window",
		"shared_instrumentation": "native lifetime/phase and edit hooks, collision timers, complete callbacks, render queries, CSV/operation/edit I/O, UI and bounded intent fingerprint remain enabled",
		"total_overhead": {"outcome": "inconclusive", "added_fraction": null,
			"reason": "shared instrumentation has no uninstrumented control; switched cost cannot qualify total diagnostics"}}
	for workload: String in ["H1", "H2"]:
		var prefix: String = "AB-" + workload
		var comparison: Dictionary = diagnostic_ab(reports, short_run, io_failed, prefix, 24 if workload == "H2" else 12)
		comparison["scope"] = result["scope"]
		var selected: Array[Dictionary] = []
		for report: Dictionary in reports:
			if str(report["id"]).begins_with(prefix + "-"): selected.append(report)
		var failures: Array[String] = heavy_workload_failures(selected, workload, short_run)
		comparison["workload_equivalence"] = "not_run" if selected.is_empty() else ("verified" if failures.is_empty() else "inconclusive")
		comparison["probe_switch"] = "not_run" if selected.is_empty() else ("verified" if failures.is_empty() else "inconclusive")
		if not failures.is_empty():
			comparison["outcome"] = "inconclusive"
			comparison["reasons"].append_array(failures)
		result["workloads"][workload] = comparison
	return result

static func heavy_workload_failures(selected: Array[Dictionary], workload: String, short_run: bool) -> Array[String]:
	var failures: Array[String] = []
	if selected.is_empty(): return failures
	if selected.size() != 4: return ["Incomplete matched heavy quartet"]
	var reference: Dictionary = selected[0].get("workload_contract", {})
	if reference.is_empty(): return ["Missing heavy workload contract"]
	var ticks: int = 60 if short_run else 1800
	var actors: int = 24 if workload == "H2" else 12
	for i: int in range(4):
		var report: Dictionary = selected[i]
		var contract: Dictionary = report.get("workload_contract", {})
		var evidence: Dictionary = report.get("workload_evidence", {})
		var accounting: Dictionary = report.get("diagnostic_accounting", {})
		var enabled: bool = i == 1 or i == 2
		if report.get("workload") != workload or contract != reference or evidence.is_empty():
			failures.append("Heavy fixtures/settings or route evidence differ")
		if int(report.get("simulation_ticks", -1)) != ticks or int(report.get("actor_ticks", -1)) != ticks * actors or int(contract.get("physics_hz", -1)) != 60:
			failures.append("Heavy ticks/actor activity do not match the fixed workload")
		if contract.get("resolution") != [1280, 720] or contract.get("visual_radius") != 96 or contract.get("data_radius") != 128 or contract.get("render_scale") != 1.0 or contract.get("triangle_colliders") != false or contract.get("max_physics_steps") != 4 or not contract.get("render_block") in [16, 32] or not contract.get("workers") in [1, 2]:
			failures.append("Heavy profile changed resolution/radii/worker/admission settings")
		if contract.get("native_policy") != {"frame_usec": 2000, "frame_upload_bytes": 1048576, "single_upload_bytes": 262144, "terrain_jobs": 64, "mesh_results": 16, "mesh_result_bytes": 33554432}:
			# JSON numbers decode as floats; compare policy values numerically below.
			var policy: Dictionary = contract.get("native_policy", {})
			for key: String in ["frame_usec", "frame_upload_bytes", "single_upload_bytes", "terrain_jobs", "mesh_results", "mesh_result_bytes"]:
				var expected: int = {"frame_usec": 2000, "frame_upload_bytes": 1048576, "single_upload_bytes": 262144, "terrain_jobs": 64, "mesh_results": 16, "mesh_result_bytes": 33554432}[key]
				if int(policy.get(key, -1)) != expected: failures.append("Heavy native admission policy differs")
		if contract.get("actors") != actors or contract.get("fixture") != 1 or contract.get("rain_instances") != (256 if workload == "H2" else 0) or contract.get("edit_rate") != (4.0 if workload == "H2" else 0.0):
			failures.append("Heavy scenario is not the required fixture/actors/edits/rain")
		if int(report.get("accepted_proxy_edits", -1)) != (ticks / 15 if workload == "H2" else 0) or int(report.get("proxy_autosaves", -1)) != (ticks / 60 if workload == "H2" else 0) or int(report.get("rejected_proxy_edits", -1)) != 0:
			failures.append("Heavy edits/storage were incomplete or deferred")
		if not report.get("operation_phase", {}).get("tracing", false) or (workload == "H2" and not report.get("edit_visibility", {}).get("enabled", false)):
			failures.append("Heavy baseline disabled shared operation/edit evidence")
		if report.get("frontier_enabled") != enabled or int(accounting.get("switched_calls", -1)) != (int(report.get("samples", -2)) if enabled else 0) or accounting.get("invalid_partition", true):
			failures.append("Heavy switched probe dispatch or callback partition is incomplete")
		var coverage: Dictionary = report.get("fog_frontier", {})
		if enabled:
			if int(coverage.get("samples", -1)) != int(report.get("samples", -2)) or int(coverage.get("invalid_samples", -1)) != 0:
				failures.append("Enabled heavy coverage evidence is unavailable or incomplete")
		elif accounting.get("switched_usec") != 0 or coverage.get("status") != "unavailable" or coverage.get("evaluation") != "inconclusive" or coverage.get("minimum_frontier_distance_m") != null or coverage.get("exposed_samples") != null:
			failures.append("Disabled coverage became a passing zero or ran the probe")
		if evidence.get("command_hash") != selected[0].get("workload_evidence", {}).get("command_hash") or evidence.get("route_checkpoints") != selected[0].get("workload_evidence", {}).get("route_checkpoints"):
			failures.append("Heavy command schedules or camera routes differ")
		if float(report.get("travelled_distance_m", -1)) < 6.5 * float(ticks) / 60.0 - 1.0:
			failures.append("Heavy sprint was not performed")
	return failures
