"""Exact v2 thresholds, correlated section uncertainty and finite stop controls."""
import copy
import csv
from fractions import Fraction
import hashlib
import json
import sys
from pathlib import Path
import unittest
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/qa'))
import shipping_cycles as v2
from test_shipping_diagnostics import fixture as old_fixture
from test_cpu_cycle_capability import boundary as raw_counter


def boundaries():
    result = []
    for i, label in enumerate(v2.LABELS):
        before = raw_counter(1000*i, (1<<63)+10000*i, 10000*i)
        after = raw_counter(1000*i+100, (1<<63)+10000*i+2000, 10000*i+2000)
        result.append(dict(label=label,before=before,after=after,wall_usec=1000*i+200,
                           snapshot=dict(generation_jobs=0),bounds=[before['reads'][0]['cycles'],after['reads'][3]['cycles']]))
    return result


def native_work(wall=0, cycles=0, request='1'):
    return dict(schema='cairn-cpu-cycle-dose-1',request_cycles=request,enabled=request!='0',passed=True,reason='measured',
                bytes_per_update=4096,update_cap=512,wall_cap_usec='50000',error=0,capped=False,
                counter_failed=False,hash_failed=False,updates=1 if request!='0' else 0,
                reached=request!='0',digest=hashlib.sha256(b'Z'*4096).hexdigest() if request!='0' else None,
                start=raw_counter(wall+1,(1<<63)+cycles,(1<<63)+cycles),
                end=raw_counter(wall+30,(1<<63)+cycles+300,(1<<63)+cycles+300),
                wall_start_usec=str(wall),wall_end_usec=str(wall+40))


def fixture(cost=500000):
    trials = old_fixture(cost)
    for t in trials:
        sections = list(map(str, t['sections_usec']))
        t['cycle'] = dict(complete=[str(t['duration_usec'])]*2, midpoint=str(t['duration_usec']),
                          sections=[[v, v] for v in sections], section_midpoints=sections, marker=['0', '0'])
        d = t['dose']
        t['dose'] = dict(valid=True, reference_cycles=str(d['reference_usec']),
                         requested_tick_cycles=str(d['requested_tick_usec']), ticks=d['ticks'],
                         cycles=[str(d['actual_usec'])]*2)
    return trials


class CycleMethodTests(unittest.TestCase):
    def test_shared_raw_bounds_preserve_correlated_uncertainty(self):
        p = v2.partition(boundaries())
        self.assertEqual(p['complete'], ['47999','52001'])
        self.assertEqual(p['midpoint'], '50000')
        self.assertEqual(sum(map(int,p['section_midpoints'])), 50000)
        self.assertNotEqual(sum(int(s[0]) for s in p['sections']), int(p['complete'][0]))

    def test_honest_failed_counter_is_retained_without_a_passing_zero(self):
        b = boundaries()
        b[-1]['after']['status'] = 'failed'
        b[-1]['after']['reads'][0].update(success=False,error=6,cycles=None)
        b[-1]['bounds'] = []
        self.assertEqual(v2.retained_partition(b), {})
        b[-1]['after']['reads'][0]['cycles'] = '0'
        with self.assertRaises(RuntimeError): v2.retained_partition(b)

    def test_raw_status_shape_and_unsigned_types_cannot_be_forged(self):
        for field, value in (('cycles', 9007199254740993),('success',1),('error',True)):
            o = raw_counter(0,2**63,2**63)
            o['reads'][0][field] = value
            with self.assertRaises(RuntimeError): v2.raw_observation(o)
        o['status'] = 'failed'
        with self.assertRaises(RuntimeError): v2.raw_observation(o)

    def test_native_work_hash_caps_and_failed_calls(self):
        self.assertEqual(v2.work_record(native_work(),'1',True),(299,301))
        for key,value in (('updates',512),('digest','0'*64),('capped',True),('counter_failed',True),
                          ('hash_failed',True),('error',6),('reached',False),('wall_end_usec','50001')):
            work = native_work()
            work[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError): v2.work_record(work,'1',True)
        self.assertEqual(v2.work_record(native_work(request='0'),'0',False),(299,301))

    def test_native_witness_must_stay_inside_its_original_tick(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            t = dict(id='partial',ticks=2,dose_rows=2,start_usec=0,dose_enabled=False,
                     cycle_boundaries=[],dose=dict(valid=True,ticks=0,cycles=['0','0'],hash_updates=0,requested_tick_cycles='0'))
            with (folder/'partial-poses.csv').open('w') as f:
                f.write('tick,usec\n1,150\n2,250\n')
            work = [native_work(100,0,'0'),native_work(200,1000,'0')]
            for i,w in enumerate(work,1):
                w['tick'] = i
                w['cycles'] = ['299','301']
            def save():
                path = folder/'partial-cycles.jsonl'
                path.write_text(''.join(json.dumps(w)+'\n' for w in work))
                t.update(dose_bytes=path.stat().st_size,dose_sha256=v2.sha(path))
            save()
            self.assertEqual(v2.dose_evidence(folder,t,partial=True)['rows'],2)
            work[0]['wall_end_usec'] = '160'
            save()
            with self.assertRaises(RuntimeError): v2.dose_evidence(folder,t,partial=True)

    def protocol(self):
        values = fixture()
        for t, (group, index, mode, dose) in zip(values, v2.expected_protocol()):
            t.update(group=group,index=index,diagnostic_mode=mode,dose_enabled=dose,complete=True,
                     id='AB-H2-cycles-%s-%d' % (group,index))
        return values

    def test_exact_failed_prefix_is_kept_without_padding_or_retry(self):
        for count in range(1,14):
            t = self.protocol()[:count]
            t[-1]['valid'] = False
            v2.verify_prefix(t, 'Guard failed')
        t = self.protocol()[:2]
        t[0]['valid'] = False
        with self.assertRaises(RuntimeError): v2.verify_prefix(t, 'Guard failed')

    def test_usable_controls_are_required_before_later_groups(self):
        t = self.protocol()
        t[4]['cycle']['sections'][1] = ['30000000']*2
        with self.assertRaises(RuntimeError): v2.verify_prefix(t, 'drift')
        with self.assertRaises(RuntimeError): v2.verify_prefix(self.protocol()[:5], '')
        t = self.protocol()
        t[6]['dose']['cycles'] = ['4000000']*2
        with self.assertRaises(RuntimeError): v2.verify_prefix(t, 'positive invalid')

    def test_strict_shipping_boundaries(self):
        for cost, expected in ((-1,'inconclusive'),(0,'passed'),(999999,'passed'),(1000000,'failed')):
            self.assertEqual(v2.evaluate(fixture(cost))['outcome'], expected)

    def test_cycles_detect_work_absorbed_by_pacing(self):
        t = fixture()
        for trial in t:
            trial['duration_usec'] = 100000000
            trial['sections_usec'] = [5000000,20000000,25000000,27000000,23000000]
        self.assertTrue(v2.controls(t)['valid'])
        self.assertEqual(v2.evaluate(t)['shipping']['point'], Fraction(1,200))

    def test_dose_upper_band_and_each_positive(self):
        t = fixture()
        t[7]['dose']['cycles'][1] = '3000001'
        self.assertFalse(v2.controls(t)['valid'])
        t[7]['dose']['cycles'] = ['1000000','2000160']
        self.assertFalse(v2.controls(t)['valid'])
        # Exactly 3% is allowed when the measured increase overlaps it.
        for i in (6,7):
            t[i]['dose']['cycles'] = ['3000000']*2
            t[i]['cycle']['complete'] = ['103000000']*2
            t[i]['cycle']['midpoint'] = '103000000'
            sections = ['5000000','20000000','25000000','27000000','26000000']
            t[i]['cycle']['sections'] = [[v,v] for v in sections]
            t[i]['cycle']['section_midpoints'] = sections
        self.assertTrue(v2.controls(t)['valid'])

    def test_fixed_request_not_adjusted_after_b1(self):
        t = fixture()
        t[7]['dose']['requested_tick_cycles'] = '464'
        self.assertFalse(v2.controls(t)['valid'])

    def test_each_invalid_trial_prevents_shipping(self):
        for i in range(13):
            t = fixture()
            t[i]['valid'] = False
            self.assertEqual(v2.evaluate(t)['outcome'], 'inconclusive')

    def test_matching_sections_not_net_duration(self):
        t = fixture()
        t[4]['cycle']['sections'][1] = ['20600000']*2
        t[4]['cycle']['sections'][2] = ['24400000']*2
        self.assertFalse(v2.controls(t)['valid'])

    def test_full_interval_drift_not_midpoint_drift(self):
        t = fixture()
        for i in (1,2,3,4):
            t[i]['cycle']['sections'] = [[str(int(v[0])-100000), str(int(v[1])+100000)] for v in t[i]['cycle']['sections']]
        r = v2.envelope(t[1:5])
        self.assertEqual(r['matching_section_drift'], Fraction(1,100))
        self.assertFalse(v2.null_usable(r))

    def test_marker_cost_on_both_arms(self):
        t = fixture(990000)
        t[9]['cycle']['marker'] = ['0','5000']
        t[10]['cycle']['marker'] = ['0','5000']
        self.assertEqual(v2.evaluate(t)['shipping']['upper'], Fraction(1,100))
        self.assertEqual(v2.evaluate(t)['outcome'], 'inconclusive')

    def test_no_callback_denominator(self):
        a, b = fixture(), fixture()
        for i,t in enumerate(b): t['callback_count'] = 1 << (i+32)
        self.assertEqual(v2.evaluate(a), v2.evaluate(b))

    def test_unsigned_midpoint_and_uncertainty(self):
        self.assertEqual(v2.midpoint((v2.MAX_U64-2,v2.MAX_U64)), v2.MAX_U64-1)
        self.assertEqual(v2.difference((2**63,2**63+10),(2**63+5,2**63+15)), (0,15))
        self.assertEqual(v2.difference((2**63,2**63+10),(2**63+20,2**63+25)), (10,25))

    def test_numeric_or_rounded_counters_and_zero_reference(self):
        for value in (9007199254740993, 1.0, '01', '-1'):
            t = fixture()
            t[1]['cycle']['complete'][0] = value
            self.assertFalse(v2.usable(t[1]))
        t = fixture()
        t[1]['cycle']['complete'][0] = '0'
        self.assertFalse(v2.usable(t[1]))

    def test_exact_json_and_cross_product(self):
        a = Fraction(v2.MAX_U64**2, 9007199254740993)
        self.assertEqual(v2.rational_json(v2.exact_json(a)), a)
        with self.assertRaises(RuntimeError): v2.rational_json(dict(n='1',d='0'))

    def test_midpoint_partition_required(self):
        t = fixture()
        t[0]['cycle']['section_midpoints'][0] = '4999999'
        self.assertFalse(v2.usable(t[0]))

    def test_partial_sequence_has_no_cost_estimate(self):
        for n in (0,1,2,4,5,6,8,9,12):
            t = fixture()[:n]
            self.assertEqual(v2.evaluate(t)['outcome'], 'inconclusive')
            self.assertEqual(v2.evaluate(t)['shipping'], {})


if __name__ == '__main__':
    unittest.main()
