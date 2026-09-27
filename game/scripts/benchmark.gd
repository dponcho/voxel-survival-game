extends Node3D

# M1 engine experiment. Proxy activity is explicitly distinct from survival systems.
const SCENARIOS: Array[Dictionary] = [
	{"id": "warmup", "seconds": 180.0, "fixture": 0, "actors": 12, "rate": 0.0},
	{"id": "N1", "seconds": 180.0, "fixture": 1, "actors": 12, "rate": 0.0},
	{"id": "N2", "seconds": 180.0, "fixture": 1, "actors": 12, "rate": 2.0},
	{"id": "H1", "seconds": 240.0, "fixture": 1, "actors": 12, "rate": 0.0},
	{"id": "H2", "seconds": 240.0, "fixture": 1, "actors": 24, "rate": 4.0},
	{"id": "N3", "seconds": 120.0, "fixture": 2, "actors": 12, "rate": 2.0},
	{"id": "R1", "seconds": 60.0, "fixture": 2, "actors": 12, "rate": 0.0},
	{"id": "paced", "seconds": 120.0, "fixture": 1, "actors": 12, "rate": 2.0},
	{"id": "AB-off-1", "seconds": 30.0, "fixture": 0, "actors": 12, "rate": 0.0},
	{"id": "AB-on-1", "seconds": 30.0, "fixture": 0, "actors": 12, "rate": 0.0},
	{"id": "AB-on-2", "seconds": 30.0, "fixture": 0, "actors": 12, "rate": 0.0},
	{"id": "AB-off-2", "seconds": 30.0, "fixture": 0, "actors": 12, "rate": 0.0}
]
const PLAYER_BOX := AABB(Vector3(-0.3, 0.0, -0.3), Vector3(0.6, 1.8, 0.6))
const Evaluation = preload("res://scripts/benchmark_evaluation.gd")
const Diagnostics = preload("res://scripts/benchmark_diagnostics.gd")
var diagnostics := Diagnostics.new()
var end_requested: bool = false
var finish_reason: String = ""
var writer_drain_usec: int = 0
var reports_open: bool = false
var finishing: bool = false
var probe: CairnProbe = CairnProbe.new()
var terrain: VoxelTerrain
var viewer: VoxelViewer
var data_viewer: VoxelViewer
var mover: VoxelBoxMover = VoxelBoxMover.new()
var camera: Camera3D
var actor_instances: MultiMeshInstance3D
var rain: MultiMeshInstance3D
var status_label: Label
var detail_label: Label
var cancel_button: Button
var report_button: Button
var state: String = "loading"
var mode: String = "full"
var render_size: int = 32
var workers: int = 1
var scenario_index: int = 0
var scenario_elapsed: float = 0.0
var elapsed_wall: float = 0.0
var simulation_ticks: int = 0
var last_frame_usec: int = 0
var loading_started: int = 0
var sample_count: int = 0
var sum_ms: float = 0.0
var max_ms: float = 0.0
var misses: int = 0
var histogram := PackedInt32Array()
var sink: CairnReportSink = CairnReportSink.new()
var raw_lines: PackedStringArray = []
var report_dir: String
var reports: Array[Dictionary] = []
var reasons: Array[String] = []
var peaks: Dictionary = {}
var start_counters: Dictionary = {}
var previous_queue: int = 0
var queue_growth_samples: int = 0
var readiness_stops: int = 0
var accepted_edits: int = 0
var rejected_edits: int = 0
var next_edit: int = 1
var actor_ticks: int = 0
var collision_usec: int = 0
var actor_phase: float = 0.0
var route_origin := Vector3(10, 8, 10)
var player := Vector3(10, 8, 10)
var velocity := Vector3.ZERO
var edit_positions: Array[Vector3i] = []
var edit_originals: Array[int] = []
var csv_usec: int = 0
var measurement_usec: int = 0
var initial_machine: Dictionary
var build_info: Dictionary
var test_mode: bool = false
var cancelled: bool = false
var matrix_index: int = 0
var next_proxy_save: float = 1.0
var proxy_saves: int = 0
var report_io_failed: bool = false
var integration_failures: Array[String] = []
var requested_distance: float = 0.0
var travelled_distance: float = 0.0
var recovery_seconds: float = -1.0
var queue_windows: Array[int] = []
var queue_window_peak: int = 0
var next_queue_window: float = 5.0
var loading_seconds: float = 0.0
var csv_bytes: int = 0
var expected_edits: Dictionary = {}
var revisit_checked: int = 0
var sun: DirectionalLight3D
var worst_event: Dictionary = {}
var operation_phases: Array[Dictionary] = []
var phase_id: int = 0
var phase_name: String = ""
var phase_start_counters: Dictionary = {}
var operation_lines: PackedStringArray = []
var operation_bytes: int = 0
var operation_file: String = ""

func _open_reports(suffix: String = "") -> void:
	csv_bytes = 0
	operation_bytes = 0
	var name: String = str(SCENARIOS[scenario_index]["id"]) + suffix + "-frames.csv"
	operation_file = name + ".operations.csv"
	sink.start(report_dir + "/" + name)
	reports_open = true
	raw_lines.append("frame,wall_s,simulation_s,interval_ms,generation_jobs,mesh_jobs,result_jobs,pending_data,pending_mesh,private_bytes,working_set,draw_calls,triangles,accepted_edits,readiness_stops,callback_usec,render_cpu_ms,render_gpu_ms,diagnostic_usec,diagnostic_frame")
	operation_lines.append("native_frame,phase,start_usec,end_usec,phase_boundary,upload_count,upload_bytes,upload_usec,upload_max_usec,upload_max_bytes,upload_max_start_usec,deletion_count,deletion_bytes,deletion_usec,deletion_max_usec,deletion_max_bytes,deletion_max_start_usec,deletion_max_kind")

func _begin_phase(label: String, trace: bool = true) -> void:
	phase_id += 1
	phase_name = label
	phase_start_counters = probe.snapshot()
	probe.begin_phase(phase_id, trace)

func _drain_operation_frames() -> void:
	for frame: Dictionary in probe.take_operation_frames():
		var upload: Dictionary = frame["upload"]
		var deletion: Dictionary = frame["deletion"]
		operation_lines.append("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d" % [
			frame["native_frame"], frame["phase"], frame["start_usec"], frame["end_usec"], int(frame["phase_boundary"]),
			upload["count"], upload["bytes"], upload["usec"], upload["max_usec"], upload["max_bytes"], upload["max_start_usec"],
			deletion["count"], deletion["bytes"], deletion["usec"], deletion["max_usec"], deletion["max_bytes"], deletion["max_start_usec"], deletion["max_kind"]])
		# Each submitted batch fits the existing sink's 64 KiB item limit.
		if operation_lines.size() >= 64: _flush_operations()

func _flush_operations() -> void:
	if operation_lines.is_empty(): return
	var payload: String = "\n".join(operation_lines) + "\n"
	if operation_bytes + payload.length() > 64 * 1024 * 1024:
		report_io_failed = true
		operation_lines.clear()
	elif sink.append_operations(payload):
		operation_bytes += payload.length()
		operation_lines.clear()
	elif operation_lines.size() >= 128:
		report_io_failed = true
		operation_lines.clear()

func _close_phase() -> Dictionary:
	if phase_name.is_empty(): return {}
	var result: Dictionary = probe.end_phase()
	_drain_operation_frames()
	_flush_operations()
	result.merge({"scenario": SCENARIOS[scenario_index]["id"], "phase": phase_name,
		"raw_operations": operation_file if bool(result["tracing"]) else "disabled for A/B baseline",
		"native_start": phase_start_counters, "native_end": probe.snapshot()})
	operation_phases.append(result)
	if int(result["dropped_frames"]) > 0:
		integration_failures.append(str(result["scenario"]) + ": native operation trace dropped frames")
	phase_name = ""
	return result

func _close_reports() -> void:
	if not reports_open: return
	var drain_start: int = Time.get_ticks_usec()
	if not await Diagnostics.drain_pending(_flush_pending_reports, _has_pending_reports, sink.has_failed, get_tree().process_frame):
		report_io_failed = true
	sink.finish()
	writer_drain_usec = Time.get_ticks_usec() - drain_start
	reports_open = false
	if not raw_lines.is_empty() or not operation_lines.is_empty() or sink.has_failed(): report_io_failed = true
	raw_lines.clear()
	operation_lines.clear()
	if report_io_failed: integration_failures.append("Incomplete diagnostic output")

func _flush_pending_reports() -> void:
	_flush_csv()
	_flush_operations()

func _has_pending_reports() -> bool:
	return not raw_lines.is_empty() or not operation_lines.is_empty()

func _ready() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument == "--m1-smoke": test_mode = true
		if argument.begins_with("--render-size="): render_size = int(argument.get_slice("=", 1))
		if argument.begins_with("--workers="): workers = int(argument.get_slice("=", 1))
		if argument.begins_with("--benchmark-mode="): mode = argument.get_slice("=", 1)
		if argument.begins_with("--matrix-index="): matrix_index = int(argument.get_slice("=", 1))
	if mode == "matrix":
		render_size = 32 if matrix_index % 2 == 0 else 16
		workers = 1 if matrix_index < 2 else 2
	if mode == "explore": scenario_index = 1
	if not render_size in [16, 32] or not workers in [1, 2]:
		get_tree().quit(2)
		return
	Engine.max_fps = 0
	Engine.max_physics_steps_per_frame = 4
	DisplayServer.window_set_size(Vector2i(1280, 720))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	probe.configure(workers, false)
	build_info = JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json"))
	initial_machine = probe.machine()
	initial_machine.merge({"cpu": OS.get_processor_name(), "logical_processors": OS.get_processor_count(),
		"gpu": RenderingServer.get_video_adapter_name(), "vendor": RenderingServer.get_video_adapter_vendor(),
		"driver": RenderingServer.get_video_adapter_api_version(), "os": OS.get_version(),
		"renderer": RenderingServer.get_current_rendering_method(),
		"display": DisplayServer.get_name(), "refresh_hz": DisplayServer.screen_get_refresh_rate()})
	var stamp: String = Time.get_datetime_string_from_system().replace(":", "-")
	report_dir = "user://diagnostics/M1-%s-%d-%d-%d" % [stamp, render_size, workers, OS.get_process_id()]
	DirAccess.make_dir_recursive_absolute(report_dir)
	_make_ui()
	_make_scene()
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	_start_scenario()

func _make_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := PanelContainer.new()
	panel.position = Vector2(20, 20)
	panel.size = Vector2(750, 180)
	layer.add_child(panel)
	var box := VBoxContainer.new()
	panel.add_child(box)
	status_label = Label.new()
	status_label.add_theme_font_size_override("font_size", 24)
	box.add_child(status_label)
	detail_label = Label.new()
	box.add_child(detail_label)
	cancel_button = Button.new()
	cancel_button.text = "Cancel check and save partial report"
	cancel_button.pressed.connect(_cancel)
	box.add_child(cancel_button)
	report_button = Button.new()
	report_button.text = "Open reports folder"
	report_button.pressed.connect(func() -> void: OS.shell_open(ProjectSettings.globalize_path(report_dir)))
	box.add_child(report_button)

func _make_scene() -> void:
	var world_environment := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("809eac")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color.WHITE
	environment.ambient_light_energy = 0.7
	environment.fog_enabled = true
	environment.fog_light_color = Color("809eac")
	environment.fog_density = 0.025
	world_environment.environment = environment
	add_child(world_environment)
	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55, -30, 0)
	sun.shadow_enabled = false
	add_child(sun)
	camera = Camera3D.new()
	camera.far = 96.0
	camera.current = true
	add_child(camera)
	actor_instances = _make_instances(24, Color("d9a353"), Vector3(0.5, 1.2, 0.5))
	rain = _make_instances(256, Color("bbd7e5"), Vector3(0.025, 0.3, 0.025))
	mover.set_step_climbing_enabled(true)
	mover.set_max_step_height(0.5)

func _make_instances(count: int, color: Color, size: Vector3) -> MultiMeshInstance3D:
	var node := MultiMeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	mesh.material = material
	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = mesh
	multimesh.instance_count = count
	node.multimesh = multimesh
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(node)
	return node

func _create_terrain(fixture: int) -> void:
	terrain = VoxelTerrain.new()
	terrain.mesh_block_size = render_size
	terrain.generate_collisions = false
	# Finite vertical fixture slab, identical in every comparison; not a new world limit.
	terrain.bounds = AABB(Vector3(-4096, -16, -4096), Vector3(8192, 48, 8192))
	terrain.max_view_distance = 128
	var generator := CairnFixture.new()
	generator.fixture = fixture
	terrain.generator = generator
	var library := VoxelBlockyLibrary.new()
	var air := VoxelBlockyModelEmpty.new()
	var stone := VoxelBlockyModelCube.new()
	var grass := VoxelBlockyModelCube.new()
	var material := StandardMaterial3D.new()
	material.vertex_color_use_as_albedo = true
	stone.color = Color("78828b")
	grass.color = Color("90a86b")
	stone.set_material_override(0, material)
	grass.set_material_override(0, material)
	library.models = [air, stone, grass]
	library.bake()
	var mesher := CairnMesher.new()
	mesher.library = library
	for side: int in range(6): mesher.set_shadow_occluder_side(side, false)
	terrain.mesher = mesher
	add_child(terrain)
	viewer = VoxelViewer.new()
	viewer.view_distance = 96
	viewer.requires_collisions = false
	viewer.position = player
	add_child(viewer)
	data_viewer = VoxelViewer.new()
	data_viewer.view_distance = 128
	data_viewer.requires_visuals = false
	data_viewer.requires_collisions = false
	data_viewer.position = player
	add_child(data_viewer)

func _start_scenario() -> void:
	state = "loading"
	_open_reports("-preparation")
	_begin_phase("preparation")
	var scenario: Dictionary = SCENARIOS[scenario_index]
	route_origin = Vector3(10, -10, 2) if scenario["id"] == "N2" else Vector3(10, 8, 10)
	player = route_origin
	velocity = Vector3.ZERO
	expected_edits.clear()
	_create_terrain(int(scenario["fixture"]))
	loading_started = Time.get_ticks_msec()
	status_label.text = "Preparing %s • %d³ render blocks • %d terrain worker(s)" % [scenario["id"], render_size, workers]
	detail_label.text = "Fixed 1280 × 720 • visual radius 96 m • data radius 128 m\nTemporary engine fixtures; no player world is touched."
	actor_instances.multimesh.visible_instance_count = int(scenario["actors"])
	rain.visible = scenario["id"] == "H2"
	var paced: bool = scenario["id"] == "paced"
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if paced else DisplayServer.VSYNC_DISABLED)
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), not str(scenario["id"]).begins_with("AB-off-"))
	probe.configure(workers, str(scenario["id"]).begins_with("H"))

func _begin_measurement() -> void:
	state = "reporting"
	_close_phase()
	await _close_reports()
	if cancelled:
		_finish("cancelled", "Cancelled by user; partial result cannot qualify M1")
		return
	state = "running"
	scenario_elapsed = 0.0
	elapsed_wall = 0.0
	simulation_ticks = 0
	sample_count = 0
	sum_ms = 0.0
	max_ms = 0.0
	worst_event = {}
	misses = 0
	histogram.resize(100001)
	histogram.fill(0)
	readiness_stops = 0
	accepted_edits = 0
	rejected_edits = 0
	next_edit = 1
	actor_ticks = 0
	actor_phase = 0.0
	collision_usec = 0
	measurement_usec = 0
	csv_usec = 0
	peaks = {}
	reasons = []
	edit_positions.clear()
	edit_originals.clear()
	start_counters = probe.snapshot()
	previous_queue = 0
	queue_growth_samples = 0
	requested_distance = 0.0
	travelled_distance = 0.0
	recovery_seconds = -1.0
	queue_windows.clear()
	queue_window_peak = 0
	next_queue_window = 5.0
	revisit_checked = 0
	end_requested = false
	finish_reason = ""
	diagnostics = Diagnostics.new()
	diagnostics.start(Time.get_ticks_usec())
	_open_reports()
	var id: String = SCENARIOS[scenario_index]["id"]
	var label: String = "gameplay"
	if id == "warmup": label = "warmup"
	elif id == "paced": label = "paced_diagnostic"
	elif id.begins_with("AB-"): label = "overhead_diagnostic"
	_begin_phase(label, not id.begins_with("AB-off-"))
	next_proxy_save = 1.0
	proxy_saves = 0
	last_frame_usec = Time.get_ticks_usec()
	if str(SCENARIOS[scenario_index]["id"]).begins_with("AB-off-"):
		status_label.text = "Measuring diagnostic baseline • 30 seconds"
		detail_label.text = "The scene continues running. Detailed counters and live labels are paused for this comparison."
	if mode == "explore": Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _unhandled_input(event: InputEvent) -> void:
	if mode != "explore": return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		camera.rotation.y -= event.relative.x * 0.002
		camera.rotation.x = clampf(camera.rotation.x - event.relative.y * 0.002, -1.4, 1.4)
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		_cancel()

func _physics_process(delta: float) -> void:
	if state != "running": return
	simulation_ticks += 1
	scenario_elapsed += delta
	var id: String = SCENARIOS[scenario_index]["id"]
	var heavy: bool = id.begins_with("H")
	var target: Vector3
	if heavy:
		# Persistent outward motion; the camera reverses every 15 seconds without teleporting the viewer.
		target = route_origin + Vector3(6.5 * scenario_elapsed, 0, 0)
	elif id == "R1" and scenario_elapsed <= 5.0:
		target = player
	elif id == "R1" or id.begins_with("AB-"):
		target = route_origin
	else:
		target = route_origin + Vector3(sin(scenario_elapsed * 0.07) * 22.0, 0, 0)
	var wanted: Vector3 = target - player
	if mode == "explore":
		var axes := Vector2(float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)), float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W)))
		wanted = camera.basis * Vector3(axes.x, 0, axes.y)
	wanted.y = 0
	if wanted.length() > 0.02: wanted = wanted.normalized() * (6.5 if heavy else 3.0)
	velocity.x = wanted.x
	velocity.z = wanted.z
	velocity.y = maxf(velocity.y - 18.0 * delta, -30.0)
	var motion: Vector3 = velocity * delta
	requested_distance += Vector2(motion.x, motion.z).length()
	var swept: AABB = AABB(player + PLAYER_BOX.position, PLAYER_BOX.size).merge(AABB(player + motion + PLAYER_BOX.position, PLAYER_BOX.size)).grow(0.1)
	var tool: VoxelTool = terrain.get_voxel_tool()
	var collision_start: int = Time.get_ticks_usec()
	if not tool.is_area_editable(swept):
		readiness_stops += 1
	else:
		var actual: Vector3 = mover.get_motion(player, motion, PLAYER_BOX, terrain)
		player += actual
		travelled_distance += Vector2(actual.x, actual.z).length()
		if absf(actual.y - motion.y) > 0.0001: velocity.y = 0.0
		if player.y < -14.0 and not "Collision route left the safe fixture" in reasons:
			reasons.append("Collision route left the safe fixture")
			integration_failures.append(id + ": collision route left the safe fixture")
	collision_usec += Time.get_ticks_usec() - collision_start
	viewer.position = player
	data_viewer.position = player
	camera.position = player + Vector3(0, 1.65, 0)
	if mode != "explore":
		camera.rotation.y = -PI * 0.5 if not heavy else (-PI * 0.5 + PI * float(int(scenario_elapsed / 15.0) % 2))
		if id == "N3": camera.rotation.y += scenario_elapsed * TAU / 30.0
		camera.rotation.x = -0.18
	_tick_proxies(delta)
	var rate: float = float(SCENARIOS[scenario_index]["rate"])
	if rate > 0.0 and scenario_elapsed >= float(next_edit) / rate:
		# A busy native read lock defers the due command to a later fixed tick.
		# At most one command is attempted per tick; missed work stays counted.
		if _edit_border(tool): next_edit += 1
	if id in ["N2", "H2"] and scenario_elapsed >= next_proxy_save:
		if sink.append(JSON.stringify({"proxy_tick": simulation_ticks, "accepted_edits": accepted_edits, "payload": "x".repeat(32768)}), true): proxy_saves += 1
		else: report_io_failed = true
		next_proxy_save += 1.0

func _tick_proxies(delta: float) -> void:
	actor_phase += delta
	# Shared day/night light proxy; no light node per voxel or lamp.
	sun.light_energy = 0.2 + 0.8 * (0.5 + 0.5 * cos(scenario_elapsed * TAU / 60.0))
	var count: int = actor_instances.multimesh.visible_instance_count
	for index: int in range(count):
		var angle: float = actor_phase * 0.3 + float(index) * TAU / float(count)
		var position_value: Vector3 = player + Vector3(cos(angle) * (5.0 + index % 4), 0.7, sin(angle) * (5.0 + index % 4))
		actor_instances.multimesh.set_instance_transform(index, Transform3D(Basis(), position_value))
	actor_ticks += count
	if rain.visible:
		for index: int in range(256):
			var offset := Vector3(float(index % 16) - 8.0, fposmod(float(index) * 0.37 - actor_phase * 8.0, 12.0), floorf(float(index) / 16.0) - 8.0)
			rain.multimesh.set_instance_transform(index, Transform3D(Basis(), player + offset))

func _edit_border(tool: VoxelTool) -> bool:
	# One toggled voxel on a 16/32 border. A bounded proxy edit, not inventory or durable saving.
	var edit_height: int = -8 if SCENARIOS[scenario_index]["id"] == "N2" else 6
	var position_value := Vector3i(int(round(player.x / 32.0)) * 32, edit_height, int(floor(player.z)) + 3)
	if not tool.is_area_editable(AABB(Vector3(position_value) - Vector3.ONE, Vector3.ONE * 3.0)):
		rejected_edits += 1
		return false
	tool.channel = VoxelBuffer.CHANNEL_TYPE
	var old: int = tool.get_voxel(position_value)
	if edit_positions.size() >= 64 and not position_value in edit_positions:
		rejected_edits += 1
		return false
	if not position_value in edit_positions:
		edit_positions.append(position_value)
		edit_originals.append(old)
	# Only the bounded temporary edit budget is admitted in M1; no arbitrary builds.
	var generator: CairnFixture = terrain.generator
	var value: int = 2 if old == 0 else 0
	if generator.try_edit(terrain, position_value, value):
		accepted_edits += 1
		expected_edits[position_value] = value
		return true
	rejected_edits += 1
	return false

func _process(_delta: float) -> void:
	if state == "finished" or state == "reporting": return
	var begin: int = Time.get_ticks_usec()
	var measured: bool = state == "running"
	_process_frame(begin)
	if measured:
		# Includes row formatting, batch submission, live UI and the final callback.
		diagnostics.record_callback(begin, Time.get_ticks_usec())
		measurement_usec = diagnostics.callback_usec
		if not finish_reason.is_empty(): _finish("failed", finish_reason)
		elif end_requested: _end_scenario()

func _process_frame(now: int) -> void:
	if phase_name != "overhead_diagnostic" or not str(SCENARIOS[scenario_index]["id"]).begins_with("AB-off-"):
		_drain_operation_frames()
	if state == "draining":
		var drain: Dictionary = probe.snapshot()
		if Time.get_ticks_msec() - loading_started > 180000:
			_finish("failed", "Terrain resources did not drain within three minutes")
			return
		if int(drain["generation_jobs"]) + int(drain["mesh_jobs"]) + int(drain["main_jobs"]) == 0:
			_close_phase()
			state = "reporting"
			await _close_reports()
			if cancelled:
				_finish("cancelled", "Cancelled by user; partial result cannot qualify M1")
				return
			scenario_index += 1
			if scenario_index >= SCENARIOS.size(): _finish("completed", "All applicable engine scenarios ran")
			else: _start_scenario()
		return
	if state == "loading":
		var stats: Dictionary = terrain.get_statistics()
		var counters: Dictionary = probe.snapshot()
		if int(counters["overloads"]) > 0:
			_finish("failed", "Fixture exceeded native mesh admission")
			return
		if Time.get_ticks_msec() - loading_started > 180000:
			_finish("failed", "Terrain did not become ready within three minutes")
			return
		if int(stats.get("resident_data", 0)) > 0 and int(stats.get("pending_data", 1)) + int(stats.get("pending_mesh", 1)) + int(stats.get("loading_data", 1)) == 0 and int(counters["generation_jobs"]) + int(counters["mesh_jobs"]) + int(counters["main_jobs"]) == 0:
			loading_seconds = float(Time.get_ticks_msec() - loading_started) / 1000.0
			_begin_measurement()
		return
	var frame_ms: float = float(now - last_frame_usec) / 1000.0
	diagnostics.record_interval(now - last_frame_usec)
	last_frame_usec = now
	elapsed_wall += frame_ms / 1000.0
	sample_count += 1
	sum_ms += frame_ms
	max_ms = maxf(max_ms, frame_ms)
	histogram[mini(100000, int(ceil(frame_ms * 100.0)))] += 1
	var id: String = SCENARIOS[scenario_index]["id"]
	var deadline: float = 33.333 if id.begins_with("H") or (id == "R1" and scenario_elapsed <= 5.0) else 16.667
	if frame_ms > deadline: misses += 1
	if id.begins_with("AB-off-"):
		# Minimal interval/histogram baseline. Disable per-frame probes, GPU
		# polling, formatting, CSV I/O and live labels; keep identical simulation.
		if scenario_elapsed >= _duration(): end_requested = true
		elif elapsed_wall > _duration() * 2.0 + 30.0:
			finish_reason = "Diagnostic baseline simulation stalled"
		return
	var counters: Dictionary = probe.snapshot()
	var terrain_stats: Dictionary = terrain.get_statistics()
	if frame_ms >= max_ms:
		worst_event = {"frame": sample_count, "wall_seconds": elapsed_wall, "simulation_seconds": scenario_elapsed,
			"player": [player.x, player.y, player.z], "native": counters.duplicate(), "terrain": terrain_stats.duplicate()}
	var queue: int = int(counters["generation_jobs"]) + int(counters["mesh_jobs"]) + int(counters["main_jobs"]) + int(terrain_stats.get("pending_data", 0)) + int(terrain_stats.get("pending_mesh", 0))
	queue_window_peak = maxi(queue_window_peak, queue)
	if elapsed_wall >= next_queue_window:
		queue_windows.append(queue_window_peak)
		if queue_windows.size() > 60: queue_windows.pop_front()
		queue_window_peak = 0
		next_queue_window += 5.0
	if id == "R1" and queue == 0 and recovery_seconds < 0.0:
		recovery_seconds = elapsed_wall
		var tool: VoxelTool = terrain.get_voxel_tool()
		tool.channel = VoxelBuffer.CHANNEL_TYPE
		for position_value: Vector3i in expected_edits:
			if tool.is_area_editable(AABB(Vector3(position_value), Vector3.ONE)):
				revisit_checked += 1
				if tool.get_voxel(position_value) != int(expected_edits[position_value]):
					integration_failures.append("R1: edited fixture value changed")
	var render_cpu: float = RenderingServer.viewport_get_measured_render_time_cpu(get_viewport().get_viewport_rid())
	var render_gpu: float = RenderingServer.viewport_get_measured_render_time_gpu(get_viewport().get_viewport_rid())
	peaks["render_cpu_ms"] = maxf(float(peaks.get("render_cpu_ms", 0.0)), render_cpu)
	if render_gpu > 0.0: peaks["render_gpu_ms"] = maxf(float(peaks.get("render_gpu_ms", 0.0)), render_gpu)
	for key: String in ["private_bytes", "working_set", "generation_jobs", "mesh_jobs", "result_jobs", "main_jobs"]:
		peaks[key] = maxi(int(peaks.get(key, 0)), int(counters.get(key, 0)))
	for key: String in ["resident_data", "resident_mesh", "pending_data", "pending_mesh"]:
		peaks[key] = maxi(int(peaks.get(key, 0)), int(terrain_stats.get(key, 0)))
	var draws: int = int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	var triangles: int = int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
	peaks["draw_calls"] = maxi(int(peaks.get("draw_calls", 0)), draws)
	peaks["triangles"] = maxi(int(peaks.get("triangles", 0)), triangles)
	var gpu_bytes: int = int(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED))
	if gpu_bytes > 0: peaks["gpu_resource_estimate_bytes"] = maxi(int(peaks.get("gpu_resource_estimate_bytes", 0)), gpu_bytes)
	var upstream_stats: Dictionary = VoxelEngine.get_stats()
	var pools: Dictionary = upstream_stats["memory_pools"]
	for key: String in ["voxel_total", "voxel_used", "block_count"]:
		peaks["pool_" + key] = maxi(int(peaks.get("pool_" + key, 0)), int(pools[key]))
	raw_lines.append("%d,%.6f,%.6f,%.6f,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.6f,%.6f,%d,%d" % [sample_count, elapsed_wall, scenario_elapsed, frame_ms,
		counters["generation_jobs"], counters["mesh_jobs"], counters["result_jobs"], terrain_stats.get("pending_data", 0), terrain_stats.get("pending_mesh", 0),
		counters.get("private_bytes", 0), counters.get("working_set", 0), draws, triangles, accepted_edits, readiness_stops,
		now, render_cpu, render_gpu, diagnostics.last_callback_usec, diagnostics.callbacks])
	if raw_lines.size() >= 128: _flush_csv()
	if sample_count % 30 == 0:
		status_label.text = "%s • %d / %d seconds • %d³ / %d worker(s)" % [id, int(scenario_elapsed), int(_duration()), render_size, workers]
		detail_label.text = "%.1f fps • %d frame deadline misses • %d accepted proxy edits\nThis is an engine experiment. Final survival systems are not present." % [1000.0 / maxf(frame_ms, 0.001), misses, accepted_edits]
	if int(counters["overloads"]) > 0: finish_reason = "Native admission rejected unsupported geometry"
	elif elapsed_wall > _duration() * 2.0 + 30.0 or sample_count > 500000:
		finish_reason = "Scenario exceeded its wall-time or diagnostic sample bound"
	elif scenario_elapsed >= _duration(): end_requested = true

func _duration() -> float:
	if mode == "explore": return 1800.0
	return 1.0 if test_mode else float(SCENARIOS[scenario_index]["seconds"])

func _percentile(percent: float) -> float:
	var remaining: int = int(ceil(float(sample_count) * percent))
	for i: int in range(histogram.size()):
		remaining -= histogram[i]
		if remaining <= 0: return float(i) / 100.0
	return max_ms

func _flush_csv() -> void:
	if raw_lines.is_empty(): return
	var start: int = Time.get_ticks_usec()
	var payload: String = "\n".join(raw_lines) + "\n"
	if csv_bytes + payload.length() > 64 * 1024 * 1024:
		report_io_failed = true
		raw_lines.clear()
	elif sink.append(payload, false):
		csv_bytes += payload.length()
		raw_lines.clear()
	elif raw_lines.size() >= 256:
		report_io_failed = true
		raw_lines.clear()
	csv_usec += Time.get_ticks_usec() - start

func _end_scenario() -> void:
	state = "reporting"
	var measured_phase: Dictionary = _close_phase()
	# Join/flush while explicitly outside gameplay, before retirement can add work.
	await _close_reports()
	if cancelled:
		_finish("cancelled", "Cancelled by user; partial result cannot qualify M1")
		return
	var scenario: Dictionary = SCENARIOS[scenario_index]
	var id: String = scenario["id"]
	var heavy: bool = id.begins_with("H")
	if id.begins_with("AB-off-"):
		# One end sample verifies a real fixture without measuring these probes
		# as part of the baseline frame series.
		peaks["resident_data"] = terrain.get_statistics().get("resident_data", 0)
	if sample_count == 0 or int(peaks.get("resident_data", 0)) == 0:
		integration_failures.append(id + ": empty terrain workload")
	if actor_ticks < simulation_ticks * int(scenario["actors"]): integration_failures.append(id + ": missing actor workload")
	if readiness_stops > 0: integration_failures.append(id + ": missing movement data")
	if readiness_stops > 0: reasons.append("Movement encountered missing data")
	if id == "R1" and (recovery_seconds < 0.0 or recovery_seconds > 5.0): reasons.append("Recovery exceeded five seconds")
	if id == "R1" and not test_mode and revisit_checked == 0: integration_failures.append("R1: no edited data revisited")
	if heavy and travelled_distance < 6.5 * scenario_elapsed - 1.0: reasons.append("Required sprint distance was not accepted")
	if queue_windows.size() >= 6:
		var growth: bool = true
		for i: int in range(queue_windows.size() - 5, queue_windows.size()):
			if queue_windows[i] <= queue_windows[i - 1]: growth = false
		if growth: reasons.append("Queue grew across the final thirty seconds")
	if report_io_failed or sink.has_failed():
		reasons.append("Diagnostic disk queue or write failed")
		integration_failures.append(id + ": incomplete diagnostic output")
	if misses > 0: reasons.append("Raw frame deadline misses require attribution and repeat")
	if elapsed_wall - scenario_elapsed > 0.25: reasons.append("Simulation fell behind wall time")
	if int(peaks.get("resident_data", 0)) > 8192 or int(peaks.get("resident_mesh", 0)) > 512: reasons.append("Resident pool cap exceeded")
	if int(peaks.get("generation_jobs", 0)) + int(peaks.get("mesh_jobs", 0)) > 64 or int(peaks.get("result_jobs", 0)) > 16: reasons.append("Native job cap exceeded")
	if int(peaks.get("draw_calls", 0)) > (400 if heavy else 250) or int(peaks.get("triangles", 0)) > (450000 if heavy else 250000): reasons.append("View geometry envelope exceeded")
	if int(peaks.get("private_bytes", 0)) > (2147483648 if heavy else 1610612736) or int(peaks.get("working_set", 0)) > (1610612736 if heavy else 1342177280): reasons.append("Process memory ceiling exceeded")
	if int(peaks.get("gpu_resource_estimate_bytes", 0)) > (402653184 if heavy else 268435456): reasons.append("Graphics resource estimate exceeded budget")
	if int(peaks.get("pool_voxel_total", 0)) > 201326592: reasons.append("Voxel allocation pool exceeded budget")
	if float(scenario["rate"]) > 0.0 and accepted_edits < int(floor(_duration() * float(scenario["rate"]))) - 1: reasons.append("Required edit workload was not accepted")
	var counters: Dictionary = probe.snapshot()
	reasons.append_array(Evaluation.operation_failures(measured_phase))
	var overhead: float = float(measurement_usec) / maxf(sum_ms * 1000.0, 1.0)
	if overhead >= 0.01: reasons.append("Diagnostic callback wall time reached 1%; A/B qualification required")
	var hard_failure: bool = readiness_stops > 0 or report_io_failed or sink.has_failed() or int(measured_phase["dropped_frames"]) > 0
	for reason: String in reasons:
		if "exceeded" in reason or "fell behind" in reason or "was not accepted" in reason or "Queue grew" in reason or "Collision" in reason: hard_failure = true
	var report: Dictionary = {"id": id, "operation_phase": measured_phase,
		"reasons": reasons.duplicate(), "samples": sample_count, "average_fps": float(sample_count) * 1000.0 / maxf(sum_ms, 0.001),
		"p50_ms": _percentile(0.5), "p95_ms": _percentile(0.95), "p99_ms": _percentile(0.99), "p99_9_ms": _percentile(0.999),
		"maximum_ms": max_ms, "deadline_misses": misses, "simulated_seconds": scenario_elapsed, "wall_seconds": elapsed_wall,
		"worst_event": worst_event.duplicate(), "raw_frames": id + "-frames.csv" if not id.begins_with("AB-off-") else "disabled for A/B baseline; histogram retained",
		"readiness_stops": readiness_stops, "accepted_proxy_edits": accepted_edits, "rejected_proxy_edits": rejected_edits,
		"actor_ticks": actor_ticks, "simulation_ticks": simulation_ticks, "collision_usec": collision_usec,
		"diagnostic_callback_wall_fraction": overhead,
		"requested_distance_m": requested_distance, "travelled_distance_m": travelled_distance,
		"recovery_seconds": recovery_seconds, "revisited_edits": revisit_checked,
		"queue_five_second_peaks": queue_windows.duplicate(), "loading_seconds": loading_seconds,
		"generation_service_per_second": float(int(counters["generated"]) - int(start_counters["generated"])) / maxf(elapsed_wall, 0.001),
		"meshing_service_per_second": float(int(counters["meshed"]) - int(start_counters["meshed"])) / maxf(elapsed_wall, 0.001),
		"generation_worker_fraction": float(int(counters["generation_usec"]) - int(start_counters["generation_usec"])) / maxf(elapsed_wall * 1000000.0 * workers, 1.0),
		"meshing_worker_fraction": float(int(counters["meshing_usec"]) - int(start_counters["meshing_usec"])) / maxf(elapsed_wall * 1000000.0 * workers, 1.0),
		"csv_write_usec": csv_usec, "peaks": peaks.duplicate(), "native_start": start_counters, "native_end": counters,
		"gpu_timing": "asynchronous engine viewport query" if peaks.has("render_gpu_ms") else "unavailable",
		"gpu_memory": "engine resource estimate; excludes unreported driver allocations" if peaks.has("gpu_resource_estimate_bytes") else "unavailable",
		"unavailable_metrics": ["independent non-voxel allocation pools", "physical presentation intervals", "driver-deferred deletion time"],
		"proxy_autosaves": proxy_saves, "presentation": "application callback intervals; physical scanout unavailable",
		"durability": "not_run: M1 edits are temporary; storage workload is not a durability test"}
	report.merge(Evaluation.scenario_result(true, hard_failure, reasons))
	if id.begins_with("AB-"):
		# Same bounded timing evidence in both modes, including the baseline distribution.
		var bins: Array[Array] = []
		for i: int in range(histogram.size()):
			if histogram[i] > 0: bins.append([i, histogram[i]])
		report["interval_histogram_10usec"] = bins
	# Final combined serialization/file hashing has its own measured lifecycle below.
	report["diagnostic_accounting"] = diagnostics.snapshot(Time.get_ticks_usec(), writer_drain_usec)
	reports.append(report)
	if mode == "explore":
		_finish("completed", "Exploration time limit reached; partial engine report saved")
		return
	if scenario_index + 1 < SCENARIOS.size() and SCENARIOS[scenario_index + 1]["id"] == "R1":
		# Revisit the same edited fixture; do not regenerate a substitute world.
		scenario_index += 1
		_begin_measurement()
	else:
		_open_reports("-retirement")
		_begin_phase("retirement")
		terrain.queue_free()
		viewer.queue_free()
		data_viewer.queue_free()
		state = "draining"
		loading_started = Time.get_ticks_msec()
		status_label.text = "Finishing scenario and retiring terrain resources…"

func _cancel() -> void:
	cancelled = true
	if state == "reporting": return
	_finish("cancelled", "Cancelled by user; partial result cannot qualify M1")

func _finish(outcome: String, message: String) -> void:
	if finishing: return
	finishing = true
	var begin: int = Time.get_ticks_usec()
	await _finish_report(outcome, message)
	# A separate terminal record avoids pretending a file can include its own write cost.
	var end: int = Time.get_ticks_usec()
	var file := FileAccess.open(report_dir + "/report-finalization.json", FileAccess.WRITE)
	var timing_saved: bool = file != null
	if file != null:
		file.store_string(JSON.stringify({"start_usec": begin, "end_usec": end, "elapsed_usec": end - begin,
			"scope": "phase closure, writer drain, summary assembly, hashing, serialization, writes/flushes and final UI",
			"excluded": "this terminal timing record write; process exit; deferred renderer work",
			"test_mode": test_mode}))
		file.flush()
		timing_saved = file.get_error() == OK
		file.close()
	if not timing_saved:
		integration_failures.append("Could not save finalization timing")
		status_label.text = "Could not save complete diagnostic evidence"
		detail_label.text = "The final timing record could not be written. Keep the partial reports; this run cannot qualify M1."
	if test_mode: get_tree().quit(0 if outcome == "completed" and integration_failures.is_empty() else 1)

func _finish_report(outcome: String, message: String) -> void:
	_close_phase()
	state = "finished"
	await _close_reports()
	if test_mode:
		integration_failures.append_array(load("res://scripts/benchmark_trace_tests.gd").verify(report_dir, operation_phases, reports))
	Engine.max_fps = 60
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)
	var summary: Dictionary = {"schema": 3, "milestone": "M1", "scope": "temporary engine proxy experiment",
		"outcome": outcome, "completed": outcome == "completed", "qualified": false,
		"qualification": "unverified", "target_certification": "unverified: review exact-build reports and all outstanding gates",
		"message": message, "build": build_info, "machine": initial_machine,
		"scenario_version": "m1-proxy-1", "fixture_version": "m1-integer-1", "test_mode": test_mode,
		"configuration": {"resolution": [1280,720], "render_scale": 1.0, "render_block": render_size, "data_chunk": 16,
			"workers": workers, "visual_radius": 96, "data_radius": 128, "fixture_y": [-16,32], "triangle_colliders": false},
		"scenarios": reports, "operation_phases": operation_phases,
		"operation_trace": {"clock": "process monotonic microseconds; join to frame callback_usec",
			"frames": "native engine process intervals; phase boundaries split a frame without resetting admission",
			"payload": "estimated vertex layout plus sequential indices at 68 bytes/vertex; reference release has zero payload",
			"deletion_kinds": {"2": "surface_remove", "3": "mesh_reference_release"},
			"bounds": "64 native frame records; 128 pending CSV rows; 64 MiB per operation file; shared bounded disk worker",
			"unavailable": ["driver-deferred work", "OS attribution"],
			"diagnostic_usec": "full previous callback elapsed wall time, keyed by diagnostic_frame; final callback retained in scenario accounting",
			"renderer": "asynchronous viewport CPU/GPU queries; not additive with native or callback times"},
		"limitations": ["M1 proxy actors, edits and weather; no survival simulation or durable world store",
			"GPU attribution and physical presentation timing unavailable", "Hardware qualification requires report review"]}
	summary["integration_failures"] = integration_failures
	summary["configuration"]["actual_workers"] = VoxelEngine.get_thread_count()
	var actual_window_size: Vector2i = DisplayServer.window_get_size()
	summary["configuration"]["reported_window_size"] = [actual_window_size.x, actual_window_size.y]
	summary["configuration"]["shadows"] = false
	summary["configuration"]["anti_aliasing"] = "disabled"
	summary["configuration"]["fog_density"] = 0.025
	summary["diagnostic_ab"] = Evaluation.diagnostic_ab(reports, test_mode, not integration_failures.is_empty())
	summary["diagnostic_accounting"] = {
		"unit": "elapsed monotonic wall microseconds; neither CPU service nor additive with overlapping worker/GPU time",
		"scenario": "measurement setup through last callback, phase close, full writer drain and report construction; excludes preparation/retirement",
		"final_report": "report-finalization.json; one-time combined reporting cost, outside the switched A/B window",
		"shared_baseline": "interval/histogram/block accounting, collision timers and native lifetime/phase counters stay enabled",
		"qualification": "unverified: switched A/B cannot certify shared baseline or unavailable deferred renderer/OS attribution"}
	var executable: String = OS.get_executable_path()
	summary["executable_sha256"] = FileAccess.get_sha256(executable)
	var pack: String = executable.get_base_dir().path_join("Cairn.pck")
	if FileAccess.file_exists(pack): summary["pack_sha256"] = FileAccess.get_sha256(pack)
	var file := FileAccess.open(report_dir + "/summary.json", FileAccess.WRITE)
	var summary_saved: bool = file != null
	if file != null:
		file.store_string(JSON.stringify(summary, "  "))
		file.flush()
		summary_saved = file.get_error() == OK
		file.close()
	file = FileAccess.open(report_dir + "/summary.txt", FileAccess.WRITE)
	if file != null:
		file.store_string("CAIRN M1 ENGINE CHECK\n" + message + "\nCompletion: " + outcome + "\nQualification: UNVERIFIED; completion is not a performance pass.\nAttach the complete report folder, including report-finalization.json and all CSV files.\n")
		file.flush()
		summary_saved = summary_saved and file.get_error() == OK
		file.close()
	else: summary_saved = false
	status_label.text = message + " • qualification unverified"
	detail_label.text = "Reports saved. Use Open reports folder and share the complete folder.\nPerformance is not certified until the report has been reviewed."
	if not summary_saved:
		integration_failures.append("Could not write the final summary")
		status_label.text = "Could not save the final report"
		detail_label.text = "Check that your drive has free space and the Cairn data folder is writable. This run cannot qualify M1."
	cancel_button.text = "Return to title"
	if cancel_button.pressed.is_connected(_cancel): cancel_button.pressed.disconnect(_cancel)
	cancel_button.pressed.connect(func() -> void:
		OS.create_process(OS.get_executable_path(), PackedStringArray())
		get_tree().quit())
	if mode == "matrix" and not cancelled and outcome == "completed" and matrix_index < 3:
		var next_process: int = OS.create_process(OS.get_executable_path(), PackedStringArray(["--", "--benchmark", "--benchmark-mode=matrix", "--matrix-index=%d" % (matrix_index + 1)]))
		if next_process > 0: get_tree().quit()
		else:
			status_label.text = "Comparison stopped: the next setting could not start"
			detail_label.text = "Keep this report. Return to the title and run the remaining settings individually."
	if test_mode:
		print("CAIRN_M1_SMOKE=" + JSON.stringify(summary))
