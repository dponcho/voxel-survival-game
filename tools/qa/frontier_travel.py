"""Independent continuous H2 work/resource oracle. Timing failures are evidence.

No engine code is imported. Exact tick/edit/storage commands and float32 motion
are reconstructed; all native/frame/event terminal records remain in the audit.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import struct

from frontier_boundary import cells, require
from frontier_edit import mesh_map

TICKS = 600
ID = 'AB-H2-travel'
JOBS = ('generation_jobs', 'mesh_jobs', 'result_jobs', 'main_jobs', 'retired_meshes')
OUTCOMES = ('submitted', 'superseded', 'cancelled', 'timeout', 'unavailable')


def single(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def positions():
    x = single(10)
    result = [x]
    for _ in range(TICKS):
        x = single(x + single(6.5 / 60))
        result.append(x)
    return result


def coordinates(player):
    current = cells(player)
    return [[x-1, y, z] for x, y, z in current] + current + [[x, 0, 0] for x in (-1, 0, 1, 2, 3, 4)] + [[0, 1, 0]]


def operation_reasons(phase):
    return [f'Individual {kind} exceeded 0.75 ms' for kind in ('upload', 'deletion') if phase[kind]['max_usec'] > 750]


def operations(folder, saved, guards):
    phases = saved['operation_phases']
    require([p['id'] for p in phases] == [1, 2, 3]
            and [p['phase'] for p in phases] == ['preparation', 'overhead_diagnostic', 'retirement'], 'Missing/reordered native phases')
    require([g['id'] for g in guards] == [1, 2, 3], 'Missing phase guards')
    count, failed, previous_end = 0, [], -1
    for phase, guard in zip(phases, guards):
        path = folder / phase['raw_operations']
        require(0 < path.stat().st_size <= 67108864, 'Missing/oversized operation file')
        with path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            require(len(reader.fieldnames) == 18, 'Malformed operation schema')
            rows = [{k: int(v) for k, v in row.items()} for row in reader]
        count += len(rows)
        require(count <= 100000 and len(rows) == phase['frames'] and rows and phase['tracing']
                and phase['dropped_frames'] == 0, 'Incomplete native operation evidence')
        for index, row in enumerate(rows):
            require(row['phase'] == phase['id'] and row['start_usec'] >= previous_end
                    and row['end_usec'] >= row['start_usec']
                    and row['phase_boundary'] == int(index == len(rows)-1), 'Native phase terminal/order mismatch')
            if index:
                require(rows[index-1]['end_usec'] == row['start_usec']
                        and rows[index-1]['native_frame'] < row['native_frame'], 'Native frame gap/reorder')
            previous_end = row['end_usec']
        require(guard['phase'] == phase['phase'] and guard['close_before_usec'] <= previous_end <= guard['close_after_usec'],
                'Native close outside clock bracket')
        for kind in ('upload', 'deletion'):
            values = [{k: r[kind+'_'+k] for k in ('count', 'bytes', 'usec', 'max_usec', 'max_bytes', 'max_start_usec')}
                      for r in rows]
            for row, value in zip(rows, values):
                require(all(v >= 0 for v in value.values()), 'Negative operation evidence')
                if value['count']:
                    require(row['start_usec'] <= value['max_start_usec'] <= row['end_usec']-value['max_usec']
                            and value['max_usec'] <= value['usec'], 'Operation clock outside phase')
                else:
                    require(not any(value.values()), 'Empty operation became nonzero')
            candidates = [v for v in values if v['count']]
            largest = max(candidates or values, key=lambda v: v['max_usec'])
            for key in ('count', 'bytes', 'usec'):
                require(phase[kind][key] == sum(v[key] for v in values), 'Operation aggregate mismatch')
            for key in ('max_usec', 'max_bytes', 'max_start_usec'):
                require(phase[kind][key] == largest[key], 'Operation maximum/first tie mismatch')
            require(phase['native_end'][kind+'_usec']-phase['native_start'][kind+'_usec'] == phase[kind]['usec'],
                    'Phase/lifetime delta mismatch')
        require(phase['peak_frame_operation_usec'] == max(r['upload_usec']+r['deletion_usec'] for r in rows)
                and phase['peak_frame_upload_bytes'] == max(r['upload_bytes'] for r in rows), 'Operation peak mismatch')
        reasons = operation_reasons(phase)
        require(guard['failures'] == reasons, 'Failed operation guard suppressed')
        if reasons: failed.append({'phase': phase['phase'], 'reasons': reasons})
    return count, failed


def observations(path):
    require(0 < path.stat().st_size <= 33554432, 'Missing/oversized observations')
    expected_x = positions()
    ticks, accepted, rejected, fingerprint, previous_usec, last_tick = [], {}, 0, 0, -1, 0
    ownership, resources, boundaries, edited_resources = {}, {}, [], {}
    count, maximum_mesh, maximum_data, maximum_retired = 0, 0, 0, 0
    terminal = None
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            require(len(line.encode()) < 32768, 'Oversized observation row')
            row = json.loads(line)
            count += 1
            tick = row['tick']
            require(count <= 4096 and row['row'] == count and row['stage'] in ('physics', 'process')
                    and last_tick <= tick <= TICKS and previous_usec <= row['usec'], 'Observation order/tick/clock mismatch')
            last_tick, previous_usec = tick, row['usec']
            require(abs(row['player'][0]-expected_x[tick]) < 1e-6 and row['player'][2] == 10
                    and -14 < row['player'][1] <= 8 and row['readiness_stops'] == 0, 'Continuous route stalled or changed')
            target = single(10 + single(6.5*tick/60))
            require(abs(row['target'][0]-target) < 1e-6 and row['target'][1:] == [8, 10]
                    and row['yaw'] == single(-math.pi/2)
                    and abs(row['camera'][0]-row['player'][0]) < 1e-6
                    and abs(row['camera'][1]-single(row['player'][1]+single(1.65))) < 1e-6
                    and row['camera'][2] == 10, 'Camera/route target changed')
            require(row['actors'] == 24*tick and row['rain'] == 256
                    and abs(row['actor_phase']-tick/60) < 1e-10, 'Actor/rain work changed')
            require(row['saves'] == tick//60 and row['next_save'] == tick//60+1, 'Missing proxy storage command')
            mapping = mesh_map(row['meshes'], coordinates(row['player']))
            for cell in ((x, 0, 0) for x in (-1, 0, 1, 2, 3, 4)):
                block = mapping[cell]
                require(block['state'] in ('visible', 'confirmed_empty'), 'Edited resident lost submitted geometry')
                if cell in edited_resources:
                    old = edited_resources[cell]
                    changed = block['desired_revision'] != old['desired_revision']
                    require(not changed or (row['stage'] == 'physics' and row['edit_attempt'].get('accepted')
                            and list(cell) in [b['block'] for b in row['edit_attempt']['after']['blocks']]),
                            'Non-edit superseded an accepted revision')
                    if block['submitted_revision'] == old['submitted_revision']:
                        require(block['mesh_id'] == old['mesh_id'], 'Resource replaced without actual new submission')
                edited_resources[cell] = block
            trace = row['trace']
            require(trace['accepted'] == row['accepted'] == len(accepted)+(int(bool(row['edit_attempt']) and row['edit_attempt']['accepted']) if row['stage']=='physics' else 0)
                    and trace['accepted'] == sum(trace[k] for k in OUTCOMES)+trace['pending']
                    and trace['overflow'] == 0 and trace['pending_high_water'] <= 64 and trace['queued'] <= 128,
                    'Missing/overflowed edit accounting')
            if row['stage'] == 'physics':
                require(tick == len(ticks)+1, 'Missing or repeated physics tick')
                previous_accepted = len(accepted)
                fingerprint = (fingerprint*65599+tick+math.floor(target*1000+0.5)+(previous_accepted+1)*31+int(single(-math.pi/2)*1000)) & 0x7fffffff
                require(row['command_hash'] == fingerprint, 'Changed production command fingerprint')
                due = tick/60 >= (previous_accepted+1)/4
                attempt = row['edit_attempt']
                require(bool(attempt) == due, 'Due edit schedule skipped or added a command')
                if due:
                    voxel = [math.floor(row['player'][0]/32+0.5)*32, 6, 13]
                    coords = [[voxel[0]//16-1, 0, 0], [voxel[0]//16, 0, 0]]
                    before, after = mesh_map(attempt['before'], coords), mesh_map(attempt['after'], coords)
                    require(attempt['voxel'] == voxel and attempt['begin_usec'] <= attempt['end_usec'] <= row['usec'], 'Edit command/clock changed')
                    if attempt['accepted']:
                        for cell in map(tuple, coords):
                            require(after[cell]['desired_revision'] is not None
                                    and after[cell]['desired_revision'] > before[cell]['desired_revision'], 'Accepted edit lost its current revision')
                        accepted[previous_accepted+1] = dict(tick=tick, voxel=voxel, begin=attempt['begin_usec'], end=attempt['end_usec'],
                            revisions={cell: after[cell]['desired_revision'] for cell in map(tuple, coords)})
                    else: rejected += 1
                ticks.append(row)
            require(row['accepted'] == len(accepted) and row['rejected'] == rejected and row['next_edit'] == len(accepted)+1,
                    'Accepted/rejected work totals changed')
            if tick and tick % 15 == 0:
                require(row['accepted'] == tick//15, 'Required due edit did not finish its scheduled tick')
            for cell, block in mapping.items():
                if cell[0] in (7, 8, 9, 10) and cell[1] in (-1, 0):
                    ownership.setdefault(cell, set()).add(block['mesh_viewers'])
                    if block['state'] in ('visible', 'confirmed_empty'):
                        identity = (block['mesh_id'], block['desired_revision'], block['submitted_revision'])
                        if cell in resources: require(resources[cell] == identity, 'Unedited handover resource/revision changed')
                        resources[cell] = identity
                    # Once prepared, a handover may not lose submitted ownership.
                    if cell in resources:
                        require(block['state'] in ('visible', 'confirmed_empty') and block['mesh_viewers'] >= 1,
                                'Prepared handover lost submitted coverage')
            n, terrain = row['native'], row['terrain']
            require(n['overloads'] == 0 and n['retired_meshes'] <= n['retired_high_water'] <= 768
                    and terrain['resident_mesh'] <= 512 and terrain['resident_data'] <= 8192, 'Native resident/retirement envelope exceeded')
            maximum_mesh = max(maximum_mesh, terrain['resident_mesh'])
            maximum_data = max(maximum_data, terrain['resident_data'])
            maximum_retired = max(maximum_retired, n['retired_high_water'])
            terminal = row
    require(len(ticks) == TICKS and len(accepted) == 40 and rejected == 0 and terminal['tick'] == TICKS,
            'Incomplete continuous H2 workload')
    for column in (7, 8, 9, 10):
        group = [(column, y, z) for z in (0, 1) for y in (-1, 0)]
        require(all(ownership.get(cell, set()) >= {1, 2} for cell in group), 'Missing actual overlapping viewer ownership')
        boundaries.append(next(t['tick'] for t in ticks if t['player'][0] > (column-6)*16))
    require(boundaries == [56, 204, 351, 499], 'Continuous handovers did not reach both following columns')
    return dict(rows=count, ticks=ticks, edits=accepted, command_hash=fingerprint, terminal=terminal,
                handover_ticks=boundaries, resident_mesh=maximum_mesh, resident_data=maximum_data, retired_high_water=maximum_retired)


def reconcile(folder, build, workers):
    folder = Path(folder)
    meta = json.loads((folder/'travel-summary.json').read_text())
    saved = json.loads((folder/'summary.json').read_text())
    require(meta['version'] == 'm1-frontier-travel-1' and meta['passed'] is True and not meta['failures']
            and meta['qualified'] is False and meta['target_performance'] == 'not_run'
            and meta['build'] == saved['build'] == build and meta['drained'] is True
            and all(meta['final_native'][k] == 0 for k in JOBS), 'Failed/incomplete/unqualified-build travel evidence')
    require(meta['ticks'] == TICKS and meta['row_cap'] == 4096 and meta['byte_cap'] == 33554432,
            'Observation bounds changed')
    require(saved['completed'] and not saved['qualified'] and not saved['integration_failures']
            and saved['benchmark_mode'] == 'travel-replay' and len(saved['scenarios']) == 1, 'Incomplete production report')
    report = saved['scenarios'][0]
    c = report['workload_contract']
    for key, expected in dict(workload='H2', fixture=1, actors=24, edit_rate=4, rain_instances=256,
        autosave_interval_s=1, route_origin=[10,8,10], seconds=10, physics_hz=60, max_physics_steps=4,
        resolution=[1280,720], render_scale=1, render_block=16, workers=workers, visual_radius=96,
        data_radius=128, triangle_colliders=False, edit_trace=True, operation_trace=True, render_queries=True).items():
        require(c[key] == expected, 'Changed H2 contract: '+key)
    require(c['native_policy'] == dict(frame_usec=2000, frame_upload_bytes=1048576, single_upload_bytes=262144,
        terrain_jobs=64, mesh_results=16, mesh_result_bytes=33554432), 'Changed admission caps')
    require(report['id'] == ID and report['simulation_ticks'] == TICKS and report['actor_ticks'] == TICKS*24
            and report['accepted_proxy_edits'] == 40 and report['proxy_autosaves'] == 10
            and report['rejected_proxy_edits'] == report['readiness_stops'] == 0
            and report['completed'] and not report['qualified'], 'Missing production work')
    path = folder/'travel-observations.jsonl'
    obs = observations(path)
    require(meta['rows'] == obs['rows'] and meta['bytes'] == path.stat().st_size
            and report['workload_evidence']['command_hash'] == obs['command_hash'], 'Saved observation totals mismatch')
    events = [json.loads(line) for line in (folder/report['edit_visibility_events']).read_text().splitlines()]
    require(len(events) == 40 and sorted(e['id'] for e in events) == list(range(1,41)), 'Missing/duplicated terminal edit event')
    outcomes = {k: 0 for k in OUTCOMES}
    latencies = []
    for event in events:
        edit = obs['edits'][event['id']]
        require(event['voxel'] == edit['voxel'] and edit['begin'] <= event['accepted_usec'] <= edit['end']
                and event['latency_usec'] == event['end_usec']-event['accepted_usec'] >= 0, 'Edit acceptance/terminal clock mismatch')
        require({tuple(t['block']):t['revision'] for t in event['targets']} == edit['revisions'], 'Original accepted revisions changed')
        require(event['outcome'] in OUTCOMES, 'Invalid terminal outcome')
        outcomes[event['outcome']] += 1
        if event['outcome'] == 'submitted': latencies.append(event['latency_usec'])
        if event['outcome'] == 'submitted':
            require(all(t['submitted'] is True for t in event['targets']), 'Submitted event has unacknowledged targets')
            # A later edit can legitimately replace the same block. Find an
            # actual observation of each original submission before that edit.
            for cell, revision in edit['revisions'].items():
                witnessed = False
                for row in obs['ticks'] + [obs['terminal']]:
                    if row['usec'] < event['end_usec']: continue
                    block = next(b for b in row['meshes']['blocks'] if tuple(b['block']) == cell)
                    if block['submitted_revision'] == revision: witnessed = True; break
                require(witnessed, 'Acknowledgement lacks observed actual submitted revision')
    trace = report['edit_visibility']
    require(all(trace[k] == v for k,v in outcomes.items()) and trace['pending'] == trace['queued'] == trace['overflow'] == 0,
            'Edit terminal counters incomplete')
    latency_failed = bool(latencies) and (max(latencies) > 200000 or (sorted(latencies)[math.ceil(len(latencies)*.95)-1]//1000+1)*1000 > 100000)
    require(('Edit visibility exceeded the 100/200 ms limits' in report['reasons']) == latency_failed,
            'Edit duration guard suppressed')
    require(('Edit visibility has superseded, cancelled, timed-out or unavailable outcomes' in report['reasons']) == bool(40-outcomes['submitted']),
            'Failed edit outcomes suppressed')
    proxy = json.loads((folder/(ID+'-frames.csv.proxy.tmp')).read_text())
    require(proxy == dict(proxy_tick=600, accepted_edits=40, payload='x'*32768), 'Final proxy save mismatch')
    operation_rows, failed = operations(folder, saved, meta['phase_guards'])
    a = report['diagnostic_accounting']
    totals = {k:a['last_'+k] for k in ('callback_usec','shared_usec','switched_usec')}
    count, intervals, exposed, previous = 0, 0, 0, None
    with (folder/report['raw_frames']).open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            count += 1
            require(int(row['frame']) == count and int(row['diagnostic_frame']) == count-1, 'Frame/final callback order mismatch')
            now, interval = int(row['callback_usec']), round(float(row['interval_ms'])*1000)
            require(previous is None or now-previous == interval, 'Lost interval')
            require(now <= report['measurement_end_usec'] and float(row['simulation_s']) <= 10, 'Terminal frame outside measurement')
            previous, intervals = now, intervals+interval
            for key, column in [('callback_usec','diagnostic_usec'),('shared_usec','diagnostic_shared_usec'),('switched_usec','diagnostic_switched_usec')]:
                totals[key] += int(row[column])
            require(int(row['diagnostic_usec']) == int(row['diagnostic_shared_usec'])+int(row['diagnostic_switched_usec']), 'Callback partition mismatch')
            require(row['frontier_status'] == 'measured' and float(row['fog_boundary_m']) == 96, 'Unavailable coverage/fog changed')
            exposed += int(float(row['frontier_distance_m']) < 96)
    require(count == a['callbacks'] == report['samples'] and all(a[k] == v for k,v in totals.items())
            and abs(intervals-report['wall_seconds']*1e6) <= 1, 'Complete callbacks/intervals missing')
    require(a['shared_usec']+a['switched_usec'] == a['callback_usec'] and not a['overflow'] and not a['invalid_partition']
            and a['end_usec']-a['start_usec'] == a['elapsed_usec']
            and 0 <= a['writer_drain_usec'] <= a['finalization_usec'] == a['end_usec']-a['last_callback_end_usec'],
            'Complete diagnostic/finalization partition mismatch')
    require(report['fog_frontier']['exposed_samples'] == exposed
            and ('Required mesh coverage is unready before fog obscures it' in report['reasons']) == bool(exposed), 'Coverage failure hidden')
    final = json.loads((folder/'report-finalization.json').read_text())
    require(final['end_usec']-final['start_usec'] == final['elapsed_usec'] > 0
            and final['start_usec'] >= a['end_usec'], 'Missing combined finalization')
    return dict(passed=True, qualified=False, target_performance='not_run', workers=workers,
        ticks=TICKS, actor_ticks=TICKS*24, edits=outcomes, proxy_saves=10,
        handover_ticks=obs['handover_ticks'], observations=obs['rows'], observation_bytes=path.stat().st_size,
        observation_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), operation_rows=operation_rows,
        frame_rows=count, exposed_samples=exposed, failed_operation_phases=failed,
        edit_latency_failed=latency_failed, scenario_evaluation=report['evaluation'], reasons=report['reasons'],
        resident_mesh=obs['resident_mesh'], resident_data=obs['resident_data'], retired_high_water=obs['retired_high_water'])
