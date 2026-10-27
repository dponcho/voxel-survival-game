"""Failed operation, exact archive and same-thread review controls; no engine."""
import copy
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/qa'))
import preparation_failed_prefix_review as review


class FailedPreparationReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = review.read(review.EVIDENCE)
        name = next(n for n in cls.proof['embedded_files'] if n.endswith('/preparation-demand-attribution.json'))
        cls.batch = json.loads(review.embedded(cls.proof['embedded_files'][name]))

    def boundaries_and_roots(self):
        boundaries = copy.deepcopy(self.batch['trials'][1]['cycle_boundaries'])
        stamp = boundaries[0]['after']['reads'][2]
        cycle, wall = int(stamp['cycles']), int(stamp['wall_after_usec'])
        def root(identity, offsets):
            return dict(id=identity, parent=0, lane=1, thread=int(boundaries[0]['before']['thread_id']),
                slot=15, start_section=0, end_section=0, full_cycles=offsets[-1]-offsets[0],
                reads=[dict(cycles=cycle+x, wall_before_usec=wall+x, wall_after_usec=wall+x,
                            flags=3, error=0) for x in offsets])
        return boundaries, [root(1, (10, 12, 28, 30)), root(2, (40, 42, 48, 50))]

    def archive(self, root, files, *, symlink=False, duplicate=False):
        path = root/'artifact.zip'
        with zipfile.ZipFile(path, 'w') as z:
            for name, data in files.items():
                item = zipfile.ZipInfo(name)
                if symlink:
                    item.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(item, data)
                if duplicate:
                    with self.assertWarns(UserWarning): z.writestr(item, data)
        expected = dict(bytes=path.stat().st_size, sha256=review.sha(path),
            files={n: dict(bytes=len(d), sha256=review.digest(d)) for n, d in files.items()})
        return path, expected

    def test_archive_requires_original_bytes_and_complete_member_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            path, expected = self.archive(Path(td), {'raw/evidence.bin': b'original measured bytes'})
            self.assertEqual(review.archive_files(path, expected), {'raw/evidence.bin': b'original measured bytes'})
            wrong = copy.deepcopy(expected); wrong['sha256'] = '0'*64
            with self.assertRaisesRegex(RuntimeError, 'archive bytes/digest'): review.archive_files(path, wrong)
            wrong = copy.deepcopy(expected); wrong['files']['raw/evidence.bin']['sha256'] = '0'*64
            with self.assertRaisesRegex(RuntimeError, 'member differs'): review.archive_files(path, wrong)

    def test_resigned_archive_cannot_escape_duplicate_or_supply_symlinks(self):
        for kind in ('parent', 'absolute', 'backslash', 'drive', 'duplicate', 'symlink'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                name = {'parent': '../escape', 'absolute': '/escape', 'backslash': 'raw\\escape',
                        'drive': 'C:/escape'}.get(kind, 'raw/data')
                path, expected = self.archive(Path(td), {name: b'x'},
                    symlink=kind == 'symlink', duplicate=kind == 'duplicate')
                with self.assertRaises(RuntimeError): review.archive_files(path, expected)

    def test_same_thread_roots_and_gaps_partition_without_process_subtraction(self):
        b, rows = self.boundaries_and_roots()
        result = review.inner_main(b, rows)
        self.assertTrue(result['partition_available'])
        self.assertEqual(result['root_full_cycles'], '30')
        self.assertEqual(int(result['gap_cycles'])+30, int(result['demand_cycles']))
        self.assertEqual(result['roots_by_slot'], {'15': '30'})
        # Exact arithmetic survives large unsigned cumulative counters.
        for boundary in b:
            for observation in (boundary['before'], boundary['after']):
                for stamp in observation['reads'][1:3]: stamp['cycles'] = str(int(stamp['cycles'])+(1 << 63))
        for row in rows:
            for stamp in row['reads']: stamp['cycles'] += 1 << 63
        large = review.inner_main(b, rows)
        self.assertEqual(large['gap_cycles'], result['gap_cycles'])

    def test_crossing_roots_never_become_clipped_demand_or_passing_zero(self):
        b, rows = self.boundaries_and_roots(); row = rows[0]
        for stamp in row['reads']:
            stamp['cycles'] -= 15; stamp['wall_before_usec'] -= 15; stamp['wall_after_usec'] -= 15
        result = review.inner_main(b, [row])
        self.assertFalse(result['partition_available'])
        self.assertEqual(result['crossing_root_ids'], [1])
        self.assertIsNone(result['gap_cycles']); self.assertIsNone(result['root_full_cycles'])

    def test_changed_owners_raw_errors_overlaps_and_forged_totals_reject(self):
        changes = [lambda r: r[0].__setitem__('thread', 99),
                   lambda r: r[0].__setitem__('full_cycles', 99),
                   lambda r: r[0]['reads'][0].__setitem__('flags', 0),
                   lambda r: r.reverse()]
        for change in changes:
            with self.subTest(change=change):
                b, rows = self.boundaries_and_roots(); change(rows)
                with self.assertRaises(RuntimeError): review.inner_main(b, rows)

    def test_failure_retains_exact_kind_payload_and_invalid_trial(self):
        trial = copy.deepcopy(self.batch['trials'][2])
        result = review.failed_event(trial, [])
        self.assertEqual((result['elapsed_usec'], result['associated_payload_bytes'], result['kind']), (819, 112280, 2))
        self.assertEqual(result['excess_usec'], 69)
        self.assertIsNone(result['event_thread_cycle_demand']); self.assertIsNone(result['os_driver_cause'])
        changes = [lambda t: t.__setitem__('valid', True),
                   lambda t: t['phases'][-1]['deletion'].__setitem__('max_usec', 750),
                   lambda t: t['phases'][-1]['deletion'].__setitem__('max_kind', 3),
                   lambda t: t['phases'][-1]['deletion'].__setitem__('max_start_usec', t['end_usec'])]
        for change in changes:
            changed = copy.deepcopy(trial); change(changed)
            with self.assertRaises(RuntimeError): review.failed_event(changed, [])

    def test_pinned_source_finding_refuses_changed_lifetime(self):
        witness = review.read(ROOT/'docs/evidence/m1-preparation-failed-prefix-review-2026-10-26.json')['source_witness']
        self.assertIn('owning local Ref<ArrayMesh>', witness['finding'])
        self.assertIn('not an executed destruction control', witness['scope'])
        frozen = witness['free_mesh_task']
        order = review.retained_release_order(frozen)
        self.assertEqual(order, sorted(order))
        changed = frozen.replace('Ref<ArrayMesh> array = _mesh;', 'ArrayMesh *array = nullptr;')
        with self.assertRaisesRegex(RuntimeError, 'lifetime changed'): review.retained_release_order(changed)

    def test_changed_consumed_proof_and_embedded_record_are_rejected_before_review(self):
        item = copy.deepcopy(self.proof['embedded_files']['process-result.json'])
        item['sha256'] = '0'*64
        with self.assertRaisesRegex(RuntimeError, 'Embedded record differs'): review.embedded(item)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'proof.json'; path.write_bytes(review.EVIDENCE.read_bytes()+b'\n')
            with self.assertRaisesRegex(RuntimeError, 'Frozen consumed-process proof differs'):
                review.derive('not-opened.zip', 'not-opened-player.zip', path)


if __name__ == '__main__':
    unittest.main()
