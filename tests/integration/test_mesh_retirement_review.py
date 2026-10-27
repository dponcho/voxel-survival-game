"""Saved review must not turn source, audit or endpoint topology into qualification."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/qa'))
import mesh_retirement_review as review


def resign(data):
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                base64_zlib=base64.b64encode(zlib.compress(data)).decode())


class MeshRetirementReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = review.read(review.PROOF)
        cls.old = review.read(review.PREFIX)

    def test_actual_twenty_cases_and_thirty_four_corruptions_reproduce(self):
        result = review.controls(self.proof)
        self.assertEqual(sum(len(v['cases']) for v in result.values()), 20)
        self.assertEqual(sum(len(v['mutations_rejected']) for v in result.values()), 34)
        # A real observed zero at clock resolution still has an event; refused
        # work has no endpoint. Neither becomes a fabricated lifetime witness.
        report = json.loads(review.embedded(self.proof['controls']['release']['report']))
        empty, refused = report['native']['cases'][1], report['native']['cases'][6]
        self.assertEqual((empty['endpoint_calls'], empty['phase']['deletion']['usec']), (1, 0))
        self.assertEqual(refused['endpoint_calls'], 0)
        self.assertIsNone(refused['endpoint_observed_usec'])

    def test_resigned_liveness_forgery_cannot_inherit_saved_validation(self):
        p = copy.deepcopy(self.proof)
        report = json.loads(review.embedded(p['controls']['release']['report']))
        report['native']['cases'][1]['endpoint_object_alive'] = True
        p['controls']['release']['report'] = resign(json.dumps(report).encode())
        with self.assertRaisesRegex(RuntimeError, 'endpoint destruction'):
            review.controls(p)

    def test_corrected_scope_and_original_rejected_scope_are_distinct(self):
        source = review.lifetime_source(self.proof, self.old)
        self.assertTrue(source['synchronous_lifetime_gap_closed'])
        self.assertEqual(source['corrected_local_scope_depth'], 1)
        self.assertEqual(source['frozen_local_scope_depth'], 0)
        p = copy.deepcopy(self.proof)
        name = 'build/patches/voxel/m1-admission.json'
        patches = json.loads(review.embedded(p['source_files'][name]))
        free = next(v for v in patches if v['path'] == 'terrain/free_mesh_task.h')
        a = '        }\n        cairn::record_deletion(bytes, start, surface);'
        b = '        cairn::record_deletion(bytes, start, surface);\n        }'
        self.assertIn(a, free['replacement'])
        free['replacement'] = free['replacement'].replace(a, b)
        p['source_files'][name] = resign(json.dumps(patches).encode())
        with self.assertRaisesRegex(RuntimeError, 'owner still outlives'):
            review.lifetime_source(p, self.old)

    def test_endpoint_hook_cannot_move_after_the_ending_clock(self):
        p = copy.deepcopy(self.proof)
        name = 'native/sandbox_world/godot/m1_hooks.h'
        text = review.embedded(p['source_files'][name]).decode()
        line = '    if (retirement_control_before_end) retirement_control_before_end(bytes, start, surface);\n'
        text = text.replace(line, '')
        at = text.index('inline void record_deletion(')
        clock = '    const uint64_t elapsed = OS::get_singleton()->get_ticks_usec() - start;\n'
        pos = text.index(clock, at)+len(clock)
        text = text[:pos]+line+text[pos:]
        p['source_files'][name] = resign(text.encode())
        with self.assertRaisesRegex(RuntimeError, 'Witness/ending-clock/charge'):
            review.lifetime_source(p, self.old)

    def test_ci_native_and_consumed_process_verdicts_remain_separate(self):
        review.verify_proof(self.proof)
        changes = [lambda p: p['ci']['run'].__setitem__('conclusion', 'failure'),
                   lambda p: p['native']['qualification']['release'].__setitem__('passed', False),
                   lambda p: p['native'].__setitem__('key', '0'*64),
                   lambda p: p['status'].__setitem__('qualified', True),
                   lambda p: p['consumed_requests']['preparation-demand-once.json'].__setitem__('enabled', True),
                   lambda p: p['permanent_consumed_reservation'].__setitem__('commit', '0'*40)]
        for change in changes:
            p = copy.deepcopy(self.proof); change(p)
            with self.subTest(change=change), self.assertRaises(RuntimeError): review.verify_proof(p)

    def test_frozen_source_identity_does_not_require_future_code_to_keep_this_native_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, item in self.proof['source_files'].items():
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(review.embedded(item))
            review.source_files(self.proof, root)
            path = root/'native/sandbox_world/godot/m1_hooks.h'
            path.write_bytes(path.read_bytes()+b'\n')
            with self.assertRaisesRegex(RuntimeError, 'Reviewed lifetime source changed'):
                review.source_files(self.proof, root)

    def test_rewritten_frozen_proof_fails_before_any_artifact_is_opened(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'changed.json'; path.write_bytes(review.PROOF.read_bytes()+b'\n')
            with self.assertRaisesRegex(RuntimeError, 'Frozen lifetime/prefix proof changed'):
                review.derive(*([Path(td)/'not-opened.zip']*6), evidence=path)

    def test_resigned_artifact_cannot_escape_duplicate_or_supply_a_link(self):
        for kind in ('parent', 'absolute', 'backslash', 'drive', 'duplicate', 'link'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                root = Path(td); path = root/'artifact.zip'
                name = {'parent': '../escape', 'absolute': '/escape', 'backslash': 'raw\\escape',
                        'drive': 'C:/escape'}.get(kind, 'raw/value')
                with zipfile.ZipFile(path, 'w') as z:
                    item = zipfile.ZipInfo(name)
                    if kind == 'link': item.external_attr = (stat.S_IFLNK | 0o777) << 16
                    z.writestr(item, b'original')
                    if kind == 'duplicate':
                        with self.assertWarns(UserWarning): z.writestr(item, b'original')
                meta = dict(size_in_bytes=path.stat().st_size, digest='sha256:'+review.retirement.sha(path))
                with self.assertRaises(RuntimeError): review.extract_artifact(path, meta, root/'output')

    def test_artifact_and_player_require_the_original_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'different.zip'; path.write_bytes(b'PK: different player')
            with self.assertRaisesRegex(RuntimeError, 'Exact portable candidate changed'):
                review.portable(path, self.proof['candidate'], self.proof['build'])
            with self.assertRaisesRegex(RuntimeError, 'Downloaded artifact bytes changed'):
                review.extract_artifact(path, dict(size_in_bytes=path.stat().st_size, digest='sha256:'+'0'*64), Path(td)/'out')

    def test_complete_platform_audits_cannot_disagree_on_one_retained_field(self):
        a = dict(portable_sha256=self.proof['candidate']['portable_sha256'], pck_entries_md5_verified=120,
                 pe_imports_verified=38, self_tests_verified=8, ordinary={'retained_failure_usec': 824},
                 mesh_retirement_controls=self.proof['local_saved_controls'], qualified=False)
        review.compare_audits(a, a, a, self.proof)
        for key, value in (('qualified', True), ('ordinary', {'retained_failure_usec': 750})):
            changed = copy.deepcopy(a); changed[key] = value
            with self.assertRaisesRegex(RuntimeError, 'Complete Windows/Linux/local'):
                review.compare_audits(a, a, changed, self.proof)

    def test_same_thread_gap_topology_is_exact_and_does_not_name_a_cause(self):
        original = review.read(review.prefix.EVIDENCE)
        name = next(n for n in original['embedded_files'] if n.endswith('/preparation-demand-attribution.json'))
        batch = json.loads(review.prefix.embedded(original['embedded_files'][name]))
        boundaries = copy.deepcopy(batch['trials'][1]['cycle_boundaries'])
        stamp = boundaries[0]['after']['reads'][2]
        cycle, wall = int(stamp['cycles']), int(stamp['wall_after_usec'])
        def row(identity, slot, offsets):
            return dict(id=identity, parent=0, lane=1, slot=slot, thread=int(boundaries[0]['before']['thread_id']),
                start_section=0, end_section=0, full_cycles=offsets[-1]-offsets[0],
                reads=[dict(cycles=cycle+x, wall_before_usec=wall+x, wall_after_usec=wall+x,
                            flags=3, error=0) for x in offsets])
        roots = [row(1, 15, (10, 12, 28, 30)), row(2, 1, (40, 42, 48, 50))]
        result = review.gaps(boundaries, roots)
        self.assertEqual(result['predecessor_successor']['15->1']['cycles'], '10')
        self.assertEqual(sum(int(v['cycles']) for v in result['predecessor_successor'].values()),
                         int(result['partition']['gap_cycles']))
        self.assertIsNone(result['causal_owner'])
        roots[0]['thread'] += 1
        with self.assertRaisesRegex(RuntimeError, 'Changed main owner'): review.gaps(boundaries, roots)


if __name__ == '__main__':
    unittest.main()
