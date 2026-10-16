"""Exact-rational, adversarial checks for the one adopted shipping method."""
import copy
from fractions import Fraction
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/qa'))
from shipping_diagnostics import controls, envelope, evaluate, LIMIT


def fixture(shipping_cost=500000):
    # Five intentionally unequal sections. Matching positions repeat exactly.
    sections = [5000000, 20000000, 25000000, 27000000, 23000000]
    values = []
    for i in range(13):
        dose = i in (6,7)
        cost = 2000160 if dose else (shipping_cost if i in (10,11) else 0)
        parts = sections.copy()
        # The positive control is in the route, not an appended terminal sleep.
        if dose:
            for j in (1,2,3): parts[j] += cost//3
        else:
            parts[4] += cost
        values.append(dict(valid=True, duration_usec=sum(parts), sections_usec=parts, marker_usec=0,
            callback_count=40000 if i % 2 else 70000,
            dose=dict(valid=True, reference_usec=100000000 if dose else 0,
                      requested_tick_usec=463 if dose else 0, actual_usec=cost if dose else 0,
                      ticks=4320 if dose else 0)))
    return values


class ShippingMethodTests(unittest.TestCase):
    def test_runtime_uses_existing_fixed_work_dispatch_and_preserves_native_inputs(self):
        root = Path(__file__).resolve().parents[2]
        runtime = (root/'game/scripts/m1_shipping_runtime.gd').read_text()
        self.assertIn('"AB-H2-pilot-%s-%d"', runtime)
        self.assertIn('"common_qualification_observer": true', runtime)
        self.assertIn('func _scenario_drained()', runtime)
        self.assertNotIn('OS.delay_', runtime)

    def test_sub_limit_complete_effect_passes(self):
        r = evaluate(fixture())
        self.assertEqual(r['outcome'], 'passed')
        self.assertEqual(r['shipping']['upper'], Fraction(1,200))
        self.assertFalse(r['qualified'])

    def test_exact_one_percent_fails(self):
        self.assertEqual(evaluate(fixture(1000000))['outcome'], 'failed')

    def test_above_one_percent_fails(self):
        self.assertEqual(evaluate(fixture(1500000))['outcome'], 'failed')

    def test_just_below_one_percent_passes(self):
        self.assertEqual(evaluate(fixture(999999))['outcome'], 'passed')

    def test_negative_attribution_is_inconclusive(self):
        self.assertEqual(evaluate(fixture(-1))['outcome'], 'inconclusive')

    def test_overlap_is_not_passed(self):
        v = fixture(990000)
        v[10]['marker_usec'] = 20000
        self.assertGreater(evaluate(v)['shipping']['upper'], LIMIT)
        self.assertEqual(evaluate(v)['outcome'], 'inconclusive')

    def test_callback_denominator_cannot_manufacture_effect(self):
        v = fixture()
        original = evaluate(v)
        for i, t in enumerate(v): t['callback_count'] = 2**(i+1)
        self.assertEqual(original, evaluate(v))

    def test_repeatable_varying_sections_are_valid(self):
        v = fixture()
        for t in v:
            t['sections_usec'][0] += 17000000
            t['sections_usec'][2] -= 17000000
        self.assertEqual(evaluate(v)['outcome'], 'passed')

    def test_cancelled_section_drift_is_not_hidden_by_whole_total(self):
        v = fixture()
        v[4]['sections_usec'][1] += 600000
        v[4]['sections_usec'][2] -= 600000
        self.assertEqual(v[4]['duration_usec'], v[1]['duration_usec'])
        self.assertFalse(controls(v)['null_valid'])
        self.assertEqual(evaluate(v)['outcome'], 'inconclusive')

    def test_idle_absorbed_real_positive_is_inconclusive(self):
        v = fixture()
        for i in (6,7):
            v[i]['duration_usec'] = v[5]['duration_usec']
            v[i]['sections_usec'] = v[5]['sections_usec'].copy()
        self.assertFalse(controls(v)['positive_valid'])
        self.assertEqual(evaluate(v)['outcome'], 'inconclusive')

    def test_positive_cost_must_match_recorded_dose(self):
        v = fixture()
        for i in (6,7): v[i]['dose']['actual_usec'] *= 2
        self.assertFalse(controls(v)['valid'])

    def test_positive_control_reference_and_all_ticks_required(self):
        for key, value in [('reference_usec', 99999999), ('ticks', 4319), ('valid', False),
                           ('requested_tick_usec', 462), ('actual_usec', 1)]:
            v = fixture()
            v[6]['dose'][key] = value
            with self.subTest(key=key): self.assertFalse(controls(v)['valid'])

    def test_incomplete_boundary_is_not_treated_as_zero(self):
        v = fixture()
        v[10]['duration_usec'] -= 1
        self.assertIsNone(envelope(v[9:13]))
        self.assertEqual(evaluate(v)['outcome'], 'inconclusive')

    def test_missing_work_or_operation_or_io_is_inconclusive(self):
        for i in range(13):
            v = fixture()
            v[i]['valid'] = False
            with self.subTest(trial=i): self.assertEqual(evaluate(v)['outcome'], 'inconclusive')

    def test_incomplete_quartet_is_not_passed(self):
        self.assertEqual(evaluate(fixture()[:8])['outcome'], 'inconclusive')
        self.assertEqual(evaluate(fixture()[:9])['outcome'], 'not_run')

    def test_large_terminal_uncertainty_blocks_null(self):
        v = fixture()
        for t in v: t['marker_usec'] = 500000
        self.assertFalse(controls(v)['null_valid'])

    def test_unequal_repeat_totals_expand_range(self):
        v = fixture()[9:13]
        v[3]['sections_usec'][4] += 100000
        v[3]['duration_usec'] += 100000
        e = envelope(v)
        self.assertLess(e['lower'], Fraction(1,200))
        self.assertGreater(e['upper'], Fraction(1,200))


if __name__ == '__main__':
    unittest.main()
