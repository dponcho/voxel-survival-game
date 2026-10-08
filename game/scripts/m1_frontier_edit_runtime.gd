extends "res://scripts/m1_frontier_boundary_runtime.gd"

# Public second +X boundary, with one accepted edit touching both render cells.
# Observe current native resources/revisions through transfer and cancellation.
# Native timing guards remain separate from correctness; neither qualifies M1.
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")
const EDIT_BEFORE := Vector3(31.9917182922363, 1.65100002288818, 10.0)
const EDIT_CROSSED := Vector3(32.1000518798828, 1.65100002288818, 10.0)
const EDIT_VOXEL := Vector3i(128, 6, 10)
const ROW_CAP := 160
const OP_ROW_CAP := 20000
const OP_FILE_CAP := 8388608
var operation_file: FileAccess
var operation_rows: int = 0
var operation_bytes: int = 0
var phase_id: int = 0
var phases: Array[Dictionary] = []
var trace_active: bool = false
var sampler_controls: Dictionary = {}

func mesh_coordinates() -> Array:
	var result: Array = [Vector3i(7, 0, 0)]
	result.append_array(Preparation.cells(EDIT_BEFORE - Vector3(0, 1.65, 0)))
	result.append_array(Preparation.cells(EDIT_CROSSED - Vector3(0, 1.65, 0)))
	result.append(Vector3i(7, 1, 0)) # Actual submitted confirmed-empty region.
	return result

func pump() -> void:
	if trace_active: probe.tick_edit_trace()
	for row: Dictionary in probe.take_operation_frames():
		var encoded: String = JSON.stringify(row) + "\n"
		var size: int = encoded.to_utf8_buffer().size()
		if operation_file == null or operation_rows >= OP_ROW_CAP or operation_bytes + size > OP_FILE_CAP:
			fail("Edit handover operation evidence exceeded its bound or has no writer")
			continue
		operation_file.store_string(encoded)
		operation_rows += 1
		operation_bytes += size
		if operation_file.get_error() != OK: fail("Edit handover operation write failed")

func begin_phase(label: String) -> void:
	phase_id += 1
	var before: int = Time.get_ticks_usec()
	probe.begin_phase(phase_id, true)
	phases.append({"id": phase_id, "label": label, "begin_before_usec": before, "begin_usec": Time.get_ticks_usec()})

func end_phase() -> void:
	phases[-1]["end_before_usec"] = Time.get_ticks_usec()
	var phase: Dictionary = probe.end_phase()
	pump()
	phases[-1]["end_usec"] = Time.get_ticks_usec()
	phases[-1]["native"] = phase
	var reasons: Array[String] = Evaluation.operation_failures(phase)
	phases[-1]["operation_failures"] = reasons
	phases[-1]["operation_evaluation"] = "failed" if not reasons.is_empty() else "passed"

func observe(stage: String) -> Dictionary:
	pump()
	var row: Dictionary = super.observe(stage)
	var ready: Array[bool] = []
	for cell: Vector3i in Preparation.cells(EDIT_BEFORE - Vector3(0, 1.65, 0)):
		ready.append(terrain.is_area_meshed(area(cell)))
	row["original_targets_submitted"] = ready
	row["edit_trace"] = probe.edit_trace_snapshot() if trace_active else {"status": "not_run"}
	row["meshes"] = probe.sample_mesh_blocks(terrain, mesh_coordinates())
	return row

func check_sampler_controls() -> void:
	var too_many: Array = []
	for i: int in range(17): too_many.append(Vector3i(i, 0, 0))
	sampler_controls = {"null_terrain": probe.sample_mesh_blocks(null, [Vector3i.ZERO]),
		"empty_request": probe.sample_mesh_blocks(terrain, []),
		"oversized_request": probe.sample_mesh_blocks(terrain, too_many),
		"malformed_request": probe.sample_mesh_blocks(terrain, [[7, 0, 0]]),
		"duplicate_request": probe.sample_mesh_blocks(terrain, [Vector3i.ZERO, Vector3i.ZERO]),
		"missing_block": probe.sample_mesh_blocks(terrain, [Vector3i(200, 0, 200)])}
	for key: String in sampler_controls:
		var sample: Dictionary = sampler_controls[key]
		if key == "missing_block":
			if sample["status"] != "measured" or sample["blocks"][0]["state"] != "missing" or sample["blocks"][0]["desired_revision"] != null: fail("Absent native block became a passing revision")
		elif sample["status"] != "unavailable" or sample["blocks"] != null or sample["probe_usec"] != null:
			fail("Unavailable native mesh observation became a passing zero")

func drain() -> bool:
	for frame: int in range(3):
		await get_tree().process_frame
		pump()
	var begin: int = Time.get_ticks_msec()
	while Time.get_ticks_msec() - begin < 60000:
		var n: Dictionary = probe.snapshot()
		if int(n["generation_jobs"]) + int(n["mesh_jobs"]) + int(n["result_jobs"]) + int(n["main_jobs"]) + int(n["retired_meshes"]) == 0: return true
		await get_tree().process_frame
		pump()
	fail("Edit handover retirement timed out")
	return false

func edit_case(mode: String, workers: int) -> void:
	var name: String = mode + "-" + str(workers)
	var first_phase: int = phases.size()
	begin_phase(name + ":preparation")
	create(false, workers)
	pose(EDIT_BEFORE)
	preparation = Preparation.new()
	preparation.start(self, base.position)
	var begin: int = Time.get_ticks_usec()
	var settled: bool = await settle()
	var rows: Array[Dictionary] = [observe("prepared")]
	if not settled or rows[0]["original_targets_submitted"].has(false): fail("Second boundary was not prepared")
	if rows[0]["assessment"]["evaluation"] != "passed" or int(rows[0]["sample"].get("empty_regions", 0)) <= 0: fail("Second boundary coverage or confirmed-empty evidence failed")
	if sampler_controls.is_empty(): check_sampler_controls()
	end_phase()
	begin_phase(name + ":edit-transfer")
	probe.start_edit_trace(true)
	trace_active = true
	var accepted: bool = (terrain.generator as CairnFixture).try_edit(terrain, EDIT_VOXEL, 2)
	rows.append(observe("edit-accepted"))
	if not accepted or int(rows[-1]["edit_trace"]["accepted"]) != 1 or int(rows[-1]["edit_trace"]["pending"]) != 1: fail("Single border edit was not accepted and pending")
	# A real processing opportunity dispatches the queued replacement. No sleep,
	# pause, queue alteration or extra edit manufactures concurrency.
	await get_tree().process_frame
	rows.append(observe("edit-dispatched"))
	var concurrent: bool = int(rows[-1]["edit_trace"]["pending"]) == 1 and int(rows[-1]["terrain"]["pending_mesh"]) == 0
	if not concurrent: fail("Edit replacement was not dispatched and pending at transfer")
	if mode != "stationary": pose(EDIT_CROSSED)
	rows.append(observe("transfer-before-engine"))
	var cancellation: bool = mode.begins_with("cancel-")
	if mode != "cancel-before":
		for frame: int in range(1 if cancellation else 16):
			preparation.advance_process(base.position)
			await get_tree().process_frame
			rows.append(observe("transfer-" + str(frame)))
			if rows[-1]["assessment"]["evaluation"] != "passed" or rows[-1]["original_targets_submitted"].has(false): fail("Edit handover lost existing submitted coverage")
		if not cancellation:
			if not await settle(): fail("Edit handover failed to settle")
			rows.append(observe("transfer-settled"))
		elif int(rows[-1]["edit_trace"]["pending"]) != 1:
			fail("Cancellation did not exercise a pending handover replacement")
	if not cancellation and int(rows[-1]["edit_trace"]["submitted"]) != 1: fail("Accepted edit did not acknowledge both current revisions before retirement")
	end_phase()
	begin_phase(name + ":retirement")
	var cleanup_begin: int = Time.get_ticks_usec()
	preparation.dispose()
	if not preparation.viewers.is_empty(): fail("Edit handover retained preparation nodes")
	preparation = null
	terrain.queue_free()
	base.queue_free()
	data.queue_free()
	camera.queue_free()
	var cancellation_meshes: Dictionary = probe.sample_mesh_blocks(terrain, mesh_coordinates())
	var cancellation_trace: Dictionary = probe.edit_trace_snapshot()
	var drained: bool = await drain()
	var before_trace_stop: Dictionary = probe.edit_trace_snapshot()
	if not cancellation and int(before_trace_stop["pending"]) != 0: fail("Completed workload left edit pending until collection stop")
	var nodes_freed: bool = not is_instance_valid(terrain) and not is_instance_valid(base) and not is_instance_valid(data) and not is_instance_valid(camera)
	if not nodes_freed: fail("Native replay nodes survived retirement")
	var trace_stop_usec: int = Time.get_ticks_usec()
	probe.finish_edit_trace()
	var trace_stop_end_usec: int = Time.get_ticks_usec()
	trace_active = false
	var events: Array = probe.take_edit_events()
	var trace: Dictionary = probe.edit_trace_snapshot()
	if int(trace["accepted"]) != 1 or int(trace["pending"]) != 0 or int(trace["overflow"]) != 0 or int(trace["queued"]) != 0 or events.size() != 1: fail("Edit event accounting was incomplete")
	if events.size() == 1:
		var event: Dictionary = events[0]
		if event["voxel"] != [128, 6, 10] or event["targets"].size() != 2: fail("Border edit affected a different workload")
		if mode == "stationary" and event["outcome"] != "submitted": fail("Matched stationary edit failed")
		# Deferred deletion can let a current native submission win the race.
		# Otherwise existing collection close cancels the abandoned pending edit;
		# record that source explicitly, never call it an acknowledgement.
		if cancellation and event["outcome"] not in ["submitted", "cancelled"]: fail("Pending edit cancellation or current completion failed")
		if mode == "handover" and event["outcome"] != "submitted": fail("Handover superseded or lost the accepted edit without another edit")
		if int(event["latency_usec"]) > 200000: fail("Border edit exceeded unchanged 200 ms acknowledgement guard")
	end_phase()
	var operation_failed: bool = false
	for phase: Dictionary in phases.slice(first_phase):
		if phase["operation_evaluation"] == "failed": operation_failed = true
	cases.append({"name": name, "workers": workers, "mode": mode, "settled": settled, "concurrent": concurrent,
		"accepted": accepted, "drained": drained, "released_preparation_viewers": 4,
		"begin_usec": begin, "cleanup_begin_usec": cleanup_begin, "end_usec": Time.get_ticks_usec(),
		"rows": rows, "phases": phases.slice(first_phase), "peaks": peaks.duplicate(), "trace": trace, "events": events,
		"final_native": probe.snapshot(), "policy": Preparation.metadata(true),
		"cancellation_meshes": cancellation_meshes, "cancellation_trace": cancellation_trace,
		"before_trace_stop": before_trace_stop, "trace_stop_usec": trace_stop_usec, "trace_stop_end_usec": trace_stop_end_usec,
		"nodes_freed": nodes_freed, "terminal_source": "collection_stop" if int(before_trace_stop["pending"]) == 1 else "native",
		"drained_meshes": probe.sample_mesh_blocks(null, mesh_coordinates()),
		"operation_evaluation": "failed" if operation_failed else "passed",
		"edit_evaluation": "passed" if events.size() == 1 and events[0]["outcome"] in (["submitted", "cancelled"] if cancellation else ["submitted"]) else "failed"})

func _run() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--frontier-edit-output="): directory = arg.trim_prefix("--frontier-edit-output=")
	if directory.is_empty():
		get_tree().quit(1)
		return
	Frontier.configure_m1_fog(environment)
	operation_file = FileAccess.open(directory.path_join("operations.jsonl"), FileAccess.WRITE)
	if operation_file == null:
		get_tree().quit(1)
		return
	for workers: int in [1, 2]:
		for mode: String in ["stationary", "handover", "cancel-before", "cancel-overlap"]: await edit_case(mode, workers)
	operation_file.flush()
	if operation_file.get_error() != OK: fail("Edit handover operation flush failed")
	operation_file.close()
	var total_rows: int = 0
	for c: Dictionary in cases: total_rows += c["rows"].size()
	if total_rows > ROW_CAP: fail("Edit handover observation row cap exceeded")
	var missing: Dictionary = Frontier.evaluate(probe.sample_frontier(null, null, AABB()), Frontier.fog_configuration(environment, 96.0))
	var report: Dictionary = {"schema": 1, "version": "m1-frontier-edit-1", "passed": failures.is_empty(),
		"failures": failures, "build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")),
		"qualified": false, "target_performance": "not_run", "cases": cases, "missing_input": missing,
		"fog": Frontier.fog_configuration(environment, 96.0), "row_cap": ROW_CAP, "file_cap_bytes": 1048576,
		"operation_rows": operation_rows, "operation_bytes": operation_bytes,
		"operation_row_cap": OP_ROW_CAP, "operation_file_cap_bytes": OP_FILE_CAP,
		"sampler_controls": sampler_controls,
		"scope": "public second 16³ +X boundary; one accepted border edit; actual resources/current revisions/transfer/cancel; no qualification"}
	var encoded: String = JSON.stringify(report)
	if encoded.to_utf8_buffer().size() > 1048576: fail("Edit handover summary cap exceeded")
	else:
		var file := FileAccess.open(directory.path_join("summary.json"), FileAccess.WRITE)
		if file == null: fail("Edit handover summary open failed")
		else:
			file.store_string(encoded)
			file.flush()
			if file.get_error() != OK: fail("Edit handover summary write failed")
			file.close()
	print("CAIRN_FRONTIER_EDIT=" + encoded)
	get_tree().quit(0 if failures.is_empty() else 1)
