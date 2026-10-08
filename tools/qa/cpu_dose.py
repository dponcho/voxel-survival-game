"""Independent rational CPU-span controls and real native-hash placement evidence.

Elapsed callback bodies are not OS CPU service, GPU time or causal probe overhead.
Clock fixtures declare hypothetical eligible routes; real hash probes run no terrain.
"""
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from fixed_work import observation as window, assess as assess_window, equal, number
from route_calibration import ORDER, compare, variation, require, LIMIT

VERSION = 'm1-cpu-dose-span-1'
LABELS = ('null','below','at','above','threshold-overlap','wait-masked','count-mask','count-drift','count-route-mix',
          'endpoint','ack-duration','incomplete','missing','reordered','stall','failed-workload','failed-operation',
          'missing-dose','dose-overlap','missing-body','phase-invalid','window-drift','route-drift','io-failed','short',
          'body-drift','main-body-drift')
HEADER = 'frame,tick,interval_usec,entry_usec,body_begin_usec,body_end_usec,dose_begin_usec,dose_end_usec,requested_usec,callback_end_usec,previous_frame,previous_callback_usec,ledger_tail_usec'.split(',')
MAX_JSON, MAX_RAW = 4*1024*1024, 64*1024*1024
NULL_KEYS = ('callbacks','body_usec','mean_body_usec','dose_usec','mean_dose_usec','complete_duration_usec',
             'entry_interval_usec','complete_callback_usec','ledger_remainder_usec','last_body_usec')
RESOLVED = ('below','at','above','wait-masked','count-mask','count-drift','endpoint','ack-duration')


def declaration(label):
    return {'null':0,'below':5,'at':10,'threshold-overlap':9}.get(label,20)


def expected_status(label):
    return 'null_observed' if label=='null' else ('cpu_span_sensitivity_observed' if label in RESOLVED else 'inconclusive')


def scope(root, not_run=False):
    require(root['version']==VERSION and root['experimental'] is True and root['qualified'] is False
            and root['legacy_authoritative'] is True and root['threshold']==.01 and root['hardware_noise_calibrated'] is False,
            'CPU experiment promoted to qualification')
    require(all(root[k] is None for k in ('causal_frontier_probe_cost','cpu_service_usec','gpu_cost','shared_causal_overhead')),
            'wall span promoted to CPU service/GPU/shared causal cost')
    if not_run:
        require(root['status']=='not_run' and root['workloads']=={}, 'ordinary benchmark ran a CPU dose')


def observation(p):
    try:
        w=window(p);a=p.get('cpu_dose_accounting',{});b=a.get('bins',[])
        require(w['status']=='measured' and a.get('version')==VERSION and a.get('invalid') is False and len(b)==7,'missing CPU ledger')
        request=number(a,'requested_per_callback_usec'); require(request>=0,'missing request')
        route=p['route_calibration']['bins']
        for j,x in enumerate(b):
            n,body,dose=(number(x,k) for k in ('samples','body_usec','dose_usec'))
            require(n==number(route[j],'samples')>0 and 0<body<=number(route[j],'callback_usec')
                    and request*n<=dose<=body and (request!=0 or dose==0),'CPU partition/callback mismatch')
        n=sum(number(x,'samples') for x in b);body=sum(number(x,'body_usec') for x in b);dose=sum(number(x,'dose_usec') for x in b)
        last=a.get('last_callback',{});begin,end=(number(last,k) for k in ('begin_usec','end_usec'))
        require(n==w['callbacks'] and body<=min(w['callback_usec'],w['elapsed_usec']) and p['diagnostic_accounting']['start_usec']<=begin<end<=p['diagnostic_accounting']['last_callback_end_usec']
                and end-begin==number(last,'body_usec')<=number(p['diagnostic_accounting'],'last_callback_usec')
                and number(last,'requested_usec')==request, 'CPU final callback lost')
        if request:
            ds,de=(number(last,k) for k in ('dose_begin_usec','dose_end_usec'))
            require(begin<=ds<=de<=end and de-ds>=request,'dose outside serialized callback')
        else: require(last.get('dose_begin_usec') is None and last.get('dose_end_usec') is None,'null dose clocks fabricated')
        return dict(status='measured',callbacks=n,body_usec=body,mean_body_usec=float(Fraction(body,n)),dose_usec=dose,
                    mean_dose_usec=float(Fraction(dose,n)),complete_duration_usec=w['elapsed_usec'],complete_callback_usec=w['callback_usec'],
                    entry_interval_usec=w['main_interval_usec']+w['terminal_interval_usec'],
                    ledger_remainder_usec=w['callback_usec']-body,last_body_usec=end-begin)
    except (ValueError,TypeError,KeyError): return dict(status='unavailable',**dict.fromkeys(NULL_KEYS))


def body_effect(obs):
    means=[Fraction(x['body_usec'],x['callbacks']) for x in obs]
    out=compare((means[0],means[3]),(means[1],means[2]))
    return {k:out[k] for k in ('classification','lower_fraction','upper_fraction')}


def assess(phases,workload,short=False,io_failed=False,declared=20):
    whole=assess_window(phases,workload,short,io_failed,0)
    out=dict(status='not_run' if not phases else 'inconclusive',qualified=False,
             body_effect=dict(classification='unavailable',lower_fraction=None,upper_fraction=None),observations=[],
             entry_interval_effect=dict(classification='unavailable',lower_fraction=None,upper_fraction=None),
             same_mode_body_variation=[],main_body_variation=[],complete_window=whole)
    if len(phases)!=4: return out
    obs=[observation(p) for p in phases];out['observations']=obs
    if any(o['status']!='measured' for o in obs): return out
    effect=body_effect(obs);out['body_effect']=effect
    out['entry_interval_effect']=body_effect([dict(body_usec=x['entry_interval_usec'],callbacks=x['callbacks']) for x in obs])
    valid=whole['status']=='null_observed' and declared>=0 and all(p['cpu_dose_accounting']['requested_per_callback_usec']==(declared if i in (1,2) else 0) for i,p in enumerate(phases))
    for left,right in ((0,3),(1,2)):
        whole_body=variation([Fraction(obs[j]['body_usec'],obs[j]['callbacks']) for j in (left,right)])
        bins=[p['cpu_dose_accounting']['bins'] for p in phases]
        main=[variation([Fraction(bins[j][k]['body_usec'],bins[j][k]['samples']) for j in (left,right)]) for k in range(6)]
        out['same_mode_body_variation'].append(float(whole_body));out['main_body_variation'].append(list(map(float,main)))
        valid &= max(whole_body,*main)<LIMIT
    first=phases[0]['cpu_dose_accounting']['bins']
    for p in phases:
        b=p['cpu_dose_accounting']['bins']
        valid &= all(b[j]['samples']*first[0]['samples']==first[j]['samples']*b[0]['samples'] for j in range(6))
    valid &= effect['classification']!='inconclusive' and (declared==0 or effect['lower_fraction']>0)
    if valid: out['status']='null_observed' if declared==0 else 'cpu_span_sensitivity_observed'
    return out


def model(label,index):
    """Closed-form section sums, independent of event expansion and ledgers."""
    request=declaration(label) if index in (1,2) else 0
    actual=11 if label=='threshold-overlap' and index==2 else request
    counts=[250]*6+[4];durations=[5000000]*6+[20000];base=[800,1200]*3+[1000]
    if (label=='count-mask' and index in (1,2)) or (label=='count-drift' and index==3): counts=[255]*6+[4]
    if label=='count-route-mix' and index in (1,2): counts=[450,250]*3+[4]
    if label=='endpoint' and index in (2,3): durations[5]-=500;durations[6]+=500
    if label=='ack-duration' and index in (2,3): durations[6]+=500
    if label=='stall' and index==1:durations[0]+=300000
    if label=='route-drift' and index==3:durations[0]+=100000;durations[1]-=100000
    if label=='body-drift' and index==3:base=[x+30 for x in base]
    if label=='main-body-drift' and index==3:base=[820,1180]*3+[1000]
    sums=[d+(0 if label=='wait-masked' else actual*(n-(j==0))) for j,(n,d) in enumerate(zip(counts,durations))]
    body=[n*(x+actual) for n,x in zip(counts,base)]
    dose=[n*(x+actual-199 if label=='dose-overlap' and index==1 else (0 if label=='missing-dose' and index==1 else actual)) for n,x in zip(counts,base)]
    return dict(request=request,actual=actual,counts=counts,durations=durations,base=base,interval_sums=sums,body_sums=body,dose_sums=dose,
                n=sum(counts),interval_total=sum(sums),body_total=sum(body),invalid=label in ('dose-overlap','missing-dose') and index==1)


def reconcile_phase(folder,p,label,index,workload):
    m=model(label,index);name=f'{workload}-{label}-{index}.csv';path=Path(folder)/name
    require(p['id']==f'CAL-{workload}-{ORDER[index]}' and p['raw_frames']==name and path.is_file() and path.stat().st_size<2*1024*1024,'raw CPU phase missing/unbounded')
    # Validate the unchanged hypothetical workload contract independently; declared
    # completion/operation faults remain explicit rather than normalized to passing.
    from fixed_work import workload_valid
    import copy
    q=copy.deepcopy(p);q['id']=f'CAL-{workload}-{ORDER[0]}';q['completed']=True;q['evaluation']='inconclusive';q['wall_seconds']=30.02
    if label=='failed-workload' and index==1:q['actor_ticks']+=1
    clones=[copy.deepcopy(q) for _ in range(4)]
    for i,x in enumerate(clones): x['id']=f'CAL-{workload}-{ORDER[i]}'
    require(workload_valid(clones,workload,False),'CPU model changed workload contract')
    require(p['completed']==(not(label=='incomplete' and index==1)) and p['actor_ticks']==(24 if workload=='H2' else 12)*1800-(label=='failed-workload' and index==1)
            and p['evaluation']==('failed' if label=='failed-operation' and index==1 else 'inconclusive'),'declared completion/workload/operation fault changed')
    require(p.get('modeled_operation')==(dict(upload=dict(max_usec=751),deletion=dict(max_usec=0),dropped_frames=0) if label=='failed-operation' and index==1 else None),'operation guard was waived')
    bins=[dict(samples=0,body_usec=0,dose_usec=0) for _ in range(7)]
    route=[dict(samples=0,usec=0,callbacks=0,callback_usec=0) for _ in range(7)]
    entry=1000200;previous=0;previous_tick=0;count=0;blocks=[];block_n=block_us=0;ack=0;last={}
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);require(reader.fieldnames==HEADER,'CPU CSV schema changed')
        for v in reader:
            row={k:(int(x) if x else None) for k,x in v.items()};count+=1
            require(count<=m['n'] and row['frame']==count and previous_tick<=row['tick']<=1800,'CPU callback order/clock changed')
            j=6 if row['tick']==1800 else (row['tick']-1)//300;position=bins[j]['samples']
            require(0<=j<7 and row['tick']==(1800 if j==6 else j*300+1) and position<m['counts'][j],'CPU route/terminal boundary changed')
            q,r=divmod(m['durations'][j],m['counts'][j]);interval=q+(position<r)+(m['actual'] if count>1 and label!='wait-masked' else 0)
            entry+=interval;begin=entry+7;end=begin+m['base'][j]+m['actual'];ds=begin+200 if m['request'] else None;de=ds+m['actual'] if ds else None
            if label=='missing-dose' and index==1:ds=None
            if label=='dose-overlap' and index==1:de=end+1
            require(row==dict(frame=count,tick=1800 if j==6 else j*300+1,interval_usec=interval,entry_usec=entry,
                    body_begin_usec=begin,body_end_usec=end,dose_begin_usec=ds,dose_end_usec=de,requested_usec=m['request'],
                    callback_end_usec=end+8,previous_frame=count-1,previous_callback_usec=previous,ledger_tail_usec=2),'CPU raw bracket/previous/final callback differs')
            bins[j]['samples']+=1;bins[j]['body_usec']+=end-begin;bins[j]['dose_usec']+=de-ds if ds is not None and de is not None else 0
            route[j]['samples']+=1;route[j]['callbacks']+=1;route[j]['usec']+=interval;route[j]['callback_usec']+=end+8-begin
            block_n+=1;block_us+=interval
            if block_us>=5000000:blocks.append(dict(samples=block_n,usec=block_us));block_n=block_us=0
            if j==6 and position==0:ack=end+10
            previous=end+8-begin;previous_tick=row['tick']
            last=dict(begin_usec=begin,end_usec=end,body_usec=end-begin,dose_begin_usec=ds,dose_end_usec=de,requested_usec=m['request'])
    require(count==m['n'] and [b['body_usec'] for b in bins]==m['body_sums'] and [b['dose_usec'] for b in bins]==m['dose_sums']
            and [x['usec'] for x in route]==m['interval_sums'],'closed-form CPU totals or saved final row missing')
    measured=last['end_usec']+10;end=measured+1055+(450000 if label=='window-drift' and index==3 else 0)
    a=p['diagnostic_accounting']
    expected=dict(start_usec=1000000,end_usec=end,elapsed_usec=end-1000000,callbacks=count,callback_usec=m['body_total']+8*count,
        shared_usec=m['body_total']+8*count,last_callback_usec=previous,last_shared_usec=previous,last_callback_end_usec=last['end_usec']+8,
        maximum_callback_usec=max(m['base'])+m['actual']+8,switched_calls=0,switched_usec=0,last_switched_usec=0,
        finalization_usec=end-last['end_usec']-8,writer_drain_usec=400,invalid_partition=False,overflow=False,blocks=blocks,partial_block=dict(samples=block_n,usec=block_us))
    equal(a,expected)
    require(p['samples']==count and p['measurement_end_usec']==measured and abs(p['wall_seconds']*1e6-m['interval_total'])<.01,'CPU window/scenario duration differs')
    ledger=p['cpu_dose_accounting'];equal(ledger,dict(version=VERSION,invalid=m['invalid'],requested_per_callback_usec=m['request'],last_callback=last))
    expected_bins=[dict(x) for x in bins]
    if label=='missing-body' and index==1:expected_bins[6].pop('body_usec')
    require(ledger['bins']==expected_bins,'CPU missing/body ledger differs')
    for raw,saved in zip(route,p['route_calibration']['bins']):
        equal(saved,dict(**raw,status='measured',mean_usec=float(Fraction(raw['usec'],raw['samples']))))
    require(p['route_calibration']['invalid'] is False and p['route_calibration']['harness_bracket_usec']==2*count
            and p['route_calibration']['closure_dose']==dict(requested_usec=0,start_usec=None,end_usec=None,elapsed_usec=0),'CPU dose became closure dose or missing precision became zero')
    require(p['edit_acknowledgement']==dict(start_usec=ack,end_usec=measured)
            and p['fixed_work_boundaries']==dict(native_phase_closed_usec=measured+(601 if label=='phase-invalid' and index==1 else 100),writer_drain_begin_usec=measured+200,writer_drain_end_usec=measured+600),'CPU acknowledgement/drain phase sequence differs')
    require(p['cpu_clock']==dict(scope='modeled clocks; hypothetical eligible workload, no CPU/GPU/terrain measurement',interval_begin_usec=1000200,
        phases=[dict(phase='preparation',begin_usec=998000,end_usec=1000000),dict(phase='overhead_diagnostic',begin_usec=1000000,end_usec=measured+100),
                dict(phase='retirement',begin_usec=end,end_usec=end+2000)],file_io_causal_usec=None),'CPU closure/I/O/retirement boundary changed')
    return dict(file=name,rows=count)


def reconcile_saved(path,folder):
    path=Path(path);folder=Path(folder);require(path.stat().st_size<=MAX_JSON,'CPU control JSON exceeds 4 MiB')
    r=json.loads(path.read_text(encoding='utf-8'))
    require(r['schema']==1 and r['passed'] is True and r['failures']==[] and r['scope']=='synthetic per-callback CPU span sensitivity; no qualification','CPU controls failed')
    require(len(r['controls'])==2*len(LABELS),'CPU control registry incomplete')
    files=list(folder.iterdir());require(len(files)==8*len(LABELS) and all(x.is_file() and x.suffix=='.csv' for x in files)
        and sum(x.stat().st_size for x in files)<=MAX_RAW,'CPU raw evidence missing/unbounded')
    seen=set();raw=[]
    for c in r['controls']:
        workload,label=c['name'].split('/');require(workload in ('H1','H2') and label in LABELS and c['name'] not in seen,'CPU control identity differs')
        seen.add(c['name']);require(c['workload']==workload and c['expected']==expected_status(label) and c['declared_per_callback_usec']==declaration(label)
            and c['short_run']==(label=='short') and c['io_failed']==(label=='io-failed'),'undeclared CPU fault/threshold changed')
        phases=c['phases'];omitted=c['omitted_phases'];roles=[p['id'].rsplit(workload+'-',1)[-1] for p in phases]
        require(roles==(list(reversed(ORDER)) if label=='reordered' else list(ORDER[:3] if label=='missing' else ORDER)) and len(omitted)==(label=='missing'),'CPU order or omitted evidence lost')
        for i,p in enumerate(sorted(phases+omitted,key=lambda x:ORDER.index(x['id'].rsplit(workload+'-',1)[-1]))):raw.append(reconcile_phase(folder,p,label,i,workload))
        oracle=assess(phases,workload,c['short_run'],c['io_failed'],declaration(label));require(oracle['status']==expected_status(label),'independent CPU verdict differs')
        scope(c['assessment']);require(c['assessment']['declared_per_callback_usec']==declaration(label),'CPU saved declaration differs')
        equal(c['assessment']['workloads'][workload],oracle)
        require(bool(c['assessment']['workloads'][workload]['reasons'])==(oracle['status']=='inconclusive'),'CPU guard reasons lost')
        require(c['assessment']['workloads']['H2' if workload=='H1' else 'H1']['status']=='not_run','CPU absent workload fabricated')
        if label=='at':require(oracle['body_effect']['lower_fraction']==.01 and oracle['body_effect']['classification']=='above_limit','exact CPU 1% boundary changed')
        if label=='wait-masked':require(oracle['body_effect']['lower_fraction']==.02 and oracle['complete_window']['duration_effect']['upper_fraction']<.000001,'wait masking control changed')
        if label=='count-mask':require(oracle['body_effect']['lower_fraction']==.02 and max(x['time_per_callback_added_fraction'] for x in oracle['complete_window']['count_duration_decomposition'])<0,'count masking control changed')
        if label=='count-route-mix':require(oracle['body_effect']['lower_fraction']<0 and oracle['status']=='inconclusive','changed route mix falsely attributed')
    require({x['file'] for x in raw}=={p.name for p in files},'CPU saved rows unreconciled')
    return dict(passed=True,controls=len(seen),modeled_phases=len(raw),raw_rows=sum(x['rows'] for x in raw),raw_files=raw,qualified=False,policy_changed=False,cpu_service_usec=None,shared_causal_overhead=None)


def reconcile_runtime(folder, expected_build=None):
    folder=Path(folder);require(sum(p.stat().st_size for p in folder.iterdir())<1024*1024,'CPU runtime evidence exceeds 1 MiB')
    expected_key = expected_build['native_source_key'] if expected_build is not None else '11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d'
    r=json.loads((folder/'summary.json').read_text(encoding='utf-8'));require(r['passed'] is True and r['failures']==[] and r['status']=='placement_verified'
        and r['qualified'] is False and r['experimental'] is True and r['max_callbacks']==128 and r['buffer_bytes']==4096 and r['max_hash_updates_per_callback']==512,
        'native CPU placement failed or bounds changed')
    require(all(r[k] is None for k in ('cpu_service_usec','causal_probe_cost','gpu_cost','shared_causal_overhead')),'runtime wall time promoted to causal qualification')
    require(isinstance(r.get('build'),dict) and r['build'].get('godot_commit')=='ed1daf0bf001b61586d9930840f2f1394092c079'
            and r['build'].get('voxel_commit')=='2ac9f5f8a8219bf499314cc0fad54ffc47df908f'
            and r['build'].get('native_source_key')==expected_key
            and isinstance(expected_key,str) and len(expected_key)==64 and all(c in '0123456789abcdef' for c in expected_key)
            and len(r['build'].get('game_commit',''))==40,'CPU probe build identity unavailable')
    if expected_build is not None:require(r['build']==expected_build,'CPU probe differs from exported build')
    require(len(r['trials'])==4 and {p.name for p in folder.iterdir()}=={'summary.json','report-finalization.json',*(f'callback-{i}.jsonl' for i in range(4))},'CPU runtime evidence missing/extra')
    buffer=bytes([90])*4096;baseline=hashlib.sha256(buffer*8).hexdigest();obs=[];all_rows=0;prior_end=0
    for i,t in enumerate(r['trials']):
        require(t['index']==i and t['raw_file']==f'callback-{i}.jsonl' and t['callbacks']==32,'runtime CPU trial identity changed')
        a=t['diagnostic_accounting'];cpu=t['cpu_dose_accounting'];start=number(a,'start_usec');entry=start;previous=0;body_sum=dose_sum=callback_sum=0
        require(start>=prior_end and cpu['version']==VERSION and cpu['invalid'] is False and cpu['requested_per_callback_usec']==(500 if i in (1,2) else 0),'runtime CPU sequence/ledger invalid')
        bins=[dict(samples=0,body_usec=0,dose_usec=0) for _ in range(7)];blocks=[];bn=bt=0;maximum=0;count=0
        with (folder/t['raw_file']).open(encoding='utf-8') as f:
            for line in f:
                row=json.loads(line);count+=1;require(count<=32,'runtime callback cap exceeded')
                begin,end,complete=(number(row,k) for k in ('body_begin_usec','body_end_usec','complete_callback_end_usec'))
                tick=1800 if count>28 else min(5,(count-1)*6//28)*300+1
                require(row['frame']==count and row['tick']==tick and row['entry_usec']==begin and begin>=entry+previous
                    and row['interval_usec']==begin-entry and row['previous_frame']==count-1 and row['previous_callback_usec']==previous
                    and begin<end<=complete and row['baseline_sha256']==baseline,'runtime callback/previous clock/native baseline hash differs')
                request=500 if i in (1,2) else 0;require(row['requested_usec']==request,'runtime request changed')
                dose=0
                if request:
                    ds,de=(number(row,k) for k in ('dose_begin_usec','dose_end_usec'));dose=de-ds;updates=number(row,'hash_updates')
                    require(begin<=ds<=de<=end and 500<=dose<=50000 and 1<=updates<=512 and row['hash_sha256']==hashlib.sha256(buffer*updates).hexdigest(),
                            'native CPU work outside callback, missing, unbounded or digest wrong')
                else:require(row['dose_begin_usec'] is None and row['dose_end_usec'] is None and row['hash_updates']==0 and row['hash_sha256'] is None,'null runtime performed a dose')
                j=6 if tick==1800 else (tick-1)//300;bins[j]['samples']+=1;bins[j]['body_usec']+=end-begin;bins[j]['dose_usec']+=dose
                body_sum+=end-begin;dose_sum+=dose;callback_sum+=complete-begin;maximum=max(maximum,complete-begin)
                bn+=1;bt+=row['interval_usec']
                if bt>=5000000:blocks.append(dict(samples=bn,usec=bt));bn=bt=0
                last=dict(begin_usec=begin,end_usec=end,body_usec=end-begin,dose_begin_usec=row['dose_begin_usec'],dose_end_usec=row['dose_end_usec'],requested_usec=request)
                entry=begin;previous=complete-begin
        require(count==32 and cpu['bins']==bins and cpu['last_callback']==last,'runtime CPU final callback or aggregate lost')
        cbend=entry+previous;db,de=(number(t,k) for k in ('writer_drain_begin_usec','writer_drain_end_usec'));end=number(a,'end_usec')
        require(start<cbend<=db<=de<=end and end-start==a['elapsed_usec'] and a['finalization_usec']==end-cbend and a['writer_drain_usec']==de-db,'runtime CPU writer/finalization scope changed')
        equal(a,dict(callbacks=count,callback_usec=callback_sum,shared_usec=callback_sum,switched_usec=0,switched_calls=0,last_switched_usec=0,
            last_shared_usec=previous,last_callback_usec=previous,last_callback_end_usec=cbend,maximum_callback_usec=maximum,blocks=blocks,partial_block=dict(samples=bn,usec=bt),invalid_partition=False,overflow=False))
        obs.append(dict(body_usec=body_sum,dose_usec=dose_sum,callbacks=count));all_rows+=count;prior_end=end
    require(r['observations']==obs,'runtime CPU mean lost final work');equal(r['body_effect'],body_effect(obs))
    final=json.loads((folder/'report-finalization.json').read_text(encoding='utf-8'))
    require(prior_end<=final['start_usec']<=final['end_usec'] and final['elapsed_usec']==final['end_usec']-final['start_usec'] and final['allocated_to_trials'] is False,
            'runtime combined reporting overlapped/allocated or missing')
    return dict(passed=True,real_callbacks=all_rows,native_hash_digests_verified=True,body_effect=r['body_effect'],qualified=False,cpu_service_usec=None,shared_causal_overhead=None)
