"""Bounded native counter capability and exact saved-evidence verification.

No v2 inventory, route, dose calibration, cost estimator or cycle/time conversion.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ci"))
from build_support import run as command, write_json, read_json, digest
from pipeline import input_hash

SCHEMA = "cairn-cpu-cycle-capability-1"
KINDS = ("process_lo", "thread_lo", "thread_hi", "process_hi")
MAX_U64 = (1 << 64) - 1
DECIMALS = ["0", "9007199254740993", "9223372036854775808", str(MAX_U64)]


def require(ok, message):
    if not ok:
        raise RuntimeError("CPU cycle capability: " + message)


def uint(value):
    require(isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]{0,19}", value) is not None,
            "counter/wall must be a canonical unsigned decimal string")
    number = int(value)
    require(number <= MAX_U64, "unsigned 64-bit overflow")
    return number


def failed_value(value, unavailable=False):
    require(value["available"] is (not unavailable) and value["success"] is False
            and type(value["error"]) is int and 0 < value["error"] <= (1 << 32) - 1
            and value["cycles"] is None, "failed/unavailable value was lost or replaced by zero")


def observation(value):
    require(value["schema"] == "cairn-cpu-cycle-observation-1" and value["status"] == "measured"
            and value["platform"] == "windows" and value["process_api"] == "QueryProcessCycleTime"
            and value["thread_api"] == "QueryThreadCycleTime", "counter unavailable, failed or contradictory")
    uint(value["thread_id"])
    reads = value["reads"]
    require(len(reads) == 4 and [v["kind"] for v in reads] == list(KINDS), "counter read nesting/order")
    previous = 0
    for item in reads:
        require(item["available"] is True and item["success"] is True
                and type(item["error"]) is int and item["error"] == 0, "unsuccessful counter")
        uint(item["cycles"])
        begin, end = uint(item["wall_before_usec"]), uint(item["wall_after_usec"])
        require(previous <= begin <= end, "wall bracket reversal")
        previous = end
    require(uint(reads[0]["cycles"]) <= uint(reads[3]["cycles"])
            and uint(reads[1]["cycles"]) <= uint(reads[2]["cycles"]), "counter reversal")
    return value


def sequence(values, same_thread=True):
    for value in values:
        observation(value)
    for start, end in zip(values, values[1:]):
        require(uint(start["reads"][-1]["wall_after_usec"]) <= uint(end["reads"][0]["wall_before_usec"]),
                "nonsequential observations")
        require(uint(start["reads"][3]["cycles"]) <= uint(end["reads"][0]["cycles"]), "process counter decreased")
        if same_thread:
            require(start["thread_id"] == end["thread_id"]
                    and uint(start["reads"][2]["cycles"]) <= uint(end["reads"][1]["cycles"]), "thread counter decreased/changed")


def demand(start, end, kind):
    observation(start)
    observation(end)
    lo, hi = (0, 3) if kind == "process" else (1, 2)
    s_lo, s_hi = (uint(start["reads"][i]["cycles"]) for i in (lo, hi))
    e_lo, e_hi = (uint(end["reads"][i]["cycles"]) for i in (lo, hi))
    require(e_lo >= s_lo and e_hi >= s_hi, "decreasing demand endpoints")
    return max(0, e_lo - s_hi), e_hi - s_lo


def verify(report, build):
    require(report["schema"] == SCHEMA and report["passed"] is True and report["qualified"] is False
            and report["target_performance"] == "not_run", "capability failed or qualification overstated")
    require(report["build"] == build and report["identity"] == {k: build[k] for k in
            ("engine_inputs", "godot_commit", "voxel_commit")}, "source/native identity")
    require(build["target_performance"] == "not_run", "target status")
    start, end = uint(report["fixture_start_usec"]), uint(report["fixture_end_usec"])
    require(uint(report["fixture_limit_usec"]) == 5_000_000 and 0 <= end-start <= 5_000_000,
            "fixture exceeded its five-second cap")
    require(report["decimal_controls"] == report["decimal_roundtrip"] == DECIMALS,
            "native/GDScript/JSON decimal roundtrip")
    failed_value(report["failed_process_call"])
    failed_value(report["failed_thread_call"])
    for key, status, unavailable in (("failed_control", "failed", False), ("unavailable_control", "unavailable", True)):
        require(report[key]["status"] == status, "native failure status")
        failed_value(report[key]["reads"][0], unavailable)
    require(report["reversed_control"]["status"] == "contradictory", "native decreasing counter control")
    main, worker = report["main_hash"], report["worker_hash"]
    outer = [report["first"], main["start"], main["end"], report["wait_start"], report["wait_end"],
             report["worker_process_start"], report["worker_process_end"], report["last"]]
    sequence(outer)
    require(start <= uint(outer[0]["reads"][0]["wall_before_usec"])
            and uint(outer[-1]["reads"][-1]["wall_after_usec"]) <= end, "fixture enclosure")
    expected = hashlib.sha256(bytes(i % 251 for i in range(4096)) * 1024).hexdigest()
    hashes = {}
    for label, work in (("main", main), ("worker", worker)):
        require(work["updates"] == work["expected_updates"] == 1024 and work["bytes_per_update"] == 4096
                and work["capped"] is False and work["error"] == 0 and work["digest"] == expected,
                "incomplete or incorrect " + label + " SHA work")
        sequence([work["start"], work["end"]])
        p, t = demand(work["start"], work["end"], "process"), demand(work["start"], work["end"], "thread")
        require(t[0] > 0 and p[1] >= t[0], label + " work has no positive thread/process witness")
        hashes[label] = dict(process_cycles=list(map(str, p)), thread_cycles=list(map(str, t)),
                             updates=1024, bytes=4096*1024, digest=expected)
    require(report["worker_joined"] is True and worker["start"]["thread_id"] != main["start"]["thread_id"],
            "worker not independently witnessed and joined")
    sequence([report["worker_process_start"], worker["start"], worker["end"], report["worker_process_end"]], False)
    process = demand(report["worker_process_start"], report["worker_process_end"], "process")
    witness = demand(worker["start"], worker["end"], "thread")
    # Strong retention check: even the enclosing process lower bound covers the
    # exited worker's upper bound. No noisy tolerance or fabricated zero is used.
    require(process[0] >= witness[1] > 0, "process counter lost exited worker demand")
    require(uint(report["wait_requested_usec"]) == 20_000
            and uint(report["wait_end"]["reads"][0]["wall_before_usec"])
                - uint(report["wait_start"]["reads"][-1]["wall_after_usec"]) >= 20_000,
            "labelled wait incomplete")
    wait = demand(report["wait_start"], report["wait_end"], "process")
    return dict(passed=True, qualified=False, target_performance="not_run", schema=SCHEMA,
                fixture_usec=end-start, hashes=hashes, worker_enclosing_process_cycles=list(map(str, process)),
                worker_thread_cycles=list(map(str, witness)), wait_process_cycles=list(map(str, wait)),
                wait_requested_usec=20_000, decimals_verified=DECIMALS,
                note="Capability/identity only. Wait need not have zero cycles. No sensitivity or cost pass.")


def mutations(report, build):
    cases = {}
    changes = {
        "rounded_uint64": lambda r: r["decimal_roundtrip"].__setitem__(1, "9007199254740992"),
        "numeric_raw_cycle": lambda r: r["first"]["reads"][0].__setitem__("cycles", 2**53+1),
        "counter_failure": lambda r: r["first"]["reads"][0].__setitem__("success", False),
        "unavailable": lambda r: r["first"].__setitem__("status", "unavailable"),
        "wall_reversal": lambda r: r["first"]["reads"][0].__setitem__("wall_before_usec", str(MAX_U64)),
        "wrong_digest": lambda r: r["worker_hash"].__setitem__("digest", "0"*64),
        "incomplete_hash": lambda r: r["main_hash"].__setitem__("updates", 1023),
        "worker_not_joined": lambda r: r.__setitem__("worker_joined", False),
        "failed_output_zero": lambda r: r["failed_process_call"].__setitem__("cycles", "0"),
        "fixture_timeout": lambda r: r.__setitem__("fixture_end_usec", str(uint(r["fixture_start_usec"])+5_000_001)),
        "lost_worker": lambda r: r["worker_hash"]["end"]["reads"][2].__setitem__("cycles", str(MAX_U64)),
        "wrong_build": lambda r: r["identity"].__setitem__("engine_inputs", "0"*64),
    }
    for name, change in changes.items():
        value = copy.deepcopy(report)
        change(value)
        try:
            verify(value, build)
        except (RuntimeError, KeyError, TypeError, ValueError) as error:
            cases[name] = str(error)
        else:
            raise RuntimeError("Accepted saved counter corruption: " + name)
    return cases


def saved_audit(reports, build):
    result = {}
    for label in ("editor", "release"):
        name = "cpu-cycle-capability-" + label
        raw = read_json(reports / (name + ".json"))
        result[label] = verify(raw, build)
        require(result[label] == read_json(reports / (name + "-validation.json")), "saved counter audit differs")
        result[label]["saved_mutations"] = mutations(raw, build)
    return result


def run():
    build = read_json(ROOT / "dist/player/BUILD_INFO.json")
    require(build["engine_inputs"] == build["native_source_key"] == input_hash(), "native source key")
    require(build["game_commit"] == os.environ["GITHUB_SHA"], "game source")
    reports = ROOT / "reports"
    for label, executable in (("editor", ROOT / "build/engine-bundle/editor.exe"), ("release", ROOT / "dist/player/Cairn.exe")):
        name = "cpu-cycle-capability-" + label
        path = reports / (name + ".json")
        require(not path.exists(), "capability smoke already has evidence; no automatic retry")
        args = [executable, "--headless"]
        if label == "editor": args += ["--path", ROOT / "game"]
        output = command(args + ["--", "--cpu-cycle-capability", "--cpu-cycle-output=" + str(path)], name, timeout=60)
        markers = [line.split("CAIRN_CPU_CYCLE_CAPABILITY=", 1)[1] for line in output.splitlines()
                   if "CAIRN_CPU_CYCLE_CAPABILITY=" in line]
        require(len(markers) == 1 and "SCRIPT ERROR:" not in output and "ERROR:" not in output, "engine error or missing result")
        terminal = json.loads(markers[0])
        require(terminal.pop("saved") is True and terminal == read_json(path), "saved/terminal report mismatch")
        write_json(reports / (name + "-validation.json"), verify(terminal, build))
    audit = saved_audit(reports, build)
    write_json(reports / "cpu-cycle-capability-audit.json", audit)
    print("CAIRN_CPU_CYCLE_AUDIT=" + json.dumps(audit, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    require(sys.argv[1:] == ["run"], "expected run")
    run()
