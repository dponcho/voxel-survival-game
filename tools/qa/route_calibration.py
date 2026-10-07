"""Independent exact-rational route-control oracle and streamed CSV reconciliation.

Only cloud evidence is read by CI. Target folders stay private. No qualification
decision or legacy classification is replaced by this supplementary assessment.
"""
import csv
from fractions import Fraction
import json
from pathlib import Path

VERSION = 'm1-route-calibration-1'
ORDER = ('reference-1', 'closure-1', 'closure-2', 'reference-2')
LIMIT = Fraction(1, 100)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def compare(reference, positive):
    r = [Fraction(v) for v in reference]
    p = [Fraction(v) for v in positive]
    lower, upper = min(p) / max(r) - 1, max(p) / min(r) - 1
    return {'added_fraction': float(sum(p) / sum(r) - 1),
            'lower_fraction': float(lower), 'upper_fraction': float(upper),
            'classification': ('above_limit' if lower >= LIMIT else
                               'below_limit' if lower >= 0 and upper < LIMIT else 'inconclusive')}


def variation(pair):
    a, b = map(Fraction, pair)
    return abs(a - b) * 2 / (a + b)


def assess(phases, workload, short=False, io_failed=False):
    """Use complete trial means; route positions only constrain repeatability."""
    if len(phases) != 4:
        return 'inconclusive', None
    valid = not short and not io_failed
    means, shape = [], []
    contract = phases[0].get('workload_contract', {})
    for i, p in enumerate(phases):
        a, ledger = p.get('diagnostic_accounting', {}), p.get('route_calibration', {})
        n = p.get('samples', 0)
        valid &= (p.get('id') == f'CAL-{workload}-{ORDER[i]}' and p.get('workload') == workload
                  and p.get('completed') is True and p.get('evaluation') != 'failed'
                  and p.get('readiness_stops') == 0 and p.get('workload_contract') == contract)
        valid &= (p.get('simulation_ticks') == (60 if short else 1800)
                  and p.get('actor_ticks') == p.get('simulation_ticks', 0) * (24 if workload == 'H2' else 12)
                  and p.get('rejected_proxy_edits') == 0 and p.get('operation_phase', {}).get('tracing') is True
                  and p.get('frontier_enabled') is False and a.get('switched_calls') == a.get('switched_usec') == 0)
        f = p.get('fog_frontier', {})
        valid &= (f.get('status') == 'unavailable' and f.get('evaluation') == 'inconclusive'
                  and f.get('exposed_samples') is None and f.get('minimum_frontier_distance_m') is None)
        valid &= (p.get('simulated_seconds', 0) >= 30
                  and abs(p.get('wall_seconds', 0) - p.get('simulated_seconds', 0)) <= .25)
        valid &= (n > 0 and a.get('callbacks') == n and a.get('overflow') is False
                  and a.get('invalid_partition') is False and ledger.get('invalid') is False
                  and ledger.get('version') == VERSION)
        elapsed = a.get('elapsed_usec', 0)
        if n <= 0 or elapsed <= 0:
            return 'inconclusive', None
        means.append(Fraction(int(elapsed), int(n)))
        valid &= (a.get('end_usec', 0) - a.get('start_usec', 0) == elapsed
                  and a.get('callback_usec') == a.get('shared_usec')
                  and a.get('end_usec', 0) - a.get('last_callback_end_usec', 0) == a.get('finalization_usec')
                  and 0 <= a.get('writer_drain_usec', -1) <= a.get('finalization_usec', -1))
        bins = ledger.get('bins', [])
        if len(bins) != 7 or any(b.get('samples', 0) <= 0 or b.get('usec', 0) <= 0 for b in bins):
            return 'inconclusive', None
        shape.append([Fraction(int(b['usec']), int(b['samples'])) for b in bins])
        valid &= all(b.get('callbacks') == b['samples'] and b.get('status') == 'measured' for b in bins)
        valid &= (sum(b['samples'] for b in bins) == n
                  and sum(b['callback_usec'] for b in bins) == a.get('callback_usec')
                  and abs(sum(b['usec'] for b in bins) - p.get('wall_seconds', 0) * 1e6) <= .01)
        dose = ledger.get('closure_dose', {})
        requested = 600000 if i in (1, 2) else 0
        valid &= dose.get('requested_usec') == requested
        if requested:
            start, end = dose.get('start_usec'), dose.get('end_usec')
            valid &= (type(start) in (int, float) and type(end) in (int, float))
            if start is None or end is None:
                return 'inconclusive', None
            valid &= (start >= max(p.get('measurement_end_usec', 0), a.get('last_callback_end_usec', 0))
                      and end <= a.get('end_usec', 0) and end - start == dose.get('elapsed_usec')
                      and requested <= end - start <= a.get('finalization_usec', -1))
        else:
            valid &= dose.get('start_usec') is None and dose.get('end_usec') is None and dose.get('elapsed_usec') == 0
    valid &= bool(contract) and contract.get('visual_radius') == 96 and contract.get('data_radius') == 128
    valid &= all(all(p.get('workload_evidence', {}).get(k) == phases[0].get('workload_evidence', {}).get(k) for k in ['command_hash', 'route_checkpoints']) for p in phases)
    null = variation((means[0], means[3]))
    drift = [[variation((shape[0][j], shape[3][j])), variation((shape[1][j], shape[2][j]))] for j in range(7)]
    valid &= max(null, variation((means[1], means[2])), *(v for pair in drift for v in pair)) < LIMIT
    effect = compare((means[0], means[3]), (means[1], means[2]))
    return ('controls_resolved' if valid and effect['classification'] == 'above_limit' else 'inconclusive'), {
        'positive': effect, 'null_repeat_variation': float(null),
        'route_repeat_variation': [{'reference': float(v[0]), 'closure': float(v[1])} for v in drift]}


def reconcile_decision(actual, expected, details):
    require(actual['status'] == expected and actual['qualified'] is False, 'incorrect calibration decision')
    if details is None:
        return
    require(len(actual['route_repeat_variation']) == 7, 'route/terminal decision missing')
    for key in ['added_fraction', 'lower_fraction', 'upper_fraction']:
        require(abs(actual['positive'][key] - details['positive'][key]) < 1e-12, 'effect envelope mismatch')
    require(actual['positive']['classification'] == details['positive']['classification'], 'effect boundary mismatch')
    require(abs(actual['null_repeat_variation'] - details['null_repeat_variation']) < 1e-12, 'null repeat mismatch')
    for a, e in zip(actual['route_repeat_variation'], details['route_repeat_variation']):
        require(all(abs(a[k] - e[k]) < 1e-12 for k in e), 'matching-section drift mismatch')


def scope(assessment):
    require(assessment['version'] == VERSION and assessment['qualified'] is False
            and assessment['legacy_authoritative'] is True and assessment['threshold'] == .01
            and assessment['hardware_noise_calibrated'] is False
            and assessment['shared_overhead']['outcome'] == 'inconclusive'
            and assessment['shared_overhead']['added_fraction'] is None, 'calibration promoted qualification')


def validate_controls(report):
    require(report['schema'] == 1 and report['passed'] is True and report['failures'] == [], 'software controls failed')
    require(report['scope'] == 'software route/closure controls; physical hardware precision unverified', 'scope changed')
    labels = {'stationary','varying','missing','reordered','stall','route-drift','failed','dose-overlap',
              'dose-missing','unavailable-bin','contract','short','io-failed'}
    require(len(report['controls']) == 26, 'control set incomplete')
    seen = set()
    for control in report['controls']:
        name = control['name']
        workload, label = name.split('/')
        require(workload in ['H1','H2'] and label in labels and name not in seen, 'invalid/duplicate control')
        seen.add(name)
        require(control['workload'] == workload, 'mislabeled workload')
        status, detail = assess(control['phases'], workload, control['short_run'], control['io_failed'])
        require(status == control['expected'], 'declared control inconsistent with independent oracle')
        scope(control['assessment'])
        reconcile_decision(control['assessment']['workloads'][workload], status, detail)
    return {'passed': True, 'controls': len(seen), 'software_sensitivity_verified': True,
            'hardware_noise_calibrated': False, 'shared_overhead_qualified': False, 'legacy_authoritative': True}


def reconcile_folder(folder):
    folder = Path(folder)
    saved = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
    require(saved['benchmark_mode'] == 'calibration' and saved['completed'] and saved['qualified'] is False
            and not saved['integration_failures'], 'incomplete calibration smoke')
    scope(saved['route_calibration'])
    require(len(saved['scenarios']) == 9 and len(saved['operation_phases']) == 27, 'phase/workload count mismatch')
    frames = 0
    for workload in ['H1', 'H2']:
        phases = [p for p in saved['scenarios'] if p.get('workload') == workload]
        require(len(phases) == 4, 'missing saved workload quartet')
        reference = phases[0]['workload_contract']
        ticks = 60 if saved['test_mode'] else 1800
        actors = 24 if workload == 'H2' else 12
        for index, phase in enumerate(phases):
            contract = phase['workload_contract']
            require(phase['id'] == f'CAL-{workload}-{ORDER[index]}' and contract == reference
                    and contract['fixture'] == 1 and contract['actors'] == actors
                    and contract['rain_instances'] == (256 if workload == 'H2' else 0)
                    and contract['edit_rate'] == (4 if workload == 'H2' else 0)
                    and contract['resolution'] == [1280,720] and contract['render_scale'] == 1
                    and contract['visual_radius'] == 96 and contract['data_radius'] == 128
                    and contract['workers'] in [1,2] and contract['render_block'] in [16,32]
                    and contract['physics_hz'] == 60 and contract['max_physics_steps'] == 4
                    and contract['triangle_colliders'] is False, 'saved calibration workload/profile changed')
            for key, value in {'frame_usec':2000,'frame_upload_bytes':1048576,'single_upload_bytes':262144,
                               'terrain_jobs':64,'mesh_results':16,'mesh_result_bytes':33554432}.items():
                require(contract['native_policy'][key] == value, 'saved native admission policy changed')
            require(phase['simulation_ticks'] == ticks and phase['actor_ticks'] == actors*ticks
                    and phase['accepted_proxy_edits'] == (ticks//15 if workload == 'H2' else 0)
                    and phase['proxy_autosaves'] == (ticks//60 if workload == 'H2' else 0)
                    and phase['rejected_proxy_edits'] == phase['readiness_stops'] == 0
                    and phase['travelled_distance_m'] >= 6.5*ticks/60-1
                    and phase['operation_phase']['tracing'] is True, 'saved actual workload activity differs')
            require(all(phase['workload_evidence'][k] == phases[0]['workload_evidence'][k]
                        for k in ['command_hash','route_checkpoints']), 'saved command schedules differ')
            require(phase['frontier_enabled'] is False and phase['diagnostic_accounting']['switched_calls'] == 0
                    and phase['diagnostic_accounting']['switched_usec'] == 0
                    and phase['fog_frontier']['status'] == 'unavailable'
                    and phase['fog_frontier']['minimum_frontier_distance_m'] is None
                    and phase['fog_frontier']['exposed_samples'] is None, 'saved switch or unavailable coverage changed')
        status, detail = assess(phases, workload, saved['test_mode'], False)
        reconcile_decision(saved['route_calibration']['workloads'][workload], status, detail)
        for phase in phases:
            bins = [dict(samples=0, usec=0, callbacks=0, callback_usec=0) for _ in range(7)]
            previous_bin = None
            count = 0
            with (folder / phase['raw_frames']).open(encoding='utf-8-sig', newline='') as f:
                for row in csv.DictReader(f):
                    tick = round(float(row['simulation_s']) * 60)
                    bucket = 6 if tick >= 1800 else max(tick - 1, 0) // 300
                    require(0 <= tick <= 1800 and int(row['frame']) == count + 1 and int(row['diagnostic_frame']) == count, 'raw ordering/clock mismatch')
                    bins[bucket]['samples'] += 1
                    bins[bucket]['usec'] += round(float(row['interval_ms']) * 1000)
                    if previous_bin is not None:
                        bins[previous_bin]['callbacks'] += 1
                        bins[previous_bin]['callback_usec'] += int(row['diagnostic_usec'])
                    else:
                        require(int(row['diagnostic_usec']) == 0, 'first row fabricated previous callback')
                    require(all(row[k] == 'unavailable' for k in list(row)[20:38]), 'null control ran frontier coverage')
                    previous_bin = bucket
                    count += 1
            require(previous_bin is not None, 'missing raw frames')
            bins[previous_bin]['callbacks'] += 1
            bins[previous_bin]['callback_usec'] += phase['diagnostic_accounting']['last_callback_usec']
            for a, e in zip(phase['route_calibration']['bins'], bins):
                require(all(a[k] == v for k,v in e.items()), 'raw route/callback/terminal ledger mismatch')
                require(a['status'] == ('measured' if e['samples'] else 'unavailable'), 'missing bin treated as available')
                require(a['mean_usec'] == (e['usec']/e['samples'] if e['samples'] else None), 'missing bin treated as zero')
            labels = [p['phase'] for p in saved['operation_phases'] if p['scenario'] == phase['id']]
            require(labels == ['preparation', 'overhead_diagnostic', 'retirement'], 'phase boundaries merged')
            a, dose = phase['diagnostic_accounting'], phase['route_calibration']['closure_dose']
            if '-closure-' in phase['id']:
                require(dose['requested_usec'] == 600000 and dose['elapsed_usec'] >= 600000
                        and dose['start_usec'] >= phase['measurement_end_usec']
                        and dose['end_usec'] <= a['end_usec'] and dose['end_usec'] - dose['start_usec'] == dose['elapsed_usec']
                        and a['writer_drain_usec'] + dose['elapsed_usec'] <= a['finalization_usec'], 'saved dose scope does not reconcile')
            else:
                require(dose == dict(requested_usec=0,start_usec=None,end_usec=None,elapsed_usec=0), 'null control added a dose')
            frames += count
    require(all(v['outcome'] == 'not_run' for v in saved['diagnostic_heavy_ab']['workloads'].values()), 'calibration replaced legacy comparison')
    return {'passed': True, 'raw_frames': frames, 'workloads': 2, 'hardware_noise_calibrated': False,
            'shared_overhead_qualified': False, 'legacy_authoritative': True}
