extends RefCounted

const Frontier = preload("res://scripts/benchmark_frontier.gd")
const ShaderFog = preload("res://scripts/benchmark_shader_fog.gd")

static func verify() -> Array[String]:
	var failures: Array[String] = []
	var sample: Dictionary = {"status": "measured", "candidate_regions": 4, "checked_regions": 3, "ready_regions": 2,
		"empty_regions": 1, "unready_regions": 1, "frontier_distance_m": 96.0, "block": [-1, -1, 0], "mesh_state": "missing"}
	var fog: Dictionary = {"enabled": true, "mode": "exponential", "density": 0.025, "height_density": 0.0}
	var result: Dictionary = Frontier.evaluate(sample, fog)
	if result["evaluation"] != "failed" or result["fog_boundary_m"] != null or result["fog_clearance_m"] != null or absf(float(result["fog_transmittance"]) - 0.090717953289) > 0.000001:
		failures.append("Exponential fog manufactured an opaque boundary or concealed a gap")
	var complete: Dictionary = sample.duplicate(true)
	complete["unready_regions"] = 0
	complete["ready_regions"] = 3
	if Frontier.evaluate(complete, fog)["evaluation"] != "inconclusive": failures.append("Missing fog boundary passed")
	fog.merge({"mode": "depth", "density": 1.0, "begin_m": 16.0, "end_m": 64.0, "curve": 1.0}, true)
	for distance: float in [63.0, 64.0, 65.0]:
		sample["frontier_distance_m"] = distance
		result = Frontier.evaluate(sample, fog)
		if result["evaluation"] != ("failed" if distance < 64.0 else "passed") or float(result["fog_clearance_m"]) != distance - 64.0:
			failures.append("Fog crossing or exact-boundary classification is wrong")
	complete["frontier_distance_m"] = 32.0
	if Frontier.evaluate(complete, fog)["evaluation"] != "inconclusive": failures.append("Clipped scan passed an unobserved fog boundary")
	for key: String in ["density", "height_density", "begin_m", "end_m", "curve"]:
		var invalid_fog: Dictionary = fog.duplicate(true)
		invalid_fog[key] = NAN
		if Frontier.evaluate(sample, invalid_fog)["status"] != "unavailable": failures.append("Non-finite fog sample passed: " + key)
	for change: Dictionary in [{"status": "unavailable"}, {"checked_regions": 0}, {"candidate_regions": 1025}, {"ready_regions": 0}, {"empty_regions": 4}, {"frontier_distance_m": NAN}, {"frontier_distance_m": -1.0}]:
		var invalid_sample: Dictionary = sample.duplicate(true)
		invalid_sample.merge(change, true)
		if Frontier.evaluate(invalid_sample, fog)["status"] != "unavailable": failures.append("Invalid native coverage passed")
	var ledger := Frontier.new()
	sample["frontier_distance_m"] = 63.0
	ledger.record(sample, fog)
	ledger.record({"status": "unavailable", "reason": "bounded scan unavailable"}, fog)
	var summary: Dictionary = ledger.snapshot(true)
	if summary["samples"] != 2 or summary["measured_samples"] != 1 or summary["invalid_samples"] != 1 or summary["exposed_samples"] != 1 or summary["evaluation"] != "failed" or summary["minimum_fog_clearance_m"] != -1.0:
		failures.append("Frontier ledger lost failed or unavailable evidence")
	if Frontier.csv_fields({}).size() != Frontier.COLUMNS.size() or Frontier.csv_fields(ledger.worst).size() != Frontier.COLUMNS.size() or Frontier.csv_fields(ledger.worst)[8] != "-1;-1;0":
		failures.append("Frontier CSV lost fields or negative coordinates")
	if ledger.snapshot(false)["evaluation"] != "not_run": failures.append("Other scenarios claimed frontier evidence")
	failures.append_array(_verify_m1_profile())
	failures.append_array(_verify_shader_model())
	return failures

static func _verify_shader_model() -> Array[String]:
	var failures: Array[String] = []
	# Independent expected encodings at exact binary16 values, both sides of
	# the nearest-rounding midpoint, and the polyfill's small-value cutoff.
	var cases: Array[Array] = [[0.0, 0x0000, 0.0], [0.5, 0x3800, 0.5],
		[0.99951171875, 0x3bff, 0.99951171875],
		[0.999755859375, 0x3bff, 0.99951171875],
		[0.9998189509608, 0x3bff, 0.99951171875],
		[0.9999211701536, 0x3bff, 0.99951171875],
		[1.0, 0x3c00, 1.0], [0.00006103515625, 0x0400, 0.00006103515625],
		[0.000060, 0x0000, 0.0]]
	for entry: Array in cases:
		var packed: Dictionary = ShaderFog.pack_opacity(float(entry[0]))
		if packed["packed_alpha_bits"] != entry[1] or packed["packed_opacity"] != entry[2]:
			failures.append("Shader polyfill packing differs from independent binary16 encoding")
	for value: float in [NAN, INF, -0.01, 1.01]:
		if not ShaderFog.pack_opacity(value).is_empty(): failures.append("Invalid shader opacity became a numeric model")
	var context: Dictionary = {"godot_commit": ShaderFog.GODOT_COMMIT, "rendering_method": "gl_compatibility",
		"rendering_driver": "opengl3", "platform": "Windows", "display": "Windows"}
	var fog: Dictionary = {"enabled": true, "mode": "depth", "density": 1.0,
		"height_density": 0.0, "begin_m": 16.0, "end_m": 96.0, "curve": 1.0}
	var sample: Dictionary = {"status": "measured", "candidate_regions": 3, "checked_regions": 3,
		"ready_regions": 2, "empty_regions": 1, "unready_regions": 1, "frontier_distance_m": 95.38}
	var ledger := Frontier.new()
	ledger.configure_renderer_model(context)
	var row: Dictionary = ledger.record(sample, fog)
	var model: Dictionary = ledger.snapshot(true)["renderer_model"]
	if row["evaluation"] != "failed" or model["evaluation"] != "failed" or model["worst_sample"]["packed_alpha_bits"] != 0x3bff:
		failures.append("Nearest rounding concealed the desktop shader's nonzero transmittance")
	if model["qualified"] or model["pixel_visibility"] != "unverified": failures.append("Shader model claimed measured pixels")
	sample["frontier_distance_m"] = 96.0
	if ShaderFog.evaluate(_evaluated_sample(sample, fog), fog, context)["evaluation"] != "passed": failures.append("Exact shader fog boundary did not pass the model")
	sample["frontier_distance_m"] = 95.99999
	if ShaderFog.evaluate(_evaluated_sample(sample, fog), fog, context)["evaluation"] != "inconclusive": failures.append("Float32 conversion certified unverified inside-boundary arithmetic")
	sample["unready_regions"] = 0
	sample["ready_regions"] = 3
	sample["frontier_distance_m"] = 95.0
	if ShaderFog.evaluate(_evaluated_sample(sample, fog), fog, context)["evaluation"] != "inconclusive": failures.append("Clipped coverage passed the shader model")
	for change: Dictionary in [{"godot_commit": "unknown"}, {"rendering_method": "forward_plus"},
		{"rendering_driver": "opengl3_angle"}, {"rendering_driver": "opengl3_es"},
		{"platform": "Web"}, {"display": "headless"}, {"display": ""}, {"rendering_driver": ""}]:
		var other: Dictionary = context.duplicate(true)
		other.merge(change, true)
		if ShaderFog.evaluate(row, fog, other)["status"] != "unavailable": failures.append("Unsupported renderer path passed the shader model")
	var invalid: Dictionary = sample.duplicate(true)
	invalid["frontier_distance_m"] = NAN
	if ShaderFog.evaluate(_evaluated_sample(invalid, fog), fog, context)["status"] != "unavailable": failures.append("Invalid frontier became a valid shader model")
	var changed_fog: Dictionary = fog.duplicate(true)
	changed_fog["density"] = 0.5
	if ShaderFog.evaluate(row, changed_fog, context)["status"] != "unavailable": failures.append("Unverified fog setting passed the shader model")
	ledger.record({"status": "unavailable"}, fog)
	model = ledger.snapshot(true)["renderer_model"]
	if model["samples"] != 2 or model["measured_samples"] != 1 or model["exposed_samples"] != 1 or model["inconclusive_samples"] != 1 or model["evaluation"] != "failed": failures.append("Shader ledger lost failed or unavailable evidence")
	return failures

static func _evaluated_sample(sample: Dictionary, fog: Dictionary) -> Dictionary:
	var row: Dictionary = sample.duplicate(true)
	row.merge(Frontier.evaluate(sample, fog), true)
	return row

static func _verify_m1_profile() -> Array[String]:
	var failures: Array[String] = []
	var environment := Environment.new()
	Frontier.configure_m1_fog(environment)
	var fog: Dictionary = Frontier.fog_configuration(environment, 96.0)
	var expected: Dictionary = {"enabled": true, "mode": "depth", "density": 1.0,
		"height_density": 0.0, "begin_m": 16.0, "end_m": 96.0, "curve": 1.0}
	if fog != expected: failures.append("Actual M1 Environment did not retain the finite 96 m fog profile")
	var sample: Dictionary = {"status": "measured", "candidate_regions": 3, "checked_regions": 3,
		"ready_regions": 2, "empty_regions": 1, "unready_regions": 1, "frontier_distance_m": 0.0}
	# Independent analytic values at endpoints and quarter points of the pinned
	# shader's smoothstep interval. Do not use the production equation as oracle.
	var distances: Array[float] = [0.0, 16.0, 36.0, 56.0, 76.0, 95.0, 96.0, 112.0]
	var transmittances: Array[float] = [1.0, 1.0, 0.84375, 0.5, 0.15625, 0.00046484375, 0.0, 0.0]
	for i: int in range(distances.size()):
		sample["frontier_distance_m"] = distances[i]
		var result: Dictionary = Frontier.evaluate(sample, fog)
		if result["fog_boundary_m"] != 96.0 or result["fog_clearance_m"] != distances[i] - 96.0 or absf(float(result["fog_transmittance"]) - transmittances[i]) > 0.000001:
			failures.append("Finite M1 fog differs from the pinned shader at distance " + str(distances[i]))
		if result["evaluation"] != ("failed" if distances[i] < 96.0 else "passed"):
			failures.append("Finite M1 fog concealed inside-boundary unready coverage")
	var complete: Dictionary = sample.duplicate(true)
	complete.merge({"ready_regions": 3, "unready_regions": 0, "frontier_distance_m": 96.0}, true)
	if Frontier.evaluate(complete, fog)["evaluation"] != "passed": failures.append("Complete coverage through the finite fog boundary did not pass")
	complete["frontier_distance_m"] = 95.0
	if Frontier.evaluate(complete, fog)["evaluation"] != "inconclusive": failures.append("Shortened scan passed an unobserved 96 m boundary")
	var partial: Dictionary = fog.duplicate(true)
	partial["density"] = 0.5
	var partial_result: Dictionary = Frontier.evaluate(sample, partial)
	if partial_result["evaluation"] != "failed" or partial_result["fog_boundary_m"] != null:
		failures.append("Partial terminal opacity concealed an unready region")
	partial["enabled"] = false
	if Frontier.evaluate(complete, partial)["evaluation"] != "inconclusive": failures.append("Disabled fog manufactured a boundary")
	return failures
