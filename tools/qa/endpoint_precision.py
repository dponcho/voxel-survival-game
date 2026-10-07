"""Cloud-only precision characterization; exact aggregates plus streamed saved clocks.

No successor classification: the existing production route verdict is reconciled.
Raw files are bounded and all terminal rows and overlapping scopes are retained.
"""
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

from route_calibration import ORDER, assess, compare, require, reconcile_decision, scope, variation

LABELS = ('null', 'positive', 'endpoint', 'ack-duration', 'count-mask', 'count-drift',
          'missing', 'reordered', 'stall', 'failed-workload', 'failed-operation',
          'unavailable', 'io-failed', 'dose-overlap')
HEADER = ('frame,tick,interval_usec,entry_usec,callback_begin_usec,callback_end_usec,'
          'previous_frame,previous_callback_usec,previous_shared_usec,previous_switched_usec,'
          'callback_write_usec,ledger_tail_usec').split(',')
MAX_REPORT = 1024 * 1024
MAX_RAW = 32 * 1024 * 1024


def cost_sum(n):
    cycles, remainder = divmod(n, 7)
    return n * 30 + cycles * 21 + remainder * (remainder + 1) // 2


def model(label, index):
    """Closed-form counts/durations. Does not expand the event loop or use saved bins."""
    extra = 5 if (label == 'count-mask' and index in (1, 2)) or (label == 'count-drift' and index == 3) else 0
    counts = [250 + extra] * 6 + [0 if label == 'unavailable' else 4]
    durations = [5000000] * 6 + [0 if label == 'unavailable' else 20000]
    if label == 'endpoint' and index in (2, 3):
        durations[5] -= 500
        durations[6] += 500
    if label == 'ack-duration' and index in (2, 3): durations[6] += 500
    if label == 'stall' and index == 1: durations[0] += 300000
    n = sum(counts)
    callback_end = 1000200 + sum(durations) + 7 + 30 + n % 7
    dose = 0 if label == 'null' or index not in (1, 2) else 600000
    end = callback_end + 2 + 1000 + dose
    return dict(counts=counts, durations=durations, n=n, callback_end=callback_end,
                dose=dose, end=end, elapsed=end-1000000)


def characterize(phases):
    """Descriptive ratios, never eligibility/qualification or a replacement estimator."""
    a = [p['diagnostic_accounting'] for p in phases]
    bins = [p['route_calibration']['bins'] for p in phases]
    mean = [Fraction(int(x['elapsed_usec']), int(x['callbacks'])) for x in a]
    # Exact identity separates whole-window duration from sample-count effects.
    ratios = []
    for ref, pos in ((0, 1), (3, 2)):
        duration = Fraction(int(a[pos]['elapsed_usec']), int(a[ref]['elapsed_usec']))
        count = Fraction(int(a[pos]['callbacks']), int(a[ref]['callbacks']))
        ratios.append(dict(duration_added_fraction=float(duration-1), callback_count_added_fraction=float(count-1),
                           mean_added_fraction=float(duration/count-1)))
    terminal = []
    for left, right in ((0, 3), (1, 2)):
        x, y = bins[left][6], bins[right][6]
        drift = variation([Fraction(int(x['usec']), int(x['samples'])), Fraction(int(y['usec']), int(y['samples']))]) if x['samples'] and y['samples'] else None
        delta = int(y['usec'])-int(x['usec']) if drift is not None else None
        elapsed_delta = int(a[right]['elapsed_usec'])-int(a[left]['elapsed_usec'])
        terminal.append(dict(section_mean_variation=float(drift) if drift is not None else None,
                             terminal_interval_delta_usec=delta, complete_window_delta_usec=elapsed_delta,
                             unscaled_terminal_delta_fraction=float(Fraction(delta, int(a[left]['elapsed_usec']))) if delta is not None else None,
                             complete_mean_variation=float(variation([mean[left], mean[right]]))))
    return dict(scope='descriptive clock precision only; no alternative pass rule',
                count_duration_decomposition=ratios, terminal_pairs=terminal,
                shared_causal_overhead=None, hardware_noise_calibrated=False)


def reconcile_phase(folder, p, label, index, workload):
    folder = Path(folder)
    expected = model(label, index)
    require(p['id'] == f'CAL-{workload}-{ORDER[index]}' and p['workload'] == workload, 'phase identity mismatch')
    actors = 24 if workload == 'H2' else 12
    contract = dict(workload=workload,fixture=1,actors=actors,edit_rate=4 if workload=='H2' else 0,
                    rain_instances=256 if workload=='H2' else 0,physics_hz=60,max_physics_steps=4,
                    edit_trace=workload=='H2',resolution=[1280,720],render_scale=1,visual_radius=96,data_radius=128,
                    triangle_colliders=False,render_block=32,workers=1,
                    native_policy=dict(frame_usec=2000,frame_upload_bytes=1048576,single_upload_bytes=262144,
                                       terrain_jobs=64,mesh_results=16,mesh_result_bytes=33554432))
    require(p['workload_contract'] == contract and p['simulation_ticks'] == 1800 and p['simulated_seconds'] == 30
            and p['actor_ticks'] == actors*1800-(1 if label=='failed-workload' and index==1 else 0)
            and p['accepted_proxy_edits'] == (120 if workload=='H2' else 0)
            and p['proxy_autosaves'] == (30 if workload=='H2' else 0) and p['rejected_proxy_edits'] == p['readiness_stops'] == 0
            and p['travelled_distance_m'] == 195 and p['completed'] is True
            and p['operation_phase']['tracing'] is True and p['workload_evidence'] == dict(command_hash=123,route_checkpoints=[]), 'modeled gameplay contract differs')
    f = p['fog_frontier']
    require(p['frontier_enabled'] is False and f['status']=='unavailable' and f['evaluation']=='inconclusive'
            and f['minimum_frontier_distance_m'] is None and f['exposed_samples'] is None, 'disabled coverage fabricated')
    failure = label=='failed-operation' and index==1
    require(p['evaluation'] == ('failed' if failure else 'inconclusive'), 'failed operation was waived')
    require(p.get('modeled_operation') == (dict(upload=dict(max_usec=751),deletion=dict(max_usec=0),dropped_frames=0) if failure else None), 'operation fixture differs')
    name = f'{workload}-{label}-{index}.csv'
    require(p['raw_frames'] == name, 'raw path mismatch')
    path = folder / name
    require(path.is_file() and path.stat().st_size <= MAX_RAW // 4, 'raw file missing or oversized')
    sums = [dict(samples=0,usec=0,callbacks=0,callback_usec=0) for _ in range(7)]
    blocks, block_n, block_usec = [], 0, 0
    entry, last_tick, prev_cost, count = 1000200, 0, 0, 0
    endpoint = ack_begin = None
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == HEADER, 'raw schema mismatch')
        for values in reader:
            require(count < expected['n'], 'raw rows exceed bounded model')
            row = {k:int(v) for k,v in values.items()}
            count += 1
            tick = row['tick']
            require(0<=last_tick<=tick<=1800 and row['frame']==count and row['previous_frame']==count-1, 'raw order mismatch')
            bucket = 6 if tick==1800 else max(tick-1,0)//300
            b = sums[bucket]
            require(b['samples'] < expected['counts'][bucket], 'raw section count mismatch')
            position = b['samples']
            if bucket<6:
                q,r = divmod(expected['durations'][bucket],expected['counts'][bucket])
                interval=q+(position<r)
            else:
                interval=5000+(500 if index in (2,3) and ((label=='endpoint' and position==0) or (label=='ack-duration' and position==3)) else 0)
            require(row['interval_usec']==interval and interval>0, 'raw interval differs from predeclared control')
            entry += interval
            cost = 30+count%7
            require(row['entry_usec']==entry and row['callback_begin_usec']==entry+7 and row['callback_end_usec']==entry+7+cost
                    and row['previous_callback_usec']==row['previous_shared_usec']==prev_cost and row['previous_switched_usec']==0
                    and row['callback_write_usec']==8 and row['ledger_tail_usec']==2, 'callback/clock/I/O partition mismatch')
            if bucket==6 and position==0:
                endpoint,ack_begin = entry,entry+7+cost+2
            b['samples']+=1; b['usec']+=interval; b['callbacks']+=1; b['callback_usec']+=cost
            block_n+=1; block_usec+=interval
            if block_usec>=5000000:
                blocks.append(dict(samples=block_n,usec=block_usec));block_n=block_usec=0
            prev_cost,last_tick=cost,tick
    require(count==expected['n'] and p['samples']==count, 'raw rows truncated')
    a=p['diagnostic_accounting']; ledger=p['route_calibration']; clock=p['precision_clock']
    for key,value in dict(start_usec=1000000,end_usec=expected['end'],elapsed_usec=expected['elapsed'],callbacks=count,
                          callback_usec=cost_sum(count),shared_usec=cost_sum(count),last_callback_usec=prev_cost,last_shared_usec=prev_cost,
                          last_callback_end_usec=expected['callback_end'],maximum_callback_usec=36,switched_calls=0,switched_usec=0,
                          last_switched_usec=0,finalization_usec=1002+expected['dose'],writer_drain_usec=400,
                          invalid_partition=False,overflow=False,blocks=blocks,partial_block=dict(samples=block_n,usec=block_usec)).items():
        require(a[key]==value, 'saved diagnostic accounting mismatch: '+key)
    require(p['measurement_end_usec']==expected['callback_end']+2 and math.isclose(p['wall_seconds']*1e6,sum(expected['durations']),abs_tol=.01), 'measurement boundary mismatch')
    require(ledger['invalid'] is False and len(ledger['bins'])==7 and ledger['harness_bracket_usec']==count*2, 'ledger bounds/brackets changed')
    for j,(raw,saved) in enumerate(zip(sums,ledger['bins'])):
        require(raw['samples']==expected['counts'][j] and raw['usec']==expected['durations'][j], 'closed-form aggregate mismatch')
        require(all(saved[k]==v for k,v in raw.items()), 'raw section does not reconcile')
        require(saved['status']==('measured' if raw['samples'] else 'unavailable'), 'unavailable section became passing zero')
        require(math.isclose(saved['mean_usec'],raw['usec']/raw['samples'],rel_tol=1e-12,abs_tol=1e-9) if raw['samples'] else saved['mean_usec'] is None, 'saved section mean mismatch')
    measured_end=expected['callback_end']+2
    begin=measured_end+700; dose=expected['dose']
    positive=index in (1,2)
    require(ledger['closure_dose']==dict(requested_usec=600000 if positive else 0,start_usec=(expected['callback_end']+1 if label=='dose-overlap' and index==1 else begin) if positive else None,
                                       end_usec=begin+dose if positive else None,elapsed_usec=dose), 'declared dose/fault mismatch')
    require(clock==dict(scope='modeled wall clocks; not terrain, disk or CPU measurements',interval_begin_usec=1000200,
                        endpoint_entry_usec=endpoint,ack_begin_usec=ack_begin,ack_end_usec=expected['callback_end']+2 if ack_begin is not None else None,
                        dose_begin_usec=begin if positive else None,dose_end_usec=begin+dose if positive else None,
                        native_phase_close_usec=measured_end+100,writer_drain_begin_usec=measured_end+200,writer_drain_end_usec=measured_end+600,callback_write_usec=count*8,
                        file_io_causal_usec=None,phases=[dict(phase='preparation',begin_usec=998000,end_usec=1000000),
                            dict(phase='overhead_diagnostic',begin_usec=1000000,end_usec=measured_end+100),
                            dict(phase='retirement',begin_usec=expected['end'],end_usec=expected['end']+2000)],
                        native_operations='unavailable: clock-only controls'), 'saved phase/ack/drain/I/O scope mismatch')
    with path.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    return dict(file=name,rows=count,sha256=digest)


def validate(report, folder):
    folder=Path(folder)
    require(report['schema']==1 and report['passed'] is True and report['failures']==[]
            and report['scope']=='software endpoint/count precision; no policy or hardware qualification', 'precision controls failed')
    require(len(report['controls'])==28, 'precision controls incomplete')
    files=list(folder.iterdir())
    require(len(files)==112 and all(p.suffix=='.csv' and p.is_file() for p in files)
            and sum(p.stat().st_size for p in files)<=MAX_RAW, 'raw evidence exceeds bounds or is incomplete')
    seen=set(); raw=[]; characterizations={}
    for c in report['controls']:
        workload,label=c['name'].split('/')
        require(workload in ('H1','H2') and label in LABELS and c['name'] not in seen and c['workload']==workload, 'invalid control identity')
        seen.add(c['name'])
        require(c['io_failed']==(label=='io-failed') and c['expected']==('controls_resolved' if label=='positive' else 'inconclusive'), 'control expectation differs')
        phases=c['phases']; omitted=c['omitted_phases']
        roles=[p['id'].rsplit(workload+'-',1)[-1] for p in phases]
        require(roles==list(reversed(ORDER)) if label=='reordered' else roles==list(ORDER[:3] if label=='missing' else ORDER), 'control order fault differs')
        require(len(omitted)==(1 if label=='missing' else 0), 'lost omitted raw evidence')
        all_phases=sorted(phases+omitted,key=lambda p:ORDER.index(p['id'].rsplit(workload+'-',1)[-1]))
        for i,p in enumerate(all_phases): raw.append(reconcile_phase(folder,p,label,i,workload))
        status,details=assess(phases,workload,io_failed=c['io_failed'])
        require(status==c['expected'], 'independent precision verdict mismatch')
        scope(c['assessment']); reconcile_decision(c['assessment']['workloads'][workload],status,details)
        # Unavailable or missing data must retain null effect, never a passing zero.
        if label in ('missing','unavailable'):
            decision=c['assessment']['workloads'][workload]
            require(decision['positive']==dict(classification='unavailable',added_fraction=None) and decision['route_repeat_variation']==[], 'missing precision fabricated')
        characterizations[c['name']]=characterize(all_phases)
    require({x['file'] for x in raw}=={p.name for p in files}, 'unreconciled raw evidence')
    return dict(passed=True,controls=len(seen),modeled_phases=len(raw),raw_rows=sum(x['rows'] for x in raw),raw_files=raw,
                characterizations=characterizations,legacy_authoritative=True,hardware_noise_calibrated=False,
                shared_overhead_qualified=False,policy_changed=False)


def reconcile_saved(report_path, folder):
    path=Path(report_path)
    require(path.stat().st_size<=MAX_REPORT, 'precision report exceeds 1 MiB')
    return validate(json.loads(path.read_text(encoding='utf-8')),folder)
