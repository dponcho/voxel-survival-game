"""One declared attribution-only release process; audits execute no engine."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/ci'))
from build_support import write_json,run as invoke,extract
from mesh_admission_candidate_audit import pack
from shipping_cycles_ci import candidate_identity as cycle_identity
import shipping_observer as observer
from shipping_observer import require,read,sha

REPORTS=ROOT/'reports/shipping-observer-pilot'
INVENTORY_PATH=ROOT/'game/diagnostics/shipping_observer_inventory.json'


def run_controls(executable,label,game=None):
    name='shipping-observer-controls-'+label;path=ROOT/'reports'/(name+'.json')
    require(not path.exists(),'Observer API controls already have evidence')
    args=[executable,'--headless']+(['--path',game] if game is not None else [])
    output=invoke(args+['--','--shipping-observer-check','--shipping-observer-output='+str(path)],name,timeout=60)
    markers=[line.split('CAIRN_SHIPPING_OBSERVER_CONTROLS=',1)[1] for line in output.splitlines() if 'CAIRN_SHIPPING_OBSERVER_CONTROLS=' in line]
    require(len(markers)==1 and 'SCRIPT ERROR:' not in output and 'ERROR:' not in output
            and json.loads(markers[0])==dict(passed=True,output=str(path)),'Observer API control runner failed')
    result=observer.validate_controls(read(path),path.parent,read(ROOT/'game/build_info.json'))
    write_json(ROOT/'reports'/(name+'-validation.json'),result)
    return result


def saved_controls(reports,build):
    reports=Path(reports);result={}
    for label in ('editor','release'):
        name='shipping-observer-controls-'+label
        result[label]=observer.validate_controls(read(reports/(name+'.json')),reports,build)
        require(result[label]==read(reports/(name+'-validation.json')),'Saved observer API controls differ')
    return result


def candidate_identity():
    result=cycle_identity()
    with zipfile.ZipFile(ROOT/'build/published-player/Cairn-windows-x86_64.zip') as z:
        observer.verify_metadata(result['build'],pack(z.read('Cairn.pck')),ROOT)
    result['observer_method']=observer.VERSION
    result['observer_inventory_sha256']=sha(INVENTORY_PATH)
    return result


def encoded(records,header):
    b=bytearray(observer.HEADER.pack(b'CAIRNOB1',1,observer.SIZE,header['cap_bytes'],len(records),header['failure_code'],header['lane_count']))
    for r in records:
        b.extend(observer.RECORD.pack(*(r[k] for k in ('id','parent','thread','slot','lane','start_section','end_section','submitted_section','complete','units','bytes'))))
        for s in r['reads']:
            b.extend(observer.STAMP.pack(s['cycles'] if s['cycles'] is not None else 0,s['wall_before_usec'],s['wall_after_usec'],
                                        int(s['available'])+2*int(s['success']),s['error']))
    return b


def saved_faults(folder,build):
    labels=('missing-span','duplicate-span','reversed-span','unavailable-zero','false-owner','missing-worker-end',
            'changed-worker-bytes','overflow-header','writer-not-joined','dropped-proxy','numeric-metadata',
            'missing-final-physics','missing-final-frame','missing-edit-ack','ignored-operation-failure',
            'continued-after-stop','positive-request','false-qualification','forged-cost','detached-native-counter')
    rejected=[]
    for label in labels:
        with tempfile.TemporaryDirectory(prefix='cairn-observer-fault-') as td:
            target=Path(td)/'raw';shutil.copytree(folder,target)
            p=read(target/'observer-attribution.json');t=p['trials'][0]
            trace=target/(t['id']+'-observers.bin')
            if label in labels[:8] or label in ('dropped-proxy','detached-native-counter'):
                header,records=observer.decode(trace.read_bytes())
                if label=='missing-span':
                    removed=next(r['id'] for r in records if r['slot']==5)
                    records=[r for r in records if r['id']!=removed]
                    for r in records:
                        if r['id']>removed:r['id']-=1
                        if r['parent']>removed:r['parent']-=1
                elif label=='duplicate-span':
                    r=copy.deepcopy(next(r for r in records if r['slot']==5));r['id']=len(records)+1;records.append(r)
                elif label=='reversed-span':next(r for r in records if r['slot']==5)['reads'][2]['cycles']=0
                elif label=='unavailable-zero':next(r for r in records if r['slot']==5)['reads'][1].update(cycles=None,available=False,success=False,error=50)
                elif label=='false-owner':next(r for r in records if r['slot']==2)['parent']=0
                elif label=='missing-worker-end':next(r for r in records if r['slot']==8)['complete']=0
                elif label=='changed-worker-bytes':next(r for r in records if r['slot']==9)['bytes']+=1
                elif label=='dropped-proxy':next(r for r in records if r['slot']==10)['slot']=9
                elif label=='detached-native-counter':
                    for r in records:
                        if r['lane']==1:
                            for s in r['reads']:
                                if s['cycles'] is not None:s['cycles']+=1<<32
                else:header['cap_bytes']+=1
                trace.write_bytes(encoded(records,header));t['observer_sha256']=sha(trace)
                t['observer'].update(record_count=len(records),trace_bytes=trace.stat().st_size,cap_bytes=header['cap_bytes'])
            elif label=='writer-not-joined':t['observer_writers'][0]['worker']['joined']=False
            elif label=='numeric-metadata':t['observer']['record_count']=float(t['observer']['record_count'])
            elif label in ('missing-final-physics','missing-final-frame','missing-edit-ack'):
                suffix={'missing-final-physics':'-poses.csv','missing-final-frame':'-frames.csv','missing-edit-ack':'-frames.csv.edits.jsonl'}[label]
                path=target/(t['id']+suffix);lines=path.read_text(encoding='utf-8-sig').splitlines();path.write_text('\n'.join(lines[:-1])+'\n')
                if label=='missing-final-physics':t['pose_sha256']=sha(path)
            elif label=='ignored-operation-failure':
                t['phases'][0]['data_apply']['max_usec']=751;t['checks']['operations']=True;t['pre_boundary_checks']['operations']=True;t['valid']=True
            elif label=='continued-after-stop':p['trials'].append(copy.deepcopy(t))
            elif label=='positive-request':t['dose']['requested_tick_cycles']='1'
            elif label=='false-qualification':p['qualified']=True
            else:p['assessment']['shipping_cost_estimate']=0
            cp=target/(t['id']+'-complete.json');body=read(cp)
            for key in body:
                if key in t:body[key]=t[key]
            write_json(cp,body)
            bp=target/(t['id']+'-boundary.json');terminal=read(bp)
            for key in terminal:
                if key in t and key!='cycle':terminal[key]=t[key]
            terminal['complete_sha256']=sha(cp);write_json(bp,terminal)
            summary=read(target/'summary.json');summary['scenarios']=[x['report'] for x in p['trials'] if x['complete']]
            summary['operation_phases']=[phase for x in p['trials'] for phase in x['phases']]
            summary['shipping_diagnostic_qualification']=p['assessment'];write_json(target/'summary.json',summary)
            write_json(target/'observer-attribution.json',p)
            try:observer.reconcile(target,build,INVENTORY_PATH)
            except (RuntimeError,KeyError,ValueError,TypeError,IndexError):rejected.append(label)
            else:raise RuntimeError('Saved observer corruption accepted: '+label)
    return dict(passed=True,count=len(rejected),rejected=rejected)


def declaration(build):
    return dict(method=observer.VERSION,build=build,inventory_sha256=sha(INVENTORY_PATH),render_block=32,workers=1,
                physics_ticks=4320,ordered_maximum=[list(x) for x in observer.expected_protocol()],maximum_trials=5,
                trace_cap_bytes=observer.CAP,process_timeout_seconds=1500,automatic_retry=False,
                positive_request_created=False,shipping_continuation=False,
                rule='Stop at first failed guard and always by five. Perturbing attribution only; no cost estimate or target action.')


def audit():
    identity=candidate_identity();require(identity==read(REPORTS/'candidate-identity.json'),'Observer candidate changed')
    build=identity['build'];controls=saved_controls(ROOT/'build/downloaded-export-evidence/reports',build)
    files=list((REPORTS/'raw').glob('*/observer-attribution.json'));require(len(files)==1,'Observer missing or repeated sequence')
    require(read(REPORTS/'sequence-declared.json')==declaration(build),'Observer prospective declaration changed')
    result=observer.reconcile(files[0].parent,build,INVENTORY_PATH)
    trials=read(files[0])['trials']
    faults=saved_faults(files[0].parent,build) if all(t['complete'] for t in trials) else dict(passed=True,count=0,rejected=[],reason='Partial prefix retained; complete-trial corruption controls unavailable')
    value=dict(passed=True,qualified=False,target_performance='not_run',candidate=identity,controls=controls,
               sequence=result,saved_faults=faults,engine_runs=1,maximum_trials=5)
    write_json(REPORTS/'independent-audit.json',value);return value


def run():
    require(not REPORTS.exists(),'Observer sequence already declared; no retry')
    REPORTS.mkdir(parents=True);identity=candidate_identity()
    saved_controls(ROOT/'build/downloaded-export-evidence/reports',identity['build'])
    write_json(REPORTS/'candidate-identity.json',identity);write_json(REPORTS/'sequence-declared.json',declaration(identity['build']))
    destination=ROOT/'build/shipping-observer-player';extract(ROOT/'build/published-player/Cairn-windows-x86_64.zip',destination)
    with (REPORTS/'release-sequence.log').open('w',encoding='utf-8') as log:
        finished=subprocess.run([str(destination/'Cairn.exe'),'--headless','--','--shipping-observer-pilot','--m1-report-root='+str(REPORTS/'raw')],
                                cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=1500)
    output=(REPORTS/'release-sequence.log').read_text(encoding='utf-8',errors='replace')
    markers=[line.split('CAIRN_SHIPPING_OBSERVER=',1)[1] for line in output.splitlines() if 'CAIRN_SHIPPING_OBSERVER=' in line]
    require(len(markers)==1 and 'SCRIPT ERROR:' not in output and 'ERROR:' not in output,'Observer engine error/missing result; keep partial evidence')
    marker=json.loads(markers[0]);require(type(marker['expected_exit']) is int and marker['expected_exit'] in (0,1)
        and finished.returncode==marker['expected_exit'] and marker['measurement_valid'] is False
        and marker['qualified'] is False and marker['outcome']=='inconclusive','Observer unexpected exit/qualification')
    folder=Path(marker['report_dir']).resolve();require(folder.is_relative_to((REPORTS/'raw').resolve()),'Observer report escaped destination')
    p=read(folder/'observer-attribution.json')
    require(marker['trials']==len(p['trials']) and marker['abort_reason']==p['abort_reason'],'Observer console/saved prefix differs')
    write_json(REPORTS/'runtime-result.json',marker)
    result=audit();print(json.dumps(dict(attribution_valid=result['sequence']['attribution_valid'],trials=result['sequence']['trials'],qualified=False)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--audit-only',action='store_true');args=parser.parse_args()
    audit() if args.audit_only else run()
