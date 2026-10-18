"""Raw observer ownership and finite-prefix corruption controls; no engine."""
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
import shipping_observer as observer


def record(identity,parent,slot,lane,thread,cycles,*,section=0,end_section=None,units=1,size=0):
    return dict(id=identity,parent=parent,slot=slot,lane=lane,thread=thread,start_section=section,
                end_section=section if end_section is None else end_section,submitted_section=section,complete=1,
                units=units,bytes=size,reads=[dict(cycles=c,wall_before_usec=c//10,wall_after_usec=c//10,flags=3,error=0) for c in cycles])


def fixture():
    return [record(1,0,4,1,77,[100,110,400,410]),record(2,1,2,1,77,[120,130,160,170]),
            record(3,1,3,1,77,[180,190,220,230]),record(4,0,8,2,88,[1000,1010,1500,1510]),
            record(5,4,9,2,88,[1100,1110,1200,1210],size=10),
            record(6,4,10,2,88,[1300,1310,1400,1410],size=6),
            record(7,4,11,2,88,[1420,1430,1440,1450])]


def encode(rows,failure=0,lanes=2):
    result=bytearray(observer.HEADER.pack(b'CAIRNOB1',1,observer.SIZE,observer.CAP,len(rows),failure,lanes))
    for r in rows:
        result.extend(observer.RECORD.pack(*(r[k] for k in ('id','parent','thread','slot','lane','start_section','end_section','submitted_section','complete','units','bytes'))))
        for s in r['reads']:result.extend(observer.STAMP.pack(*(s[k] for k in ('cycles','wall_before_usec','wall_after_usec','flags','error'))))
    return result


def metadata(rows,failure=0,lanes=2):
    return dict(schema='cairn-observer-ledger-1',cap_bytes=observer.CAP,record_count=len(rows),failure_code=failure,
                lane_count=lanes,trace_bytes=40+192*len(rows),file='trace.bin',passed=failure==0,closed=True)


class ObserverReaderTests(unittest.TestCase):
    def audit(self,rows,**kwargs):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'trace.bin';path.write_bytes(encode(rows,**kwargs))
            return observer.ledger(path,metadata(rows,**kwargs))

    def test_nested_union_is_charged_once_and_bookkeeping_is_separate(self):
        a=self.audit(fixture())
        self.assertEqual(a['lanes'][0]['root_full_cycles'],'310')
        self.assertEqual(a['lanes'][0]['exclusive_body_cycles'],'250')
        self.assertEqual(a['lanes'][0]['bookkeeping_cycles'],'60')
        output=next(g for g in a['groups'] if g['slot']=='callback_output')
        self.assertEqual(output['exclusive_body_cycles'],'190')
        self.assertIsNone(output['bytes'])

    def test_missing_duplicate_or_extra_record_is_rejected(self):
        for mutate in ('missing','duplicate','extra'):
            data=encode(fixture())
            if mutate=='missing':data=data[:-192]
            elif mutate=='extra':data.extend(bytes(192))
            else:data[40+192:40+384]=data[40:40+192]
            with self.subTest(mutate=mutate),self.assertRaises(RuntimeError):observer.decode(data)

    def test_reversed_counter_cannot_be_disguised_by_ordered_walls(self):
        r=fixture();r[1]['reads'][2]['cycles']=1
        with self.assertRaises(RuntimeError):self.audit(r)

    def test_false_parent_or_false_worker_owner_is_rejected(self):
        for change in ('root','lane','thread','slot'):
            r=fixture()
            if change=='root':r[1]['parent']=0
            elif change=='lane':r[1]['lane']=2
            elif change=='thread':r[1]['thread']=88
            else:r[4]['slot']=2
            with self.subTest(change=change),self.assertRaises(RuntimeError):self.audit(r)

    def test_missing_worker_terminal_witness_cannot_pass(self):
        r=fixture();r[3]['complete']=0
        with self.assertRaises(RuntimeError):self.audit(r)

    def test_unavailable_or_failed_counter_is_not_a_zero(self):
        r=fixture();r[1]['reads'][1].update(cycles=0,flags=1,error=6)
        with self.assertRaises(RuntimeError):self.audit(r)
        r[1]['reads'][1]['cycles']=123
        with self.assertRaises(RuntimeError):observer.decode(encode(r))

    def test_honest_counter_failure_is_retained_without_derived_measurements(self):
        r=fixture();r[1]['reads'][1].update(cycles=0,flags=1,error=6)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'trace.bin';p.write_bytes(encode(r,failure=4))
            a=observer.ledger(p,metadata(r,failure=4),failed=True)
            self.assertFalse(a['passed'])
            self.assertIsNone(a['records'][1]['reads'][1]['cycles'])
            self.assertEqual(a['groups'],[])
            with self.assertRaises(RuntimeError):observer.ledger(p,metadata(r,failure=4))

    def test_numeric_metadata_cannot_round_binary_population(self):
        r=fixture()
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'trace.bin';p.write_bytes(encode(r));m=metadata(r);m['record_count']=float(m['record_count'])
            with self.assertRaises(RuntimeError):observer.ledger(p,m)

    def test_missing_trace_after_io_failure_is_unavailable_not_zero(self):
        t=dict(id='failed',valid=False,observer_sha256='',observer=dict(schema='cairn-observer-ledger-1',
            file='failed-observers.bin',cap_bytes=observer.CAP,failure_code=7,passed=False,closed=False,trace_bytes=0))
        with tempfile.TemporaryDirectory() as td:
            a=observer.trial_ledger(td,t)
            self.assertFalse(a['passed']);self.assertIsNone(a['retained_bytes']);self.assertEqual(a['groups'],[])
            self.assertEqual(a['evidence_integrity'],'retained_io_failure')
            t['valid']=True
            with self.assertRaises(RuntimeError):observer.trial_ledger(td,t)

    def test_header_cap_and_reserved_flags_are_strict(self):
        for offset,value in ((12,191),(16,observer.CAP+1),(40+64+24,4)):
            data=encode(fixture());struct.pack_into('<I',data,offset,value)
            with self.assertRaises(RuntimeError):observer.decode(data)

    def test_unsigned_endpoints_do_not_round_above_signed_range(self):
        r=fixture()
        for row in r:
            for stamp in row['reads']:stamp['cycles']+=(1<<63)+9007199254740993
        a=self.audit(r)
        self.assertEqual(a['lanes'][0]['root_full_cycles'],'310')
        self.assertGreater(a['records'][0]['reads'][0]['cycles'],1<<63)

    def test_worker_incarnation_allows_id_reuse_but_rejects_overlap(self):
        r=fixture();r.append(record(8,0,8,3,88,[20,30,40,50]))
        a=self.audit(r,lanes=3)
        self.assertEqual([l['thread_id'] for l in a['lanes']],['77','88','88'])
        for stamp in r[-1]['reads']:stamp['wall_before_usec']+=105;stamp['wall_after_usec']+=105
        with self.assertRaises(RuntimeError):self.audit(r,lanes=3)

    def test_section_crossing_is_retained_separately_for_workers(self):
        r=fixture();r[3]['end_section']=1
        a=self.audit(r)
        self.assertTrue(any(g['section']=='cross_section' for g in a['groups']))
        r[0]['end_section']=1
        with self.assertRaises(RuntimeError):self.audit(r)

    def protocol(self):
        return [dict(id='AB-H2-observer-%s-%d'%(g,i),group=g,index=i,diagnostic_mode='bare',dose_enabled=False,
                     dose=dict(requested_tick_cycles='0',reference_cycles='0'),valid=True,complete=True) for g,i in observer.expected_protocol()]

    def test_prefix_stops_at_five_even_if_controls_could_pass(self):
        t=self.protocol();observer.verify_prefix(t)
        t.append(copy.deepcopy(t[-1]))
        with self.assertRaises(RuntimeError):observer.verify_prefix(t)

    def test_failed_prefix_is_retained_without_retry_or_padding(self):
        for n in range(1,6):
            t=self.protocol()[:n];t[-1].update(valid=False,complete=False);observer.verify_prefix(t)
        t=self.protocol();t[1]['valid']=False
        with self.assertRaises(RuntimeError):observer.verify_prefix(t)
        with self.assertRaises(RuntimeError):observer.verify_prefix(self.protocol()[:4])

    def test_any_shipping_or_positive_arm_is_rejected(self):
        for key,value in (('diagnostic_mode','shipping'),('dose_enabled',True)):
            t=self.protocol();t[2][key]=value
            with self.assertRaises(RuntimeError):observer.verify_prefix(t)
        t=self.protocol();t[2]['dose']['requested_tick_cycles']='1'
        with self.assertRaises(RuntimeError):observer.verify_prefix(t)


if __name__=='__main__':unittest.main()
