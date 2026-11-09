"""Post-boundary I/O cannot license another trial or rewrite measured evidence."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/qa'))
import preparation_prefix as prefix
import preparation_demand as owners


def trial(index, valid=True, complete=True):
    group, number = ('warmup',0) if index == 0 else ('bare',index-1)
    stamp = 100*index+10
    return dict(id='AB-H2-preparation-%s-%d'%(group,number),group=group,index=number,
                diagnostic_mode='bare',dose_enabled=False,dose=dict(requested_tick_cycles='0',reference_cycles='0'),
                complete=complete,valid=valid,checks=dict(io=True),io_failed=False,
                start_usec=stamp,end_usec=stamp+1,marker_end_usec=stamp+2)


def retained(path):
    if not path.is_file(): return dict(name=path.name,status='missing',bytes=None,sha256=None)
    return dict(name=path.name,status='retained',bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def fixture(folder, count=1, failure_at=None, failed_trial=False, failure_bytes=None):
    path = Path(folder)/'sequence-prefix.json'
    batch = dict(trials=[],prefix_publications=[],batch_publication_valid=True,abort_reason='')
    for index in range(count):
        t = trial(index,not failed_trial or index != count-1)
        batch['trials'].append(t)
        fail = index == failure_at
        if fail:
            if failure_bytes is not None: path.write_bytes(failure_bytes)
        else:
            path.write_text(json.dumps(dict(schema=prefix.SCHEMA,trials=batch['trials'],no_retry=True)))
        batch['prefix_publications'].append(dict(schema=prefix.SCHEMA,id=t['id'],trial_count=index+1,
            write_succeeded=not fail,write_error=12 if fail else 0,passed=not fail,start_usec=t['marker_end_usec']+1,
            end_usec=t['marker_end_usec']+2,file=retained(path)))
    if failure_at is not None:
        last = batch['trials'][failure_at]
        batch['abort_reason'] = prefix.ABORT if last['valid'] else 'Attribution trial guard failed: '+last['id']
        batch['batch_publication_valid'] = False
    return batch


class PrefixPublicationTests(unittest.TestCase):
    def test_full_success_reconciles_the_real_final_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            b = fixture(td,5)
            self.assertTrue(prefix.publications(td,b)['passed'])
            owners.verify_prefix(b['trials'])

    def test_failed_first_publication_stops_with_unchanged_valid_trial(self):
        with tempfile.TemporaryDirectory() as td:
            b = fixture(td,failure_at=0)
            original = copy.deepcopy(b['trials'])
            result = prefix.publications(td,b)
            self.assertFalse(result['passed'])
            self.assertEqual(result['last_file']['status'],'missing')
            self.assertIsNone(result['last_file']['bytes'])
            with self.assertRaisesRegex(RuntimeError,'Early preparation stop'):
                owners.verify_prefix(b['trials'])
            owners.verify_prefix(b['trials'],publication_failure=not result['passed'])
            self.assertEqual(b['trials'],original)
            self.assertTrue(b['trials'][0]['checks']['io'])

    def test_stale_preceding_prefix_is_retained_but_not_promoted_to_latest_success(self):
        with tempfile.TemporaryDirectory() as td:
            b = fixture(td,3,failure_at=2)
            result = prefix.publications(td,b)
            self.assertFalse(result['passed'])
            self.assertEqual(result['last_file']['status'],'retained')
            self.assertEqual(len(json.loads((Path(td)/'sequence-prefix.json').read_text())['trials']),2)
            self.assertTrue(all(t['valid'] for t in b['trials']))

    def test_real_empty_or_partial_failed_files_are_distinct_from_missing(self):
        for raw in (b'', b'{"schema":'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as td:
                b = fixture(td,failure_at=0,failure_bytes=raw)
                result = prefix.publications(td,b)
                self.assertFalse(result['passed'])
                self.assertEqual(result['last_file']['bytes'],len(raw))
                self.assertEqual(result['last_file']['status'],'retained')

    def test_even_a_partial_later_trial_is_continuation_after_publication_failure(self):
        with tempfile.TemporaryDirectory() as td:
            b = fixture(td,failure_at=0)
            b['trials'].append(trial(1,False,False))
            with self.assertRaisesRegex(RuntimeError,'Continued after prefix'):
                prefix.publications(td,b)

    def test_a_later_successful_attempt_cannot_hide_an_earlier_failure(self):
        with tempfile.TemporaryDirectory() as td:
            b = fixture(td,2,failure_at=0)
            with self.assertRaisesRegex(RuntimeError,'Continued after prefix'):
                prefix.publications(td,b)

    def test_last_trial_failure_keeps_work_valid_but_batch_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            b = fixture(td,5,failure_at=4)
            result = prefix.publications(td,b)
            owners.verify_prefix(b['trials'],publication_failure=not result['passed'])
            self.assertTrue(all(t['valid'] for t in b['trials']))
            self.assertFalse(result['passed'])

    def test_resigned_snapshot_loss_or_retry_is_rejected_by_semantics(self):
        for key,value in [('trials',[]),('no_retry',False)]:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as td:
                b = fixture(td,5); path=Path(td)/'sequence-prefix.json'
                saved=json.loads(path.read_text());saved[key]=value;path.write_text(json.dumps(saved))
                b['prefix_publications'][-1]['file']=retained(path)
                with self.assertRaisesRegex(RuntimeError,'Published prefix changed'):
                    prefix.publications(td,b)

    def test_forged_success_missing_zero_and_raw_verdicts_are_rejected(self):
        changes = [lambda b:b.__setitem__('batch_publication_valid',True),
                   lambda b:b['prefix_publications'][0].__setitem__('write_error',0),
                   lambda b:b['prefix_publications'][0].__setitem__('passed',True),
                   lambda b:b['prefix_publications'][0]['file'].__setitem__('bytes',0),
                   lambda b:b['prefix_publications'][0].__setitem__('trial_count',True),
                   lambda b:b.__setitem__('abort_reason','')]
        for change in changes:
            with tempfile.TemporaryDirectory() as td:
                b=fixture(td,failure_at=0);change(b)
                with self.assertRaises(RuntimeError):prefix.publications(td,b)

    def test_publication_is_outside_the_completed_boundary_and_before_next_setup(self):
        for modification in ('inside','next'):
            with self.subTest(modification=modification), tempfile.TemporaryDirectory() as td:
                b=fixture(td,5)
                if modification=='inside':b['prefix_publications'][0]['start_usec']=b['trials'][0]['end_usec']
                else:b['trials'][1]['start_usec']=0
                with self.assertRaises(RuntimeError):prefix.publications(td,b)
        with tempfile.TemporaryDirectory() as td:
            b=fixture(td,5)
            b['trials'][0]['marker_cycles']=dict(end=dict(reads=[{},{},{},dict(wall_after_usec='999')]))
            with self.assertRaisesRegex(RuntimeError,'terminal counter'):
                prefix.publications(td,b)

    def test_no_complete_trial_has_no_attempt_and_no_invented_file(self):
        with tempfile.TemporaryDirectory() as td:
            b=dict(trials=[trial(0,False,False)],prefix_publications=[],batch_publication_valid=True,abort_reason='abort')
            self.assertEqual(prefix.publications(td,b)['status'],'not_attempted')
            (Path(td)/'sequence-prefix.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError,'without a publication'):
                prefix.publications(td,b)

    def test_first_failed_trial_cause_survives_an_additional_publication_failure(self):
        with tempfile.TemporaryDirectory() as td:
            b=fixture(td,failed_trial=True,failure_at=0)
            self.assertFalse(prefix.publications(td,b)['passed'])
            b['abort_reason']=prefix.ABORT
            with self.assertRaisesRegex(RuntimeError,'first stop reason'):
                prefix.publications(td,b)


if __name__=='__main__':unittest.main()
