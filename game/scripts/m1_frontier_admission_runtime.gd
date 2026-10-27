extends "res://scripts/m1_frontier_travel_runtime.gd"

const ADMISSION_ROW_CAP: int = 4096
const ADMISSION_BYTE_CAP: int = 33554432
var priority: bool = false
var admission_file: FileAccess
var admission_rows: int = 0
var admission_bytes: int = 0
var admission_failed: bool = false

func _ready() -> void:
	priority = "--mesh-admission-priority" in OS.get_cmdline_user_args()
	probe.begin_mesh_admission_trace()
	super._ready()
	admission_file = FileAccess.open(report_dir.path_join("mesh-admission.jsonl"), FileAccess.WRITE)
	if admission_file == null: admission_failed = true

func _create_terrain(fixture: int) -> void:
	super._create_terrain(fixture)
	if not probe.set_mesh_admission(terrain, false, player + Vector3(0, 1.65, 0), true):
		admission_failed = true

func _begin_phase(label: String, trace: bool = true) -> void:
	super._begin_phase(label, trace)
	if is_instance_valid(terrain) and not probe.set_mesh_admission(terrain, priority and label == "overhead_diagnostic", camera.position, true):
		admission_failed = true

func _close_phase() -> Dictionary:
	if is_instance_valid(terrain) and not probe.set_mesh_admission(terrain, false, camera.position, true):
		admission_failed = true
	return super._close_phase()

func _process_frame(now: int) -> void:
	_drain_admission()
	if is_instance_valid(terrain) and not probe.set_mesh_admission(terrain, priority and state in ["running", "acknowledging"], camera.position, true):
		admission_failed = true
	super._process_frame(now)

func _physics_step(delta: float) -> void:
	super._physics_step(delta)
	if is_instance_valid(terrain) and not probe.set_mesh_admission(terrain, priority and state in ["running", "acknowledging"], camera.position, true):
		admission_failed = true

func _drain_admission() -> void:
	for row: Dictionary in probe.take_mesh_admission_frames():
		var encoded: String = JSON.stringify(row) + "\n"
		var size: int = encoded.to_utf8_buffer().size()
		if admission_file == null or size >= 65536 or admission_rows >= ADMISSION_ROW_CAP or admission_bytes + size > ADMISSION_BYTE_CAP:
			admission_failed = true
			continue
		admission_file.store_string(encoded)
		admission_rows += 1
		admission_bytes += size
		if admission_file.get_error() != OK: admission_failed = true

func _finish_report(outcome: String, message: String) -> void:
	# Native/frame/edit accounting and the production combined report remain intact.
	_drain_admission()
	if admission_failed: integration_failures.append("Mesh admission trace unavailable, overflowed or I/O failed")
	await super._finish_report(outcome, message)
	var begin: int = Time.get_ticks_usec()
	_drain_admission()
	if admission_file != null:
		admission_file.flush()
		admission_failed = admission_failed or admission_file.get_error() != OK
		admission_file.close()
	var snapshot: Dictionary = probe.mesh_admission_snapshot()
	var result: Dictionary = {"version": "m1-mesh-admission-1", "build": build_info,
		"passed": outcome == "completed" and integration_failures.is_empty() and not admission_failed,
		"qualified": false, "target_performance": "not_run", "priority": priority,
		"rows": admission_rows, "bytes": admission_bytes, "snapshot": snapshot,
		"row_cap": ADMISSION_ROW_CAP, "byte_cap": ADMISSION_BYTE_CAP,
		"trace_finalization_begin_usec": begin, "trace_finalization_end_usec": Time.get_ticks_usec(),
		"scope": "experimental native admission order; same continuous H2 work; observer perturbs wall time; no target/overhead qualification"}
	var file := FileAccess.open(report_dir.path_join("mesh-admission-summary.json"), FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(result, "  "))
		file.flush()
		if file.get_error() != OK: result["passed"] = false
		file.close()
	else: result["passed"] = false
	print("CAIRN_MESH_ADMISSION=" + JSON.stringify(result))
