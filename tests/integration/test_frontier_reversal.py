import copy
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from frontier_travel import observations, positions, single
from frontier_edit import NULL_FIELDS


def fixture():
    # Independent exact float32 addition and integer command oracle. Camera
    # assignment occurs twice in production: negative half PI, then plus PI.
    f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
    x=f32(10);step=f32(13/120);accepted=fingerprint=0;rows=[]
    revisions={c:100+c for c in range(-1,9)}
    for tick in range(1,1201):
        x=f32(x+step);stamp=1000000+tick*16667
        target=f32(10+f32(13*tick/120))
        yaw=f32(f32(-math.pi/2)+math.pi) if tick>=900 else f32(-math.pi/2)
        fingerprint=(fingerprint*65599+tick+math.floor(target*1000+.5)+(accepted+1)*31+int(yaw*1000))&0x7fffffff
        column=math.ceil((x+96)/16)
        current=[[column,y,z] for z in (0,1) for y in (-1,0)]
        primary=[[a-1,b,c] for a,b,c in current]+current+[[a,0,0] for a in range(-1,5)]+[[0,1,0]]
        def sample(coords):
            blocks=[]
            for c in coords:
                if x-16*(c[0]+1)>=96:
                    blocks.append(dict(block=c,state='missing',**{k:None for k in NULL_FIELDS}));continue
                rev=revisions.get(c[0],100+c[0]) if c[1:]==[0,0] else 100+c[0]
                empty=c[1]==1
                refs=2 if c[0] in range(7,15) and abs(x-(c[0]-6)*16)<.15 else 1
                blocks.append(dict(block=c,state='confirmed_empty' if empty else 'visible',loaded=True,visible=True,
                    has_mesh=not empty,mesh_id=None if empty else str(100000+rev*100+c[1]*2+c[2]),mesh_viewers=refs,
                    collision_viewers=0,queued_update=False,desired_revision=rev,submitted_revision=rev))
            return dict(status='measured',reason='',probe_usec=1,blocks=blocks)
        attempt={}
        if tick%15==0:
            v=[math.floor(x/32+.5)*32,6,13];coords=[[v[0]//16-1,0,0],[v[0]//16,0,0]]
            before=sample(coords)
            for c in coords:revisions[c[0]]+=100
            accepted+=1
            attempt=dict(voxel=v,accepted=True,begin_usec=stamp-3,end_usec=stamp-1,before=before,after=sample(coords))
        rows.append(dict(row=tick,stage='physics',state='running',usec=stamp,tick=tick,engine_frame=tick,
            player=[x,f32(.001),10],camera=[x,f32(f32(.001)+f32(1.65)),10],yaw=yaw,target=[target,8,10],
            actors=24*tick,actor_phase=tick/60,rain=256,accepted=accepted,rejected=0,next_edit=accepted+1,
            saves=tick//60,next_save=tick//60+1,command_hash=fingerprint,readiness_stops=0,
            native=dict(overloads=0,retired_meshes=0,retired_high_water=100),terrain=dict(resident_mesh=511,resident_data=867),
            trace=dict(accepted=accepted,submitted=accepted,superseded=0,cancelled=0,timeout=0,unavailable=0,pending=0,
                pending_high_water=1,queued=0,overflow=0),preparation_positions=[[16*a+8,16*b+8,16*c+8] for a,b,c in current],
            meshes=sample(primary),edit_tail=sample([[a,0,0] for a in (5,6,7,8)]),
            lateral=sample([[column-1,y,-1] for y in (-1,0)]),edit_attempt=attempt,camera_reversed=tick>=900))
    return rows


def save(path,rows):
    path.write_bytes(''.join(json.dumps(r)+'\n' for r in rows).encode())


class FrontierReversal(unittest.TestCase):
    def test_outward_motion_camera_only_transition_all_work_and_legitimate_eviction(self):
        rows=fixture()
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'rows.jsonl';save(p,rows);result=observations(p,reversal=True)
        self.assertEqual(result['handover_ticks'],[56,204,351,499,647,794,942,1090])
        self.assertEqual(len(result['edits']),80)
        self.assertEqual(result['terminal']['actors'],28800)
        self.assertEqual(result['terminal']['saves'],20)
        self.assertEqual(result['lateral_exposed'],0)
        self.assertGreater(rows[899]['player'][0],rows[898]['player'][0])
        self.assertLess(rows[898]['yaw'],0);self.assertGreater(rows[899]['yaw'],0)
        self.assertEqual(rows[-1]['player'][0],positions(1200)[-1])
        self.assertTrue(result['evictions'])
        self.assertTrue(all(e['retired_observation']['desired_revision'] is None for e in result['evictions']))

    def test_missing_changed_reversal_work_retention_alias_and_guards_are_rejected(self):
        rows=fixture()
        faults=('incomplete','order','stalled','motion-reversed','camera-not-reversed','camera-early','flag',
            'actors','rain','save','due','hash','unavailable-tail','tail-order','alias','inside-eviction',
            'nonnull-missing','revision','resource','handover','overflow')
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'rows.jsonl'
            for fault in faults:
                bad=copy.deepcopy(rows);r=bad[899]
                if fault=='incomplete':bad.pop()
                if fault=='order':bad.reverse()
                if fault=='stalled':r['player'][0]=bad[898]['player'][0]
                if fault=='motion-reversed':r['player'][0]-=.21667
                if fault=='camera-not-reversed':r['yaw']=bad[898]['yaw']
                if fault=='camera-early':bad[898]['yaw']=r['yaw']
                if fault=='flag':r['camera_reversed']=False
                if fault=='actors':r['actors']-=24
                if fault=='rain':r['rain']=0
                if fault=='save':r['saves']-=1
                if fault=='due':r['edit_attempt']={}
                if fault=='hash':r['command_hash']+=1
                if fault=='unavailable-tail':r['edit_tail']=dict(status='unavailable',reason='missing',blocks=None,probe_usec=None)
                if fault=='tail-order':r['edit_tail']['blocks'].reverse()
                if fault=='alias':bad[0]['edit_tail']['blocks'][1]['mesh_id']='9007199254740993'
                if fault=='inside-eviction':bad[0]['edit_tail']['blocks'][0]=dict(block=[5,0,0],state='missing',**{k:None for k in NULL_FIELDS})
                if fault=='nonnull-missing':
                    missing=next(b for b in bad[-1]['meshes']['blocks'] if b['state']=='missing');missing['submitted_revision']=1
                if fault=='revision':bad[1000]['edit_tail']['blocks'][0]['desired_revision']+=1
                if fault=='resource':
                    i=next(i for i,v in enumerate(bad) if v['edit_attempt'].get('voxel')==[128,6,13])
                    bad[i]['edit_tail']['blocks'][2]['mesh_id']=bad[i-1]['edit_tail']['blocks'][2]['mesh_id']
                if fault=='handover':
                    for v in bad:
                        for b in v['meshes']['blocks']:
                            if b['state']!='missing':b['mesh_viewers']=1
                if fault=='overflow':r['trace']['overflow']=1
                save(p,bad)
                with self.subTest(fault=fault),self.assertRaises(RuntimeError):observations(p,reversal=True)

    def test_longer_case_cannot_replace_legacy_600_tick_expectations(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'rows.jsonl';save(p,fixture())
            with self.assertRaises(RuntimeError):observations(p)


if __name__=='__main__':unittest.main()
