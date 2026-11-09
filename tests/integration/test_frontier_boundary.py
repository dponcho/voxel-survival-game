import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from frontier_boundary import cells, preparation_bounds, classification, reconcile, FIXTURE, STAGES


def report():
    f = json.loads(FIXTURE.read_text())
    cases = []
    for name in f['controls']:
        enabled = name.startswith('corrected')
        rows = []
        for i,stage in enumerate(STAGES):
            camera = f['before_camera'] if i==0 else ([48.5,f['crossed_camera'][1],10] if i==19 else f['crossed_camera'])
            block = [9,0,0] if i==19 else ([7,0,-1] if enabled or i==18 else [7,0,0])
            import math
            d = math.sqrt(sum(max(v*16-p,p-(v+1)*16,0)**2 for v,p in zip(block,camera)))
            sample = dict(status='measured',candidate_regions=238,checked_regions=162,ready_regions=116,
                          unready_regions=46,empty_regions=22,frontier_distance_m=d,block=block,mesh_state='missing')
            outcome,clearance,transmittance = classification(sample,f['fog'])
            base = [camera[0],camera[1]-1.65,camera[2]]
            targets = cells([f['before_camera'][0] if i<=2 else f['crossed_camera'][0],0,10])
            rows.append(dict(stage=stage,usec=100+i,engine_frame=i//2,camera=camera,yaw=f['yaw'],base_pose=base,sample=sample,
                assessment=dict(evaluation=outcome,status='measured',fog_clearance_m=clearance,fog_transmittance=transmittance),
                original_targets_submitted=[enabled or i==18]*4,preparation_cells=targets if enabled else [],
                terrain=dict(resident_mesh=511 if enabled else 507,resident_data=867),native=dict(retired_meshes=0,overloads=0)))
        cases.append(dict(name=name,workers=int(name[-1]),enabled=enabled,settled=True,drained=True,begin_usec=99,cleanup_begin_usec=130,end_usec=140,
                          released_preparation_viewers=4 if enabled else 0,policy=dict(viewer_count=4 if enabled else 0,required_visual_radius_m=96,data_radius_m=128),
                          rows=rows,peaks=dict(resident_mesh=511,resident_data=867,retired_meshes=0,overloads=0),
                          final_native={k:0 for k in ('generation_jobs','mesh_jobs','result_jobs','main_jobs','retired_meshes')}))
    return dict(schema=1,version='m1-forward-four-1',passed=True,failures=[],qualified=False,target_performance='not_run',build={'test':'synthetic'},cases=cases,
                fog=f['fog'],row_cap=128,missing_input=dict(status='unavailable',evaluation='inconclusive',fog_clearance_m=None,fog_boundary_m=None,fog_transmittance=None))


class FrontierBoundary(unittest.TestCase):
    def test_negative_fractional_geometry_and_bounds(self):
        self.assertEqual(cells([10,8,10]), [[7,-1,0],[7,0,0],[7,-1,1],[7,0,1]])
        self.assertEqual(cells([-0.125,8,-0.125]), [[6,-1,-1],[6,0,-1],[6,-1,0],[6,0,0]])
        for x in [-1023.75,-32,-16.125,-.125,0,10,15.9583473205566,16,16.0666809082031,31.875,195,205]:
            for z in [-31.875,-.125,0,7.99,8,10,15.875,32]:
                self.assertLessEqual(preparation_bounds([x,8,z]),511)

    def test_saved_rows_and_failure_guards(self):
        s = report()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'summary.json'
            path.write_text(json.dumps(s))
            self.assertEqual(reconcile(Path(temp),s['build'])['native_rows'],80)
            for kind in ('missing','reordered','stalled','unready','bounds','zero-null','qualified','io','counts','distance','handover','undrained','failed'):
                bad = copy.deepcopy(s)
                if kind=='missing': bad['cases'][0]['rows'].pop()
                if kind=='reordered': bad['cases'].reverse()
                if kind=='stalled': bad['cases'][0]['settled']=False
                if kind=='unready': bad['cases'][1]['rows'][1]['original_targets_submitted'][0]=False
                if kind=='bounds': bad['cases'][0]['peaks']['resident_mesh']=513
                if kind=='zero-null': bad['missing_input']['fog_clearance_m']=0
                if kind=='qualified': bad['qualified']=True
                if kind=='io': bad['passed']=False; bad['failures']=['write failed']
                if kind=='counts': bad['cases'][0]['rows'][1]['sample']['ready_regions']=0
                if kind=='distance': bad['cases'][0]['rows'][1]['sample']['frontier_distance_m']=0
                if kind=='handover': bad['cases'][1]['rows'][2]['preparation_cells'][0][0]=8
                if kind=='undrained': bad['cases'][0]['final_native']['mesh_jobs']=1
                if kind=='failed': bad['cases'][1]['rows'][-1]['assessment']['evaluation']='passed'
                path.write_text(json.dumps(bad))
                with self.subTest(kind=kind), self.assertRaises(RuntimeError): reconcile(Path(temp),s['build'])

    def test_missing_measurement_never_passing_zero(self):
        fog=json.loads(FIXTURE.read_text())['fog']
        self.assertEqual(classification({'status':'unavailable'},fog),('inconclusive',None,None))
        with self.assertRaises(RuntimeError): classification(dict(status='measured'),fog)
