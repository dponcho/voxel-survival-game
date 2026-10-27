"""Only two hash-bound public source files can be restored after transfer."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/qa'))
import preparation_demand_ci as launch
import preparation_demand_saved_recheck as replay


class PreparationSavedReplayTests(unittest.TestCase):
    def fixture(self,root):
        recovery=launch.read(replay.RECOVERY)
        launch.write_json(root/'preflight.json',dict(context=dict(source_commit=recovery['source_commit']),
            source_sha256={n:d['sha256'] for n,d in recovery['files'].items()}))
        path=root/'recovery.json';launch.write_json(path,recovery)
        measured=root/'raw/fixture-poses.csv';measured.parent.mkdir();measured.write_bytes(b'synthetic measured bytes\n')
        return path,recovery,measured

    def test_exact_source_restoration_preserves_all_measured_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);path,record,measured=self.fixture(root)
            before=measured.read_bytes();restored=replay.restore_sources(root,path)
            self.assertEqual(len(restored),2)
            for item in restored:self.assertEqual(launch.sha(root/item['path']),item['sha256'])
            self.assertEqual(measured.read_bytes(),before)
            self.assertEqual(replay.restore_sources(root,path),[])

    def test_resigned_wrong_bytes_or_another_source_cannot_be_restored(self):
        for kind in ('bytes','source','digest'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                root=Path(td);path,record,_=self.fixture(root)
                item=record['files']['.github/workflows/ci.yml']
                if kind=='bytes':item['base64']='eA=='
                elif kind=='source':record['source_commit']='0'*40
                else:item['sha256']='0'*64
                launch.write_json(path,record)
                with self.assertRaises(RuntimeError):replay.restore_sources(root,path)

    def test_measured_files_and_escaped_paths_cannot_be_recovered(self):
        for name in ('raw/fixture-poses.csv','../secret','.github/workflows/other.yml'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as td:
                root=Path(td);path,_,_=self.fixture(root)
                p=launch.read(root/'preflight.json');p['source_sha256'][name]='0'*64
                launch.write_json(root/'preflight.json',p)
                with self.assertRaisesRegex(RuntimeError,'Unexpected source snapshot path'):
                    replay.restore_sources(root,path)

    def test_launch_and_saved_replay_modes_are_exclusive_and_artifact_bound(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'request.json'
            for enabled in (True,False):
                launch.write_json(path,dict(enabled=enabled,source_run=40259410841,artifact_id=12623918109))
                self.assertIs(launch.recheck_plan(path),enabled)
            launch.write_json(path,dict(enabled=True,source_run=40259410841,artifact_id=1))
            with self.assertRaises(RuntimeError):launch.recheck_plan(path)
            with patch.object(launch,'plan',return_value=True),patch.object(launch,'recheck_plan',return_value=True),\
                 patch.object(sys,'argv',['launcher','plan']):
                with self.assertRaisesRegex(RuntimeError,'same CI request'):launch.main()


if __name__=='__main__':unittest.main()
