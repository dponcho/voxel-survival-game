extends Node

const Frame = preload("res://scripts/benchmark_frame_slack.gd")
const Diagnostics = preload("res://scripts/benchmark_diagnostics.gd")
var directory: String = ""
var failures: Array[String] = []
var old_max_fps: int = 0

class CycleProbe extends Node:
	var controller: Variant
	var buffer := PackedByteArray()
	var phase: int = 0
	var frame: int = 0
	var started: int = 0
	var first_entry: int = 0
	var ledger := Frame.new()
	var timing := Diagnostics.new()
	var rows: Array[Dictionary] = []
	var trials: Array[Dictionary] = []
	var anchor: Dictionary = {}

	func _ready() -> void:
		buffer.resize(4096)
		buffer.fill(90)
		_begin()

	func _begin() -> void:
		frame = 0
		rows.clear()
		ledger = Frame.new()
		timing = Diagnostics.new()
		started = Time.get_ticks_usec()
		timing.start(started)
		set_process(true)

	func _process(_delta: float) -> void:
		var entry: int = Time.get_ticks_usec()
		var engine_frame: int = Engine.get_process_frames()
		if not rows.is_empty():
			rows[-1]["next_entry_usec"] = entry
			rows[-1]["successor_engine_frame"] = engine_frame
			ledger.record(rows[-1])
			timing.record_interval(entry - int(rows[-1]["entry_usec"]))
		if frame == 32:
			anchor = {"entry_usec": entry, "engine_frame": engine_frame, "previous_callback_usec": timing.last_callback_usec}
			set_process(false)
			call_deferred("_close")
			anchor["complete_callback_end_usec"] = Time.get_ticks_usec()
			return
		if frame == 0: first_entry = entry
		frame += 1
		var begin: int = Time.get_ticks_usec()
		var common := HashingContext.new()
		if common.start(HashingContext.HASH_SHA256) != OK: controller.failures.append("Frame baseline hash start failed")
		for update: int in range(8):
			if common.update(buffer) != OK: controller.failures.append("Frame baseline hash failed")
		var baseline_digest: String = common.finish().hex_encode()
		var request: int = (500 if phase < 4 else 20000) if phase % 4 in [1, 2] else 0
		var ds: Variant = null
		var de: Variant = null
		var updates: int = 0
		var digest: Variant = null
		if request > 0:
			ds = Time.get_ticks_usec()
			var hash := HashingContext.new()
			if hash.start(HashingContext.HASH_SHA256) != OK: controller.failures.append("Frame dose hash start failed")
			while updates < 8192 and (updates == 0 or Time.get_ticks_usec() - int(ds) < request):
				if hash.update(buffer) != OK: controller.failures.append("Frame dose hash failed")
				updates += 1
			digest = hash.finish().hex_encode()
			de = Time.get_ticks_usec()
			if int(de) - int(ds) < request or int(de) - int(ds) > 100000: controller.failures.append("Frame dose outside bounded request")
		var end: int = Time.get_ticks_usec()
		var tick: int = 1800 if frame > 28 else mini(5, int((frame - 1) * 6 / 28)) * 300 + 1
		rows.append({"frame": frame, "tick": tick, "engine_frame": engine_frame, "entry_usec": entry,
			"body_begin_usec": begin, "body_end_usec": end, "dose_begin_usec": ds, "dose_end_usec": de,
			"requested_usec": request, "hash_updates": updates, "hash_sha256": digest, "baseline_sha256": baseline_digest,
			"baseline_updates": 8, "previous_callback_usec": timing.last_callback_usec})
		timing.record_callback(entry, Time.get_ticks_usec())
		rows[-1]["complete_callback_end_usec"] = timing.last_callback_end_usec

	func _close() -> void:
		var db: int = Time.get_ticks_usec()
		var name: String = "cycle-" + str(phase) + ".jsonl"
		var file := FileAccess.open(controller.directory.path_join(name), FileAccess.WRITE)
		if file == null: controller.failures.append("Frame rows open failed")
		else:
			for row: Dictionary in rows: file.store_line(JSON.stringify(row))
			file.flush()
			if file.get_error() != OK: controller.failures.append("Frame rows write failed")
			file.close()
		var de: int = Time.get_ticks_usec()
		var report: Dictionary = {"index": phase, "samples": frame, "completed": true, "work_units_valid": true,
			"operation_evaluation": "unavailable", "raw_file": name, "first_entry_usec": first_entry, "closing_anchor": anchor,
			"frame_slack_accounting": ledger.snapshot(), "phase_boundaries": {"callback_phase_closed_usec": anchor["complete_callback_end_usec"],
				"writer_drain_begin_usec": db, "writer_drain_end_usec": de}, "render_signals": null, "wait_service_usec": null,
			"native_operation_evidence": "unavailable: no terrain or voxel operation phase in this microprobe"}
		# Native phase closure is deliberately unavailable; this actual microprobe is
		# not fed into the hypothetical eligible-workload assessor.
		report["diagnostic_accounting"] = timing.snapshot(Time.get_ticks_usec(), de - db)
		trials.append(report)
		phase += 1
		if phase < 8: _begin()
		else: controller.complete(trials)

func _ready() -> void: call_deferred("_run")

func _run() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--frame-output="): directory = arg.trim_prefix("--frame-output=")
	if directory.is_empty():
		get_tree().quit(1)
		return
	old_max_fps = Engine.max_fps
	Engine.max_fps = 100
	var probe := CycleProbe.new()
	probe.controller = self
	add_child(probe)

func complete(trials: Array[Dictionary]) -> void:
	var final_begin: int = Time.get_ticks_usec()
	var gaps: Array[Dictionary] = []
	for index: int in range(8):
		var begin: int = trials[index]["diagnostic_accounting"]["end_usec"]
		var end: int = trials[index + 1]["diagnostic_accounting"]["start_usec"] if index < 7 else final_begin
		gaps.append({"begin_usec": begin, "end_usec": end, "elapsed_usec": end - begin,
			"scope": "unallocated snapshot/append/controller transition; not added to nested callback or cycle costs"})
	var groups: Array[Dictionary] = []
	for group: int in range(2):
		var observations: Array[Dictionary] = []
		for index: int in range(4):
			var trial: Dictionary = trials[group * 4 + index]
			var o: Dictionary = {"callbacks": trial["samples"], "cycle_usec": 0, "body_usec": 0, "dose_usec": 0}
			for b: Dictionary in trial["frame_slack_accounting"]["bins"]:
				for key: String in ["cycle_usec", "body_usec", "dose_usec"]: o[key] += b[key]
			observations.append(o)
		groups.append({"kind": "limiter_slack" if group == 0 else "beyond_limiter", "observations": observations,
			"effects": Frame.effects(observations), "status": "descriptive; cloud scheduling and limiter state not causal attribution"})
	Engine.max_fps = old_max_fps
	var report: Dictionary = {"schema": 1, "version": Frame.VERSION, "passed": failures.is_empty(), "failures": failures,
		"status": "placement_verified" if failures.is_empty() else "failed", "qualified": false, "experimental": true,
		"build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")), "trials": trials, "groups": groups, "unallocated_phase_gaps": gaps,
		"max_fps": 100, "restored_max_fps": Engine.max_fps, "old_max_fps": old_max_fps, "body_callbacks": 256, "closing_anchor_callbacks": 8,
		"buffer_bytes": 4096, "max_hash_updates": 8192, "render_signals": null, "wait_service_usec": null,
		"cpu_service_usec": null, "gpu_cost": null, "physical_presentation": null, "causal_probe_cost": null, "shared_causal_overhead": null,
		"scope": "real callback-entry cycles, engine limiter and native CPU placement; no terrain workload or target precision"}
	var file := FileAccess.open(directory.path_join("summary.json"), FileAccess.WRITE)
	if file == null: failures.append("Frame summary open failed")
	else:
		file.store_string(JSON.stringify(report))
		file.flush()
		if file.get_error() != OK: failures.append("Frame summary write failed")
		file.close()
	var final_end: int = Time.get_ticks_usec()
	file = FileAccess.open(directory.path_join("report-finalization.json"), FileAccess.WRITE)
	if file == null: failures.append("Frame finalization open failed")
	else:
		file.store_string(JSON.stringify({"start_usec": final_begin, "end_usec": final_end, "elapsed_usec": final_end - final_begin,
			"allocated_to_trials": false, "scope": "combined construction/write and limiter restore; excludes terminal record write and exit"}))
		file.flush()
		if file.get_error() != OK: failures.append("Frame finalization write failed")
		file.close()
	print("CAIRN_FRAME_SLACK_RUNTIME=" + JSON.stringify(report))
	get_tree().quit(0 if failures.is_empty() else 1)
