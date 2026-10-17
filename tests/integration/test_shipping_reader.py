"""Synthetic file-shape tests; these clocks are never runtime/target evidence."""
import copy
import csv
import hashlib
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/qa'))
from shipping_diagnostics import FRAME_FIELDS, POSE_FIELDS, poses, frames, observation_record
from full_height import TICKS, target, command_hash, leg, DIRECTIONS


class ShippingReaderTests(unittest.TestCase):
    def test_physics_and_callback_populations_remain_distinct(self):
        p = dict(rows=4320, command_hash=123)
        f = dict(rows=1080, peak_mesh=392)
        result = observation_record('trial', 'bare', p, f)
        self.assertEqual((result['physics_rows'], result['frame_rows']), (4320,1080))
        self.assertNotIn('rows', result)
        self.assertEqual((p['rows'], f['rows']), (4320,1080))

    @classmethod
    def setUpClass(cls):
        cls.pose_rows = []
        fingerprint = 0
        previous = [10,72,10]
        for tick in range(1,TICKS+1):
            goal = target(tick)
            p = [goal[0],64.001,goal[2]]
            fingerprint = command_hash(tick,fingerprint)
            direction = leg(tick)
            # Values exactly reconstruct the native float32 handover arithmetic.
            from shipping_diagnostics import single
            center = [single(single(v)+32*d) for v,d in zip(previous,DIRECTIONS[direction])]
            row = [tick,1000000+tick*16667,*p,fingerprint,tick*24,tick//15,0,tick//60,0,
                   tick-1,tick-1,*previous,direction,*center,0,0,0,0,'-']
            cls.pose_rows.append(dict(zip(POSE_FIELDS,row)))
            previous = p
        cls.trial = dict(route_clocks_usec=[1000000]+[1000000+i*1440*16667 for i in (1,2,3)],
            end_usec=1000000+TICKS*16667+1000,dose_enabled=False,
            dose=dict(actual_usec=0,hash_updates=0,ticks=0,requested_tick_usec=0))

    def save_csv(self, path, fields, rows):
        with path.open('w',encoding='utf-8',newline='') as f:
            writer = csv.DictWriter(f,fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_all_actual_pose_handover_and_work_fields_reconcile(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'poses.csv'
            self.save_csv(p,POSE_FIELDS,self.pose_rows)
            r = poses(p,self.trial)
            self.assertEqual(r['rows'],TICKS)
            self.assertEqual(r['command_hash'],1241625024)

    def test_missing_physics_or_reversed_motion_or_changed_prep_is_rejected(self):
        for fault in ('missing','motion','preparation','actor','save'):
            values = copy.deepcopy(self.pose_rows)
            if fault == 'missing': values.pop()
            elif fault == 'motion': values[1500]['x'] += 2
            elif fault == 'preparation': values[200]['prep_x'] += 32
            elif fault == 'actor': values[-1]['actors'] -= 1
            else: values[-1]['saves'] -= 1
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as d:
                p = Path(d)/'poses.csv'
                self.save_csv(p,POSE_FIELDS,values)
                with self.assertRaises(RuntimeError): poses(p,self.trial)

    def test_separately_recorded_native_hash_dose_and_digest_reconcile(self):
        values = copy.deepcopy(self.pose_rows)
        trial = copy.deepcopy(self.trial)
        trial['dose_enabled'] = True
        count, requested = 32, 463
        digest = hashlib.sha256(bytes([90])*(4096*count)).hexdigest()
        for row in values:
            row.update(dose_start_usec=row['usec']-requested-1,dose_end_usec=row['usec']-1,
                       dose_request_usec=requested,hash_updates=count,hash_sha256=digest)
        trial['dose'].update(actual_usec=TICKS*requested,hash_updates=TICKS*count,ticks=TICKS,requested_tick_usec=requested)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'positive.csv'
            self.save_csv(p,POSE_FIELDS,values)
            self.assertEqual(poses(p,trial)['dose_actual_usec'],TICKS*requested)
            values[-1]['hash_sha256'] = '0'*64
            self.save_csv(p,POSE_FIELDS,values)
            with self.assertRaises(RuntimeError): poses(p,trial)

    def callback_fixture(self):
        values = []
        for tick in range(1,TICKS+1):
            values.append(dict(frame=tick,entry_usec=1000000+tick*16667+10,interval_usec=16667,
                tick=tick,resident_mesh=392,resident_data=5104,generation_jobs=0,mesh_jobs=0,
                result_jobs=0,retired_meshes=0,accepted=tick//15,readiness_stops=0,coverage_alarms=0,
                frontier_status='measured',fog_boundary_m=96,frontier_distance_m=96,fog_clearance_m=0,
                frontier_checked_regions=100,frontier_ready_regions=100,frontier_unready_regions=0,
                frontier_empty_regions=30,frontier_candidate_regions=100))
            goal = target(tick)
            values[-1].update(camera_x=goal[0],camera_y=65.651,camera_z=goal[2],
                              camera_yaw=(-math.pi/2,math.pi/2,math.pi)[leg(tick)])
        trial = copy.deepcopy(self.trial)
        end = values[-1]['entry_usec']+20
        trial.update(callback_count=TICKS,callback_last_end_usec=end,
            report=dict(samples=TICKS,measurement_end_usec=end+100,wall_seconds=TICKS*16667/1000000,
                peaks=dict(resident_mesh=392,resident_data=5104),
                diagnostic_accounting=dict(callbacks=TICKS,last_callback_end_usec=end,overflow=False)))
        return values,trial

    def test_complete_callback_count_clock_and_final_callback_reconcile(self):
        values,trial = self.callback_fixture()
        fields = list(FRAME_FIELDS)+[k for k in values[0] if k not in FRAME_FIELDS]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'frames.csv'
            self.save_csv(p,fields,values)
            self.assertEqual(frames(p,trial)['rows'],TICKS)

    def test_missing_final_callback_coverage_cap_and_clock_fail(self):
        for fault in ('missing','coverage','memory','catchup','clock','camera'):
            values,trial = self.callback_fixture()
            if fault == 'missing': values.pop()
            elif fault == 'coverage': values[10]['frontier_distance_m'] = 95
            elif fault == 'memory': values[20]['resident_data'] = 8193
            elif fault == 'catchup': values[30]['tick'] += 5
            elif fault == 'camera': values[1500]['camera_yaw'] = -math.pi/2
            else: values[-1]['entry_usec'] += 1
            fields = list(FRAME_FIELDS)+[k for k in values[0] if k not in FRAME_FIELDS]
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as d:
                p = Path(d)/'frames.csv'
                self.save_csv(p,fields,values)
                with self.assertRaises(RuntimeError): frames(p,trial)


if __name__ == '__main__':
    unittest.main()
