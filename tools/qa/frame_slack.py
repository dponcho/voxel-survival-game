"""Independent exact callback-cycle arithmetic and saved native CPU evidence.

An owned cycle includes OS scheduling and engine waits. It is not CPU service,
GPU completion, physical presentation or causal/shared diagnostic overhead.
"""
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from fixed_work import number, equal
from route_calibration import require, compare, variation, LIMIT

VERSION = 'm1-frame-slack-1'
LABELS = ('null','below','at','above','threshold-overlap','slack','final-dose','count-drift','count-route-mix',
          'endpoint','ack-duration','incomplete','missing','reordered','stall','failed-workload','failed-operation',
          'missing-dose','dose-overlap','missing-body','phase-invalid','window-drift','io-failed','short','body-drift',
          'main-body-drift','missing-successor','cycle-overlap','cycle-drift','main-cycle-drift')
TOTALS = ('cycle_usec','body_usec','dose_usec','callback_usec','callback_overhead_usec','outside_callback_usec')
HEADER = 'frame,tick,entry_usec,body_begin_usec,body_end_usec,dose_begin_usec,dose_end_usec,requested_usec,complete_callback_end_usec,next_entry_usec,previous_callback_usec,baseline_updates'.split(',')
NULL_KEYS = ('callbacks',*TOTALS,'complete_duration_usec','closing_anchor_usec','last_cycle_usec')
MAX_JSON, MAX_RAW = 2*1024*1024, 2*1024*1024


def declaration(label):
    return {'null':0,'below':100,'at':200,'threshold-overlap':199,'slack':500}.get(label,400)


def expected_status(label):
    return 'null_observed' if label=='null' else ('slack_observed' if label=='slack' else
        ('frame_sensitivity_observed' if label in ('below','at','above','final-dose','endpoint','ack-duration') else 'inconclusive'))


def scope(r, not_run=False):
    require(r['version']==VERSION and r['experimental'] is True and r['qualified'] is False and r['legacy_authoritative'] is True
            and r['threshold']==.01 and r['hardware_noise_calibrated'] is False, 'frame observation promoted to qualification')
    require(all(r[k] is None for k in ('cpu_service_usec','gpu_cost','physical_presentation','causal_probe_cost','shared_causal_overhead')),
            'wall cycle promoted to service/GPU/presentation/causal cost')
    if not_run:require(r['status']=='not_run' and r['workloads']=={},'ordinary workload ran frame dose')


def observation(p):
    try:
        l=p['frame_slack_accounting'];a=p['diagnostic_accounting'];b=p['phase_boundaries'];anchor=p['closing_anchor'];bins=l['bins']
        require(l['version']==VERSION and l['invalid'] is False and len(bins)==7 and a['invalid_partition'] is False and a['overflow'] is False,'invalid frame ledger')
        out=dict(status='measured',callbacks=sum(number(x,'samples') for x in bins),**{k:sum(number(x,k) for x in bins) for k in TOTALS})
        for x in bins:
            require(number(x,'samples')>0 and all(number(x,k)>=0 for k in TOTALS) and x['body_usec']>0
                and x['body_usec']+x['callback_overhead_usec']==x['callback_usec'] and x['callback_usec']+x['outside_callback_usec']==x['cycle_usec']
                and x['dose_usec']<=x['body_usec'],'cycle overlapping partition')
        start,end=(number(a,k) for k in ('start_usec','end_usec'));first=number(p,'first_entry_usec')
        ae,ac=(number(anchor,k) for k in ('entry_usec','complete_callback_end_usec'));last=l['last_cycle']
        le,ln,lc=(number(last,k) for k in ('entry_usec','next_entry_usec','complete_callback_end_usec'))
        native,db,de=(number(b,k) for k in ('native_phase_closed_usec','writer_drain_begin_usec','writer_drain_end_usec'))
        require(0<=start<=first<=le<ln==ae<ac<=native<=db<=de<=end and end-start==number(a,'elapsed_usec')<=600000000
            and out['cycle_usec']==ae-first,'cycle/anchor/phase boundary unavailable')
        require(out['callbacks']==number(p,'samples')==number(a,'callbacks') and out['callback_usec']==number(a,'callback_usec')==number(a,'shared_usec')
            and a['switched_usec']==a['switched_calls']==0 and lc==number(a,'last_callback_end_usec')
            and end-lc==number(a,'finalization_usec') and de-db==number(a,'writer_drain_usec'),'callback/finalization scope lost')
        require(le<=number(last,'body_begin_usec')<number(last,'body_end_usec')<=lc<=ln,'final body/anchor lost')
        request=number(last,'requested_usec');require(request>=0,'last request unavailable')
        if request:
            ds,dt=(number(last,k) for k in ('dose_begin_usec','dose_end_usec'))
            require(last['body_begin_usec']<=ds<dt<=last['body_end_usec'] and dt-ds>=request,'last dose unavailable/overlapping')
        else:require(last.get('dose_begin_usec') is None and last.get('dose_end_usec') is None,'null last dose fabricated')
        require(number(b,'measurement_begin_usec')==start and 0<=number(b,'preparation_begin_usec')<=start and number(b,'retirement_begin_usec')==end<=number(b,'retirement_end_usec')
            and 0<=number(p,'acknowledgement_usec')<=end-start and number(anchor,'previous_callback_usec')==number(a,'last_callback_usec')==lc-le,'phase/ack/anchor callback evidence unavailable')
        out.update(complete_duration_usec=end-start,closing_anchor_usec=ac-ae,last_cycle_usec=ln-le)
        return out
    except (ValueError,TypeError,KeyError):return dict(status='unavailable',**dict.fromkeys(NULL_KEYS))


def effects(obs):
    def effect(key):
        means=[Fraction(o[key],o['callbacks']) for o in obs]
        e=compare((means[0],means[3]),(means[1],means[2]))
        return {k:e[k] for k in ('classification','lower_fraction','upper_fraction')}
    return dict(cycle_effect=effect('cycle_usec'),body_effect=effect('body_usec'))


def assess(phases,declared,final_only=False,io_failed=False):
    out=dict(status='not_run' if not phases else 'inconclusive',observations=[],same_mode_pairs=[],
        cycle_effect=dict(classification='unavailable',lower_fraction=None,upper_fraction=None),
        body_effect=dict(classification='unavailable',lower_fraction=None,upper_fraction=None))
    if len(phases)!=4:return out
    obs=[observation(p) for p in phases];out['observations']=obs
    if any(o['status']!='measured' for o in obs):return out
    out.update(effects(obs))
    valid=not io_failed and all(p['index']==i and p['completed'] is True and p['work_units_valid'] is True
        and p.get('operation_evaluation')=='inconclusive' and p['samples']==32 and p['frame_slack_accounting']['stalled'] is False for i,p in enumerate(phases))
    for i,o in enumerate(obs):
        request=declared if i in (1,2) else 0
        valid &= request>=0 and o['dose_usec']>=request*(1 if final_only else o['callbacks']) and (request!=0 or o['dose_usec']==0)
        valid &= all(p['samples']==q['samples'] for p,q in zip(phases[i]['frame_slack_accounting']['bins'],phases[0]['frame_slack_accounting']['bins']))
    for left,right in ((0,3),(1,2)):
        a,b=obs[left],obs[right];variations=[variation((a[k],b[k])) for k in ('complete_duration_usec','cycle_usec','body_usec')]
        main=[variation((phases[left]['frame_slack_accounting']['bins'][j][k],phases[right]['frame_slack_accounting']['bins'][j][k])) for j in range(6) for k in ('cycle_usec','body_usec')]
        td=phases[right]['frame_slack_accounting']['bins'][6]['cycle_usec']-phases[left]['frame_slack_accounting']['bins'][6]['cycle_usec']
        ad=phases[right]['acknowledgement_usec']-phases[left]['acknowledgement_usec'];u=max(abs(td),abs(ad));uf=Fraction(2*u,a['complete_duration_usec']+b['complete_duration_usec'])
        out['same_mode_pairs'].append(dict(variations=list(map(float,variations)),terminal_delta_usec=td,acknowledgement_delta_usec=ad,endpoint_uncertainty_usec=u,endpoint_uncertainty_fraction=float(uf)))
        valid &= max(*variations,*main,uf)<LIMIT
    valid &= out['cycle_effect']['classification']!='inconclusive' and (declared==0 or out['body_effect']['lower_fraction']>0)
    if valid:out['status']='null_observed' if declared==0 else ('slack_observed' if out['cycle_effect']['upper_fraction']==0 else 'frame_sensitivity_observed')
    return out


def model(label,index):
    """Predeclared section constants; no production ledger or evaluator is called."""
    counts=[4,5,5,4,5,5,4]
    if label=='count-drift' and index==3:counts[6]+=4
    if label=='count-route-mix' and index in (1,2):counts[0]+=8
    if label=='short':counts[6]-=1
    request=declaration(label) if index in (1,2) else 0
    actual=201 if label=='threshold-overlap' and index==2 else request
    base=[800,1200]*3+[1000];cycle=[20000]*7
    if label=='count-route-mix':cycle=[16000,24000]*3+[20000]
    if label=='body-drift' and index==3:base=[x+30 for x in base]
    if label=='main-body-drift' and index==3:base=[825,1175]*3+[1000]
    if label=='cycle-drift' and index==3:cycle=[x+500 for x in cycle]
    if label=='main-cycle-drift' and index==3:cycle[0]+=300;cycle[1]-=240
    cycles=[n*(c+(actual if label not in ('slack','final-dose') else 0)) for n,c in zip(counts,cycle)]
    bodies=[n*(b+(actual if label!='final-dose' else 0)) for n,b in zip(counts,base)]
    doses=[n*actual for n in counts]
    if label=='final-dose':cycles[-1]+=actual;bodies[-1]+=actual;doses=[0]*6+[actual]
    if label=='endpoint' and index in (2,3):cycles[5]-=500;cycles[6]+=500
    if label=='ack-duration' and index in (2,3):cycles[6]+=500
    if label=='stall' and index==1:cycles[0]+=300000
    return dict(counts=counts,request=request,actual=actual,base=base,cycle=cycle,cycle_sums=cycles,body_sums=bodies,dose_sums=doses)


def modeled_rows(label,index):
    m=model(label,index);entry=1000200;previous=0;frame=0
    for j,n in enumerate(m['counts']):
        for pos in range(n):
            frame+=1;request=m['request'] if label!='final-dose' or (j==6 and pos==n-1) else 0
            dose=201 if label=='threshold-overlap' and index==2 else request
            duration=m['cycle'][j]+(dose if label!='slack' else 0)
            if label=='endpoint' and index in (2,3):duration+=(-500 if j==5 and pos==n-1 else (500 if j==6 and pos==0 else 0))
            if label=='ack-duration' and index in (2,3) and j==6 and pos==n-1:duration+=500
            if label=='stall' and index==1 and frame==1:duration+=300000
            begin=entry+7;end=begin+m['base'][j]+dose;ds=begin+200 if request else None;de=ds+dose if ds is not None else None
            if label=='missing-dose' and index==1:ds=None
            if label=='dose-overlap' and index==1:de=end+1
            nxt=end+7 if label=='cycle-overlap' and index==1 and frame==1 else entry+duration
            if label=='missing-successor' and index==1 and j==6 and pos==n-1:nxt=None
            yield dict(frame=frame,tick=1800 if j==6 else j*300+1,entry_usec=entry,body_begin_usec=begin,body_end_usec=end,
                dose_begin_usec=ds,dose_end_usec=de,requested_usec=request,complete_callback_end_usec=end+8,next_entry_usec=nxt,
                previous_callback_usec=previous,baseline_updates=7 if label=='failed-workload' and index==1 and frame==1 else 8)
            previous=end+8-entry;entry+=duration


def aggregate(rows):
    """Sum exclusive raw partitions; invalid fixture clocks stay visibly invalid."""
    bins=[dict(samples=0,**dict.fromkeys(TOTALS,0)) for _ in range(7)]
    for r in rows:
        j=6 if r['tick']==1800 else (r['tick']-1)//300;b=bins[j];b['samples']+=1
        e,bb,be,cb,nx=(r[k] for k in ('entry_usec','body_begin_usec','body_end_usec','complete_callback_end_usec','next_entry_usec'))
        ds,de=r['dose_begin_usec'],r['dose_end_usec'];body=be-bb;callback=cb-e
        vals=dict(cycle_usec=(-1 if nx is None else nx)-e,body_usec=body,dose_usec=de-ds if ds is not None and de is not None else 0,
                  callback_usec=callback,callback_overhead_usec=callback-body,outside_callback_usec=(-1 if nx is None else nx)-cb)
        for k,v in vals.items():b[k]+=max(0,v)
    return bins


def reconcile_phase(folder,p,label,index):
    path=Path(folder)/(label+'-'+str(index)+'.csv');require(p['raw_file']==path.name and path.is_file(),'modeled frame file missing')
    rows=[]
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);require(reader.fieldnames==HEADER,'frame CSV schema changed')
        for r in reader:rows.append({k:int(v) if v else None for k,v in r.items()});require(len(rows)<=40,'unbounded frame control')
    expected=list(modeled_rows(label,index));require(rows==expected,'modeled frame body/dose/successor changed')
    m=model(label,index);bins=aggregate(rows);invalid=label in ('missing-dose','dose-overlap','missing-successor','cycle-overlap') and index==1
    if not invalid:
        require([b['cycle_usec'] for b in bins]==m['cycle_sums'] and [b['body_usec'] for b in bins]==m['body_sums'] and [b['dose_usec'] for b in bins]==m['dose_sums'],'independent section totals differ')
    if label=='missing-body' and index==1:bins[-1].pop('body_usec')
    l=p['frame_slack_accounting'];equal(l,dict(version=VERSION,invalid=invalid,stalled=label=='stall' and index==1,bins=bins,last_cycle=rows[-1]))
    n=len(rows);actual_end=1000200+sum(m['cycle_sums']);anchor=dict(entry_usec=actual_end,complete_callback_end_usec=actual_end+15,previous_callback_usec=rows[-1]['complete_callback_end_usec']-rows[-1]['entry_usec'])
    require(p['closing_anchor']==anchor and p['first_entry_usec']==1000200 and p['samples']==n and p['index']==index,'closing anchor/count changed')
    closed=actual_end+15;end=closed+1055+(20000 if label=='window-drift' and index==3 else 0);a=p['diagnostic_accounting']
    total_callback=sum(r['complete_callback_end_usec']-r['entry_usec'] for r in rows);last=anchor['previous_callback_usec']
    blocks=[];bn=bt=0
    for i,r in enumerate(rows):
        duration=(rows[i+1]['entry_usec'] if i+1<n else actual_end)-r['entry_usec'];bn+=1;bt+=duration
        if bt>=5000000:blocks.append(dict(samples=bn,usec=bt));bn=bt=0
    equal(a,dict(start_usec=1000000,end_usec=end,elapsed_usec=end-1000000,callbacks=n,callback_usec=total_callback,shared_usec=total_callback,
        switched_usec=0,switched_calls=0,last_callback_usec=last,last_shared_usec=last,last_switched_usec=0,last_callback_end_usec=rows[-1]['complete_callback_end_usec'],
        maximum_callback_usec=max(r['complete_callback_end_usec']-r['entry_usec'] for r in rows),finalization_usec=end-rows[-1]['complete_callback_end_usec'],
        writer_drain_usec=400,blocks=blocks,partial_block=dict(samples=bn,usec=bt),invalid_partition=False,overflow=False))
    require(p['phase_boundaries']==dict(preparation_begin_usec=998000,measurement_begin_usec=1000000,
        native_phase_closed_usec=closed+(601 if label=='phase-invalid' and index==1 else 100),writer_drain_begin_usec=closed+200,writer_drain_end_usec=closed+600,
        retirement_begin_usec=end,retirement_end_usec=end+2000),'native/drain/preparation/retirement scopes differ')
    ack=next(r['complete_callback_end_usec'] for r in rows if r['tick']==1800)
    require(p['acknowledgement_usec']==closed-ack and p['completed']==(not(label=='incomplete' and index==1)) and p['work_units_valid']==(not(label=='failed-workload' and index==1)), 'endpoint/work guard waived')
    require(p['operation_evaluation']==('failed' if label=='failed-operation' and index==1 else 'inconclusive') and
        p.get('modeled_operation')==(dict(upload=dict(max_usec=751),deletion=dict(max_usec=0),dropped_frames=0) if label=='failed-operation' and index==1 else None),'operation failure waived')
    require(p['render_signals'] is None and p['wait_service_usec'] is None,'unobserved render/wait measured as zero')
    return n


def reconcile_saved(path,folder):
    path=Path(path);folder=Path(folder);require(path.stat().st_size<=MAX_JSON,'frame controls exceed 2 MiB');r=json.loads(path.read_text())
    require(r['schema']==1 and r['passed'] is True and r['failures']==[] and len(r['controls'])==len(LABELS),'frame controls failed/incomplete')
    files=list(folder.iterdir());require(len(files)==len(LABELS)*4 and all(p.is_file() and p.suffix=='.csv' for p in files) and sum(p.stat().st_size for p in files)<=MAX_RAW,'frame CSV registry unbounded/missing')
    seen=set();rows=0;phases=0
    for c in r['controls']:
        label=c['name'];require(label in LABELS and label not in seen and c['expected']==expected_status(label) and c['declared_usec']==declaration(label),'undeclared frame control');seen.add(label)
        all_phases=c['phases']+c['omitted_phases'];require(sorted(p['index'] for p in all_phases)==list(range(4)),'frame phase missing/duplicate')
        for p in all_phases:rows+=reconcile_phase(folder,p,label,p['index']);phases+=1
        scope(c['assessment']);equal(c['assessment'],assess(c['phases'],declaration(label),label=='final-dose',label=='io-failed'))
        require(c['assessment']['status']==expected_status(label),'saved frame classification changed')
    return dict(passed=True,controls=len(seen),modeled_phases=phases,raw_rows=rows,qualified=False,cpu_service_usec=None,shared_causal_overhead=None)


def digest(updates):
    h=hashlib.sha256();buffer=bytes([90])*4096
    for _ in range(updates):h.update(buffer)
    return h.hexdigest()


def reconcile_runtime(folder,expected_build=None):
    folder=Path(folder);files=list(folder.iterdir())
    require(len(files)==10 and all(p.is_file() for p in files) and sum(p.stat().st_size for p in files)<=2*1024*1024,'native frame evidence missing/unbounded')
    r=json.loads((folder/'summary.json').read_text());require(r['schema']==1 and r['version']==VERSION and r['passed'] is True and r['failures']==[]
        and r['status']=='placement_verified' and r['qualified'] is False and r['experimental'] is True,'native frame placement failed')
    require(r['max_fps']==100 and r['old_max_fps']==r['restored_max_fps'] and r['body_callbacks']==256 and r['closing_anchor_callbacks']==8
        and r['buffer_bytes']==4096 and r['max_hash_updates']==8192,'native frame configuration/bounds changed')
    require(all(r[k] is None for k in ('cpu_service_usec','gpu_cost','physical_presentation','causal_probe_cost','shared_causal_overhead','render_signals','wait_service_usec')),
        'unmeasured frame costs promoted to passing zeros')
    build=r['build'];require(build['godot_commit']=='ed1daf0bf001b61586d9930840f2f1394092c079'
        and build['voxel_commit']=='2ac9f5f8a8219bf499314cc0fad54ffc47df908f'
        and build['native_source_key']=='11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d'
        and len(build['game_commit'])==40 and (expected_build is None or build==expected_build),'native frame build identity mismatch')
    require(len(r['trials'])==8 and len(r['groups'])==2,'native frame quartet missing')
    observations=[];prior_end=prior_engine=-1;rows_total=0;anchor_total=0;baseline=digest(8)
    for index,p in enumerate(r['trials']):
        require(p['index']==index and p['samples']==32 and p['completed'] is True and p['work_units_valid'] is True and p['operation_evaluation']=='unavailable'
            and p['raw_file']==f'cycle-{index}.jsonl' and p['render_signals'] is None and p['wait_service_usec'] is None,'native frame workload/phase fields changed')
        a=p['diagnostic_accounting'];start=number(a,'start_usec');end=number(a,'end_usec');anchor=p['closing_anchor'];rows=[]
        require(start>=prior_end and end-start==number(a,'elapsed_usec')>0 and end-start<=60000000,'native trial clocks reordered/unbounded')
        with (folder/p['raw_file']).open() as f:
            for line in f:
                rows.append(json.loads(line));require(len(rows)<=32,'native callback queue unbounded')
        require(len(rows)==32,'native final body/successor lost')
        previous=0;blocks=[];bn=bt=0;request=(500 if index<4 else 20000) if index%4 in (1,2) else 0
        for j,row in enumerate(rows):
            entry,begin,body_end,complete,nxt=(number(row,k) for k in ('entry_usec','body_begin_usec','body_end_usec','complete_callback_end_usec','next_entry_usec'))
            engine=number(row,'engine_frame');successor=number(row,'successor_engine_frame')
            tick=1800 if j>=28 else min(5,j*6//28)*300+1
            require(row['frame']==j+1 and row['tick']==tick and row['baseline_updates']==8 and row['baseline_sha256']==baseline
                and row['previous_callback_usec']==previous and row['requested_usec']==request and start<=entry<=begin<body_end<=complete<=nxt
                and successor==engine+1 and engine>prior_engine,'native cycle/order/body ownership changed')
            next_row=rows[j+1] if j<31 else anchor
            require(nxt==number(next_row,'entry_usec') and successor==number(next_row,'engine_frame'),'native successor does not own the following entry')
            if j==0:require(entry==p['first_entry_usec'],'first native anchor lost')
            if request:
                ds,de=(number(row,k) for k in ('dose_begin_usec','dose_end_usec'));updates=number(row,'hash_updates')
                require(begin<=ds<de<=body_end and request<=de-ds<=100000 and 1<=updates<=8192 and row['hash_sha256']==digest(updates),
                    'native dose placement/count/digest invalid')
            else:require(row['dose_begin_usec'] is None and row['dose_end_usec'] is None and row['hash_updates']==0 and row['hash_sha256'] is None,'null native performed dose')
            previous=complete-entry;prior_engine=engine;bn+=1;bt+=nxt-entry
            if bt>=5000000:blocks.append(dict(samples=bn,usec=bt));bn=bt=0
        ae,ac=(number(anchor,k) for k in ('entry_usec','complete_callback_end_usec'));b=p['phase_boundaries'];db,de=(number(b,k) for k in ('writer_drain_begin_usec','writer_drain_end_usec'))
        require(rows[-1]['next_entry_usec']==ae<ac<=db<=de<=end and b['callback_phase_closed_usec']==ac and anchor['previous_callback_usec']==previous
            and 'native_phase_closed_usec' not in b and p['native_operation_evidence'].startswith('unavailable:'),'actual anchor/drain/native unavailable scope changed')
        prior_engine=anchor['engine_frame'];bins=aggregate(rows);l=p['frame_slack_accounting']
        equal(l,dict(version=VERSION,invalid=False,stalled=any(x['next_entry_usec']-x['entry_usec']>250000 for x in rows),bins=bins,last_cycle=rows[-1]))
        callback=sum(x['complete_callback_end_usec']-x['entry_usec'] for x in rows)
        equal(a,dict(callbacks=32,callback_usec=callback,shared_usec=callback,switched_usec=0,switched_calls=0,last_switched_usec=0,
            last_callback_usec=previous,last_shared_usec=previous,last_callback_end_usec=rows[-1]['complete_callback_end_usec'],
            maximum_callback_usec=max(x['complete_callback_end_usec']-x['entry_usec'] for x in rows),finalization_usec=end-rows[-1]['complete_callback_end_usec'],
            writer_drain_usec=de-db,blocks=blocks,partial_block=dict(samples=bn,usec=bt),invalid_partition=False,overflow=False))
        total={k:sum(x[k] for x in bins) for k in TOTALS};require(total['cycle_usec']==ae-p['first_entry_usec']
            and total['body_usec']+total['callback_overhead_usec']+total['outside_callback_usec']==total['cycle_usec'],'native exclusive cycle partition changed')
        observations.append(dict(callbacks=32,**{k:total[k] for k in ('cycle_usec','body_usec','dose_usec')}));rows_total+=32;anchor_total+=1;prior_end=end
    for g,group in enumerate(r['groups']):
        obs=observations[g*4:g*4+4];require(group['kind']==('limiter_slack' if g==0 else 'beyond_limiter') and group['observations']==obs,'native frame groups reordered')
        equal(group['effects'],effects(obs))
    final=json.loads((folder/'report-finalization.json').read_text());require(prior_end<=final['start_usec']<=final['end_usec']
        and final['elapsed_usec']==final['end_usec']-final['start_usec'] and final['allocated_to_trials'] is False,'combined finalization missing/overlapped/allocated')
    require(len(r['unallocated_phase_gaps'])==8,'phase snapshot/controller gaps missing')
    for i,gap in enumerate(r['unallocated_phase_gaps']):
        begin=r['trials'][i]['diagnostic_accounting']['end_usec'];end=r['trials'][i+1]['diagnostic_accounting']['start_usec'] if i<7 else final['start_usec']
        equal(gap,dict(begin_usec=begin,end_usec=end,elapsed_usec=end-begin));require(end>=begin,'controller gap reordered')
    window=final['end_usec']-r['trials'][0]['diagnostic_accounting']['start_usec']
    require(window==sum(p['diagnostic_accounting']['elapsed_usec'] for p in r['trials'])+sum(g['elapsed_usec'] for g in r['unallocated_phase_gaps'])+final['elapsed_usec'],
        'complete probe lost phase/report costs')
    return dict(passed=True,body_callbacks=rows_total,closing_anchor_callbacks=anchor_total,native_hash_digests_verified=True,
        final_body_successors_verified=True,complete_probe_window_usec=window,unallocated_phase_gap_usec=sum(g['elapsed_usec'] for g in r['unallocated_phase_gaps']),
        groups=r['groups'],qualified=False,cpu_service_usec=None,shared_causal_overhead=None)
