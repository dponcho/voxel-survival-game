"""Exact v2 thresholds, correlated section uncertainty and finite stop controls."""
import copy
from fractions import Fraction
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/qa'))
import shipping_cycles as v2
from test_shipping_diagnostics import fixture as old_fixture


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
