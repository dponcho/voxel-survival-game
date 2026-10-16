import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from full_height import observations,mesh_cells,target,command_hash,TICKS
from frontier_edit import NULL_FIELDS


def fixture(enabled):
    f32=lambda v:struct.unpack('<f',struct.pack('<f',float(v)))[0]
    ideal=[Fraction(10),Fraction(72),Fraction(10)]
    controls=[(0,1)]*1440+[(0,-1)]*1440+[(2,1)]*1440
    rows=[];poses={0:[10,72,10]};value=0;fingerprint=0
    for tick in range(TICKS+1):
        if tick:
            axis,sign=controls[tick-1];ideal[axis]+=sign*Fraction(13,120)
        goal=[f32(10+f32(ideal[0]-10)),72.0,f32(10+f32(ideal[2]-10))]
        p=[f32(ideal[0]),72 if tick==0 else f32(64.001),f32(ideal[2])]
        current=0 if tick<=1440 else 1 if tick<=2880 else 2
        if tick:
            fingerprint=(fingerprint*65599+tick+math.floor(goal[0]*1000+.5)
                         +math.floor(goal[2]*1000+.5)*31+current*17)&0x7fffffff
            if tick%15==0:
                edit=[math.floor(float(ideal[0])/32+.5)*32,70,math.floor(float(ideal[2])/32+.5)*32+13]
                if edit==[0,70,13]:value=2 if value==0 else 0
        source=max(0,tick-1);decision=source
        direction=0 if decision<1440 else 1 if decision<2880 else 2
        axis_vector=((1,0,0),(-1,0,0),(0,0,1))[direction]
        center=[f32(a+32*b) for a,b in zip(poses[source],axis_vector)]
        owned=mesh_cells(p)
        if enabled:owned|=mesh_cells(center)
        blocks=[]
        for c in ((0,1,0),(0,2,0),(5,1,0),(0,1,5)):
            if c not in owned:
                blocks.append(dict(block=list(c),state='missing',**{k:None for k in NULL_FIELDS}))
            else:
                blocks.append(dict(block=list(c),state='visible',loaded=True,visible=True,has_mesh=True,
                    mesh_id=str(1000+c[0]*100+c[1]*10+c[2]),mesh_viewers=1,collision_viewers=0,
                    queued_update=False,desired_revision=10,submitted_revision=10))
        ready=p[0]<=144 and p[2]<=144
        row=dict(row=tick+1,stage='prepared' if tick==0 else 'physics',tick=tick,leg=current,
            usec=1000000+tick*16667,player=p,target=goal,camera=[p[0],f32(p[1]+f32(1.65)),p[2]],
            yaw=f32((-math.pi/2,math.pi/2,math.pi)[current]),actors=24*tick,accepted=tick//15,
            rejected=0,saves=tick//60,command_hash=fingerprint,readiness_stops=0,
            native=dict(generation_jobs=0,mesh_jobs=0,result_jobs=0,main_jobs=0,overloads=0,
                        retired_meshes=0,retired_high_water=400),
            terrain=dict(resident_mesh=len(owned),resident_data=5000),origin_data_ready=ready,
            origin_value=value if ready else None,meshes=dict(status='measured',reason='',probe_usec=1,blocks=blocks),
            preparation=dict(positions=[center] if enabled else [],source_tick=source,
                             decision_tick=decision,source_player=poses[source],direction=direction))
        if tick==0:
            row.update(visual_area_ready=True,data_area_ready=True,preparation_area_ready=True if enabled else None,
                       vertical_voxels=[[-64,1],[-32,1],[40,1],[63,2],[64,0],[191,0]])
        rows.append(row);poses[tick]=p
    terminal=copy.deepcopy(rows[-1]);terminal.update(row=TICKS+2,stage='terminal',usec=rows[-1]['usec']+1)
    rows.append(terminal)
    return rows


def save(path,rows):
    # Godot's default JSON formatter retains 15 significant decimal digits.
    # Reconstruct float32 before arithmetic; parsed decimal floats need not be bit-equal.
    def native_roundtrip(v):
        if isinstance(v,float):return float(format(v,'.15g'))
        if isinstance(v,list):return [native_roundtrip(x) for x in v]
        if isinstance(v,dict):return {k:native_roundtrip(x) for k,x in v.items()}
        return v
    path.write_text(''.join(json.dumps(native_roundtrip(row),separators=(',',':'))+'\n' for row in rows))


class FullHeight(unittest.TestCase):
    def test_interior_and_negative_full_height_demand_and_direction_unions(self):
        base=mesh_cells((10,65,10))
        self.assertEqual(len(base),343)
        self.assertEqual(len(mesh_cells((-.125,65,-.125))),343)
        ahead=[mesh_cells(p) for p in ((42,65,10),(-22,65,10),(10,65,42))]
        self.assertTrue(all(len(base|other)==392 for other in ahead))
        self.assertLessEqual(len(base|ahead[0]|ahead[1]),448)
        self.assertLessEqual(len(base|ahead[1]|ahead[2]),448)
        self.assertEqual(target(1440),[166,72,10])
        self.assertEqual(target(2880),[10,72,10])
        self.assertEqual(target(4320),[10,72,166])

    def test_complete_actual_reversal_cross_axis_work_and_data_mesh_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'observations.jsonl'
            for enabled in (False,True):
                rows=fixture(enabled);save(path,rows);result=observations(path,enabled)
                self.assertTrue(result['data_evicted_and_reloaded'])
                self.assertTrue(result['mesh_evicted_and_reloaded'])
                self.assertEqual(result['initial_regions'],392 if enabled else 343)
                self.assertEqual(rows[-1]['accepted'],288)
                self.assertEqual(rows[-1]['actors'],103680)
                self.assertEqual(rows[-1]['saves'],72)
                h=0
                for tick in range(1,TICKS+1):h=command_hash(tick,h)
                self.assertEqual(result['command_hash'],h)

    def test_lost_work_camera_only_reversal_slab_unbounded_viewer_and_missing_evidence_fail(self):
        rows=fixture(True)
        faults=('missing-row','order','camera-only','no-cross-axis','height','slab','radius','direction',
                'work','save','hash','unavailable','nonnull-missing','lost-data-eviction','changed-reload','resident','retirement')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'observations.jsonl'
            for fault in faults:
                bad=copy.deepcopy(rows)
                if fault=='missing-row':bad.pop()
                elif fault=='order':bad[1],bad[2]=bad[2],bad[1]
                elif fault=='camera-only':bad[1441]['player'][0]=bad[1440]['player'][0]
                elif fault=='no-cross-axis':bad[2881]['player'][2]=10
                elif fault=='height':bad[40]['player'][1]=0
                elif fault=='slab':bad[0]['vertical_voxels'][0][1]=0
                elif fault=='radius':bad[100]['preparation']['positions'][0][0]+=32
                elif fault=='direction':bad[1441]['preparation']['direction']=0
                elif fault=='work':bad[100]['accepted']-=1
                elif fault=='save':bad[60]['saves']=0
                elif fault=='hash':bad[100]['command_hash']+=1
                elif fault=='unavailable':bad[100]['meshes']['status']='unavailable'
                elif fault=='nonnull-missing':
                    next(b for r in bad for b in r['meshes']['blocks'] if b['state']=='missing')['submitted_revision']=0
                elif fault=='lost-data-eviction':
                    for r in bad:
                        if r['leg']==0 and not r['origin_data_ready']:
                            r['origin_data_ready']=True;r['origin_value']=0
                elif fault=='changed-reload':
                    next(r for r in bad[1441:] if r['origin_data_ready'])['origin_value']=7
                elif fault=='resident':bad[100]['terrain']['resident_mesh']=513
                elif fault=='retirement':bad[100]['native']['retired_high_water']=769
                save(path,bad)
                with self.subTest(fault=fault),self.assertRaises(RuntimeError):observations(path,True)


if __name__=='__main__':unittest.main()
