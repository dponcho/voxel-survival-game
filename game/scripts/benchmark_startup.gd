extends RefCounted

# Elapsed wall time, not CPU service time or a diagnosis of external processes.
const PHASE_CAP: int = 6
const PREFIX_CAP: int = 64
const SPAN_CAP: int = 16
var active: bool = true
var phases: Array[Dictionary] = []
var current: int = -1
var previous: int = -1
var previous_begin: int = -1
var spans: Array[Dictionary] = []
var render_begin_usec: int = -1
var dropped_spans: int = 0
var total_dropped_spans: int = 0
var invalid_spans: int = 0
var unpaired_render_signals: int = 0
var phase_overflow: bool = false
var stopped_usec: int = 0
var stop_reason: String = ""

func begin_phase(id: int, scenario: String, label: String, now: int) -> void:
	if not active: return
	if current >= 0: phases[current]["end_usec"] = now
	if phases.size() >= PHASE_CAP:
		phase_overflow = true
		stop(now, "phase capacity exceeded")
		return
	current = phases.size()
	phases.append({"id": id, "scenario": scenario, "phase": label, "start_usec": now,
		"end_usec": null, "intervals": 0, "maximum_interval_usec": 0,
		"first_intervals": [], "worst_interval": {}, "renderer_observations": [],
		"maximum_observed_renderer_cpu_ms": 0.0, "worst_renderer_observation": {}})

func begin_process(now: int, measured_frame: Variant, previous_diagnostic_usec: Variant) -> void:
	if not active: return
	if previous_begin >= 0: _close_interval(now, measured_frame, previous_diagnostic_usec, false)
	previous_begin = -1
	spans.clear()
	dropped_spans = 0
	if current >= 0 and phases[current]["scenario"] == "N1" and phases[current]["phase"] == "gameplay" and int(phases[current]["intervals"]) >= PREFIX_CAP:
		stop(now, "first gameplay interval window complete")
		return
	previous_begin = now
	previous = current

func record_span(kind: String, begin: int, end: int) -> void:
	if not active: return
	if kind not in ["process", "physics", "render"] or begin < 0 or end < begin:
		invalid_spans += 1
		return
	if spans.size() >= SPAN_CAP:
		dropped_spans += 1
		total_dropped_spans += 1
		return
	spans.append({"kind": kind, "start_usec": begin, "end_usec": end})

func render_started(now: int) -> void:
	if not active: return
	if render_begin_usec >= 0: unpaired_render_signals += 1
	render_begin_usec = now

func render_finished(now: int) -> void:
	if not active: return
	if render_begin_usec < 0:
		unpaired_render_signals += 1
		return
	record_span("render", render_begin_usec, now)
	render_begin_usec = -1

func observe_renderer(now: int, frame: int, cpu: float, gpu: float, gpu_status: String) -> void:
	if not active or current < 0: return
	var phase: Dictionary = phases[current]
	var observations: Array = phase["renderer_observations"]
	var cpu_valid: bool = is_finite(cpu) and cpu > 0.0 and cpu * 1000.0 <= float(now)
	var new_maximum: bool = cpu_valid and cpu > float(phase["maximum_observed_renderer_cpu_ms"])
	if observations.size() >= PREFIX_CAP and not new_maximum: return
	var row: Dictionary = {"observed_usec": now, "measured_frame": frame, "origin_frame": null,
		"cpu_elapsed_ms": cpu if cpu_valid else null, "cpu_status": "measured" if cpu_valid else "unavailable",
		"gpu_ms": gpu if gpu_status == "valid" else null, "gpu_status": gpu_status,
		"scope": "latest asynchronous viewport result; not assigned to this callback interval"}
	if observations.size() < PREFIX_CAP: observations.append(row)
	if new_maximum:
		phase["maximum_observed_renderer_cpu_ms"] = cpu
		phase["worst_renderer_observation"] = row.duplicate(true)

func _close_interval(now: int, measured_frame: Variant, diagnostic: Variant, terminal: bool) -> void:
	if previous < 0 or now < previous_begin:
		invalid_spans += 1
		return
	var phase: Dictionary = phases[previous]
	var elapsed: int = now - previous_begin
	phase["intervals"] += 1
	var first: Array = phase["first_intervals"]
	var worst: bool = elapsed > int(phase["maximum_interval_usec"]) or phase["worst_interval"].is_empty()
	if first.size() >= PREFIX_CAP and not worst: return
	var row: Dictionary = interval_sample(previous_begin, now, spans, dropped_spans, render_begin_usec)
	row.merge({"start_phase_id": phase["id"], "end_phase_id": phases[current]["id"],
		"crossed_phase_boundary": previous != current, "ending_measured_frame": measured_frame,
		"previous_diagnostic_usec": diagnostic if previous == current else null, "terminal": terminal}, true)
	if terminal: row["stage_evidence_complete"] = false
	if first.size() < PREFIX_CAP: first.append(row)
	if worst:
		phase["maximum_interval_usec"] = elapsed
		phase["worst_interval"] = row.duplicate(true)

static func interval_sample(begin: int, end: int, events: Array[Dictionary], dropped: int = 0, open_render: int = -1) -> Dictionary:
	var ranges: Array[Array] = []
	var kinds: Dictionary = {"process": [], "physics": [], "render": []}
	var clipped: Array[Dictionary] = []
	for event: Dictionary in events:
		var start: int = maxi(begin, int(event["start_usec"]))
		var finish: int = mini(end, int(event["end_usec"]))
		if finish <= start: continue
		var pair: Array = [start, finish]
		ranges.append(pair)
		kinds[event["kind"]].append(pair)
		clipped.append({"kind": event["kind"], "start_usec": start, "end_usec": finish})
	var elapsed: int = end - begin
	var covered: int = _union_usec(ranges)
	var per_kind: Dictionary = {}
	var summed: int = 0
	for kind: String in kinds:
		var typed_ranges: Array[Array] = []
		for pair: Array in kinds[kind]: typed_ranges.append(pair)
		per_kind[kind] = _union_usec(typed_ranges)
		summed += int(per_kind[kind])
	return {"start_usec": begin, "end_usec": end, "interval_usec": elapsed,
		"stage_spans": clipped, "stage_wall_usec": per_kind, "observed_union_usec": covered,
		"overlap_usec": summed - covered, "outside_observed_stages_usec": elapsed - covered,
		"render_span_status": "measured" if not kinds["render"].is_empty() else "unavailable",
		"open_render_start_usec": open_render if open_render >= 0 else null,
		"dropped_spans": dropped, "stage_evidence_complete": dropped == 0 and open_render < 0,
		"causal_attribution": "inconclusive", "background_activity": "unverified"}

static func _union_usec(ranges: Array[Array]) -> int:
	if ranges.is_empty(): return 0
	ranges.sort_custom(func(a: Array, b: Array) -> bool: return int(a[0]) < int(b[0]))
	var begin: int = int(ranges[0][0])
	var end: int = int(ranges[0][1])
	var total: int = 0
	for pair: Array in ranges:
		if int(pair[0]) > end:
			total += end - begin
			begin = int(pair[0])
		end = maxi(end, int(pair[1]))
	return total + end - begin

func stop(now: int, reason: String) -> void:
	if not active: return
	if previous_begin >= 0: _close_interval(now, null, null, true)
	previous_begin = -1
	if current >= 0: phases[current]["end_usec"] = now
	active = false
	stopped_usec = now
	stop_reason = reason
	spans.clear()

func snapshot() -> Dictionary:
	return {"scope": "benchmark initialization, initial preparation/warmup/retirement, N1 preparation and first 64 gameplay intervals",
		"clock": "process monotonic microseconds; elapsed wall time, not CPU service time",
		"phase_cap": PHASE_CAP, "prefix_cap_per_phase": PREFIX_CAP, "pending_span_cap": SPAN_CAP,
		"phases": phases.duplicate(true), "stopped_usec": stopped_usec, "stop_reason": stop_reason,
		"phase_overflow": phase_overflow, "invalid_spans": invalid_spans,
		"dropped_spans": total_dropped_spans,
		"unpaired_render_signals": unpaired_render_signals,
		"process_span_scope": "synchronous benchmark process/ready body through probes, formatting and UI; excludes callback ledger write, end-of-scenario continuations and unrelated engine work",
		"physics_span_scope": "synchronous benchmark physics callback; excludes other engine physics work",
		"stage_evidence_complete_scope": "retained completed spans only; false for dropped spans, an open render bracket or a terminal partial interval; unavailable stages and causality remain unverified",
		"render_signal_scope": "pre/post draw signal delivery; may include render queue, driver waits, scheduling and deferred delivery; not GPU completion or scanout",
		"native_join": "same clock and phase IDs as operation_phases/raw_operations; operation time may overlap stage spans and must not be added",
		"phase_transition_scope": "logical interval groups begin at startup phase hooks and include closing/report-drain gaps until the next hook; a crossing interval retains both phase IDs",
		"unavailable": ["pre-benchmark engine boot", "CPU service time", "background process identity/activity", "shader compilation attribution", "driver/OS wait cause", "asynchronous viewport result origin frame", "physical presentation", "startup timing overhead qualification"],
		"evaluation": "inconclusive", "qualified": false}
