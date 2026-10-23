"""Recheck downloaded counter candidate/evidence without executing any engine."""
import contextlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ci"))
from build_support import read_json, write_json, digest
from cpu_cycle_capability import saved_audit, require
import mesh_admission_candidate_audit as prior
from shipping_saved_artifact_recheck import normalize


def run():
    source = ROOT / "build/downloaded-export-evidence"
    published = ROOT / "build/published-player"
    require(not (ROOT/"reports").exists(), "fresh independent recheck required")
    require((source/"build/dependencies.lock.json").read_bytes() == (ROOT/"build/dependencies.lock.json").read_bytes(),
            "downloaded dependency lock differs")
    shutil.copytree(source/"reports", ROOT/"reports")
    (ROOT/"build/engine-bundle").mkdir(parents=True)
    shutil.copy2(source/"build/engine-bundle/manifest.json", ROOT/"build/engine-bundle/manifest.json")
    (ROOT/"dist").mkdir()
    shutil.copy2(published/"Cairn-windows-x86_64.zip", ROOT/"dist/Cairn-windows-x86_64.zip")
    with (ROOT/"reports/counter-candidate-recheck.log").open("w",encoding="utf-8") as log:
        with contextlib.redirect_stdout(log): prior.audit()
    actual = read_json(ROOT/"reports/m1-mesh-admission-independent-audit.json")
    expected = read_json(source/"reports/m1-mesh-admission-independent-audit.json")
    require(normalize(actual) == normalize(expected), "cross-platform candidate/evidence audit differs")
    counter = saved_audit(ROOT/"reports", read_json(published/"BUILD_INFO.json"))
    require(counter == read_json(source/"reports/cpu-cycle-capability-audit.json"), "counter saved recheck differs")
    write_json(ROOT/"reports/cpu-cycle-downloaded-recheck.json", dict(passed=True, qualified=False,
        engine_executed=False, target_performance="not_run", portable_sha256=digest(published/"Cairn-windows-x86_64.zip"),
        counter_capability=counter, candidate_audit_reproduced=True, target_action_required_now=False))
    print("Downloaded counter candidate, exact saved evidence and corruption controls rechecked; no engine executed.")


if __name__ == "__main__": run()
