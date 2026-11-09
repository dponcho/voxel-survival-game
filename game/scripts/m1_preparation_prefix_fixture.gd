extends "res://scripts/m1_preparation_demand_runtime.gd"

# A controller fixture, never a short route. The inherited drain/handover and
# production prefix publication/start guard run; world setup is a counted seam.
var setup_calls: int = 0
var finish_calls: int = 0
var final_outcome: String = ""
var inject_prefix_failure: bool = false
var injected_open_error: int = OK
var immutable_files: Dictionary = {}
var fixture_io_ok: bool = true

func _ready() -> void:
	set_process(false)
	set_physics_process(false)

func _setup_trial() -> void:
	setup_calls += 1
	state = "loading"

func _close_phase() -> Dictionary:
	return {}

func _close_reports() -> void:
	reports_open = false

func _drain_operation_frames() -> void:
	pass

func _scenario_drained() -> void:
	_publish_finished_trial()

func _finish_report(outcome: String, _message: String) -> void:
	finish_calls += 1
	final_outcome = _publication_outcome(outcome)
	state = "finished"

func _write_json(name: String, value: Dictionary) -> bool:
	if name == "sequence-prefix.json" and inject_prefix_failure:
		# A real failed FileAccess open in the production JSON writer. The
		# intended prefix remains missing or retains its preceding bytes.
		var result: bool = super._write_json("write-blocker/sequence-prefix.json", value)
		injected_open_error = FileAccess.get_open_error()
		return result
	return super._write_json(name, value)

func stage(index: int, valid_trial: bool) -> void:
	var group: String = "warmup" if index == 0 else "bare"
	var number: int = 0 if index == 0 else index - 1
	var now: int = Time.get_ticks_usec()
	trial = {"id": "AB-H2-preparation-%s-%d" % [group, number], "group": group, "index": number,
		"diagnostic_mode": "bare", "dose_enabled": false, "dose": {"requested_tick_cycles": "0", "reference_cycles": "0"},
		"valid": valid_trial, "complete": true, "checks": {"io": true}, "io_failed": false,
		"start_usec": now, "end_usec": now, "marker_end_usec": now, "synthetic_controller_fixture": true}
	for suffix: String in ["-complete.json", "-boundary.json"]:
		var name: String = str(trial.id) + suffix
		fixture_io_ok = _write_json(name, trial.duplicate(true)) and fixture_io_ok
		immutable_files[name] = FileAccess.get_sha256(report_dir.path_join(name))

func exercise(folder: String, index: int, valid_trial: bool, fail_prefix: bool) -> Dictionary:
	report_dir = folder
	test_mode = false
	mode = "preparation-prefix-controller-control"
	scenarios.clear()
	_append_scenario("warmup", 0)
	for number: int in range(4): _append_scenario("bare", number)
	probe = CairnProbe.new()
	probe.configure(1, false)
	var before: Dictionary = probe.snapshot()
	for previous: int in range(index):
		scenario_index = previous
		stage(previous, true)
		_publish_finished_trial()
	scenario_index = index
	stage(index, valid_trial)
	var blocker := FileAccess.open(report_dir.path_join("write-blocker"), FileAccess.WRITE)
	if blocker == null: fixture_io_ok = false
	else:
		blocker.store_string("blocker\n")
		blocker.flush()
		fixture_io_ok = blocker.get_error() == OK and fixture_io_ok
		blocker.close()
	inject_prefix_failure = fail_prefix
	state = "draining"
	loading_started = Time.get_ticks_msec()
	await _process_frame(Time.get_ticks_usec())
	var refused_entry: bool = not abort_reason.is_empty()
	if refused_entry: _start_scenario() # Exercise the real stopped-entry guard.
	var immutable: bool = true
	for name: String in immutable_files:
		immutable = immutable and FileAccess.get_sha256(report_dir.path_join(name)) == immutable_files[name]
	return {"index": index, "valid_trial": valid_trial, "fail_prefix": fail_prefix,
		"fixture_io_ok": fixture_io_ok, "trials": trials, "prefix_publications": prefix_publications,
		"batch_publication_valid": _batch_publication_valid(), "abort_reason": abort_reason,
		"setup_calls": setup_calls, "finish_calls": finish_calls, "final_outcome": final_outcome,
		"stopped_entry_checked": refused_entry, "injected_open_error": injected_open_error,
		"immutable_files": immutable_files, "immutable_preserved": immutable,
		"native_before": before, "native_after": probe.snapshot(), "observer_active": probe.observer_status().active,
		"scope": "Synthetic completion; real publication/writer/start guard/inherited drain. Setup seam counts dispatch; no route or world setup."}
