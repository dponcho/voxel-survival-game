extends "res://scripts/m1_full_height_runtime.gd"

# Separate perturbing attribution-only mode. The v1/v2 entry points and readers remain intact.
# The identical native binary/enforcement clocks are used in every mode.
const Method = preload("res://scripts/m1_shipping_cycles_method.gd")
const X = preload("res://scripts/m1_cycle_exact.gd")
const Elapsed = preload("res://scripts/m1_shipping_method.gd")
const ATTR_VERSION: String = "m1-shipping-observer-attribution-1"
const INVENTORY: String = "res://diagnostics/shipping_observer_inventory.json"
const FRAME_HEADER: String = "frame,entry_usec,interval_usec,tick,resident_mesh,resident_data,generation_jobs,mesh_jobs,result_jobs,retired_meshes,accepted,readiness_stops,coverage_alarms"
const POSE_HEADER: String = "tick,usec,x,y,z,command_hash,actors,accepted,rejected,saves,readiness_stops,source_tick,decision_tick,source_x,source_y,source_z,direction,prep_x,prep_y,prep_z,dose_start_usec,dose_end_usec,dose_request_usec,hash_updates,hash_sha256"
var inventory: Dictionary = {}
var trials: Array[Dictionary] = []
var trial: Dictionary = {}
var active_scenario: Dictionary = {}
var abort_reason: String = ""
var cycle_boundaries: Array[Dictionary] = []
var dose_file: FileAccess
var dose_rows: int = 0
var dose_bytes: int = 0
var observer_writer_start: Dictionary = {}
var observer_writer_file: String = ""
var observer_writers: Array[Dictionary] = []
var requested_tick_cycles: String = "0"
var route_clock: Array[int] = []
var shipping_rows: Array[Dictionary] = []
var shipping_count: int = 0
var shipping_sum_usec: int = 0
var shipping_max_usec: int = 0
var shipping_misses: int = 0
var pose_file: FileAccess
var forensic_file: FileAccess
var pose_bytes: int = 0
var forensic_bytes: int = 0
var pilot_result: Dictionary = {}
var closure_spans: Array[Dictionary] = []
var drain_spans: Array[Dictionary] = []
var phase_first: int = 0
var callback_begin_usec: int = 0

func _configure_experiment() -> void:
	mode = "observer-attribution"
	test_mode = true
	render_size = 32
	workers = 1
	preparation_enabled = true
	inventory = JSON.parse_string(FileAccess.get_file_as_string(INVENTORY))
	scenarios.clear()
	_append_scenario("warmup", 0)
	for index: int in range(4): _append_scenario("bare", index)

func _append_scenario(group: String, index: int) -> void:
	scenarios.append({"id": "AB-H2-observer-%s-%d" % [group, index], "group": group, "index": index,
		"diagnostic_mode": "bare", "dose": false, "workload": "H2", "seconds": 72.0,
		"fixture": 3, "actors": 24, "rate": 4.0, "frontier_enabled": true})

func _full_height_observer_enabled() -> bool: return false
func _legacy_trace_validation_enabled() -> bool: return false
func _shipping_qualification() -> Dictionary: return pilot_result

func _is_forensic() -> bool: return false
func _is_shipping() -> bool: return false

func _capture_boundary(label: String) -> Dictionary:
	# Both reads surround common snapshot work. The identical record is shared
	# by the preceding and following section, never sampled twice at a handover.
	var before: Dictionary = probe.cpu_cycle_observation()
	var span: int = probe.observer_begin(12)
	var snapshot: Dictionary = probe.snapshot()
	if span > 0: probe.observer_end(span)
	var after: Dictionary = probe.cpu_cycle_observation()
	return {"label": label, "before": before, "snapshot": snapshot, "after": after,
		"bounds": Method.boundary_bounds(before, after), "wall_usec": Time.get_ticks_usec()}

func _start_scenario() -> void:
	finish_reason = ""
	active_scenario = scenarios[scenario_index].duplicate(true)
	cycle_boundaries.clear()
	cycle_boundaries.append(_capture_boundary("start"))
	var begin: int = cycle_boundaries[0].wall_usec
	observer_writers.clear()
	if not probe.observer_start(report_dir.path_join(str(active_scenario.id) + "-observers.bin")):
		finish_reason = "Observer ledger could not start"
	_reset_route_state()
	trial = {"id": active_scenario["id"], "group": active_scenario["group"], "index": active_scenario["index"],
		"diagnostic_mode": active_scenario["diagnostic_mode"], "dose_enabled": active_scenario["dose"],
		"start_usec": begin, "inventory_sha256": FileAccess.get_sha256(INVENTORY), "valid": false,
		"dose": {"ticks": 0, "hash_updates": 0, "valid": true, "cycles": ["0", "0"],
			"reference_cycles": "0", "requested_tick_cycles": "0"}}
	phase_first = operation_phases.size()
	closure_spans.clear()
	drain_spans.clear()
	route_clock.clear()
	shipping_rows.clear()
	shipping_count = 0
	shipping_sum_usec = 0
	shipping_max_usec = 0
	shipping_misses = 0
	var optional_begin: int = Time.get_ticks_usec()
	if _is_shipping(): shipping_rows = []
	trial["optional_setup"] = {"start_usec": optional_begin, "end_usec": Time.get_ticks_usec(), "enabled": _is_shipping()}
	pose_bytes = 0
	forensic_bytes = 0
	dose_rows = 0
	dose_bytes = 0
	requested_tick_cycles = "0"
	trial.dose.requested_tick_cycles = requested_tick_cycles

	pose_file = FileAccess.open(report_dir.path_join(str(trial["id"]) + "-poses.csv"), FileAccess.WRITE)
	if pose_file == null: report_io_failed = true
	else: pose_file.store_line(POSE_HEADER)
	dose_file = FileAccess.open(report_dir.path_join(str(trial.id) + "-cycles.jsonl"), FileAccess.WRITE)
	if dose_file == null: report_io_failed = true
	if _is_forensic():
		forensic_file = FileAccess.open(report_dir.path_join(str(trial["id"]) + "-forensic.jsonl"), FileAccess.WRITE)
		if forensic_file == null: report_io_failed = true
	super._start_scenario()
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), _is_forensic())
	if cycle_boundaries[0].bounds.is_empty(): finish_reason = "Start process-cycle evidence unavailable or contradictory"

func _scenario_drained() -> void:
	_finish_trial()

func _open_reports(suffix: String = "") -> void:
	sink.set_observer_probe(probe)
	observer_writer_start = probe.cpu_cycle_observation()
	observer_writer_file = str(scenarios[scenario_index].id) + suffix + "-frames.csv"
	var span: int = probe.observer_begin(7)
	super._open_reports(suffix)
	raw_lines.clear()
	raw_lines.append(FRAME_HEADER + "," + ",".join(Frontier.COLUMNS))
	if not _is_forensic(): operation_lines.clear()
	probe.observer_end(span)

func _begin_phase(label: String, _trace: bool = true) -> void:
	super._begin_phase(label, _is_forensic())

func _close_phase() -> Dictionary:
	var span: int = probe.observer_begin(7)
	var begin: int = Time.get_ticks_usec()
	var result: Dictionary = super._close_phase()
	if not result.is_empty(): closure_spans.append({"phase": result["phase"], "start_usec": begin, "end_usec": Time.get_ticks_usec()})
	probe.observer_end(span)
	return result

func _close_reports() -> void:
	if not reports_open: return
	var begin: int = Time.get_ticks_usec()
	await super._close_reports()
	observer_writers.append({"file": observer_writer_file, "process_start": observer_writer_start,
		"process_end": probe.cpu_cycle_observation(), "worker": sink.observer_worker_snapshot()})
	drain_spans.append({"start_usec": begin, "end_usec": Time.get_ticks_usec()})

func _reset_route_state() -> void:
	# Preparation calls _sync_pose too: discard the preceding trial's final leg.
	simulation_ticks = 0
	full_command_hash = 0
	previous_pose = FULL_ORIGIN
	previous_tick = 0
	source_pose = FULL_ORIGIN
	source_tick = 0
	preparation_direction = 0
	preparation_decision_tick = 0

func _begin_measurement() -> void:
	_reset_route_state()
	await super._begin_measurement()
	cycle_boundaries.append(_capture_boundary("prepared"))
	probe.observer_section(1)
	route_clock.append(int(cycle_boundaries[-1].wall_usec))
	if cycle_boundaries[-1].bounds.is_empty(): finish_reason = "Preparation cycle evidence unavailable or contradictory"
	status_label.text = "Observer attribution • %s • %s • trial %d" % [active_scenario["group"], active_scenario["diagnostic_mode"], scenario_index + 1]
	detail_label.text = "72 seconds of fixed +X/-X/+Z work, then complete closure.\nNo profile matrix or automatic calibration rerun."

func _capture_workload_contract() -> Dictionary:
	var result: Dictionary = super._capture_workload_contract()
	result.merge({"version": ATTR_VERSION, "full_height_observation": false,
		"operation_trace": _is_forensic(), "render_queries": _is_forensic(),
		"diagnostic_mode": active_scenario["diagnostic_mode"], "inventory_sha256": FileAccess.get_sha256(INVENTORY),
		"common_qualification_observer": true}, true)
	return result

func _physics_step(delta: float) -> void:
	if not finish_reason.is_empty(): return
	var before: int = simulation_ticks
	super._physics_step(delta)
	if simulation_ticks == before: return
	# Retain the same zero-request witness in every real tick. No positive
	# request exists in this attribution-only process.
	var native_span: int = probe.observer_begin(5)
	var work: Dictionary = probe.cpu_cycle_dose(requested_tick_cycles)
	probe.observer_end(native_span)
	var output_span: int = probe.observer_begin(6)
	work["tick"] = simulation_ticks
	work["cycles"] = Method.thread_demand(work.get("start", {}), work.get("end", {}))
	if not bool(work.get("passed", false)) or work.cycles.is_empty():
		trial.dose.valid = false
		finish_reason = "Native in-route cycle witness, SHA work or hard cap failed"

	var encoded: String = JSON.stringify(work) + "\n"
	dose_bytes += encoded.to_utf8_buffer().size()
	dose_rows += 1
	if dose_file == null or dose_bytes > 33554432 or dose_rows > TICKS: report_io_failed = true
	else:
		dose_file.store_string(encoded)
		if dose_file.get_error() != OK: report_io_failed = true
	if report_io_failed: finish_reason = "Cycle/pose witness I/O or byte cap failed"
	if simulation_ticks % 1440 == 0:
		probe.observer_end(output_span)
		cycle_boundaries.append(_capture_boundary(["+X", "-X", "+Z"][simulation_ticks / 1440 - 1]))
		route_clock.append(int(cycle_boundaries[-1].wall_usec))
		if cycle_boundaries[-1].bounds.is_empty(): finish_reason = "Route process-cycle evidence unavailable or contradictory"
		probe.observer_section(simulation_ticks / 1440 + 1)
		output_span = probe.observer_begin(6, 0)
	var now: int = route_clock[-1] if simulation_ticks % 1440 == 0 else Time.get_ticks_usec()
	var center: Vector3 = preparation.position
	var row: String = "%d,%d,%.9f,%.9f,%.9f,%d,%d,%d,%d,%d,%d,%d,%d,%.9f,%.9f,%.9f,%d,%.9f,%.9f,%.9f,%d,%d,%d,%d,%s" % [simulation_ticks, now,
		player.x, player.y, player.z, full_command_hash, actor_ticks, accepted_edits, rejected_edits, proxy_saves, readiness_stops,
		source_tick, preparation_decision_tick, source_pose.x, source_pose.y, source_pose.z, preparation_direction,
		center.x, center.y, center.z, 0, 0, 0, 0, "-"]
	pose_bytes += row.length() + 1
	if pose_file == null or pose_bytes > 8388608: report_io_failed = true
	else:
		pose_file.store_line(row)
		if pose_file.get_error() != OK: report_io_failed = true
	probe.observer_end(output_span)
	if int(probe.observer_status().failure_code) != 0: finish_reason = "Observer span, counter, ownership or trace cap failed"

func _process_frame(now: int) -> void:
	if not finish_reason.is_empty() and state in ["loading", "running", "acknowledging"]:
		_finish("failed", finish_reason)
		return
	if state == "loading":
		var prep_span: int = probe.observer_begin(1)
		var prep_stats: Dictionary = terrain.get_statistics()
		var prep_native: Dictionary = probe.snapshot()
		var ready: bool = int(prep_stats.get("resident_data", 0)) > 0 and int(prep_stats.get("pending_data", 1)) + int(prep_stats.get("pending_mesh", 1)) + int(prep_stats.get("loading_data", 1)) == 0 and int(prep_native["generation_jobs"]) + int(prep_native["mesh_jobs"]) + int(prep_native["main_jobs"]) == 0
		probe.observer_end(prep_span)
		if int(probe.observer_status().failure_code) != 0:
			finish_reason = "Preparation observer span, counter or cap failed"
		elif int(prep_native["overloads"]) > 0:
			finish_reason = "Fixture exceeded native mesh admission"
		elif Time.get_ticks_msec() - loading_started > 180000:
			finish_reason = "Terrain did not become ready within three minutes"
		elif ready:
			loading_seconds = float(Time.get_ticks_msec() - loading_started) / 1000.0
			_begin_measurement()
		return
	if state not in ["running", "acknowledging"]:
		if state == "draining":
			var tail: Dictionary = probe.snapshot()
			# Upstream main_jobs does not describe every retained resource/result.
			# Keep this native phase open until all declared work actually drains.
			if int(tail.get("retired_meshes", -1)) != 0 or int(tail.get("result_jobs", -1)) != 0:
				if _is_forensic(): _drain_operation_frames()
				if Time.get_ticks_msec() - loading_started > 180000:
					_finish("failed", "Pilot result/retirement queues did not drain within three minutes")
				return
		super._process_frame(now)
		return
	_advance_preparation()
	var callback_span: int = probe.observer_begin(4)
	if edit_trace_active:
		probe.tick_edit_trace()
		_drain_edit_events()
	if _is_forensic(): _drain_operation_frames()
	var interval: int = now - last_frame_usec
	var frame_ms: float = float(interval) / 1000.0
	diagnostics.record_interval(interval)
	last_frame_usec = now
	elapsed_wall += float(interval) / 1000000.0
	sample_count += 1
	sum_ms += frame_ms
	max_ms = maxf(max_ms, frame_ms)
	histogram[mini(100000, int(ceil(frame_ms * 100.0)))] += 1
	if frame_ms > 33.333: misses += 1
	var query_span: int = probe.observer_begin(2)
	var counters: Dictionary = probe.snapshot()
	var stats: Dictionary = terrain.get_statistics()
	for key: String in ["private_bytes", "working_set", "generation_jobs", "mesh_jobs", "result_jobs", "main_jobs"]:
		peaks[key] = maxi(int(peaks.get(key, 0)), int(counters.get(key, 0)))
	for key: String in ["resident_data", "resident_mesh", "pending_data", "pending_mesh"]:
		peaks[key] = maxi(int(peaks.get(key, 0)), int(stats.get(key, 0)))
	var pools: Dictionary = VoxelEngine.get_stats()["memory_pools"]
	for key: String in ["voxel_total", "voxel_used", "block_count"]:
		peaks["pool_" + key] = maxi(int(peaks.get("pool_" + key, 0)), int(pools[key]))
	probe.observer_end(query_span)
	var frontier_span: int = probe.observer_begin(3)
	var sample: Dictionary = _frontier_sample()
	probe.observer_end(frontier_span)
	var alarm: int = int(sample.get("evaluation", "") == "failed")
	raw_lines.append("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d" % [sample_count, now, interval, simulation_ticks,
		stats.get("resident_mesh", 0), stats.get("resident_data", 0), counters["generation_jobs"], counters["mesh_jobs"],
		counters["result_jobs"], counters["retired_meshes"], accepted_edits, readiness_stops, alarm] + "," + ",".join(Frontier.csv_fields(sample)))
	if raw_lines.size() >= 128: _flush_csv()
	if _is_shipping():
		shipping_count += 1
		shipping_sum_usec += interval
		shipping_max_usec = maxi(shipping_max_usec, interval)
		if interval > 33333: shipping_misses += 1
		if simulation_ticks >= (shipping_rows.size() + 1) * 60 and shipping_rows.size() < 72:
			shipping_rows.append({"second": shipping_rows.size() + 1, "tick": simulation_ticks,
				"native": probe.snapshot(), "terrain": terrain.get_statistics()})
	if _is_forensic():
		var detail: Dictionary = {"frame": sample_count, "usec": now, "native": counters, "terrain": stats,
			"frontier": sample, "render_cpu_ms": RenderingServer.viewport_get_measured_render_time_cpu(get_viewport().get_viewport_rid()),
			"render_gpu_ms": RenderingServer.viewport_get_measured_render_time_gpu(get_viewport().get_viewport_rid())}
		var encoded: String = JSON.stringify(detail)
		forensic_bytes += encoded.length() + 1
		if forensic_file == null or forensic_bytes > 67108864: report_io_failed = true
		else:
			forensic_file.store_line(encoded)
			if forensic_file.get_error() != OK: report_io_failed = true
		if sample_count % 30 == 0:
			status_label.text = "Forensic companion • %d / 72 seconds" % int(scenario_elapsed)
			detail_label.text = "%d frames • %d submitted commands; perturbing forensic mode" % [sample_count, accepted_edits]
	if int(counters["overloads"]) > 0 or int(stats.get("resident_mesh", 0)) > 512 or int(stats.get("resident_data", 0)) > 8192:
		finish_reason = "Pilot admission/resource envelope failed"
	elif elapsed_wall > 174.0 or sample_count > 500000: finish_reason = "Pilot exceeded fixed-work wall/sample bound"
	elif simulation_ticks >= TICKS: end_requested = true
	probe.observer_end(callback_span)
	if int(probe.observer_status().failure_code) != 0: finish_reason = "Callback observer span, counter, ownership or trace cap failed"

func _end_scenario() -> void:
	trial["last_command_usec"] = route_clock[-1] if route_clock.size() == 4 else 0
	await super._end_scenario()

func _write_json(name: String, value: Dictionary) -> bool:
	var file := FileAccess.open(report_dir.path_join(name), FileAccess.WRITE)
	if file == null: return false
	file.store_string(JSON.stringify(value, "  "))
	file.flush()
	var ok: bool = file.get_error() == OK
	file.close()
	return ok

func _finish_trial() -> void:
	var report_span: int = probe.observer_begin(7)
	var final_native: Dictionary = probe.snapshot()
	var drained: bool = true
	for key: String in ["generation_jobs", "mesh_jobs", "result_jobs", "main_jobs", "retired_meshes"]:
		if int(final_native[key]) != 0: drained = false
	for file: FileAccess in [pose_file, forensic_file, dose_file]:
		if file != null:
			file.flush()
			if file.get_error() != OK: report_io_failed = true
			file.close()
	pose_file = null
	forensic_file = null
	dose_file = null
	var shipping_begin: int = Time.get_ticks_usec()
	if _is_shipping():
		if not _write_json(str(trial["id"]) + "-shipping.json", {"rows": shipping_rows, "interval_count": shipping_count,
			"interval_sum_usec": shipping_sum_usec, "interval_max_usec": shipping_max_usec, "deadline_misses": shipping_misses}): report_io_failed = true
		# Dispose optional retained telemetry inside its own trial, never in A3's
		# next bare setup (which would charge switched cleanup to the reference).
		shipping_rows.clear()
	trial["optional_finalization"] = {"start_usec": shipping_begin, "end_usec": Time.get_ticks_usec(), "enabled": _is_shipping()}
	var phases: Array = operation_phases.slice(phase_first)
	var operation_ok: bool = phases.size() == 3
	for phase: Dictionary in phases:
		if not Evaluation.operation_failures(phase).is_empty(): operation_ok = false
	var report: Dictionary = reports[-1] if not reports.is_empty() else {}
	var resource_ok: bool = int(peaks.get("private_bytes", 0)) > 0 and int(peaks.get("private_bytes", 0)) <= 2147483648 and int(peaks.get("working_set", 0)) > 0 and int(peaks.get("working_set", 0)) <= 1610612736 and int(peaks.get("pool_voxel_total", 0)) <= 201326592
	var visibility: Dictionary = report.get("edit_visibility", {})
	var edits_ok: bool = int(visibility.get("accepted", -1)) == 288 and int(visibility.get("submitted", -1)) == 288 and int(visibility.get("p95_upper_usec", -1)) > 0 and int(visibility.get("p95_upper_usec", -1)) <= 100000 and int(visibility.get("max_usec", -1)) >= 0 and int(visibility.get("max_usec", -1)) <= 200000
	for key: String in ["pending", "queued", "overflow", "superseded", "cancelled", "timeout", "unavailable"]:
		edits_ok = edits_ok and int(visibility.get(key, -1)) == 0
	trial["checks"] = {"integration": integration_failures.is_empty(), "io": not report_io_failed,
		"drained": drained, "operations": operation_ok, "resources": resource_ok, "edits": edits_ok,
		"route_clocks": route_clock.size() == 4, "ticks": simulation_ticks == TICKS,
		"accepted": accepted_edits == 288, "rejected": rejected_edits == 0, "saves": proxy_saves == 72,
		"actors": actor_ticks == 103680, "readiness": readiness_stops == 0, "policy": not policy_failed,
		"coverage": int(report.get("fog_frontier", {}).get("exposed_samples", -1)) == 0 and report.get("fog_frontier", {}).get("evaluation", "") == "passed"}
	trial.merge({"valid": integration_failures.is_empty() and not report_io_failed and drained and operation_ok and resource_ok and edits_ok and route_clock.size() == 4 and simulation_ticks == TICKS and accepted_edits == 288 and rejected_edits == 0 and proxy_saves == 72 and actor_ticks == 103680 and readiness_stops == 0 and not policy_failed and int(report.get("fog_frontier", {}).get("exposed_samples", -1)) == 0 and report.get("fog_frontier", {}).get("evaluation", "") == "passed",
		"policy_failed": policy_failed,
		"route_clocks_usec": route_clock.duplicate(), "report": report, "phases": phases,
		"closures": closure_spans.duplicate(true), "writer_drains": drain_spans.duplicate(true),
		"native_final": final_native, "drained": drained, "operation_ok": operation_ok,
		"io_failed": report_io_failed, "integration_failures": integration_failures.duplicate(),
		"pose_sha256": FileAccess.get_sha256(report_dir.path_join(str(trial["id"]) + "-poses.csv")),
		"pose_bytes": pose_bytes, "forensic_bytes": forensic_bytes, "dose_rows": dose_rows, "dose_bytes": dose_bytes,
		"dose_sha256": FileAccess.get_sha256(report_dir.path_join(str(trial.id) + "-cycles.jsonl")),
		"callback_count": diagnostics.callbacks, "callback_last_end_usec": diagnostics.last_callback_end_usec,
		"renderer_queries": _is_forensic(), "raw_operation_trace": _is_forensic()}, true)
	var serialize_begin: int = Time.get_ticks_usec()
	var filename: String = str(trial["id"]) + "-complete.json"
	trial["pre_boundary_checks"] = trial.checks.duplicate(true)
	var complete_report: Dictionary = trial.duplicate(true)
	complete_report.erase("valid")
	complete_report.erase("checks")
	if not _write_json(filename, complete_report):
		report_io_failed = true
		trial["valid"] = false
	probe.observer_end(report_span)
	trial["observer_writers"] = observer_writers.duplicate(true)
	trial["observer"] = probe.observer_finish()
	var observer_path: String = report_dir.path_join(str(trial.id) + "-observers.bin")
	trial["observer_sha256"] = FileAccess.get_sha256(observer_path) if FileAccess.file_exists(observer_path) else ""
	cycle_boundaries.append(_capture_boundary("complete-after-report-flush"))
	var end: int = cycle_boundaries[-1].wall_usec
	trial["end_usec"] = end
	trial["duration_usec"] = end - int(trial["start_usec"])
	trial["report_finalization"] = {"start_usec": serialize_begin, "end_usec": end}
	var sections: Array[int] = []
	var clocks: Array = [trial["start_usec"]] + route_clock + [end]
	for index: int in range(clocks.size() - 1): sections.append(int(clocks[index + 1]) - int(clocks[index]))
	trial["sections_usec"] = sections
	trial["cycle_boundaries"] = cycle_boundaries.duplicate(true)
	trial["cycle"] = Method.partition(cycle_boundaries)
	trial.checks["cycles"] = not trial.cycle.is_empty()
	trial.checks["dose"] = bool(trial.dose.valid)
	trial.checks["observers"] = bool(trial.observer.get("passed", false)) and not Method.process_demand(trial.observer.get("emit_start", {}), trial.observer.get("emit_end", {})).is_empty() and not Method.thread_demand(trial.observer.get("emit_start", {}), trial.observer.get("emit_end", {})).is_empty()
	trial.valid = bool(trial.valid) and trial.checks.cycles and trial.checks.dose and trial.checks.observers
	var marker_start: Dictionary = probe.cpu_cycle_observation()
	var marker_begin: int = Time.get_ticks_usec()
	if not _write_json(str(trial["id"]) + "-boundary.json", {"id": trial["id"], "start_usec": trial["start_usec"],
		"end_usec": end, "duration_usec": trial["duration_usec"], "sections_usec": sections,
		"cycle_boundaries": trial.cycle_boundaries, "cycle": trial.cycle.duplicate(true),
		"observer": trial.observer, "observer_sha256": trial.observer_sha256, "observer_writers": trial.observer_writers,
		"report_finalization": trial["report_finalization"], "complete_sha256": FileAccess.get_sha256(report_dir.path_join(filename))}):
		report_io_failed = true
		trial["valid"] = false
	trial["marker_usec"] = Time.get_ticks_usec() - marker_begin
	trial["marker_start_usec"] = marker_begin
	trial["marker_end_usec"] = marker_begin + int(trial["marker_usec"])
	var marker_end: Dictionary = probe.cpu_cycle_observation()
	trial["marker_cycles"] = {"start": marker_start, "end": marker_end}
	var marker_bounds: Array = Method.process_demand(marker_start, marker_end)
	trial.checks["marker"] = not marker_bounds.is_empty()
	trial.checks["io"] = not report_io_failed
	trial["io_failed"] = report_io_failed
	trial.valid = bool(trial.valid) and trial.checks.marker and trial.checks.io
	if not trial.cycle.is_empty(): trial.cycle["marker"] = marker_bounds
	trial["complete"] = true
	trials.append(trial.duplicate(true))
	if not _write_json("sequence-prefix.json", {"trials": trials, "no_retry": true}): report_io_failed = true
	if not bool(trial.valid): abort_reason = "Attribution trial guard failed: " + str(trial.id)
	trial.clear()
	if not abort_reason.is_empty(): scenarios.resize(scenario_index + 1)
	# Exactly warm-up + four bare trials. Never append another group.

func _target_machine() -> bool:
	# This perturbing attribution mode can never qualify target performance.
	return false

func _finish_report(outcome: String, message: String) -> void:
	# An aborted route is evidence, never a fabricated complete trial. Close its
	# writers and retain its precise prefix without running a replacement trial.
	if not trial.is_empty():
		_close_phase()
		await _close_reports()
		for file: FileAccess in [pose_file, forensic_file, dose_file]:
			if file != null:
				file.flush()
				if file.get_error() != OK: report_io_failed = true
				file.close()
		pose_file = null
		forensic_file = null
		dose_file = null
		trial["observer_writers"] = observer_writers.duplicate(true)
		trial["observer"] = probe.observer_finish()
		var observer_path: String = report_dir.path_join(str(trial.id) + "-observers.bin")
		trial["observer_sha256"] = FileAccess.get_sha256(observer_path) if FileAccess.file_exists(observer_path) else ""
		abort_reason = message
		trial.merge({"complete": false, "valid": false, "abort_reason": message,
			"ticks": simulation_ticks, "cycle_boundaries": cycle_boundaries.duplicate(true),
			"dose_rows": dose_rows, "dose_bytes": dose_bytes, "pose_bytes": pose_bytes,
			"native_final": probe.snapshot(), "phases": operation_phases.slice(phase_first),
			"closures": closure_spans.duplicate(true), "writer_drains": drain_spans.duplicate(true),
			"io_failed": report_io_failed, "integration_failures": integration_failures.duplicate(),
			"pose_sha256": FileAccess.get_sha256(report_dir.path_join(str(trial.id) + "-poses.csv")),
			"dose_sha256": FileAccess.get_sha256(report_dir.path_join(str(trial.id) + "-cycles.jsonl"))}, true)
		_write_json(str(trial.id) + "-partial.json", trial)
		trials.append(trial.duplicate(true))
		trial.clear()
	pilot_result = {"method": ATTR_VERSION, "qualified": false, "outcome": "inconclusive",
		"controls": {"valid": false}, "shipping_cost_estimate": null}
	if abort_reason.is_empty() and pilot_result.outcome == "inconclusive": abort_reason = "Attribution prefix ended; no continuation permitted"
	pilot_result["abort_reason"] = abort_reason
	var valid: bool = not trials.is_empty()
	for t: Dictionary in trials:
		valid = valid and bool(t.valid)
	var elapsed: Dictionary = {}
	for item: Array in [["bare", 1]]:
		if trials.size() >= item[1] + 4: elapsed[item[0]] = Elapsed.envelope(trials.slice(item[1], item[1] + 4))
	var result: Dictionary = {"version": ATTR_VERSION, "policy": Method.POLICY, "build": build_info,
		"machine": initial_machine, "inventory": inventory, "inventory_sha256": FileAccess.get_sha256(INVENTORY),
		"trial_guards_valid": valid, "measurement_valid": valid and bool(pilot_result.controls.valid), "qualified": false, "target_performance": "not_run",
		"trials": trials, "assessment": pilot_result, "abort_reason": abort_reason,
		"elapsed_descriptive": elapsed, "descriptive_cycle_null": Method.envelope(trials.slice(1, 5)) if trials.size() == 5 else {}, "max_trials": 5,
		"scope": "perturbing common-observer attribution only; no cost estimate, continuation or target qualification"}
	if not _write_json("observer-attribution.json", result): integration_failures.append("Attribution summary write failed")
	await super._finish_report(outcome, message)
	status_label.text = "Observer attribution: " + str(pilot_result.outcome)
	detail_label.text = "Keep all complete and partial evidence. M1 remains unqualified.\n" + abort_reason
	print("CAIRN_SHIPPING_OBSERVER=" + JSON.stringify({"measurement_valid": valid and bool(pilot_result.controls.valid), "qualified": false,
		"outcome": pilot_result.outcome, "report_dir": report_dir, "trials": trials.size(),
		"abort_reason": abort_reason, "expected_exit": 0 if outcome == "completed" and integration_failures.is_empty() else 1}))
