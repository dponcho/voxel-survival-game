"""Saved preparation demand only. Never launches or reclassifies an engine run.

Whole-main bounds come from shared raw thread observations. Inner gaps are
direct differences of consecutive same-thread endpoints, never process minus
thread demand. Old codecs, reconciliations and cost verdicts remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

import shipping_cycles as cycles
import shipping_cycles_review as review
import shipping_observer as observer

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'docs/evidence/m1-shipping-observer-cloud-2026-10-19.json'
VERSION = 'm1-saved-preparation-demand-review-1'
require = cycles.require


def main_partition(boundaries):
    cycles.partition(boundaries)  # Preserve the original shared-boundary checks.
    observations = [o for b in boundaries for o in (b['before'], b['after'])]
    cycles.sequence(observations)
    thread = observations[0]['thread_id']
    require(cycles.uint(thread) > 0, 'Missing main-thread identity')
    bounds = [(cycles.uint(b['before']['reads'][1]['cycles']),
               cycles.uint(b['after']['reads'][2]['cycles'])) for b in boundaries]
    sections = [cycles.difference(a, b) for a, b in zip(bounds, bounds[1:])]
    midpoints = [cycles.midpoint(b)-cycles.midpoint(a) for a, b in zip(bounds, bounds[1:])]
    complete = cycles.difference(bounds[0], bounds[-1])
    midpoint = cycles.midpoint(bounds[-1])-cycles.midpoint(bounds[0])
    require(sum(midpoints) == midpoint and complete[0] <= midpoint <= complete[1],
            'Main section midpoint partition lost')
    return dict(thread_id=thread, boundary_bounds=[list(map(str, b)) for b in bounds],
                sections=[list(map(str, b)) for b in sections], section_midpoints=list(map(str, midpoints)),
                complete=list(map(str, complete)), midpoint=str(midpoint))


def inner_partition(boundaries, records):
    main = main_partition(boundaries)
    require(records, 'Missing raw spans')
    observer.ownership(records, max(r['lane'] for r in records))
    start = boundaries[0]['after']['reads'][2]
    end = boundaries[1]['before']['reads'][1]
    lo, hi = cycles.uint(start['cycles']), cycles.uint(end['cycles'])
    wall_lo, wall_hi = cycles.uint(start['wall_after_usec']), cycles.uint(end['wall_before_usec'])
    require(lo <= hi and wall_lo <= wall_hi, 'Reversed inner preparation window')
    roots = [r for r in records if r['lane'] == 1 and r['parent'] == 0]
    require(roots and all(str(r['thread']) == main['thread_id'] for r in roots),
            'Raw spans detached from shared main-thread identity')
    inside, crossing, outside = [], [], []
    for r in roots:
        first, last = r['reads'][0], r['reads'][3]
        wholly = wall_lo <= first['wall_before_usec'] <= last['wall_after_usec'] <= wall_hi
        if wholly:
            require(lo <= first['cycles'] <= last['cycles'] <= hi and r['start_section'] == 0,
                    'Inner root counter/context disagrees with wall enclosure')
            inside.append(r)
        elif first['wall_before_usec'] < wall_hi and last['wall_after_usec'] > wall_lo:
            crossing.append(r['id'])
        elif r['start_section'] == 0:
            outside.append(dict(id=r['id'], slot=observer.SLOTS[r['slot']-1],
                                cycles=[str(first['cycles']), str(last['cycles'])],
                                wall_usec=[str(first['wall_before_usec']), str(last['wall_after_usec'])]))
    result = dict(thread_id=main['thread_id'], endpoints=[str(lo), str(hi)],
                  wall_enclosure_usec=[str(wall_lo), str(wall_hi)], demand_cycles=str(hi-lo),
                  crossing_root_ids=crossing, outside_inner_preparation_roots=outside,
                  partition_available=not crossing)
    if crossing:
        # Never clip a crossing span, or assign its unknown partial demand to a gap.
        result.update(root_full_cycles=None, gap_cycles=None, gap_count=None)
        return result
    previous, gaps, root_full = lo, [], 0
    for r in inside:
        a, b = r['reads'][0]['cycles'], r['reads'][3]['cycles']
        require(previous <= a <= b <= hi, 'Inner roots overlap or escape counter window')
        gaps.append(a-previous)
        root_full += r['full_cycles']
        previous = b
    gaps.append(hi-previous)
    require(root_full+sum(gaps) == hi-lo, 'Same-thread root/gap union lost demand')
    gap_bytes = json.dumps(list(map(str, gaps)), separators=(',', ':')).encode()
    result.update(root_count=len(inside), root_full_cycles=str(root_full), gap_count=len(gaps),
                  nonzero_gap_count=sum(g > 0 for g in gaps), gap_cycles=str(sum(gaps)),
                  largest_gap_cycles=str(max(gaps)), gap_sequence_sha256=hashlib.sha256(gap_bytes).hexdigest())
    return result


def derive(artifact_root, evidence_path=EVIDENCE):
    artifact_root, evidence_path = Path(artifact_root), Path(evidence_path)
    evidence = cycles.read(evidence_path)
    pilot = evidence['pilot']
    folder = artifact_root/'raw'/Path(pilot['raw_folder'].replace('\\', '/')).name
    review.verify_manifest(folder, pilot['raw_file_manifest'])
    saved = cycles.read(artifact_root/'independent-audit.json')
    audit = observer.reconcile(folder, evidence['candidate']['build'],
                               ROOT/'game/diagnostics/shipping_observer_inventory.json')
    require(audit == saved['sequence'] == pilot['saved_audit'], 'Original saved audit differs')
    trials = cycles.read(folder/'observer-attribution.json')['trials']
    require(trials == pilot['trials'] and len(trials) == 5 and all(t['valid'] for t in trials),
            'Review requires the original complete five-trial prefix')
    rows = []
    for t in trials:
        main = main_partition(t['cycle_boundaries'])
        raw = observer.trial_ledger(folder, t)
        inner = inner_partition(t['cycle_boundaries'], raw['records'])
        require(inner['partition_available'], 'Saved inner preparation has crossing roots')
        phase = t['phases'][0]
        require(phase['phase'] == 'preparation', 'Missing preparation native frame witness')
        rows.append(dict(id=t['id'], main=main, inner_preparation=inner,
                         process_preparation_cycles=t['cycle']['sections'][0],
                         process_preparation_midpoint=t['cycle']['section_midpoints'][0],
                         preparation_native_frames=phase['frames'],
                         native_work=review.native_work(t)))
    pairs = []
    for a, b in ((rows[1], rows[4]), (rows[2], rows[3])):
        pairs.append(dict(trials=[a['id'], b['id']],
            process_preparation_midpoint_change=str(int(b['process_preparation_midpoint'])-int(a['process_preparation_midpoint'])),
            main_preparation_midpoint_change=str(int(b['main']['section_midpoints'][0])-int(a['main']['section_midpoints'][0])),
            inner_main_change=str(int(b['inner_preparation']['demand_cycles'])-int(a['inner_preparation']['demand_cycles'])),
            inner_root_full_change=str(int(b['inner_preparation']['root_full_cycles'])-int(a['inner_preparation']['root_full_cycles'])),
            inner_gap_change=str(int(b['inner_preparation']['gap_cycles'])-int(a['inner_preparation']['gap_cycles']))))
    require(all(r['native_work'] == rows[0]['native_work'] for r in rows), 'Saved native work differs')
    return dict(schema=VERSION, source_evidence_sha256=cycles.sha(evidence_path),
                source_runtime_commit=evidence['runtime_source_commit'],
                raw_files_verified=len(pilot['raw_file_manifest']),
                raw_bytes_verified=sum(v['bytes'] for v in pilot['raw_file_manifest'].values()),
                old_audit_reproduced=True, engine_runs=0, trials=rows, pairs=pairs,
                interpretation='Direct main-thread bounds and unowned inner gaps; no process/thread subtraction, frame normalization, causal owner or shipping-cost estimate.',
                measurement_valid=False, shipping_cost_estimate=None, qualified=False, target_performance='not_run')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-root', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    result = derive(args.artifact_root, args.evidence)
    if args.check:
        require(result == cycles.read(args.check), 'Committed preparation review differs')
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, engine_runs=0, raw_files=result['raw_files_verified'],
                          trials=len(result['trials']), qualified=False)))


if __name__ == '__main__':
    main()
