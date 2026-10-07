extends RefCounted

# Supplementary sensitivity experiment. Never replaces a legacy verdict.
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")
const HeavyAB = preload("res://scripts/benchmark_heavy_ab.gd")
const ORDER: Array[String] = ["reference-1", "closure-1", "closure-2", "reference-2"]
const DOSE_USEC: int = 600000
const TICKS: int = 1800
const VERSION: String = "m1-route-calibration-1"
var bins: Array[Dictionary] = []
var invalid: bool = false
var previous_tick: int = 0
var last_bin: int = -1
var harness_usec: int = 0
var dose: Dictionary = {"requested_usec": 0, "start_usec": null, "end_usec": null, "elapsed_usec": 0}

func _init() -> void:
	for index: int in range(7): bins.append({"samples": 0, "usec": 0, "callbacks": 0, "callback_usec": 0})

static func active(scenario: Dictionary) -> bool:
	return str(scenario.get("id", "")).begins_with("CAL-H")

static func scenarios(warmup: Dictionary) -> Array[Dictionary]:
	var result: Array[Dictionary] = HeavyAB.scenarios(warmup)
	for index: int in range(1, result.size()):
		var position: int = (index - 1) % 4
		result[index]["id"] = "CAL-" + str(result[index]["workload"]) + "-" + ORDER[position]
		result[index]["frontier_enabled"] = false
		result[index]["closure_dose_usec"] = DOSE_USEC if position in [1, 2] else 0
	return result

static func bin_index(tick: int) -> int:
	return 6 if tick >= TICKS else int(float(maxi(tick, 1) - 1) / 300.0)

func record_interval(tick: int, usec: int) -> void:
	if tick < previous_tick or tick < 0 or tick > TICKS or usec <= 0: invalid = true
	previous_tick = tick
	last_bin = bin_index(clampi(tick, 0, TICKS))
	bins[last_bin]["samples"] += 1
	bins[last_bin]["usec"] += usec

func record_callback(usec: int) -> void:
	if last_bin < 0 or usec < 0:
		invalid = true
		return
	bins[last_bin]["callbacks"] += 1
	bins[last_bin]["callback_usec"] += usec

func snapshot() -> Dictionary:
	var saved: Array[Dictionary] = bins.duplicate(true)
	for section: Dictionary in saved:
		section["status"] = "measured" if int(section["samples"]) > 0 else "unavailable"
		section["mean_usec"] = float(section["usec"]) / float(section["samples"]) if int(section["samples"]) > 0 else null
	return {"version": VERSION, "bins": saved, "invalid": invalid,
		"mapping": "callback-entry simulation tick: 0..300,301..600,...1501..1799; tick 1800 terminal/acknowledgement retained separately",
		"harness_bracket_usec": harness_usec,
		"harness_scope": "ledger call wall brackets; clock reads excluded; callback ledger tail outside callback timer but inside complete window; causal added cost unavailable",
		"closure_dose": dose.duplicate(true)}

static func _variation(a: float, b: float) -> float:
	return absf(a - b) / ((a + b) * 0.5)

static func compare(off: Array[float], on: Array[float]) -> Dictionary:
	var lower: float = on.min() / off.max() - 1.0
	var upper: float = on.max() / off.min() - 1.0
	return {"added_fraction": (on[0] + on[1]) / (off[0] + off[1]) - 1.0,
		"lower_fraction": lower, "upper_fraction": upper,
		"classification": "above_limit" if lower >= 0.01 else ("below_limit" if lower >= 0.0 and upper < 0.01 else "inconclusive")}

static func evaluate(reports: Array[Dictionary], short_run: bool, io_failed: bool) -> Dictionary:
	var result: Dictionary = {"version": VERSION, "qualified": false, "legacy_authoritative": true,
		"scope": "route-matched null repeats and known nonoverlapping closure wall delay; supplementary sensitivity only",
		"threshold": 0.01, "workloads": {}, "hardware_noise_calibrated": false,
		"shared_overhead": {"outcome": "inconclusive", "added_fraction": null,
			"reason": "minimal clocks/route ledger and shared operation/edit/render/CSV instrumentation have no uninstrumented control"}}
	for workload: String in ["H1", "H2"]:
		var selected: Array[Dictionary] = []
		for report: Dictionary in reports:
			if str(report.get("id", "")).begins_with("CAL-" + workload + "-"): selected.append(report)
		var assessment: Dictionary = {"status": "not_run" if selected.is_empty() else "inconclusive", "qualified": false,
			"positive": {"classification": "unavailable", "added_fraction": null}, "null_repeat_variation": null,
			"route_repeat_variation": [], "reasons": []}
		result["workloads"][workload] = assessment
		if selected.is_empty(): continue
		var reasons: Array[String] = []
		assessment["reasons"] = reasons
		if selected.size() != 4:
			reasons.append("Incomplete calibration quartet")
			continue
		var disabled: Array[bool] = [false, false, false, false]
		reasons.append_array(Evaluation.heavy_workload_failures(selected, workload, short_run, disabled))
		var means: Array[float] = []
		var routes: Array[Array] = []
		for index: int in range(4):
			var report: Dictionary = selected[index]
			var a: Dictionary = report.get("diagnostic_accounting", {})
			var ledger: Dictionary = report.get("route_calibration", {})
			if report.get("id") != "CAL-" + workload + "-" + ORDER[index] or not report.get("completed", false) or report.get("evaluation") == "failed" or int(report.get("readiness_stops", -1)) != 0:
				reasons.append("Reordered, incomplete or failed calibration workload")
			if float(report.get("simulated_seconds", 0)) < 30.0 or absf(float(report.get("wall_seconds", 0)) - float(report.get("simulated_seconds", 0))) > 0.25:
				reasons.append("Short or stalled calibration simulation")
			var count: int = int(report.get("samples", 0))
			if count <= 0 or int(a.get("callbacks", -1)) != count or a.get("overflow", true) or a.get("invalid_partition", true) or ledger.get("invalid", true) or ledger.get("version") != VERSION:
				reasons.append("Missing or invalid calibration accounting")
				continue
			var elapsed: int = int(a.get("elapsed_usec", 0))
			if elapsed <= 0 or int(a.get("end_usec", 0)) - int(a.get("start_usec", 0)) != elapsed:
				reasons.append("Invalid complete calibration window")
				continue
			if int(a.get("callback_usec", -1)) != int(a.get("shared_usec", -2)) or int(a.get("end_usec", 0)) - int(a.get("last_callback_end_usec", 0)) != int(a.get("finalization_usec", -1)) or int(a.get("writer_drain_usec", -1)) < 0 or int(a.get("writer_drain_usec", 0)) > int(a.get("finalization_usec", -1)):
				reasons.append("Callback/finalization/drain partition is invalid")
			means.append(float(elapsed) / float(count))
			var section_means: Array[float] = []
			var samples: int = 0
			var intervals: int = 0
			var callbacks: int = 0
			var callback_cost: int = 0
			var sections: Array = ledger.get("bins", [])
			if sections.size() != 7:
				reasons.append("Missing route sections or terminal evidence")
				continue
			var sections_valid: bool = true
			for section: Dictionary in sections:
				var n: int = int(section.get("samples", 0))
				var usec: int = int(section.get("usec", 0))
				if n <= 0 or usec <= 0 or int(section.get("callbacks", -1)) != n or section.get("status") != "measured":
					reasons.append("Unavailable route section")
					sections_valid = false
				section_means.append(float(usec) / maxf(n, 1.0))
				samples += n
				intervals += usec
				callbacks += int(section.get("callbacks", 0))
				callback_cost += int(section.get("callback_usec", 0))
			if samples != count or callbacks != count or callback_cost != int(a.get("callback_usec", -1)) or absf(float(intervals) - float(report.get("wall_seconds", 0)) * 1000000.0) > 0.01:
				reasons.append("Route ledger does not reconcile with complete callbacks/intervals")
			if not sections_valid: continue
			routes.append(section_means)
			var dose: Dictionary = ledger.get("closure_dose", {})
			var requested: int = DOSE_USEC if index in [1, 2] else 0
			if int(dose.get("requested_usec", -1)) != requested:
				reasons.append("Calibration dose differs from declared control")
			if requested == 0:
				if dose.get("start_usec") != null or dose.get("end_usec") != null or int(dose.get("elapsed_usec", -1)) != 0: reasons.append("Null control ran a closure dose")
			else:
				var begin: int = int(dose.get("start_usec", 0))
				var end: int = int(dose.get("end_usec", 0))
				if begin < int(report.get("measurement_end_usec", 0)) or begin < int(a.get("last_callback_end_usec", 0)) or end > int(a.get("end_usec", 0)) or end - begin != int(dose.get("elapsed_usec", -1)) or end - begin < requested or end - begin > int(a.get("finalization_usec", -1)):
					reasons.append("Closure dose is missing, overlapping or outside the complete cost window")
		if short_run: reasons.append("Smoke cannot calibrate hardware sensitivity")
		if io_failed: reasons.append("Run has failed or incomplete evidence")
		if means.size() != 4 or routes.size() != 4: continue
		assessment["null_repeat_variation"] = _variation(means[0], means[3])
		if _variation(means[0], means[3]) >= 0.01 or _variation(means[1], means[2]) >= 0.01: reasons.append("Whole-trial same-mode repeats differ by 1% or more")
		for section: int in range(7):
			var off: float = _variation(routes[0][section], routes[3][section])
			var on: float = _variation(routes[1][section], routes[2][section])
			assessment["route_repeat_variation"].append({"reference": off, "closure": on})
			if off >= 0.01 or on >= 0.01: reasons.append("Matching route/terminal sections differ by 1% or more")
		var off: Array[float] = [means[0], means[3]]
		var on: Array[float] = [means[1], means[2]]
		assessment["positive"] = compare(off, on)
		if assessment["positive"]["classification"] != "above_limit": reasons.append("Known above-limit closure control was not resolved")
		if reasons.is_empty(): assessment["status"] = "controls_resolved"
	return result
