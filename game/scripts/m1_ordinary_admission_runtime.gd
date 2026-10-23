extends "res://scripts/benchmark.gd"

# Production methods and ordinary ledgers only. No travel observer/admission trace.
var priority: bool = false
var policy_failed: bool = false
var phase_guards: Array[Dictionary] = []

func _ready() -> void:
	priority = "--mesh-admission-priority" in OS.get_cmdline_user_args()
	test_mode = true
	mode = "ordinary-admission"
	render_size = 16
	scenarios = [{"id": "AB-H2-ordinary", "workload": "H2", "seconds": 20.0,
		"fixture": 1, "actors": 24, "rate": 4.0, "frontier_enabled": true}]
	super._ready()
	startup.stop(Time.get_ticks_usec(), "ordinary path comparison; no startup observer")
	_disconnect_startup_signals()

func _duration() -> float:
	return 20.0

func _policy(enabled: bool) -> void:
	if is_instance_valid(terrain) and not probe.set_mesh_admission(terrain, enabled, camera.position, false):
		policy_failed = true

func _begin_phase(label: String, trace: bool = true) -> void:
	super._begin_phase(label, trace)
	_policy(priority and label == "overhead_diagnostic")

func _physics_step(delta: float) -> void:
	super._physics_step(delta)
	_policy(priority and state in ["running", "acknowledging"])

func _process_frame(now: int) -> void:
	_policy(priority and state in ["running", "acknowledging"])
	super._process_frame(now)

func _close_phase() -> Dictionary:
	_policy(false)
	var before: int = Time.get_ticks_usec()
	var result: Dictionary = super._close_phase()
	if not result.is_empty():
		phase_guards.append({"id": result["id"], "phase": result["phase"],
			"close_before_usec": before, "close_after_usec": Time.get_ticks_usec(),
			"failures": Evaluation.operation_failures(result)})
	return result

func _capture_workload_contract() -> Dictionary:
	var result: Dictionary = super._capture_workload_contract()
	result["admission_policy"] = "priority" if priority else "fifo"
	result["admission_trace"] = false
	result["replay_observation"] = false
	return result

func _finish_report(outcome: String, message: String) -> void:
	if policy_failed: integration_failures.append("Native ordinary admission policy rejected")
	await super._finish_report(outcome, message)
	var final_native: Dictionary = probe.snapshot()
	var trace: Dictionary = probe.mesh_admission_snapshot()
	var drained: bool = true
	for key: String in ["generation_jobs", "mesh_jobs", "result_jobs", "main_jobs", "retired_meshes"]:
		if int(final_native[key]) != 0: drained = false
	var result: Dictionary = {"version": "m1-ordinary-admission-1", "build": build_info,
		"passed": outcome == "completed" and integration_failures.is_empty() and drained and not bool(trace["enabled"]) and int(trace["recorded"]) == 0,
		"qualified": false, "target_performance": "not_run", "priority": priority,
		"phase_guards": phase_guards, "final_native": final_native, "drained": drained,
		"admission_trace": {"status": "unavailable", "rows": null, "selection_witnesses": null, "reason": "disabled by design"},
		"replay_observation": {"status": "unavailable", "rows": null, "resource_witnesses": null, "reason": "disabled by design"},
		"native_trace_state": trace, "scope": "ordinary ledgers; neither causal overhead nor target qualification"}
	var file := FileAccess.open(report_dir.path_join("ordinary-admission-summary.json"), FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(result, "  "))
		file.flush()
		if file.get_error() != OK: result["passed"] = false
		file.close()
	else: result["passed"] = false
	print("CAIRN_ORDINARY_ADMISSION=" + JSON.stringify(result))
