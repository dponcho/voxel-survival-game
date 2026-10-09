extends SceneTree

const ShaderFog = preload("res://scripts/benchmark_shader_fog.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var build: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json"))
	var context: Dictionary = {"godot_commit": build.get("godot_commit", ""),
		"rendering_method": RenderingServer.get_current_rendering_method(),
		"rendering_driver": RenderingServer.get_current_rendering_driver_name(),
		"platform": OS.get_name(), "display": DisplayServer.get_name()}
	var report: Dictionary = {"status": "unavailable", "passed": false, "qualified": false,
		"scope": "tiny canvas readback of shared Compatibility packHalf2x16 conversion; terrain fog and target pixels unverified",
		"context": context, "gpu": RenderingServer.get_video_adapter_name(),
		"api": RenderingServer.get_video_adapter_api_version(), "samples": []}
	if not ShaderFog.context_supported(context):
		report["reason"] = "Unsupported render probe context"
		_finish(report, 0)
		return
	var viewport := SubViewport.new()
	viewport.size = Vector2i(8, 8)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var shader := Shader.new()
	# Encode both bytes instead of reading 8-bit opacity, which would conceal
	# the 0x3bff versus 0x3c00 distinction near opacity one.
	shader.code = "shader_type canvas_item; render_mode unshaded; uniform float opacity; void fragment() { uint bits = packHalf2x16(vec2(opacity, 0.0)) & 65535u; COLOR = vec4(float(bits & 255u) / 255.0, float((bits >> 8u) & 255u) / 255.0, 0.0, 1.0); }"
	var material := ShaderMaterial.new()
	material.shader = shader
	var rect := ColorRect.new()
	rect.size = Vector2(8, 8)
	rect.material = material
	viewport.add_child(rect)
	var failures: Array[String] = []
	var cases: Array[Array] = [[0.0, 0x0000], [0.5, 0x3800], [0.99951171875, 0x3bff],
		[0.999755859375, 0x3bff], [0.9998189509608, 0x3bff], [0.9999211701536, 0x3bff], [1.0, 0x3c00]]
	for entry: Array in cases:
		material.set_shader_parameter("opacity", entry[0])
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		var image: Image = viewport.get_texture().get_image()
		if image == null or image.is_empty():
			failures.append("No rendered conversion readback")
			break
		var pixel: Color = image.get_pixel(4, 4)
		var bits: int = int(roundf(pixel.r * 255.0)) | (int(roundf(pixel.g * 255.0)) << 8)
		report["samples"].append({"opacity": entry[0], "expected_bits": entry[1], "observed_bits": bits})
		if bits != int(entry[1]): failures.append("Rendered packHalf2x16 differs from independent expected encoding")
	report["failures"] = failures
	report["status"] = "passed" if failures.is_empty() else "failed"
	report["passed"] = failures.is_empty()
	viewport.queue_free()
	_finish(report, 0 if failures.is_empty() else 1)

func _finish(report: Dictionary, code: int) -> void:
	print("CAIRN_M1_FOG_RENDER=" + JSON.stringify(report))
	quit(code)
