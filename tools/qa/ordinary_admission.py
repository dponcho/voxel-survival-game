"""Ordinary H2 comparison; no mesh-selection/resource observer is assumed."""
import csv
import json
import math
from pathlib import Path

from frontier_travel import single, positions, operations, retirement_guard, OUTCOMES
from frontier_boundary import require
from terrain_budget import reconcile_folder


def command_oracle():
    fingerprint = 0
    for tick in range(1,1201):
        target = single(10+single(13*tick/120))
        yaw = single(single(-math.pi/2)+math.pi) if tick >= 900 else single(-math.pi/2)
        fingerprint = (fingerprint*65599+tick+math.floor(target*1000+.5)+(1+(tick-1)//15)*31+int(yaw*1000)) & 0x7fffffff
    return fingerprint


def reconcile(folder, build, workers, priority):
    folder = Path(folder)
    saved = json.loads((folder/'summary.json').read_text(encoding='utf-8-sig'))
    meta = json.loads((folder/'ordinary-admission-summary.json').read_text(encoding='utf-8-sig'))
    require(meta['passed'] and not meta['qualified'] and meta['target_performance'] == 'not_run'
            and meta['priority'] is priority and meta['build'] == saved['build'] == build
            and saved['completed'] and not saved['qualified'] and not saved['integration_failures']
            and saved['benchmark_mode'] == 'ordinary-admission' and len(saved['scenarios']) == 1, 'Incomplete ordinary comparison')
    for key in ('admission_trace','replay_observation'):
        require(meta[key]['status'] == 'unavailable' and meta[key]['rows'] is None, 'Disabled observer became passing zeros')
    trace = meta['native_trace_state']
    require(trace['enabled'] is False and all(trace[k] == 0 for k in ('recorded','popped','dropped','queued','high_water','max_pending')),
            'Ordinary path unexpectedly traced admission')
    require(not (folder/'mesh-admission.jsonl').exists() and not (folder/'travel-observations.jsonl').exists(), 'Ordinary path emitted replay observation')
    require(meta['drained'] is True, 'Ordinary native work did not drain')
    retirement_guard(meta['final_native'],drained=True)
    report = saved['scenarios'][0]
    c = report['workload_contract']
    expected = dict(workload='H2',fixture=1,actors=24,edit_rate=4,rain_instances=256,autosave_interval_s=1,
        route_origin=[10,8,10],player_start=[10,8,10],seconds=20,physics_hz=60,max_physics_steps=4,
        resolution=[1280,720],render_scale=1,render_block=16,workers=workers,visual_radius=96,data_radius=128,
        camera_fov=75,camera_far=96,terrain_bounds=[-4096,-16,-4096,8192,48,8192],triangle_colliders=False,
        edit_trace=True,operation_trace=True,render_queries=True,admission_trace=False,replay_observation=False,
        admission_policy='priority' if priority else 'fifo')
    require(all(c[k] == v for k,v in expected.items()), 'Ordinary H2 workload configuration changed')
    require(c['native_policy'] == dict(frame_usec=2000,frame_upload_bytes=1048576,single_upload_bytes=262144,
        terrain_jobs=64,mesh_results=16,mesh_result_bytes=33554432)
        and c['frontier_preparation']['viewer_count'] == 4
        and c['fog'] == dict(enabled=True,mode='depth',density=1,height_density=0,begin_m=16,end_m=96,curve=1), 'Ordinary coverage/budgets changed')
    require(report['id'] == 'AB-H2-ordinary' and report['simulation_ticks'] == 1200 and report['actor_ticks'] == 28800
            and report['accepted_proxy_edits'] == 80 and report['proxy_autosaves'] == 20
            and report['rejected_proxy_edits'] == report['readiness_stops'] == 0
            and report['simulated_seconds'] == 20, 'Ordinary fixed workload lost work')
    e = report['workload_evidence']
    require(e['command_hash'] == command_oracle() and e['due_edits'] == 80
            and abs(e['player_end'][0]-positions(1200)[-1]) < 1e-6
            and -14 < e['player_end'][1] < 8 and e['player_end'][2] == 10, 'Ordinary motion/edit fingerprint changed')
    require([p['tick'] for p in e['route_checkpoints']] == [1,900,1200], 'Camera reversal checkpoints missing')
    for p in e['route_checkpoints']:
        yaw = single(single(-math.pi/2)+math.pi) if p['tick'] >= 900 else single(-math.pi/2)
        require(abs(p['yaw']-yaw) < 1e-12 and abs(p['target_x']-single(10+single(13*p['tick']/120))) < 1e-6, 'Original camera turn changed')
    event_path = folder/report['edit_visibility_events']
    require(0 < event_path.stat().st_size <= 8388608, 'Missing/oversized ordinary edit evidence')
    events = [json.loads(line) for line in event_path.read_text().splitlines()]
    require(len(events) == 80 and sorted(e['id'] for e in events) == list(range(1,81)), 'Missing ordinary original edit outcomes')
    outcomes = {k:0 for k in OUTCOMES}
    latencies, revisions = [], {}
    for event in sorted(events,key=lambda v:v['id']):
        tick = event['id']*15
        x = math.floor(positions(1200)[tick]/32+.5)*32
        require(event['voxel'] == [x,6,13] and event['outcome'] in outcomes
                and event['latency_usec'] == event['end_usec']-event['accepted_usec'] >= 0
                and event['end_usec'] <= report['measurement_end_usec'], 'Ordinary edit command/clock changed')
        require([t['block'] for t in event['targets']] == [[x//16-1,0,0],[x//16,0,0]], 'Original border edit targets changed')
        for target in event['targets']:
            cell = tuple(target['block'])
            require(target['revision'] > revisions.get(cell,0), 'Original edit revision reused')
            revisions[cell] = target['revision']
        outcomes[event['outcome']] += 1
        if event['outcome'] == 'submitted':
            require(all(t['submitted'] is True for t in event['targets']), 'Original revision did not submit')
            latencies.append(event['latency_usec'])
    t = report['edit_visibility']
    require(t['accepted'] == 80 and all(t[k] == v for k,v in outcomes.items())
            and t['pending'] == t['queued'] == t['overflow'] == 0, 'Ordinary edit outcome accounting incomplete')
    p95 = (sorted(latencies)[math.ceil(.95*len(latencies))-1]//1000+1)*1000 if latencies else 0
    require(t['max_usec'] == max(latencies,default=0) and t['p95_upper_usec'] == p95, 'Ordinary edit latency aggregate changed')
    require(json.loads((folder/'AB-H2-ordinary-frames.csv.proxy.tmp').read_text()) ==
            dict(proxy_tick=1200,accepted_edits=80,payload='x'*32768), 'Ordinary proxy save lost terminal work')
    count, failed = operations(folder,saved,meta['phase_guards'])
    terrain = reconcile_folder(folder,saved)
    frame_path = folder/report['raw_frames']
    require(0 < frame_path.stat().st_size <= 67108864, 'Missing/oversized ordinary frame evidence')
    with frame_path.open(encoding='utf-8-sig',newline='') as stream:
        frames = list(csv.DictReader(stream))
    require(frames and len(frames) == report['samples'] and len(frames) <= 100000, 'Ordinary frame evidence incomplete')
    intervals = exposed = 0
    a = report['diagnostic_accounting']
    totals = {k:a['last_'+k] for k in ('callback_usec','shared_usec','switched_usec')}
    previous = None
    for i,row in enumerate(frames,1):
        now, interval = int(row['callback_usec']),round(float(row['interval_ms'])*1000)
        require(int(row['frame']) == i and int(row['diagnostic_frame']) == i-1
                and (previous is None or now-previous == interval), 'Ordinary frame/final callback gap')
        previous = now; intervals += interval
        require(row['frontier_status'] == 'measured' and float(row['fog_boundary_m']) == 96, 'Required ordinary coverage unavailable')
        exposed += int(float(row['frontier_distance_m']) < 96)
        for key,column in [('callback_usec','diagnostic_usec'),('shared_usec','diagnostic_shared_usec'),('switched_usec','diagnostic_switched_usec')]:
            totals[key] += int(row[column])
        require(int(row['diagnostic_usec']) == int(row['diagnostic_shared_usec'])+int(row['diagnostic_switched_usec']), 'Ordinary callback partition mismatch')
    require(float(frames[-1]['simulation_s']) == 20 and all(a[k] == v for k,v in totals.items())
            and a['callbacks'] == len(frames) and abs(intervals-report['wall_seconds']*1e6) <= 1
            and a['last_callback_end_usec'] <= report['measurement_end_usec'] <= a['end_usec'], 'Ordinary terminal accounting missing')
    require(report['fog_frontier']['exposed_samples'] == exposed, 'Ordinary coverage alarms suppressed')
    require(('Required mesh coverage is unready before fog obscures it' in report['reasons']) == bool(exposed), 'Ordinary coverage guard suppressed')
    require(('Diagnostic callback wall time reached 1%; A/B qualification required' in report['reasons']) == (100*a['callback_usec'] >= intervals), 'Ordinary diagnostic guard suppressed')
    require(report['peaks']['resident_mesh'] <= 512 and report['peaks']['resident_data'] <= 8192, 'Ordinary resident cap exceeded')
    final = json.loads((folder/'report-finalization.json').read_text())
    require(final['end_usec']-final['start_usec'] == final['elapsed_usec'] > 0 and final['start_usec'] >= a['end_usec'], 'Ordinary finalization missing')
    ready = exposed == 0 and outcomes['submitted'] == 80 and t['max_usec'] <= 200000 and p95 <= 100000 and not failed
    return dict(passed=True,bounded_acceptance=ready,qualified=False,target_performance='not_run',priority=priority,
        coverage_alarms=exposed,edits=outcomes,edit_max_usec=t['max_usec'],edit_p95_upper_usec=p95,
        operation_rows=count,failed_operation_phases=failed,terrain=terrain,frame_rows=len(frames),
        scenario_evaluation=report['evaluation'],reasons=report['reasons'],
        admission_witnesses=None,resource_observations=None,causal_overhead=None)


def compare(fifo, priority, build, workers):
    result = dict(fifo=reconcile(fifo,build,workers,False),priority=reconcile(priority,build,workers,True))
    left = json.loads((Path(fifo)/'summary.json').read_text())['scenarios'][0]
    right = json.loads((Path(priority)/'summary.json').read_text())['scenarios'][0]
    a,b = left['workload_contract'].copy(),right['workload_contract'].copy()
    a.pop('admission_policy');b.pop('admission_policy')
    require(a == b and left['workload_evidence'] == right['workload_evidence'], 'FIFO/priority work not matched')
    return dict(passed=True,qualified=False,target_performance='not_run',workers=workers,**result)
