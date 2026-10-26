"""Saved controller proof and prospective scope fail closed under re-signing."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/qa'))
import preparation_prefix_review as review


def replace_file(proof,name,data):
    item = proof['files'][name]
    proof['embedded_bytes'] += len(data)-item['bytes']
    item.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                base64_zlib=base64.b64encode(zlib.compress(data)).decode())


class CorrectedLaunchReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = json.loads(review.EVIDENCE.read_text())

    def changed_report(self,change):
        proof = copy.deepcopy(self.proof)
        report = json.loads(review.prior.embedded(proof['files']['release/controls.json']))
        change(report)
        replace_file(proof,'release/controls.json',json.dumps(report).encode())
        return proof

    def test_all_four_current_controls_and_66_saved_corruptions_reproduce(self):
        prefix = review.replay(self.proof)
        owners = review.prior.replay(dict(files=self.proof['owner_files'],controls=self.proof['owner_controls']),
                                    self.proof['candidate']['build'])
        self.assertEqual(prefix['file_count']+owners['file_count'],140)
        self.assertEqual(prefix['bytes']+owners['bytes'],860237)
        self.assertEqual(prefix['semantic_corruptions_rejected']+owners['semantic_corruptions_rejected'],66)
        self.assertEqual([owners['controls'][k]['raw']['record_count'] for k in ('editor','release')],[1380,1583])

    def test_source_witness_is_identical_with_a_windows_default_codepage(self):
        original=Path.read_text
        expected=review.source_witness(self.proof)
        def windows_default(path,encoding=None,errors=None):
            if encoding is None:return path.read_bytes().decode('cp1252')
            return original(path,encoding=encoding,errors=errors)
        with patch.object(Path,'read_text',windows_default):
            self.assertEqual(review.source_witness(self.proof),expected)

    def test_resigned_continuation_cannot_inherit_a_passing_control(self):
        proof = self.changed_report(lambda r:r['cases'][1].__setitem__('setup_calls',1))
        with self.assertRaisesRegex(RuntimeError,'Controller started setup'):
            review.replay(proof)

    def test_resigned_late_io_cannot_rewrite_an_original_trial_flag(self):
        proof = self.changed_report(lambda r:r['cases'][1]['trials'][0].__setitem__('io_failed',True))
        with self.assertRaisesRegex(RuntimeError,'Late batch failure rewrote'):
            review.replay(proof)

    def test_resigned_immutable_file_and_hash_still_must_match_original_trial(self):
        proof = copy.deepcopy(self.proof)
        name = 'AB-H2-preparation-warmup-0-complete.json'
        key = 'release/case-1/'+name
        data = json.loads(review.prior.embedded(proof['files'][key]))
        data['invented_late_observation'] = True
        raw = json.dumps(data).encode()
        replace_file(proof,key,raw)
        report = json.loads(review.prior.embedded(proof['files']['release/controls.json']))
        report['cases'][1]['immutable_files'][name] = hashlib.sha256(raw).hexdigest()
        replace_file(proof,'release/controls.json',json.dumps(report).encode())
        with self.assertRaisesRegex(RuntimeError,'Immutable fixture snapshot differs'):
            review.replay(proof)

    def test_nested_control_paths_cannot_escape_or_invent_an_eighth_case(self):
        for name in ('../controls.json','release/../controls.json','release/case-0/..',
                     'release/case-7/controls.json','release/case-0/C:bad','release/..\\controls.json'):
            proof = copy.deepcopy(self.proof)
            proof['files'][name] = proof['files'].pop('release/process.log')
            with self.subTest(name=name),self.assertRaisesRegex(RuntimeError,'path escaped'):
                review.replay(proof)

    def test_missing_file_is_rejected_even_with_resigned_population_counts(self):
        proof = copy.deepcopy(self.proof)
        item = proof['files'].pop('release/case-1/AB-H2-preparation-warmup-0-complete.json')
        proof['embedded_file_count'] -= 1
        proof['embedded_bytes'] -= item['bytes']
        with self.assertRaises((RuntimeError,OSError)):
            review.replay(proof)

    def test_forged_saved_prefix_qualification_is_rejected(self):
        proof = copy.deepcopy(self.proof)
        proof['controls']['editor']['qualified'] = True
        with self.assertRaisesRegex(RuntimeError,'verdicts or corruptions'):
            review.replay(proof)

    def test_ci_native_qualification_and_consumed_pilot_verdicts_stay_frozen(self):
        changes = [lambda p:p['status'].__setitem__('qualified',True),
            lambda p:p['ci']['jobs'][0].__setitem__('conclusion','failure'),
            lambda p:p['validation'].__setitem__('shipping_observer_pilot',True),
            lambda p:p['native']['qualification']['release'].__setitem__('passed',False),
            lambda p:p['linux_downloaded_replay'].__setitem__('engine_executed',True)]
        review.verify_proof(self.proof)
        for change in changes:
            proof = copy.deepcopy(self.proof);change(proof)
            with self.assertRaises(RuntimeError):review.verify_proof(proof)

    def test_boundary_or_rejected_tail_changes_need_a_new_review_even_if_resigned(self):
        for which in ('boundary','rejected'):
            with self.subTest(which=which),tempfile.TemporaryDirectory() as td:
                root = Path(td)
                names = [review.prior.RUNTIME,review.prior.BASE,'game/scripts/m1_preparation_prefix_before.gd',
                         'docs/evidence/m1-preparation-owner-launch-review-2026-10-25.json']
                for name in names:
                    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,path)
                name = names[0] if which=='boundary' else names[2]
                path=root/name;text=path.read_text()
                if which=='boundary':text=text.replace('trial["marker_usec"] = Time.get_ticks_usec() - marker_begin',
                    'trial["marker_usec"] = Time.get_ticks_usec() - marker_begin + 1')
                else:text=text.replace('report_io_failed = true','report_io_failed = false')
                path.write_text(text)
                proof=copy.deepcopy(self.proof)
                proof['preparation_metadata']['sources_sha256'][Path(name).name]=hashlib.sha256(text.encode()).hexdigest()
                with self.assertRaisesRegex(RuntimeError,'finalizer/boundary changed|Frozen rejected publication'):
                    review.source_witness(proof,root)

    def test_different_candidate_and_proof_cannot_inherit_this_review(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'different.zip';path.write_bytes(b'PK: different candidate')
            with self.assertRaisesRegex(RuntimeError,'ZIP differs'):
                review.prior.candidate(path,self.proof)
            evidence=Path(td)/'changed-proof.json';evidence.write_bytes(review.EVIDENCE.read_bytes()+b' ')
            with self.assertRaisesRegex(RuntimeError,'proof bytes changed'):review.derive(path,evidence)

    def test_declaration_cannot_change_exact_candidate_work_limits_or_retry(self):
        saved=json.loads((ROOT/'docs/evidence/m1-preparation-demand-declaration-2026-10-25.json').read_text())
        identity=saved['candidate']
        review.verify_declaration(saved,identity)
        changes=[lambda d:d.__setitem__('processes',2),lambda d:d.__setitem__('processes',True),
            lambda d:d.__setitem__('automatic_retry',True),lambda d:d.__setitem__('maximum_trials',6),
            lambda d:d['candidate'].__setitem__('pck_sha256','0'*64),
            lambda d:d['fixed_work'].__setitem__('physics_ticks',4319),
            lambda d:d['fixed_work'].__setitem__('terrain_workers',2),
            lambda d:d.__setitem__('positive_shipping_continuation',True),
            lambda d:d['observer_bounds'].__setitem__('trace_bytes',33554433)]
        for change in changes:
            bad=copy.deepcopy(saved);change(bad)
            with self.assertRaisesRegex(RuntimeError,'declaration changed'):review.verify_declaration(bad,identity)


if __name__ == '__main__':unittest.main()
