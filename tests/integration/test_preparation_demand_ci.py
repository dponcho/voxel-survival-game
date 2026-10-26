"""The declared cloud process cannot be duplicated, enlarged or retried."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/qa'))
import preparation_demand_ci as launch


class Response(io.BytesIO):
    status=201


class API:
    def __init__(self,error=None):self.requests=[];self.error=error
    def open(self,request,timeout):
        self.requests.append(request)
        if self.error:raise self.error
        return Response(json.dumps(dict(ref=launch.REF,object=dict(type='commit',sha=launch.review.SOURCE,
            url='https://api.github.com/repos/'+launch.REPOSITORY+'/git/commits/'+launch.review.SOURCE))).encode())


class Process:
    pid=123
    def __init__(self,*args,**kwargs):self.args=args;self.kwargs=kwargs;self.killed=False;self.timeouts=[]
    def wait(self,timeout=None):self.timeouts.append(timeout);return -9 if self.killed else 0
    def kill(self):self.killed=True


class PreparationLauncherTests(unittest.TestCase):
    def context(self,folder):
        event=folder/'event.json'
        launch.write_json(event,dict(number=2,pull_request=dict(head=dict(repo=dict(full_name=launch.REPOSITORY),
            ref='codex/m1-engine-proof',sha='a'*40))))
        return dict(GITHUB_ACTIONS='true',GITHUB_REPOSITORY=launch.REPOSITORY,GITHUB_EVENT_NAME='pull_request',
            GITHUB_RUN_ATTEMPT='1',GITHUB_RUN_ID='12345',GITHUB_SHA='b'*40,GITHUB_EVENT_PATH=str(event),
            CAIRN_RESERVATION_TOKEN='unit-test-placeholder')

    def preflight(self,folder,env):
        launch.write_json(folder/'preflight.json',dict(context=launch.context(env)))

    def test_plan_accepts_consumption_and_rejects_unknown_declarations(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'request.json'
            for enabled in (True,False):
                launch.write_json(path,dict(enabled=enabled,declaration_sha256=launch.DECLARATION_SHA256))
                self.assertIs(launch.plan(path),enabled)
            for item in (dict(enabled=1,declaration_sha256=launch.DECLARATION_SHA256),
                         dict(enabled=True,declaration_sha256='0'*64)):
                launch.write_json(path,item)
                with self.assertRaises(RuntimeError):launch.plan(path)

    def test_forks_manual_invocations_and_rerun_attempts_cannot_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);env=self.context(root)
            for key,value in [('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','workflow_dispatch'),
                              ('GITHUB_REPOSITORY','another/repository')]:
                bad=dict(env);bad[key]=value
                with self.assertRaises(RuntimeError):launch.context(bad)
            data=launch.read(root/'event.json');data['pull_request']['head']['repo']['full_name']='fork/repo'
            launch.write_json(root/'event.json',data)
            with self.assertRaises(RuntimeError):launch.context(env)

    def test_permanent_claim_is_created_once_and_never_updated(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);env=self.context(root);self.preflight(root,env);api=API()
            launch.reserve(root,env,api)
            self.assertEqual(len(api.requests),1)
            self.assertEqual(api.requests[0].method,'POST')
            self.assertEqual(json.loads(api.requests[0].data),dict(ref=launch.REF,sha=launch.review.SOURCE))
            self.assertEqual(launch.read(root/'reservation.json')['status'],'reserved')
            with self.assertRaises(FileExistsError):launch.reserve(root,env,api)
            self.assertEqual(len(api.requests),1)

    def test_conflict_or_uncertain_network_claim_is_not_retried_or_adopted(self):
        for error in (urllib.error.HTTPError('https://api.github.com',422,'exists',{},None),
                      urllib.error.URLError('uncertain result')):
            with self.subTest(error=type(error).__name__),tempfile.TemporaryDirectory() as td:
                root=Path(td);env=self.context(root);self.preflight(root,env);api=API(error)
                with self.assertRaises(type(error)):launch.reserve(root,env,api)
                saved=launch.read(root/'reservation.json')
                self.assertEqual(saved['status'],'refused_or_uncertain')
                self.assertIs(saved['retry_permitted'],False)
                self.assertNotIn('unit-test-placeholder',(root/'reservation.json').read_text())
                with self.assertRaises(FileExistsError):launch.reserve(root,env,api)
                self.assertEqual(len(api.requests),1)

    def test_one_spawn_has_exact_scope_and_no_credentials(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);calls=[]
            def spawn(*args,**kwargs):
                process=Process(*args,**kwargs);calls.append(process);return process
            with patch.object(launch,'ROOT',root),patch.dict(os.environ,{'ACTIONS_RUNTIME_TOKEN':'private','GH_TOKEN':'private'}):
                value=launch.execute_once(root,root/'Cairn.exe',{},spawn)
                with self.assertRaises(FileExistsError):launch.execute_once(root,root/'Cairn.exe',{},spawn)
            self.assertEqual(len(calls),1);self.assertEqual(value['engine_processes'],1)
            self.assertEqual(calls[0].args[0][1:4],['--headless','--','--preparation-demand-pilot'])
            self.assertEqual(len(calls[0].args[0]),6)
            self.assertTrue(all('TOKEN' not in k and 'SECRET' not in k for k in calls[0].kwargs['env']))
            self.assertLessEqual(calls[0].timeouts[0],30)

    def test_timeout_kills_the_only_process_and_retains_its_result(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);process=Process();times=iter([0,1501,1502])
            with patch.object(launch,'ROOT',root):
                result=launch.execute_once(root,root/'Cairn.exe',{},lambda *a,**k:process,lambda:next(times))
            self.assertTrue(process.killed);self.assertTrue(result['timed_out'])
            self.assertEqual(result['returncode'],-9);self.assertEqual(result['spawn_attempts'],1)
            self.assertEqual(launch.read(root/'process-result.json'),result)

    def test_failed_os_launch_consumes_local_attempt_without_inventing_a_process(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            def failed(*args,**kwargs):raise FileNotFoundError('synthetic launch failure')
            with patch.object(launch,'ROOT',root):result=launch.execute_once(root,root/'Cairn.exe',{},failed)
            self.assertEqual(result['engine_processes'],0);self.assertIsNone(result['returncode'])
            self.assertEqual(result['launch_error'],'FileNotFoundError')
            with self.assertRaises(FileExistsError):launch.execute_once(root,root/'Cairn.exe',{},failed)

    def marker_fixture(self,root):
        folder=root/'raw'/'synthetic-case';folder.mkdir(parents=True)
        launch.write_json(folder/'preparation-demand-attribution.json',dict(trials=[{}],abort_reason='failed guard'))
        value=dict(report_dir=str(folder),trials=1,abort_reason='failed guard',expected_exit=1,
                   measurement_valid=False,qualified=False,outcome='inconclusive')
        return value

    def test_honest_failed_trial_exit_remains_a_failed_measurement(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);value=self.marker_fixture(root)
            (root/'release-sequence.log').write_text('CAIRN_PREPARATION_ATTRIBUTION='+json.dumps(value)+'\n')
            result=launch.marker(root,dict(timed_out=False,launch_error=None,returncode=1))
            self.assertEqual(result['relative_raw_folder'],'synthetic-case')
            self.assertIs(result['qualified'],False)

    def test_console_escape_wrong_exit_duplicate_or_forged_qualification_is_rejected(self):
        for kind in ('escape','exit','duplicate','qualified','engine-error'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                root=Path(td);value=self.marker_fixture(root)
                result=dict(timed_out=False,launch_error=None,returncode=1)
                if kind=='escape':value['report_dir']=str(root.parent)
                elif kind=='exit':result['returncode']=0
                elif kind=='qualified':value['qualified']=True
                log='CAIRN_PREPARATION_ATTRIBUTION='+json.dumps(value)+'\n'
                if kind=='duplicate':log+=log
                elif kind=='engine-error':log+='SCRIPT ERROR: synthetic\n'
                (root/'release-sequence.log').write_text(log)
                with self.assertRaises(RuntimeError):launch.marker(root,result)

    def test_run_refuses_an_unclaimed_or_changed_preflight_before_spawn(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);env=self.context(root);self.preflight(root,env)
            launch.write_json(root/'reservation.json',dict(status='refused_or_uncertain'))
            with patch.object(launch,'REPORTS',root),patch.object(sys,'platform','win32'),patch.dict(os.environ,env),\
                 patch.object(launch,'execute_once') as execute:
                with self.assertRaises(RuntimeError):launch.run()
                execute.assert_not_called()

    def test_windows_only_execution_and_consumed_flags_are_preserved(self):
        with patch.object(sys,'platform','linux'):
            with self.assertRaisesRegex(RuntimeError,'Windows release'):launch.run()
        workflow=(ROOT/'.github/workflows/ci.yml').read_text()
        self.assertIn("needs.plan.outputs.launch != 'true'",workflow)
        self.assertIn('shipping_cycles_pilot: false',workflow)
        self.assertIn('shipping_observer_pilot: false',workflow)
        finite=(ROOT/'.github/workflows/preparation-demand.yml').read_text()
        self.assertNotIn('strategy:',finite)
        self.assertEqual(finite.count('preparation_demand_ci.py run'),1)
        self.assertNotIn('pipeline.py',finite)

    def audit_fixture(self,root):
        identity=dict(portable_sha256='a'*64)
        launch.write_json(root/'preflight.json',dict(context={'run_id':'12345'},candidate=identity,
            source_sha256={},report_root='D:\\CI\\reports\\preparation-demand-pilot'))
        launch.write_json(root/'preflight-review.json',dict(synthetic_fixture=True))
        (root/'sequence-declared.json').write_bytes(launch.DECLARATION.read_bytes())
        launch.write_json(root/'reservation.json',dict(status='reserved',context={'run_id':'12345'},
            ref=launch.REF,sha=launch.review.SOURCE,http_status=201))
        launch.write_json(root/'launch-record.json',dict(context={'run_id':'12345'},timeout_seconds=1500,
            automatic_retry=False,command=['D:\\player\\Cairn.exe','--headless','--','--preparation-demand-pilot',
            '--preparation-demand-declaration=D:\\CI\\reports\\preparation-demand-pilot\\sequence-declared.json',
            '--m1-report-root=D:\\CI\\reports\\preparation-demand-pilot\\raw']))
        launch.write_json(root/'process-result.json',dict(pid=123,returncode=-9,timed_out=True,launch_error=None,
            elapsed_seconds=1500.01,engine_processes=1,spawn_attempts=1))
        (root/'release-sequence.log').write_text('Synthetic unfinalized process fixture\n')
        return identity

    def test_unfinalized_evidence_replays_without_inventing_zero_trials(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);identity=self.audit_fixture(root)
            with patch.object(launch,'candidate',return_value=identity),\
                 patch.object(launch.review,'derive',return_value=dict(synthetic_fixture=True)):
                first=launch.audit(root);second=launch.audit(root)
            self.assertEqual(first,second);self.assertIsNone(first['sequence']['trials'])
            self.assertIsNone(first['saved_faults']['count'])
            self.assertFalse(first['attribution_valid']);self.assertFalse(first['execution_valid'])
            self.assertTrue(first['files']);self.assertFalse(first['engine_executed_by_audit'])

    def test_saved_process_scope_and_count_cannot_be_forged(self):
        for kind in ('extra-option','cap','numeric-process','path-escape'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                root=Path(td);identity=self.audit_fixture(root)
                path=root/('process-result.json' if kind=='numeric-process' else 'launch-record.json')
                value=launch.read(path)
                if kind=='extra-option':value['command'].append('--forensic')
                elif kind=='cap':value['timeout_seconds']=1501
                elif kind=='numeric-process':value['engine_processes']=True
                else:value['command'][5]='--m1-report-root=D:\\elsewhere'
                launch.write_json(path,value)
                with patch.object(launch,'candidate',return_value=identity),\
                     patch.object(launch.review,'derive',return_value=dict(synthetic_fixture=True)):
                    with self.assertRaises(RuntimeError):launch.audit(root)

    def test_preflight_failure_is_preserved_and_never_consumes_the_process(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);reports=root/'reports';source=root/'synthetic.py';source.write_text('# fixture\n')
            with patch.object(launch,'plan',return_value=True),patch.object(launch,'context',return_value={}),\
                 patch.object(launch,'ROOT',root),patch.object(launch,'REPORTS',reports),\
                 patch.object(launch,'DESTINATION',root/'player'),patch.object(launch,'SNAPSHOTS',('synthetic.py',)),\
                 patch.object(launch.review,'derive',side_effect=RuntimeError('Synthetic failed preflight')):
                with self.assertRaisesRegex(RuntimeError,'Synthetic failed'):launch.prepare()
            error=launch.read(reports/'preflight-error.json')
            self.assertEqual(error['engine_processes'],0);self.assertFalse(error['declaration_consumed'])
            result=launch.audit(reports)
            self.assertEqual(result['sequence']['evidence_integrity'],'preflight_failed')
            self.assertIsNone(result['candidate']);self.assertIsNone(result['sequence']['trials'])
            self.assertEqual(result,launch.audit(reports))


if __name__=='__main__':unittest.main()
