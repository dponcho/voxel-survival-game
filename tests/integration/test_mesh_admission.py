import copy
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from mesh_admission import verify_record, revision, urgency, lateral_boundaries


def record(priority=False):
    pending=[[7,0,-6,3,'101',None],[7,0,-1,3,'102',None],[7,-1,-1,3,'103',None],
             [7,0,2,3,'104',None],[4,0,0,7,'9007199254740993','9007199254740992']]
    return dict(row=1,phase=2,start_usec=100,end_usec=200,decision_usec=1,origin=[16.6083488464355,1.65100002288818,10],
        side=16,priority=priority,valid=True,pending_count=5,admitted=2,jobs_before=0,jobs_after=2,
        pending=pending,order=[4,1,2,3,0] if priority else [0,1,2,3,4],loads=[0,1])


class MeshAdmissionTests(unittest.TestCase):
    def test_fifo_bypass_and_priority_actual_selection(self):
        pending,chosen,bypass=verify_record(record(),False)
        self.assertEqual(chosen,[0,1])
        self.assertTrue(any(x['block']==[7,-1,-1] for x in bypass))
        pending,chosen,bypass=verify_record(record(True),True)
        self.assertEqual(chosen,[4,1]);self.assertEqual(bypass,[])
        self.assertEqual(pending[4][4],9007199254740993)
        self.assertIsNone(pending[0][5])

    def test_exact_geometric_order_negative_coordinates_and_ties(self):
        row=record(True)
        row['pending']=[[-1,0,0,3,'1',None],[0,0,0,3,'2',None],[1,0,0,3,'3',None]]
        row.update(origin=[0,0,0],pending_count=3,admitted=3,loads=[0,1,2],order=[0,1,2])
        verify_record(row,True)
        self.assertEqual(urgency([-1,0,0,3,1,None],[0,0,0],16),(1,0))
        row['order']=[1,0,2]
        with self.assertRaises(RuntimeError): verify_record(row,True)

    def test_missing_stale_reordered_failed_caps_and_unavailable_are_rejected(self):
        for fault in ('invalid','missing','order','revision','null-desired','stale-loaded','side','phase','origin',
                      'origin-null','origin-unavailable','infinite','priority-escaped','priority-missing','load-cap','load-null',
                      'loads-unavailable','clock','duplicate','count','boolean-phase','boolean-order','missing-item'):
            row=record(True)
            if fault=='invalid':row['valid']=False
            if fault=='missing':row['pending']=None
            if fault=='order':row['order'].reverse()
            if fault=='revision':row['pending'][0][4]=9007199254740993
            if fault=='null-desired':row['pending'][0][4]=None
            if fault=='stale-loaded':row['pending'][4][5]=None
            if fault=='side':row['side']=32
            if fault=='phase':row['phase']=4
            if fault=='origin':row['origin'][0]=4096
            if fault=='origin-null':row['origin'][0]=None
            if fault=='origin-unavailable':row['origin']=None
            if fault=='infinite':row['origin'][0]=math.inf
            if fault=='priority-escaped':row['phase']=1
            if fault=='priority-missing':row['priority']=False;row['order']=list(range(5))
            if fault=='load-cap':row['loads'][0]=4
            if fault=='load-null':row['loads'][0]=None
            if fault=='loads-unavailable':row['loads']=None
            if fault=='clock':row['end_usec']=99
            if fault=='duplicate':row['pending'][0]=copy.deepcopy(row['pending'][1])
            if fault=='count':row['pending_count']=513
            if fault=='boolean-phase':row['phase']=True
            if fault=='boolean-order':row['order'][0]=True
            if fault=='missing-item':row['pending'][0]=None
            with self.subTest(fault=fault),self.assertRaises(RuntimeError):verify_record(row,True)

    def test_null_revision_is_known_no_submission_not_a_passing_zero(self):
        self.assertIsNone(revision(None,missing=True))
        self.assertEqual(revision(str(2**64-1)),2**64-1)
        for value in (None,0,'0','01',str(2**64),'unavailable',1.0):
            with self.subTest(value=value),self.assertRaises(RuntimeError):revision(value)

    def test_submission_entry_brackets_preserve_false_and_uncertain(self):
        def observation(index,x,ready):
            block=dict(block=[7,0,-1],state='visible' if ready else 'pending',loaded=ready,visible=ready,has_mesh=ready,
                mesh_id='2001' if ready else None,mesh_viewers=1,collision_viewers=0,queued_update=not ready,
                desired_revision=102,submitted_revision=102 if ready else None)
            return dict(row=index,tick=index,usec=300+index*100,camera=[x,1.65,10],
                lateral=dict(status='measured',reason='',probe_usec=1,blocks=[block]))
        admission={(7,0,-1):dict(desired_revision='102',start_usec=100,end_usec=200)}
        # Outside at x=16; inside at x=17. Submission observation precedes entry.
        rows=[observation(1,16,True),observation(2,17,True)]
        result=lateral_boundaries(rows,admission)[0]
        self.assertIs(result['submitted_before_entry'],True)
        self.assertEqual(result['submission_window_usec'],[200,400])
        # First ready at the first inside sample leaves order within the gap unknown.
        rows[0]=observation(1,16,False)
        result=lateral_boundaries(rows,admission)[0]
        self.assertIsNone(result['submitted_before_entry'])
        self.assertEqual(result['submission_window_usec'],[400,500])
        # Actual inside unready is a failure, even when submission later completes.
        rows[1]=observation(2,17,False)
        rows.append(observation(3,18,True))
        result=lateral_boundaries(rows,admission)[0]
        self.assertIs(result['submitted_before_entry'],False)
        self.assertEqual(result['submission_window_usec'],[500,600])
        result=lateral_boundaries(rows[:2],admission)[0]
        self.assertIsNone(result['first_submission'])
        self.assertIsNone(result['submission_window_usec'])
        for fault in ('missing-outside','stale','revision','clock'):
            damaged=copy.deepcopy(rows)
            if fault=='missing-outside':damaged=damaged[1:]
            if fault=='stale':damaged[-1]['lateral']['blocks'][0]['submitted_revision']=101
            if fault=='revision':damaged[0]['lateral']['blocks'][0]['desired_revision']=101
            if fault=='clock':damaged[-1]['usec']=199
            with self.subTest(fault=fault),self.assertRaises(RuntimeError):lateral_boundaries(damaged,admission)

    def test_phase_gap_retains_fifo_and_rejects_priority(self):
        row=record();row['phase']=0
        verify_record(row,False)
        row['priority']=True
        with self.assertRaises(RuntimeError):verify_record(row,True)


    def test_pre_admission_missing_revision_remains_null(self):
        from frontier_edit import NULL_FIELDS
        missing=dict(block=[7,0,-1],state='missing',**{k:None for k in NULL_FIELDS})
        current=dict(block=[7,0,-1],state='visible',loaded=True,visible=True,has_mesh=True,
            mesh_id='2001',mesh_viewers=1,collision_viewers=0,queued_update=False,
            desired_revision=102,submitted_revision=102)
        def sample(i,x,t,b):
            return dict(row=i,tick=i,usec=t,camera=[x,1.65,10],
                lateral=dict(status='measured',reason='',probe_usec=1,blocks=[b]))
        admissions={(7,0,-1):dict(desired_revision='102',start_usec=100,end_usec=200)}
        rows=[sample(1,16,90,missing),sample(2,16,300,current),sample(3,17,400,current)]
        result=lateral_boundaries(rows,admissions)[0]
        self.assertIsNone(result['first_observation']['desired_revision'])
        self.assertIsNone(result['first_observation']['submitted_revision'])
        self.assertIs(result['submitted_before_entry'],True)
        rows[0]['usec']=201
        with self.assertRaises(RuntimeError):lateral_boundaries(rows,admissions)


if __name__=='__main__':unittest.main()
