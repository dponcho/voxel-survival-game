"""Pure adversarial checks for the real-entry retirement capability reader."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/qa'))
import mesh_retirement as retirement
from preparation_owner_review import embedded


def fixture():
    # These counters are a retained raw observation, not a synthetic performance
    # claim. Case observations below are synthetic reader fixtures only.
    proof = retirement.read(ROOT/'docs/evidence/m1-preparation-owner-cloud-2026-10-25.json')
    prior = json.loads(embedded(proof['files']['release/controls.json']))['native']
    n = dict(schema='cairn-mesh-retirement-controls-1',passed=True,qualified=False,status='complete',
        fixture_start_usec=prior['fixture_start_usec'],fixture_end_usec=prior['fixture_end_usec'],
        fixture_limit_usec='5000000',process_start=copy.deepcopy(prior['process_start']),
        process_end=copy.deepcopy(prior['process_end']),thread=prior['process_start']['thread_id'],
        wire_case_cap=10,endpoint_hook_cleared=True,cases=[],native_start=copy.deepcopy(prior['native_start']),
        native_end=copy.deepcopy(prior['native_start']),external_alive_before_release=True,external_alive_after_release=False)
    base=int(n['process_start']['reads'][3]['wall_after_usec'])+10
    ids=[(1 << 63)+i+100 for i in range(10)];ids[3]=ids[4]=ids[2];ids[7]=ids[6];ids[9]=0
    def operation(calls,kind,payload,start):
        return dict(count=calls,bytes=payload,usec=5 if calls else 0,max_usec=5 if calls else 0,
            max_bytes=payload,max_start_usec=start if calls else 0,max_kind=kind if calls else 0)
    for i,expected in enumerate(retirement.CASES):
        name,before_surface,after_surface,before_refs,endpoint_alive,after_alive,postpone,calls=expected
        begin=base+i*100;surface=name in ('surface-0','surface-1');payload=192 if surface else 0
        deletion=operation(calls,2 if surface else 3,payload,begin+1);zero=operation(0,0,0,0)
        phase=dict(id=100+i,upload=copy.deepcopy(zero),deletion=copy.deepcopy(deletion),data_apply=copy.deepcopy(zero),
            frames=1,dropped_frames=0,tracing=True,peak_frame_operation_usec=deletion['usec'],peak_frame_upload_bytes=0,
            terrain_accounting_version=2,data_apply_nested_usec=0,peak_frame_terrain_usec=deletion['usec'],
            peak_single_upload_bytes=0,terrain_time_overruns=0,terrain_upload_overruns=0)
        frame=dict(native_frame=i+1,phase=100+i,start_usec=begin-1,end_usec=begin+11,phase_boundary=True,
            upload=copy.deepcopy(zero),deletion=copy.deepcopy(deletion),data_apply=copy.deepcopy(zero),
            data_apply_nested_usec=0,frame_terrain_usec=deletion['usec'],frame_upload_bytes_total=0,
            frame_single_upload_bytes=0,frame_time_limit_usec=1000,frame_upload_limit_bytes=524288)
        injected=251 if name=='postponed' else 0
        row=dict(name=name,entry='frozen-before-run' if i==0 else ('FreeMeshTask::add' if i==9 else 'FreeMeshTask::run'),
            object_id=str(ids[i]),object_alive_before_call=i!=9,references_before_call=before_refs,
            mesh_rid_valid_before_call=True if i!=9 else None,
            surfaces_before_call=before_surface,injected_admission_charge_usec=injected,charge_before_usec=injected,
            call_begin_order=str(i*3+1),call_end_order=str(i*3+3),call_begin_usec=str(begin),call_end_usec=str(begin+10),
            object_alive_after_call=after_alive,references_after_call=1 if after_alive else None,
            surfaces_after_call=after_surface,postpone=postpone,endpoint_calls=calls,endpoint_object_alive=endpoint_alive,
            endpoint_references=1 if endpoint_alive else None,
            endpoint_surfaces=after_surface if endpoint_alive and i!=0 else (0 if i==0 else None),
            endpoint_observed_usec=str(begin+3) if calls else None,endpoint_order=str(i*3+2) if calls else None,
            endpoint_thread=n['thread'] if calls else None,endpoint_operation_start_usec=str(begin+1) if calls else None,
            endpoint_payload_bytes=payload if calls else None,endpoint_surface=surface if calls else None,
            charge_after_usec=injected+deletion['usec'],phase=phase,frames=[frame])
        n['cases'].append(row)
    n['external_release_begin_usec']=str(base+520);n['external_release_end_usec']=str(base+521)
    build=dict(game_commit='f'*40,native_source_key='a'*64)
    return dict(schema=retirement.SCHEMA,build=build,native=n,passed=True,qualified=False,
        target_performance='not_run',route_executed=False),build


class MeshRetirementTests(unittest.TestCase):
    def test_rejected_and_corrected_lifetimes_shared_owner_and_null_reconcile(self):
        report,build=fixture();result=retirement.validate(report,build)
        self.assertTrue(result['rejected_lifetime_reproduced'])
        self.assertTrue(result['corrected_object_absent_before_ending_clock'])
        self.assertTrue(result['shared_owner_preserved']);self.assertFalse(result['qualified'])
        self.assertEqual(len(result['cases']),10)

    def test_all_seventeen_resigned_saved_faults_are_rejected(self):
        report,build=fixture()
        self.assertEqual(len(retirement.mutations(report,build)),17)

    def test_a_real_over_limit_elapsed_observation_does_not_become_a_performance_pass(self):
        report,build=fixture();rows=report['native']['cases'];r=rows[1]
        for i in range(2,10):
            row=rows[i]
            for key in ('call_begin_usec','call_end_usec','endpoint_observed_usec','endpoint_operation_start_usec'):
                if row[key] is not None:row[key]=str(int(row[key])+800)
            for frame in row['frames']:
                frame['start_usec']+=800;frame['end_usec']+=800
                if frame['deletion']['count']:frame['deletion']['max_start_usec']+=800
            if row['phase']['deletion']['count']:row['phase']['deletion']['max_start_usec']+=800
        report['native']['external_release_begin_usec']=str(int(report['native']['external_release_begin_usec'])+800)
        report['native']['external_release_end_usec']=str(int(report['native']['external_release_end_usec'])+800)
        for d in (r['phase']['deletion'],r['frames'][0]['deletion']):d['usec']=d['max_usec']=751
        r['charge_after_usec']=751;r['phase']['peak_frame_operation_usec']=751;r['phase']['peak_frame_terrain_usec']=751
        r['frames'][0]['frame_terrain_usec']=751
        r['call_end_usec']=str(int(r['call_begin_usec'])+756);r['frames'][0]['end_usec']=int(r['call_end_usec'])+1
        result=retirement.validate(report,build)
        self.assertTrue(result['passed']);self.assertFalse(result['operation_guards_valid'])
        self.assertFalse(result['qualified'])
        self.assertEqual(result['cases'][1]['operation_reasons'],['Individual deletion exceeded 0.75 ms'])

    def test_unobserved_endpoints_stay_null(self):
        for name in ('postponed','null-add'):
            for key,value in (('endpoint_references',0),('endpoint_observed_usec','0'),('endpoint_surface',False)):
                report,build=fixture();row=next(r for r in report['native']['cases'] if r['name']==name);row[key]=value
                with self.subTest(name=name,key=key),self.assertRaises(RuntimeError):retirement.validate(report,build)

    def test_boolean_counts_or_rounded_object_ids_cannot_replace_observations(self):
        changes=[lambda r:r['native']['cases'][1].__setitem__('references_before_call',True),
            lambda r:r['native']['cases'][1]['phase'].__setitem__('frames',True),
            lambda r:r['native']['cases'][1].__setitem__('object_id',float(1 << 63))]
        for change in changes:
            report,build=fixture();change(report)
            with self.assertRaises(RuntimeError):retirement.validate(report,build)

    def test_surface_steps_and_postponed_attempt_keep_their_actual_owner(self):
        for index in (3,7):
            report,build=fixture();report['native']['cases'][index]['object_id']=report['native']['cases'][1]['object_id']
            with self.assertRaisesRegex(RuntimeError,'object identity'):retirement.validate(report,build)

    def test_process_counter_failure_does_not_become_zero(self):
        report,build=fixture();report['native']['process_end']['reads'][1]['success']=False
        with self.assertRaises(RuntimeError):retirement.validate(report,build)

    def test_frozen_negative_native_body_cannot_be_silently_rewritten(self):
        self.assertEqual(retirement.source_metadata()['before_run_sha256'],retirement.BEFORE_SHA256)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);path=root/'native/sandbox_world/godot/retirement_before.h';path.parent.mkdir(parents=True)
            path.write_text((ROOT/path.relative_to(root)).read_text().replace('Ref<ArrayMesh> array = _mesh;','Ref<ArrayMesh> array;'))
            with self.assertRaisesRegex(RuntimeError,'Frozen rejected'):retirement.source_metadata(root)


if __name__=='__main__':unittest.main()
