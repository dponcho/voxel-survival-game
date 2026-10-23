import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from frontier_boundary import FIXTURE, classification, cells
from frontier_edit import (COORDINATES, MODES, NEW, NULL_FIELDS, OLD, TARGETS,
                           reconcile, route_poses, stages)


def empty_totals():
    return dict(count=0, bytes=0, usec=0, max_usec=0, max_bytes=0, max_start_usec=0, max_kind=0)


def unavailable():
    return dict(status='unavailable', reason='invalid bounded input', blocks=None, probe_usec=None)


def trace(pending, outcome='submitted', enabled=True):
    result = dict(enabled=enabled, accepted=1, submitted=0, superseded=0, cancelled=0, timeout=0,
                  unavailable=0, overflow=0, pending=pending, pending_high_water=1, queued=0,
                  max_usec=0, p95_upper_usec=0)
    if not pending:
        result[outcome] = 1
        result['queued'] = int(enabled)
        if outcome == 'submitted':
            result['max_usec'], result['p95_upper_usec'] = 40, 1000
    return result


def meshes(index, mode):
    blocks = []
    complete = index >= 5 and not mode.startswith('cancel')
    for i, coord in enumerate(COORDINATES):
        if coord in NEW and (index < 5 or mode == 'stationary'):
            block = dict(block=coord, state='missing', **{k: None for k in NULL_FIELDS})
        else:
            has_mesh = coord not in ([7, 0, 0], [7, 1, 0])
            edited = coord in TARGETS and index >= 1
            revision = 100+i+(500 if edited else 0)
            refs = 2 if coord in OLD and mode != 'stationary' and index == 4 else 1
            block = dict(block=coord, state='visible' if has_mesh else 'confirmed_empty', loaded=True,
                         visible=True, has_mesh=has_mesh, mesh_id=str(10000+i+(10000 if edited and complete else 0)) if has_mesh else None,
                         mesh_viewers=refs, collision_viewers=0, queued_update=edited and index == 1,
                         desired_revision=revision, submitted_revision=revision if not edited or complete else 100+i)
        blocks.append(block)
    return dict(status='measured', reason='', probe_usec=5, blocks=blocks)


def report():
    fog = json.loads(FIXTURE.read_text())['fog']
    cases, operations = [], []
    before, crossed = route_poses()
    for workers in (1, 2):
        for mode in MODES:
            base = (len(cases)+1)*1000
            cancellation = mode.startswith('cancel')
            outcome = 'cancelled' if cancellation else 'submitted'
            rows = []
            for i, stage in enumerate(stages(mode)):
                pose = before if i < 3 or mode == 'stationary' else crossed
                block = [8, 0, -1]
                distance = ((128-pose[0])**2 + 10**2)**.5
                sample = dict(status='measured', candidate_regions=24, checked_regions=20, ready_regions=10,
                              empty_regions=1, unready_regions=10, frontier_distance_m=distance, block=block, mesh_state='missing')
                _, clearance, transmittance = classification(sample, fog)
                rows.append(dict(stage=stage, usec=base+20+i*10, engine_frame=base+i,
                    camera=pose, base_pose=[pose[0],pose[1]-1.65,pose[2]], yaw=-1.57079637050629,
                    preparation_cells=cells(before if i<=4 or mode=='stationary' else crossed),
                    sample=sample, assessment=dict(status='measured', evaluation='passed', fog_clearance_m=clearance, fog_transmittance=transmittance),
                    original_targets_submitted=[True]*4, terrain=dict(resident_mesh=511, resident_data=867, pending_mesh=2 if i==1 else 0),
                    native=dict(retired_meshes=0, overloads=0), edit_trace=trace(int(i<5),outcome) if i else {'status':'not_run'},
                    meshes=meshes(i,mode)))
            phases = []
            for label, lo, hi in [('preparation',base,base+25), ('edit-transfer',base+27,base+300), ('retirement',base+301,base+500)]:
                pid = len(operations)+1
                totals = empty_totals()
                row = dict(phase=pid, native_frame=pid, start_usec=lo, end_usec=hi, phase_boundary=True,
                           upload=totals.copy(), deletion=totals.copy())
                operations.append(row)
                native = dict(id=pid, upload=totals.copy(), deletion=totals.copy(), frames=1, dropped_frames=0,
                              tracing=True, peak_frame_operation_usec=0, peak_frame_upload_bytes=0)
                phases.append(dict(id=pid, label=f'{mode}-{workers}:{label}', begin_before_usec=lo-1, begin_usec=lo+1,
                                   end_before_usec=hi-1, end_usec=hi+1, native=native, operation_failures=[], operation_evaluation='passed'))
            event_end = base+320 if cancellation else base+69
            event = dict(id=1, voxel=[128,6,10], accepted_usec=base+29, end_usec=event_end,
                         latency_usec=event_end-base-29, outcome=outcome,
                         targets=[dict(block=c, revision=600+COORDINATES.index(c), submitted=not cancellation) for c in TARGETS])
            cases.append(dict(name=f'{mode}-{workers}', mode=mode, workers=workers, accepted=True, settled=True, concurrent=True,
                drained=True, nodes_freed=True, released_preparation_viewers=4, begin_usec=base+10, cleanup_begin_usec=base+302, end_usec=base+502,
                rows=rows, phases=phases, peaks=dict(resident_mesh=511, resident_data=867, retired_meshes=0, retired_high_water=0, overloads=0),
                final_native={k:0 for k in ('generation_jobs','mesh_jobs','result_jobs','main_jobs','retired_meshes','retired_high_water','overloads')},
                events=[event], trace=trace(0,outcome,False), before_trace_stop=trace(0,outcome), trace_stop_usec=base+501,
                trace_stop_end_usec=base+501, terminal_source='native',
                policy=dict(viewer_count=4, required_visual_radius_m=96, data_radius_m=128), edit_evaluation='passed', operation_evaluation='passed',
                cancellation_meshes=copy.deepcopy(rows[-1]['meshes']), cancellation_trace=copy.deepcopy(rows[-1]['edit_trace']), drained_meshes=unavailable()))
    missing = dict(status='measured', reason='', probe_usec=1,
                   blocks=[dict(block=[200,0,200], state='missing', **{k:None for k in NULL_FIELDS})])
    summary = dict(schema=1, version='m1-frontier-edit-1', passed=True, failures=[], qualified=False, target_performance='not_run',
                   build={'fixture':'independent synthetic histories'}, cases=cases, fog=fog, row_cap=160, file_cap_bytes=1048576,
                   operation_row_cap=20000, operation_file_cap_bytes=8388608,
                   missing_input=dict(status='unavailable', evaluation='inconclusive', fog_clearance_m=None, fog_boundary_m=None, fog_transmittance=None),
                   sampler_controls={k:unavailable() for k in ('null_terrain','empty_request','oversized_request','malformed_request','duplicate_request')})
    summary['sampler_controls']['missing_block'] = missing
    return summary, operations


def save(folder, summary, operations):
    encoded = ''.join(json.dumps(row)+'\n' for row in operations)
    summary['operation_rows'], summary['operation_bytes'] = len(operations), len(encoded.encode())
    # The runtime writes exact UTF-8 bytes, including LF, on Windows too.
    (folder/'operations.jsonl').write_bytes(encoded.encode('utf-8'))
    # Godot sorts Dictionary keys; their insertion order is not evidence.
    (folder/'summary.json').write_text(json.dumps(summary, sort_keys=True), encoding='utf-8')


def scale_clocks(summary, operations, factor):
    for case in summary['cases']:
        for key in ('begin_usec', 'cleanup_begin_usec', 'end_usec', 'trace_stop_usec', 'trace_stop_end_usec'):
            case[key] *= factor
        for row in case['rows']:
            row['usec'] *= factor
        for phase in case['phases']:
            for key in ('begin_before_usec', 'begin_usec', 'end_before_usec', 'end_usec'):
                phase[key] *= factor
        for event in case['events']:
            for key in ('accepted_usec', 'end_usec', 'latency_usec'):
                event[key] *= factor
        for t in [case['trace'], case['before_trace_stop'], case['cancellation_trace']] + [r['edit_trace'] for r in case['rows']]:
            if t.get('submitted'):
                t['max_usec'] = case['events'][0]['latency_usec']
                t['p95_upper_usec'] = (t['max_usec']//1000+1)*1000
    for row in operations:
        row['start_usec'] *= factor
        row['end_usec'] *= factor


class FrontierEdit(unittest.TestCase):
    def test_exact_route_and_saved_reference_revision_histories(self):
        self.assertEqual(route_poses(), [[31.991718292236328,1.6510000228881836,10.0], [32.10005187988281,1.6510000228881836,10.0]])
        summary, operations = report()
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            save(folder,summary,operations)
            r = reconcile(folder,summary['build'])
            self.assertEqual((r['cases'],r['native_rows'],r['mesh_observations'],r['operation_phases']), (8,102,1100,24))
            self.assertEqual(len(r['submitted']),4)
            self.assertEqual(len(r['cancellations']),4)
            self.assertFalse(r['qualified'])
            # Existing collection close is explicit cancellation, and a current
            # native completion may win deferred deletion. Neither is fabricated.
            for kind in ('collection_stop','native_completion'):
                s, raw = report()
                c=s['cases'][2 if kind=='collection_stop' else 3]
                event=c['events'][0]
                if kind=='collection_stop':
                    c['before_trace_stop']=trace(1)
                    c['terminal_source']='collection_stop'
                    event.update(end_usec=c['trace_stop_usec'],latency_usec=c['trace_stop_usec']-event['accepted_usec'])
                else:
                    event['outcome']='submitted'
                    for target in event['targets']: target['submitted']=True
                    duration=event['latency_usec']
                    c['trace']=trace(0,'submitted',False)
                    c['before_trace_stop']=trace(0,'submitted')
                    for t in (c['trace'],c['before_trace_stop']):
                        t['max_usec']=duration
                        t['p95_upper_usec']=(duration//1000+1)*1000
                save(folder,s,raw)
                self.assertTrue(reconcile(folder,s['build'])['passed'])
                c['terminal_source']='native' if kind=='collection_stop' else 'collection_stop'
                save(folder,s,raw)
                with self.assertRaises(RuntimeError): reconcile(folder,s['build'])

    def test_corrupt_workload_revisions_references_nulls_and_drain_fail(self):
        summary, operations = report()
        mutations = {
            'missing-case': lambda s: s['cases'].pop(),
            'reordered-case': lambda s: s['cases'].reverse(),
            'missing-row': lambda s: s['cases'][0]['rows'].pop(),
            'stalled': lambda s: s['cases'][0].update(settled=False),
            'not-dispatched': lambda s: s['cases'][1]['rows'][2]['terrain'].update(pending_mesh=1),
            'lost-accepted': lambda s: s['cases'][1]['rows'][3]['edit_trace'].update(pending=0),
            'lost-overlap': lambda s: s['cases'][1]['rows'][4]['meshes']['blocks'][1].update(mesh_viewers=1),
            'dropped-resource': lambda s: s['cases'][1]['rows'][4]['meshes']['blocks'][1].update(loaded=False),
            'superseded-revision': lambda s: s['cases'][1]['rows'][4]['meshes']['blocks'][2].update(desired_revision=999),
            'stale-submission': lambda s: s['cases'][1]['rows'][-1]['meshes']['blocks'][2].update(submitted_revision=999),
            'unedited-replaced': lambda s: s['cases'][1]['rows'][-1]['meshes']['blocks'][1].update(mesh_id='123'),
            'no-real-replacement': lambda s: s['cases'][1]['rows'][-1]['meshes']['blocks'][2].update(mesh_id='10002'),
            'stop-cancelled': lambda s: s['cases'][2]['before_trace_stop'].update(pending=1,cancelled=0),
            'nodes-survived': lambda s: s['cases'][0].update(nodes_freed=False),
            'undrained': lambda s: s['cases'][0]['final_native'].update(result_jobs=1),
            'null-zero': lambda s: s['sampler_controls']['null_terrain'].update(probe_usec=0),
            'missing-zero': lambda s: s['sampler_controls']['missing_block']['blocks'][0].update(desired_revision=0),
            'absent-observation': lambda s: s['cases'][0]['rows'][0].update(meshes=unavailable()),
            'ack-duration': lambda s: s['cases'][0]['events'][0].update(latency_usec=200001),
            'ack-histogram': lambda s: s['cases'][0]['trace'].update(p95_upper_usec=0),
            'failed-workload': lambda s: s.update(passed=False,failures=['lost edit']),
            'qualified': lambda s: s.update(qualified=True),
            'bounds': lambda s: s['cases'][0]['peaks'].update(resident_mesh=513),
            'drain-high-water': lambda s: s['cases'][0]['final_native'].update(retired_high_water=769),
        }
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            for label,mutate in mutations.items():
                bad=copy.deepcopy(summary)
                mutate(bad)
                save(folder,bad,operations)
                with self.subTest(label=label), self.assertRaises(RuntimeError):
                    reconcile(folder,bad['build'])

    def test_750_guard_exact_rows_phase_closure_and_io(self):
        for duration in (749,750,751):
            summary, operations=report()
            scale_clocks(summary,operations,40)
            value=dict(count=1,bytes=1024,usec=duration,max_usec=duration,max_bytes=1024,max_start_usec=40001,max_kind=1)
            operations[0]['upload']=value.copy()
            phase=summary['cases'][0]['phases'][0]
            phase['native'].update(upload=value.copy(),peak_frame_operation_usec=duration,peak_frame_upload_bytes=1024)
            if duration>750:
                phase.update(operation_failures=['Individual upload exceeded 0.75 ms'],operation_evaluation='failed')
                summary['cases'][0]['operation_evaluation']='failed'
            with tempfile.TemporaryDirectory() as temp:
                folder=Path(temp)
                save(folder,summary,operations)
                result=reconcile(folder,summary['build'])
                self.assertEqual(bool(result['failed_operation_phases']), duration>750)
                for kind in ('aggregate','phase-end','crossed-clock','reordered','missing','io','guard'):
                    bad,raw=copy.deepcopy(summary),copy.deepcopy(operations)
                    if kind=='aggregate': bad['cases'][0]['phases'][0]['native']['upload']['count']=2
                    if kind=='phase-end': raw[0]['phase_boundary']=False
                    if kind=='crossed-clock':
                        raw[0]['upload']['max_start_usec']=raw[0]['end_usec']-duration+1
                        bad['cases'][0]['phases'][0]['native']['upload']['max_start_usec']=raw[0]['upload']['max_start_usec']
                    if kind=='reordered': raw.reverse()
                    if kind=='missing': raw.pop()
                    if kind=='guard': bad['cases'][0]['phases'][0]['operation_evaluation']='failed' if duration<=750 else 'passed'
                    save(folder,bad,raw)
                    if kind=='io': (folder/'operations.jsonl').write_text('')
                    with self.subTest(duration=duration,kind=kind), self.assertRaises(RuntimeError):
                        reconcile(folder,bad['build'])
        # The largest individual operation has the first tie's identity, not
        # the sum of both frames or the last equal-duration operation.
        summary, operations=report()
        scale_clocks(summary,operations,40)
        first=operations[0]
        second=copy.deepcopy(first)
        first.update(end_usec=40400,phase_boundary=False)
        second.update(start_usec=40400,native_frame=2)
        first['upload']=dict(count=1,bytes=512,usec=250,max_usec=250,max_bytes=512,max_start_usec=40001,max_kind=1)
        second['upload']=dict(count=2,bytes=1024,usec=500,max_usec=250,max_bytes=512,max_start_usec=40401,max_kind=1)
        operations.insert(1,second)
        phase=summary['cases'][0]['phases'][0]['native']
        phase.update(frames=2,upload=dict(count=3,bytes=1536,usec=750,max_usec=250,max_bytes=512,max_start_usec=40001,max_kind=1),
                     peak_frame_operation_usec=500,peak_frame_upload_bytes=1024)
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            save(folder,summary,operations)
            self.assertTrue(reconcile(folder,summary['build'])['passed'])
            phase['upload']['max_start_usec']=40401
            save(folder,summary,operations)
            with self.assertRaises(RuntimeError): reconcile(folder,summary['build'])
