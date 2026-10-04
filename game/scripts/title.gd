extends Control

const REQUIRED_CLASSES: Array[StringName] = [
	&"VoxelTerrain", &"VoxelMesherBlocky", &"VoxelBoxMover", &"SandboxWorld"
]
var build_info: Dictionary = {}
var profile: OptionButton


func _ready() -> void:
	if "--benchmark" in OS.get_cmdline_user_args() or "--m1-smoke" in OS.get_cmdline_user_args():
		get_tree().call_deferred("change_scene_to_file", "res://scenes/benchmark.tscn")
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json"))
	if parsed is Dictionary:
		build_info = parsed
	$Margin/Content/Build.text = "Build %s\nGodot %s • Renderer: %s (%s)" % [
		str(build_info.get("game_commit", "unavailable")).left(12),
		Engine.get_version_info().get("string", "unavailable"),
		RenderingServer.get_current_rendering_method(), DisplayServer.get_name()
	]
	$Margin/Content/Check.pressed.connect(_interactive_check)
	$Margin/Content/Quit.pressed.connect(func() -> void: get_tree().quit())
	$Margin/Content/Check.grab_focus()
	$Margin/Content/Description.text = "Milestone 1 • Terrain and engine performance experiment"
	profile = OptionButton.new()
	for label: String in ["32³ render blocks • 1 worker (baseline)", "16³ render blocks • 1 worker", "32³ render blocks • 2 workers", "16³ render blocks • 2 workers"]:
		profile.add_item(label)
	$Margin/Content.add_child(profile)
	$Margin/Content.move_child(profile, 5)
	for entry: Array in [["Run startup timing check (~20 s + loading)", "startup"], ["Run performance check (~24 min)", "full"], ["Compare all four settings (~96 min)", "matrix"], ["Explore the terrain fixture", "explore"]]:
		var button := Button.new()
		button.text = entry[0]
		button.pressed.connect(_launch_benchmark.bind(entry[1]))
		$Margin/Content.add_child(button)
		$Margin/Content.move_child(button, $Margin/Content.get_child_count() - 2)
	if "--self-test" in OS.get_cmdline_user_args():
		var report: Dictionary = await _self_test()
		print("CAIRN_SELF_TEST=" + JSON.stringify(report))
		get_tree().quit(0 if report["passed"] else 1)

func _launch_benchmark(mode: String) -> void:
	var sizes: Array[int] = [32, 16, 32, 16]
	var counts: Array[int] = [1, 1, 2, 2]
	var arguments := PackedStringArray(["--", "--benchmark", "--render-size=%d" % sizes[profile.selected], "--workers=%d" % counts[profile.selected], "--benchmark-mode=" + mode])
	if OS.create_process(OS.get_executable_path(), arguments) > 0: get_tree().quit()
	else: $Margin/Content/Result.text = "Could not start the engine check."


func _interactive_check() -> void:
	$Margin/Content/Check.disabled = true
	var report: Dictionary = await _self_test()
	$Margin/Content/Result.text = (
		"Startup check passed. Native modules are ready. Performance remains unverified."
		if report["passed"] else "Startup check failed: " + str(report["errors"])
	)
	$Margin/Content/Check.disabled = false


func _self_test() -> Dictionary:
	var errors: Array[String] = []
	for class_name_value: StringName in REQUIRED_CLASSES:
		if not ClassDB.can_instantiate(class_name_value):
			errors.append("Missing native class: " + str(class_name_value))
	if not errors.is_empty():
		return {"passed": false, "errors": errors}
	var entry: RefCounted = ClassDB.instantiate(&"SandboxWorld")
	var identity: Dictionary = entry.call("get_build_identity")
	for key: String in ["engine_inputs", "godot_commit", "voxel_commit"]:
		if identity.get(key, "") != build_info.get(key, "missing"):
			errors.append("Build identity mismatch: " + key)
	var terrain: Node3D = ClassDB.instantiate(&"VoxelTerrain")
	terrain.set("generate_collisions", false)
	var mesher: Resource = ClassDB.instantiate(&"VoxelMesherBlocky")
	terrain.set("mesher", mesher)
	var mover: RefCounted = ClassDB.instantiate(&"VoxelBoxMover")
	if mover == null or terrain.get("generate_collisions") != false:
		errors.append("Voxel collision configuration failed")
	add_child(terrain)
	await get_tree().process_frame
	if not terrain.is_inside_tree():
		errors.append("Native terrain did not enter the scene tree")
	terrain.queue_free()
	await get_tree().process_frame
	if VoxelEngine.get_thread_count() != 1:
		errors.append("Expected exactly one terrain worker")
	if ProjectSettings.get_setting("rendering/renderer/rendering_method") != "gl_compatibility":
		errors.append("Compatibility renderer is not configured")
	var probe_path: String = "user://m0-startup-probe.tmp"
	var probe: FileAccess = FileAccess.open(probe_path, FileAccess.WRITE)
	if probe == null:
		errors.append("Default data directory is not writable")
	else:
		probe.store_string("Cairn M0")
		probe.close()
		if FileAccess.get_file_as_string(probe_path) != "Cairn M0":
			errors.append("Data directory readback failed")
		DirAccess.remove_absolute(probe_path)
	return {
		"passed": errors.is_empty(), "errors": errors, "identity": identity,
		"game_commit": build_info.get("game_commit", "unavailable"),
		"display": DisplayServer.get_name(), "terrain_workers": VoxelEngine.get_thread_count(),
		"renderer": RenderingServer.get_current_rendering_method(),
		"target_performance": "not_run"
	}
