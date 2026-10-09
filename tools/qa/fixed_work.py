"""Independent rational fixed-work oracle; raw rows use the established precision reader.

No target data or engine execution. Duration, counts and endpoint spans are separate;
combined final reporting is an external record and is never allocated to repeats.
"""
import copy
from fractions import Fraction
import json
import math
from pathlib import Path

from endpoint_precision import model, reconcile_phase, MAX_RAW
from route_calibration import ORDER, LIMIT, compare, variation, require, assess as legacy_assess, reconcile_decision, scope as legacy_scope

VERSION = 'm1-fixed-work-elapsed-1'
LABELS = ('null','below','at','above','threshold-overlap','endpoint','ack-duration','count-mask','count-drift',
          'incomplete','missing','reordered','stall','failed-workload','failed-operation','unavailable','io-failed',
          'dose-overlap','window-drift','route-drift','phase-invalid','missing-window')
MAX_REPORT = 3 * 1024 * 1024
MAX_FILES = len(LABELS) * 8
NULL_KEYS = ('elapsed_usec','callbacks','time_per_callback_usec','terminal_interval_usec','terminal_callbacks',
             'ack_marker_usec','setup_and_callback_tail_usec','main_interval_usec','finalization_usec',
             'writer_drain_usec','dose_usec','callback_usec','shared_usec','switched_usec')


def number(data, key):
    value = data.get(key)
    require(type(value) in (int,float) and math.isfinite(value) and int(value)==value and abs(value)<=9e12,
            'unavailable/noninteger clock')
    return int(value)


def observation(p):
    try:
        a, l, b = p.get('diagnostic_accounting',{}), p.get('route_calibration',{}), p.get('fixed_work_boundaries',{})
        d, n = number(a,'elapsed_usec'), number(a,'callbacks')
        start, end, last = (number(a,k) for k in ('start_usec','end_usec','last_callback_end_usec'))
        measured = number(p,'measurement_end_usec')
        native, db, de = (number(b,k) for k in ('native_phase_closed_usec','writer_drain_begin_usec','writer_drain_end_usec'))
        require(0<d<=600000000 and 0<n<=2000000 and number(p,'samples')==n and end-start==d
                and 0<=start<=last<=measured<=native<=db<=de<=end, 'invalid wall/phase sequence')
        require(a.get('overflow') is False and a.get('invalid_partition') is False and l.get('invalid') is False
                and l.get('version')=='m1-route-calibration-1', 'invalid ledger')
        require(number(a,'finalization_usec')==end-last and number(a,'writer_drain_usec')==de-db
                and 0<=number(a,'last_callback_usec')<=number(a,'callback_usec')==number(a,'shared_usec')
                and number(a,'switched_usec')==number(a,'switched_calls')==0, 'invalid nested accounting')
        bins=l.get('bins',[])
        require(len(bins)==7 and all(number(x,'samples')>0 and number(x,'usec')>0
                    and number(x,'samples')==number(x,'callbacks') and number(x,'callback_usec')>=0
                    and x.get('status')=='measured' for x in bins), 'missing terminal/sections')
        intervals=sum(number(x,'usec') for x in bins)
        require(sum(number(x,'samples') for x in bins)==n and sum(number(x,'callback_usec') for x in bins)==number(a,'callback_usec')
                and abs(intervals-p.get('wall_seconds',-1)*1e6)<=.01 and intervals<=last-start, 'lost rows/costs')
        dose=l.get('closure_dose',{})
        request, duration=number(dose,'requested_usec'),number(dose,'elapsed_usec')
        require(request>=0 and duration>=0, 'missing dose')
        if request:
            ds,dt=number(dose,'start_usec'),number(dose,'end_usec')
            require(de<=ds<=dt<=end and dt-ds==duration>=request, 'overlapping dose')
        else:
            require(dose.get('start_usec') is None and dose.get('end_usec') is None and duration==0, 'null ran dose')
        ack=p.get('edit_acknowledgement',{})
        ab,ae=number(ack,'start_usec'),number(ack,'end_usec')
        require(ab>=0 and ae==measured and (ab==0 or start<=ab<=measured), 'ack scope unavailable')
        return dict(status='measured',elapsed_usec=d,callbacks=n,time_per_callback_usec=float(Fraction(d,n)),
                    terminal_interval_usec=number(bins[6],'usec'),terminal_callbacks=number(bins[6],'samples'),
                    ack_marker_usec=ae-ab if ab else 0,setup_and_callback_tail_usec=last-start-intervals,
                    main_interval_usec=intervals-number(bins[6],'usec'),finalization_usec=end-last,
                    writer_drain_usec=de-db,dose_usec=duration,callback_usec=number(a,'callback_usec'),
                    shared_usec=number(a,'shared_usec'),switched_usec=0)
    except (ValueError,TypeError,KeyError):
        return dict(status='unavailable',**dict.fromkeys(NULL_KEYS))


def workload_valid(phases, workload, short):
    c=phases[0].get('workload_contract',{})
    actors=24 if workload=='H2' else 12
    ticks=60 if short else 1800
    expected=dict(workload=workload,fixture=1,actors=actors,edit_rate=4 if workload=='H2' else 0,
                  rain_instances=256 if workload=='H2' else 0,physics_hz=60,max_physics_steps=4,
                  resolution=[1280,720],render_scale=1,visual_radius=96,data_radius=128,triangle_colliders=False)
    policy=dict(frame_usec=2000,frame_upload_bytes=1048576,single_upload_bytes=262144,
                terrain_jobs=64,mesh_results=16,mesh_result_bytes=33554432)
    if not all(c.get(k)==v for k,v in expected.items()) or c.get('native_policy')!=policy or c.get('workers') not in (1,2) or c.get('render_block') not in (16,32): return False
    for i,p in enumerate(phases):
        f=p.get('fog_frontier',{})
        a=p.get('diagnostic_accounting',{})
        e=p.get('workload_evidence',{})
        if not (p.get('id')==f'CAL-{workload}-{ORDER[i]}' and p.get('workload')==workload and p.get('workload_contract')==c
                and p.get('completed') is True and p.get('evaluation')!='failed' and p.get('readiness_stops')==0
                and p.get('simulation_ticks')==ticks and p.get('actor_ticks')==actors*ticks
                and p.get('accepted_proxy_edits')==(ticks//15 if workload=='H2' else 0)
                and p.get('proxy_autosaves')==(ticks//60 if workload=='H2' else 0) and p.get('rejected_proxy_edits')==0
                and p.get('operation_phase',{}).get('tracing') is True
                and (workload!='H2' or (c.get('edit_trace') is True and p.get('edit_visibility',{}).get('accepted')==p.get('accepted_proxy_edits')))
                and p.get('frontier_enabled') is False and a.get('switched_calls')==a.get('switched_usec')==0
                and f.get('status')=='unavailable' and f.get('evaluation')=='inconclusive'
                and f.get('minimum_frontier_distance_m') is None and f.get('exposed_samples') is None
                and e and all(e.get(k)==phases[0].get('workload_evidence',{}).get(k) for k in ('command_hash','route_checkpoints'))
                and p.get('travelled_distance_m',-1)>=6.5*ticks/60-1
                and p.get('simulated_seconds',0)>=30 and abs(p.get('wall_seconds',0)-p.get('simulated_seconds',0))<=.25): return False
    return True


def assess(phases, workload, short=False, io_failed=False, declared=600000):
    out=dict(status='not_run' if not phases else 'inconclusive',qualified=False,
             duration_effect=dict(classification='unavailable',added_fraction=None),observations=[],
             same_mode_pairs=[],count_duration_decomposition=[])
    if len(phases)!=4: return out
    obs=[observation(p) for p in phases];out['observations']=obs
    if any(o['status']!='measured' for o in obs): return out
    d=[o['elapsed_usec'] for o in obs]
    effect=compare((d[0],d[3]),(d[1],d[2]));out['duration_effect']=effect
    valid=workload_valid(phases,workload,short) and not short and not io_failed and declared>=0
    valid &= all(p['route_calibration']['closure_dose']['requested_usec']==(declared if i in (1,2) else 0) for i,p in enumerate(phases))
    for left,right in ((0,3),(1,2)):
        x,y=obs[left],obs[right]
        denominator=Fraction(d[left]+d[right],2)
        td=y['terminal_interval_usec']-x['terminal_interval_usec'];ad=y['ack_marker_usec']-x['ack_marker_usec']
        uncertainty=max(abs(td),abs(ad)) # overlapping descriptions, never added
        main=[variation((int(phases[left]['route_calibration']['bins'][j]['usec']),int(phases[right]['route_calibration']['bins'][j]['usec']))) for j in range(6)]
        whole=variation((d[left],d[right]));endpoint=Fraction(uncertainty)/denominator
        out['same_mode_pairs'].append(dict(complete_duration_variation=float(whole),main_duration_variation=list(map(float,main)),
            terminal_interval_delta_usec=td,ack_marker_delta_usec=ad,endpoint_uncertainty_usec=uncertainty,
            endpoint_uncertainty_fraction=float(endpoint),callback_count_delta=y['callbacks']-x['callbacks']))
        valid &= max(whole,endpoint,*main)<LIMIT
    for ref,pos in ((0,1),(3,2)):
        duration=Fraction(d[pos],d[ref]);count=Fraction(obs[pos]['callbacks'],obs[ref]['callbacks'])
        out['count_duration_decomposition'].append(dict(duration_added_fraction=float(duration-1),callback_count_added_fraction=float(count-1),
                                                      time_per_callback_added_fraction=float(duration/count-1)))
    lower=Fraction(min(d[1:3]),max(d[0],d[3]))-1
    valid &= effect['classification']!='inconclusive' and (declared==0 or lower>0)
    if valid: out['status']='null_observed' if declared==0 else 'sensitivity_observed'
    return out


def scope(root):
    require(root['version']==VERSION and root['experimental'] is True and root['qualified'] is False
            and root['legacy_authoritative'] is True and root['threshold']==.01 and root['hardware_noise_calibrated'] is False
            and root['per_frame_probe_cost'] is None and root['shared_causal_overhead'] is None
            and root['combined_report_finalization']==dict(status='external_record',file='report-finalization.json',allocated_to_trials=False),
            'experimental estimate promoted to qualification or allocated report cost')


def equal(actual,expected):
    if isinstance(expected,dict):
        require(set(actual)>=set(expected),'saved result fields missing')
        for k,v in expected.items(): equal(actual[k],v)
    elif isinstance(expected,list):
        require(len(actual)==len(expected),'lost saved pairs/observations')
        for a,e in zip(actual,expected): equal(a,e)
    elif isinstance(expected,float):
        require(type(actual) in (int,float) and math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12),'saved rational result differs')
    else: require(type(actual)==type(expected) and actual==expected,'saved classification/null/integer differs')


def dose_for(label,index):
    declared={'null':0,'below':150106,'at':300213,'threshold-overlap':299000}.get(label,600000)
    return declared,(301000 if label=='threshold-overlap' and index==2 else declared) if index in (1,2) else 0


def reconcile_control_phase(folder,p,label,index,workload):
    # Normalize only explicit new closure clocks/guard faults to the established
    # exact raw reader. Check every changed field independently before normalization.
    q=copy.deepcopy(p); m=model(label,index)
    declared,dose=dose_for(label,index)
    end=m['callback_end']+2+1055+dose+(450000 if label=='window-drift' and index==3 else 0)
    a=q['diagnostic_accounting'];c=q['precision_clock'];l=q['route_calibration']
    require(p['completed']==(not(label=='incomplete' and index==1)), 'completion fault changed')
    require(('elapsed_usec' not in a) if label=='missing-window' and index==1 else a['elapsed_usec']==end-1000000,'new complete duration differs')
    require(a['end_usec']==end and a['finalization_usec']==end-m['callback_end'] and c['phases'][2]==dict(phase='retirement',begin_usec=end,end_usec=end+2000),'new closure/retirement boundary differs')
    b=dict(native_phase_closed_usec=m['callback_end']+102,writer_drain_begin_usec=m['callback_end']+202,writer_drain_end_usec=m['callback_end']+602)
    if label=='phase-invalid' and index==1:b['native_phase_closed_usec']+=501
    require(p['fixed_work_boundaries']==b and p['edit_acknowledgement']==dict(start_usec=c['ack_begin_usec'] or 0,end_usec=m['callback_end']+2),'ack/native/drain guard differs')
    ds=m['callback_end']+702
    actual_dose=dict(requested_usec=declared if index in (1,2) else 0,start_usec=(m['callback_end']+1 if label=='dose-overlap' and index==1 else ds) if index in (1,2) and declared else None,
                     end_usec=ds+dose if index in (1,2) and declared else None,elapsed_usec=dose)
    require(l['closure_dose']==actual_dose and c['dose_begin_usec']==(ds if index in (1,2) else None)
            and c['dose_end_usec']==(ds+dose if index in (1,2) else None),'new declared/actual dose differs')
    q['completed']=True
    a.update(end_usec=m['end'],elapsed_usec=m['elapsed'],finalization_usec=1002+m['dose'])
    c['phases'][2]=dict(phase='retirement',begin_usec=m['end'],end_usec=m['end']+2000)
    c['dose_end_usec']=ds+m['dose'] if index in (1,2) else None
    l['closure_dose']=dict(requested_usec=600000 if index in (1,2) else 0,
                          start_usec=(m['callback_end']+1 if label=='dose-overlap' and index==1 else ds) if index in (1,2) else None,
                          end_usec=ds+m['dose'] if index in (1,2) else None,elapsed_usec=m['dose'])
    return reconcile_phase(folder,q,label,index,workload)


def validate(report,folder):
    folder=Path(folder)
    require(report['schema']==1 and report['passed'] is True and report['failures']==[] and report['scope']=='synthetic fixed-work closure controls; no target qualification','fixed-work controls failed')
    require(len(report['controls'])==len(LABELS)*2,'missing fixed-work controls')
    files=list(folder.iterdir())
    require(len(files)==MAX_FILES and all(p.is_file() and p.suffix=='.csv' for p in files)
            and sum(p.stat().st_size for p in files)<=64*1024*1024,'unbounded/missing raw evidence')
    seen=set();raw=[]
    for c in report['controls']:
        workload,label=c['name'].split('/')
        require(workload in ('H1','H2') and label in LABELS and c['name'] not in seen and c['workload']==workload,'invalid control identity')
        seen.add(c['name']);declared,_=dose_for(label,0)
        expected='null_observed' if label=='null' else ('sensitivity_observed' if label in ('below','at','above','endpoint','ack-duration','count-mask','count-drift') else 'inconclusive')
        require(c['expected']==expected and c['declared_dose_usec']==declared and c['io_failed']==(label=='io-failed'),'undeclared control changed')
        phases=c['phases'];omitted=c['omitted_phases']
        roles=[p['id'].rsplit(workload+'-',1)[-1] for p in phases]
        require(roles==list(reversed(ORDER)) if label=='reordered' else roles==list(ORDER[:3] if label=='missing' else ORDER),'order/completeness fault changed')
        require(len(omitted)==(1 if label=='missing' else 0),'omitted raw evidence lost')
        for i,p in enumerate(sorted(phases+omitted,key=lambda p:ORDER.index(p['id'].rsplit(workload+'-',1)[-1]))):raw.append(reconcile_control_phase(folder,p,label,i,workload))
        oracle=assess(phases,workload,io_failed=c['io_failed'],declared=declared)
        require(oracle['status']==expected,'independent fixed-work status differs')
        scope(c['assessment']);require(c['assessment']['declared_dose_usec']==declared,'saved declaration differs')
        equal(c['assessment']['workloads'][workload],oracle)
        require(bool(c['assessment']['workloads'][workload]['reasons'])==(expected=='inconclusive'),'guard reasons lost')
        require(c['assessment']['workloads']['H2' if workload=='H1' else 'H1']['status']=='not_run','absent workload fabricated')
        if label=='null':
            require(c['legacy_assessment'] is None,'zero-dose null must not invoke the legacy known-positive path')
        else:
            status,detail=legacy_assess(phases,workload,io_failed=c['io_failed'])
            legacy_scope(c['legacy_assessment']);reconcile_decision(c['legacy_assessment']['workloads'][workload],status,detail)
        if label=='at':require(oracle['duration_effect']['classification']=='above_limit' and oracle['duration_effect']['lower_fraction']==.01,'exact 1% boundary lost')
        if label=='below':require(oracle['duration_effect']['classification']=='below_limit','below boundary changed')
        if label=='count-mask':require(oracle['duration_effect']['lower_fraction']>.01 and max(v['time_per_callback_added_fraction'] for v in oracle['count_duration_decomposition'])<.01,'callback counts concealed closure duration')
    require({p['file'] for p in raw}=={p.name for p in files},'unreconciled fixed-work rows')
    return dict(passed=True,controls=len(seen),modeled_phases=len(raw),raw_rows=sum(p['rows'] for p in raw),raw_files=raw,
                legacy_authoritative=True,policy_changed=False,hardware_noise_calibrated=False,shared_overhead_qualified=False)


def reconcile_saved(path,folder):
    path=Path(path);require(path.stat().st_size<=MAX_REPORT,'fixed-work JSON exceeds 3 MiB')
    return validate(json.loads(path.read_text(encoding='utf-8')),folder)


def reconcile_runtime(folder):
    folder=Path(folder);saved=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    root=saved['fixed_work_sensitivity'];scope(root)
    require(root['declared_dose_usec']==600000,'runtime dose changed')
    for workload in ('H1','H2'):
        phases=[p for p in saved['scenarios'] if str(p['id']).startswith('CAL-'+workload+'-')]
        oracle=assess(phases,workload,saved['test_mode'],bool(saved['integration_failures']))
        equal(root['workloads'][workload],oracle)
    final=json.loads((folder/'report-finalization.json').read_text(encoding='utf-8'))
    require(final['elapsed_usec']==final['end_usec']-final['start_usec']>=0
            and all(p['diagnostic_accounting']['end_usec']<=final['start_usec'] for p in saved['scenarios']),
            'combined finalization missing or overlaps trial allocation')
    return dict(passed=True,workloads=2,combined_report_elapsed_usec=final['elapsed_usec'],allocated_to_trials=False,
                hardware_noise_calibrated=False,legacy_authoritative=True)
