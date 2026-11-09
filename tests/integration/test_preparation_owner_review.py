"""Saved artifact authenticity and corrupt cleanup witnesses must fail closed."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/qa'))
import preparation_owner_review as review


class OwnerLaunchReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = json.loads(review.EVIDENCE.read_text())

    def changed_report(self, change):
        proof = copy.deepcopy(self.proof)
        item = proof['files']['release/controls.json']
        report = json.loads(review.embedded(item))
        change(report)
        raw = json.dumps(report).encode()
        item.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                    base64_zlib=base64.b64encode(zlib.compress(raw)).decode())
        return proof

    def test_exact_current_and_cancelled_controls_replay_without_reclassification(self):
        current = review.replay(self.proof, self.proof['candidate']['build'])
        previous = self.proof['preceding_cancelled_run']
        cancelled = review.replay(previous, previous['build'])
        self.assertEqual([current['controls'][k]['raw']['record_count'] for k in ('editor','release')], [1680,1182])
        self.assertEqual([cancelled['controls'][k]['raw']['record_count'] for k in ('editor','release')], [1536,2620])
        self.assertEqual(current['semantic_corruptions_rejected']+cancelled['semantic_corruptions_rejected'], 84)
        self.assertEqual(previous['conclusion'], 'cancelled')

    def test_resigned_unjoined_writer_is_rejected_by_semantics(self):
        proof = self.changed_report(lambda r: r['native']['worker'].__setitem__('joined', False))
        with self.assertRaisesRegex(RuntimeError, 'joined/detached writer'):
            review.replay(proof, proof['candidate']['build'])

    def test_resigned_retained_recorder_cannot_be_a_destruction_witness(self):
        proof = self.changed_report(lambda r: r['native']['release'].__setitem__('strong_owners', 2))
        with self.assertRaisesRegex(RuntimeError, 'retained/open'):
            review.replay(proof, proof['candidate']['build'])

    def test_forged_qualification_does_not_change_replayed_verdict(self):
        proof = copy.deepcopy(self.proof)
        proof['controls']['editor']['qualified'] = True
        with self.assertRaisesRegex(RuntimeError, 'verdicts or corruption'):
            review.replay(proof, proof['candidate']['build'])

    def test_embedded_hash_truncation_trailing_data_and_expansion_are_rejected(self):
        original = self.proof['files']['editor/controls.json.bin']
        mutations = [dict(original, sha256='0'*64), dict(original, bytes=original['bytes']-1),
                     dict(original, bytes=True), dict(original, bytes=review.owners.CAP+1),
                     dict(original, base64_zlib=original['base64_zlib'][:-4]),
                     dict(original, base64_zlib=base64.b64encode(base64.b64decode(original['base64_zlib'])+b'junk').decode())]
        for item in mutations:
            with self.subTest(item=item['bytes']), self.assertRaises((RuntimeError,ValueError,zlib.error)):
                review.embedded(item)

    def test_embedded_path_cannot_escape_its_binary_directory(self):
        for name in ('../controls.json', 'editor/../controls.json', 'editor/..', 'release/C:bad', 'release/..\\bad'):
            proof = copy.deepcopy(self.proof)
            proof['files'][name] = proof['files']['editor/controls.json']
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, 'path escaped'):
                review.replay(proof, proof['candidate']['build'])

    def test_a_different_candidate_cannot_inherit_the_saved_controls(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'other.zip'
            path.write_bytes(b'PK: wrong candidate')
            with self.assertRaisesRegex(RuntimeError, 'ZIP differs'):
                review.candidate(path, self.proof)


if __name__ == '__main__':
    unittest.main()
