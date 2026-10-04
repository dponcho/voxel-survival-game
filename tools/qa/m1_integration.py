"""Additional M1 cloud-only coverage; uses the already qualified engine bundle."""
import json
import subprocess
from pathlib import Path
from fog_render_probe import run as check_fog_render

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
           "--script", "res://scripts/m1_streaming_tests.gd"],
          "m1-streaming-collision-eviction-cancellation", "CAIRN_M1_STREAMING=", 600)
    for render_size, workers in [(16, 1), (32, 2), (16, 2)]:
        check([ROOT / "dist/player/Cairn.exe", "--headless", "--", "--m1-smoke",
               f"--render-size={render_size}", f"--workers={workers}"],
              f"m1-release-{render_size}-{workers}", "CAIRN_M1_SMOKE=")
    check([ROOT / "dist/player/Cairn.exe", "--headless", "--", "--m1-smoke",
           "--benchmark-mode=startup"], "m1-startup-release", "CAIRN_M1_SMOKE=")
    check_fog_render()
