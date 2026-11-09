extends "res://scripts/m1_preparation_prefix_fixture.gd"

# Frozen rejected implementation: c4c599e's saved source witness, runtime lines
# 456-461. Run only by the paired controller control, never by a route.
func _publish_finished_trial() -> void:
	trial["complete"] = true
	trials.append(trial.duplicate(true))
	if not _write_json("sequence-prefix.json", {"trials": trials, "no_retry": true}): report_io_failed = true
	if not bool(trial.valid): abort_reason = "Attribution trial guard failed: " + str(trial.id)
	trial.clear()
	if not abort_reason.is_empty(): scenarios.resize(scenario_index + 1)
