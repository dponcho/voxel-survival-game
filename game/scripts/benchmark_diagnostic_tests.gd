extends RefCounted

const Evaluation = preload("res://scripts/benchmark_evaluation.gd")
const Diagnostics = preload("res://scripts/benchmark_diagnostics.gd")

static func verify_flush(next_frame: Signal) -> Array[String]:
	var failures: Array[String] = []
	var writer: Dictionary = {"attempts": 0, "pending": true, "writes": 0}
	var flush := func() -> void:
		writer["attempts"] += 1
		if writer["attempts"] >= 3:
			writer["pending"] = false
			writer["writes"] += 1
	var pending := func() -> bool: return bool(writer["pending"])
	var healthy := func() -> bool: return false
	if not await Diagnostics.drain_pending(flush, pending, healthy, next_frame, 4) or writer["writes"] != 1:
		failures.append("Transient writer rejection lost or duplicated the final batch")
	var blocked := func() -> bool: return true
	var no_progress := func() -> void: pass
	if await Diagnostics.drain_pending(no_progress, blocked, healthy, next_frame, 3):
		failures.append("Permanently blocked writer was reported complete")
	if await Diagnostics.drain_pending(no_progress, blocked, blocked, next_frame, 3):
		failures.append("Failed writer was reported complete")
	return failures

static func _phases(on_usec: int = 30150000, off_usec: int = 30000000) -> Array[Dictionary]:
	var phases: Array[Dictionary] = []
	for id: String in ["AB-off-1", "AB-on-1", "AB-on-2", "AB-off-2"]:
		var blocks: Array[Dictionary] = []
		for i: int in range(6): blocks.append({"samples": 1000, "usec": 5000000})
		phases.append({"id": id, "completed": true, "samples": 6000, "simulated_seconds": 30.0,
			"wall_seconds": 30.0, "readiness_stops": 0, "actor_ticks": 21600, "simulation_ticks": 1800,
			"evaluation": "passed", "diagnostic_accounting": {"callbacks": 6000, "overflow": false,
				"elapsed_usec": off_usec if id.begins_with("AB-off") else on_usec, "blocks": blocks}})
	return phases

static func verify() -> Array[String]:
	var failures: Array[String] = []
	for sample: Dictionary in [
		{"value": 0.0, "expected": "unavailable"}, {"value": 3.0, "expected": "valid"},
		{"value": -1.0, "expected": "invalid"}, {"value": INF, "expected": "invalid"},
		{"value": NAN, "expected": "invalid"}, {"value": 1.0e15, "expected": "invalid"}]:
		if Evaluation.gpu_sample_status(sample["value"], 1000000) != sample["expected"]:
			failures.append("Invalid or unavailable GPU query contaminated valid timing")
	var ledger := Diagnostics.new()
	ledger.start(100)
	# Simulated probes (10), formatting/flush (20), UI (30): timer ends after all three.
	ledger.record_callback(120, 180)
	ledger.record_callback(200, 300)
	var result: Dictionary = ledger.snapshot(450, 80)
	if result["elapsed_usec"] != 350 or result["callback_usec"] != 160 or result["callbacks"] != 2 or result["last_callback_usec"] != 100 or result["finalization_usec"] != 150 or result["writer_drain_usec"] != 80:
		failures.append("Diagnostic scopes lost setup, final callback, UI or writer drain")
	for i: int in range(65): ledger.record_interval(5000000)
	if ledger.blocks.size() != 64 or not ledger.overflow: failures.append("Diagnostic block storage is unbounded or overflow hidden")
	var cases: Array[Dictionary] = [
		{"name": "stable below limit", "phases": _phases(), "expected": "passed"},
		{"name": "stable above limit", "phases": _phases(30600000), "expected": "failed"},
		{"name": "exact limit", "phases": _phases(30300000), "expected": "failed"},
		{"name": "negative effect", "phases": _phases(29400000), "expected": "inconclusive"}]
	for label: String in ["baseline drift", "enabled drift", "threshold overlap", "block drift", "missing", "duplicate", "stalled", "no samples", "missing actor", "overflow"]:
		var phases: Array[Dictionary] = _phases()
		match label:
			"baseline drift": phases[3]["diagnostic_accounting"]["elapsed_usec"] = 31000000
			"enabled drift": phases[2]["diagnostic_accounting"]["elapsed_usec"] = 31000000
			"threshold overlap":
				phases[1]["diagnostic_accounting"]["elapsed_usec"] = 30270000
				phases[2]["diagnostic_accounting"]["elapsed_usec"] = 30330000
			"block drift": phases[1]["diagnostic_accounting"]["blocks"][2]["usec"] = 5100000
			"missing": phases.pop_back()
			"duplicate": phases[2]["id"] = "AB-on-1"
			"stalled": phases[1]["wall_seconds"] = 32.0
			"no samples": phases[1]["samples"] = 0
			"missing actor": phases[1]["actor_ticks"] = 0
			"overflow": phases[1]["diagnostic_accounting"]["overflow"] = true
		cases.append({"name": label, "phases": phases, "expected": "inconclusive"})
	for test: Dictionary in cases:
		result = Evaluation.diagnostic_ab(test["phases"], false, false)
		if result["outcome"] != test["expected"] or result["qualified"]:
			failures.append("A/B classification: " + str(test["name"]))
	if Evaluation.diagnostic_ab(_phases(), true, false)["outcome"] != "inconclusive": failures.append("Smoke qualified overhead")
	if Evaluation.diagnostic_ab(_phases(), false, true)["outcome"] != "inconclusive": failures.append("Failed I/O qualified overhead")
	var empty: Array[Dictionary] = []
	if Evaluation.diagnostic_ab(empty, false, false)["outcome"] != "not_run": failures.append("Missing A/B run was evaluated")
	return failures
