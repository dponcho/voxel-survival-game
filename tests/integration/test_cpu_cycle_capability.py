"""Exact-integer/failure readers; synthetic fixtures are never runtime evidence."""
import copy
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/qa"))
from cpu_cycle_capability import uint, observation, demand, verify, mutations, DECIMALS, MAX_U64


def boundary(wall, process, thread, thread_id="1"):
    return dict(schema="cairn-cpu-cycle-observation-1", status="measured", platform="windows",
        process_api="QueryProcessCycleTime", thread_api="QueryThreadCycleTime", thread_id=thread_id,
        reads=[dict(kind=kind, available=True, success=True, error=0, cycles=str(cycles),
                    wall_before_usec=str(wall+2*i), wall_after_usec=str(wall+2*i+1))
               for i, (kind, cycles) in enumerate(zip(("process_lo", "thread_lo", "thread_hi", "process_hi"),
                                                     (process, thread, thread+1, process+1)))])


def fixture():
    build = dict(engine_inputs="a"*64, native_source_key="a"*64, godot_commit="b"*40,
                 voxel_commit="c"*40, game_commit="d"*40, target_performance="not_run")
    failed = dict(available=True, success=False, error=6, cycles=None)
    digest = hashlib.sha256(bytes(i % 251 for i in range(4096))*1024).hexdigest()
    def work(start, end):
        return dict(start=start, end=end, updates=1024, expected_updates=1024, bytes_per_update=4096,
                    capped=False, error=0, digest=digest)
    p = 2**63
    report = dict(schema="cairn-cpu-cycle-capability-1", passed=True, qualified=False, target_performance="not_run",
        build=build, identity={k: build[k] for k in ("engine_inputs", "godot_commit", "voxel_commit")},
        fixture_start_usec="0", fixture_end_usec="20500", fixture_limit_usec="5000000",
        decimal_controls=DECIMALS.copy(), decimal_roundtrip=DECIMALS.copy(),
        failed_process_call=failed.copy(), failed_thread_call=failed.copy(),
        failed_control=dict(status="failed", reads=[failed.copy()]),
        unavailable_control=dict(status="unavailable", reads=[dict(available=False,success=False,error=50,cycles=None)]),
        reversed_control=dict(status="contradictory"), first=boundary(10,p,100),
        main_hash=work(boundary(30,p+100,200),boundary(60,p+1100,1000)),
        wait_start=boundary(100,p+1200,1100), wait_end=boundary(20120,p+1300,1200), wait_requested_usec="20000",
        worker_process_start=boundary(20150,p+1400,1300), worker_process_end=boundary(20300,p+3400,1400),
        worker_joined=True, worker_hash=work(boundary(20170,p+1500,10,"2"),boundary(20250,p+3200,1510,"2")),
        last=boundary(20400,p+3500,1500))
    return report, build


class CpuCycleTests(unittest.TestCase):
    def test_full_unsigned_domain_survives_json_as_strings(self):
        import json
        self.assertEqual([uint(v) for v in json.loads(json.dumps(DECIMALS))], [0,2**53+1,2**63,MAX_U64])
        for bad in (0, True, 1.0, "-1", "+1", "01", "1.0", " 1", "", str(MAX_U64+1)):
            with self.subTest(value=bad), self.assertRaises(RuntimeError): uint(bad)

    def test_conservative_brackets_above_signed_limit(self):
        first = boundary(1, 2**63+10, 100)
        last = boundary(20, 2**63+110, 150)
        self.assertEqual(demand(first,last,"process"), (99,101))
        self.assertEqual(demand(first,last,"thread"), (49,51))
        self.assertEqual(demand(first,first,"process"), (0,1))

    def test_failed_calls_reversals_and_rounding_cannot_be_a_pass(self):
        for key, value in (("available",False),("success",False),("error",6),("cycles",2**53)):
            report = boundary(1,2**63,10)
            report["reads"][0][key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError): observation(report)
        report = boundary(1,100,10)
        report["reads"][3]["cycles"] = "99"
        with self.assertRaises(RuntimeError): observation(report)

    def test_worker_retention_and_saved_mutations(self):
        report,build = fixture()
        result = verify(report,build)
        self.assertTrue(result["passed"])
        self.assertFalse(result["qualified"])
        self.assertEqual(result["worker_enclosing_process_cycles"], ["1999","2001"])
        self.assertEqual(len(mutations(report,build)),12)

    def test_positive_thread_witness_must_fit_post_join_process_lower_bound(self):
        report,build = fixture()
        # Keep all counters ordered/positive, but make the enclosing process
        # demand too small to retain the worker's independent thread witness.
        report["worker_hash"]["end"]["reads"][1]["cycles"] = "3010"
        report["worker_hash"]["end"]["reads"][2]["cycles"] = "3011"
        with self.assertRaises(RuntimeError):
            verify(report,build)

    def test_wait_is_labelled_and_need_not_have_zero_process_cycles(self):
        report,build = fixture()
        self.assertEqual(verify(report,build)["wait_process_cycles"], ["99","101"])
        report["wait_requested_usec"] = "0"
        with self.assertRaises(RuntimeError): verify(report,build)


if __name__ == "__main__": unittest.main()
