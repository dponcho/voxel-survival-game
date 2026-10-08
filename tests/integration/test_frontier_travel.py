import copy
import csv
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from frontier_travel import cells, coordinates, observations, operation_reasons, operations, positions, single


def fixture():
    result, accepted, fingerprint = [], 0, 0
    revisions = {x:100+x for x in (-1,0,1,2,3,4)}
    for tick,x in enumerate(positions()[1:],1):
        stamp=1000000+tick*16667
        target=single(10+single(6.5*tick/60))
        fingerprint=(fingerprint*65599+tick+math.floor(target*1000+.5)+(accepted+1)*31+int(single(-math.pi/2)*1000))&0x7fffffff
        player=[x,single(.001),10]
        def sample(coords):
            blocks=[]
            for c in coords:
                rev=revisions.get(c[0],100+c[0]) if c[1:]==[0,0] else 100+c[0]
                empty=c[1]==1
                refs=2 if c[0] in (7,8,9,10) and abs(x-(c[0]-6)*16)<.15 else 1
                blocks.append(dict(block=c,state='confirmed_empty' if empty else 'visible',loaded=True,visible=True,
                    has_mesh=not empty,mesh_id=None if empty else str(100000+rev*100+c[1]*2+c[2]),mesh_viewers=refs,collision_viewers=0,
                    queued_update=False,desired_revision=rev,submitted_revision=rev))
            return dict(status='measured',reason='',probe_usec=1,blocks=blocks)
        attempt={}
        if tick%15==0:
            v=[math.floor(x/32+.5)*32,6,13]
            coords=[[v[0]//16-1,0,0],[v[0]//16,0,0]]
            before=sample(coords)
            for c in coords: revisions[c[0]]+=100
            accepted+=1
            attempt=dict(voxel=v,accepted=True,begin_usec=stamp-3,end_usec=stamp-1,before=before,after=sample(coords))
        trace=dict(accepted=accepted,submitted=accepted,superseded=0,cancelled=0,timeout=0,unavailable=0,pending=0,
                   pending_high_water=1,queued=0,overflow=0)
        result.append(dict(row=tick,stage='physics',state='running',usec=stamp,tick=tick,engine_frame=tick,
            player=player,camera=[x,single(player[1]+single(1.65)),10],yaw=single(-math.pi/2),target=[target,8,10],
            actors=24*tick,actor_phase=tick/60,rain=256,accepted=accepted,rejected=0,next_edit=accepted+1,
            saves=tick//60,next_save=tick//60+1,command_hash=fingerprint,readiness_stops=0,
            native=dict(overloads=0,retired_meshes=0,retired_high_water=100),terrain=dict(resident_mesh=511,resident_data=867),
            trace=trace,preparation_positions=[[16*x+8,16*y+8,16*z+8] for x,y,z in cells(player)],
            meshes=sample(coordinates(player)),lateral=sample([[cells(player)[0][0]-1,y,-1] for y in (-1,0)]),edit_attempt=attempt))
    return result


def save(path,rows):
    path.write_bytes((''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows)).encode())


class FrontierTravel(unittest.TestCase):
    def test_exact_continuous_commands_and_four_handovers(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'rows.jsonl';save(path,fixture())
            result=observations(path)
            self.assertEqual(result['handover_ticks'],[56,204,351,499])
            self.assertEqual(len(result['edits']),40)
            self.assertEqual(result['terminal']['saves'],10)
            self.assertEqual(result['terminal']['actors'],14400)
            self.assertEqual(positions()[-1],74.99976348876953)

    def test_missing_reordered_stalled_failed_work_and_null(self):
        good=fixture()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'rows.jsonl'
            for kind in ('missing','reorder','stalled','actors','rain','save','due','fingerprint','revision','resource','stale-mesh','ownership','release','empty','preparation','null','bounds','overflow','io'):
                bad=copy.deepcopy(good)
                row=bad[203]
                if kind=='missing': bad.pop()
                if kind=='reorder': bad.reverse()
                if kind=='stalled': row['player'][0]-=.1
                if kind=='actors': row['actors']-=24
                if kind=='rain': row['rain']=0
                if kind=='save': row['saves']-=1
                if kind=='due': bad[209]['edit_attempt']={}
                if kind=='fingerprint': row['command_hash']+=1
                if kind=='revision': row['meshes']['blocks'][8]['desired_revision']+=1
                if kind=='resource': row['meshes']['blocks'][0]['mesh_id']='9007199254740993'
                if kind=='stale-mesh':
                    r=bad[14];prior=bad[13]
                    for b in r['meshes']['blocks']:
                        if b['block'] in ([-1,0,0],[0,0,0]):
                            b['mesh_id']=next(v['mesh_id'] for v in prior['meshes']['blocks'] if v['block']==b['block'])
                if kind=='ownership':
                    for r in bad:
                        for b in r['meshes']['blocks']: b['mesh_viewers']=1
                if kind=='release':
                    for r in bad:
                        for b in r['meshes']['blocks']:
                            if b['block'][0]==8 and r['tick']>=204: b['mesh_viewers']=2
                if kind=='empty': row['meshes']['blocks'][-1]['desired_revision']+=1
                if kind=='preparation': row['preparation_positions'][0][0]+=32
                if kind=='null': row['meshes']=dict(status='unavailable',reason='missing',blocks=None,probe_usec=None)
                if kind=='bounds': row['native']['retired_high_water']=769
                if kind=='overflow': row['trace']['overflow']=1
                if kind=='io': bad=[]
                save(path,bad)
                with self.subTest(kind=kind),self.assertRaises(RuntimeError): observations(path)

    def test_operation_threshold_remains_visible(self):
        for duration in (749,750,751):
            phase=dict(upload=dict(max_usec=duration),deletion=dict(max_usec=duration))
            self.assertEqual(operation_reasons(phase),[] if duration<=750 else
                ['Individual upload exceeded 0.75 ms','Individual deletion exceeded 0.75 ms'])

    def test_saved_phase_boundaries_aggregates_and_failed_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for duration in (749,750,751):
                phases=[];guards=[];raw=[]
                for pid,label in enumerate(('preparation','overhead_diagnostic','retirement'),1):
                    start=pid*10000
                    upload=dict(count=1,bytes=512,usec=duration,max_usec=duration,max_bytes=512,max_start_usec=start+1,max_kind=1)
                    deletion=dict(count=0,bytes=0,usec=0,max_usec=0,max_bytes=0,max_start_usec=0,max_kind=0)
                    row=dict(native_frame=pid,phase=pid,start_usec=start,end_usec=start+2000,phase_boundary=1)
                    for kind,value in [('upload',upload),('deletion',deletion)]:
                        row.update({kind+'_'+k:v for k,v in value.items() if k!='max_kind' or kind=='deletion'})
                    name=f'{pid}.csv'
                    with (root/name).open('w',newline='') as stream:
                        writer=csv.DictWriter(stream,fieldnames=row);writer.writeheader();writer.writerow(row)
                    raw.append(row)
                    phases.append(dict(id=pid,phase=label,raw_operations=name,frames=1,tracing=True,dropped_frames=0,
                        upload=upload,deletion=deletion,peak_frame_operation_usec=duration,peak_frame_upload_bytes=512,
                        native_start=dict(upload_usec=0,deletion_usec=0),native_end=dict(upload_usec=duration,deletion_usec=0)))
                    guards.append(dict(id=pid,phase=label,close_before_usec=start+1999,close_after_usec=start+2001,
                        failures=operation_reasons(phases[-1])))
                saved=dict(operation_phases=phases)
                count,failed=operations(root,saved,guards)
                self.assertEqual(count,3);self.assertEqual(len(failed),3 if duration>750 else 0)
                for kind in ('aggregate','order','close','failure','terminal','missing'):
                    bad=copy.deepcopy(saved);g=copy.deepcopy(guards);rows=copy.deepcopy(raw)
                    if kind=='aggregate': bad['operation_phases'][0]['upload']['count']+=1
                    if kind=='order': bad['operation_phases'].reverse()
                    if kind=='close': g[0]['close_after_usec']=rows[0]['end_usec']-1
                    if kind=='failure': g[0]['failures']=[] if duration>750 else ['Individual upload exceeded 0.75 ms']
                    if kind=='terminal': rows[0]['phase_boundary']=0
                    if kind=='missing': rows[0]=None
                    with (root/'1.csv').open('w',newline='') as stream:
                        writer=csv.DictWriter(stream,fieldnames=raw[0]);writer.writeheader()
                        if rows[0]: writer.writerow(rows[0])
                    with self.subTest(duration=duration,kind=kind),self.assertRaises(RuntimeError): operations(root,bad,g)
