extends RefCounted

# Conservative required-region coverage, not pixel visibility or physical scanout.
const FOG_BEGIN_M: float = 16.0
const FOG_END_M: float = 96.0
const ShaderFog = preload("res://scripts/benchmark_shader_fog.gd")
const COLUMNS: Array[String] = ["frontier_status", "frontier_candidate_regions", "frontier_checked_regions", "frontier_ready_regions", "frontier_empty_regions", "frontier_unready_regions", "frontier_distance_m", "frontier_kind", "frontier_block", "frontier_mesh_state", "fog_boundary_m", "fog_clearance_m", "fog_transmittance", "frontier_probe_usec", "camera_x", "camera_y", "camera_z", "camera_yaw"]
var samples: int = 0
var measured: int = 0
var invalid: int = 0
var exposed: int = 0
var inconclusive: int = 0
var minimum_distance: Variant = null
var minimum_clearance: Variant = null
var worst: Dictionary = {}
var renderer_context: Dictionary = {}
var renderer_measured: int = 0
var renderer_exposed: int = 0
var renderer_inconclusive: int = 0
var renderer_worst: Dictionary = {}

func configure_renderer_model(context: Dictionary) -> void:
	renderer_context = context.duplicate(true)

static func configure_m1_fog(environment: Environment) -> void:
	# Pinned Compatibility depth fog uses radial smoothstep, not camera Z depth.
	# Density 1 reaches opacity 1 at 96 m without an arbitrary opacity cutoff.
	environment.fog_enabled = true
	environment.fog_mode = Environment.FOG_MODE_DEPTH
	environment.fog_density = 1.0
	environment.fog_depth_begin = FOG_BEGIN_M
	environment.fog_depth_end = FOG_END_M
	environment.fog_depth_curve = 1.0
	environment.fog_height_density = 0.0

static func fog_configuration(environment: Environment, far_m: float) -> Dictionary:
	var end_m: float = environment.fog_depth_end if environment.fog_depth_end > 0.0 else far_m
	return {"enabled": environment.fog_enabled,
		"mode": "exponential" if environment.fog_mode == Environment.FOG_MODE_EXPONENTIAL else "depth",
		"density": environment.fog_density, "height_density": environment.fog_height_density,
		"begin_m": minf(environment.fog_depth_begin, end_m - 0.001), "end_m": end_m,
		"curve": environment.fog_depth_curve}

static func evaluate(sample: Dictionary, fog: Dictionary) -> Dictionary:
	var result: Dictionary = {"status": "unavailable", "evaluation": "inconclusive", "reason": sample.get("reason", "missing frontier sample"),
		"fog_boundary_m": null, "fog_clearance_m": null, "fog_transmittance": null}
	if sample.get("status", "unavailable") != "measured": return result
	var checked: int = int(sample.get("checked_regions", -1))
	var ready: int = int(sample.get("ready_regions", -1))
	var unready: int = int(sample.get("unready_regions", -1))
	var candidates: int = int(sample.get("candidate_regions", -1))
	var empty: int = int(sample.get("empty_regions", -1))
	var distance: float = float(sample.get("frontier_distance_m", NAN))
	if checked <= 0 or candidates < checked or candidates > 1024 or ready < 0 or unready < 0 or ready + unready != checked or empty < 0 or empty > ready or not is_finite(distance) or distance < 0.0:
		result["reason"] = "invalid or incomplete frontier sample"
		return result
	var density: float = float(fog.get("density", NAN))
	var height_density: float = float(fog.get("height_density", NAN))
	if not is_finite(density) or density < 0.0 or density > 1.0 or not is_finite(height_density) or height_density != 0.0:
		result["reason"] = "invalid or unsupported fog configuration"
		return result
	var transmittance: float = 1.0
	var boundary: Variant = null
	var boundary_reason: String = "fog is disabled or has no finite opaque boundary"
	if bool(fog.get("enabled", false)):
		if fog.get("mode", "") == "exponential":
			# Pinned Compatibility shader: 1 - exp(-length(vertex) * density).
			transmittance = exp(-distance * density)
			boundary_reason = "exponential fog has no finite fully opaque boundary"
		elif fog.get("mode", "") == "depth":
			var begin_m: float = float(fog.get("begin_m", NAN))
			var end_m: float = float(fog.get("end_m", NAN))
			var curve: float = float(fog.get("curve", NAN))
			if not is_finite(begin_m) or not is_finite(end_m) or not is_finite(curve) or begin_m < 0.0 or end_m <= begin_m or curve <= 0.0:
				result["reason"] = "invalid depth fog configuration"
				return result
			var t: float = clampf((distance - begin_m) / (end_m - begin_m), 0.0, 1.0)
			transmittance = 1.0 - pow(t * t * (3.0 - 2.0 * t), curve) * density
			if density == 1.0: boundary = end_m
		else:
			result["reason"] = "unknown fog mode"
			return result
	result["status"] = "measured"
	result["fog_transmittance"] = transmittance
	result["fog_boundary_m"] = boundary
	if boundary != null: result["fog_clearance_m"] = distance - float(boundary)
	if unready > 0 and (boundary == null or distance < float(boundary)):
		result["evaluation"] = "failed"
		result["reason"] = "Required mesh coverage is unready before fog obscures it"
	elif boundary == null:
		result["reason"] = boundary_reason
	elif unready == 0 and distance < float(boundary):
		result["reason"] = "far clip limits coverage evidence before the fog boundary"
	else:
		result["evaluation"] = "passed"
		result["reason"] = ""
	return result

func record(sample: Dictionary, fog: Dictionary) -> Dictionary:
	var row: Dictionary = sample.duplicate(true)
	row.merge(evaluate(sample, fog), true)
	samples += 1
	if row["status"] == "measured":
		measured += 1
		var distance: float = float(row["frontier_distance_m"])
		if minimum_distance == null or distance < float(minimum_distance): minimum_distance = distance
		if row["fog_clearance_m"] != null and (minimum_clearance == null or float(row["fog_clearance_m"]) < float(minimum_clearance)):
			minimum_clearance = row["fog_clearance_m"]
		if row["evaluation"] == "failed": exposed += 1
	else: invalid += 1
	if row["evaluation"] == "inconclusive": inconclusive += 1
	if worst.is_empty() or (row["evaluation"] == "failed" and (worst["evaluation"] != "failed" or float(row["frontier_distance_m"]) < float(worst["frontier_distance_m"]))): worst = row.duplicate(true)
	var renderer_row: Dictionary = ShaderFog.evaluate(row, fog, renderer_context)
	if renderer_row["status"] == "measured": renderer_measured += 1
	if renderer_row["evaluation"] == "failed": renderer_exposed += 1
	if renderer_row["evaluation"] == "inconclusive": renderer_inconclusive += 1
	if renderer_worst.is_empty() or (renderer_row["evaluation"] == "failed" and (renderer_worst["evaluation"] != "failed" or float(row["frontier_distance_m"]) < float(renderer_worst["frontier_distance_m"]))):
		renderer_worst = row.duplicate(true)
		renderer_worst.merge(renderer_row, true)
	return row

func snapshot(active: bool, enabled: bool = true) -> Dictionary:
	if not active: return {"evaluation": "not_run", "samples": 0, "renderer_model": {"evaluation": "not_run", "samples": 0, "qualified": false}}
	if not enabled:
		return {"status": "unavailable", "evaluation": "inconclusive", "reason": "probe disabled for matched A/B baseline",
			"samples": 0, "measured_samples": 0, "invalid_samples": 0, "exposed_samples": null,
			"minimum_frontier_distance_m": null, "minimum_fog_clearance_m": null, "qualified": false,
			"renderer_model": {"status": "unavailable", "evaluation": "inconclusive", "samples": 0,
				"measured_samples": 0, "exposed_samples": null, "qualified": false}}
	return {"evaluation": "failed" if exposed > 0 else ("inconclusive" if samples == 0 or inconclusive > 0 else "passed"), "samples": samples,
		"measured_samples": measured, "invalid_samples": invalid, "exposed_samples": exposed,
		"inconclusive_samples": inconclusive,
		"minimum_frontier_distance_m": minimum_distance, "minimum_fog_clearance_m": minimum_clearance,
		"worst_sample": worst.duplicate(true), "qualified": false,
		"renderer_model": {"evaluation": "failed" if renderer_exposed > 0 else ("inconclusive" if samples == 0 or renderer_inconclusive > 0 else "passed"),
			"scope": "analytic opacity quantized with pinned desktop shader polyfill; shader arithmetic and pixels unverified",
			"model": ShaderFog.MODEL, "context": renderer_context.duplicate(true), "samples": samples,
			"measured_samples": renderer_measured, "exposed_samples": renderer_exposed,
			"inconclusive_samples": renderer_inconclusive, "worst_sample": renderer_worst.duplicate(true),
			"qualified": false, "pixel_visibility": "unverified"}}

static func csv_fields(sample: Dictionary) -> PackedStringArray:
	if sample.is_empty():
		var missing := PackedStringArray()
		missing.resize(COLUMNS.size())
		missing.fill("not_run")
		return missing
	var fields := PackedStringArray([str(sample["status"])])
	for key: String in ["candidate_regions", "checked_regions", "ready_regions", "empty_regions", "unready_regions", "frontier_distance_m", "frontier_kind"]:
		fields.append(str(sample.get(key, "unavailable")))
	var block: Array = sample.get("block", [])
	fields.append("%d;%d;%d" % block if block.size() == 3 else "unavailable")
	fields.append(str(sample.get("mesh_state", "unavailable")))
	for key: String in ["fog_boundary_m", "fog_clearance_m", "fog_transmittance", "probe_usec", "camera_x", "camera_y", "camera_z", "camera_yaw"]:
		fields.append("unavailable" if sample.get(key) == null else str(sample[key]))
	return fields
