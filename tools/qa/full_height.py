"""Independent full-height demand, real movement, edits and complete-ledger audit."""
import csv
import copy
import json
import math
from pathlib import Path
import shutil
import tempfile

from frontier_boundary import require
from frontier_travel import single, operations, retirement_guard, OUTCOMES
from frontier_edit import mesh_map
from terrain_budget import reconcile_folder

TICKS = 4320
LEG_TICKS = 1440
ID = 'AB-H2-full-height'
BOUNDS = ((-4096,4096),(-64,192),(-4096,4096))
COORDINATES = [[0,1,0],[0,2,0],[5,1,0],[0,1,5]]
DIRECTIONS = ((1,0,0),(-1,0,0),(0,0,1))


def leg(tick):
    return min(2,max(0,tick-1)//LEG_TICKS)


def target(tick):
    # Closed-form rational distances, independent of runtime elapsed-time routing.
    if tick <= LEG_TICKS: return [single(10+single(13*tick/120)),72.0,10.0]
    if tick <= 2*LEG_TICKS: return [single(10+single(13*(2*LEG_TICKS-tick)/120)),72.0,10.0]
    return [10.0,72.0,single(10+single(13*(tick-2*LEG_TICKS)/120))]


def command_hash(tick, previous):
    p=target(tick)
    return (previous*65599+tick+math.floor(p[0]*1000+.5)
            +math.floor(p[2]*1000+.5)*31+leg(tick)*17)&0x7fffffff


def mesh_cells(pose, radius=96):
    # Enumerate block-box intersections rather than copying native span arithmetic.
    intervals=[(max(lo,p-radius),min(hi,p+radius)) for p,(lo,hi) in zip(pose,BOUNDS)]
    result=set()
    for z in range(math.floor(intervals[2][0]/32)-1,math.ceil(intervals[2][1]/32)+1):
        for y in range(math.floor(intervals[1][0]/32)-1,math.ceil(intervals[1][1]/32)+1):
            for x in range(math.floor(intervals[0][0]/32)-1,math.ceil(intervals[0][1]/32)+1):
                if all(max(c*32,lo)<min((c+1)*32,hi) for c,(lo,hi) in zip((x,y,z),intervals)):
                    result.add((x,y,z))
    return result


def edit_position(tick):
    p=target(tick)
    return [math.floor(p[0]/32+.5)*32,70,math.floor(p[2]/32+.5)*32+13]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def observations(path, enabled):
    require(0<path.stat().st_size<=16777216,'Missing/oversized full-height observations')
    values=[json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines()]
    require(len(values)==TICKS+2 and [r['row'] for r in values]==list(range(1,TICKS+3)),
            'Missing/reordered full-height observations')
    require(values[0]['stage']=='prepared' and values[-1]['stage']=='terminal'
            and all(r['stage']=='physics' for r in values[1:-1]),'Full-height observation stages changed')
    poses={0:[10,72,10]}; previous_usec=-1; fingerprint=0; origin_value=0
    ready_before=mesh_missing=data_missing=mesh_returned=data_returned=False
    peak_mesh=peak_data=peak_retired=0
    for index,row in enumerate(values):
        tick=0 if index==0 else min(index,TICKS)
        require(row['tick']==tick and row['leg']==leg(tick) and row['usec']>=previous_usec,
                'Full-height tick/leg/clock changed')
        previous_usec=row['usec']; p=row['player']; goal=target(tick)
        require(all(abs(a-b)<.01 for a,b in zip((p[0],p[2]),(goal[0],goal[2])))
                and 63.99<=p[1]<=72.01,'Full-height actual movement stalled, reversed incorrectly or clipped')
        if row['stage']=='physics':
            fingerprint=command_hash(tick,fingerprint)
            if tick%15==0 and edit_position(tick)==[0,70,13]: origin_value=2 if origin_value==0 else 0
        require(row['command_hash']==fingerprint and row['actors']==24*tick
                and row['accepted']==tick//15 and row['rejected']==row['readiness_stops']==0
                and row['saves']==tick//60,'Full-height route/work/command fingerprint changed')
        require(row['target']==goal and abs(row['yaw']-single((-math.pi/2,math.pi/2,math.pi)[leg(tick)]))<1e-12
                and abs(row['camera'][0]-p[0])<1e-7 and abs(row['camera'][2]-p[2])<1e-7
                and abs(row['camera'][1]-single(p[1]+single(1.65)))<1e-7,'Full-height camera/target changed')
        poses[tick]=p
        prep=row['preparation']; centers=prep['positions']
        require(len(centers)==int(enabled),'Full-height preparation viewer count changed')
        if enabled:
            source,decision=prep['source_tick'],prep['decision_tick']
            require(0<=source<=decision<=tick and tick-source<=8 and source in poses
                    and prep['source_player']==poses[source] and prep['direction']==leg(min(TICKS,decision+1)),
                    'Preparation lost its bounded process handover or movement direction')
            expected=[single(v+32*d) for v,d in zip(poses[source],DIRECTIONS[prep['direction']])]
            require(centers==[expected],'Full-height preparation moved outside its declared demand')
        terrain,native=row['terrain'],row['native']
        require(0<terrain['resident_mesh']<=(448 if enabled else 343) and 0<terrain['resident_data']<=8192,
                'Full-height resident envelope exceeded')
        require(native['generation_jobs']+native['mesh_jobs']<=64 and native['result_jobs']<=16,
                'Full-height native queue envelope exceeded')
        retirement_guard(native)
        peak_mesh=max(peak_mesh,terrain['resident_mesh']);peak_data=max(peak_data,terrain['resident_data'])
        peak_retired=max(peak_retired,native['retired_meshes'])
        meshes=mesh_map(row['meshes'],COORDINATES)
        require(all(b['collision_viewers'] in (0,None) for b in meshes.values()),'Full-height collision mesh owner appeared')
        ground=meshes[(0,1,0)]
        if tick==0: ready_before=ground['loaded'] is True
        if leg(tick)==0 and ground['state']=='missing': mesh_missing=True
        if leg(tick)==1 and mesh_missing and ground['loaded'] is True: mesh_returned=True
        if row['origin_data_ready']:
            require(row['origin_value']==origin_value,'Full-height edit overlay changed across data reload')
            if leg(tick)==1 and data_missing: data_returned=True
        else:
            require(row['origin_value'] is None,'Missing full-height data was read as air')
            if leg(tick)==0: data_missing=True
    prepared=values[0];cells=mesh_cells(prepared['player'])
    require(len(cells)==343,'Full-height preparation was clipped into a slab')
    for center in prepared['preparation']['positions']:cells|=mesh_cells(center)
    require(prepared['terrain']['resident_mesh']==len(cells)==(392 if enabled else 343)
            and prepared['visual_area_ready'] is True and prepared['data_area_ready'] is True
            and prepared['preparation_area_ready'] is (True if enabled else None),
            'Full-height complete initial demand did not settle')
    require(prepared['vertical_voxels']==[[-64,1],[-32,1],[40,1],[63,2],[64,0],[191,0]],
            'Full-height native generator was replaced by the old slab')
    require(ready_before and mesh_missing and data_missing and mesh_returned and data_returned,
            'Full-height route did not evict and reload edited data/mesh')
    return dict(rows=len(values),command_hash=fingerprint,first_usec=values[0]['usec'],last_usec=values[-1]['usec'],
                peak_mesh=peak_mesh,peak_data=peak_data,
                peak_retired=peak_retired,initial_regions=len(cells),data_evicted_and_reloaded=True,
                mesh_evicted_and_reloaded=True,terminal_player=values[-1]['player'])


def reconcile(folder,build,enabled):
    folder=Path(folder);s=read(folder/'summary.json');m=read(folder/'full-height-summary.json')
    require(m['version']=='m1-full-height-1' and m['passed'] is True and not m['qualified']
            and m['target_performance']=='not_run' and m['preparation_enabled'] is enabled
            and m['priority'] is True and m['build']==s['build']==build and s['completed']
            and not s['qualified'] and not s['integration_failures'] and s['benchmark_mode']=='full-height'
            and s['configuration']['fixture_y']==[-64,192] and len(s['scenarios'])==1,
            'Incomplete full-height experiment')
    trace=m['native_trace_state']
    require(trace['enabled'] is False and all(trace[k]==0 for k in ('recorded','popped','dropped','queued','high_water','max_pending')),
            'Full-height experiment unexpectedly enabled admission tracing')
    require(m['drained'] is True,'Full-height native drain failed');retirement_guard(m['final_native'],drained=True)
    r=s['scenarios'][0];c=r['workload_contract']
    expected=dict(version='m1-full-height-1',fixture=3,workload='H2',actors=24,edit_rate=4,rain_instances=256,
        autosave_interval_s=1,route_origin=[10,72,10],player_start=[10,72,10],seconds=72,physics_hz=60,
        max_physics_steps=4,resolution=[1280,720],render_scale=1,render_block=32,workers=1,
        visual_radius=96,data_radius=128,terrain_bounds=[-4096,-64,-4096,8192,256,8192],triangle_colliders=False,
        camera_fov=75,camera_far=96,admission_policy='priority',admission_trace=False,edit_trace=True,
        operation_trace=True,render_queries=True,full_height_observation=True)
    require(all(c[k]==v for k,v in expected.items()),'Full-height workload configuration changed')
    require(c['native_policy']==dict(frame_usec=2000,frame_upload_bytes=1048576,single_upload_bytes=262144,
        terrain_jobs=64,mesh_results=16,mesh_result_bytes=33554432)
        and c['fog']==dict(enabled=True,mode='depth',density=1,height_density=0,begin_m=16,end_m=96,curve=1),
        'Full-height safety or fog budgets changed')
    prep=c['frontier_preparation']
    require(prep==dict(version='m1-directional-32-1',enabled=enabled,viewer_count=int(enabled),viewer_radius_m=96,
        lead_m=32,required_visual_radius_m=96,data_radius_m=128,handover='previous process pose; next movement leg',
        resident_mesh_bound=448 if enabled else 343,
        data_scope='128 m base data viewer plus measured mesh halo/preparation union'),'Full-height preparation policy changed')
    require(r['id']==ID and r['simulation_ticks']==TICKS and r['simulated_seconds']==72 and r['actor_ticks']==103680
            and r['accepted_proxy_edits']==288 and r['proxy_autosaves']==72
            and r['rejected_proxy_edits']==r['readiness_stops']==0 and r['workload_evidence']['due_edits']==288,
            'Full-height fixed work lost commands')
    path=folder/'full-height-observations.jsonl';obs=observations(path,enabled)
    require(m['rows']==obs['rows']==m['row_cap']==TICKS+2 and m['bytes']==path.stat().st_size
            and m['byte_cap']==16777216 and m['distinct_edit_positions']==11,
            'Full-height observation I/O or edit bound mismatch')
    events=[json.loads(line) for line in (folder/r['edit_visibility_events']).read_text().splitlines()]
    require(len(events)==288 and sorted(e['id'] for e in events)==list(range(1,289)),
            'Full-height original edit outcomes missing')
    outcomes={k:0 for k in OUTCOMES};latencies=[];revisions={}
    for e in sorted(events,key=lambda e:e['id']):
        position=edit_position(e['id']*15);x,y,z=position
        require(e['voxel']==position and e['outcome'] in outcomes
                and e['latency_usec']==e['end_usec']-e['accepted_usec']>=0
                and e['end_usec']<=r['measurement_end_usec'],'Full-height edit command/clock changed')
        require([v['block'] for v in e['targets']]==[[x//32-1,y//32,z//32],[x//32,y//32,z//32]],
                'Full-height border-edit targets changed')
        for v in e['targets']:
            cell=tuple(v['block']);require(v['revision']>revisions.get(cell,0),'Full-height original edit revision reused')
            revisions[cell]=v['revision']
        outcomes[e['outcome']]+=1
        if e['outcome']=='submitted':
            require(all(v['submitted'] is True for v in e['targets']),'Full-height edit never submitted its current revision')
            latencies.append(e['latency_usec'])
    edit=r['edit_visibility'];p95=(sorted(latencies)[math.ceil(.95*len(latencies))-1]//1000+1)*1000 if latencies else 0
    require(edit['accepted']==288 and all(edit[k]==v for k,v in outcomes.items()) and edit['enabled'] is False
            and edit['pending']==edit['queued']==edit['overflow']==0 and edit['max_usec']==max(latencies,default=0)
            and edit['p95_upper_usec']==p95,'Full-height terminal edit totals disagree')
    require(('Edit visibility has superseded, cancelled, timed-out or unavailable outcomes' in r['reasons'])
            ==(outcomes['submitted']!=288),'Full-height failed edit outcomes suppressed')
    require(('Edit visibility exceeded the 100/200 ms limits' in r['reasons'])
            ==bool(latencies and (p95>100000 or max(latencies)>200000)),
            'Full-height edit latency failure suppressed')
    require(read(folder/(ID+'-frames.csv.proxy.tmp'))==dict(proxy_tick=TICKS,accepted_edits=288,payload='x'*32768),
            'Full-height terminal proxy save missing')
    count,failed=operations(folder,s,m['phase_guards']);terrain=reconcile_folder(folder,s)
    with (folder/r['raw_frames']).open(encoding='utf-8-sig',newline='') as f:frames=list(csv.DictReader(f))
    require(0<len(frames)==r['samples']<=100000,'Full-height raw frames incomplete')
    a=r['diagnostic_accounting'];totals={k:a['last_'+k] for k in ('callback_usec','shared_usec','switched_usec')}
    intervals=exposed=0;previous=None;coverage_by_leg=[0,0,0]
    for index,row in enumerate(frames,1):
        now=int(row['callback_usec']);span=round(float(row['interval_ms'])*1000)
        require(int(row['frame'])==index and int(row['diagnostic_frame'])==index-1
                and (previous is None or now-previous==span),'Full-height raw callback gap')
        previous=now;intervals+=span
        require(row['frontier_status']=='measured' and float(row['fog_boundary_m'])==96,
                'Full-height required coverage unavailable')
        alarm=float(row['frontier_distance_m'])<96;exposed+=alarm
        coverage_by_leg[leg(round(float(row['simulation_s'])*60))]+=alarm
        for key,col in (('callback_usec','diagnostic_usec'),('shared_usec','diagnostic_shared_usec'),('switched_usec','diagnostic_switched_usec')):
            totals[key]+=int(row[col])
        require(int(row['diagnostic_usec'])==int(row['diagnostic_shared_usec'])+int(row['diagnostic_switched_usec']),
                'Full-height callback partition changed')
    require(float(frames[-1]['simulation_s'])==72 and a['callbacks']==len(frames)
            and all(a[k]==v for k,v in totals.items()) and abs(intervals-r['wall_seconds']*1e6)<=1
            and a['last_callback_end_usec']<=r['measurement_end_usec']<=a['end_usec'],
            'Full-height terminal callback/finalization missing')
    require(a['start_usec']<=obs['first_usec']<=obs['last_usec']<=r['measurement_end_usec']
            and obs['terminal_player']==r['workload_evidence']['player_end'],
            'Full-height observations disagree with complete measurement boundary')
    require(r['fog_frontier']['exposed_samples']==exposed
            and ('Required mesh coverage is unready before fog obscures it' in r['reasons'])==bool(exposed),
            'Full-height coverage failure suppressed')
    require(('Diagnostic callback wall time reached 1%; A/B qualification required' in r['reasons'])==(100*a['callback_usec']>=intervals),
            'Full-height diagnostic failure suppressed')
    final=read(folder/'report-finalization.json');closing=m['observer_finalization']
    require(final['start_usec']<=closing['start_usec']<=closing['end_usec']<=final['end_usec']
            and final['end_usec']-final['start_usec']==final['elapsed_usec']>0 and final['start_usec']>=a['end_usec'],
            'Full-height observer finalization outside complete timing boundary')
    ready=exposed==0 and outcomes['submitted']==288 and p95<=100000 and edit['max_usec']<=200000 and not failed
    return dict(passed=True,qualified=False,target_performance='not_run',preparation_enabled=enabled,
        bounded_acceptance=ready,coverage_alarms=exposed,coverage_by_leg=coverage_by_leg,edits=outcomes,
        edit_p95_upper_usec=p95,edit_max_usec=edit['max_usec'],operation_rows=count,failed_operation_phases=failed,
        terrain=terrain,frame_rows=len(frames),observation=obs,scenario_evaluation=r['evaluation'],reasons=r['reasons'])


def compare(baseline,prepared,build):
    result=dict(baseline=reconcile(baseline,build,False),prepared=reconcile(prepared,build,True))
    left=read(Path(baseline)/'summary.json')['scenarios'][0]
    right=read(Path(prepared)/'summary.json')['scenarios'][0]
    a,b=left['workload_contract'].copy(),right['workload_contract'].copy()
    a.pop('frontier_preparation');b.pop('frontier_preparation')
    require(a==b and left['workload_evidence']==right['workload_evidence'],'Full-height comparison lost matched work')
    return dict(passed=True,qualified=False,target_performance='not_run',**result)


def mutations(folder,build):
    """Twelve corruptions of actual saved evidence; no engine or invented clocks."""
    faults=('missing','truncated','camera-only','slab','preparation','missing-as-air',
            'reload','terminal-work','failed','budget','phase-guard','final-callback')
    rejected={}
    for fault in faults:
        with tempfile.TemporaryDirectory(prefix='cairn-full-height-mutation-') as tmp:
            d=Path(tmp);shutil.copytree(folder,d,dirs_exist_ok=True)
            p=d/'full-height-observations.jsonl';m=read(d/'full-height-summary.json');s=read(d/'summary.json')
            rows=[json.loads(line) for line in p.read_text().splitlines()]
            if fault=='missing':p.unlink()
            elif fault in ('truncated','camera-only','slab','preparation','missing-as-air','reload','terminal-work'):
                if fault=='truncated':rows.pop()
                elif fault=='camera-only':rows[1441]['player'][0]=rows[1440]['player'][0]
                elif fault=='slab':rows[0]['vertical_voxels'][0][1]=0
                elif fault=='preparation':rows[100]['preparation']['positions'][0][0]+=32
                elif fault=='missing-as-air':next(r for r in rows if not r['origin_data_ready'])['origin_value']=0
                elif fault=='reload':next(r for r in rows[1441:] if r['origin_data_ready'])['origin_value']=7
                else:rows[-1]['accepted']-=1
                p.write_text(''.join(json.dumps(row)+'\n' for row in rows));m['bytes']=p.stat().st_size
            elif fault=='failed':m['passed']=False
            elif fault=='budget':s['scenarios'][0]['workload_contract']['native_policy']['frame_usec']=3000
            elif fault=='phase-guard':m['phase_guards'][0]['failures']=['fabricated guard']
            elif fault=='final-callback':s['scenarios'][0]['diagnostic_accounting']['last_callback_usec']+=1
            (d/'full-height-summary.json').write_text(json.dumps(m));(d/'summary.json').write_text(json.dumps(s))
            try:reconcile(d,build,True)
            except (RuntimeError,ValueError,TypeError,KeyError,OSError) as error:rejected[fault]=str(error)
            else:raise RuntimeError('Full-height saved mutation accepted: '+fault)
    return dict(passed=True,count=len(rejected),all_rejected=True,reasons=rejected)
