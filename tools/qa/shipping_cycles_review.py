"""Saved-only review of the stopped v2 null control; never launches an engine.

Ratios use exact fractions. Nested thread witnesses describe only their enclosed
work and are never subtracted from, or added to, the complete process demand.
This review does not reclassify trials or estimate unrun shipping overhead.
"""
import argparse
from bisect import bisect_left
import csv
from fractions import Fraction
import json
from pathlib import Path

import shipping_cycles as cycles

ROOT = Path(__file__).resolve().parents[2]
SECTIONS = ('preparation', '+X', '-X', '+Z', 'lifecycle_tail')
WORK = ('generated', 'meshed', 'uploads', 'upload_bytes', 'stale_results', 'overloads')


def expansion_constraints(lower, upper, limit=cycles.LIMIT):
    """Necessary and sufficient constraints for one symmetric expansion E >= 0.

    [lower-E, upper+E] contains zero iff E >= zero_required. Its width is
    strictly below limit iff E < width_budget. Neither is a fitted correction.
    """
    cycles.require(all(type(v) in (int, Fraction) for v in (lower, upper, limit)),
                   'Range constraints require exact integers or fractions')
    lower, upper, limit = map(Fraction, (lower, upper, limit))
    cycles.require(lower <= upper and limit > 0, 'Invalid raw range/limit')
    zero_required = max(Fraction(0), lower, -upper)
    width_budget = (limit-(upper-lower))/2
    return dict(zero_containment_requires_at_least=zero_required,
                strict_width_requires_less_than=width_budget,
                jointly_feasible=zero_required < width_budget,
                narrowest_zero_containing_width=upper-lower+2*zero_required)


def null_components(trials):
    cycles.require(len(trials) == 4 and all(cycles.usable(t) for t in trials),
                   'Review requires four complete usable null trials')
    a = [cycles.interval(trials[i]['cycle']['complete']) for i in (0, 3)]
    b = [cycles.interval(trials[i]['cycle']['complete']) for i in (1, 2)]
    alo, ahi = min(v[0] for v in a), max(v[1] for v in a)
    blo, bhi = min(v[0] for v in b), max(v[1] for v in b)
    lower, upper = Fraction(blo-ahi, ahi), Fraction(bhi-alo, alo)
    actual = cycles.envelope(trials)
    drift, marker = actual['matching_section_drift'], actual['terminal_marker_uncertainty']
    width = upper-lower+2*drift+2*marker
    cycles.require(width == actual['upper']-actual['lower'], 'Width decomposition differs')
    return dict(reference_lower_cycles=str(alo), raw_lower=lower, raw_upper=upper,
                raw_width=upper-lower, matching_section_width=2*drift, marker_width=2*marker,
                expanded_width=width, original_envelope=actual,
                expansion_constraints=expansion_constraints(lower, upper),
                drift_budget_with_saved_raw_range_and_marker=(cycles.LIMIT-(upper-lower))/2-marker,
                original_null_usable=cycles.null_usable(actual))


def section_pair(a, b, reference):
    rows = []
    for name, x, y, xm, ym in zip(SECTIONS, a['cycle']['sections'], b['cycle']['sections'],
                                 a['cycle']['section_midpoints'], b['cycle']['section_midpoints']):
        xl, xh = cycles.interval(x)
        yl, yh = cycles.interval(y)
        signed = cycles.natural(ym)-cycles.natural(xm)
        conservative = max(abs(xl-yh), abs(xh-yl))
        cycles.require(conservative >= abs(signed), 'Section midpoint outside difference bound')
        rows.append(dict(section=name, signed_midpoint_difference_cycles=str(signed),
                         conservative_absolute_difference_cycles=str(conservative),
                         fraction=Fraction(conservative, reference)))
    net = sum(int(r['signed_midpoint_difference_cycles']) for r in rows)
    absolute = sum(abs(int(r['signed_midpoint_difference_cycles'])) for r in rows)
    bound = sum(int(r['conservative_absolute_difference_cycles']) for r in rows)
    cycles.require(net == int(b['cycle']['midpoint'])-int(a['cycle']['midpoint']),
                   'Section/complete midpoint differences disagree')
    return dict(trials=[a['id'], b['id']], sections=rows, signed_complete_difference_cycles=str(net),
                absolute_midpoint_difference_sum_cycles=str(absolute),
                conservative_difference_sum_cycles=str(bound),
                boundary_uncertainty_expansion_cycles=str(bound-absolute),
                cancellation_cycles=str(absolute-abs(net)), fraction=Fraction(bound, reference))


def native_work(trial):
    snapshots = [b['snapshot'] for b in trial['cycle_boundaries']]
    cycles.require(len(snapshots) == 6, 'Missing native boundary snapshot')
    rows = []
    for name, a, b in zip(SECTIONS, snapshots, snapshots[1:]):
        row = {}
        for key in WORK:
            cycles.require(type(a[key]) is int and type(b[key]) is int and 0 <= a[key] <= b[key],
                           'Native lifetime work counter decreased or changed type: '+key)
            row[key] = b[key]-a[key]
        rows.append(dict(section=name, **row))
    return rows


def verify_manifest(folder, manifest):
    folder = Path(folder)
    actual = {str(p.relative_to(folder)).replace('\\', '/') for p in folder.rglob('*') if p.is_file()}
    cycles.require(actual == set(manifest), 'Raw file population differs from committed evidence')
    for name, expected in manifest.items():
        path = folder/name
        cycles.require(not path.is_symlink() and path.resolve().is_relative_to(folder.resolve()),
                       'Unsafe saved-evidence path')
        cycles.require(path.stat().st_size == expected['bytes'] and cycles.sha(path) == expected['sha256'],
                       'Changed saved-evidence bytes: '+name)


def common_observer_records(folder, trial):
    """All rows have already passed the unchanged raw trial reconciler."""
    rows = [json.loads(line) for line in (folder/(trial['id']+'-cycles.jsonl')).read_text().splitlines()]
    cycles.require(len(rows) == cycles.TICKS and trial['dose_enabled'] is False,
                   'Expected the original zero-request witnesses')
    legs = []
    for leg, name in enumerate(SECTIONS[1:4]):
        bounds = [0, 0]
        for row in rows[leg*1440:(leg+1)*1440]:
            cycles.require(row['request_cycles'] == '0' and row['updates'] == 0 and row['digest'] is None,
                           'Null witness contains positive work')
            for i, value in enumerate(cycles.demand(row['start'], row['end'], 'thread')):
                bounds[i] += value
        legs.append(dict(section=name, rows=1440, thread_cycles=list(map(str, bounds))))
    total = [sum(int(leg['thread_cycles'][i]) for leg in legs) for i in (0, 1)]
    complete = cycles.interval(trial['cycle']['complete'])
    with (folder/(trial['id']+'-frames.csv')).open(encoding='utf-8-sig', newline='') as f:
        callbacks = list(csv.DictReader(f))
    # Use the shared wall boundaries, rather than allocating callbacks by tick.
    # Entry exactly at a boundary belongs to the preceding section. Preparation
    # has no rows in this gameplay CSV; its native phase frame count is separate.
    ends = trial['route_clocks_usec'][1:]+[trial['end_usec']]
    counts = [0]*4
    for row in callbacks:
        index = bisect_left(ends, int(row['entry_usec']))
        cycles.require(index < len(counts), 'Callback outside saved complete boundary')
        counts[index] += 1
    accounting = trial['report']['diagnostic_accounting']
    return dict(zero_request_witness=dict(rows=len(rows), legs=legs, thread_cycles=list(map(str, total)),
                    fraction_of_complete_process=[Fraction(total[0], complete[1]), Fraction(total[1], complete[0])],
                    scope='Enclosed main-thread native call only; excludes subsequent exact arithmetic, JSON/pose formatting and writes. Not total common-observer cost.'),
                gameplay_callback_rows=dict(zip(SECTIONS[1:], counts)),
                native_phase_frames={p['phase']: p['frames'] for p in trial['phases']},
                callback_wall_usec={k: accounting[k] for k in ('callback_usec', 'switched_usec', 'shared_usec')},
                cycle_jsonl_bytes=trial['dose_bytes'], pose_csv_bytes=trial['pose_bytes'])


def review(evidence_path, folder, inventory_path):
    evidence_path, folder, inventory_path = map(Path, (evidence_path, folder, inventory_path))
    evidence = cycles.read(evidence_path)
    cycles.require(evidence['schema'] == 'cairn-m1-shipping-cpu-cycles-evidence-1'
                   and evidence['method'] == cycles.VERSION and evidence['policy'] == cycles.POLICY,
                   'Unknown stopped-evidence identity')
    pilot, build = evidence['pilot'], evidence['candidate']['build']
    cycles.require(pilot['engine_launches'] == 1 and pilot['trials_count'] == 5
                   and evidence['status']['shipping_cost_estimate'] is None,
                   'Review requires the stopped five-trial sequence')
    verify_manifest(folder, pilot['raw_file_manifest'])
    raw = cycles.read(folder/'shipping-cycles.json')
    cycles.require(raw['trials'] == pilot['trials'] and raw['build'] == build, 'Raw/committed trials differ')
    audit = cycles.reconcile(folder, build, inventory_path)
    cycles.require(audit == pilot['saved_audit'] and audit['measurement_valid'] is False
                   and audit['cycle_cost'] == 'inconclusive' and audit['qualified'] is False,
                   'Original saved audit/verdict changed')
    trials = pilot['trials']
    components = null_components(trials[1:5])
    reference = int(components['reference_lower_cycles'])
    records = []
    for t in trials:
        records.append(dict(id=t['id'], group=t['group'], cycle=t['cycle'],
                            elapsed_sections_usec=t['sections_usec'], callback_count=t['callback_count'],
                            native_work_by_section=native_work(t), observers=common_observer_records(folder, t)))
    work_equal = all(r['native_work_by_section'] == records[0]['native_work_by_section'] for r in records[1:])
    return cycles.exact_json(dict(schema='cairn-m1-shipping-cycles-null-review-1', engine_executed=False,
        inputs=dict(evidence_file=evidence_path.name, evidence_sha256=cycles.sha(evidence_path),
                    raw_files=len(pilot['raw_file_manifest']), inventory_sha256=cycles.sha(inventory_path),
                    exported_game_commit=build['game_commit'], native_source_key=build['native_source_key'],
                    reader_sha256={p: cycles.sha(ROOT/p) for p in
                        ('tools/qa/shipping_cycles_review.py', 'tools/qa/shipping_cycles.py',
                         'tools/qa/shipping_diagnostics.py', 'tools/qa/cpu_cycle_capability.py')}),
        original=dict(evidence_integrity=audit['evidence_integrity'], trial_guards_valid=audit['trial_guards_valid'],
                      measurement_valid=False, cycle_cost='inconclusive', shipping_cost_estimate=None,
                      qualified=False, target_performance='not_run'),
        null=components, section_pairs=dict(off=section_pair(trials[1], trials[4], reference),
                                           on=section_pair(trials[2], trials[3], reference)),
        matching_native_work=work_equal, trials=records,
        interpretation=dict(cause_isolated=False, total_common_observer_cpu_cost='unavailable',
                            callback_normalization_applied=False, fitted_correction_applied=False,
                            process_and_thread_totals_added=False, cycles_converted_to_time=False),
        disposition='Retain the stopped result. Attribute common observers prospectively before any further qualification sequence.',
        target_action_required_now=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT/'docs/evidence/m1-shipping-cpu-cycles-cloud-2026-10-18.json')
    parser.add_argument('--raw', type=Path, required=True, help='Original extracted per-sequence raw folder')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true', help='Compare an existing review without writing')
    args = parser.parse_args()
    result = review(args.evidence, args.raw, ROOT/'game/diagnostics/shipping_cycles_inventory.json')
    if args.check:
        cycles.require(cycles.read(args.output) == result, 'Saved review differs')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print('Saved null review verified; no engine ran, no cost or target qualification follows.')


if __name__ == '__main__':
    main()
