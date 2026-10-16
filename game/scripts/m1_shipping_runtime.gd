extends "res://scripts/m1_full_height_runtime.gd"

# This is the sole prospective shipping pilot, not another calibration family.
# The identical native binary/enforcement clocks are used in every mode.
const Method = preload("res://scripts/m1_shipping_method.gd")
const INVENTORY: String = "res://diagnostics/shipping_inventory.json"
const FRAME_HEADER: String = "frame,entry_usec,interval_usec,tick,resident_mesh,resident_data,generation_jobs,mesh_jobs,result_jobs,retired_meshes,accepted,readiness_stops,coverage_alarms"
const POSE_HEADER: String = "tick,usec,x,y,z,command_hash,actors,accepted,rejected,saves,readiness_stops,source_tick,decision_tick,source_x,source_y,source_z,direction,prep_x,prep_y,prep_z,dose_start_usec,dose_end_usec,dose_request_usec,hash_updates,hash_sha256"
var inventory: Dictionary = {}
var trials: Array[Dictionary] = []
var trial: Dictionary = {}
var active_scenario: Dictionary = {}
var single_mode: String = ""
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
var dose_buffer := PackedByteArray()
var positive_reference_usec: int = 0
var dose_request_usec: int = 0
var pilot_result: Dictionary = {}
var closure_spans: Array[Dictionary] = []
var drain_spans: Array[Dictionary] = []
var phase_first: int = 0
var callback_begin_usec: int = 0

func _configure_experiment() -> void:
	mode = "shipping-pilot"
	test_mode = "--shipping-pilot-check" in OS.get_cmdline_user_args()
	render_size = 32
	preparation_enabled = true
	inventory = JSON.parse_string(FileAccess.get_file_as_string(INVENTORY))
	dose_buffer.resize(4096)
	dose_buffer.fill(90)
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--shipping-pilot-case="): single_mode = argument.get_slice("=", 1)
	scenarios.clear()
	if not single_mode.is_empty():
		if not single_mode in ["bare", "shipping", "forensic"]:
			integration_failures.append("Unknown shipping mode")
			single_mode = "bare"
		_append_scenario("single", 0, single_mode)
		return
	_append_scenario("warmup", 0, "bare")
	for group: String in ["null", "positive"]:
		for index: int in range(4): _append_scenario(group, index, "bare", group == "positive" and index in [1, 2])

func _append_scenario(group: String, index: int, diagnostic_mode: String, dose: bool = false) -> void:
	scenarios.append({"id": "AB-pilot-%s-%d" % [group, index], "group": group, "index": index,
		"diagnostic_mode": diagnostic_mode, "dose": dose, "workload": "H2", "seconds": 72.0,
		"fixture": 3, "actors": 24, "rate": 4.0, "frontier_enabled": true})

func _full_height_observer_enabled() -> bool: return false
func _legacy_trace_validation_enabled() -> bool: return false
func _shipping_qualification() -> Dictionary: return pilot_result

func _is_forensic() -> bool: return active_scenario.get("diagnostic_mode", "bare") == "forensic"
func _is_shipping() -> bool: return active_scenario.get("diagnostic_mode", "bare") in ["shipping", "forensic"]

func _start_scenario() -> void:
	active_scenario = scenarios[scenario_index].duplicate(true)
	var begin: int = Time.get_ticks_usec()
	trial = {"id": active_scenario["id"], "group": active_scenario["group"], "index": active_scenario["index"],
		"diagnostic_mode": active_scenario["diagnostic_mode"], "dose_enabled": active_scenario["dose"],
		"start_usec": begin, "inventory_sha256": FileAccess.get_sha256(INVENTORY), "valid": false,
		"dose": {"ticks": 0, "actual_usec": 0, "hash_updates": 0, "valid": true,
			"reference_usec": positive_reference_usec, "requested_tick_usec": 0}}
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
	dose_request_usec = int(ceil(float(positive_reference_usec) * 0.02 / float(TICKS))) if active_scenario["dose"] else 0
	trial["dose"]["requested_tick_usec"] = dose_request_usec
	if active_scenario["dose"] and (dose_request_usec <= 0 or dose_request_usec > 2000):
		integration_failures.append("Positive dose request unavailable or above declared cap")
	pose_file = FileAccess.open(report_dir.path_join(str(trial["id"]) + "-poses.csv"), FileAccess.WRITE)
	if pose_file == null: report_io_failed = true
	else: pose_file.store_line(POSE_HEADER)
	if _is_forensic():
		forensic_file = FileAccess.open(report_dir.path_join(str(trial["id"]) + "-forensic.jsonl"), FileAccess.WRITE)
		if forensic_file == null: report_io_failed = true
	super._start_scenario()
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), _is_forensic())

func _scenario_drained() -> void:
	_finish_trial()

func _open_reports(suffix: String = "") -> void:
	super._open_reports(suffix)
	raw_lines.clear()
	raw_lines.append(FRAME_HEADER + "," + ",".join(Frontier.COLUMNS))
	if not _is_forensic(): operation_lines.clear()

func _begin_phase(label: String, _trace: bool = true) -> void:
	super._begin_phase(label, _is_forensic())

func _close_phase() -> Dictionary:
	var begin: int = Time.get_ticks_usec()
	var result: Dictionary = super._close_phase()
	if not result.is_empty(): closure_spans.append({"phase": result["phase"], "start_usec": begin, "end_usec": Time.get_ticks_usec()})
	return result

func _close_reports() -> void:
	if not reports_open: return
	var begin: int = Time.get_ticks_usec()
	await super._close_reports()
	drain_spans.append({"start_usec": begin, "end_usec": Time.get_ticks_usec()})

func _begin_measurement() -> void:
	full_command_hash = 0
	previous_pose = FULL_ORIGIN
	previous_tick = 0
	source_pose = FULL_ORIGIN
	source_tick = 0
	preparation_direction = 0
	preparation_decision_tick = 0
	await super._begin_measurement()
	route_clock.append(Time.get_ticks_usec())
	status_label.text = "Focused pilot • %s • %s • trial %d" % [active_scenario["group"], active_scenario["diagnostic_mode"], scenario_index + 1]
	detail_label.text = "72 seconds of fixed +X/-X/+Z work, then complete closure.\nNo profile matrix or automatic calibration rerun."

func _capture_workload_contract() -> Dictionary:
	var result: Dictionary = super._capture_workload_contract()
	result.merge({"version": Method.VERSION, "full_height_observation": false,
		"operation_trace": _is_forensic(), "render_queries": _is_forensic(),
		"diagnostic_mode": active_scenario["diagnostic_mode"], "inventory_sha256": FileAccess.get_sha256(INVENTORY),
		"common_qualification_observer": true}, true)
	return result

func _physics_step(delta: float) -> void:
	var before: int = simulation_ticks
	super._physics_step(delta)
	if simulation_ticks == before: return
	var ds: int = 0
	var de: int = 0
	var updates: int = 0
	var digest: String = "-"
	if active_scenario["dose"] and dose_request_usec > 0 and dose_request_usec <= 2000:
		ds = Time.get_ticks_usec()
		var hash := HashingContext.new()
		if hash.start(HashingContext.HASH_SHA256) != OK: trial["dose"]["valid"] = false
		while updates < 512 and (updates == 0 or Time.get_ticks_usec() - ds < dose_request_usec):
			if hash.update(dose_buffer) != OK: trial["dose"]["valid"] = false
			updates += 1
		digest = hash.finish().hex_encode()
		de = Time.get_ticks_usec()
		trial["dose"]["ticks"] += 1
		trial["dose"]["actual_usec"] += de - ds
		trial["dose"]["hash_updates"] += updates
		if de - ds < dose_request_usec or de - ds > 50000 or digest.length() != 64: trial["dose"]["valid"] = false
	var now: int = Time.get_ticks_usec()
	if simulation_ticks % 1440 == 0: route_clock.append(now)
	var center: Vector3 = preparation.position
	var row: String = "%d,%d,%.9f,%.9f,%.9f,%d,%d,%d,%d,%d,%d,%d,%d,%.9f,%.9f,%.9f,%d,%.9f,%.9f,%.9f,%d,%d,%d,%d,%s" % [simulation_ticks, now,
		player.x, player.y, player.z, full_command_hash, actor_ticks, accepted_edits, rejected_edits, proxy_saves, readiness_stops,
		source_tick, preparation_decision_tick, source_pose.x, source_pose.y, source_pose.z, preparation_direction,
		center.x, center.y, center.z, ds, de, dose_request_usec, updates, digest]
	pose_bytes += row.length() + 1
	if pose_file == null or pose_bytes > 8388608: report_io_failed = true
	else:
		pose_file.store_line(row)
		if pose_file.get_error() != OK: report_io_failed = true

func _process_frame(now: int) -> void:
	if state not in ["running", "acknowledging"]:
		super._process_frame(now)
		return
	_advance_preparation()
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
	var counters: Dictionary = probe.snapshot()
	var stats: Dictionary = terrain.get_statistics()
	for key: String in ["private_bytes", "working_set", "generation_jobs", "mesh_jobs", "result_jobs", "main_jobs"]:
		peaks[key] = maxi(int(peaks.get(key, 0)), int(counters.get(key, 0)))
	for key: String in ["resident_data", "resident_mesh", "pending_data", "pending_mesh"]:
		peaks[key] = maxi(int(peaks.get(key, 0)), int(stats.get(key, 0)))
	var pools: Dictionary = VoxelEngine.get_stats()["memory_pools"]
	for key: String in ["voxel_total", "voxel_used", "block_count"]:
		peaks["pool_" + key] = maxi(int(peaks.get("pool_" + key, 0)), int(pools[key]))
	var sample: Dictionary = _frontier_sample()
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
	var final_native: Dictionary = probe.snapshot()
	var drained: bool = true
	for key: String in ["generation_jobs", "mesh_jobs", "result_jobs", "main_jobs", "retired_meshes"]:
		if int(final_native[key]) != 0: drained = false
	for file: FileAccess in [pose_file, forensic_file]:
		if file != null:
			file.flush()
			if file.get_error() != OK: report_io_failed = true
			file.close()
	pose_file = null
	forensic_file = null
	var shipping_begin: int = Time.get_ticks_usec()
	if _is_shipping():
		if not _write_json(str(trial["id"]) + "-shipping.json", {"rows": shipping_rows, "interval_count": shipping_count,
			"interval_sum_usec": shipping_sum_usec, "interval_max_usec": shipping_max_usec, "deadline_misses": shipping_misses}): report_io_failed = true
	trial["optional_finalization"] = {"start_usec": shipping_begin, "end_usec": Time.get_ticks_usec(), "enabled": _is_shipping()}
	var phases: Array = operation_phases.slice(phase_first)
	var operation_ok: bool = phases.size() == 3
	for phase: Dictionary in phases:
		if not Evaluation.operation_failures(phase).is_empty(): operation_ok = false
	var report: Dictionary = reports[-1] if not reports.is_empty() else {}
	var resource_ok: bool = int(peaks.get("private_bytes", 0)) <= 2147483648 and int(peaks.get("working_set", 0)) <= 1610612736 and int(peaks.get("pool_voxel_total", 0)) <= 201326592
	trial.merge({"valid": integration_failures.is_empty() and not report_io_failed and drained and operation_ok and resource_ok and route_clock.size() == 4 and simulation_ticks == TICKS and accepted_edits == 288 and rejected_edits == 0 and proxy_saves == 72 and actor_ticks == 103680 and readiness_stops == 0 and not policy_failed and int(report.get("fog_frontier", {}).get("exposed_samples", -1)) == 0 and report.get("fog_frontier", {}).get("evaluation", "") == "passed",
		"route_clocks_usec": route_clock.duplicate(), "report": report, "phases": phases,
		"closures": closure_spans.duplicate(true), "writer_drains": drain_spans.duplicate(true),
		"native_final": final_native, "drained": drained, "operation_ok": operation_ok,
		"io_failed": report_io_failed, "integration_failures": integration_failures.duplicate(),
		"pose_sha256": FileAccess.get_sha256(report_dir.path_join(str(trial["id"]) + "-poses.csv")),
		"pose_bytes": pose_bytes, "forensic_bytes": forensic_bytes,
		"callback_count": diagnostics.callbacks, "callback_last_end_usec": diagnostics.last_callback_end_usec,
		"renderer_queries": _is_forensic(), "raw_operation_trace": _is_forensic()}, true)
	var serialize_begin: int = Time.get_ticks_usec()
	var filename: String = str(trial["id"]) + "-complete.json"
	if not _write_json(filename, trial):
		report_io_failed = true
		trial["valid"] = false
	var end: int = Time.get_ticks_usec()
	trial["end_usec"] = end
	trial["duration_usec"] = end - int(trial["start_usec"])
	trial["report_finalization"] = {"start_usec": serialize_begin, "end_usec": end}
	var sections: Array[int] = []
	var clocks: Array = [trial["start_usec"]] + route_clock + [end]
	for index: int in range(clocks.size() - 1): sections.append(int(clocks[index + 1]) - int(clocks[index]))
	trial["sections_usec"] = sections
	var marker_begin: int = Time.get_ticks_usec()
	if not _write_json(str(trial["id"]) + "-boundary.json", {"id": trial["id"], "start_usec": trial["start_usec"],
		"end_usec": end, "duration_usec": trial["duration_usec"], "sections_usec": sections,
		"report_finalization": trial["report_finalization"], "complete_sha256": FileAccess.get_sha256(report_dir.path_join(filename))}):
		report_io_failed = true
		trial["valid"] = false
	trial["marker_usec"] = Time.get_ticks_usec() - marker_begin
	trial["marker_start_usec"] = marker_begin
	trial["marker_end_usec"] = marker_begin + int(trial["marker_usec"])
	trials.append(trial.duplicate(true))
	if active_scenario["group"] == "positive" and active_scenario["index"] == 0: positive_reference_usec = trial["duration_usec"]
	trial.clear()
	if trials.size() == 9 and single_mode.is_empty() and Method.controls(trials)["valid"]:
		for index: int in range(4): _append_scenario("shipping", index, "shipping" if index in [1, 2] else "bare")

func _target_machine() -> bool:
	# This declaration is intentionally narrow and does not certify pacing/GPU/M1.
	return initial_machine.get("platform", "") == "Windows" and initial_machine.get("display", "") != "headless" and "i7-7600U" in str(initial_machine.get("cpu", "")) and "620" in str(initial_machine.get("gpu", ""))

func _finish_report(outcome: String, message: String) -> void:
	if not trial.is_empty(): _finish_trial()
	pilot_result = Method.evaluate(trials, _target_machine())
	if not single_mode.is_empty():
		pilot_result["outcome"] = "not_run"
		pilot_result["qualified"] = false
	var passed: bool = outcome == "completed" and not trials.is_empty() and integration_failures.is_empty()
	for value: Dictionary in trials: passed = passed and bool(value["valid"])
	var result: Dictionary = {"version": Method.VERSION, "build": build_info, "machine": initial_machine,
		"inventory": inventory, "inventory_sha256": FileAccess.get_sha256(INVENTORY),
		"passed": passed, "qualified": false, "target_performance": "not_run", "single_mode": single_mode,
		"trials": trials, "assessment": pilot_result,
		"scope": "incremental declared optional shipping inventory; common qualification observers remain; not total diagnostic overhead or M1 qualification"}
	if not _write_json("shipping-pilot.json", result): integration_failures.append("Shipping pilot summary write failed")
	await super._finish_report(outcome, message)
	if not passed: integration_failures.append("Shipping pilot work/boundary/operation/I/O control failed")
	status_label.text = "Shipping diagnostic pilot: " + str(pilot_result["outcome"])
	detail_label.text = "Keep the complete report folder. M1 remains unqualified.\n" + str(pilot_result["stop_decision"])
	print("CAIRN_SHIPPING_PILOT=" + JSON.stringify({"passed": passed and integration_failures.is_empty(),
		"qualified": false, "outcome": pilot_result["outcome"], "report_dir": report_dir, "trials": trials.size()}))
