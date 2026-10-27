"""Saved-review limits: distinguish uncertainty, cancellation and byte integrity."""
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/qa'))
import shipping_cycles_review as review


class NullReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((ROOT/'docs/evidence/m1-shipping-cpu-cycles-cloud-2026-10-18.json').read_text())
        cls.trials = cls.evidence['pilot']['trials']

    def test_actual_range_has_incompatible_zero_and_width_requirements(self):
        result = review.null_components(self.trials[1:5])
        constraints = result['expansion_constraints']
        self.assertFalse(constraints['jointly_feasible'])
        self.assertLess(result['raw_upper'], 0)
        self.assertGreater(constraints['narrowest_zero_containing_width'], Fraction(1, 100))
        self.assertEqual(constraints['zero_containment_requires_at_least'], -result['raw_upper'])
        self.assertGreater(constraints['zero_containment_requires_at_least'],
                           constraints['strict_width_requires_less_than'])

    def test_strict_width_boundary_is_not_rounded_into_feasibility(self):
        exact = review.expansion_constraints(Fraction(-8, 1000), Fraction(-2, 1000))
        self.assertEqual(exact['narrowest_zero_containing_width'], Fraction(1, 100))
        self.assertFalse(exact['jointly_feasible'])
        self.assertTrue(review.expansion_constraints(Fraction(-7, 1000), Fraction(-2, 1000))['jointly_feasible'])
        self.assertTrue(review.expansion_constraints(Fraction(-1, 1000), Fraction(1, 1000))['jointly_feasible'])
        self.assertEqual(review.expansion_constraints(-8, -2, 10)['narrowest_zero_containing_width'], Fraction(10))
        for lower, upper in ((-0.008, -0.002), (False, Fraction(0))):
            with self.assertRaises(RuntimeError): review.expansion_constraints(lower, upper)

    def test_components_exactly_reassemble_original_width(self):
        r = review.null_components(self.trials[1:5])
        self.assertEqual(r['raw_width']+r['matching_section_width']+r['marker_width'], r['expanded_width'])
        actual = self.evidence['pilot']['assessment']['controls']['null']
        expected = Fraction(int(actual['upper']['n']), int(actual['upper']['d']))-Fraction(
            int(actual['lower']['n']), int(actual['lower']['d']))
        self.assertEqual(r['expanded_width'], expected)
        self.assertFalse(r['original_null_usable'])

    def test_complete_cancellation_does_not_erase_section_variation(self):
        r = review.section_pair(self.trials[1], self.trials[4], 44467510906)
        self.assertEqual(r['signed_complete_difference_cycles'], '2134094')
        self.assertEqual(r['absolute_midpoint_difference_sum_cycles'], '460033942')
        self.assertEqual(r['conservative_difference_sum_cycles'], '462975829')
        self.assertEqual(r['boundary_uncertainty_expansion_cycles'], '2941887')
        self.assertEqual(r['cancellation_cycles'], '457899848')
        self.assertGreater(r['fraction'], Fraction(1, 100))

    def test_matching_native_work_is_observed_not_assumed_from_fixed_ticks(self):
        baseline = review.native_work(self.trials[0])
        self.assertTrue(all(review.native_work(t) == baseline for t in self.trials))
        changed = copy.deepcopy(self.trials[1])
        changed['cycle_boundaries'][-1]['snapshot']['meshed'] += 1
        self.assertNotEqual(review.native_work(changed), baseline)
        changed['cycle_boundaries'][-1]['snapshot']['uploads'] = 0
        with self.assertRaises(RuntimeError): review.native_work(changed)

    def test_missing_or_unusable_trial_cannot_supply_null_components(self):
        with self.assertRaises(RuntimeError): review.null_components(self.trials[1:4])
        changed = copy.deepcopy(self.trials[1:5])
        changed[0]['valid'] = False
        with self.assertRaises(RuntimeError): review.null_components(changed)

    def test_manifest_rejects_same_size_tampering_missing_and_extra_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root/'original.json'
            p.write_bytes(b'123')
            manifest = {p.name: dict(bytes=3, sha256=hashlib.sha256(b'123').hexdigest())}
            review.verify_manifest(root, manifest)
            p.write_bytes(b'124')
            with self.assertRaises(RuntimeError): review.verify_manifest(root, manifest)
            p.unlink()
            with self.assertRaises(RuntimeError): review.verify_manifest(root, manifest)
            p.write_bytes(b'123')
            (root/'unexpected.json').write_bytes(b'{}')
            with self.assertRaises(RuntimeError): review.verify_manifest(root, manifest)

    def test_manifest_rejects_escaping_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)/'raw'
            root.mkdir()
            outside = Path(td)/'outside'
            outside.write_bytes(b'123')
            (root/'link').symlink_to(outside)
            manifest = {'link': dict(bytes=3, sha256=hashlib.sha256(b'123').hexdigest())}
            with self.assertRaises(RuntimeError): review.verify_manifest(root, manifest)


if __name__ == '__main__':
    unittest.main()
