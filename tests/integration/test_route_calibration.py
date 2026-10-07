"""Independent closed-form trial fixtures and adversarial saved controls."""
import copy
import csv
import json
import tempfile
from fractions import Fraction
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from route_calibration import assess, compare, reconcile_decision, reconcile_folder, scope, variation


def phases(varying=True):
    # Direct aggregate arithmetic; no clock/event loop or production ledger.
    out = []
    for i, role in enumerate(['reference-1','closure-1','closure-2','reference-2']):
        values = [4000,6000]*3 if varying else [5000]*6
        bins = [dict(samples=1000, usec=v*1000, callbacks=1000, callback_usec=20000,
                     status='measured', mean_usec=v) for v in values]
        bins.append(dict(samples=1,usec=1000,callbacks=1,callback_usec=20,status='measured',mean_usec=1000))
        delay = 600000 if i in (1,2) else 0
        elapsed = 30002200 + delay
        out.append(dict(id='CAL-H1-'+role,workload='H1',completed=True,evaluation='inconclusive',
                        simulation_ticks=1800,actor_ticks=21600,simulated_seconds=30,wall_seconds=30.001,
                        readiness_stops=0,rejected_proxy_edits=0,frontier_enabled=False,samples=6001,
                        workload_contract=dict(visual_radius=96,data_radius=128),
                        workload_evidence=dict(command_hash=123,route_checkpoints=[]),
                        operation_phase=dict(tracing=True),measurement_end_usec=31001200,
                        fog_frontier=dict(status='unavailable',evaluation='inconclusive',exposed_samples=None,minimum_frontier_distance_m=None),
                        diagnostic_accounting=dict(callbacks=6001,overflow=False,invalid_partition=False,switched_calls=0,switched_usec=0,
                                                   start_usec=1000000,end_usec=1000000+elapsed,elapsed_usec=elapsed,
                                                   callback_usec=120020,shared_usec=120020,last_callback_end_usec=31001200,
                                                   finalization_usec=1000+delay,writer_drain_usec=400),
                        route_calibration=dict(version='m1-route-calibration-1',invalid=False,bins=bins,
                                               closure_dose=dict(requested_usec=delay,start_usec=31002200 if delay else None,
                                                                 end_usec=31002200+delay if delay else None,elapsed_usec=delay))))
    return out


class RouteCalibrationTests(unittest.TestCase):
    def test_repeatable_route_shape_does_not_reject_null_or_positive_controls(self):
        for varying in [False, True]:
            status, details = assess(phases(varying), 'H1')
            self.assertEqual(status, 'controls_resolved')
            self.assertEqual(details['null_repeat_variation'], 0)
            self.assertEqual(details['positive']['classification'], 'above_limit')
            self.assertAlmostEqual(details['positive']['added_fraction'], 600000/30002200)

    def test_between_repeat_drift_is_retained_even_when_whole_trial_is_identical(self):
        p = phases()
        p[3]['route_calibration']['bins'][0]['usec'] += 100000
        p[3]['route_calibration']['bins'][1]['usec'] -= 100000
        status, d = assess(p, 'H1')
        self.assertEqual(status, 'inconclusive')
        self.assertEqual(d['null_repeat_variation'], 0)
        self.assertGreater(d['route_repeat_variation'][0]['reference'], .01)

    def test_exact_boundary_overlap_and_speedup(self):
        self.assertEqual(compare([1000,1000],[1010,1010])['classification'], 'above_limit')
        self.assertEqual(compare([1000,1000],[1005,1005])['classification'], 'below_limit')
        self.assertEqual(compare([1000,1000],[1009,1011])['classification'], 'inconclusive')
        self.assertEqual(compare([1000,1000],[990,990])['classification'], 'inconclusive')
        self.assertEqual(variation([1000,1020]), Fraction(2,101))

    def test_missing_reordered_stalled_failed_and_short_never_resolve(self):
        for mutate in [lambda p: p.pop(),lambda p:p.reverse(),
                       lambda p:p[1].__setitem__('wall_seconds',31),
                       lambda p:p[1].__setitem__('evaluation','failed'),
                       lambda p:p[1]['workload_contract'].__setitem__('visual_radius',80)]:
            p=phases();mutate(p)
            self.assertEqual(assess(p,'H1')[0], 'inconclusive')
        self.assertEqual(assess(phases(),'H1',short=True)[0], 'inconclusive')
        self.assertEqual(assess(phases(),'H1',io_failed=True)[0], 'inconclusive')

    def test_closure_must_follow_last_callback_and_stay_in_full_window(self):
        for key,value in [('start_usec',31001199),('end_usec',32000000),('elapsed_usec',599999),('requested_usec',0)]:
            p=phases();p[1]['route_calibration']['closure_dose'][key]=value
            self.assertEqual(assess(p,'H1')[0], 'inconclusive')
        p=phases();p[0]['route_calibration']['closure_dose']['start_usec']=31002200
        self.assertEqual(assess(p,'H1')[0], 'inconclusive')

    def test_lost_terminal_callback_or_partition_cannot_reconcile(self):
        for mutate in [lambda p:p[1]['route_calibration']['bins'][6].__setitem__('samples',0),
                       lambda p:p[1]['route_calibration']['bins'][6].__setitem__('callback_usec',0),
                       lambda p:p[1]['diagnostic_accounting'].__setitem__('shared_usec',1),
                       lambda p:p[1]['diagnostic_accounting'].__setitem__('finalization_usec',1),
                       lambda p:p[1]['fog_frontier'].__setitem__('status','measured')]:
            p=phases();mutate(p)
            self.assertEqual(assess(p,'H1')[0], 'inconclusive')

    def test_saved_decision_and_qualification_scope_are_checked(self):
        status,d = assess(phases(),'H1')
        a=dict(status=status,qualified=False,**d)
        reconcile_decision(a,status,d)
        b=copy.deepcopy(a);b['positive']['added_fraction'] += .001
        with self.assertRaises(ValueError): reconcile_decision(b,status,d)
        b=copy.deepcopy(a);b['status']='inconclusive'
        with self.assertRaises(ValueError): reconcile_decision(b,status,d)
        root=dict(version='m1-route-calibration-1',qualified=False,legacy_authoritative=True,
                  threshold=.01,hardware_noise_calibrated=False,shared_overhead=dict(outcome='inconclusive',added_fraction=None))
        scope(root)
        root['shared_overhead']['added_fraction']=0
        with self.assertRaises(ValueError): scope(root)

    def test_saved_rows_reconcile_and_retain_missing_sections_and_phase_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            records=[]; operations=[dict(scenario='warmup',phase=v) for v in ['preparation','warmup','retirement']]
            header=['frame','wall_s','simulation_s','interval_ms','generation_jobs','mesh_jobs','result_jobs','pending_data',
                    'pending_mesh','private_bytes','working_set','draw_calls','triangles','accepted_edits','readiness_stops',
                    'callback_usec','render_cpu_ms','render_gpu_ms','diagnostic_usec','diagnostic_frame']
            header += ['frontier_'+str(i) for i in range(18)] + ['diagnostic_switched_usec','diagnostic_shared_usec']
            for workload in ['H1','H2']:
                for p in phases():
                    p['id']=p['id'].replace('H1',workload);p['workload']=workload
                    p['actor_ticks']=1800*(24 if workload=='H2' else 12)
                    p['accepted_proxy_edits']=120 if workload=='H2' else 0
                    p['proxy_autosaves']=30 if workload=='H2' else 0
                    p['travelled_distance_m']=195
                    p['workload_contract'].update(fixture=1,actors=24 if workload=='H2' else 12,
                                                 rain_instances=256 if workload=='H2' else 0,edit_rate=4 if workload=='H2' else 0,
                                                 resolution=[1280,720],render_scale=1,workers=1,render_block=32,
                                                 physics_hz=60,max_physics_steps=4,triangle_colliders=False,
                                                 native_policy=dict(frame_usec=2000,frame_upload_bytes=1048576,single_upload_bytes=262144,
                                                                    terrain_jobs=64,mesh_results=16,mesh_result_bytes=33554432))
                    p['raw_frames']=p['id']+'-frames.csv'
                    a=p['diagnostic_accounting'];a['callbacks']=13;a['callback_usec']=a['shared_usec']=260;a['last_callback_usec']=20
                    p['samples']=13
                    for b in p['route_calibration']['bins'][:6]:
                        b['samples']=b['callbacks']=2;b['callback_usec']=40;b['mean_usec']=b['usec']/2
                    fields=[];wall=0
                    ticks=[1,300,301,600,601,900,901,1200,1201,1500,1501,1799,1800]
                    for i,tick in enumerate(ticks):
                        b=6 if tick>=1800 else max(tick-1,0)//300
                        interval=p['route_calibration']['bins'][b]['mean_usec'];wall+=interval
                        row={k:0 for k in header}
                        row.update(frame=i+1,wall_s=wall/1e6,simulation_s=tick/60,interval_ms=interval/1000,
                                   diagnostic_frame=i,diagnostic_usec=20 if i else 0)
                        for k in header[20:38]: row[k]='unavailable'
                        fields.append(row)
                    with (folder/p['raw_frames']).open('w',newline='') as f:
                        w=csv.DictWriter(f,fieldnames=header);w.writeheader();w.writerows(fields)
                    records.append(p)
                    operations += [dict(scenario=p['id'],phase=v) for v in ['preparation','overhead_diagnostic','retirement']]
            root=dict(version='m1-route-calibration-1',qualified=False,legacy_authoritative=True,threshold=.01,
                      hardware_noise_calibrated=False,shared_overhead=dict(outcome='inconclusive',added_fraction=None),workloads={})
            for workload in ['H1','H2']:
                status, detail=assess([p for p in records if p['workload']==workload],workload)
                root['workloads'][workload]=dict(status=status,qualified=False,**detail)
            summary=dict(benchmark_mode='calibration',completed=True,qualified=False,integration_failures=[],test_mode=False,
                         route_calibration=root,scenarios=[dict(id='warmup',workload='warmup')]+records,operation_phases=operations,
                         diagnostic_heavy_ab=dict(workloads={k:dict(outcome='not_run') for k in ['H1','H2']}))
            target=folder/'summary.json';target.write_text(json.dumps(summary))
            self.assertEqual(reconcile_folder(folder)['raw_frames'],104)
            # Losing the final callback and merging retirement both break saved evidence.
            bad=copy.deepcopy(summary);bad['scenarios'][1]['diagnostic_accounting']['last_callback_usec']=0
            target.write_text(json.dumps(bad))
            with self.assertRaises(ValueError): reconcile_folder(folder)
            bad=copy.deepcopy(summary);bad['operation_phases'][5]['phase']='overhead_diagnostic'
            target.write_text(json.dumps(bad))
            with self.assertRaises(ValueError): reconcile_folder(folder)
            bad=copy.deepcopy(summary);bad['scenarios'][1]['workload_contract']['native_policy']['frame_usec']=1000
            target.write_text(json.dumps(bad))
            with self.assertRaises(ValueError): reconcile_folder(folder)


if __name__ == '__main__': unittest.main()
