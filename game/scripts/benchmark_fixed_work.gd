extends RefCounted

# Experimental fixed-work closure sensitivity. All existing verdicts stay authoritative.
const Calibration = preload("res://scripts/benchmark_calibration.gd")
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")
const VERSION: String = "m1-fixed-work-elapsed-1"
const MAX_ELAPSED: int = 600000000

static func integer(data: Dictionary, key: String) -> int:
	var value: Variant = data.get(key)
	if not (value is int or value is float): return -1
	if not is_finite(float(value)) or float(value) != floor(float(value)) or absf(float(value)) > 9000000000000.0: return -1
	return int(value)

static func unavailable() -> Dictionary:
	return {"status": "unavailable", "elapsed_usec": null, "callbacks": null, "time_per_callback_usec": null,
		"terminal_interval_usec": null, "terminal_callbacks": null, "ack_marker_usec": null,
		"setup_and_callback_tail_usec": null, "main_interval_usec": null, "finalization_usec": null,
		"writer_drain_usec": null, "dose_usec": null, "callback_usec": null, "shared_usec": null, "switched_usec": null}

static func observation(report: Dictionary) -> Dictionary:
	var a: Dictionary = report.get("diagnostic_accounting", {})
	var ledger: Dictionary = report.get("route_calibration", {})
	var bounds: Dictionary = report.get("fixed_work_boundaries", {})
	var elapsed: int = integer(a, "elapsed_usec")
	var count: int = integer(a, "callbacks")
	var begin: int = integer(a, "start_usec")
	var end: int = integer(a, "end_usec")
	var last: int = integer(a, "last_callback_end_usec")
	var measured: int = integer(report, "measurement_end_usec")
	var native_end: int = integer(bounds, "native_phase_closed_usec")
	var drain_begin: int = integer(bounds, "writer_drain_begin_usec")
	var drain_end: int = integer(bounds, "writer_drain_end_usec")
	var sections: Array = ledger.get("bins", [])
	if elapsed <= 0 or elapsed > MAX_ELAPSED or count <= 0 or count > 2000000 or count != integer(report, "samples") or begin < 0 or end - begin != elapsed or not (begin <= last and last <= measured and measured <= native_end and native_end <= drain_begin and drain_begin <= drain_end and drain_end <= end): return unavailable()
	if a.get("overflow", true) or a.get("invalid_partition", true) or ledger.get("invalid", true) or ledger.get("version") != Calibration.VERSION or sections.size() != 7: return unavailable()
	if integer(a, "finalization_usec") != end - last or integer(a, "writer_drain_usec") != drain_end - drain_begin or integer(a, "callback_usec") < 0 or integer(a, "shared_usec") != integer(a, "callback_usec") or integer(a, "switched_usec") != 0 or integer(a, "switched_calls") != 0 or integer(a, "last_callback_usec") < 0 or integer(a, "last_callback_usec") > integer(a, "callback_usec"): return unavailable()
	var n: int = 0
	var interval: int = 0
	var costs: int = 0
	for section: Dictionary in sections:
		var samples: int = integer(section, "samples")
		var usec: int = integer(section, "usec")
		if samples <= 0 or usec <= 0 or integer(section, "callbacks") != samples or integer(section, "callback_usec") < 0 or section.get("status") != "measured": return unavailable()
		n += samples
		interval += usec
		costs += integer(section, "callback_usec")
	if n != count or costs != integer(a, "callback_usec") or absf(float(interval) - float(report.get("wall_seconds", -1)) * 1000000.0) > 0.01 or interval > elapsed - (end - last): return unavailable()
	var dose: Dictionary = ledger.get("closure_dose", {})
	var requested: int = integer(dose, "requested_usec")
	var duration: int = integer(dose, "elapsed_usec")
	if requested < 0 or duration < 0: return unavailable()
	if requested == 0:
		if dose.get("start_usec") != null or dose.get("end_usec") != null or duration != 0: return unavailable()
	else:
		var dose_begin: int = integer(dose, "start_usec")
		var dose_end: int = integer(dose, "end_usec")
		if dose_begin < drain_end or dose_end > end or dose_end - dose_begin != duration or duration < requested: return unavailable()
	var ack: Dictionary = report.get("edit_acknowledgement", {})
	var ack_begin: int = integer(ack, "start_usec")
	var ack_end: int = integer(ack, "end_usec")
	if ack_begin < 0 or ack_end != measured or (ack_begin > 0 and (ack_begin < begin or ack_begin > measured)): return unavailable()
	var terminal: Dictionary = sections[6]
	return {"status": "measured", "elapsed_usec": elapsed, "callbacks": count,
		"time_per_callback_usec": float(elapsed) / float(count), "terminal_interval_usec": integer(terminal, "usec"),
		"terminal_callbacks": integer(terminal, "samples"), "ack_marker_usec": ack_end - ack_begin if ack_begin > 0 else 0,
		"setup_and_callback_tail_usec": elapsed - interval - (end - last), "main_interval_usec": interval - integer(terminal, "usec"),
		"finalization_usec": end - last, "writer_drain_usec": drain_end - drain_begin, "dose_usec": duration,
		"callback_usec": costs, "shared_usec": integer(a, "shared_usec"), "switched_usec": integer(a, "switched_usec")}

static func duration_effect(d: Array[int]) -> Dictionary:
	var low_ref: int = mini(d[0], d[3])
	var high_ref: int = maxi(d[0], d[3])
	var low_pos: int = mini(d[1], d[2])
	var high_pos: int = maxi(d[1], d[2])
	# Integer comparisons keep the exactly-1% boundary independent of float rounding.
	var classification: String = "inconclusive"
	if 100 * (low_pos - high_ref) >= high_ref: classification = "above_limit"
	elif low_pos >= high_ref and 100 * (high_pos - low_ref) < low_ref: classification = "below_limit"
	return {"classification": classification, "added_fraction": float(d[1] + d[2]) / float(d[0] + d[3]) - 1.0,
		"lower_fraction": float(low_pos - high_ref) / float(high_ref), "upper_fraction": float(high_pos - low_ref) / float(low_ref)}

static func evaluate(reports: Array[Dictionary], short_run: bool, io_failed: bool, declared_dose: int = Calibration.DOSE_USEC) -> Dictionary:
	var result: Dictionary = {"version": VERSION, "experimental": true, "qualified": false, "legacy_authoritative": true,
		"threshold": 0.01, "declared_dose_usec": declared_dose, "hardware_noise_calibrated": false,
		"estimand": "complete measurement setup through scenario report construction wall duration for matched 1800 simulation ticks; count is not a denominator",
		"combined_report_finalization": {"status": "external_record", "file": "report-finalization.json", "allocated_to_trials": false},
		"scope": "fixed-work closure sensitivity; render throughput and time per callback descriptive; per-frame CPU/GPU critical-path and shared causal overhead unavailable",
		"per_frame_probe_cost": null, "shared_causal_overhead": null, "workloads": {}}
	for workload: String in ["H1", "H2"]:
		var selected: Array[Dictionary] = []
		for report: Dictionary in reports:
			if str(report.get("id", "")).begins_with("CAL-" + workload + "-"): selected.append(report)
		var assessment: Dictionary = {"status": "not_run" if selected.is_empty() else "inconclusive", "qualified": false,
			"duration_effect": {"classification": "unavailable", "added_fraction": null}, "observations": [],
			"same_mode_pairs": [], "count_duration_decomposition": [], "reasons": []}
		result["workloads"][workload] = assessment
		if selected.is_empty(): continue
		var reasons: Array[String] = []
		assessment["reasons"] = reasons
		if selected.size() != 4:
			reasons.append("Incomplete fixed-work quartet")
			continue
		reasons.append_array(Evaluation.heavy_workload_failures(selected, workload, short_run, [false, false, false, false]))
		var durations: Array[int] = []
		for index: int in range(4):
			var p: Dictionary = selected[index]
			var o: Dictionary = observation(p)
			assessment["observations"].append(o)
			if p.get("id") != "CAL-" + workload + "-" + Calibration.ORDER[index] or not p.get("completed", false) or p.get("evaluation") == "failed" or integer(p, "readiness_stops") != 0: reasons.append("Reordered, incomplete or failed workload")
			if float(p.get("simulated_seconds", 0)) < 30.0 or absf(float(p.get("wall_seconds", 0)) - float(p.get("simulated_seconds", 0))) > 0.25: reasons.append("Short or stalled fixed-work simulation")
			if o["status"] != "measured":
				reasons.append("Unavailable or invalid complete-window/terminal/phase evidence")
				continue
			durations.append(o["elapsed_usec"])
			var expected: int = declared_dose if index in [1, 2] else 0
			if integer(p.get("route_calibration", {}).get("closure_dose", {}), "requested_usec") != expected or declared_dose < 0: reasons.append("Dose differs from predeclared control")
		if short_run: reasons.append("Smoke does not calibrate hardware sensitivity")
		if io_failed: reasons.append("Failed or incomplete saved evidence")
		if durations.size() != 4: continue
		assessment["duration_effect"] = duration_effect(durations)
		for pair: Array in [[0, 3], [1, 2]]:
			var left: int = pair[0]
			var right: int = pair[1]
			var a: Dictionary = assessment["observations"][left]
			var b: Dictionary = assessment["observations"][right]
			var denominator: int = durations[left] + durations[right]
			var terminal_delta: int = b["terminal_interval_usec"] - a["terminal_interval_usec"]
			var ack_delta: int = b["ack_marker_usec"] - a["ack_marker_usec"]
			var main_variations: Array[float] = []
			for section: int in range(6):
				var x: int = integer(selected[left]["route_calibration"]["bins"][section], "usec")
				var y: int = integer(selected[right]["route_calibration"]["bins"][section], "usec")
				main_variations.append(float(2 * absi(x - y)) / float(x + y))
				if 200 * absi(x - y) >= x + y: reasons.append("Matching main-section duration instability")
			var uncertainty: int = maxi(absi(terminal_delta), absi(ack_delta))
			assessment["same_mode_pairs"].append({"complete_duration_variation": float(2 * absi(durations[right] - durations[left])) / float(denominator),
				"main_duration_variation": main_variations, "terminal_interval_delta_usec": terminal_delta, "ack_marker_delta_usec": ack_delta,
				"endpoint_uncertainty_usec": uncertainty, "endpoint_uncertainty_fraction": float(2 * uncertainty) / float(denominator),
				"callback_count_delta": b["callbacks"] - a["callbacks"]})
			if 200 * absi(durations[right] - durations[left]) >= denominator: reasons.append("Complete-window same-mode duration instability")
			if 200 * uncertainty >= denominator: reasons.append("Terminal/acknowledgement uncertainty reaches 1% of complete trial")
		for pair: Array in [[0, 1], [3, 2]]:
			var ref: Dictionary = assessment["observations"][pair[0]]
			var pos: Dictionary = assessment["observations"][pair[1]]
			var duration_ratio: float = float(pos["elapsed_usec"]) / float(ref["elapsed_usec"])
			var count_ratio: float = float(pos["callbacks"]) / float(ref["callbacks"])
			assessment["count_duration_decomposition"].append({"duration_added_fraction": duration_ratio - 1.0,
				"callback_count_added_fraction": count_ratio - 1.0, "time_per_callback_added_fraction": duration_ratio / count_ratio - 1.0})
		var effect: Dictionary = assessment["duration_effect"]
		if effect["classification"] == "inconclusive": reasons.append("Duration envelope overlaps threshold or apparent speedup")
		if declared_dose > 0 and float(effect.get("lower_fraction", 0)) <= 0: reasons.append("Declared closure effect is not visible in duration")
		if reasons.is_empty(): assessment["status"] = "null_observed" if declared_dose == 0 else "sensitivity_observed"
	return result
