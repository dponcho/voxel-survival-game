"""New owners retain direct unsigned spans, ownership and complete disposal."""
import copy
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/qa'))
import preparation_demand as prep
import shipping_observer as old
from test_shipping_observer import record, encode


def fixture():
    rows = [record(1,0,2,1,77,[100,110,190,200]),
            record(2,1,15,1,77,[120,130,160,170]),
            record(3,2,16,1,77,[135,140,150,155]),
            record(4,0,13,2,88,[210,220,230,240]),
            record(5,0,14,2,88,[250,260,270,280])]
    for r in rows:
        for s in r['reads']: s['wall_before_usec']=s['wall_after_usec']=s['cycles']
        if r['slot'] >= 13: r['units']=1; r['bytes']=1
    rows[3]['end_section']=1
    rows[4]['bytes']=2
    data=bytearray(encode(rows,lanes=2)); data[:8]=b'CAIRNOB2'; struct.pack_into('<I',data,8,2)
    witness=dict(schema='cairn-preparation-owners-1',passed=True,unpublished=True,drained=True,
                 in_flight=0,configured_workers=1,session_destroyed=True,session_bytes=1000,main_thread='77',
                 owners=[dict(lane=2,thread='88',incarnation='9',pool='VoxelEngine.general',worker_index=0,
                              pool_joined=False,in_flight=0,attached_usec='210',retired_usec=None,detached_usec='300')],
                 counts=[dict(slot=s,attempted='1',completed='1',overload=str(int(s==14)),crossing=str(int(s==13))) for s in range(13,17)])
    h, decoded=prep.decode(bytes(data))
    return data,h,decoded,witness


class PreparationTests(unittest.TestCase):
    def test_version_is_separate_and_old_reader_rejects(self):
        data,_,_,_=fixture()
        with self.assertRaises(RuntimeError): old.decode(data)
        struct.pack_into('<I',data,8,1)
        with self.assertRaises(RuntimeError): prep.decode(data)

    def test_nested_main_is_union_once_and_crossing_is_separate(self):
        _,h,rows,w=fixture(); result=prep.ownership(rows,h['lane_count'],w)
        self.assertEqual(result['lanes'][0]['root_full_cycles'],'100')
        self.assertEqual(result['lanes'][0]['exclusive_body_cycles'],'50')
        self.assertEqual(result['lanes'][0]['bookkeeping_cycles'],'50')
        self.assertEqual(result['crossing_ids'],[4])
        self.assertEqual(result['native'][0]['crossing'],1)
        self.assertEqual(rows[3]['full_cycles'],30)

    def test_direct_unsigned_values_remain_exact(self):
        _,h,rows,w=fixture()
        for r in rows:
            for s in r['reads']: s['cycles']+=2**63
        r=prep.ownership(rows,h['lane_count'],w)
        self.assertEqual(r['lanes'][0]['root_full_cycles'],'100')

    def test_main_section_crossing_is_rejected_without_clipping(self):
        _,h,rows,w=fixture();rows[1]['end_section']=1
        with self.assertRaises(RuntimeError): prep.ownership(rows,h['lane_count'],w)
        self.assertEqual(rows[1]['end_section'],1)

    def test_missing_incarnation_retirement_or_detach_cannot_pass(self):
        for key,value in [('thread','77'),('incarnation','0'),('worker_index',1),('pool_joined',True),('detached_usec',None),('detached_usec','220')]:
            _,h,rows,w=fixture();w['owners'][0][key]=value
            with self.subTest(key=key),self.assertRaises((RuntimeError,TypeError)): prep.ownership(rows,h['lane_count'],w)
        _,h,rows,w=fixture();w['owners'][0]['retired_usec']='280'
        w['owners'].append(dict(w['owners'][0],lane=3,thread='99',incarnation='10',attached_usec='270',retired_usec=None))
        with self.assertRaises(RuntimeError): prep.ownership(rows,3,w)

    def test_native_attempt_completion_outcome_crossing_population(self):
        for key,value in [('attempted','0'),('completed','2'),('overload','0'),('crossing','1')]:
            _,h,rows,w=fixture();w['counts'][1][key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError): prep.ownership(rows,h['lane_count'],w)
        for key,value in [('start_section',1),('submitted_section',1),('bytes',0),('complete',0),('lane',1)]:
            _,h,rows,w=fixture();rows[3][key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError): prep.ownership(rows,h['lane_count'],w)

    def test_unpublish_drain_and_both_lifetimes_are_required(self):
        for key,value in [('unpublished',False),('drained',False),('session_destroyed',False),('in_flight',1),('configured_workers',2)]:
            _,h,rows,w=fixture();w[key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError): prep.ownership(rows,h['lane_count'],w)

    def test_raw_failure_reversal_and_overlapping_children_reject(self):
        for key,value in [('cycles',None),('flags',1),('error',6),('wall_before_usec',1),('cycles',1)]:
            _,h,rows,w=fixture();rows[1]['reads'][2][key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError): prep.ownership(rows,h['lane_count'],w)
        _,h,rows,w=fixture();rows[2]['parent']=1; rows[1]['reads'][3]['wall_after_usec']=180
        with self.assertRaises(RuntimeError): prep.ownership(rows,h['lane_count'],w)

    def test_cap_prefix_is_explicit_and_not_an_ordinary_trace(self):
        data,_,_,_=fixture();data=data[:232];struct.pack_into('<Q',data,16,232)
        struct.pack_into('<Q',data,24,1);struct.pack_into('<I',data,32,1)
        with self.assertRaises(RuntimeError): prep.decode(data)
        self.assertEqual(prep.decode(data,failed_cap=True)[0]['record_count'],1)
        with self.assertRaises(RuntimeError): prep.decode(data[:-1],failed_cap=True)

    def test_controls_stay_required_and_only_the_declared_launcher_dispatches(self):
        pipeline=(ROOT/'tools/ci/pipeline.py').read_text()
        self.assertIn('preparation_controls(editor, "editor", game)',pipeline)
        self.assertIn('preparation_controls(player / "Cairn.exe", "release")',pipeline)
        self.assertNotIn('--preparation-demand-pilot',pipeline)
        # A separate prospective declaration now permits the new launcher.
        # Ordinary build/control workflows still cannot invoke the route directly.
        for path in (ROOT/'.github/workflows').glob('*.yml'):
            self.assertNotIn('--preparation-demand-pilot',path.read_text())
        metadata=prep.source_metadata(ROOT)
        self.assertEqual((metadata['method'],metadata['inventory'],metadata['raw_version']),
                         (prep.VERSION,prep.INVENTORY,2))


if __name__=='__main__': unittest.main()
