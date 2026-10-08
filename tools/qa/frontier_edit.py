"""Independent saved native mesh/reference/edit/operation reconciliation.

One seam edit per case, at the public second route boundary. This checks
correctness and retains failed timing guards; it cannot qualify M1/hardware.
"""
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct

from frontier_boundary import cells, classification, require

MODES = ('stationary', 'handover', 'cancel-before', 'cancel-overlap')
CHAR_MODES = ('stationary', 'handover', 'cancel')
COUNTERS = ('accepted', 'submitted', 'superseded', 'cancelled', 'timeout', 'unavailable', 'pending', 'overflow', 'queued')
NULL_FIELDS = ('loaded', 'visible', 'has_mesh', 'mesh_id', 'mesh_viewers', 'collision_viewers',
               'queued_update', 'desired_revision', 'submitted_revision')
TARGETS = [[7, 0, 0], [8, 0, 0]]
OLD = [[8, -1, 0], [8, 0, 0], [8, -1, 1], [8, 0, 1]]
NEW = [[9, -1, 0], [9, 0, 0], [9, -1, 1], [9, 0, 1]]
COORDINATES = [TARGETS[0]] + OLD + NEW + [[7, 1, 0]]


def route_poses():
    # Integrate the actual command in IEEE single precision; do not translate
    # the old first-boundary pose by 16 m or reuse the production cell planner.
    single = lambda v: struct.unpack('<f', struct.pack('<f', v))[0]
    x, step, poses = single(10), single(Fraction(13, 120)), []
    for tick in range(1, 205):
        x = single(x + step)
        if tick in (203, 204):
            poses.append([x, single(1.65100002288818), single(10)])
    return poses


def stages(mode):
    result = ['prepared', 'edit-accepted', 'edit-dispatched', 'transfer-before-engine']
    if mode == 'cancel-overlap':
        return result + ['transfer-0']
    if mode.startswith('cancel'):
        return result
    return result + [f'transfer-{i}' for i in range(16)] + ['transfer-settled']


def unavailable(sample):
    require(sample['status'] == 'unavailable' and sample['blocks'] is None and sample['probe_usec'] is None
            and isinstance(sample['reason'], str) and bool(sample['reason']), 'Unavailable meshes became passing zeros')


def mesh_map(sample):
    require(sample['status'] == 'measured' and sample['reason'] == '' and type(sample['probe_usec']) in (int, float)
            and sample['probe_usec'] >= 0 and int(sample['probe_usec']) == sample['probe_usec'], 'Missing native mesh observation')
    require([r['block'] for r in sample['blocks']] == COORDINATES, 'Missing/reordered native block observations')
    result = {}
    for block in sample['blocks']:
        position = tuple(block['block'])
        require(block['state'] in ('missing', 'pending', 'hidden', 'visible', 'confirmed_empty'), 'Invalid native mesh state')
        if block['state'] == 'missing':
            require(all(block[k] is None for k in NULL_FIELDS), 'Missing block became zero revision/reference')
        else:
            for key in ('loaded', 'visible', 'has_mesh', 'queued_update'):
                require(type(block[key]) is bool, 'Missing mesh Boolean')
            require(all(type(block[k]) in (int, float) and int(block[k]) == block[k] and 0 <= block[k] <= 2
                        for k in ('mesh_viewers', 'collision_viewers')), 'Invalid native viewer references')
            for key in ('desired_revision', 'submitted_revision'):
                value = block[key]
                require(value is None or (type(value) in (int, float) and int(value) == value and value > 0), 'Invalid native revision')
            require(block['has_mesh'] == (type(block['mesh_id']) is str), 'Resource identity/geometry mismatch')
            if block['has_mesh']:
                require(block['mesh_id'].isdigit() and int(block['mesh_id']) > 0, 'Missing exact decimal mesh identity')
            if block['state'] in ('visible', 'confirmed_empty'):
                require(block['loaded'] and block['visible'] and block['mesh_viewers'] > 0 and block['submitted_revision'] is not None,
                        'Unsubmitted/hidden resource reported ready')
                require(block['has_mesh'] == (block['state'] == 'visible'), 'Confirmed-empty state changed')
        result[position] = block
    return result


def trace_counts(trace, enabled=None):
    require(all(type(trace[k]) in (int, float) and int(trace[k]) == trace[k] and trace[k] >= 0 for k in COUNTERS), 'Invalid edit counters')
    require(trace['accepted'] == 1 and trace['overflow'] == 0 and trace['pending_high_water'] == 1, 'Wrong edit admission/queue evidence')
    require(trace['accepted'] == sum(trace[k] for k in ('submitted', 'superseded', 'cancelled', 'timeout', 'unavailable', 'pending')), 'Edit outcome does not account for acceptance')
    require(trace['queued'] <= 1, 'Edit terminal queue exceeded one event')
    if enabled is not None:
        require(trace['enabled'] is enabled, 'Edit collection boundary mismatch')


def reconcile_operations(folder, summary):
    path = folder / 'operations.jsonl'
    require(0 < path.stat().st_size == summary['operation_bytes'] <= summary['operation_file_cap_bytes'] == 8388608,
            'Operation I/O byte count/bound mismatch')
    phases = [p for c in summary['cases'] for p in c['phases']]
    require([p['id'] for p in phases] == list(range(1, len(phases)+1)), 'Incomplete/reordered operation phases')
    groups = {int(p['id']): [] for p in phases}
    count, previous_phase, previous_frame = 0, 1, -1
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            require(0 < len(line.encode()) < 4096, 'Oversized operation row')
            row = json.loads(line)
            phase = int(row['phase'])
            require(phase in groups and previous_phase <= phase <= previous_phase+1, 'Missing/reordered operation rows')
            require(row['native_frame'] >= previous_frame, 'Native operation frame order changed')
            previous_frame = row['native_frame']
            previous_phase = phase
            groups[phase].append(row)
            count += 1
            require(count <= 20000, 'Operation row cap exceeded')
    require(count == summary['operation_rows'] and summary['operation_row_cap'] == 20000, 'Operation row count mismatch')
    failed = []
    previous_end = -1
    for phase in phases:
        rows, native = groups[int(phase['id'])], phase['native']
        require(rows and native['id'] == phase['id'] and native['frames'] == len(rows) and native['dropped_frames'] == 0
                and native['tracing'] is True, 'Incomplete native operation phase')
        require(rows[0]['start_usec'] >= previous_end and rows[0]['start_usec'] <= phase['begin_usec'] <= rows[0]['end_usec']
                and rows[-1]['end_usec'] <= phase['end_usec'], 'Phase closure boundary mismatch')
        if 'begin_before_usec' in phase:
            require(phase['begin_before_usec'] <= rows[0]['start_usec'] <= phase['begin_usec']
                    and phase['end_before_usec'] <= rows[-1]['end_usec'] <= phase['end_usec'], 'Phase clocks outside brackets')
        previous_end = rows[-1]['end_usec']
        for i, row in enumerate(rows):
            require(row['start_usec'] <= row['end_usec'] and row['phase_boundary'] is (i == len(rows)-1), 'Missing/extra terminal native row')
            if i:
                require(rows[i-1]['end_usec'] == row['start_usec'] and rows[i-1]['native_frame'] < row['native_frame'], 'Operation frame gap/reorder')
        for kind in ('upload', 'deletion'):
            values = [r[kind] for r in rows]
            for row, value in zip(rows, values):
                require(all(type(v) in (int, float) and int(v) == v and v >= 0 for v in value.values()), 'Invalid operation integers')
                if value['count']:
                    require(value['max_kind'] in ((1,) if kind == 'upload' else (2, 3))
                            and row['start_usec'] <= value['max_start_usec']
                            and value['max_start_usec'] + value['max_usec'] <= row['end_usec']
                            and value['max_usec'] <= value['usec'], 'Operation maximum outside its row')
                else:
                    require(all(v == 0 for v in value.values()), 'Empty operation became a measured nonzero')
            maximum = max(values, key=lambda v: v['max_usec'])
            # Native record keeps the first operation for a zero-duration tie.
            candidates = [v for v in values if v['count']]
            if candidates:
                maximum = max(candidates, key=lambda v: v['max_usec'])
            exact = {k: sum(v[k] for v in values) for k in ('count', 'bytes', 'usec')}
            exact.update({k: maximum[k] for k in ('max_usec', 'max_bytes', 'max_start_usec', 'max_kind')})
            require(native[kind] == exact, 'Phase aggregate differs from complete saved operation rows')
        require(native['peak_frame_operation_usec'] == max(r['upload']['usec']+r['deletion']['usec'] for r in rows)
                and native['peak_frame_upload_bytes'] == max(r['upload']['bytes'] for r in rows), 'Native frame peak mismatch')
        reasons = []
        if native['upload']['max_usec'] > 750:
            reasons.append('Individual upload exceeded 0.75 ms')
        if native['deletion']['max_usec'] > 750:
            reasons.append('Individual deletion exceeded 0.75 ms')
        require(phase['operation_failures'] == reasons and phase['operation_evaluation'] == ('failed' if reasons else 'passed'),
                '750 us operation guard suppressed or changed')
        if reasons:
            failed.append(phase['label'])
    return count, failed, hashlib.sha256(path.read_bytes()).hexdigest()


def reconcile(folder, build, *, characterization=False):
    path = folder / 'summary.json'
    require(0 < path.stat().st_size <= 1048576, 'Missing/oversized edit evidence')
    summary = json.loads(path.read_text())
    version = 'm1-frontier-edit-characterization-1' if characterization else 'm1-frontier-edit-1'
    modes = CHAR_MODES if characterization else MODES
    require(summary['schema'] == 1 and summary['version'] == version, 'Wrong edit replay schema/version')
    if characterization:
        require(summary['passed'] is False and summary['failures'] == ['Edit event accounting was incomplete', 'Pending edit cancellation failed'],
                'Characterization did not retain its actual failures')
    else:
        require(summary['passed'] is True and summary['failures'] == [], 'Failed/incomplete edit replay')
    require(summary['qualified'] is False and summary['target_performance'] == 'not_run' and summary['build'] == build, 'Wrong build or qualification')
    expected = [f'{mode}-{workers}' for workers in (1, 2) for mode in modes]
    require([c['name'] for c in summary['cases']] == expected, 'Missing/reordered seam controls')
    before, crossed = route_poses()
    count, handovers, submitted, cancellations = 0, [], [], []
    for case in summary['cases']:
        mode, workers = case['mode'], case['workers']
        cancellation = mode.startswith('cancel')
        require(case['name'] == f'{mode}-{workers}' and case['settled'] is True and case['concurrent'] is True
                and case['accepted'] is True and case['drained'] is True, 'Stalled/non-concurrent/incomplete seam workload')
        require(case['released_preparation_viewers'] == 4 and case['policy']['viewer_count'] == 4
                and case['policy']['required_visual_radius_m'] == 96 and case['policy']['data_radius_m'] == 128, 'Viewer workload changed')
        require([p['label'] for p in case['phases']] == [case['name']+':'+v for v in ('preparation', 'edit-transfer', 'retirement')], 'Phase accounting lost preparation/retirement')
        require([r['stage'] for r in case['rows']] == stages(mode), 'Missing/reordered seam observations')
        require(case['begin_usec'] < case['cleanup_begin_usec'] <= case['end_usec'], 'Seam lifetime boundaries changed')
        require(all(case['final_native'][k] == 0 for k in ('generation_jobs', 'mesh_jobs', 'result_jobs', 'main_jobs', 'retired_meshes')), 'Native work not drained')
        require(case['peaks']['resident_mesh'] <= 512 and case['peaks']['resident_data'] <= 8192
                and case['peaks']['retired_meshes'] <= 768 and case['peaks']['overloads'] == 0, 'Transient envelope exceeded')
        if not characterization:
            require(case['peaks']['retired_meshes'] <= case['peaks']['retired_high_water'] <= 768
                    and case['final_native']['retired_high_water'] <= case['peaks']['retired_high_water']
                    and case['final_native']['overloads'] == 0, 'Retirement high-water evidence lost or exceeded')
        previous, engine, observations = case['begin_usec'], -1, []
        for i, row in enumerate(case['rows']):
            require(previous <= row['usec'] <= case['cleanup_begin_usec'] and row['engine_frame'] >= engine, 'Seam row chronology changed')
            previous, engine = row['usec'], row['engine_frame']
            pose = before if i < 3 or mode == 'stationary' else crossed
            require(all(abs(a-b) < 1e-6 for a,b in zip(row['camera'], pose)) and row['yaw'] == -1.57079637050629, 'Public route pose changed')
            require(all(abs(a-b) < 1e-6 for a,b in zip(row['base_pose'], [pose[0], pose[1]-1.65, pose[2]])), 'Base/camera route changed')
            preparation_pose = before if i <= 4 or mode == 'stationary' else crossed
            require(row['preparation_cells'] == cells(preparation_pose), 'Preparation latch changed')
            outcome, clearance, transmittance = classification(row['sample'], summary['fog'])
            require(outcome == row['assessment']['evaluation'] == 'passed' and row['assessment']['status'] == 'measured'
                    and abs(row['assessment']['fog_clearance_m']-clearance) < 1e-8
                    and abs(row['assessment']['fog_transmittance']-transmittance) < 1e-12, 'Coverage failed or fog arithmetic changed')
            sample = row['sample']
            require(sample['empty_regions'] > 0, 'Confirmed-empty coverage not exercised')
            if sample['unready_regions']:
                box = sample['block']
                lo = [v*16 for v in box]; hi = [(v+1)*16 for v in box]
                lo[1] = max(-16, lo[1]); hi[1] = min(7, hi[1])
                distance = math.sqrt(sum(max(l-p, p-h, 0)**2 for l,p,h in zip(lo, pose, hi)))
                require(abs(distance-sample['frontier_distance_m']) < 1e-4, 'Native distance disagrees with independent box')
            require(row['original_targets_submitted'] == [True]*4 and row['terrain']['resident_mesh'] <= 512
                    and row['terrain']['resident_data'] <= 8192 and row['native']['retired_meshes'] <= 768
                    and row['native']['overloads'] == 0, 'Lost mesh coverage or resident bounds')
            if i:
                trace_counts(row['edit_trace'], enabled=True)
            if i in (1, 2, 3):
                require(row['edit_trace']['pending'] == 1, 'Concurrency interval lost accepted edit')
            if i == 2:
                require(row['terrain']['pending_mesh'] == 0 and row['engine_frame'] > case['rows'][1]['engine_frame'], 'Replacement not actually dispatched')
            if not characterization:
                observations.append(mesh_map(row['meshes']))
            count += 1
        trace, events = case['trace'], case['events']
        trace_counts(trace, enabled=False)
        require(trace['pending'] == 0 and trace['queued'] == (1 if characterization else 0) and len(events) == 1,
                'Missing or duplicate terminal edit event')
        event = events[0]
        require(event['id'] == 1 and event['voxel'] == [128, 6, 10]
                and [t['block'] for t in event['targets']] == TARGETS, 'Different seam edit/affected revisions')
        require(case['rows'][1]['usec'] >= event['accepted_usec'] >= case['rows'][0]['usec']
                and event['accepted_usec'] <= event['end_usec'] <= case['end_usec']
                and event['latency_usec'] == event['end_usec']-event['accepted_usec'] <= 200000,
                'Edit acknowledgement duration/boundary/guard changed')
        wanted = 'cancelled' if cancellation else 'submitted'
        allowed = ('cancelled', 'submitted') if cancellation and not characterization else (wanted,)
        if characterization and mode != 'stationary':
            allowed = ('superseded',)
        require(event['outcome'] in allowed, 'Accepted edit lost without a new edit')
        require(trace[event['outcome']] == 1 and case['edit_evaluation'] == ('failed' if characterization and mode != 'stationary' else 'passed'), 'Edit outcome failure hidden')
        require(all(t['revision'] > 0 and type(t['submitted']) is bool for t in event['targets']), 'Missing affected revision')
        if event['outcome'] == 'submitted':
            require(all(t['submitted'] for t in event['targets']) and trace['max_usec'] == event['latency_usec']
                    and trace['p95_upper_usec'] == (event['latency_usec']//1000+1)*1000,
                    'Incomplete exact revision acknowledgement')
            submitted.append(case['name'])
        if cancellation:
            cancellations.append({'case': case['name'], 'outcome': event['outcome']})
        if mode == 'handover':
            handovers.append({'case': case['name'], 'outcome': event['outcome'], 'edit_evaluation': case['edit_evaluation']})
        if not characterization:
            original, accepted = observations[:2]
            for position in map(tuple, [TARGETS[0]]+OLD+[[7, 1, 0]]):
                b = original[position]
                require(b['state'] in ('visible', 'confirmed_empty') and b['mesh_viewers'] == 1
                        and b['desired_revision'] == b['submitted_revision'] and not b['queued_update'], 'Preparation did not submit original resource')
            for target in event['targets']:
                position = tuple(target['block'])
                require(accepted[position]['desired_revision'] == target['revision'] > original[position]['desired_revision']
                        and accepted[position]['queued_update'] is True
                        and accepted[position]['submitted_revision'] == original[position]['submitted_revision']
                        and accepted[position]['mesh_id'] == original[position]['mesh_id'], 'Edit did not retain old mesh while queuing current revision')
                require(all(b[position]['desired_revision'] == target['revision'] for b in observations[1:]), 'Viewer handover advanced an accepted edit revision')
                if not cancellation:
                    final = observations[-1][position]
                    require(final['submitted_revision'] == target['revision'] and not final['queued_update']
                            and (final['mesh_id'] != original[position]['mesh_id'] if final['has_mesh'] or original[position]['has_mesh']
                                 else final['state'] == 'confirmed_empty'), 'Current edit resource not actually replaced')
            for position in map(tuple, [c for c in OLD if c not in TARGETS]+[[7, 1, 0]]):
                require(all(b[position]['mesh_id'] == original[position]['mesh_id']
                            and b[position]['desired_revision'] == b[position]['submitted_revision'] == original[position]['submitted_revision']
                            for b in observations), 'Unedited handover replaced or rescheduled an existing resource')
            for b in observations:
                for position in map(tuple, [TARGETS[0]]+OLD+[[7, 1, 0]]):
                    require(b[position]['loaded'] and b[position]['visible'] and b[position]['mesh_viewers'] >= 1
                            and b[position]['collision_viewers'] == 0, 'Viewer transfer lost a native visual reference')
            if mode == 'handover':
                for position in map(tuple, OLD):
                    refs = [b[position]['mesh_viewers'] for b in observations]
                    require(refs[0] == 1 and 2 in refs and refs[-1] == 1, 'No actual preparation/base reference overlap')
                require(all(observations[-1][tuple(c)]['state'] in ('visible', 'confirmed_empty')
                            and observations[-1][tuple(c)]['mesh_viewers'] == 1 for c in NEW), 'Next preparation column not actually submitted')
            if mode == 'stationary':
                require(all(b[tuple(c)]['mesh_viewers'] == 1 for b in observations for c in OLD), 'Stationary control changed viewer ownership')
            if mode == 'cancel-overlap':
                require(case['rows'][-1]['edit_trace']['pending'] == 1
                        and all(observations[-1][tuple(c)]['mesh_viewers'] == 2 for c in OLD), 'Cancellation did not exercise overlap with current edit pending')
            cancelled_map = mesh_map(case['cancellation_meshes'])
            require(all(cancelled_map[p]['mesh_id'] == observations[-1][p]['mesh_id']
                        and cancelled_map[p]['desired_revision'] == observations[-1][p]['desired_revision'] for p in cancelled_map), 'Queued deletion changed evidence before native cancellation')
            unavailable(case['drained_meshes'])
            trace_counts(case['before_trace_stop'], enabled=True)
            close = case['before_trace_stop']
            trace_counts(case['cancellation_trace'], enabled=True)
            require(case['cancellation_trace']['pending'] == int(cancellation), 'Cancellation request did not retain actual edit state')
            require(case['nodes_freed'] is True and case['trace_stop_usec'] <= case['trace_stop_end_usec'] <= case['end_usec'], 'Native cancellation/drain missing')
            if close['pending']:
                require(cancellation and close['pending'] == 1 and close['queued'] == 0 and event['outcome'] == 'cancelled'
                        and case['terminal_source'] == 'collection_stop'
                        and case['trace_stop_usec'] <= event['end_usec'] <= case['trace_stop_end_usec'], 'Collection close misclassified as native acknowledgement')
            else:
                require(case['terminal_source'] == 'native' and close['queued'] == 1
                        and all(close[k] == trace[k] for k in ('submitted','superseded','cancelled','timeout','unavailable'))
                        and event['end_usec'] <= case['trace_stop_usec'], 'Native terminal event changed during collection close')
                if cancellation:
                    require(event['end_usec'] >= case['cleanup_begin_usec'], 'Native cancellation completion predates actual request')
    require(count <= summary['row_cap'] == (128 if characterization else 160), 'Observation row cap changed')
    require(summary['missing_input']['status'] == 'unavailable' and summary['missing_input']['evaluation'] == 'inconclusive'
            and all(summary['missing_input'][k] is None for k in ('fog_clearance_m', 'fog_boundary_m', 'fog_transmittance')), 'Missing frontier became passing zero')
    if not characterization:
        controls = summary['sampler_controls']
        require(set(controls) == {'null_terrain', 'empty_request', 'oversized_request', 'malformed_request', 'duplicate_request', 'missing_block'}, 'Missing observer controls')
        for key, sample in controls.items():
            if key != 'missing_block':
                unavailable(sample)
        absent = controls['missing_block']
        require(absent['status'] == 'measured' and absent['blocks'][0]['block'] == [200, 0, 200]
                and absent['blocks'][0]['state'] == 'missing' and all(absent['blocks'][0][k] is None for k in NULL_FIELDS), 'Missing resident observation lost null semantics')
    operation_rows, failed, digest = reconcile_operations(folder, summary)
    if not characterization:
        for case in summary['cases']:
            require(case['operation_evaluation'] == ('failed' if any(p['label'] in failed for p in case['phases']) else 'passed'), 'Case operation failure hidden')
    return {'passed': True, 'version': version, 'cases': len(summary['cases']), 'native_rows': count,
            'mesh_observations': None if characterization else (count+len(summary['cases']))*len(COORDINATES),
            'operation_phases': len(summary['cases'])*3, 'operation_rows': operation_rows,
            'operation_sha256': digest, 'failed_operation_phases': failed, 'submitted': submitted,
            'cancellations': cancellations, 'handovers': handovers, 'qualified': False,
            'scope': 'second boundary + one concurrent seam edit per case; cloud correctness; not full route/HD 620'}
