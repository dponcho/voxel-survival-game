import copy
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from frame_slack import (LABELS,TOTALS,HEADER,VERSION,declaration,expected_status,modeled_rows,aggregate,model,
                        observation,assess,effects,reconcile_phase,reconcile_saved,reconcile_runtime,digest,scope)


def fixture(folder,label,index):
    rows=list(modeled_rows(label,index));m=model(label,index);name=f'{label}-{index}.csv'
    with (folder/name).open('w',newline='') as f:
        w=csv.DictWriter(f,HEADER);w.writeheader();w.writerows(rows)
    bins=aggregate(rows)
    if label=='missing-body' and index==1:bins[-1].pop('body_usec')
    entry=1000200+sum(m['cycle_sums']);last=rows[-1]['complete_callback_end_usec']-rows[-1]['entry_usec'];closed=entry+15;end=closed+1055+(20000 if label=='window-drift' and index==3 else 0)
    callback=sum(r['complete_callback_end_usec']-r['entry_usec'] for r in rows);blocks=[];bn=bt=0
    for j,r in enumerate(rows):
        bn+=1;bt+=(rows[j+1]['entry_usec'] if j+1<len(rows) else entry)-r['entry_usec']
        if bt>=5000000:blocks.append(dict(samples=bn,usec=bt));bn=bt=0
    p=dict(index=index,samples=len(rows),completed=not(label=='incomplete' and index==1),work_units_valid=not(label=='failed-workload' and index==1),
        operation_evaluation='failed' if label=='failed-operation' and index==1 else 'inconclusive',raw_file=name,first_entry_usec=1000200,
        closing_anchor=dict(entry_usec=entry,complete_callback_end_usec=closed,previous_callback_usec=last),
        acknowledgement_usec=closed-next(r['complete_callback_end_usec'] for r in rows if r['tick']==1800),
        frame_slack_accounting=dict(version=VERSION,invalid=label in ('missing-dose','dose-overlap','missing-successor','cycle-overlap') and index==1,
            stalled=label=='stall' and index==1,bins=bins,last_cycle=rows[-1]),
        diagnostic_accounting=dict(start_usec=1000000,end_usec=end,elapsed_usec=end-1000000,callbacks=len(rows),callback_usec=callback,shared_usec=callback,
            switched_usec=0,switched_calls=0,last_callback_usec=last,last_shared_usec=last,last_switched_usec=0,last_callback_end_usec=rows[-1]['complete_callback_end_usec'],
            maximum_callback_usec=max(r['complete_callback_end_usec']-r['entry_usec'] for r in rows),finalization_usec=end-rows[-1]['complete_callback_end_usec'],writer_drain_usec=400,
            blocks=blocks,partial_block=dict(samples=bn,usec=bt),invalid_partition=False,overflow=False),
        phase_boundaries=dict(preparation_begin_usec=998000,measurement_begin_usec=1000000,native_phase_closed_usec=closed+(601 if label=='phase-invalid' and index==1 else 100),
            writer_drain_begin_usec=closed+200,writer_drain_end_usec=closed+600,retirement_begin_usec=end,retirement_end_usec=end+2000),render_signals=None,wait_service_usec=None)
    if label=='failed-operation' and index==1:p['modeled_operation']=dict(upload=dict(max_usec=751),deletion=dict(max_usec=0),dropped_frames=0)
    return p


def root(phases,label):
    r=assess(phases,declaration(label),label=='final-dose',label=='io-failed')
    return dict(r,version=VERSION,experimental=True,qualified=False,legacy_authoritative=True,threshold=.01,hardware_noise_calibrated=False,
        cpu_service_usec=None,gpu_cost=None,physical_presentation=None,causal_probe_cost=None,shared_causal_overhead=None,workloads={})


def native_fixture(folder):
    trials=[];all_obs=[];start=1000000;engine=1
    for index in range(8):
        request=(500 if index<4 else 20000) if index%4 in (1,2) else 0;cycle=max(10000,request+230);entry=start+100;first=entry;rows=[];previous=0
        for j in range(32):
            begin=entry+10;end=begin+200+request;complete=end+20;nxt=entry+cycle
            rows.append(dict(frame=j+1,tick=1800 if j>=28 else min(5,j*6//28)*300+1,engine_frame=engine,successor_engine_frame=engine+1,
                entry_usec=entry,body_begin_usec=begin,body_end_usec=end,complete_callback_end_usec=complete,next_entry_usec=nxt,
                requested_usec=request,dose_begin_usec=begin+100 if request else None,dose_end_usec=begin+100+request if request else None,
                baseline_updates=8,baseline_sha256=digest(8),hash_updates=2 if request else 0,hash_sha256=digest(2) if request else None,previous_callback_usec=previous))
            previous=complete-entry;entry=nxt;engine+=1
        name=f'cycle-{index}.jsonl';(folder/name).write_text(''.join(json.dumps(r)+'\n' for r in rows))
        anchor=dict(entry_usec=entry,engine_frame=engine,complete_callback_end_usec=entry+30,previous_callback_usec=previous);engine+=1
        db=entry+100;de=db+200;end=de+100;callback=sum(r['complete_callback_end_usec']-r['entry_usec'] for r in rows);bins=aggregate(rows)
        trials.append(dict(index=index,samples=32,completed=True,work_units_valid=True,operation_evaluation='unavailable',raw_file=name,
            first_entry_usec=first,closing_anchor=anchor,frame_slack_accounting=dict(version=VERSION,invalid=False,stalled=False,bins=bins,last_cycle=rows[-1]),
            phase_boundaries=dict(callback_phase_closed_usec=anchor['complete_callback_end_usec'],writer_drain_begin_usec=db,writer_drain_end_usec=de),render_signals=None,wait_service_usec=None,
            native_operation_evidence='unavailable: no terrain',diagnostic_accounting=dict(start_usec=start,end_usec=end,elapsed_usec=end-start,callbacks=32,callback_usec=callback,
            shared_usec=callback,switched_usec=0,switched_calls=0,last_switched_usec=0,last_callback_usec=previous,last_shared_usec=previous,last_callback_end_usec=rows[-1]['complete_callback_end_usec'],
            maximum_callback_usec=previous,finalization_usec=end-rows[-1]['complete_callback_end_usec'],writer_drain_usec=de-db,blocks=[],partial_block=dict(samples=32,usec=32*cycle),invalid_partition=False,overflow=False)))
        all_obs.append(dict(callbacks=32,cycle_usec=32*cycle,body_usec=32*(200+request),dose_usec=32*request));start=end+100
    groups=[dict(kind='limiter_slack' if g==0 else 'beyond_limiter',observations=all_obs[4*g:4*g+4],effects=effects(all_obs[4*g:4*g+4])) for g in range(2)]
    r=dict(schema=1,version=VERSION,passed=True,failures=[],status='placement_verified',qualified=False,experimental=True,
        max_fps=100,old_max_fps=60,restored_max_fps=60,body_callbacks=256,closing_anchor_callbacks=8,buffer_bytes=4096,max_hash_updates=8192,
        cpu_service_usec=None,gpu_cost=None,physical_presentation=None,causal_probe_cost=None,shared_causal_overhead=None,render_signals=None,wait_service_usec=None,
        unallocated_phase_gaps=[dict(begin_usec=p['diagnostic_accounting']['end_usec'],end_usec=trials[i+1]['diagnostic_accounting']['start_usec'] if i<7 else start,
            elapsed_usec=(trials[i+1]['diagnostic_accounting']['start_usec'] if i<7 else start)-p['diagnostic_accounting']['end_usec']) for i,p in enumerate(trials)],
        build=dict(godot_commit='ed1daf0bf001b61586d9930840f2f1394092c079',voxel_commit='2ac9f5f8a8219bf499314cc0fad54ffc47df908f',
                   native_source_key='11db4c9b8ea4d81f361faa9c32cfbd3ab7cb4c21e9053c7ccf0942e975b81d5d',game_commit='f'*40),trials=trials,groups=groups)
    (folder/'summary.json').write_text(json.dumps(r));(folder/'report-finalization.json').write_text(json.dumps(dict(start_usec=start,end_usec=start+500,elapsed_usec=500,allocated_to_trials=False)))
    return r


class FrameSlackTests(unittest.TestCase):
    def test_all_predeclared_controls_and_closed_form_thresholds(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            for label in LABELS:
                p=[fixture(folder,label,i) for i in range(4)]
                for i,x in enumerate(p):reconcile_phase(folder,x,label,i)
                if label=='missing':p.pop()
                if label=='reordered':p.reverse()
                out=assess(p,declaration(label),label=='final-dose',label=='io-failed')
                self.assertEqual(out['status'],expected_status(label),label)
                if label in ('below','at','above'):
                    self.assertEqual(out['observations'][0]['cycle_usec'],640000)
                    self.assertEqual(out['observations'][0]['body_usec'],32000)
                    self.assertEqual(out['cycle_effect']['lower_fraction'],{'below':.005,'at':.01,'above':.02}[label])

    def test_slack_and_final_dose_are_different_observations(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            out=assess([fixture(folder,'slack',i) for i in range(4)],500)
            self.assertEqual(out['body_effect']['lower_fraction'],.5);self.assertEqual(out['cycle_effect']['upper_fraction'],0)
            out=assess([fixture(folder,'final-dose',i) for i in range(4)],400,True)
            self.assertEqual(out['cycle_effect']['lower_fraction'],.000625);self.assertEqual(out['body_effect']['lower_fraction'],.0125)
            self.assertEqual(out['observations'][1]['last_cycle_usec'],20400)

    def test_counts_and_composition_cannot_silently_attribute_dose(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label in ('count-drift','count-route-mix'):
                p=[fixture(Path(tmp),label,i) for i in range(4)];o=assess(p,400);self.assertEqual(o['status'],'inconclusive')
                self.assertGreater(o['observations'][1]['dose_usec'],0)
                if label=='count-route-mix':self.assertLess(o['cycle_effect']['upper_fraction'],0)

    def test_missing_measurements_are_null_and_instability_is_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label in ('missing-body','missing-dose','dose-overlap','phase-invalid','missing-successor','cycle-overlap'):
                o=observation(fixture(Path(tmp),label,1));self.assertEqual(o['status'],'unavailable');self.assertTrue(all(v is None for k,v in o.items() if k!='status'))
            for label in ('body-drift','main-body-drift','cycle-drift','main-cycle-drift','window-drift','stall','failed-operation','failed-workload'):
                o=assess([fixture(Path(tmp),label,i) for i in range(4)],400);self.assertEqual(o['status'],'inconclusive')

    def test_raw_successor_final_body_and_ledger_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);p=fixture(folder,'above',1);path=folder/p['raw_file'];original=path.read_text().splitlines()
            for field,value in [(9,''),(9,'0'),(4,'0'),(5,''),(10,'0'),(11,'7')]:
                lines=original.copy();row=lines[-1].split(',');row[field]=value;lines[-1]=','.join(row);path.write_text('\n'.join(lines)+'\n')
                with self.assertRaises(ValueError):reconcile_phase(folder,p,'above',1)
            path.write_text('\n'.join(original[:-1])+'\n')
            with self.assertRaises(ValueError):reconcile_phase(folder,p,'above',1)

    def test_saved_registry_classification_qualification_and_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);controls=[]
            for label in LABELS:
                p=[fixture(folder,label,i) for i in range(4)];omitted=[]
                if label=='missing':omitted.append(p.pop())
                if label=='reordered':p.reverse()
                controls.append(dict(name=label,expected=expected_status(label),declared_usec=declaration(label),phases=p,omitted_phases=omitted,assessment=root(p,label)))
            r=dict(schema=1,passed=True,failures=[],controls=controls);path=folder.parent/(folder.name+'.json');path.write_text(json.dumps(r));o=reconcile_saved(path,folder)
            self.assertEqual(o['controls'],30);self.assertEqual(o['modeled_phases'],120)
            for change in (lambda x:x['controls'].pop(),lambda x:x['controls'][0]['assessment'].__setitem__('qualified',True),lambda x:x['controls'][2]['assessment']['cycle_effect'].__setitem__('classification','below_limit')):
                bad=copy.deepcopy(r);change(bad);path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):reconcile_saved(path,folder)
            path.unlink()

    def test_real_native_cycles_digests_and_closing_anchors(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);r=native_fixture(folder);o=reconcile_runtime(folder,r['build'])
            self.assertEqual(o['body_callbacks'],256);self.assertEqual(o['closing_anchor_callbacks'],8);self.assertTrue(o['final_body_successors_verified'])
            with self.assertRaises(ValueError):reconcile_runtime(folder,dict(r['build'],game_commit='0'*40))
            path=folder/'cycle-1.jsonl';original=path.read_text();rows=[json.loads(x) for x in original.splitlines()]
            for key,value in [('hash_sha256','0'*64),('next_entry_usec',0),('successor_engine_frame',0),('dose_end_usec',0),('baseline_updates',7)]:
                bad=copy.deepcopy(rows);bad[-1][key]=value;path.write_text(''.join(json.dumps(x)+'\n' for x in bad))
                with self.assertRaises(ValueError):reconcile_runtime(folder)

    def test_anchor_drain_finalization_and_unavailable_attribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);r=native_fixture(folder);path=folder/'summary.json'
            for change in (lambda x:x['trials'][-1]['closing_anchor'].__setitem__('entry_usec',0),lambda x:x.__setitem__('wait_service_usec',0),lambda x:x.__setitem__('restored_max_fps',0)):
                bad=copy.deepcopy(r);change(bad);path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):reconcile_runtime(folder)
            path.write_text(json.dumps(r));final=folder/'report-finalization.json';d=json.loads(final.read_text());d['allocated_to_trials']=True;final.write_text(json.dumps(d))
            with self.assertRaises(ValueError):reconcile_runtime(folder)


if __name__=='__main__':unittest.main()
