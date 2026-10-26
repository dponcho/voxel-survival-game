"""One frozen preparation process; permanent reservation, no retry or rebuild."""
import argparse
import copy
import json
import os
from pathlib import Path,PureWindowsPath
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

import preparation_demand as prep
import preparation_prefix_review as review

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/ci'))
from build_support import write_json,extract

REPOSITORY = 'dponcho/voxel-survival-game'
DECLARATION = ROOT/'docs/evidence/m1-preparation-demand-declaration-2026-10-25.json'
DECLARATION_SHA256 = '17cf4e05bfa024aa93c3fcc8b5aebb061db69acf5aca7789e5dfa52d6757daad'
REQUEST = ROOT/'build/preparation-demand-once.json'
REF = 'refs/heads/codex/reserved-preparation-demand-'+DECLARATION_SHA256
REPORTS = ROOT/'reports/preparation-demand-pilot'
PLAYER = ROOT/'build/published-player/Cairn-windows-x86_64.zip'
DESTINATION = ROOT/'build/preparation-demand-player'
SNAPSHOTS = ('tools/qa/preparation_demand_ci.py','tools/qa/preparation_demand_saved_recheck.py',
             'tools/qa/preparation_prefix_review.py',
             '.github/workflows/ci.yml','.github/workflows/preparation-demand.yml','build/preparation-demand-once.json')
require,read,sha = prep.require,prep.read,prep.sha


def plan(request=REQUEST):
    value = read(request)
    require(type(value['enabled']) is bool and value == dict(enabled=value['enabled'],declaration_sha256=DECLARATION_SHA256),
            'Unknown preparation launch request')
    require(sha(DECLARATION) == DECLARATION_SHA256,'Frozen declaration bytes changed')
    return value['enabled']


def context(env=None):
    env = os.environ if env is None else env
    require(env.get('GITHUB_ACTIONS') == 'true' and env.get('GITHUB_REPOSITORY') == REPOSITORY and
            env.get('GITHUB_EVENT_NAME') == 'pull_request' and env.get('GITHUB_RUN_ATTEMPT') == '1',
            'Only the first owned-PR Actions attempt may reserve or launch')
    event = read(Path(env['GITHUB_EVENT_PATH']))
    head = event['pull_request']['head']
    require(event['number'] == 2 and head['repo']['full_name'] == REPOSITORY and
            head['ref'] == 'codex/m1-engine-proof' and re.fullmatch('[0-9a-f]{40}',head['sha']) and
            re.fullmatch('[0-9a-f]{40}',env['GITHUB_SHA']) and re.fullmatch('[1-9][0-9]*',env['GITHUB_RUN_ID']),
            'Preparation launch repository/ref/run differs')
    return dict(repository=REPOSITORY,pr=2,source_commit=head['sha'],workflow_commit=env['GITHUB_SHA'],
                run_id=env['GITHUB_RUN_ID'],run_attempt=1)


def candidate():
    require(sha(DECLARATION) == DECLARATION_SHA256,'Frozen declaration bytes changed')
    proof = read(review.EVIDENCE)
    identity = review.prior.candidate(PLAYER,proof,ROOT)
    review.verify_declaration(read(DECLARATION),identity)
    return identity


def prepare():
    require(plan(),'Preparation request is consumed/disabled')
    ctx = context()
    require(not REPORTS.exists() and not DESTINATION.exists(),'Existing preparation output forbids another launch')
    REPORTS.mkdir(parents=True)
    write_json(REPORTS/'preflight-attempt.json',dict(context=ctx,declaration_sha256=DECLARATION_SHA256,
        engine_processes=0,reservation_created=False))
    try:
        sources = {}
        for name in SNAPSHOTS:
            path = REPORTS/'source'/name;path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,path);sources[name]=sha(path)
        result = review.derive(PLAYER)
        require(result['candidate'] == candidate(),'Preflight candidate changed')
        write_json(REPORTS/'preflight-review.json',result)
        shutil.copy2(DECLARATION,REPORTS/'sequence-declared.json')
        extract(PLAYER,DESTINATION)
        require(sha(DESTINATION/'Cairn.exe') == result['candidate']['exe_sha256'] and
                sha(DESTINATION/'Cairn.pck') == result['candidate']['pck_sha256'],'Extracted candidate changed')
        write_json(REPORTS/'preflight.json',dict(schema='cairn-preparation-launch-preflight-1',context=ctx,
            candidate=result['candidate'],declaration_sha256=DECLARATION_SHA256,source_sha256=sources,
            controls_verified=4,corruptions_rejected=66,engine_processes=0,report_root=str(REPORTS)))
    except Exception as error:
        write_json(REPORTS/'preflight-error.json',dict(error_type=type(error).__name__,message=str(error),
            engine_processes=0,reservation_created=False,declaration_consumed=False))
        raise


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl): return None


def reserve(folder=REPORTS,env=None,opener=None):
    env = os.environ if env is None else env
    ctx = context(env);folder=Path(folder)
    require(read(folder/'preflight.json')['context'] == ctx,'Reservation detached from preflight')
    path=folder/'reservation.json'
    # Reserve the local attempt before any network call; uncertain failures are
    # retained, never retried. The permanent remote ref is the cross-run lock.
    with path.open('x',encoding='utf-8') as f:
        json.dump(dict(schema='cairn-preparation-reservation-1',status='attempting',context=ctx,
            ref=REF,sha=review.SOURCE,declaration_sha256=DECLARATION_SHA256),f)
    token=env.get('CAIRN_RESERVATION_TOKEN','')
    require(bool(token),'Missing scoped reservation token')
    request=urllib.request.Request('https://api.github.com/repos/'+REPOSITORY+'/git/refs',method='POST',
        data=json.dumps(dict(ref=REF,sha=review.SOURCE)).encode(),headers={'Authorization':'Bearer '+token,
        'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'})
    opener=urllib.request.build_opener(NoRedirect) if opener is None else opener
    try:
        with opener.open(request,timeout=60) as response:
            value=json.load(response)
            require(response.status == 201 and value['ref'] == REF and
                    value['object'] == dict(type='commit',sha=review.SOURCE,url=value['object']['url']),
                    'Reservation response differs')
        result=read(path);result.update(status='reserved',http_status=201,response=value)
        write_json(path,result)
    except Exception as error:
        result=read(path);result.update(status='refused_or_uncertain',http_status=getattr(error,'code',None),
            error_type=type(error).__name__,retry_permitted=False)
        write_json(path,result)
        raise


def child_environment():
    env={k:v for k,v in os.environ.items() if 'TOKEN' not in k.upper() and 'SECRET' not in k.upper()}
    user=ROOT/'build/preparation-demand-userdata';user.mkdir(parents=True,exist_ok=True)
    env.update(APPDATA=str(user),LOCALAPPDATA=str(user))
    return env


def execute_once(folder,executable,ctx,spawn=subprocess.Popen,clock=time.monotonic):
    folder=Path(folder)
    command=[str(executable),'--headless','--','--preparation-demand-pilot',
             '--preparation-demand-declaration='+str(folder/'sequence-declared.json'),
             '--m1-report-root='+str(folder/'raw')]
    # Exclusive record is also checked on a repeated invocation in one job.
    with (folder/'launch-record.json').open('x',encoding='utf-8') as f:
        json.dump(dict(context=ctx,command=command,timeout_seconds=1500,automatic_retry=False),f,indent=2)
    begin=clock();pid=None;code=None;timed_out=False;error_type=None
    with (folder/'release-sequence.log').open('w',encoding='utf-8') as log:
        try:
            process=spawn(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env=child_environment())
            pid=process.pid
            while True:
                remaining=1500-(clock()-begin)
                if remaining <= 0:
                    timed_out=True;process.kill();code=process.wait();break
                try: code=process.wait(timeout=min(30,remaining));break
                except subprocess.TimeoutExpired:
                    print('Preparation process: %d seconds; no retry.'%int(clock()-begin),flush=True)
        except OSError as error: error_type=type(error).__name__
    result=dict(pid=pid,returncode=code,timed_out=timed_out,launch_error=error_type,
                elapsed_seconds=clock()-begin,engine_processes=int(pid is not None),spawn_attempts=1)
    write_json(folder/'process-result.json',result)
    return result


def marker(folder,result):
    folder=Path(folder)
    output=(folder/'release-sequence.log').read_text(encoding='utf-8',errors='replace')
    rows=[json.loads(s.split('CAIRN_PREPARATION_ATTRIBUTION=',1)[1]) for s in output.splitlines()
          if 'CAIRN_PREPARATION_ATTRIBUTION=' in s]
    require(not result['timed_out'] and result['launch_error'] is None and len(rows) == 1 and
            'SCRIPT ERROR:' not in output and 'ERROR:' not in output,'Engine error or unfinalized prefix; keep all evidence')
    value=rows[0]
    require(type(value['expected_exit']) is int and value['expected_exit'] in (0,1) and
            result['returncode'] == value['expected_exit'] and value['qualified'] is False and
            value['measurement_valid'] is False and value['outcome'] == 'inconclusive','Unexpected attribution exit/verdict')
    location=Path(value['report_dir']).resolve();raw=(folder/'raw').resolve()
    require(location.is_relative_to(raw) and location.parent == raw,'Runtime report escaped raw root')
    value['relative_raw_folder']=location.name
    p=read(location/'preparation-demand-attribution.json')
    require(value['trials'] == len(p['trials']) and value['abort_reason'] == p['abort_reason'],
            'Runtime marker differs from retained batch')
    return value


def run():
    require(sys.platform == 'win32','Only the declared Windows release process may run')
    ctx=context();before=read(REPORTS/'preflight.json');reservation=read(REPORTS/'reservation.json')
    require(reservation['status'] == 'reserved' and reservation['http_status'] == 201 and
            reservation['context'] == before['context'] == ctx and reservation['ref'] == REF and
            reservation['sha'] == review.SOURCE,'No matching exclusive remote reservation')
    require(candidate() == before['candidate'] and sha(REPORTS/'sequence-declared.json') == DECLARATION_SHA256,
            'Candidate/declaration changed after reservation')
    require(all(sha(ROOT/name) == expected for name,expected in before['source_sha256'].items()),
            'Launcher source changed after preflight')
    require(sha(DESTINATION/'Cairn.exe') == before['candidate']['exe_sha256'] and
            sha(DESTINATION/'Cairn.pck') == before['candidate']['pck_sha256'],'Extracted executable/PCK changed')
    result=execute_once(REPORTS,DESTINATION/'Cairn.exe',ctx)
    write_json(REPORTS/'runtime-result.json',marker(REPORTS,result))


def resign(folder,p):
    """Re-sign synthetic corruptions so semantic readers must reject them."""
    for t in p['trials']:
        if not t['complete']: continue
        path=folder/(t['id']+'-complete.json');body=read(path)
        for key in body:
            if key in t: body[key]=t[key]
        write_json(path,body)
        path=folder/(t['id']+'-boundary.json');body=read(path)
        for key in body:
            if key in t and key != 'cycle': body[key]=t[key]
        body['complete_sha256']=sha(folder/(t['id']+'-complete.json'));write_json(path,body)
    if p['prefix_publications'] and p['prefix_publications'][-1]['passed']:
        path=folder/'sequence-prefix.json'
        write_json(path,dict(schema='cairn-preparation-sequence-prefix-1',trials=[t for t in p['trials'] if t['complete']],no_retry=True))
        p['prefix_publications'][-1]['file'].update(bytes=path.stat().st_size,sha256=sha(path))
    summary=read(folder/'summary.json');summary.update(scenarios=[t['report'] for t in p['trials'] if t['complete']],
        operation_phases=[x for t in p['trials'] for x in t['phases']],shipping_diagnostic_qualification=p['assessment'])
    write_json(folder/'summary.json',summary);write_json(folder/'preparation-demand-attribution.json',p)


def saved_faults(folder,build):
    original=read(folder/'preparation-demand-attribution.json')
    labels=['false-qualification','invented-cost','continued-trial','positive-request','overlapping-publication']
    complete=next((i for i,t in enumerate(original['trials']) if t['complete']),None)
    attributable=next((i for i,t in enumerate(original['trials']) if t['complete'] and
        t['observer'].get('passed') is True and t['preparation_owners'].get('passed') is True),None)
    if attributable is not None: labels+=['unjoined-writer','retained-recorder']
    if complete is not None: labels+=['ignored-operation-guard']
    if original['prefix_publications'] and not original['batch_publication_valid']: labels+=['hidden-publication-failure']
    rejected=[]
    for label in labels:
        with tempfile.TemporaryDirectory(prefix='cairn-preparation-fault-') as td:
            target=Path(td)/'raw';shutil.copytree(folder,target);p=read(target/'preparation-demand-attribution.json')
            if label=='false-qualification':p['qualified']=True
            elif label=='invented-cost':p['assessment']['shipping_cost_estimate']=0
            elif label=='continued-trial':p['trials'].append(copy.deepcopy(p['trials'][-1]))
            elif label=='positive-request':p['trials'][-1]['dose']['requested_tick_cycles']='1'
            elif label=='overlapping-publication':
                if not p['prefix_publications']: continue
                p['prefix_publications'][0]['start_usec']=0
            elif label=='hidden-publication-failure':p['batch_publication_valid']=True
            elif label=='unjoined-writer':p['trials'][attributable]['observer_writers'][0]['worker']['joined']=False
            elif label=='retained-recorder':p['trials'][attributable]['observer_disposal']['disposed']=False
            else:
                t=p['trials'][complete];t['phases'][0]['data_apply']['max_usec']=751
                t['checks']['operations']=t['pre_boundary_checks']['operations']=True
            resign(target,p)
            try: prep.reconcile(target,build,ROOT/'game/diagnostics/preparation_demand_inventory.json')
            except (RuntimeError,KeyError,ValueError,TypeError,IndexError,OSError):rejected.append(label)
            else: raise RuntimeError('Saved preparation corruption accepted: '+label)
    return dict(passed=True,count=len(rejected),rejected=rejected)


def files(folder):
    result={}
    for path in sorted(Path(folder).rglob('*')):
        require(not path.is_symlink(),'Evidence contains a symlink')
        if path.is_file() and path.name != 'independent-audit.json':
            result[path.relative_to(folder).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha(path))
    return result


def audit(folder=REPORTS):
    folder=Path(folder)
    if not (folder/'preflight.json').exists():
        error=read(folder/'preflight-error.json')
        require(error['engine_processes'] == 0 and error['reservation_created'] is False and
            not any((folder/n).exists() for n in ('reservation.json','launch-record.json','process-result.json')),
            'Preflight failure invented a reservation or engine result')
        result=dict(passed=True,qualified=False,target_performance='not_run',engine_executed_by_audit=False,
            engine_processes=0,candidate=None,execution_valid=False,attribution_valid=False,
            sequence=dict(evidence_integrity='preflight_failed',trials=None,attribution_valid=False),
            saved_faults=dict(count=None,rejected=None),preflight_error=error,files=files(folder))
        write_json(folder/'independent-audit.json',result)
        return result
    preflight=read(folder/'preflight.json');identity=candidate()
    require(read(folder/'preflight-review.json') == review.derive(PLAYER),'Saved preflight review changed')
    require(preflight['candidate'] == identity and sha(folder/'sequence-declared.json') == DECLARATION_SHA256,
            'Saved preparation candidate/declaration changed')
    for name,expected in preflight['source_sha256'].items():
        require(sha(folder/'source'/name) == expected,'Saved launch source changed')
    reservation=read(folder/'reservation.json')
    require(reservation['status'] == 'reserved' and reservation['context'] == preflight['context'] and
            reservation['ref'] == REF and reservation['sha'] == review.SOURCE and reservation['http_status'] == 201,
            'Saved exclusive reservation differs')
    process=read(folder/'process-result.json');launch=read(folder/'launch-record.json')
    require(type(process['spawn_attempts']) is int and process['spawn_attempts'] == 1 and
            type(process['engine_processes']) is int and process['engine_processes'] == int(process['pid'] is not None) and
            (process['pid'] is None or type(process['pid']) is int and process['pid'] > 0) and
            launch['context'] == preflight['context'] and launch['timeout_seconds'] == 1500 and
            launch['automatic_retry'] is False,'Saved process count/context/cap differs')
    args=launch['command'];recorded_root=PureWindowsPath(preflight['report_root'])
    require(len(args) == 6 and PureWindowsPath(args[0]).name == 'Cairn.exe' and
            args[1:4] == ['--headless','--','--preparation-demand-pilot'] and
            args[4].startswith('--preparation-demand-declaration=') and args[5].startswith('--m1-report-root=') and
            PureWindowsPath(args[4].split('=',1)[1]) == recorded_root/'sequence-declared.json' and
            PureWindowsPath(args[5].split('=',1)[1]) == recorded_root/'raw','Saved launch command changed scope')
    batches=list((folder/'raw').glob('*/preparation-demand-attribution.json'))
    require(len(batches) <= 1,'Repeated preparation batch')
    sequence=dict(evidence_integrity='retained_unfinalized',attribution_valid=False,measurement_valid=False,
        trials=None,qualified=False,shipping_cost_estimate=None,target_performance='not_run')
    faults=dict(passed=True,count=None,rejected=None,reason='Unfinalized evidence; complete-trial corruptions unavailable')
    if len(batches) == 1 and (batches[0].parent/'summary.json').exists():
        with zipfile.ZipFile(PLAYER) as z: build=json.loads(z.read('BUILD_INFO.json'))
        sequence=prep.reconcile(batches[0].parent,build,ROOT/'game/diagnostics/preparation_demand_inventory.json')
        faults=saved_faults(batches[0].parent,build)
    output=(folder/'release-sequence.log').read_text(encoding='utf-8',errors='replace')
    markers=[json.loads(s.split('CAIRN_PREPARATION_ATTRIBUTION=',1)[1]) for s in output.splitlines()
             if 'CAIRN_PREPARATION_ATTRIBUTION=' in s]
    execution_valid=False
    if (folder/'runtime-result.json').exists():
        saved=read(folder/'runtime-result.json');relative=saved.pop('relative_raw_folder')
        require(len(markers) == 1 and markers[0] == saved and len(batches) == 1 and
                relative == batches[0].parent.name and
                PureWindowsPath(saved['report_dir']) == recorded_root/'raw'/relative,
                'Saved console/result path differs')
        p=read(batches[0])
        require(type(saved['expected_exit']) is int and saved['expected_exit'] in (0,1) and
                saved['expected_exit'] == process['returncode'] and saved['trials'] == len(p['trials']) and
                saved['abort_reason'] == p['abort_reason'] and saved['qualified'] is False and
                saved['measurement_valid'] is False and saved['outcome'] == 'inconclusive',
                'Saved runtime exit/verdict differs')
        execution_valid=(not process['timed_out'] and process['launch_error'] is None and
            'SCRIPT ERROR:' not in output and 'ERROR:' not in output)
    result=dict(passed=True,qualified=False,target_performance='not_run',engine_executed_by_audit=False,
        engine_processes=process['engine_processes'],candidate=identity,reservation=reservation,
        process=process,execution_valid=execution_valid,
        attribution_valid=execution_valid and sequence['attribution_valid'],
        sequence=sequence,saved_faults=faults,files=files(folder))
    write_json(folder/'independent-audit.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['plan','prepare','reserve','run','audit'])
    args=parser.parse_args()
    if args.command=='plan':
        enabled=plan()
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:f.write('launch='+str(enabled).lower()+'\n')
    elif args.command=='prepare':prepare()
    elif args.command=='reserve':reserve()
    elif args.command=='run':run()
    else:
        value=audit();print(json.dumps(dict(passed=True,engine_processes=value['engine_processes'],
            sequence=value['sequence']['evidence_integrity'],qualified=False)))


if __name__=='__main__':main()
