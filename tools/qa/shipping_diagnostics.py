"""Independent saved-file shipping pilot reader. Never executes an engine.

The exact-rational estimator is independent of the GDScript implementation.
Complete duration is never divided by callbacks/ticks. All observer costs are
explicitly conditional; this does not estimate total CPU/GPU instrumentation.
"""
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct

from full_height import TICKS, command_hash, target, leg, DIRECTIONS, edit_position
from terrain_budget import reasons as operation_reasons, reconcile_folder as terrain_reconcile

VERSION = 'm1-shipping-complete-trial-1'
INVENTORY = 'm1-shipping-inventory-1'
LIMIT = Fraction(1, 100)
CONTROL_OUTCOMES = {
    **{'shipping-'+str(v):outcome for v,outcome in
       ((-1,'inconclusive'),(0,'passed'),(500000,'passed'),(999999,'passed'),(1000000,'failed'),(1500000,'failed'))},
    'real-dose-absorbed-in-idle':'inconclusive', 'same-total-cancelled-route-drift':'inconclusive',
    'terminal-uncertainty-overlap':'inconclusive', 'callback-count-is-not-denominator':'passed',
    'repeatable-nonflat-route':'passed', **{'invalid-trial-'+str(i):'inconclusive' for i in range(13)}
}
FRAME_FIELDS = ('frame', 'entry_usec', 'interval_usec', 'tick', 'resident_mesh', 'resident_data',
                'generation_jobs', 'mesh_jobs', 'result_jobs', 'retired_meshes', 'accepted',
                'readiness_stops', 'coverage_alarms')
POSE_FIELDS = ('tick', 'usec', 'x', 'y', 'z', 'command_hash', 'actors', 'accepted', 'rejected',
               'saves', 'readiness_stops', 'source_tick', 'decision_tick', 'source_x', 'source_y',
               'source_z', 'direction', 'prep_x', 'prep_y', 'prep_z', 'dose_start_usec',
               'dose_end_usec', 'dose_request_usec', 'hash_updates', 'hash_sha256')


def require(value, message):
    if not value:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def single(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def envelope(trials):
    if len(trials) != 4:
        return None
    if any(not t.get('valid') or type(t.get('duration_usec')) is not int
           or t['duration_usec'] <= 0 or len(t.get('sections_usec', [])) != 5
           or any(v < 0 for v in t['sections_usec'])
           or type(t.get('marker_usec')) is not int or t['marker_usec'] < 0
           or sum(t['sections_usec']) != t['duration_usec'] for t in trials):
        return None
    a = [trials[i]['duration_usec'] for i in (0, 3)]
    b = [trials[i]['duration_usec'] for i in (1, 2)]
    drift = max(Fraction(sum(abs(x-y) for x, y in zip(trials[i]['sections_usec'], trials[j]['sections_usec'])), min(a))
                for i, j in ((0, 3), (1, 2)))
    marker = Fraction(max(trials[i].get('marker_usec', 0)+trials[j].get('marker_usec', 0)
                          for i in (0, 3) for j in (1, 2)), min(a))
    return dict(lower=Fraction(min(b), max(a))-1-drift-marker,
                upper=Fraction(max(b), min(a))-1+drift+marker,
                point=Fraction(sum(b), sum(a))-1, matching_section_drift=drift,
                terminal_marker_uncertainty=marker)


def controls(trials):
    if len(trials) < 9 or not all(t.get('valid') for t in trials[:9]):
        return dict(valid=False, null_valid=False, positive_valid=False)
    n, p = envelope(trials[1:5]), envelope(trials[5:9])
    if n is None or p is None:
        return dict(valid=False, null_valid=False, positive_valid=False)
    null_ok = n['lower'] <= 0 <= n['upper'] and n['upper']-n['lower'] < LIMIT and n['matching_section_drift'] < LIMIT
    a = [trials[i]['duration_usec'] for i in (5, 8)]
    dose_values = []
    doses_ok = True
    request = math.ceil(Fraction(a[0], 50*TICKS))
    for t in trials[6:8]:
        d = t['dose']
        doses_ok &= (d.get('reference_usec') == a[0] and d.get('requested_tick_usec') == request
                     and d.get('actual_usec', 0) >= request*TICKS and d.get('ticks') == TICKS
                     and d.get('valid') is True)
        dose_values.append(d.get('actual_usec', 0))
    dose_low, dose_high = Fraction(min(dose_values), max(a)), Fraction(max(dose_values), min(a))
    positive_ok = (doses_ok and dose_low > LIMIT and p['lower'] >= LIMIT
                   and p['matching_section_drift'] < LIMIT and p['upper'] >= dose_low and p['lower'] <= dose_high)
    return dict(valid=bool(null_ok and positive_ok), null_valid=bool(null_ok), positive_valid=bool(positive_ok),
                null=n, positive=p, dose_fraction=[dose_low, dose_high])


def evaluate(trials):
    c = controls(trials)
    result = dict(outcome='inconclusive', qualified=False, controls=c, shipping=None)
    if not all(t.get('valid') for t in trials) or not c['valid']:
        return result
    if len(trials) != 13:
        result['outcome'] = 'not_run'
        return result
    e = envelope(trials[9:13])
    result['shipping'] = e
    if e is None or e['matching_section_drift'] >= LIMIT or e['point'] < 0:
        return result
    if e['upper'] < LIMIT:
        result['outcome'] = 'passed'
    elif e['lower'] >= LIMIT:
        result['outcome'] = 'failed'
    return result


def floating(value):
    if isinstance(value, Fraction):
        return float(value)
    if isinstance(value, dict):
        return {k: floating(v) for k, v in value.items()}
    if isinstance(value, list):
        return [floating(v) for v in value]
    return value


def compare_method(actual, expected):
    require(actual['outcome'] == expected['outcome'] and actual['qualified'] is False,
            'Shipping runtime/rational-reader decision mismatch')
    ac, ec = actual['controls'], expected['controls']
    require(ac['valid'] == ec['valid'], 'Shipping control decision mismatch')
    if 'null' in ec:
        for key in ('null_valid', 'positive_valid'):
            require(ac[key] == ec[key], 'Shipping sensitivity decision mismatch')
        for name in ('null', 'positive'):
            for key, value in ec[name].items():
                require(math.isclose(ac[name][key], float(value), rel_tol=1e-10, abs_tol=1e-12),
                        'Shipping control envelope mismatch')
    if expected['shipping'] is not None:
        for key, value in expected['shipping'].items():
            require(math.isclose(actual['shipping'][key], float(value), rel_tol=1e-10, abs_tol=1e-12),
                    'Shipping effect envelope mismatch')


def validate_method_controls(control):
    require(control['passed'] is True and control['fixed_work_dispatch'] is True
            and len(control['cases']) == 24 and control['qualified'] is False, 'Missing adopted method controls')
    require([case['name'] for case in control['cases']] == list(CONTROL_OUTCOMES),
            'Missing, duplicated or reordered adopted method controls')
    references = (0,1,215999,216000,216001,216000000,216000001)
    require(control['dose_request_vectors'] == [[v,math.ceil(Fraction(v,50*TICKS))] for v in references],
            'Nominal positive dose integer ceiling mismatch')
    for case in control['cases']:
        compare_method(case['assessment'], evaluate(case['trials']))
        require(case['assessment']['outcome'] == CONTROL_OUTCOMES[case['name']],
                'Adopted method control failed its independent known outcome')
    return dict(passed=True, cases=24, integer_request_vectors=len(references), qualified=False)


def poses(path, trial):
    require(0 < path.stat().st_size < 8388608, 'Missing/oversized pilot physics evidence')
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        require(tuple(reader.fieldnames) == POSE_FIELDS, 'Pilot physics schema changed')
        rows = list(reader)
    require(len(rows) == TICKS, 'Missing/extra pilot fixed physics work')
    actual_dose = updates = 0
    previous = trial['route_clocks_usec'][0]
    fingerprint = 0
    positions = {0: [10, 72, 10]}
    dose = trial['dose']
    digests = {}
    for tick, row in enumerate(rows, 1):
        integers = ('tick', 'usec', 'command_hash', 'actors', 'accepted', 'rejected', 'saves',
                    'readiness_stops', 'source_tick', 'decision_tick', 'direction', 'dose_start_usec',
                    'dose_end_usec', 'dose_request_usec', 'hash_updates')
        r = {k: int(row[k]) for k in integers}
        p = [float(row[k]) for k in ('x', 'y', 'z')]
        fingerprint = command_hash(tick, fingerprint)
        goal = target(tick)
        require(r['tick'] == tick and previous <= r['usec'] <= trial['end_usec']
                and all(abs(p[i]-goal[i]) < .01 for i in (0, 2))
                and 63.99 <= p[1] <= 72.01 and (tick < 120 or 64 <= p[1] <= 64.01),
                'Pilot actual route, support or monotonic fixed work changed')
        require(r['command_hash'] == fingerprint and r['actors'] == tick*24
                and r['accepted'] == tick//15 and r['rejected'] == r['readiness_stops'] == 0
                and r['saves'] == tick//60, 'Pilot actor/edit/save work changed')
        source, decision = r['source_tick'], r['decision_tick']
        require(0 <= source <= decision < tick and tick-source <= 8 and source in positions
                and r['direction'] == leg(min(TICKS, decision+1)), 'Pilot preparation handover changed')
        origin = [float(row[k]) for k in ('source_x', 'source_y', 'source_z')]
        center = [float(row[k]) for k in ('prep_x', 'prep_y', 'prep_z')]
        require(all(abs(a-b) < 1e-7 for a, b in zip(origin, positions[source]))
                and all(abs(c-single(single(pv)+32*axis)) < 1e-7
                        for c, pv, axis in zip(center, origin, DIRECTIONS[r['direction']])),
                'Pilot preparation viewer left its bounded demand')
        if trial['dose_enabled']:
            start, end = r['dose_start_usec'], r['dose_end_usec']
            require(previous <= start <= end <= r['usec'] and r['dose_request_usec'] == dose['requested_tick_usec']
                    and 0 < r['dose_request_usec'] <= 2000 and r['dose_request_usec'] <= end-start <= 50000
                    and 1 <= r['hash_updates'] <= 512, 'Missing/unbounded or out-of-route positive dose')
            count = r['hash_updates']
            if count not in digests:
                digests[count] = hashlib.sha256(bytes([90])*(4096*count)).hexdigest()
            require(row['hash_sha256'] == digests[count], 'Positive native hash work/digest changed')
            actual_dose += end-start
            updates += count
        else:
            require(all(r[k] == 0 for k in ('dose_start_usec', 'dose_end_usec', 'dose_request_usec', 'hash_updates'))
                    and row['hash_sha256'] == '-', 'Undeclared dose in a bare/shipping control')
        if tick % 1440 == 0:
            require(r['usec'] == trial['route_clocks_usec'][tick//1440], 'Pilot route section endpoint changed')
        positions[tick] = p
        previous = r['usec']
    require(dose['actual_usec'] == actual_dose and dose['hash_updates'] == updates
            and dose['ticks'] == (TICKS if trial['dose_enabled'] else 0), 'Positive dose totals do not reconcile')
    return dict(rows=len(rows), command_hash=fingerprint, terminal_player=positions[TICKS],
                dose_actual_usec=actual_dose, dose_hash_updates=updates)


def frames(path, trial):
    require(0 < path.stat().st_size <= 64*1024*1024, 'Missing/oversized pilot callback evidence')
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        require(tuple(reader.fieldnames[:len(FRAME_FIELDS)]) == FRAME_FIELDS, 'Pilot callback schema changed')
        rows = list(reader)
    report = trial['report']
    require(len(rows) == report['samples'] == trial['callback_count'] > 0, 'Missing pilot callback/final callback')
    previous = None
    last_tick = 0
    maximum_mesh = maximum_data = 0
    total_interval = 0
    for index, row in enumerate(rows, 1):
        r = {k: int(row[k]) for k in FRAME_FIELDS}
        require(r['frame'] == index and trial['route_clocks_usec'][0] <= r['entry_usec'] <= trial['end_usec']
                and r['interval_usec'] >= 0 and (previous is None or r['entry_usec']-previous == r['interval_usec'])
                and last_tick <= r['tick'] <= min(TICKS,last_tick+4), 'Pilot callback clock/tick/catch-up cap changed')
        require(0 < r['resident_mesh'] <= 512 and 0 < r['resident_data'] <= 8192
                and 0 <= r['generation_jobs'] and 0 <= r['mesh_jobs'] and r['generation_jobs']+r['mesh_jobs'] <= 64
                and 0 <= r['result_jobs'] <= 16 and 0 <= r['retired_meshes'] <= 768
                and r['accepted'] == r['tick']//15 and r['readiness_stops'] == r['coverage_alarms'] == 0,
                'Pilot observed coverage/readiness/resource envelope failed')
        # These values are the actual analytic scan, not inferred from the mode.
        require(row['frontier_status'] == 'measured' and float(row['fog_boundary_m']) == 96
                and float(row['frontier_distance_m']) >= 96
                and math.isclose(float(row['fog_clearance_m']), float(row['frontier_distance_m'])-96, abs_tol=1e-4),
                'Pilot frontier evidence unavailable or exposed')
        checked, ready, unready, empty, candidates = [int(row['frontier_'+v]) for v in
            ('checked_regions','ready_regions','unready_regions','empty_regions','candidate_regions')]
        require(0 < checked <= candidates <= 1024 and ready+unready == checked and 0 <= empty <= ready,
                'Pilot frontier scan was truncated or invalid')
        goal = target(r['tick'])
        yaw = single((-math.pi/2,math.pi/2,math.pi)[leg(r['tick'])])
        require(abs(float(row['camera_x'])-goal[0]) < .01 and abs(float(row['camera_z'])-goal[2]) < .01
                and 65.64 <= float(row['camera_y']) <= 73.66
                and (r['tick'] < 120 or 65.64 <= float(row['camera_y']) <= 65.66)
                and abs(float(row['camera_yaw'])-yaw) < 1e-5, 'Pilot actual camera/view direction changed')
        previous, last_tick = r['entry_usec'], r['tick']
        maximum_mesh = max(maximum_mesh, r['resident_mesh'])
        maximum_data = max(maximum_data, r['resident_data'])
        total_interval += r['interval_usec']
    accounting = report['diagnostic_accounting']
    require(last_tick == TICKS and trial['callback_last_end_usec'] == accounting['last_callback_end_usec']
            and previous <= trial['callback_last_end_usec'] <= report['measurement_end_usec']
            and accounting['callbacks'] == len(rows) and not accounting['overflow']
            and report['peaks']['resident_mesh'] == maximum_mesh and report['peaks']['resident_data'] == maximum_data
            and abs(report['wall_seconds']*1000000-total_interval) < 1,
            'Pilot last callback, interval totals or resident peaks lost')
    return dict(rows=len(rows), peak_mesh=maximum_mesh, peak_data=maximum_data, interval_usec=total_interval)


def trial_evidence(folder, t, inventory_hash):
    name = t['id']
    complete_path, boundary_path = folder/(name+'-complete.json'), folder/(name+'-boundary.json')
    complete, boundary = read(complete_path), read(boundary_path)
    require(all(t[k] == v for k, v in complete.items()), 'Complete per-trial report differs from batch')
    require(all(t[k] == v for k, v in boundary.items() if k != 'complete_sha256')
            and boundary['complete_sha256'] == sha(complete_path), 'Complete boundary/report hash differs')
    require(t['valid'] is True and t['io_failed'] is False and t['drained'] is True
            and t['operation_ok'] is True and not t['integration_failures'] and t['inventory_sha256'] == inventory_hash,
            'Failed/incomplete work, I/O, operation, inventory or drain evidence')
    clocks = [t['start_usec']]+t['route_clocks_usec']+[t['end_usec']]
    require(len(clocks) == 6 and all(b >= a for a, b in zip(clocks, clocks[1:]))
            and t['duration_usec'] == clocks[-1]-clocks[0] and t['duration_usec'] >= 72000000
            and t['sections_usec'] == [b-a for a, b in zip(clocks, clocks[1:])]
            and sum(t['sections_usec']) == t['duration_usec'], 'Incomplete/non-partitioned whole-trial boundary')
    require(t['end_usec'] <= t['marker_start_usec'] <= t['marker_end_usec']
            and t['marker_usec'] == t['marker_end_usec']-t['marker_start_usec'], 'Missing terminal marker uncertainty')
    for key in ('optional_setup', 'optional_finalization', 'report_finalization'):
        span = t[key]
        require(t['start_usec'] <= span['start_usec'] <= span['end_usec'] <= t['end_usec'], 'Optional/report span outside complete trial')
    require(t['report_finalization']['end_usec'] == t['end_usec'] and len(t['closures']) == len(t['writer_drains']) == 3,
            'Missing native closure or writer-drain boundary')
    for span in t['closures']+t['writer_drains']:
        require(t['start_usec'] <= span['start_usec'] <= span['end_usec'] <= t['report_finalization']['start_usec'],
                'Native/writer closure outside complete trial')
    require(all(t['native_final'][k] == 0 for k in ('generation_jobs', 'mesh_jobs', 'result_jobs', 'main_jobs', 'retired_meshes')),
            'Pilot native queues did not drain')
    require(t['native_final']['overloads'] == 0 and t['native_final']['retired_high_water'] <= 768,
            'Pilot native admission/retirement ceiling failed')
    phases = t['phases']
    require([p['phase'] for p in phases] == ['preparation', 'overhead_diagnostic', 'retirement']
            and all(p['scenario'] == name and p['terrain_accounting_version'] == 2 and not operation_reasons(p) for p in phases),
            'Pilot complete native operation guards failed')
    forensic = t['diagnostic_mode'] == 'forensic'
    shipping = t['diagnostic_mode'] in ('shipping', 'forensic')
    require(t['raw_operation_trace'] is forensic and t['renderer_queries'] is forensic
            and all(p['tracing'] is forensic for p in phases)
            and t['optional_setup']['enabled'] is shipping and t['optional_finalization']['enabled'] is shipping,
            'Actual runtime mode switches differ from the inventory')
    r, c = t['report'], t['report']['workload_contract']
    fixed = dict(version=VERSION, workload='H2', fixture=3, actors=24, edit_rate=4,
                 rain_instances=256, seconds=72, physics_hz=60, max_physics_steps=4,
                 route_origin=[10,72,10], player_start=[10,72,10], autosave_interval_s=1,
                 camera_fov=75, camera_far=96,
                 resolution=[1280,720], render_scale=1, render_block=32, workers=1,
                 visual_radius=96, data_radius=128, triangle_colliders=False,
                 terrain_bounds=[-4096,-64,-4096,8192,256,8192], admission_policy='priority',
                 admission_trace=False, edit_trace=True, operation_trace=forensic, render_queries=forensic,
                 full_height_observation=False, common_qualification_observer=True,
                 diagnostic_mode=t['diagnostic_mode'], inventory_sha256=inventory_hash)
    require(all(c.get(k) == v for k, v in fixed.items()) and c['frontier_preparation']['viewer_count'] == 1
            and c['frontier_preparation']['lead_m'] == 32 and c['native_policy'] == dict(frame_usec=2000,
                frame_upload_bytes=1048576, single_upload_bytes=262144, terrain_jobs=64,
                mesh_results=16, mesh_result_bytes=33554432), 'Pilot workload/policy/configuration changed')
    require(c['fog'] == dict(enabled=True,mode='depth',density=1,height_density=0,begin_m=16,end_m=96,curve=1)
            and c['frontier_preparation']['enabled'] is True and c['frontier_preparation']['viewer_radius_m'] == 96
            and c['frontier_preparation']['resident_mesh_bound'] == 448, 'Pilot fog/preparation envelope changed')
    limits = dict(private_bytes=2147483648, working_set=1610612736, pool_voxel_total=201326592)
    require(all(0 <= r['peaks'][k] <= limit for k, limit in limits.items())
            and r['peaks']['private_bytes'] > 0 and r['peaks']['working_set'] > 0, 'Pilot observed memory envelope failed')
    require(r['simulation_ticks'] == TICKS and r['actor_ticks'] == 103680 and r['accepted_proxy_edits'] == 288
            and r['rejected_proxy_edits'] == r['readiness_stops'] == 0 and r['proxy_autosaves'] == 72
            and r['edit_visibility']['accepted'] == r['edit_visibility']['submitted'] == 288
            and r['edit_visibility']['pending'] == r['edit_visibility']['queued'] == r['edit_visibility']['overflow'] == 0
            and r['edit_visibility']['p95_upper_usec'] <= 100000 and r['edit_visibility']['max_usec'] <= 200000
            and r['fog_frontier']['exposed_samples'] == 0 and r['fog_frontier']['evaluation'] == 'passed',
            'Pilot final edit/work/coverage acknowledgement missing or failed')
    require(t['last_command_usec'] == t['route_clocks_usec'][-1] <= r['measurement_end_usec']
            <= t['closures'][1]['start_usec'] <= t['writer_drains'][1]['end_usec'] <= t['end_usec'],
            'Pilot last-edit/native/report closure boundary changed')
    events = [json.loads(v) for v in (folder/r['edit_visibility_events']).read_text(encoding='utf-8-sig').splitlines()]
    require(len(events) == 288 and sorted(e['id'] for e in events) == list(range(1,289))
            and all(e['outcome'] == 'submitted' for e in events), 'Missing/substituted edit-submission evidence')
    revisions, latencies = {}, []
    for event in sorted(events, key=lambda e:e['id']):
        x,y,z = edit_position(event['id']*15)
        require(event['voxel'] == [x,y,z] and t['route_clocks_usec'][0] <= event['accepted_usec'] <= event['end_usec'] <= r['measurement_end_usec']
                and event['latency_usec'] == event['end_usec']-event['accepted_usec']
                and [v['block'] for v in event['targets']] == [[x//32-1,y//32,z//32],[x//32,y//32,z//32]],
                'Pilot original edit command/clock/border targets changed')
        for value in event['targets']:
            cell = tuple(value['block'])
            require(value['submitted'] is True and value['revision'] > revisions.get(cell,0),
                    'Pilot original mesh revision was not submitted')
            revisions[cell] = value['revision']
        latencies.append(event['latency_usec'])
    p95 = (sorted(latencies)[math.ceil(.95*len(latencies))-1]//1000+1)*1000
    require(r['edit_visibility']['max_usec'] == max(latencies) and r['edit_visibility']['p95_upper_usec'] == p95,
            'Pilot original edit latency aggregate mismatch')
    require(read(folder/(name+'-frames.csv.proxy.tmp')) == dict(proxy_tick=TICKS, accepted_edits=288, payload='x'*32768),
            'Pilot final proxy-save work missing')
    pp = folder/(name+'-poses.csv')
    require(t['pose_sha256'] == sha(pp), 'Pilot physics evidence hash differs')
    observed_poses = poses(pp, t)
    observed_frames = frames(folder/(name+'-frames.csv'), t)
    optional = folder/(name+'-shipping.json')
    require(optional.exists() is shipping, 'Shipping telemetry appeared in a disabled mode or is missing')
    if shipping:
        s = read(optional)
        require(len(s['rows']) == 72 and [row['second'] for row in s['rows']] == list(range(1,73))
                and all(row['second']*60 <= row['tick'] <= min(TICKS, row['second']*60+4) for row in s['rows'])
                and s['interval_count'] == observed_frames['rows'] and s['interval_sum_usec'] == observed_frames['interval_usec'],
                'Bounded optional shipping telemetry did not run/flush')
    fp = folder/(name+'-forensic.jsonl')
    require(fp.exists() is forensic, 'Forensic observer leaked into a shipping/bare control')
    if forensic:
        detail = [json.loads(v) for v in fp.read_text(encoding='utf-8-sig').splitlines()]
        require(len(detail) == observed_frames['rows'] and all('render_cpu_ms' in row and 'render_gpu_ms' in row for row in detail),
                'Forensic renderer/detail trace did not run')
        terrain_reconcile(folder, {'operation_phases': phases})
    return dict(id=name, mode=t['diagnostic_mode'], **observed_poses, **observed_frames)


def reconcile(folder, build, inventory_path):
    folder = Path(folder)
    p, s = read(folder/'shipping-pilot.json'), read(folder/'summary.json')
    inventory = read(inventory_path)
    ih = sha(inventory_path)
    require(p['version'] == VERSION and p['build'] == s['build'] == build and p['inventory'] == inventory
            and inventory['version'] == INVENTORY and p['inventory_sha256'] == ih
            and p['passed'] is True and not p['qualified'] and p['target_performance'] == 'not_run'
            and s['completed'] and not s['qualified'] and not s['integration_failures']
            and s['benchmark_mode'] == 'shipping-pilot', 'Pilot identity/inventory/completion mismatch')
    trials = p['trials']
    if p['single_mode']:
        require(len(trials) == 1 and trials[0]['group'] == 'single' and trials[0]['index'] == 0
                and trials[0]['diagnostic_mode'] == p['single_mode'] and p['assessment']['outcome'] == 'not_run'
                and not trials[0]['dose_enabled'], 'Single companion unexpectedly claims overhead qualification')
    else:
        expected = [('warmup', 0, 'bare', False)]
        for group in ('null', 'positive'):
            expected += [(group, i, 'bare', group == 'positive' and i in (1,2)) for i in range(4)]
        c = controls(trials)
        if c['valid']:
            expected += [('shipping', i, 'shipping' if i in (1,2) else 'bare', False) for i in range(4)]
        require([(t['group'], t['index'], t['diagnostic_mode'], t['dose_enabled']) for t in trials] == expected,
                'Pilot exceeded/missed its predeclared finite protocol')
        compare_method(p['assessment'], evaluate(trials))
    records = [trial_evidence(folder, t, ih) for t in trials]
    require(s['scenarios'] == [t['report'] for t in trials] and s['operation_phases'] == [phase for t in trials for phase in t['phases']]
            and s['shipping_diagnostic_qualification'] == p['assessment'], 'Batch/legacy companion differs from complete trials')
    return dict(passed=True, qualified=False, method=VERSION, trials=len(trials), records=records,
                assessment=floating(evaluate(trials)) if not p['single_mode'] else {'outcome':'not_run'},
                target_performance='not_run')
