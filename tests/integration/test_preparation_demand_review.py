"""Direct saved thread bounds and same-thread union ownership, without an engine."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/qa'))
import preparation_demand_review as review


class PreparationDemandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        evidence = json.loads(review.EVIDENCE.read_text())
        cls.trials = evidence['pilot']['trials']

    def boundaries(self):
        return copy.deepcopy(self.trials[1]['cycle_boundaries'])

    def records(self, boundaries):
        start = boundaries[0]['after']['reads'][2]
        cycle, wall = int(start['cycles']), int(start['wall_after_usec'])
        thread = int(boundaries[0]['before']['thread_id'])

        def span(identity, parent, offsets):
            return dict(id=identity, parent=parent, thread=thread, lane=1, slot=1,
                        start_section=0, end_section=0, submitted_section=0, complete=1,
                        units=1, bytes=0, reads=[dict(cycles=cycle+o, wall_before_usec=wall+o,
                            wall_after_usec=wall+o, available=True, success=True, error=0) for o in offsets])
        return [span(1, 0, (10, 12, 28, 30)), span(2, 1, (15, 16, 19, 20)),
                span(3, 0, (40, 42, 48, 50))]

    def test_saved_whole_main_preparation_changes_are_direct_observations(self):
        expected = [(2630843343, 2631298233, 2631070788),
                    (2782657997, 2782998056, 2782828026),
                    (2598401260, 2598722871, 2598562066),
                    (2776120144, 2776437075, 2776278610),
                    (2618384974, 2618704502, 2618544738)]
        actual = [review.main_partition(t['cycle_boundaries']) for t in self.trials]
        for row, (lo, hi, midpoint) in zip(actual, expected):
            self.assertEqual(row['sections'][0], [str(lo), str(hi)])
            self.assertEqual(row['section_midpoints'][0], str(midpoint))
            self.assertEqual(sum(map(int, row['section_midpoints'])), int(row['midpoint']))
        self.assertEqual(int(actual[4]['section_midpoints'][0])-int(actual[1]['section_midpoints'][0]), -164283288)
        self.assertEqual(int(actual[3]['section_midpoints'][0])-int(actual[2]['section_midpoints'][0]), 177716544)

    def test_unsigned_cumulative_counters_above_signed_max_keep_exact_demand(self):
        boundaries = self.boundaries()
        before = review.main_partition(boundaries)
        for b in boundaries:
            for o in (b['before'], b['after']):
                for r in o['reads'][1:3]:
                    r['cycles'] = str(int(r['cycles'])+(1 << 63))
        after = review.main_partition(boundaries)
        self.assertEqual(before['sections'], after['sections'])
        self.assertEqual(before['section_midpoints'], after['section_midpoints'])

    def test_bad_raw_boundaries_never_become_zero_demand(self):
        changes = [lambda b: b[1]['before'].__setitem__('thread_id', '99'),
                   lambda b: b[1]['before']['reads'][1].__setitem__('cycles', 5),
                   lambda b: b[1]['before']['reads'][1].__setitem__('cycles', '00'),
                   lambda b: b[1]['before']['reads'][1].__setitem__('cycles', str(1 << 64)),
                   lambda b: b[1]['before']['reads'][1].__setitem__('success', False),
                   lambda b: b[1]['before'].__setitem__('status', 'unavailable'),
                   lambda b: b[1]['before']['reads'][1].__setitem__('wall_before_usec', '0'),
                   lambda b: b[1].__setitem__('label', 'complete-after-report-flush')]
        for change in changes:
            with self.subTest(change=change):
                b = self.boundaries()
                change(b)
                with self.assertRaises(RuntimeError): review.main_partition(b)

    def test_nested_children_are_charged_once_and_gaps_cover_the_inner_window(self):
        b = self.boundaries()
        r = review.inner_partition(b, self.records(b))
        self.assertTrue(r['partition_available'])
        self.assertEqual(r['root_count'], 2)
        self.assertEqual(r['root_full_cycles'], '30')  # Child's five cycles already belong to root 1.
        self.assertEqual(r['gap_count'], 3)
        self.assertEqual(int(r['gap_cycles'])+30, int(r['demand_cycles']))
        self.assertEqual(r['crossing_root_ids'], [])

    def test_prepared_boundary_snapshot_stays_outside_the_safe_inner_window(self):
        b = self.boundaries()
        records = self.records(b)
        outside = copy.deepcopy(records[-1])
        outside.update(id=4, slot=12)
        end = b[1]['before']['reads'][1]
        for offset, stamp in enumerate(outside['reads'], 1):
            stamp.update(cycles=int(end['cycles'])+offset,
                         wall_before_usec=int(end['wall_before_usec'])+offset,
                         wall_after_usec=int(end['wall_before_usec'])+offset)
        records.append(outside)
        r = review.inner_partition(b, records)
        self.assertEqual(r['root_full_cycles'], '30')
        self.assertEqual(r['outside_inner_preparation_roots'][0]['id'], 4)
        self.assertEqual(r['outside_inner_preparation_roots'][0]['slot'], 'boundary_snapshot')

    def test_crossing_span_is_retained_without_clipping_or_fabricated_gaps(self):
        b = self.boundaries()
        records = self.records(b)
        records = [records[0]]
        lo = int(b[0]['after']['reads'][2]['cycles'])
        wall = int(b[0]['after']['reads'][2]['wall_after_usec'])
        for offset, stamp in zip((-5, -4, 4, 5), records[0]['reads']):
            stamp.update(cycles=lo+offset, wall_before_usec=wall+offset, wall_after_usec=wall+offset)
        r = review.inner_partition(b, records)
        self.assertFalse(r['partition_available'])
        self.assertEqual(r['crossing_root_ids'], [1])
        self.assertIsNone(r['gap_cycles'])
        self.assertIsNone(r['root_full_cycles'])

    def test_counter_failure_false_owner_and_overlap_reject_inner_union(self):
        b = self.boundaries()
        changes = [lambda r: r[0]['reads'][0].__setitem__('success', False),
                   lambda r: r[1].__setitem__('thread', 99),
                   lambda r: r[0]['reads'][0].__setitem__('cycles', 0),
                   lambda r: r[2]['reads'][0].__setitem__('wall_before_usec', 0)]
        for change in changes:
            with self.subTest(change=change):
                records = self.records(b)
                change(records)
                with self.assertRaises(RuntimeError): review.inner_partition(b, records)


if __name__ == '__main__':
    unittest.main()
