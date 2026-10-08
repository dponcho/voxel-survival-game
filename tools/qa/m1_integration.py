"""Additional M1 cloud-only coverage; uses the already qualified engine bundle."""
import json
import subprocess
from pathlib import Path
from fog_render_probe import run as check_fog_render
from diagnostic_method_validation import validate as validate_method
from route_calibration import validate_controls, reconcile_folder
from endpoint_precision import reconcile_saved as reconcile_precision
from fixed_work import reconcile_saved as reconcile_fixed, reconcile_runtime
from cpu_dose import reconcile_saved as reconcile_cpu, reconcile_runtime as reconcile_cpu_runtime, scope as cpu_scope

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def check(command, name, marker, timeout=300):
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / (name + ".log")
    with path.open("w", encoding="utf-8") as log:
        result = subprocess.run([str(value) for value in command], cwd=ROOT,
                                stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    output = path.read_text(encoding="utf-8", errors="replace")
    matches = [line.split(marker, 1)[1] for line in output.splitlines() if marker in line]
    if result.returncode or not matches or "SCRIPT ERROR:" in output or "ERROR:" in output:
        raise RuntimeError(f"{name}: failed; see {path.name}\n{output[-12000:]}")
    report = json.loads(matches[-1])
    if report.get("passed") is False or report.get("integration_failures"):
        raise RuntimeError(f"{name}: incorrect native result: {report}")
    (REPORTS / (name + ".json")).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"{name}: passed", flush=True)


if __name__ == "__main__":
    check([ROOT / "build/engine-bundle/editor.exe", "--headless", "--path", ROOT / "game",
           "--script", "res://scripts/benchmark_method_validation.gd"],
          "m1-diagnostic-method-controls", "CAIRN_DIAGNOSTIC_METHOD=", 60)
    controls = json.loads((REPORTS / "m1-diagnostic-method-controls.json").read_text(encoding="utf-8"))
    method = validate_method(controls)
    (REPORTS / "m1-diagnostic-method-validation.json").write_text(json.dumps(method, indent=2), encoding="utf-8")
    print("diagnostic method controls reconciled; heavy method remains unvalidated", flush=True)
    check([ROOT / "build/engine-bundle/editor.exe", "--headless", "--path", ROOT / "game",
           "--script", "res://scripts/benchmark_calibration_tests.gd"],
          "m1-route-calibration-controls", "CAIRN_ROUTE_CONTROLS=", 60)
    route_controls = json.loads((REPORTS / "m1-route-calibration-controls.json").read_text(encoding="utf-8"))
    if (REPORTS / "m1-route-calibration-controls.json").stat().st_size > 1024 * 1024:
        raise RuntimeError("Route control report exceeds 1 MiB")
    (REPORTS / "m1-route-calibration-validation.json").write_text(
        json.dumps(validate_controls(route_controls), indent=2), encoding="utf-8")
    precision_raw = REPORTS / "m1-endpoint-precision-raw"
    precision_raw.mkdir(exist_ok=True)
    check([ROOT / "build/engine-bundle/editor.exe", "--headless", "--path", ROOT / "game",
           "--script", "res://scripts/benchmark_endpoint_precision_tests.gd", "--",
           "--precision-output=" + str(precision_raw)],
          "m1-endpoint-precision-controls", "CAIRN_ENDPOINT_PRECISION=", 60)
    (REPORTS / "m1-endpoint-precision-validation.json").write_text(json.dumps(
        reconcile_precision(REPORTS / "m1-endpoint-precision-controls.json", precision_raw), indent=2), encoding="utf-8")
    print("endpoint/count clocks and authoritative verdicts independently reconciled", flush=True)
    fixed_raw = REPORTS / "m1-fixed-work-raw"
    fixed_raw.mkdir(exist_ok=True)
    check([ROOT / "build/engine-bundle/editor.exe", "--headless", "--path", ROOT / "game",
           "--script", "res://scripts/benchmark_fixed_work_tests.gd", "--", "--fixed-output=" + str(fixed_raw)],
          "m1-fixed-work-controls", "CAIRN_FIXED_WORK=", 60)
    (REPORTS / "m1-fixed-work-validation.json").write_text(json.dumps(
        reconcile_fixed(REPORTS / "m1-fixed-work-controls.json", fixed_raw), indent=2), encoding="utf-8")
    print("fixed-work durations/counts and exact boundaries independently reconciled", flush=True)
    cpu_raw = REPORTS / "m1-cpu-dose-raw"
    cpu_raw.mkdir(exist_ok=True)
    check([ROOT / "build/engine-bundle/editor.exe", "--headless", "--path", ROOT / "game",
           "--script", "res://scripts/benchmark_cpu_dose_tests.gd", "--", "--cpu-output=" + str(cpu_raw)],
          "m1-cpu-dose-controls", "CAIRN_CPU_DOSE_CONTROLS=", 60)
    (REPORTS / "m1-cpu-dose-validation.json").write_text(json.dumps(
        reconcile_cpu(REPORTS / "m1-cpu-dose-controls.json", cpu_raw), indent=2), encoding="utf-8")
    for executable, suffix in [(ROOT / "build/engine-bundle/editor.exe", "editor"),
                               (ROOT / "dist/player/Cairn.exe", "release")]:
        runtime_raw = REPORTS / ("m1-cpu-dose-" + suffix + "-raw")
        runtime_raw.mkdir(exist_ok=True)
        command = [executable, "--headless", "--path", ROOT / "game"] if suffix == "editor" else [executable, "--headless"]
        check(command + ["--", "--cpu-dose-probe", "--cpu-output=" + str(runtime_raw)],
              "m1-cpu-dose-" + suffix, "CAIRN_CPU_DOSE_RUNTIME=", 60)
        (REPORTS / ("m1-cpu-dose-" + suffix + "-validation.json")).write_text(json.dumps(
            reconcile_cpu_runtime(runtime_raw, json.loads((ROOT / "dist/player/BUILD_INFO.json").read_text(encoding="utf-8"))), indent=2), encoding="utf-8")
    print("CPU clock thresholds, count/wait/route masking and real native callback placement reconciled", flush=True)
    check([ROOT / "build/engine-bundle/editor.exe", "--headless", "--path", ROOT / "game",
           "--script", "res://scripts/m1_streaming_tests.gd"],
          "m1-streaming-collision-eviction-cancellation", "CAIRN_M1_STREAMING=", 600)
    for render_size, workers in [(16, 1), (32, 2), (16, 2)]:
        check([ROOT / "dist/player/Cairn.exe", "--headless", "--", "--m1-smoke",
               f"--render-size={render_size}", f"--workers={workers}",
               "--m1-report-root=" + str(REPORTS / f"m1-release-{render_size}-{workers}-raw")],
              f"m1-release-{render_size}-{workers}", "CAIRN_M1_SMOKE=")
    check([ROOT / "dist/player/Cairn.exe", "--headless", "--", "--m1-smoke",
           "--benchmark-mode=startup", "--m1-report-root=" + str(REPORTS / "m1-startup-raw")], "m1-startup-release", "CAIRN_M1_SMOKE=")
    check([ROOT / "dist/player/Cairn.exe", "--headless", "--", "--m1-smoke",
           "--benchmark-mode=heavy-ab", "--m1-report-root=" + str(REPORTS / "m1-heavy-ab-raw")], "m1-heavy-ab-release", "CAIRN_M1_SMOKE=")
    raw_root = REPORTS / "m1-route-calibration-raw"
    check([ROOT / "dist/player/Cairn.exe", "--headless", "--", "--m1-smoke",
           "--benchmark-mode=calibration", "--m1-report-root=" + str(raw_root)],
          "m1-route-calibration-release", "CAIRN_M1_SMOKE=")
    folders = list(raw_root.glob("*/summary.json"))
    if len(folders) != 1:
        raise RuntimeError("Calibration smoke folder missing or duplicated")
    (REPORTS / "m1-route-calibration-saved.json").write_text(
        json.dumps(reconcile_folder(folders[0].parent), indent=2), encoding="utf-8")
    (REPORTS / "m1-fixed-work-saved.json").write_text(
        json.dumps(reconcile_runtime(folders[0].parent), indent=2), encoding="utf-8")
    for summary_path in REPORTS.glob("m1-*-raw/*/summary.json"):
        saved = json.loads(summary_path.read_text(encoding="utf-8"))
        cpu_scope(saved["cpu_dose_sensitivity"], not_run=True)
        if any("cpu_dose_accounting" in p for p in saved["scenarios"]):
            raise RuntimeError("Ordinary gameplay/calibration unexpectedly ran a CPU dose")
    check_fog_render()
