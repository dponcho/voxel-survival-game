"""Independent expanded clocks and adversarial persistence; no engine executed here."""
import copy
import csv
from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from endpoint_precision import HEADER, LABELS, characterize, cost_sum, model, reconcile_phase, reconcile_saved, validate
from route_calibration import assess
from test_route_calibration import phases


def fixture(folder,label,index,workload="H1"):
    # Different row alignment from the production fixture: each main run ends
    # at a fixed eligible tick. Exact counts/costs come from aggregate arithmetic.
    p=phases(False)[index]
    m=model(label,index); counts=m['counts']; durations=m['durations']
    p['id']=p['id'].replace('H1',workload);p['workload']=workload
    p['actor_ticks']=1800*(24 if workload=='H2' else 12)
    p['workload_contract']=dict(workload=workload,fixture=1,actors=24 if workload=='H2' else 12,edit_rate=4 if workload=='H2' else 0,rain_instances=256 if workload=='H2' else 0,
        physics_hz=60,max_physics_steps=4,edit_trace=workload=="H2",resolution=[1280,720],render_scale=1,
        visual_radius=96,data_radius=128,triangle_colliders=False,render_block=32,workers=1,
        native_policy=dict(frame_usec=2000,frame_upload_bytes=1048576,single_upload_bytes=262144,
                           terrain_jobs=64,mesh_results=16,mesh_result_bytes=33554432))
    p.update(accepted_proxy_edits=120 if workload=='H2' else 0,proxy_autosaves=30 if workload=='H2' else 0,travelled_distance_m=195)
    entry=1000200;frame=0;cost=0;blocks=[];block_n=block_usec=0;endpoint=ack_begin=None
    name=f'{workload}-{label}-{index}.csv'
    with (folder/name).open('w',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(HEADER)
        for section,(n,duration) in enumerate(zip(counts,durations)):
            for position in range(n):
                q,r=divmod(duration,n)
                interval=q+(position<r)
                if section==6:
                    interval=5000+(500 if index in (2,3) and ((label=='endpoint' and position==0) or (label=='ack-duration' and position==3)) else 0)
                entry+=interval;frame+=1
                new_cost=30+frame%7
                writer.writerow([frame,1800 if section==6 else section*300+1,interval,entry,entry+7,entry+7+new_cost,
                                 frame-1,cost,cost,0,8,2])
                cost=new_cost
                if section==6 and position==0: endpoint=entry;ack_begin=entry+7+cost+2
                block_n+=1;block_usec+=interval
                if block_usec>=5000000:
                    blocks.append(dict(samples=block_n,usec=block_usec));block_n=block_usec=0
    bins=[];prior=0
    for n,duration in zip(counts,durations):
        bins.append(dict(samples=n,usec=duration,callbacks=n,callback_usec=cost_sum(prior+n)-cost_sum(prior),
                         status='measured' if n else 'unavailable',mean_usec=duration/n if n else None))
        prior+=n
    a=dict(start_usec=1000000,end_usec=m['end'],elapsed_usec=m['elapsed'],callbacks=frame,
           callback_usec=cost_sum(frame),shared_usec=cost_sum(frame),last_callback_usec=cost,last_shared_usec=cost,
           last_callback_end_usec=m['callback_end'],maximum_callback_usec=36,switched_calls=0,switched_usec=0,
           last_switched_usec=0,finalization_usec=1002+m['dose'],writer_drain_usec=400,
           invalid_partition=False,overflow=False,blocks=blocks,partial_block=dict(samples=block_n,usec=block_usec))
    end=m['callback_end']+2;begin=end+200;dose=m['dose']
    p.update(samples=frame,wall_seconds=sum(durations)/1e6,measurement_end_usec=end,raw_frames=name,diagnostic_accounting=a)
    p['route_calibration'].update(bins=bins,harness_bracket_usec=frame*2,
        closure_dose=dict(requested_usec=600000 if index in (1,2) else 0,start_usec=(end-1 if label=='dose-overlap' and index==1 else begin) if index in (1,2) else None,
                          end_usec=begin+dose if index in (1,2) else None,elapsed_usec=dose))
    p['precision_clock']=dict(scope='modeled wall clocks; not terrain, disk or CPU measurements',interval_begin_usec=1000200,
        endpoint_entry_usec=endpoint,ack_begin_usec=ack_begin,ack_end_usec=end if ack_begin is not None else None,
        dose_begin_usec=begin if index in (1,2) else None,dose_end_usec=begin+dose if index in (1,2) else None,
        writer_drain_begin_usec=begin+dose+100,writer_drain_end_usec=begin+dose+500,
        callback_write_usec=frame*8,file_io_causal_usec=None,phases=[dict(phase='preparation',begin_usec=998000,end_usec=1000000),
            dict(phase='overhead_diagnostic',begin_usec=1000000,end_usec=m['end']),
            dict(phase='retirement',begin_usec=m['end'],end_usec=m['end']+2000)],native_operations='unavailable: clock-only controls')
    if label=='failed-workload' and index==1: p['actor_ticks']-=1
    if label=='failed-operation' and index==1:
        p['evaluation']='failed';p['modeled_operation']=dict(upload=dict(max_usec=751),deletion=dict(max_usec=0),dropped_frames=0)
    return p


class EndpointPrecisionTests(unittest.TestCase):
    def test_closed_form_costs_match_expanded_cycles_and_counts(self):
        for n in [0,1,6,7,8,1500,1504,1534]:
            self.assertEqual(cost_sum(n),sum(30+i%7 for i in range(1,n+1)))
        self.assertEqual(model('count-mask',1)['n']-model('positive',1)['n'],30)

    def test_terminal_guard_rejects_tiny_unscaled_drift_without_trimming(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label,expected_delta in [('endpoint',0),('ack-duration',500)]:
                p=[fixture(Path(tmp),label,i) for i in range(4)]
                for i,x in enumerate(p): reconcile_phase(tmp,x,label,i,'H1')
                status,d=assess(p,'H1')
                self.assertEqual(status,'inconclusive')
                self.assertEqual(d['positive']['classification'],'above_limit')
                self.assertGreater(d['route_repeat_variation'][6]['reference'],.01)
                self.assertTrue(all(x['reference']<.01 and x['closure']<.01 for x in d['route_repeat_variation'][:6]))
                c=characterize(p)['terminal_pairs'][0]
                self.assertEqual(c['terminal_interval_delta_usec'],500)
                self.assertEqual(c['complete_window_delta_usec'],expected_delta)
                self.assertLess(c['unscaled_terminal_delta_fraction'],.00002)
                self.assertLess(c['complete_mean_variation'],.00002)
                self.assertEqual(sum(b['samples'] for b in p[3]['route_calibration']['bins']),1504)

    def test_unequal_counts_conceal_known_positive_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=[fixture(Path(tmp),'count-mask',i) for i in range(4)]
            status,d=assess(p,'H1')
            self.assertEqual(status,'inconclusive')
            self.assertEqual(d['positive']['classification'],'below_limit')
            for x in characterize(p)['count_duration_decomposition']:
                self.assertGreater(x['duration_added_fraction'],.019)
                self.assertGreater(x['callback_count_added_fraction'],.019)
                self.assertLess(x['mean_added_fraction'],.0001)
                self.assertAlmostEqual(1+x['mean_added_fraction'],(1+x['duration_added_fraction'])/(1+x['callback_count_added_fraction']))
            self.assertEqual(p[0]['simulation_ticks'],p[1]['simulation_ticks'])

    def test_null_positive_failed_stalled_missing_unavailable_stay_authoritative(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label in ['null','positive','count-drift','stall','failed-workload','failed-operation','unavailable','dose-overlap','io-failed']:
                p=[fixture(Path(tmp),label,i) for i in range(4)]
                for i,x in enumerate(p): reconcile_phase(tmp,x,label,i,'H1')
                status,d=assess(p,'H1',io_failed=label=='io-failed')
                self.assertEqual(status,'controls_resolved' if label=='positive' else 'inconclusive')
                if label=='null': self.assertEqual(d['positive']['added_fraction'],0)
                if label=='unavailable':
                    self.assertIsNone(d)
                    self.assertIsNone(p[0]['route_calibration']['bins'][6]['mean_usec'])
                    self.assertIsNone(characterize(p)['terminal_pairs'][0]['unscaled_terminal_delta_fraction'])
            self.assertEqual(assess(p[:3],'H1')[0],'inconclusive')
            self.assertEqual(assess(p[::-1],'H1')[0],'inconclusive')

    def test_saved_phase_tail_ack_drain_io_and_operation_mutations_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=fixture(Path(tmp),'positive',1)
            mutations=[lambda p:p['diagnostic_accounting'].__setitem__('last_callback_usec',0),
                       lambda p:p['diagnostic_accounting'].__setitem__('callback_usec',1),
                       lambda p:p['route_calibration']['bins'][6].__setitem__('samples',0),
                       lambda p:p['precision_clock'].__setitem__('ack_begin_usec',1),
                       lambda p:p['precision_clock'].__setitem__('writer_drain_begin_usec',p['measurement_end_usec']),
                       lambda p:p['precision_clock'].__setitem__('callback_write_usec',0),
                       lambda p:p['precision_clock'].__setitem__('file_io_causal_usec',0),
                       lambda p:p['precision_clock']['phases'][2].__setitem__('phase','overhead_diagnostic'),
                       lambda p:p['workload_contract'].__setitem__('workers',2)]
            for mutate in mutations:
                bad=copy.deepcopy(p);mutate(bad)
                with self.assertRaises(ValueError): reconcile_phase(tmp,bad,'positive',1,'H1')
            failed=fixture(Path(tmp),'failed-operation',1);failed['evaluation']='inconclusive'
            with self.assertRaises(ValueError): reconcile_phase(tmp,failed,'failed-operation',1,'H1')

    def test_raw_callback_order_and_final_row_corruption_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);p=fixture(folder,'positive',0);path=folder/p['raw_frames']
            original=path.read_text().splitlines()
            for field,value in [(6,'100'),(7,'0'),(9,'1'),(10,'0'),(11,'0'),(1,'1801')]:
                lines=original.copy();row=lines[-1].split(',');row[field]=value;lines[-1]=','.join(row)
                path.write_text('\n'.join(lines)+'\n')
                with self.assertRaises(ValueError): reconcile_phase(folder,p,'positive',0,'H1')
            path.write_text('\n'.join(original[:-1])+'\n')
            with self.assertRaises(ValueError): reconcile_phase(folder,p,'positive',0,'H1')

    def test_saved_roundoff_tolerance_is_not_a_precision_policy_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);p=fixture(folder,'count-mask',1)
            p=json.loads(json.dumps(p))
            p['route_calibration']['bins'][0]['mean_usec']+=1e-9
            reconcile_phase(folder,p,'count-mask',1,'H1')
            p['route_calibration']['bins'][0]['mean_usec']+=.001
            with self.assertRaises(ValueError): reconcile_phase(folder,p,'count-mask',1,'H1')

    def test_complete_saved_control_set_and_decisions_reconcile(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);controls=[]
            for workload in ['H1','H2']:
                for label in LABELS:
                    p=[fixture(folder,label,i,workload) for i in range(4)];omitted=[]
                    if label=='missing': omitted.append(p.pop())
                    if label=='reordered': p.reverse()
                    status,d=assess(p,workload,io_failed=label=='io-failed')
                    decision=dict(status=status,qualified=False,**(d or dict(positive=dict(classification='unavailable',added_fraction=None),
                        null_repeat_variation=None,route_repeat_variation=[])))
                    assessment=dict(version='m1-route-calibration-1',qualified=False,legacy_authoritative=True,threshold=.01,
                                    hardware_noise_calibrated=False,shared_overhead=dict(outcome='inconclusive',added_fraction=None),
                                    workloads={workload:decision})
                    controls.append(dict(name=workload+'/'+label,workload=workload,io_failed=label=='io-failed',expected=status,
                                         phases=p,omitted_phases=omitted,assessment=assessment))
            report=dict(schema=1,passed=True,failures=[],scope='software endpoint/count precision; no policy or hardware qualification',controls=controls)
            result=validate(report,folder)
            self.assertEqual(result['modeled_phases'],112)
            self.assertEqual(result['controls'],28)
            self.assertFalse(result['policy_changed'])
            self.assertGreater(result['raw_rows'],160000)
            for mutate in [lambda r:r['controls'].pop(),
                           lambda r:r['controls'][1]['assessment']['workloads']['H1'].__setitem__('status','inconclusive'),
                           lambda r:r['controls'][0]['assessment']['shared_overhead'].__setitem__('added_fraction',0),
                           lambda r:r['controls'][6]['omitted_phases'].clear(),
                           lambda r:r['controls'][11]['assessment']['workloads']['H1']['positive'].__setitem__('added_fraction',0)]:
                bad=copy.deepcopy(report);mutate(bad)
                with self.assertRaises(ValueError): validate(bad,folder)
            (folder/'H2-positive-0.csv').unlink()
            with self.assertRaises(ValueError): validate(report,folder)

    def test_saved_report_size_is_bounded_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'large.json';path.write_bytes(b' '* (1024*1024+1))
            with self.assertRaisesRegex(ValueError,'exceeds'): reconcile_saved(path,tmp)


if __name__=='__main__': unittest.main()
