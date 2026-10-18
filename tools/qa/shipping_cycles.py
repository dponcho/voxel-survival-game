"""Independent v2 raw-cycle interval/rational reader. Never runs an engine.

Each process total already includes its threads. Thread demand witnesses only
the known-positive dose; it is never added to the process total or timed in Hz.
"""
import copy
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re

from cpu_cycle_capability import uint, observation, sequence, demand, MAX_U64
from shipping_diagnostics import require, read, sha, poses as route_poses, frames, envelope as elapsed_envelope
from shipping_diagnostics import trial_evidence as common_trial_evidence
from terrain_budget import reasons as operation_reasons

VERSION = 'm1-shipping-cpu-cycles-1'
POLICY = 'm1-shipping-diagnostics-2'
INVENTORY = 'm1-shipping-inventory-2'
LIMIT = Fraction(1, 100)
TICKS = 4320
LABELS = ['start', 'prepared', '+X', '-X', '+Z', 'complete-after-report-flush']


def natural(value):
    require(type(value) is str and re.fullmatch(r'0|[1-9][0-9]*', value) is not None,
            'Cycle demand must be a canonical exact decimal string')
    return int(value)


def interval(value):
    require(type(value) is list and len(value) == 2, 'Missing cycle interval')
    lo, hi = map(natural, value)
    require(lo <= hi, 'Reversed cycle interval')
    return lo, hi


def midpoint(bounds):
    lo, hi = bounds
    return lo + (hi-lo)//2


def difference(a, b):
    require(b[0] >= a[0] and b[1] >= a[1], 'Decreasing cycle endpoints')
    return max(0, b[0]-a[1]), b[1]-a[0]


def boundary(value):
    a, b = value['before'], value['after']
    sequence([a, b])
    expected = [a['reads'][0]['cycles'], b['reads'][3]['cycles']]
    require(value['bounds'] == expected and uint(b['reads'][3]['wall_after_usec']) <= value['wall_usec'],
            'Boundary does not enclose the common snapshot')
    require(type(value['snapshot']) is dict and 'generation_jobs' in value['snapshot'], 'Missing boundary snapshot')
    return tuple(map(uint, expected))


def partition(boundaries):
    require(len(boundaries) == 6 and [b['label'] for b in boundaries] == LABELS, 'Missing/shared section boundary')
    values = [boundary(b) for b in boundaries]
    for a, b in zip(boundaries, boundaries[1:]):
        sequence([a['after'], b['before']])
        require(a['wall_usec'] <= b['wall_usec'], 'Reversed boundary wall times')
    sections = [difference(a, b) for a, b in zip(values, values[1:])]
    mids = [midpoint(b)-midpoint(a) for a, b in zip(values, values[1:])]
    complete = difference(values[0], values[-1])
    total = midpoint(values[-1])-midpoint(values[0])
    require(sum(mids) == total and complete[0] <= total <= complete[1], 'Midpoint partition lost')
    return dict(complete=list(map(str, complete)), midpoint=str(total),
                sections=[list(map(str, s)) for s in sections], section_midpoints=list(map(str, mids)))


def usable(t):
    try:
        require(t.get('valid') is True, 'Invalid trial')
        c = t['cycle']
        complete = interval(c['complete'])
        interval(c['marker'])
        require(complete[0] > 0 and len(c['sections']) == len(c['section_midpoints']) == 5, 'Incomplete cycle demand')
        for s in c['sections']:
            interval(s)
        mid = natural(c['midpoint'])
        require(sum(map(natural, c['section_midpoints'])) == mid and complete[0] <= mid <= complete[1], 'Midpoint partition')
        return True
    except (RuntimeError, KeyError, TypeError, ValueError):
        return False


def envelope(trials):
    if len(trials) != 4 or not all(usable(t) for t in trials):
        return {}
    a, b = [[interval(trials[i]['cycle']['complete']) for i in indices] for indices in ((0, 3), (1, 2))]
    alo, ahi = min(v[0] for v in a), max(v[1] for v in a)
    blo, bhi = min(v[0] for v in b), max(v[1] for v in b)
    sections = [[interval(s) for s in t['cycle']['sections']] for t in trials]
    drift = max(sum(max(abs(x[0]-y[1]), abs(x[1]-y[0])) for x, y in zip(sections[i], sections[j]))
                for i, j in ((0, 3), (1, 2)))
    marker = max(interval(trials[i]['cycle']['marker'])[1]+interval(trials[j]['cycle']['marker'])[1]
                 for i in (0, 3) for j in (1, 2))
    amid = sum(natural(trials[i]['cycle']['midpoint']) for i in (0, 3))
    bmid = sum(natural(trials[i]['cycle']['midpoint']) for i in (1, 2))
    return dict(lower=Fraction(blo-ahi, ahi)-Fraction(drift+marker, alo),
                upper=Fraction(bhi-alo, alo)+Fraction(drift+marker, alo),
                point=Fraction(bmid-amid, amid), matching_section_drift=Fraction(drift, alo),
                terminal_marker_uncertainty=Fraction(marker, alo))


def null_usable(n):
    return bool(n and n['lower'] <= 0 <= n['upper'] and n['upper']-n['lower'] < LIMIT
                and n['matching_section_drift'] < LIMIT)


def controls(trials):
    result = dict(valid=False, null_valid=False, positive_valid=False, null={}, positive={}, dose_fractions=[])
    if len(trials) < 5 or not all(usable(t) for t in trials[:9]):
        return result
    n = envelope(trials[1:5])
    result.update(null=n, null_valid=null_usable(n))
    if len(trials) < 9:
        return result
    p = envelope(trials[5:9])
    result['positive'] = p
    if not p:
        return result
    a = [interval(trials[i]['cycle']['complete']) for i in (5, 8)]
    alo, ahi = min(v[0] for v in a), max(v[1] for v in a)
    ref = natural(trials[5]['cycle']['midpoint'])
    positive_ok = p['lower'] >= LIMIT and p['matching_section_drift'] < LIMIT
    for t in trials[6:8]:
        d = t['dose']
        try:
            dl, dh = interval(d['cycles'])
            require(d.get('valid') is True and d.get('ticks') == TICKS
                    and d.get('reference_cycles') == str(ref)
                    and d.get('requested_tick_cycles') == str((ref+50*TICKS-1)//(50*TICKS))
                    and natural(d['requested_tick_cycles']) > 0
                    and dl >= natural(d['requested_tick_cycles'])*TICKS, 'Invalid positive dose')
        except (RuntimeError, KeyError, TypeError, ValueError):
            return result
        lo, hi = Fraction(dl, ahi), Fraction(dh, alo)
        result['dose_fractions'].append([lo, hi])
        positive_ok &= lo > LIMIT and hi <= Fraction(3, 100) and p['upper'] >= lo and p['lower'] <= hi
    result.update(positive_valid=bool(positive_ok), valid=bool(result['null_valid'] and positive_ok))
    return result


def evaluate(trials):
    c = controls(trials)
    result = dict(policy=POLICY, method=VERSION, qualified=False, outcome='inconclusive', controls=c,
                  shipping={}, threshold=LIMIT)
    if not all(usable(t) for t in trials) or not c['valid'] or len(trials) != 13:
        return result
    e = envelope(trials[9:13])
    result['shipping'] = e
    if not e or e['matching_section_drift'] >= LIMIT or e['point'] < 0:
        return result
    if e['upper'] < LIMIT:
        result['outcome'] = 'passed'
    elif e['lower'] >= LIMIT:
        result['outcome'] = 'failed'
    return result


def exact_json(value):
    if isinstance(value, Fraction):
        return dict(n=str(value.numerator), d=str(value.denominator))
    if isinstance(value, dict):
        return {k: exact_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [exact_json(v) for v in value]
    return value


def rational_json(value):
    if type(value) is dict and set(value) == {'n', 'd'}:
        n, d = value['n'], value['d']
        require(type(n) is str and re.fullmatch(r'0|-?[1-9][0-9]*', n) is not None and natural(d) > 0,
                'Malformed exact rational')
        return Fraction(int(n), int(d))
    if isinstance(value, dict):
        return {k: rational_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [rational_json(v) for v in value]
    return value


def compare_method(actual, expected):
    converted = rational_json(actual)
    require(all(converted.get(k) == v for k, v in expected.items()), 'V2 exact runtime/independent method mismatch')


def work_record(work, request, enabled):
    """Verify one actual native witness; the hash cache avoids rehashing identical updates."""
    require(work['schema'] == 'cairn-cpu-cycle-dose-1' and work['request_cycles'] == request
            and work['enabled'] is enabled and work['passed'] is True and work['reason'] == 'measured'
            and work['bytes_per_update'] == 4096 and work['update_cap'] == 512 and work['wall_cap_usec'] == '50000'
            and work['error'] == 0 and work['capped'] is False and work['counter_failed'] is False
            and work['hash_failed'] is False, 'Missing/failed native cycle dose')
    sequence([work['start'], work['end']])
    lo, hi = demand(work['start'], work['end'], 'thread')
    begin, end = uint(work['wall_start_usec']), uint(work['wall_end_usec'])
    require(begin <= uint(work['start']['reads'][0]['wall_before_usec'])
            <= uint(work['end']['reads'][3]['wall_after_usec']) <= end and end-begin <= 50000,
            'Native dose wall bracket/cap failed')
    if enabled:
        updates = work['updates']
        require(type(updates) is int and 0 < updates < 512 and lo >= uint(request) > 0 and work['reached'] is True,
                'Native dose missing work/request or update cap hit')
        if updates not in HASHES:
            HASHES[updates] = hashlib.sha256(b'Z'*(4096*updates)).hexdigest()
        require(work['digest'] == HASHES[updates], 'Native SHA digest/update count differs')
    else:
        require(request == '0' and work['updates'] == 0 and work['digest'] is None and work['reached'] is False,
                'Undeclared positive SHA work')
    return lo, hi


HASHES = {}


def validate_method_controls(report, build):
    require(report['schema'] == 'cairn-shipping-cycles-controls-1' and report['method'] == VERSION
            and report['policy'] == POLICY and report['passed'] is True and report['qualified'] is False
            and report['fixed_work_dispatch'] is True and report['build'] == build, 'Missing v2 executable controls/identity')
    expected = {**{'shipping-'+str(n): outcome for n, outcome in
                  ((-1,'inconclusive'), (0,'passed'), (500000,'passed'), (999999,'passed'), (1000000,'failed'), (1500000,'failed'))},
                'same-total-section-drift':'inconclusive', 'terminal-uncertainty':'inconclusive', 'masked-positive':'inconclusive',
                **{'dose-band-'+lo+'-'+hi:'inconclusive' for lo, hi in
                   [('1000000','1000000'),('3000000','3000000'),('3000001','3000001'),('999999','2000000')]},
                **{'invalid-trial-'+str(i):'inconclusive' for i in range(13)},
                'uncertain-boundaries':'inconclusive', 'midpoint-partition-loss':'inconclusive'}
    require([c['name'] for c in report['cases']] == list(expected), 'Missing/reordered exact method controls')
    for case in report['cases']:
        calculated = evaluate(case['trials'])
        compare_method(case['assessment'], calculated)
        require(calculated['outcome'] == expected[case['name']], 'Incorrect known v2 method outcome')
    refs = [0, 1, 215999, 216000, 216001, 9007199254740993, 1 << 63, MAX_U64]
    require(report['request_vectors'] == [[str(v), str((v+216000-1)//216000)] for v in refs], 'Exact cycle request ceiling differs')
    require(report['exact_vectors'] == dict(above_signed=str((1<<63)+9007199254740993),
                max_midpoint=str(MAX_U64-1), negative=str(9007199254740993-(1<<63)), cross_product=str(MAX_U64**2)),
            'Unsigned/cross-product exact arithmetic failed')
    require([c['name'] for c in report['boundary_cases']] == ['above-signed-domain','numeric','failed','reversed','missing'],
            'Missing native boundary arithmetic/failure controls')
    for i, case in enumerate(report['boundary_cases']):
        if not i:
            require(case['partition'] == partition(case['boundaries']), 'Shared uint64 boundary partition differs')
        else:
            require(case['partition'] == {}, 'Failed native boundary was admitted')
            try:
                partition(case['boundaries'])
            except (RuntimeError, KeyError, TypeError, ValueError):
                pass
            else:
                raise RuntimeError('Independent reader accepted failed boundary: '+case['name'])
    work_record(report['native_zero'], '0', False)
    witness = work_record(report['native_positive'], '1', True)
    sequence([report['native_zero']['end'], report['native_positive']['start']])
    require(len(report['native_rejected']) == 4 and all(v['passed'] is False and v['reason'] == 'invalid request or thread'
            for v in report['native_rejected']), 'Native invalid decimal request accepted')
    return dict(passed=True, method_cases=len(expected), exact_request_vectors=len(refs), boundary_cases=5,
                native_positive_cycles=list(map(str, witness)), qualified=False)


SOURCES = ('m1_cycle_exact.gd', 'm1_shipping_cycles_method.gd', 'm1_shipping_cycles_runtime.gd',
           'm1_shipping_cycles_tests.gd', 'm1_full_height_runtime.gd', 'benchmark.gd', 'title.gd')


def source_metadata(root):
    root = Path(root)
    return dict(policy=POLICY, method=VERSION,
                inventory_sha256=sha(root/'game/diagnostics/shipping_cycles_inventory.json'),
                sources_sha256={name: sha(root/'game/scripts'/name) for name in SOURCES},
                native_probe_sha256=sha(root/'native/sandbox_world/godot/cpu_cycle_probe.cpp'),
                native_dose_core_sha256=sha(root/'native/sandbox_world/core/cycle_dose.h'))


def verify_metadata(build, contents, root):
    root = Path(root)
    require(build['shipping_cycles'] == source_metadata(root), 'V2 source/inventory/native identity differs')
    require(contents['diagnostics/shipping_cycles_inventory.json'] == (root/'game/diagnostics/shipping_cycles_inventory.json').read_bytes(),
            'Published v2 executable inventory differs')
    for name in SOURCES:
        stem = 'scripts/'+name[:-3]
        require(contents[stem+'.gdc'].startswith(b'GDSC')
                and ('res://'+stem+'.gdc').encode() in contents[stem+'.gd.remap'], 'Missing v2 tokenized script: '+name)


def saved_controls(reports, build):
    result = {}
    for label in ('editor','release'):
        name = 'shipping-cycles-controls-'+label
        result[label] = validate_method_controls(read(Path(reports)/(name+'.json')), build)
        require(result[label] == read(Path(reports)/(name+'-validation.json')), 'Saved v2 method controls differ')
    return result


def expected_protocol():
    result = [('warmup', 0, 'bare', False)]
    for group in ('null', 'positive', 'shipping'):
        result += [(group, i, 'shipping' if group == 'shipping' and i in (1,2) else 'bare',
                    group == 'positive' and i in (1,2)) for i in range(4)]
    return result


def verify_prefix(trials, abort_reason):
    require(1 <= len(trials) <= 13 and type(abort_reason) is str, 'Missing/oversized finite sequence')
    actual = [(t['group'], t['index'], t['diagnostic_mode'], t['dose_enabled']) for t in trials]
    require(actual == expected_protocol()[:len(trials)], 'Sequence repeated, padded, reordered or changed mode')
    for i, t in enumerate(trials):
        require(t['id'] == 'AB-H2-cycles-%s-%d' % (t['group'], t['index']), 'Unexpected trial identity')
        if i < len(trials)-1:
            require(t['complete'] is True and t['valid'] is True, 'Sequence continued after failed/partial trial')
        if i >= 5:
            require(null_usable(envelope(trials[1:5])), 'Positive quartet started without a usable null')
        if i >= 9:
            require(controls(trials[:9])['valid'], 'Shipping started without usable controls')
    if len(trials) < 13 and trials[-1]['valid'] is True:
        require((len(trials) == 5 and not null_usable(envelope(trials[1:5])))
                or (len(trials) == 9 and not controls(trials)['valid']), 'Premature or padded finite stop')
    if len(trials) < 13 or not trials[-1]['valid']:
        require(bool(abort_reason), 'Missing explicit early stop reason')


def dose_evidence(folder, t, partial=False):
    path = folder/(t['id']+'-cycles.jsonl')
    require(sha(path) == t['dose_sha256'] and 0 <= path.stat().st_size <= 33554432,
            'Missing/changed/oversized native cycle evidence')
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines()]
    count = t['ticks'] if partial else t['report']['simulation_ticks']
    require(len(rows) == count == t['dose_rows'] <= TICKS and path.stat().st_size == t['dose_bytes'],
            'Missing/extra native witness per real physics tick')
    total = [0, 0]
    updates = 0
    all_passed = True
    previous = None
    for tick, w in enumerate(rows, 1):
        require(w['tick'] == tick and w['request_cycles'] == t['dose']['requested_tick_cycles'],
                'Dose request changed after B1 or detached from real ticks')
        if w['passed'] is True:
            bounds = work_record(w, t['dose']['requested_tick_cycles'], t['dose_enabled'])
            require(w['cycles'] == list(map(str, bounds)), 'Actual native dose interval differs')
            if previous is not None:
                sequence([previous, w['start']])
            previous = w['end']
            if t['dose_enabled']:
                for i in (0,1): total[i] += bounds[i]
                updates += w['updates']
        else:
            # A failed native control is retained, never admitted to estimation.
            require(partial and tick == count and t['dose']['valid'] is False
                    and w.get('reason') != 'measured', 'Unlabelled or ignored native failure')
            all_passed = False
    d = t['dose']
    require(d['valid'] is all_passed and d['ticks'] == (count if t['dose_enabled'] else 0)
            and (not all_passed or (d['cycles'] == list(map(str,total)) and d['hash_updates'] == updates)),
            'Native per-tick dose totals/validity differ')
    return dict(rows=count, positive=t['dose_enabled'], total_cycles=list(map(str,total)), hash_updates=updates,
                witness_valid=all_passed)


def derive_checks(t):
    r, p, v = t['report'], t['report']['peaks'], t['report']['edit_visibility']
    phases, final = t['phases'], t['native_final']
    edits = (v.get('accepted') == v.get('submitted') == 288 and 0 < v.get('p95_upper_usec', -1) <= 100000
             and 0 <= v.get('max_usec', -1) <= 200000 and all(v.get(k) == 0 for k in
             ('pending','queued','overflow','superseded','cancelled','timeout','unavailable')))
    return dict(integration=not t['integration_failures'], io=not t['io_failed'],
                drained=all(final.get(k) == 0 for k in ('generation_jobs','mesh_jobs','result_jobs','main_jobs','retired_meshes')),
                operations=len(phases) == 3 and not any(operation_reasons(p) for p in phases),
                resources=(0 < p.get('private_bytes', -1) <= 2147483648 and 0 < p.get('working_set', -1) <= 1610612736
                           and 0 <= p.get('pool_voxel_total', -1) <= 201326592), edits=edits,
                route_clocks=len(t['route_clocks_usec']) == 4, ticks=r['simulation_ticks'] == TICKS,
                accepted=r['accepted_proxy_edits'] == 288, rejected=r['rejected_proxy_edits'] == 0,
                saves=r['proxy_autosaves'] == 72, actors=r['actor_ticks'] == 103680,
                readiness=r['readiness_stops'] == 0, policy=not t['policy_failed'],
                coverage=r['fog_frontier'].get('exposed_samples') == 0 and r['fog_frontier'].get('evaluation') == 'passed')


def trial_evidence(folder, t, inventory_hash):
    name = t['id']
    require(t['inventory_sha256'] == inventory_hash and t['diagnostic_mode'] in ('bare','shipping'), 'V2 trial inventory/mode differs')
    require(sha(folder/(name+'-poses.csv')) == t['pose_sha256'], 'Changed physics evidence')
    if not t['complete']:
        require(t['valid'] is False and read(folder/(name+'-partial.json')) == t and t['abort_reason'],
                'Partial trial was substituted or qualified')
        with (folder/(name+'-poses.csv')).open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        require(len(rows) == t['ticks'] <= TICKS and [int(r['tick']) for r in rows] == list(range(1,len(rows)+1)),
                'Partial physics prefix missing or padded')
        evidence = dose_evidence(folder, t, partial=True)
        return dict(id=name, complete=False, evidence_integrity='retained_partial', measurement_valid=False,
                    abort_reason=t['abort_reason'], dose=evidence)
    cp, bp = folder/(name+'-complete.json'), folder/(name+'-boundary.json')
    complete, saved_boundary = read(cp), read(bp)
    require(all(t.get(k) == v for k, v in complete.items()), 'Complete v2 trial report differs from batch')
    require(saved_boundary['complete_sha256'] == sha(cp), 'Complete v2 report hash differs')
    require(all(t.get(k) == v for k, v in saved_boundary.items() if k not in ('complete_sha256','cycle')),
            'Post-flush cycle boundary differs from saved terminal marker')
    expected = partition(t['cycle_boundaries'])
    require(saved_boundary['cycle'] == expected, 'Marker changed shared partition')
    marker = t['marker_cycles']
    sequence([t['cycle_boundaries'][-1]['after'], marker['start'], marker['end']])
    marker_bounds = demand(marker['start'], marker['end'], 'process')
    require(t['end_usec'] <= t['marker_start_usec'] <= t['marker_end_usec']
            and uint(marker['start']['reads'][3]['wall_after_usec']) <= t['marker_start_usec']
            and t['marker_end_usec'] <= uint(marker['end']['reads'][0]['wall_before_usec']),
            'Terminal marker write escaped measured cycle bounds')
    expected['marker'] = list(map(str, marker_bounds))
    require(t['cycle'] == expected, 'V2 raw boundary intervals/midpoint partition differ')
    clocks = [b['wall_usec'] for b in t['cycle_boundaries']]
    require(clocks == [t['start_usec']]+t['route_clocks_usec']+[t['end_usec']]
            and t['sections_usec'] == [b-a for a,b in zip(clocks,clocks[1:])]
            and sum(t['sections_usec']) == t['duration_usec'], 'Elapsed section partition differs')
    dose = dose_evidence(folder, t)
    checks = derive_checks(t)
    require(t['pre_boundary_checks'] == checks, 'Work/operation guard flags differ from saved evidence')
    checks.update(cycles=True, dose=dose['witness_valid'], marker=True)
    require(t['checks'] == checks and t['valid'] is all(checks.values()) and t['operation_ok'] is checks['operations']
            and t['drained'] is checks['drained'], 'Invalid work/counter/operation guards used as a valid measurement')
    shared = {}
    if all(v for k,v in checks.items() if k != 'operations'):
        # Reuse the unchanged common fixed-work, pose, frame, edit, resource and
        # lifecycle verifier. Its old wall-dose columns stay explicitly zero;
        # the native v2 JSONL above is the only positive witness.
        view = copy.deepcopy(t)
        view['checks'] = {k:v for k,v in checks.items() if k not in ('cycles','dose','marker')}
        view['dose_enabled'] = False
        view['dose'] = dict(actual_usec=0, hash_updates=0, ticks=0, requested_tick_usec=0)
        shared = common_trial_evidence(folder, view, inventory_hash, method_version=VERSION, verify_saved_boundary=False)
    return dict(id=name, complete=True, evidence_integrity='verified', measurement_valid=all(checks.values()),
                checks=checks, operation_failures=[dict(phase=p['phase'], reasons=operation_reasons(p))
                  for p in t['phases'] if operation_reasons(p)], cycle=expected, dose=dose, common=shared)


def reconcile(folder, build, inventory_path):
    folder = Path(folder)
    p, s = read(folder/'shipping-cycles.json'), read(folder/'summary.json')
    require(p['version'] == VERSION and p['policy'] == POLICY and p['build'] == s['build'] == build
            and p['inventory'] == read(inventory_path) and p['inventory']['version'] == INVENTORY
            and p['inventory_sha256'] == sha(inventory_path) and p['qualified'] is False
            and p['target_performance'] == 'not_run' and s['qualified'] is False
            and s['benchmark_mode'] == 'shipping-cycles' and p['max_trials'] == 13, 'V2 pilot identity differs')
    trials = p['trials']
    verify_prefix(trials, p['abort_reason'])
    reference = None
    for t in trials:
        if t['dose_enabled']:
            require(reference is not None and t['dose']['reference_cycles'] == reference
                    and t['dose']['requested_tick_cycles'] == str((natural(reference)+216000-1)//216000),
                    'Positive A0 request changed before/between B1/B2')
        if t['group'] == 'positive' and t['index'] == 0:
            reference = t.get('cycle', {}).get('midpoint')
    records = [trial_evidence(folder, t, sha(inventory_path)) for t in trials]
    expected = evaluate(trials)
    compare_method(p['assessment'], expected)
    require(p['assessment']['abort_reason'] == p['abort_reason'] and (expected['outcome'] != 'inconclusive' or p['abort_reason']),
            'Inconclusive pilot missing explicit stop decision')
    guards = all(r['measurement_valid'] for r in records)
    valid = guards and expected['controls']['valid']
    require(p['trial_guards_valid'] is guards and p['measurement_valid'] is valid
            and s['shipping_diagnostic_qualification'] == p['assessment'], 'V2 batch validity/assessment differs')
    require(s['scenarios'] == [t['report'] for t in trials if t['complete']]
            and s['operation_phases'] == [phase for t in trials for phase in t['phases']], 'V2 lifecycle/batch differs')
    for group, start in (('null',1),('positive',5),('shipping',9)):
        if len(trials) >= start+4:
            expected_elapsed = elapsed_envelope(trials[start:start+4])
            actual = p['elapsed_descriptive'][group]
            require(actual.get('valid') is bool(expected_elapsed), 'Elapsed descriptive validity differs')
            if expected_elapsed:
                require(all(math.isclose(actual[k], float(v), rel_tol=1e-10, abs_tol=1e-12)
                            for k,v in expected_elapsed.items()), 'Elapsed descriptive envelope differs')
    return dict(passed=True, evidence_integrity='verified' if all(t['complete'] for t in trials) else 'retained_partial',
                measurement_valid=valid, trial_guards_valid=guards, cycle_cost=expected['outcome'],
                assessment=exact_json(expected), abort_reason=p['abort_reason'], trials=len(trials), records=records,
                qualified=False, target_performance='not_run')
