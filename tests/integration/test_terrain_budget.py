import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from terrain_budget import reasons, reconcile_rows


def evidence(upload=600, deletion=600, data=0, nested=0, payload=20):
    row = dict(native_frame=4,phase=1,start_usec=10,end_usec=5000,upload_count=1,upload_bytes=payload,
        upload_usec=upload,upload_max_usec=upload,upload_max_bytes=payload,upload_max_start_usec=10,
        deletion_usec=deletion,data_apply_count=int(data > 0),data_apply_usec=data,
        data_apply_max_usec=data,data_apply_max_start_usec=10 if data else 0,data_apply_nested_usec=nested,
        frame_terrain_usec=upload+deletion+data-nested,frame_upload_bytes_total=payload,
        frame_single_upload_bytes=payload,frame_time_limit_usec=1000,frame_upload_limit_bytes=524288)
    op=lambda n:dict(max_usec=n)
    phase=dict(terrain_accounting_version=2,frames=1,dropped_frames=0,upload=op(upload),deletion=op(deletion),
        data_apply=dict(count=int(data>0),usec=data,max_usec=data,max_start_usec=10 if data else 0,
                        bytes=0,max_bytes=0,max_kind=4 if data else 0),data_apply_nested_usec=nested,
        peak_frame_terrain_usec=row['frame_terrain_usec'],peak_single_upload_bytes=payload,
        terrain_time_overruns=int(row['frame_terrain_usec']>1000),terrain_upload_overruns=int(payload>524288))
    return row,phase


class TerrainBudgets(unittest.TestCase):
    def test_two_legal_operations_fail_the_cumulative_contract(self):
        row,phase=evidence()
        result=reconcile_rows([row],phase)
        self.assertEqual(result['outcome'],'failed')
        self.assertEqual(reasons(phase),['Cumulative terrain frame time exceeded its 1/2 ms budget'])

    def test_complete_task_and_nested_children_are_charged_once(self):
        row,phase=evidence(upload=150,deletion=0,data=900,nested=150)
        self.assertEqual(reconcile_rows([row],phase)['outcome'],'failed')
        self.assertEqual(phase['peak_frame_terrain_usec'],900)
        self.assertEqual(reasons(phase),['Individual data application exceeded 0.75 ms'])
        damaged=copy.deepcopy(phase);damaged['data_apply_nested_usec']=0
        with self.assertRaises(RuntimeError):reconcile_rows([row],damaged)

    def test_phase_reset_cannot_hide_a_native_frame_overrun(self):
        a,pa=evidence(upload=600,deletion=0)
        a['end_usec']=700
        b,pb=evidence(upload=600,deletion=0)
        b.update(phase=2,start_usec=700,end_usec=1400,upload_max_start_usec=700,frame_terrain_usec=1200,frame_upload_bytes_total=40)
        pb.update(peak_frame_terrain_usec=1200,terrain_time_overruns=1)
        state={};reconcile_rows([a],pa,state)
        self.assertEqual(reconcile_rows([b],pb,state)['outcome'],'failed')
        b['frame_terrain_usec']=600;pb['peak_frame_terrain_usec']=600;pb['terrain_time_overruns']=0
        state={};reconcile_rows([a],pa,state)
        with self.assertRaises(RuntimeError):reconcile_rows([b],pb,state)

    def test_payload_and_time_limits_are_independent(self):
        row,phase=evidence(upload=1,deletion=0,payload=524289)
        self.assertEqual(reconcile_rows([row],phase)['outcome'],'failed')
        self.assertIn('Cumulative frame upload payload exceeded its budget',reasons(phase))
        self.assertIn('Individual upload payload exceeded 256 KiB',reasons(phase))

    def test_idle_phase_configuration_does_not_latch_an_unused_allowance(self):
        a,pa=evidence(upload=0,deletion=0,payload=0)
        a.update(upload_count=0,deletion_count=0,end_usec=700)
        b,pb=copy.deepcopy(a),copy.deepcopy(pa)
        b.update(phase=2,start_usec=701,end_usec=1400,
                 frame_time_limit_usec=2000,frame_upload_limit_bytes=1048576)
        state={};reconcile_rows([a],pa,state)
        self.assertEqual(reconcile_rows([b],pb,state)['outcome'],'passed')

    def test_zero_duration_operation_latches_allowance_through_idle_segments(self):
        for kind in ('upload','deletion','data_apply'):
            with self.subTest(kind=kind):
                a,pa=evidence(upload=0,deletion=0,payload=0)
                a.update(upload_count=0,deletion_count=0,end_usec=700)
                a[kind+'_count']=1
                if kind=='data_apply':pa['data_apply'].update(count=1,max_start_usec=0,max_kind=4)
                b,pb=evidence(upload=0,deletion=0,payload=0)
                b.update(upload_count=0,deletion_count=0,phase=2,start_usec=701,end_usec=1400)
                c,pc=copy.deepcopy(b),copy.deepcopy(pb)
                c.update(phase=3,start_usec=1401,end_usec=2100,
                         frame_time_limit_usec=2000,frame_upload_limit_bytes=1048576)
                if kind=='data_apply':a['data_apply_max_start_usec']=10;pa['data_apply']['max_start_usec']=10
                state={};reconcile_rows([a],pa,state);reconcile_rows([b],pb,state)
                with self.assertRaisesRegex(RuntimeError,'Same-frame allowance increased'):
                    reconcile_rows([c],pc,state)

    def test_unavailable_truncated_and_fabricated_metrics_do_not_pass(self):
        row,phase=evidence(upload=1,deletion=0)
        for fault in ('null','missing','nested','clock','aggregate','budget'):
            r,p=copy.deepcopy(row),copy.deepcopy(phase)
            if fault=='null':r['data_apply_usec']=None
            if fault=='missing':del r['frame_terrain_usec']
            if fault=='nested':r['data_apply_nested_usec']=1
            if fault=='clock':r['data_apply_count']=1;r['data_apply_max_start_usec']=6000
            if fault=='aggregate':p['peak_frame_terrain_usec']=0
            if fault=='budget':r['frame_time_limit_usec']=3000
            with self.subTest(fault=fault),self.assertRaises(RuntimeError):reconcile_rows([r],p)
        self.assertEqual(reconcile_rows([],dict(terrain_accounting_version=1))['outcome'],'inconclusive')


if __name__=='__main__':unittest.main()
