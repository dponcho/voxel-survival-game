"""Independent native pending-order oracle; no engine or production selector import."""
import hashlib
import json
import math
from pathlib import Path
import re

from frontier_boundary import require
from frontier_travel import reconcile as travel, single
from frontier_edit import mesh_map

CELLS = {(x, y, -1) for x in (7, 8, 9, 10) for y in (-1, 0)}


def revision(value, missing=False):
    if value is None:
        require(missing, 'Missing desired revision')
        return None
    require(isinstance(value, str) and re.fullmatch(r'[1-9][0-9]{0,19}', value)
            and int(value) <= 2**64-1, 'Inexact/invalid revision identity')
    return int(value)


def urgency(item, origin, side):
    x, y, z, flags, desired, submitted = item
    replacement = flags & 2 and flags & 4 and desired != submitted
    fresh = flags & 2 and not flags & 4
    category = 0 if replacement else 1 if fresh else 2
    # Closed-box nearest point is independent of the native gap formula.
    closest = [min(max(p, side*c), side*(c+1)) for c, p in zip((x,y,z), origin)]
    squared = sum((p-q)**2 for p,q in zip(origin, closest))
    return category, squared if category == 1 else 0


def verify_record(row, mode):
    require(row['valid'] is True and type(row['priority']) is bool and type(row['side']) is int and row['side'] == 16
            and type(row['phase']) is int and row['phase'] in (0,1,2,3), 'Unavailable/native phase mismatch')
    require(type(row['pending_count']) is int and 0 <= row['pending_count'] <= 512
            and isinstance(row['pending'], list) and len(row['pending']) == row['pending_count'], 'Missing/bounded pending vector')
    origin = row['origin']
    require(isinstance(origin,list) and len(origin) == 3 and all(type(p) in (int,float) and math.isfinite(p) and abs(p) < 4096 for p in origin), 'Unavailable origin')
    origin = [single(p) for p in origin] # Recover the actual float32 API inputs from serialized decimals.
    pending = []
    for raw in row['pending']:
        require(isinstance(raw,list) and len(raw) == 6 and all(type(v) is int for v in raw[:4]) and raw[3] & 1
                and 0 <= raw[3] <= 15, 'Invalid pending native block state')
        d, s = revision(raw[4]), revision(raw[5], missing=True)
        require(not raw[3] & 4 or s is not None, 'Loaded region lost actual submitted revision')
        pending.append([*raw[:4], d, s])
    require(len({tuple(c[:3]) for c in pending}) == len(pending), 'Duplicated pending request')
    require(not row['priority'] or (mode and row['phase'] == 2), 'Priority escaped the declared gameplay intervention')
    if mode and row['phase'] == 2 and pending:
        require(row['priority'] is True, 'Declared priority not applied to pending work')
    expected = sorted(range(len(pending)), key=lambda i:(*urgency(pending[i],origin,16),i)) if row['priority'] else list(range(len(pending)))
    require(isinstance(row['order'],list) and all(type(n) is int for n in row['order'])
            and row['order'] == expected, 'Selected order differs from independent priority/FIFO oracle')
    require(type(row['admitted']) is int and 0 <= row['admitted'] <= len(pending)
            and isinstance(row['loads'],list) and len(row['loads']) == row['admitted']
            and all(type(n) is int and 0 <= n < 4 for n in row['loads']), 'Four-task admission guard bypassed')
    require(type(row['jobs_before']) is int and type(row['jobs_after']) is int
            and row['jobs_before'] >= 0 and row['jobs_after'] >= 0, 'Missing native job measurement')
    require(type(row['start_usec']) is int and type(row['end_usec']) is int and type(row['decision_usec']) is int
            and row['start_usec'] >= 0 and 0 <= row['decision_usec'] <= row['end_usec']-row['start_usec'], 'Invalid native decision interval')
    chosen = expected[:row['admitted']]
    bypasses = []
    if not row['priority'] and row['phase'] == 2:
        for i,c in enumerate(pending):
            cell = tuple(c[:3])
            if cell not in CELLS or i in chosen or urgency(c,origin,16)[0] != 1: continue
            farther = [j for j in chosen if urgency(pending[j],origin,16)[0] == 1
                       and urgency(pending[j],origin,16)[1] > urgency(c,origin,16)[1]]
            if farther: bypasses.append(dict(block=list(cell),desired_revision=str(c[4]),row=row['row'],
                start_usec=row['start_usec'],queue_rank=i,closer_distance_squared=urgency(c,origin,16)[1],
                admitted_farther=[dict(block=pending[j][:3],rank=j,distance_squared=urgency(pending[j],origin,16)[1]) for j in farther]))
    return pending, chosen, bypasses


def lateral_boundaries(rows, admissions):
    """Join actual submission observations to admission and sampled entry bounds.

    Submission is a bracket, not an invented exact timestamp. A first inside
    observation that is ready alone cannot prove readiness before entry.
    """
    history = {c:dict(last_outside=None,first_inside=None,first_ready=None,last_unready=None) for c in admissions}
    for row in rows:
        coordinates = [b['block'] for b in row['lateral']['blocks']]
        for cell,block in mesh_map(row['lateral'],coordinates).items():
            if cell not in history: continue
            h, admitted = history[cell], admissions[cell]
            require(block['desired_revision'] is not None and int(block['desired_revision']) == int(admitted['desired_revision']),
                    'Lateral request changed revision between admission and observation')
            ready = block['state'] in ('visible','confirmed_empty')
            if ready:
                require(block['desired_revision'] == block['submitted_revision'], 'Stale lateral submission reported current')
            distance_squared = urgency([*cell,3,0,None],[single(p) for p in row['camera']],16)[1]
            item = dict(row=row['row'],tick=row['tick'],usec=row['usec'],state=block['state'],
                distance_squared=distance_squared,current=ready,mesh_id=block['mesh_id'],
                desired_revision=str(int(block['desired_revision'])),
                submitted_revision=str(int(block['submitted_revision'])) if block['submitted_revision'] is not None else None)
            if ready and h['first_ready'] is None:
                require(admitted['end_usec'] <= item['usec'], 'Submission observed before its actual admission')
                h['first_ready'] = dict(observation=item,
                    after_usec=max(admitted['end_usec'],h['last_unready']['usec'] if h['last_unready'] else admitted['end_usec']))
            if not ready and h['first_ready'] is None: h['last_unready'] = item
            if h['first_inside'] is None:
                if distance_squared < 96**2: h['first_inside'] = item
                else: h['last_outside'] = item
    result = []
    for cell,h in sorted(history.items()):
        require(h['first_inside'] is not None and h['last_outside'] is not None, 'Missing lateral entry observations')
        inside,outside,ready = h['first_inside'],h['last_outside'],h['first_ready']
        before = False if not inside['current'] else True if outside['current'] else None
        result.append(dict(block=list(cell),admission=admissions[cell],last_outside=outside,first_inside=inside,
            first_submission=ready,submitted_before_entry=before,
            submission_window_usec=None if ready is None else [ready['after_usec'],ready['observation']['usec']]))
    return result


def reconcile(folder, build, workers=1, priority=False):
    folder = Path(folder)
    t = travel(folder, build, workers)
    meta = json.loads((folder/'mesh-admission-summary.json').read_text())
    require(meta['version'] == 'm1-mesh-admission-1' and meta['passed'] is True and meta['qualified'] is False
            and meta['target_performance'] == 'not_run' and meta['build'] == build and meta['priority'] is priority
            and meta['row_cap'] == 4096 and meta['byte_cap'] == 33554432, 'Failed/missing admission report')
    snapshot = meta['snapshot']
    require(snapshot['enabled'] is True and snapshot['dropped'] == snapshot['queued'] == 0
            and snapshot['recorded'] == snapshot['popped'] == meta['rows'] and 0 < meta['rows'] <= 4096
            and 0 < snapshot['high_water'] <= 64 and snapshot['max_pending'] <= 512
            and snapshot['record_cap'] == 64 and snapshot['pending_cap'] == 512
            and 0 < snapshot['fixed_storage_bytes'] <= 2097152, 'Native trace overflow/missing records')
    saved = json.loads((folder/'summary.json').read_text())
    phases = {p['id']:p for p in saved['operation_phases']}
    # Native segments are independent of callback clocks; use their exact CSV endpoints.
    import csv
    windows = {}
    for pid,p in phases.items():
        with (folder/p['raw_operations']).open(encoding='utf-8-sig',newline='') as stream:
            rows = list(csv.DictReader(stream))
        windows[pid] = (int(rows[0]['start_usec']),int(rows[-1]['end_usec']))
    gaps = [(windows[1][1],windows[2][0]),(windows[2][1],windows[3][0]),
            (windows[3][1],meta['trace_finalization_begin_usec'])]
    path = folder/'mesh-admission.jsonl'
    require(0 < path.stat().st_size == meta['bytes'] <= 33554432, 'Missing/oversized admission file')
    count = maximum = decision_sum = decision_max = admissions = 0
    previous = -1
    initial = {}; bypasses = {}; priority_changes = gap_records = 0
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            require(len(line.encode()) < 65536, 'Oversized admission row')
            row = json.loads(line);count += 1
            require(count <= 4096 and row['row'] == count and row['start_usec'] >= previous, 'Lost/reordered/stalled native selection record')
            pending, chosen, skipped = verify_record(row,priority)
            previous = row['end_usec'];maximum = max(maximum,len(pending));admissions += len(chosen)
            decision_sum += row['decision_usec'];decision_max = max(decision_max,row['decision_usec'])
            brackets = [windows[row['phase']]] if row['phase'] else gaps
            require(any(lo <= row['start_usec'] <= row['end_usec'] <= hi for lo,hi in brackets), 'Admission escaped native phase/closure gap')
            gap_records += int(row['phase'] == 0)
            priority_changes += int(row['priority'] and row['order'] != list(range(len(pending))))
            for item in skipped: bypasses.setdefault(tuple(item['block']),item)
            if row['phase'] == 2:
                for rank in chosen:
                    c = pending[rank];cell = tuple(c[:3])
                    if cell in CELLS and not c[3] & 4:
                        initial.setdefault(cell,dict(block=list(cell),desired_revision=str(c[4]),row=count,
                            start_usec=row['start_usec'],end_usec=row['end_usec'],original_queue_rank=rank,
                            selected_rank=chosen.index(rank),origin=row['origin']))
    require(count == meta['rows'] and maximum == snapshot['max_pending'] and set(initial) == CELLS,
            'Missing original lateral admissions or native trace totals')
    if priority: require(priority_changes > 0,'Priority experiment did not change actual native selection')
    require(meta['trace_finalization_end_usec'] >= meta['trace_finalization_begin_usec'] >= previous,
            'Missing external admission trace finalization')
    with (folder/'travel-observations.jsonl').open(encoding='utf-8') as stream:
        boundaries = lateral_boundaries((json.loads(line) for line in stream),initial)
    return dict(passed=True,qualified=False,target_performance='not_run',priority=priority,travel=t,
        native_records=count,native_bytes=path.stat().st_size,native_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        max_pending=maximum,admitted=admissions,priority_changed_records=priority_changes,
        phase_closure_gap_records=gap_records,lateral_boundaries=boundaries,
        decision_usec=decision_sum,max_decision_usec=decision_max,
        first_lateral_admissions=[initial[c] for c in sorted(initial)],fifo_farther_before_closer=[bypasses[c] for c in sorted(bypasses)],
        lateral_coverage_resolved=t['exposed_samples']==t['lateral_exposed_observations']==0,
        shared_causal_overhead=None,per_frame_cpu_gpu_causal_cost=None)


def compare(fifo_folder, priority_folder, build, workers):
    fifo = reconcile(fifo_folder,build,workers,False)
    priority = reconcile(priority_folder,build,workers,True)
    summaries = [json.loads((Path(p)/'summary.json').read_text())['scenarios'][0] for p in (fifo_folder,priority_folder)]
    require(summaries[0]['workload_contract'] == summaries[1]['workload_contract']
            and summaries[0]['workload_evidence'] == summaries[1]['workload_evidence'], 'Admission comparison changed workload commands')
    demonstrated = bool(fifo['fifo_farther_before_closer']) and fifo['travel']['exposed_samples'] > 0
    return dict(passed=True,qualified=False,target_performance='not_run',workers=workers,
        fifo=fifo,priority=priority,matched_work=True,fifo_selection_limitation_demonstrated=demonstrated,
        closure_corrected=demonstrated and priority['lateral_coverage_resolved'],
        status='bounded coverage correction' if demonstrated and priority['lateral_coverage_resolved'] else 'coverage remains unresolved; retain failure and next cause')
