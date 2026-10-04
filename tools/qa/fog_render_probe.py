"""Optional hosted render evidence; unavailable OpenGL never becomes a pass."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
MARKER = "CAIRN_M1_FOG_RENDER="
NO_CONTEXT = (
    "Your video card drivers seem not to support the required OpenGL",
    "Unable to initialize OpenGL video driver",
    "Can't create an OpenGL context",
    "Failed to create an OpenGL context",
    "Could not initialize OpenGL",
)


def classify(output, returncode, timed_out=False):
    # A shader/parser defect is a failure even if a driver error also appears.
    if "SCRIPT ERROR:" in output or "SHADER ERROR:" in output or "Shader compilation failed" in output:
        raise RuntimeError("Fog conversion probe has a script or shader error")
    matches = [line.split(MARKER, 1)[1] for line in output.splitlines() if MARKER in line]
    if matches:
        report = json.loads(matches[-1])
        if returncode or timed_out or "ERROR:" in output:
            raise RuntimeError("Fog conversion probe failed after engine startup")
        if report.get("status") == "unavailable" and report.get("qualified") is False:
            return report
        if report.get("status") != "passed" or report.get("passed") is not True or report.get("qualified") is not False:
            raise RuntimeError("Fog conversion probe returned incorrect evidence")
        expected = [0x0000, 0x3800, 0x3bff, 0x3bff, 0x3bff, 0x3bff, 0x3c00]
        samples = report.get("samples", [])
        if len(samples) != len(expected) or any(row.get("expected_bits") != bits or row.get("observed_bits") != bits
                                                for row, bits in zip(samples, expected)):
            raise RuntimeError("Fog conversion readback did not retain the independent encodings")
        return report
    if any(message.lower() in output.lower() for message in NO_CONTEXT):
        return {"status": "unavailable", "passed": False, "qualified": False,
                "reason": "Hosted runner could not initialize the required OpenGL context",
                "scope": "conversion probe only; terrain fog and target pixels unverified"}
    raise RuntimeError("Fog conversion probe did not complete; unknown failure or timeout")


def run():
    REPORTS.mkdir(exist_ok=True)
    log_path = REPORTS / "m1-fog-render.log"
    command = [ROOT / "build/engine-bundle/editor.exe", "--path", ROOT / "game",
               "--rendering-method", "gl_compatibility", "--rendering-driver", "opengl3",
               "--resolution", "32x32", "--audio-driver", "Dummy",
               "--script", "res://scripts/benchmark_fog_render_probe.gd"]
    timed_out = False
    with log_path.open("w", encoding="utf-8") as log:
        try:
            result = subprocess.run([str(value) for value in command], cwd=ROOT,
                                    stdout=log, stderr=subprocess.STDOUT, timeout=45)
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            returncode = None
    output = log_path.read_text(encoding="utf-8", errors="replace")
    try:
        report = classify(output, returncode, timed_out)
    except (RuntimeError, ValueError) as error:
        raise RuntimeError(f"{error}; see {log_path.name}\n{output[-8000:]}") from error
    (REPORTS / "m1-fog-render.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"m1-fog-render: {report['status']} (target pixels unverified)", flush=True)


if __name__ == "__main__":
    run()
