"""Independent expanded controls, exact threshold arithmetic and corrupted evidence."""
import copy
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from cpu_dose import LABELS,HEADER,VERSION,model,declaration,expected_status,observation,assess,body_effect,reconcile_phase,reconcile_saved,reconcile_runtime,scope
from test_endpoint_precision import fixture as old_fixture


def fixture(folder,label,index,workload='H1'):
    p=old_fixture(folder,label,index,workload);p.pop('precision_clock')
    p['edit_visibility']=dict(accepted=120 if workload=='H2' else 0)
    m=model(label,index);entry=1000200;frame=0;prev=0;ack=0;blocks=[];bn=bt=0;maximum=0;last={}
    bins=[dict(samples=0,body_usec=0,dose_usec=0) for _ in range(7)]
    route=[dict(samples=0,usec=0,callbacks=0,callback_usec=0) for _ in range(7)]
    with (folder/p['raw_frames']).open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(HEADER)
        for j,(n,duration,base) in enumerate(zip(m['counts'],m['durations'],m['base'])):
            for pos in range(n):
                frame+=1;q,r=divmod(duration,n);interval=q+(pos<r)+(m['actual'] if frame>1 and label!='wait-masked' else 0)
                entry+=interval;begin=entry+7;end=begin+base+m['actual'];ds=begin+200 if m['request'] else None;de=ds+m['actual'] if ds else None
                if label=='missing-dose' and index==1:ds=None
                if label=='dose-overlap' and index==1:de=end+1
                tick=1800 if j==6 else j*300+1
                writer.writerow([frame,tick,interval,entry,begin,end,ds,de,m['request'],end+8,frame-1,prev,2])
                bins[j]['samples']+=1;bins[j]['body_usec']+=end-begin;bins[j]['dose_usec']+=(de-ds) if ds is not None and de is not None else 0
                route[j]['samples']+=1;route[j]['callbacks']+=1;route[j]['usec']+=interval;route[j]['callback_usec']+=end+8-begin
                bn+=1;bt+=interval
                if bt>=5000000:blocks.append(dict(samples=bn,usec=bt));bn=bt=0
                if j==6 and pos==0:ack=end+10
                prev=end+8-begin;maximum=max(maximum,prev)
                last=dict(begin_usec=begin,end_usec=end,body_usec=end-begin,dose_begin_usec=ds,dose_end_usec=de,requested_usec=m['request'])
    measured=end+10;end=measured+1055+(450000 if label=='window-drift' and index==3 else 0)
    p.update(samples=frame,wall_seconds=sum(x['usec'] for x in route)/1e6,measurement_end_usec=measured)
    p['diagnostic_accounting']=dict(start_usec=1000000,end_usec=end,elapsed_usec=end-1000000,callbacks=frame,
        callback_usec=sum(x['callback_usec'] for x in route),shared_usec=sum(x['callback_usec'] for x in route),last_callback_usec=prev,last_shared_usec=prev,
        last_callback_end_usec=last['end_usec']+8,maximum_callback_usec=maximum,switched_calls=0,switched_usec=0,last_switched_usec=0,
        finalization_usec=end-last['end_usec']-8,writer_drain_usec=400,invalid_partition=False,overflow=False,blocks=blocks,partial_block=dict(samples=bn,usec=bt))
    for x in route:x.update(status='measured',mean_usec=x['usec']/x['samples'])
    p['route_calibration'].update(bins=route,invalid=False,harness_bracket_usec=frame*2,closure_dose=dict(requested_usec=0,start_usec=None,end_usec=None,elapsed_usec=0))
    p['cpu_dose_accounting']=dict(version=VERSION,invalid=m['invalid'],requested_per_callback_usec=m['request'],bins=bins,last_callback=last)
    p['edit_acknowledgement']=dict(start_usec=ack,end_usec=measured)
    p['fixed_work_boundaries']=dict(native_phase_closed_usec=measured+(601 if label=='phase-invalid' and index==1 else 100),writer_drain_begin_usec=measured+200,writer_drain_end_usec=measured+600)
    p['cpu_clock']=dict(scope='modeled clocks; hypothetical eligible workload, no CPU/GPU/terrain measurement',interval_begin_usec=1000200,
        phases=[dict(phase='preparation',begin_usec=998000,end_usec=1000000),dict(phase='overhead_diagnostic',begin_usec=1000000,end_usec=measured+100),
                dict(phase='retirement',begin_usec=end,end_usec=end+2000)],file_io_causal_usec=None)
    if label=='incomplete' and index==1:p['completed']=False
    if label=='missing-body' and index==1:p['cpu_dose_accounting']['bins'][6].pop('body_usec')
    return p


def root(phases,workload,label):
    oracle=assess(phases,workload,label=='short',label=='io-failed',declaration(label))
    oracle['reasons']=['declared guard'] if oracle['status']=='inconclusive' else []
    return dict(version=VERSION,experimental=True,qualified=False,legacy_authoritative=True,threshold=.01,hardware_noise_calibrated=False,
        causal_frontier_probe_cost=None,cpu_service_usec=None,gpu_cost=None,shared_causal_overhead=None,
        declared_per_callback_usec=declaration(label),workloads={workload:oracle,('H2' if workload=='H1' else 'H1'):dict(status='not_run')})


def runtime_fixture(folder):
    buffer=bytes([90])*4096;baseline=hashlib.sha256(buffer*8).hexdigest();trials=[];obs=[];start=1000000
    for i in range(4):
        request=500 if i in (1,2) else 0;body=200+request;bins=[dict(samples=0,body_usec=0,dose_usec=0) for _ in range(7)]
        rows=[];prev=0;entry=start
        for frame in range(1,33):
            begin=entry+2000;end=begin+body;tick=1800 if frame>28 else min(5,(frame-1)*6//28)*300+1;j=6 if tick==1800 else (tick-1)//300
            ds=begin+100 if request else None;de=ds+request if ds else None
            rows.append(dict(frame=frame,tick=tick,entry_usec=begin,interval_usec=2000,body_begin_usec=begin,body_end_usec=end,
                dose_begin_usec=ds,dose_end_usec=de,requested_usec=request,hash_updates=2 if request else 0,
                hash_sha256=hashlib.sha256(buffer*2).hexdigest() if request else None,baseline_sha256=baseline,
                previous_frame=frame-1,previous_callback_usec=prev,complete_callback_end_usec=end+20))
            bins[j]['samples']+=1;bins[j]['body_usec']+=body;bins[j]['dose_usec']+=request;entry=begin;prev=body+20
        (folder/f'callback-{i}.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
        cbend=entry+prev;db=cbend+100;de=db+200;end=de+100
        last=dict(begin_usec=entry,end_usec=entry+body,body_usec=body,dose_begin_usec=rows[-1]['dose_begin_usec'],dose_end_usec=rows[-1]['dose_end_usec'],requested_usec=request)
        trials.append(dict(index=i,raw_file=f'callback-{i}.jsonl',callbacks=32,cpu_dose_accounting=dict(version=VERSION,invalid=False,requested_per_callback_usec=request,bins=bins,last_callback=last),
            writer_drain_begin_usec=db,writer_drain_end_usec=de,diagnostic_accounting=dict(start_usec=start,end_usec=end,elapsed_usec=end-start,
                finalization_usec=end-cbend,writer_drain_usec=de-db,callbacks=32,callback_usec=32*prev,shared_usec=32*prev,switched_usec=0,switched_calls=0,last_switched_usec=0,
                last_shared_usec=prev,last_callback_usec=prev,last_callback_end_usec=cbend,maximum_callback_usec=prev,blocks=[],partial_block=dict(samples=32,usec=64000),invalid_partition=False,overflow=False)))
        obs.append(dict(body_usec=32*body,dose_usec=32*request,callbacks=32));start=end+100
    report=dict(schema=1,passed=True,failures=[],status='placement_verified',qualified=False,experimental=True,max_callbacks=128,buffer_bytes=4096,max_hash_updates_per_callback=512,
        build=dict(godot_commit='ed1daf0bf001b61586d9930840f2f1394092c079',voxel_commit='2ac9f5f8a8219bf499314cc0fad54ffc47df908f',
                   native_source_key='11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d',game_commit='f'*40),
        cpu_service_usec=None,causal_probe_cost=None,gpu_cost=None,shared_causal_overhead=None,trials=trials,observations=obs,body_effect=body_effect(obs))
    (folder/'summary.json').write_text(json.dumps(report))
    (folder/'report-finalization.json').write_text(json.dumps(dict(start_usec=start,end_usec=start+500,elapsed_usec=500,allocated_to_trials=False)))
    return report


class CpuDoseTests(unittest.TestCase):
    def test_closed_form_sums_all_declared_controls_and_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            for workload in ('H1','H2'):
                for label in LABELS:
                    phases=[fixture(folder,label,i,workload) for i in range(4)]
                    for i,p in enumerate(phases):reconcile_phase(folder,p,label,i,workload)
                    if label=='missing':phases.pop()
                    if label=='reordered':phases.reverse()
                    out=assess(phases,workload,label=='short',label=='io-failed',declaration(label))
                    self.assertEqual(out['status'],expected_status(label),(workload,label))
                    if label=='at':self.assertEqual(out['body_effect']['lower_fraction'],.01)

    def test_wait_and_count_masking_keep_body_effect_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label in ('wait-masked','count-mask'):
                p=[fixture(Path(tmp),label,i) for i in range(4)];out=assess(p,'H1')
                self.assertEqual(out['body_effect']['lower_fraction'],.02)
                self.assertLess(out['complete_window']['duration_effect']['upper_fraction'],.01)
                if label=='count-mask':self.assertTrue(all(x['time_per_callback_added_fraction']<0 for x in out['complete_window']['count_duration_decomposition']))

    def test_changed_route_mix_is_not_causal_attribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=[fixture(Path(tmp),'count-route-mix',i) for i in range(4)];out=assess(p,'H1')
            self.assertEqual(out['status'],'inconclusive');self.assertLess(out['body_effect']['lower_fraction'],0)
            self.assertEqual(out['observations'][1]['mean_dose_usec'],20)
            for j,b in enumerate(p[1]['cpu_dose_accounting']['bins']):self.assertEqual(Fraction(b['body_usec'],b['samples'])-Fraction(p[0]['cpu_dose_accounting']['bins'][j]['body_usec'],p[0]['cpu_dose_accounting']['bins'][j]['samples']),20)

    def test_body_threshold_and_entry_interval_are_distinct_estimands(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=assess([fixture(Path(tmp),'at',i) for i in range(4)],'H1',declared=10)
            self.assertEqual(out['body_effect']['classification'],'above_limit')
            self.assertEqual(out['entry_interval_effect']['classification'],'below_limit')
            self.assertEqual(out['entry_interval_effect']['lower_fraction'],float(Fraction(1503*10,30020000)))
            out=assess([fixture(Path(tmp),'wait-masked',i) for i in range(4)],'H1')
            self.assertEqual(out['entry_interval_effect']['lower_fraction'],0)
            self.assertEqual(out['observations'][1]['dose_usec'],1504*20)

    def test_missing_null_phase_and_nested_cost_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label in ('missing-body','missing-dose','dose-overlap','phase-invalid'):
                p=fixture(Path(tmp),label,1);o=observation(p)
                self.assertEqual(o['status'],'unavailable');self.assertTrue(all(v is None for k,v in o.items() if k!='status'))
            p=fixture(Path(tmp),'null',0);self.assertEqual(observation(p)['dose_usec'],0)
            p['cpu_dose_accounting']['last_callback']['dose_begin_usec']=0;self.assertEqual(observation(p)['status'],'unavailable')

    def test_whole_and_main_body_instability_remain_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label in ('body-drift','main-body-drift','window-drift','route-drift'):
                out=assess([fixture(Path(tmp),label,i) for i in range(4)],'H1');self.assertEqual(out['status'],'inconclusive')
            out=assess([fixture(Path(tmp),'main-body-drift',i) for i in range(4)],'H1')
            self.assertEqual(out['same_mode_body_variation'][0],0);self.assertGreater(max(out['main_body_variation'][0]),.01)

    def test_raw_final_row_clocks_dose_and_previous_callbacks_cannot_be_lost(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);p=fixture(folder,'above',1);path=folder/p['raw_frames'];original=path.read_text().splitlines()
            for field,value in [(1,'1799'),(6,''),(7,'1'),(9,'1'),(10,'0'),(11,'0'),(12,'0')]:
                lines=original.copy();row=lines[-1].split(',');row[field]=value;lines[-1]=','.join(row);path.write_text('\n'.join(lines)+'\n')
                with self.assertRaises(ValueError):reconcile_phase(folder,p,'above',1,'H1')
            path.write_text('\n'.join(original[:-1])+'\n')
            with self.assertRaises(ValueError):reconcile_phase(folder,p,'above',1,'H1')

    def test_saved_complete_registry_classifications_bounds_and_qualification(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);controls=[]
            for w in ('H1','H2'):
                for label in LABELS:
                    p=[fixture(folder,label,i,w) for i in range(4)];omitted=[]
                    if label=='missing':omitted.append(p.pop())
                    if label=='reordered':p.reverse()
                    controls.append(dict(name=w+'/'+label,workload=w,expected=expected_status(label),declared_per_callback_usec=declaration(label),short_run=label=='short',io_failed=label=='io-failed',phases=p,omitted_phases=omitted,assessment=root(p,w,label)))
            report=dict(schema=1,passed=True,failures=[],scope='synthetic per-callback CPU span sensitivity; no qualification',controls=controls)
            path=folder.parent/(folder.name+'.json');path.write_text(json.dumps(report));result=reconcile_saved(path,folder)
            self.assertEqual(result['controls'],54);self.assertEqual(result['modeled_phases'],216)
            for change in (lambda r:r['controls'].pop(),lambda r:r['controls'][0]['assessment'].__setitem__('qualified',True),lambda r:r['controls'][2]['assessment']['workloads']['H1']['body_effect'].__setitem__('classification','below_limit')):
                bad=copy.deepcopy(report);change(bad);path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):reconcile_saved(path,folder)
            path.unlink()

    def test_real_native_digest_and_callback_drain_finalization_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);report=runtime_fixture(folder);out=reconcile_runtime(folder,report['build'])
            self.assertEqual(out['real_callbacks'],128);self.assertTrue(out['native_hash_digests_verified']);self.assertFalse(out['qualified'])
            with self.assertRaises(ValueError):reconcile_runtime(folder,dict(report['build'],game_commit='0'*40))
            rebuilt=copy.deepcopy(report)
            rebuilt['build']['native_source_key']='a'*64
            summary_path=folder/'summary.json'
            summary_path.write_text(json.dumps(rebuilt))
            self.assertEqual(reconcile_runtime(folder,rebuilt['build']),out)
            with self.assertRaises(ValueError):reconcile_runtime(folder,report['build'])
            with self.assertRaises(ValueError):reconcile_runtime(folder)
            rebuilt['build']['native_source_key']=''
            summary_path.write_text(json.dumps(rebuilt))
            with self.assertRaises(ValueError):reconcile_runtime(folder,rebuilt['build'])
            summary_path.write_text(json.dumps(report))
            path=folder/'callback-1.jsonl';original=path.read_text();rows=[json.loads(x) for x in original.splitlines()]
            for key,value in [('hash_sha256','0'*64),('dose_begin_usec',0),('complete_callback_end_usec',0),('previous_callback_usec',0),('hash_updates',0)]:
                bad=copy.deepcopy(rows);bad[-1][key]=value;path.write_text(''.join(json.dumps(x)+'\n' for x in bad))
                with self.assertRaises(ValueError):reconcile_runtime(folder)
            path.write_text(original);final=folder/'report-finalization.json';r=json.loads(final.read_text());r['allocated_to_trials']=True;final.write_text(json.dumps(r))
            with self.assertRaises(ValueError):reconcile_runtime(folder)

    def test_ordinary_summary_and_service_attribution_stay_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=[fixture(Path(tmp),'above',i) for i in range(4)];r=root(p,'H1','above');scope(r)
            r['cpu_service_usec']=0
            with self.assertRaises(ValueError):scope(r)


if __name__=='__main__':unittest.main()
