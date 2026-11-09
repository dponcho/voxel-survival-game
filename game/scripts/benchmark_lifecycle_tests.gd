extends RefCounted

# Exercise the actual scenario start and process/closure driver. Async native
# outcomes are covered by edit_visibility tests and saved export-smoke traces.
class Harness extends "res://scripts/benchmark.gd":
	var pending: int = 0
	var closed: bool = false
	var terminal_outcome: String = ""

	func _ready() -> void: pass
	func _open_reports(_suffix: String = "") -> void: pass
	func _begin_phase(_label: String, _trace: bool = true) -> void: pass
	func _create_terrain(_fixture: int) -> void:
		if viewer == null:
			viewer = VoxelViewer.new()
			data_viewer = VoxelViewer.new()
			add_child(viewer)
			add_child(data_viewer)
	func _pending_edits() -> int: return pending
	func _process_frame(now: int) -> void:
		diagnostics.record_interval(now - last_frame_usec)
		last_frame_usec = now
		sample_count += 1
	func _end_scenario() -> void:
		closed = true
		state = "reporting"
	func _finish(outcome: String, _message: String) -> void:
		terminal_outcome = outcome
		state = "finished"

static func verify(tree: SceneTree) -> Array[String]:
	var failures: Array[String] = []
	var fixture := Harness.new()
	fixture.set_process(false)
	fixture.set_physics_process(false)
	tree.root.add_child(fixture)
	fixture.set_process(false)
	fixture.set_physics_process(false)
	fixture._make_scene()
	fixture.status_label = Label.new()
	fixture.detail_label = Label.new()
	fixture.add_child(fixture.status_label)
	fixture.add_child(fixture.detail_label)
	# Reproduce a cave camera followed by both outward streaming fixtures.
	for index: int in [2, 3, 4]:
		fixture.scenario_index = index
		fixture.camera.position = Vector3(1200, -25, 80)
		fixture.camera.rotation = Vector3(0.7, 1.0, 0)
		fixture.scenario_elapsed = 255.0
		fixture._start_scenario()
		var expected: Vector3 = Vector3(10, -10, 2) if index == 2 else Vector3(10, 8, 10)
		if fixture.player != expected or fixture.viewer.position != expected or fixture.data_viewer.position != expected or fixture.camera.position != expected + Vector3(0, 1.65, 0):
			failures.append("New fixture kept a stale player/viewer/camera pose")
		if not is_equal_approx(fixture.camera.rotation.x, -0.18) or not is_equal_approx(fixture.camera.rotation.y, -PI * 0.5) or fixture.scenario_elapsed != 0.0:
			failures.append("New fixture kept the previous route clock or camera heading")

	fixture.state = "running"
	fixture.edit_trace_active = true
	fixture.end_requested = true
	fixture.pending = 1
	fixture.scenario_elapsed = 240.0
	fixture.sample_count = 0
	fixture.last_frame_usec = Time.get_ticks_usec()
	fixture.diagnostics.start(fixture.last_frame_usec)
	fixture._process(0.0)
	if fixture.closed or fixture.state != "acknowledging": failures.append("Last-tick edit was closed before asynchronous submission")
	var position_before: Vector3 = fixture.player
	var ticks_before: int = fixture.simulation_ticks
	fixture._physics_process(1.0 / 60.0)
	if fixture.player != position_before or fixture.simulation_ticks != ticks_before or fixture.scenario_elapsed != 240.0:
		failures.append("Acknowledgement extended the route or issued new workload")
	await tree.process_frame
	fixture._process(0.0)
	if fixture.closed: failures.append("Pending edit was cancelled on the next frame")
	fixture.pending = 0
	fixture._process(0.0)
	if not fixture.closed or fixture.sample_count != 3 or fixture.diagnostics.callbacks != 3:
		failures.append("Final acknowledgement frames were lost or closure did not resume")

	fixture.closed = false
	fixture.state = "running"
	fixture.pending = 1
	fixture._complete_scenario_if_ready(100)
	fixture._complete_scenario_if_ready(200100)
	if fixture.closed or not fixture.terminal_outcome.is_empty(): failures.append("Existing 200 ms acknowledgement window was shortened")
	fixture._complete_scenario_if_ready(200101)
	if fixture.terminal_outcome != "failed" or fixture.closed: failures.append("Permanently pending trace was reported complete or waited without a bound")
	fixture.state = "acknowledging"
	fixture.terminal_outcome = ""
	fixture._cancel()
	if not fixture.cancelled or fixture.terminal_outcome != "cancelled": failures.append("User cancellation waited for edit acknowledgement")
	fixture.free()
	return failures
