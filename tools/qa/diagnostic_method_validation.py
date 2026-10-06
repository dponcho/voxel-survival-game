"""Independent oracle for the pinned-engine synthetic method controls.

Closed-form counts over six constant-cost sections avoid reusing the frame loop,
ledger or classifier. This validates evaluator behavior, not hardware overhead.
Only synthetic cloud evidence is passed to this tool in Actions.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path

BLOCK = 5_000_000
DURATION = 30_000_000
START = 1_000_000
SETUP = 200
CLOSURE = 1_000
MAX_REPORT_BYTES = 512 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def reference_intervals(profile, permille):
    """Aggregate constant-interval runs analytically, retaining the final tail."""
    require(len(profile) == 6 and all(type(v) in [int, float] and v > 0 and int(v) == v for v in profile),
            "invalid synthetic profile")
    profile = [int(v) for v in profile]
    clock = samples = block_time = block_samples = 0
    blocks = []
    for section, nominal in enumerate(profile, 1):
        period = nominal * (1000 + permille) // 1000
        endpoint = section * BLOCK
        count = (endpoint - clock + period - 1) // period
        runs = [(period, count)]
        if section == 6 and clock + count * period > DURATION:
            runs = [(period, count - 1), (DURATION - clock - (count - 1) * period, 1)]
        for interval, remaining in runs:
            while remaining:
                take = min(remaining, (BLOCK - block_time + interval - 1) // interval)
                block_time += take * interval
                block_samples += take
                samples += take
                clock += take * interval
                remaining -= take
                if block_time >= BLOCK:
                    blocks.append({"samples": block_samples, "usec": block_time})
                    block_time = block_samples = 0
    require(clock == DURATION, "reference lost final interval")
    return samples, blocks, {"samples": block_samples, "usec": block_time}


def validate(report):
    require(report.get("schema") == 1 and report.get("passed") is True and report.get("failures") == [],
            "engine controls failed or unsupported schema")
    require(report.get("hardware_noise_calibrated") is False and report.get("shared_control_present") is False,
            "synthetic control claimed hardware/shared qualification")
    require(report.get("scope") == "synthetic-clock evaluator controls; not physical A/A or target qualification",
            "control scope changed")
    for key, expected in [("start_usec", START), ("duration_usec", DURATION), ("setup_usec", SETUP), ("closure_usec", CLOSURE)]:
        require(report.get(key) == expected, "unexpected " + key)
    controls = report.get("controls", [])
    require(len(controls) == 16, "missing or duplicate controls")
    seen = set()
    decisions = []
    for control in controls:
        workload = control["workload"]
        profile = control["profile_usec"]
        varying = profile == [4000, 5000, 4000, 5000, 4000, 5000]
        require(workload in ["H1", "H2"] and (varying or profile == [5000] * 6), "invalid workload/profile")
        effect = control["frame_scale_permille"]
        closure = control["enabled_closure_delta_usec"]
        effects = {(0, 0): "null", (5, 0): "below-limit", (20, 0): "above-limit", (0, 600000): "closure-cost"}
        require((effect, closure) in effects, "unexpected injected effect")
        name = workload + ("/varying/" if varying else "/stationary/") + effects[effect, closure]
        require(control["name"] == name and name not in seen, "duplicate or mislabeled control")
        seen.add(name)
        means = []
        variations = []
        require(len(control["phases"]) == 4, "incomplete quartet")
        for index, phase in enumerate(control["phases"]):
            enabled = index in [1, 2]
            require(phase["id"] == "AB-" + workload + "-" + ["off-1", "on-1", "on-2", "off-2"][index], "phase order")
            samples, blocks, partial = reference_intervals(profile, effect if enabled else 0)
            elapsed = DURATION + SETUP + CLOSURE + (closure if enabled else 0)
            account = phase["diagnostic_accounting"]
            require(phase["samples"] == samples and account["callbacks"] == samples, "interval/callback counts")
            require(account["blocks"] == blocks and account["partial_block"] == partial, "block or tail reconciliation")
            require(account["start_usec"] == START and account["end_usec"] == START + elapsed and account["elapsed_usec"] == elapsed, "full window reconciliation")
            require(account["last_callback_end_usec"] == START + SETUP + DURATION and phase["measurement_end_usec"] == account["last_callback_end_usec"], "final callback boundary")
            require(account["finalization_usec"] == CLOSURE + (closure if enabled else 0) and account["writer_drain_usec"] == 400, "nested closure/drain scope")
            require(account["callback_usec"] == samples * (100 if enabled else 20) and account["last_callback_usec"] == (100 if enabled else 20), "callback cost")
            require(account["switched_usec"] == samples * (80 if enabled else 0) and account["shared_usec"] == samples * 20 and account["switched_calls"] == (samples if enabled else 0), "switched/shared partition")
            require(account["invalid_partition"] is False and account["overflow"] is False, "invalid or overflowed control")
            require(phase["wall_seconds"] == 30 and phase["simulated_seconds"] == 30 and phase["simulation_ticks"] == 1800 and phase["actor_ticks"] == 1800 * (24 if workload == "H2" else 12), "simulation contract")
            means.append(Fraction(elapsed, samples))
            sections = [Fraction(block["usec"], block["samples"]) for block in blocks]
            variations.append((max(sections) - min(sections)) / (sum(sections) / len(sections)))
        require(len(means) == 4, "incomplete quartet")
        # Identical repeats yield an exact singleton ratio, independently of
        # the evaluator's floating-point conservative-envelope calculation.
        ratio = means[1] / means[0] - 1
        expected = "inconclusive" if varying else ("failed" if ratio >= Fraction(1, 100) else "passed")
        decision = control["comparison"]
        require(control["expected"] == expected and decision["outcome"] == expected, "control classification")
        for key in ["added_fraction", "lower_fraction", "upper_fraction"]:
            require(abs(decision[key] - float(ratio)) < 1e-12, "effect/window ratio " + key)
        require(decision["baseline_variation"] == 0 and decision["enabled_variation"] == 0, "identical repeats drifted")
        require(len(decision["within_phase_variation"]) == 4 and all(abs(actual - float(expected)) < 1e-12 for actual, expected in zip(decision["within_phase_variation"], variations)), "section stationarity arithmetic")
        for key, indices in [("off_mean_ms", [0, 3]), ("on_mean_ms", [1, 2])]:
            require(len(decision[key]) == 2 and all(abs(actual - float(means[index] / 1000)) < 1e-12 for actual, index in zip(decision[key], indices)), "full-window mean " + key)
        require(decision["workload_equivalence"] == "verified" and decision["probe_switch"] == "verified" and decision["qualified"] is False, "prerequisites or qualification")
        require(decision["reasons"] == (["Within-phase timing is unstable"] * 4 if varying else []), "unexpected eligibility reason")
        require(control["total_overhead"]["outcome"] == "inconclusive" and control["total_overhead"]["added_fraction"] is None, "missing shared control passed")
        decisions.append({"name": name, "injected_frame_scale_permille": effect,
                          "full_window_fraction": float(ratio), "outcome": expected})
    return {"passed": True, "controls": decisions, "control_count": len(seen),
            "finding": "stationarity gate rejects perfectly repeatable varying-route null and positive controls",
            "heavy_method_validated": False, "hardware_noise_calibrated": False,
            "shared_overhead_qualified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    require(args.report.stat().st_size <= MAX_REPORT_BYTES, "control report exceeds bound")
    result = validate(json.loads(args.report.read_text(encoding="utf-8")))
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
