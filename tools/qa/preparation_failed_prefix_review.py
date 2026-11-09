"""Review the consumed preparation prefix, retained owners and release lifetime.

Saved bytes and pinned source only. No engine, candidate rebuild, qualification
reclassification, thread/process arithmetic or replacement declaration.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import zipfile
import zlib

import preparation_demand_ci as launch
import preparation_demand_review as old_review
import preparation_demand_saved_recheck as recovery
import shipping_cycles_review as work
import terrain_budget

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'docs/evidence/m1-preparation-demand-cloud-2026-10-25.json'
PROOF_SHA256 = 'adf7012ca93db9a235f58e6b1346e5d15e79fa61b5cbc3de6aec4bb5340a2a08'
UPSTREAM = ROOT/'docs/evidence/m1-retirement-call-source-2026-10-26.json'
UPSTREAM_SHA256 = 'd21072d9846d6825e3808f5cb007701d539d875c67bc21799614181d89899573'
VERSION = 'm1-preparation-failed-prefix-review-1'
require, read, sha = launch.require, launch.read, launch.sha


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive_files(path, expected):
    """Verify the exact archive and its complete, contained file population."""
    path = Path(path)
    require(path.stat().st_size == expected['bytes'] <= 12*1024*1024 and
            sha(path) == expected['sha256'], 'Original archive bytes/digest differ')
    with zipfile.ZipFile(path) as z:
        items = z.infolist()
        names = [i.filename for i in items]
        require(1 <= len(items) <= 128 and len(names) == len(set(names)) and
                set(names) == set(expected['files']), 'Archive file population differs')
        require(sum(i.file_size for i in items) <= 80*1024*1024, 'Expanded archive exceeds bound')
        files = {}
        for item in items:
            parts = item.filename.split('/')
            require(all(p not in ('', '.', '..') and ':' not in p and '\\' not in p for p in parts)
                    and not item.is_dir() and not stat.S_ISLNK(item.external_attr >> 16),
                    'Archive path escaped or is not a regular file')
            data = z.read(item)
            require(expected['files'][item.filename] == dict(bytes=len(data), sha256=digest(data)),
                    'Original archive member differs')
            files[item.filename] = data
        return files


def embedded(item):
    require(item['encoding'] == 'base64+zlib' and type(item['bytes']) is int and
            0 <= item['bytes'] <= launch.prep.CAP, 'Embedded record byte bound differs')
    raw = base64.b64decode(item['data'], validate=True)
    decoder = zlib.decompressobj()
    data = decoder.decompress(raw, item['bytes']+1)
    require(len(data) == item['bytes'] and decoder.eof and not decoder.unconsumed_tail and
            not decoder.unused_data and digest(data) == item['sha256'], 'Embedded record differs')
    return data


def inner_main(boundaries, records):
    """Exact same-thread root/gap union after the original ownership reader."""
    main = old_review.main_partition(boundaries)
    start, end = boundaries[0]['after']['reads'][2], boundaries[1]['before']['reads'][1]
    lo, hi = int(start['cycles']), int(end['cycles'])
    wall_lo, wall_hi = int(start['wall_after_usec']), int(end['wall_before_usec'])
    require(lo <= hi and wall_lo <= wall_hi, 'Reversed safe preparation enclosure')
    roots = [r for r in records if r['lane'] == 1 and r['parent'] == 0]
    require(roots and all(str(r['thread']) == main['thread_id'] for r in roots), 'Changed main owner')
    inside, crossing, outside = [], [], []
    for row in roots:
        first, last = row['reads'][0], row['reads'][3]
        require(all(s['flags'] == 3 and s['error'] == 0 and type(s['cycles']) is int
                    for s in row['reads']), 'Unavailable raw root endpoint')
        if wall_lo <= first['wall_before_usec'] <= last['wall_after_usec'] <= wall_hi:
            require(row['start_section'] == row['end_section'] == 0 and
                    lo <= first['cycles'] <= last['cycles'] <= hi and
                    row['full_cycles'] == last['cycles']-first['cycles'], 'Root counter/context differs')
            inside.append(row)
        elif first['wall_before_usec'] < wall_hi and last['wall_after_usec'] > wall_lo:
            crossing.append(row['id'])
        elif row['start_section'] == 0:
            outside.append(row['id'])
    result = dict(main_thread=main['thread_id'], endpoints=list(map(str, (lo, hi))),
        wall_enclosure_usec=[wall_lo, wall_hi], demand_cycles=str(hi-lo),
        crossing_root_ids=crossing, outside_root_ids=outside, partition_available=not crossing)
    if crossing:
        return dict(result, root_full_cycles=None, gap_cycles=None, root_count=None, roots_by_slot=None)
    previous, gaps, by_slot = lo, [], {}
    for row in inside:
        first, last = row['reads'][0]['cycles'], row['reads'][3]['cycles']
        require(previous <= first <= last <= hi, 'Root overlap/reversal in preparation')
        gaps.append(first-previous)
        by_slot[row['slot']] = by_slot.get(row['slot'], 0)+row['full_cycles']
        previous = last
    gaps.append(hi-previous)
    full = sum(by_slot.values())
    require(full+sum(gaps) == hi-lo, 'Root/gap partition lost demand')
    return dict(result, root_full_cycles=str(full), gap_cycles=str(sum(gaps)), root_count=len(inside),
        roots_by_slot={str(k): str(v) for k, v in sorted(by_slot.items())},
        gap_count=len(gaps), largest_gap_cycles=str(max(gaps)),
        gap_sequence_sha256=digest(json.dumps(list(map(str, gaps)), separators=(',', ':')).encode()))


def failed_event(trial, records):
    require(trial['complete'] is True and trial['valid'] is False and
            trial['checks']['operations'] is False, 'Failed completed trial required')
    failed = [p for p in trial['phases'] if terrain_budget.reasons(p)]
    require(len(failed) == 1 and failed[0]['phase'] == 'retirement', 'Failure phase differs')
    phase = failed[0]
    maximum = phase['deletion']
    require(terrain_budget.reasons(phase) == ['Individual deletion exceeded 0.75 ms'] and
            all(type(maximum[k]) is int for k in ('max_start_usec', 'max_usec', 'max_bytes', 'max_kind')) and
            maximum['max_usec'] > 750 and maximum['max_bytes'] > 0 and maximum['max_kind'] == 2,
            'Retained failure is not a measured surface-removal maximum')
    start, end = maximum['max_start_usec'], maximum['max_start_usec']+maximum['max_usec']
    require(trial['start_usec'] <= start < end <= trial['end_usec'], 'Failure outside trial')
    main = [r for r in records if r['lane'] == 1]
    overlap = [dict(id=r['id'], slot=r['slot'], start_section=r['start_section'],
        end_section=r['end_section']) for r in main
        if r['reads'][0]['wall_before_usec'] < end and r['reads'][3]['wall_after_usec'] > start]
    return dict(trial=trial['id'], phase='retirement', kind=2, kind_name='surface-removal path',
        wall_start_usec=start, wall_end_usec=end, elapsed_usec=maximum['max_usec'], limit_usec=750,
        excess_usec=maximum['max_usec']-750, associated_payload_bytes=maximum['max_bytes'],
        phase_deletion_count=maximum['count'], phase_deletion_bytes=maximum['bytes'],
        phase_deletion_usec=maximum['usec'], raw_operation_trace=trial['raw_operation_trace'],
        main_spans_overlapping_event=overlap, direct_preparation_scopes_admit_only_section=0,
        event_thread_cycle_demand=None, os_driver_cause=None,
        qualification='Complete failed measurement retained; no cause or operation pass inferred.')


def retained_release_order(free):
    """Bind the finding to this frozen source; do not require future code to keep the defect."""
    sequence = ('Ref<ArrayMesh> array = _mesh;', '} else { _mesh.unref(); }',
                'cairn::record_deletion(bytes, start, surface);', '    }\n    ~FreeMeshTask()')
    require(all(free.count(s) == 1 for s in sequence) and
            [free.index(s) for s in sequence] == sorted(free.index(s) for s in sequence),
            'Reviewed temporary-owner lifetime changed; make a new review')
    return [free.index(s) for s in sequence]


def source_witness(root=ROOT, upstream=UPSTREAM):
    root = Path(root)
    require(sha(upstream) == UPSTREAM_SHA256, 'Pinned upstream source witness differs')
    upstream_record = read(upstream)
    pins = read(root/'build/dependencies.lock.json')
    require(all(f['commit'] == pins['godot' if f['repository'] == 'godotengine/godot' else 'voxel']['commit']
                for f in upstream_record['files']), 'Source witness pin differs')
    patches = read(root/'build/patches/voxel/m1-admission.json')
    free = next(p['replacement'] for p in patches if p['path'] == 'terrain/free_mesh_task.h')
    retained_release_order(free)
    parent = next(p['replacement'] for p in patches if p['path'] == 'engine/voxel_engine.cpp'
                  and 'record_data_apply' in p['replacement'])
    require(parent.count('cairn::record_data_apply(start, previous);') == 1 and
            '_time_spread_task_runner.process' not in parent, 'Parent bracket source differs')
    files = ('native/sandbox_world/core/operation_metrics.h', 'native/sandbox_world/godot/m1_hooks.h',
             'native/sandbox_world/core/preparation_observer.h', 'build/patches/voxel/m1-admission.json',
             'build/patches/voxel/m1-preparation.json')
    return dict(owned_source_sha256={p: sha(root/p) for p in files},
        free_mesh_task=free, completed_task_parent=parent, upstream=upstream_record,
        finding='An owning local Ref<ArrayMesh> survives record_deletion. On the empty ArrayMesh path, '
            '_mesh.unref() cannot be the last release while that local Ref remains; its destructor '
            'and possible ArrayMesh destruction/free_rid occur after the operation timer/charge.',
        scope='Source-level lifetime finding, not an executed destruction control. Complete trial '
            'process bounds still include this work. No GPU/deferred/OS cost or explanation of the kind-2 overrun follows.')


def derive(artifact, candidate, evidence=EVIDENCE):
    require(sha(evidence) == PROOF_SHA256, 'Frozen consumed-process proof differs')
    proof = read(evidence)
    require(proof['process']['engine_processes'] == proof['process']['spawn_attempts'] == 1 and
            proof['decision']['declared_process_consumed'] is True and
            proof['original_ci']['run']['conclusion'] == 'failure' and
            proof['saved_recheck_ci']['run']['conclusion'] == 'success', 'Consumed process identity differs')
    require(launch.plan() is False and launch.recheck_plan() is False, 'A consumed preparation request is enabled')
    data = archive_files(artifact, proof['original_archive'])
    require(digest(data['independent-audit.json']) == proof['original_windows_audit_sha256'],
            'Original independent audit differs')
    for name, item in proof['embedded_files'].items():
        require(embedded(item) == data[name], 'Embedded original differs from downloaded archive')
    original = json.loads(data['independent-audit.json'])
    preflight = launch.review.derive(candidate)
    require(preflight == json.loads(data['preflight-review.json']) and
            preflight['candidate'] == proof['candidate'] == original['candidate'], 'Frozen candidate/review differs')
    with zipfile.ZipFile(candidate) as z:
        build = json.loads(z.read('BUILD_INFO.json'))
    require(json.loads(data['process-result.json']) == proof['process'] and
            json.loads(data['reservation.json']) == proof['reservation'] and
            json.loads(data['runtime-result.json']) == proof['runtime_result'], 'Retained launch identity differs')
    with tempfile.TemporaryDirectory(prefix='cairn-failed-prefix-review-') as td:
        folder = Path(td)
        for name, body in data.items():
            path = folder/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        restored = recovery.restore_sources(folder)
        require(launch.files(folder) == proof['audited_files'] and restored == proof['source_snapshot_recovery'],
                'Original manifest or recovered source provenance differs')
        raw = next((folder/'raw').iterdir())
        sequence = launch.prep.reconcile(raw, build, ROOT/'game/diagnostics/preparation_demand_inventory.json')
        faults = launch.saved_faults(raw, build)
        require(sequence == original['sequence'] == proof['sequence'] and
                faults == original['saved_faults'] == proof['saved_faults'], 'Original sequence/fault audit differs')
        for item in proof['downloaded_replays'].values():
            result = json.loads(embedded(item['report']))
            require(result == item['result'] == proof['local_replay'] and result['sequence'] == sequence
                    and result['engine_executed'] is False, 'Retained independent replay differs')
        batch = read(raw/'preparation-demand-attribution.json')
        require(len(batch['trials']) == 3 and [t['valid'] for t in batch['trials']] == [True, True, False],
                'Original failed prefix changed')
        rows, failure = [], None
        for trial in batch['trials']:
            ledger = launch.prep.trial_ledger(raw, trial)
            require(ledger['passed'] is True, 'Owner ledger unavailable')
            main = old_review.main_partition(trial['cycle_boundaries'])
            partition = inner_main(trial['cycle_boundaries'], ledger['records'])
            rows.append(dict(id=trial['id'], complete=trial['complete'], valid=trial['valid'],
                failed_checks=[k for k, v in trial['checks'].items() if v is not True],
                process_preparation_bounds=trial['cycle']['sections'][0],
                process_preparation_midpoint=trial['cycle']['section_midpoints'][0],
                main_preparation_bounds=main['sections'][0], main_preparation_midpoint=main['section_midpoints'][0],
                inner_main=partition, direct_native_owners=ledger['ownership']['native'],
                preparation_native_work=work.native_work(trial)[0],
                preparation_native_frames=trial['phases'][0]['frames'], records=ledger['record_count'],
                owner_session_destroyed=trial['preparation_owners']['session_destroyed'],
                recorder_disposed=trial['observer_disposal']['disposed']))
            if trial['valid'] is False:
                failure = failed_event(trial, ledger['records'])
        require(all(t['preparation_native_work'] == rows[0]['preparation_native_work'] for t in rows),
                'Recorded preparation work differs')
    return dict(schema=VERSION, reader_sha256=sha(Path(__file__)), source_evidence_sha256=PROOF_SHA256,
        upstream_source_evidence_sha256=UPSTREAM_SHA256, candidate=preflight['candidate'],
        archive_sha256=proof['original_archive']['sha256'], archive_files_verified=len(data),
        audited_files_verified=len(proof['audited_files']), source_snapshot_recovery=restored,
        original_sequence_audit_reproduced=True, saved_corruptions=faults,
        engine_processes_executed_by_review=0, total_retained_engine_processes=1,
        trials=rows, failure=failure, source_witness=source_witness(),
        valid_bare_trials=sum(t['valid'] and '-bare-' in t['id'] for t in rows),
        complete_bare_quartet=False, comparative_null=None, shipping_cost_estimate=None,
        attribution_valid=False, measurement_valid=False, qualified=False, target_performance='not_run',
        decision=dict(next_task='Correct empty-ArrayMesh last-owner release timing and prove real destruction inside the existing operation bracket.',
            new_process_declared=False, repeat_consumed_process=False, laptop_action=False,
            preparation_cause='Unavailable: direct owner spans leave most main preparation demand in same-thread gaps.',
            failure_cause='Unavailable: recorded kind-2 overrun has no event-specific CPU/OS/driver attribution.',
            next_acceptance=['Preserve the operational start/end clocks, 750 us individual guard, cumulative native-frame charging and phase carry.',
                'Release every local/task-owned mesh reference before recording deletion; retain shared external owners honestly.',
                'Use bounded actual production-path controls for empty/surfaced/non-ArrayMesh resources, shared owners, postponement and real last-owner destruction.',
                'Demonstrate the frozen rejected lifetime and corrected destruction order, with destructor witness before the measured endpoint and independently rejected corruptions.',
                'Build new matching native editor/debug/release and portable candidate; run required correctness/package checks and saved Windows/Linux audits.',
                'Keep every consumed pilot/request false. No attribution route, retry, fitted correction, payload reduction, threshold change or laptop/M2 task in that increment.']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    result = derive(args.artifact, args.candidate)
    if args.check:
        require(result == read(args.check), 'Committed failed-prefix review differs')
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, engine_processes=0, files=result['audited_files_verified'],
        trials=len(result['trials']), failure_usec=result['failure']['elapsed_usec'], qualified=False)))


if __name__ == '__main__':
    main()
