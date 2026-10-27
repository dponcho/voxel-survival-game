"""Independent clock-controls oracle and corrupted-evidence checks."""
import copy
from fractions import Fraction
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/qa"))
from diagnostic_method_validation import reference_intervals, validate


def event_walk(profile, effect):
    # Deliberately expand individual events. The production Python oracle
    # instead works over closed-form constant-period runs and section crossings.
    clock = block_usec = block_samples = samples = 0
    blocks = []
    while clock < 30_000_000:
        interval = profile[clock // 5_000_000] * (1000 + effect) // 1000
        interval = min(interval, 30_000_000 - clock)
        clock += interval
        samples += 1
        block_usec += interval
        block_samples += 1
        if block_usec >= 5_000_000:
            blocks.append({"samples": block_samples, "usec": block_usec})
            block_usec = block_samples = 0
    return samples, blocks, {"samples": block_samples, "usec": block_usec}


def fixture():
    report = {"schema": 1, "passed": True, "failures": [],
              "scope": "synthetic-clock evaluator controls; not physical A/A or target qualification",
              "hardware_noise_calibrated": False, "shared_control_present": False,
              "start_usec": 1_000_000, "duration_usec": 30_000_000,
              "setup_usec": 200, "closure_usec": 1000, "controls": []}
    for workload in ["H1", "H2"]:
        for varying in [False, True]:
            for effect, closure, label in [(0, 0, "null"), (5, 0, "below-limit"),
                                            (20, 0, "above-limit"), (0, 600000, "closure-cost")]:
                profile = [4000, 5000] * 3 if varying else [5000] * 6
                phases, means, variations = [], [], []
                for index, repetition in enumerate(["off-1", "on-1", "on-2", "off-2"]):
                    enabled = index in [1, 2]
                    n, blocks, partial = event_walk(profile, effect if enabled else 0)
                    elapsed = 30_001_200 + (closure if enabled else 0)
                    account = {"callbacks": n, "blocks": blocks, "partial_block": partial,
                               "start_usec": 1_000_000, "end_usec": 1_000_000 + elapsed, "elapsed_usec": elapsed,
                               "last_callback_end_usec": 31_000_200, "finalization_usec": 1000 + (closure if enabled else 0),
                               "writer_drain_usec": 400, "callback_usec": n * (100 if enabled else 20),
                               "last_callback_usec": 100 if enabled else 20, "switched_usec": n * (80 if enabled else 0),
                               "shared_usec": n * 20, "switched_calls": n if enabled else 0,
                               "invalid_partition": False, "overflow": False}
                    phases.append({"id": "AB-" + workload + "-" + repetition, "samples": n,
                                   "diagnostic_accounting": account, "measurement_end_usec": 31_000_200,
                                   "wall_seconds": 30, "simulated_seconds": 30, "simulation_ticks": 1800,
                                   "actor_ticks": 1800 * (24 if workload == "H2" else 12)})
                    means.append(Fraction(elapsed, n))
                    b = [Fraction(v["usec"], v["samples"]) for v in blocks]
                    variations.append(float((max(b) - min(b)) / (sum(b) / len(b))))
                ratio = float(means[1] / means[0] - 1)
                expected = "inconclusive" if varying else ("failed" if label in ["above-limit", "closure-cost"] else "passed")
                comparison = {"outcome": expected, "added_fraction": ratio, "lower_fraction": ratio, "upper_fraction": ratio,
                              "off_mean_ms": [float(means[i] / 1000) for i in [0, 3]],
                              "on_mean_ms": [float(means[i] / 1000) for i in [1, 2]],
                              "within_phase_variation": variations, "baseline_variation": 0, "enabled_variation": 0,
                              "workload_equivalence": "verified", "probe_switch": "verified", "qualified": False,
                              "reasons": ["Within-phase timing is unstable"] * 4 if varying else []}
                report["controls"].append({"name": workload + ("/varying/" if varying else "/stationary/") + label,
                                           "workload": workload, "profile_usec": profile, "frame_scale_permille": effect,
                                           "enabled_closure_delta_usec": closure, "expected": expected, "phases": phases,
                                           "comparison": comparison, "total_overhead": {"outcome": "inconclusive", "added_fraction": None}})
    return report


class MethodValidationTests(unittest.TestCase):
    def setUp(self):
        self.report = fixture()

    def test_closed_form_matches_events_across_section_and_tail_boundaries(self):
        for profile in [[5000] * 6, [4000, 5000] * 3, [4013, 5007, 3979, 5011, 4081, 4967]]:
            for effect in [0, 5, 20]:
                with self.subTest(profile=profile, effect=effect):
                    self.assertEqual(reference_intervals(profile, effect), event_walk(profile, effect))

    def test_stationary_controls_work_but_varying_controls_do_not_qualify(self):
        result = validate(self.report)
        self.assertEqual(result["control_count"], 16)
        self.assertFalse(result["heavy_method_validated"])
        self.assertFalse(result["hardware_noise_calibrated"])
        self.assertFalse(result["shared_overhead_qualified"])

    def test_missing_or_duplicate_controls_are_rejected(self):
        for mutation in [lambda x: x["controls"].pop(), lambda x: x["controls"].__setitem__(1, copy.deepcopy(x["controls"][0]))]:
            report = copy.deepcopy(self.report)
            mutation(report)
            with self.assertRaises(ValueError): validate(report)

    def test_dropped_tail_or_callback_rows_cannot_reconcile(self):
        for key in ["callbacks", "elapsed_usec", "last_callback_end_usec", "finalization_usec", "switched_usec", "shared_usec"]:
            report = copy.deepcopy(self.report)
            report["controls"][1]["phases"][1]["diagnostic_accounting"][key] += 1
            with self.subTest(key=key), self.assertRaises(ValueError): validate(report)
        report = copy.deepcopy(self.report)
        report["controls"][1]["phases"][1]["diagnostic_accounting"]["partial_block"]["usec"] -= 1
        with self.assertRaises(ValueError): validate(report)

    def test_modified_classification_or_scope_is_rejected(self):
        for mutation in [lambda x: x["controls"][4]["comparison"].__setitem__("outcome", "passed"),
                         lambda x: x.__setitem__("hardware_noise_calibrated", True),
                         lambda x: x["controls"][0]["total_overhead"].__setitem__("outcome", "passed")]:
            report = copy.deepcopy(self.report)
            mutation(report)
            with self.assertRaises(ValueError): validate(report)

    def test_missing_quartet_and_wrong_effect_are_rejected(self):
        report = copy.deepcopy(self.report)
        report["controls"][0]["phases"].pop()
        with self.assertRaises(ValueError): validate(report)
        report = copy.deepcopy(self.report)
        report["controls"][2]["frame_scale_permille"] = 5
        with self.assertRaises(ValueError): validate(report)

    def test_finalization_cost_remains_in_full_window(self):
        result = validate(self.report)
        closure = next(row for row in result["controls"] if row["name"] == "H1/stationary/closure-cost")
        self.assertEqual(closure["outcome"], "failed")
        self.assertAlmostEqual(closure["full_window_fraction"], 600000 / 30001200)


if __name__ == "__main__":
    unittest.main()
