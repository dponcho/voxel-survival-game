extends Node

# Cloud-only main-loop placement probe. No terrain workload or target qualification.
const CPU = preload("res://scripts/benchmark_cpu_dose.gd")
const Diagnostics = preload("res://scripts/benchmark_diagnostics.gd")
var directory: String = ""
var failures: Array[String] = []

class CallbackProbe extends Node:
	var controller: Variant
	var buffer := PackedByteArray()
	var phase: int = 0
	var frame: int = 0
	var started: int = 0
	var previous_entry: int = 0
	var cpu := CPU.new()
	var timing := Diagnostics.new()
	var rows: Array[Dictionary] = []
	var trials: Array[Dictionary] = []

	func _ready() -> void:
		buffer.resize(4096)
		buffer.fill(90)
		_begin()

	func _begin() -> void:
		frame = 0
		rows.clear()
		cpu = CPU.new()
		timing = Diagnostics.new()
		started = Time.get_ticks_usec()
		previous_entry = started
		timing.start(started)
		set_process(true)

	func _process(_delta: float) -> void:
		var begin: int = Time.get_ticks_usec()
		var interval: int = begin - previous_entry
		previous_entry = begin
		frame += 1
		var baseline := HashingContext.new()
		if baseline.start(HashingContext.HASH_SHA256) != OK: controller.failures.append("Baseline hash start failed")
		for update: int in range(8):
			if baseline.update(buffer) != OK: controller.failures.append("Baseline hash update failed")
		var baseline_digest: String = baseline.finish().hex_encode()
		var requested: int = 500 if phase in [1, 2] else 0
		var ds: Variant = null
		var de: Variant = null
		var updates: int = 0
		var digest: Variant = null
		if requested > 0:
			ds = Time.get_ticks_usec()
			var hash := HashingContext.new()
			if hash.start(HashingContext.HASH_SHA256) != OK: controller.failures.append("Dose hash start failed")
			# Each update is synchronous native mbedTLS work on the process thread.
			# Bound dispatches and wall time; never sleep, yield, spawn or perform I/O.
			while updates < 512 and (updates == 0 or Time.get_ticks_usec() - int(ds) < requested):
				if hash.update(buffer) != OK: controller.failures.append("Dose hash update failed")
				updates += 1
			digest = hash.finish().hex_encode()
			de = Time.get_ticks_usec()
			if updates == 0 or int(de) - int(ds) < requested or int(de) - int(ds) > 50000: controller.failures.append("Native CPU dose did not meet bounded request")
		var end: int = Time.get_ticks_usec()
		var tick: int = 1800 if frame > 28 else mini(5, int((frame - 1) * 6 / 28)) * 300 + 1
		cpu.record(tick, begin, end, ds, de, requested)
		timing.record_interval(interval)
		rows.append({"frame": frame, "tick": tick, "entry_usec": begin, "interval_usec": interval,
			"body_begin_usec": begin, "body_end_usec": end, "dose_begin_usec": ds, "dose_end_usec": de,
			"requested_usec": requested, "hash_updates": updates, "hash_sha256": digest, "baseline_sha256": baseline_digest,
			"previous_frame": timing.callbacks, "previous_callback_usec": timing.last_callback_usec})
		timing.record_callback(begin, Time.get_ticks_usec())
		rows[-1]["complete_callback_end_usec"] = timing.last_callback_end_usec
		if frame == 32:
			set_process(false)
			call_deferred("_close")

	func _close() -> void:
		var drain_begin: int = Time.get_ticks_usec()
		var name: String = "callback-" + str(phase) + ".jsonl"
		var file := FileAccess.open(controller.directory.path_join(name), FileAccess.WRITE)
		if file == null:
			controller.failures.append("Cannot save CPU callback rows")
		else:
			for row: Dictionary in rows: file.store_line(JSON.stringify(row))
			file.flush()
			if file.get_error() != OK: controller.failures.append("CPU callback row write failed")
			file.close()
		var drain_end: int = Time.get_ticks_usec()
		var report: Dictionary = {"index": phase, "raw_file": name, "callbacks": frame, "cpu_dose_accounting": cpu.snapshot(),
			"writer_drain_begin_usec": drain_begin, "writer_drain_end_usec": drain_end,
			"scope": "32 real native-hash process callbacks; terrain/actors/1800-tick workload not run"}
		report["diagnostic_accounting"] = timing.snapshot(Time.get_ticks_usec(), drain_end - drain_begin)
		trials.append(report)
		phase += 1
		if phase < 4: _begin()
		else: controller.complete(trials)

func _ready() -> void: call_deferred("_run")

func _run() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--cpu-output="): directory = argument.trim_prefix("--cpu-output=")
	if directory.is_empty():
		get_tree().quit(1)
		return
	var probe := CallbackProbe.new()
	probe.controller = self
	add_child(probe)

func complete(trials: Array[Dictionary]) -> void:
	var final_begin: int = Time.get_ticks_usec()
	var observations: Array[Dictionary] = []
	for trial: Dictionary in trials:
		var body: int = 0
		var dose: int = 0
		for b: Dictionary in trial["cpu_dose_accounting"]["bins"]:
			body += b["body_usec"]
			dose += b["dose_usec"]
		observations.append({"body_usec": body, "dose_usec": dose, "callbacks": trial["callbacks"]})
	var report: Dictionary = {"schema": 1, "passed": failures.is_empty(), "failures": failures,
		"build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")),
		"status": "placement_verified" if failures.is_empty() else "failed", "qualified": false, "experimental": true,
		"scope": "real synchronous native SHA256 callback placement; not hardware precision or matched terrain workload",
		"body_effect": CPU.effect(observations), "observations": observations, "trials": trials,
		"cpu_service_usec": null, "causal_probe_cost": null, "gpu_cost": null, "shared_causal_overhead": null,
		"max_callbacks": 128, "buffer_bytes": 4096, "max_hash_updates_per_callback": 512,
		"native_operation_evidence": "unavailable: no terrain/native voxel workload in this probe"}
	var file := FileAccess.open(directory.path_join("summary.json"), FileAccess.WRITE)
	if file == null: failures.append("CPU summary write failed")
	else:
		file.store_string(JSON.stringify(report))
		file.flush()
		if file.get_error() != OK: failures.append("CPU summary flush failed")
		file.close()
	var final_end: int = Time.get_ticks_usec()
	file = FileAccess.open(directory.path_join("report-finalization.json"), FileAccess.WRITE)
	if file == null: failures.append("CPU finalization record write failed")
	else:
		file.store_string(JSON.stringify({"start_usec": final_begin, "end_usec": final_end, "elapsed_usec": final_end - final_begin,
			"scope": "combined summary construction and write; excludes this terminal record write and process exit", "allocated_to_trials": false}))
		file.flush()
		if file.get_error() != OK: failures.append("CPU finalization flush failed")
		file.close()
	print("CAIRN_CPU_DOSE_RUNTIME=" + JSON.stringify(report))
	get_tree().quit(0 if failures.is_empty() else 1)
