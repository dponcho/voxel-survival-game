extends RefCounted

# Pinned scene.glsl uses stdlib_inc.glsl. Desktop Config defaults the
# USE_HALF2FLOAT polyfill on; ANGLE and Web explicitly disable it.
const GODOT_COMMIT: String = "ed1daf0bf001b61586d9930840f2f1394092c079"
const MODEL: String = "godot_desktop_float2half_truncate"

static func context_supported(context: Dictionary) -> bool:
	var platform: String = str(context.get("platform", ""))
	var display: String = str(context.get("display", ""))
	var desktop: bool = (platform == "Windows" and display == "Windows") or (platform == "Linux" and display in ["X11", "Wayland"])
	return desktop and context.get("godot_commit", "") == GODOT_COMMIT and context.get("rendering_method", "") == "gl_compatibility" and context.get("rendering_driver", "") == "opengl3"

static func pack_opacity(opacity: float) -> Dictionary:
	if not is_finite(opacity) or opacity < 0.0 or opacity > 1.0: return {}
	var bytes := PackedByteArray()
	bytes.resize(4)
	bytes.encode_float(0, opacity)
	var bits: int = bytes.decode_u32(0)
	var exponent: int = bits & 0x7f800000
	var half: int = 0
	if exponent > 0x38000000:
		half = (((exponent - 0x38000000) >> 13) & 0x7c00) | ((bits >> 13) & 0x03ff)
	var value: float = 0.0
	if half != 0:
		value = pow(2.0, float((half >> 10) - 15)) * (1.0 + float(half & 0x03ff) / 1024.0)
	return {"float32_opacity": bytes.decode_float(0), "packed_alpha_bits": half,
		"packed_opacity": value, "packed_transmittance": 1.0 - value}

static func evaluate(sample: Dictionary, fog: Dictionary, context: Dictionary) -> Dictionary:
	var result: Dictionary = {"status": "unavailable", "evaluation": "inconclusive",
		"reason": "Unsupported or unavailable renderer context", "model": MODEL,
		"packed_alpha_bits": null, "packed_opacity": null, "packed_transmittance": null,
		"qualified": false, "pixel_visibility": "unverified"}
	if not context_supported(context): return result
	if sample.get("status", "unavailable") != "measured":
		result["reason"] = "Invalid or unavailable analytic frontier sample"
		return result
	# Support only the verified M1 shader configuration. Other shader paths,
	# custom fog and arithmetic/precision contracts need separate verification.
	if fog != {"enabled": true, "mode": "depth", "density": 1.0, "height_density": 0.0, "begin_m": 16.0, "end_m": 96.0, "curve": 1.0}:
		result["reason"] = "Unsupported shader fog configuration"
		return result
	var transmittance: float = float(sample.get("fog_transmittance", NAN))
	if not is_finite(transmittance) or transmittance < 0.0 or transmittance > 1.0:
		result["reason"] = "Invalid analytic fog transmittance"
		return result
	var packed: Dictionary = pack_opacity(1.0 - transmittance)
	if packed.is_empty():
		result["reason"] = "Invalid analytic fog transmittance"
		return result
	result.merge(packed, true)
	result["status"] = "measured"
	var distance: float = float(sample["frontier_distance_m"])
	if int(sample["unready_regions"]) > 0 and float(result["packed_transmittance"]) > 0.0:
		result["evaluation"] = "failed"
		result["reason"] = "Unready region permits nonzero shader-model transmittance"
	elif distance < 96.0:
		# Float32 shader arithmetic may differ from the double analytic equation.
		# A conversion-only model cannot promote an inside-boundary alarm to pass.
		result["reason"] = "Inside-boundary shader arithmetic or clipped coverage is unverified"
	else:
		result["evaluation"] = "passed"
		result["reason"] = ""
	return result
