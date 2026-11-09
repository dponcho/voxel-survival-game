"""An exact saved review must preserve failed evidence, writer bounds and source order."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/qa'))
import operation_witness_review as review


def resign(data):
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                base64_zlib=base64.b64encode(zlib.compress(data)).decode())


class OperationWitnessReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = review.read(review.PROOF)

    def test_actual_fifty_cases_and_seventy_four_faults_reproduce(self):
        result = review.controls(self.proof)
        self.assertEqual((result['operation_cases'], result['lifetime_cases'], result['semantic_faults_rejected']),
                         (30, 20, 74))
        for value in result['operation'].values():
            self.assertFalse(value['operation_guards_valid'])
            self.assertFalse(value['witness_integrity_valid'])
            self.assertEqual((value['first_failure_id'], value['upload_first_tie_maximum_id'], value['overflow']), (1, 2, 2))
            self.assertIsNone(value['events'][-1]['body_cycles'])

    def test_all_embedded_source_and_raw_file_digests_are_verified(self):
        self.assertEqual(len(review.embedded_manifest(self.proof)), 50)
        p = copy.deepcopy(self.proof)
        p['controls']['release']['files']['controls.json.events']['bytes'] += 1
        with self.assertRaisesRegex(RuntimeError, 'Embedded saved file changed'):
            review.embedded_manifest(p)

    def test_failed_ci_and_false_native_or_target_pass_cannot_inherit_the_proof(self):
        review.verify_proof(self.proof)
        changes = (
            lambda p: p['ci']['run'].__setitem__('conclusion', 'failure'),
            lambda p: p['native']['qualification']['debug'].__setitem__('passed', False),
            lambda p: p['native'].__setitem__('key', '0'*64),
            lambda p: p['build']['engine_binaries'].__setitem__('template_release.exe', '0'*64),
            lambda p: p.__setitem__('source_tree', '0'*40),
            lambda p: p['status'].__setitem__('qualified', True),
            lambda p: p['original_windows_failure'].__setitem__('conclusion', 'success'),
            lambda p: p['consumed_requests']['preparation-demand-once.json'].__setitem__('enabled', True),
            lambda p: p['permanent_consumed_reservation'].__setitem__('commit', '0'*40),
        )
        for change in changes:
            p = copy.deepcopy(self.proof); change(p)
            self.assertNotEqual(p, self.proof)
            with self.subTest(change=change), self.assertRaises(RuntimeError): review.verify_proof(p)

    def test_writer_receipt_thread_close_and_byte_forgeries_are_rejected(self):
        for key, value in (('proof_bytes', 1), ('proof_sha256', '0'*64),
                           ('terminal_receipt_write_included', True)):
            p = copy.deepcopy(self.proof)
            files = p['controls']['release']['files']
            receipt = json.loads(review.embedded(files['controls.json.writer.json']))
            receipt[key] = value
            files['controls.json.writer.json'] = resign(json.dumps(receipt).encode())
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError, 'writer differs'):
                review.controls(p)
        p = copy.deepcopy(self.proof)
        files = p['controls']['release']['files']
        receipt = json.loads(review.embedded(files['controls.json.writer.json']))
        receipt['start']['thread_id'] = '0'
        files['controls.json.writer.json'] = resign(json.dumps(receipt).encode())
        with self.assertRaises(RuntimeError): review.controls(p)

    def test_padding_cannot_escape_total_serialized_process_cap(self):
        p = copy.deepcopy(self.proof)
        files = p['controls']['release']['files']
        receipt = review.embedded(files['controls.json.writer.json'])
        # JSON whitespace is semantically inert and all enclosing digests are
        # valid. Actual file sizes must still enforce the per-process bound.
        files['controls.json.writer.json'] = resign(receipt+b' '*review.witness.OUTPUT_CAP)
        with self.assertRaisesRegex(RuntimeError, 'writer differs'): review.controls(p)

    def test_rewritten_saved_validation_cannot_hide_a_false_guard_pass(self):
        p = copy.deepcopy(self.proof)
        item = p['controls']['release']
        saved = json.loads(review.embedded(item['files']['validation.json']))
        saved['operation_guards_valid'] = True
        item['result'] = saved
        p['local_saved_controls']['release'] = saved
        item['files']['validation.json'] = resign(json.dumps(saved).encode())
        with self.assertRaisesRegex(RuntimeError, 'Saved operation witness controls differ'): review.controls(p)

    def test_last_owner_scope_must_end_before_both_ending_reads(self):
        self.assertEqual(review.source_contract(self.proof)['corrected_local_scope_depth'], 1)
        p = copy.deepcopy(self.proof)
        name = 'build/patches/voxel/m1-admission.json'
        patch = json.loads(review.embedded(p['source_files'][name]))
        free = next(x for x in patch if x['path'] == 'terrain/free_mesh_task.h')
        before = '        }\n        cairn::record_deletion(bytes, start, surface, witness);'
        after = '        cairn::record_deletion(bytes, start, surface, witness);\n        }'
        self.assertIn(before, free['replacement'])
        free['replacement'] = free['replacement'].replace(before, after)
        p['source_files'][name] = resign(json.dumps(patch).encode())
        with self.assertRaisesRegex(RuntimeError, 'Last owner outlives ending reads'): review.source_contract(p)

    def test_counter_reads_cannot_move_beyond_the_operational_wall_end(self):
        p = copy.deepcopy(self.proof)
        name = 'native/sandbox_world/godot/m1_hooks.h'
        text = review.embedded(p['source_files'][name]).decode()
        line = '    if (witness) operation_witness_ending(witness,surface ? 2 : 3,bytes,0);\n'
        self.assertEqual(text.count(line), 1)
        text = text.replace(line, '')
        start = text.index('inline void record_deletion(')
        clock = '    const uint64_t end = OS::get_singleton()->get_ticks_usec();\n'
        pos = text.index(clock, start)+len(clock)
        p['source_files'][name] = resign((text[:pos]+line+text[pos:]).encode())
        with self.assertRaisesRegex(RuntimeError, 'endpoint/charge order changed'): review.source_contract(p)

    def test_close_cost_cannot_move_outside_its_process_end_observation(self):
        p = copy.deepcopy(self.proof)
        name = 'native/sandbox_world/godot/operation_witness.cpp'
        text = review.embedded(p['source_files'][name]).decode()
        text = text.replace('file->close(); file.unref(); closed = true;', 'closed = true;')
        text = text.replace('d["emit_end"] = probe.cpu_cycle_observation();',
                            'd["emit_end"] = probe.cpu_cycle_observation(); file->close(); file.unref();')
        p['source_files'][name] = resign(text.encode())
        with self.assertRaisesRegex(RuntimeError, 'endpoint/charge order changed'): review.source_contract(p)

    def test_frozen_history_preserves_the_failed_prefix(self):
        history = review.verify_history(self.proof)
        self.assertEqual(history['consumed_prefix_failure']['elapsed_usec'], 819)
        self.assertFalse(history['complete_bare_quartet'])

    def test_frozen_source_validation_does_not_pin_future_native_work(self):
        # Bind snapshots in an isolated tree. Full current-source/native-key
        # equality belongs to the review CLI, not every future regression run.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, item in self.proof['source_files'].items():
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(review.embedded(item))
            review.source_files(self.proof, root)
            path = root/'native/sandbox_world/godot/m1_hooks.h'
            path.write_bytes(path.read_bytes()+b'\n')
            with self.assertRaisesRegex(RuntimeError, 'Reviewed operation source changed'):
                review.source_files(self.proof, root)

    def test_changed_proof_fails_before_any_artifact_is_opened(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'changed.json'; path.write_bytes(review.PROOF.read_bytes()+b'\n')
            with mock.patch.object(review.archive, 'extract_artifact') as extract:
                with self.assertRaisesRegex(RuntimeError, 'Frozen operation proof changed'):
                    review.derive(*([Path(td)/'absent.zip']*4), evidence=path)
                extract.assert_not_called()

    def test_complete_audit_comparison_rejects_a_single_changed_failure(self):
        audit = json.loads(review.embedded(self.proof['windows_independent_audit']))
        result = review.compare_audits(audit, audit, audit, self.proof)
        self.assertEqual(result['ordinary']['operation_rows'], 37355)
        bad = copy.deepcopy(audit)
        bad['ordinary']['retained_operation_exceedances'][0]['max_usec'] = 750
        with self.assertRaisesRegex(RuntimeError, 'Complete candidate audits differ'):
            review.compare_audits(audit, audit, bad, self.proof)

    def test_original_broader_reports_cannot_be_resigned_to_erase_an_edit_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, item in self.proof['broader_failure_sources'].items():
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(review.embedded(item))
            result = review.broader_failures(root, self.proof)
            self.assertEqual([v['max_usec'] for v in result['operations']], [803, 763, 893])
            self.assertEqual([v['edit_visibility']['p95_upper_usec'] for v in result['edits']], [166000, 166000])
            # Other failed comparison baselines must be retained separately,
            # rather than filtered out to match the older summary's two rows.
            original = next(root.glob('m1-release-16-1-raw/*/summary.json'))
            baseline = root/'comparison-baseline/summary.json'; baseline.parent.mkdir()
            baseline.write_bytes(original.read_bytes())
            expanded = review.broader_failures(root, self.proof)
            self.assertEqual(len(expanded['comparison_baseline_edits']), 1)
            self.assertEqual(expanded['comparison_baseline_edits'][0]['edit_visibility']['p95_upper_usec'], 166000)
            target = next(root.glob('m1-release-16-1-raw/*/summary.json'))
            data = review.read(target)
            scenario = next(s for s in data['scenarios'] if s['id'] == 'H2')
            scenario['edit_visibility']['p95_upper_usec'] = 100000
            target.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'Broader failures changed'): review.broader_failures(root, self.proof)


if __name__ == '__main__': unittest.main()
