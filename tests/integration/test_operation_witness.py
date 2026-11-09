"""Independent raw integer codec/counter/selection attacks; actual entries run in CI."""
import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
import operation_witness as witness


def fixture():
    # Synthetic reader fixture, not measured performance. Two exact integer
    # events: the first fails at 751us, then a larger 900us maximum follows.
    prefix = 9007199254740993
    raw = bytearray(b'CAIRNOP1'+struct.pack('<II',1,296))
    raw.extend(struct.pack('<16Q',128,2,2,2,0,2,0,0,0,1,2,8,40000,1,0,0))
    raw.extend(struct.pack('<12Q',2,0,0,0,900,0,0,0,2,0,0,0))
    raw.extend(bytes(16))
    for i,(start,end) in enumerate(((100,851),(900,1800)),1):
        raw.extend(struct.pack('<20Q2I',i,0,i,1,i,44,44,start,end,192,0,0,end-start,end+1,0,1,i,1000,192,524288,1,1))
        for j,before in enumerate((start+1,start+3,end-4,end-2)):
            raw.extend(struct.pack('<QQQII',prefix+100*i+j,before,before+1,3,0))
    return raw


class OperationWitnessTests(unittest.TestCase):
    def test_exact_large_thread_cycles_body_full_bounds_and_first_failure(self):
        h,rows = witness.decode(bytes(fixture()))
        self.assertEqual(h['first_failure'],1); self.assertEqual(h['max_ids'],[2,0,0,0])
        self.assertEqual(rows[0]['reads'][0]['cycles'],'9007199254741093')
        self.assertEqual([rows[0][key] for key in ('body_cycles','full_cycles','uncertainty_cycles')],['1','3','2'])
        self.assertEqual(rows[1]['elapsed_usec'],900)

    def test_failed_or_unavailable_counter_has_null_bounds_not_passing_zero(self):
        for flags,error,status in ((1,6,'failed'),(0,50,'unavailable')):
            blob = fixture(); struct.pack_into('<Q',blob,16+8*7,1)
            struct.pack_into('<I',blob,256+164,3)
            for i in range(4):
                pos = 256+168+32*i
                struct.pack_into('<Q',blob,pos,0);struct.pack_into('<II',blob,pos+24,flags,error)
            _,rows = witness.decode(bytes(blob))
            self.assertEqual(rows[0]['status'],status)
            self.assertIsNone(rows[0]['body_cycles']);self.assertIsNone(rows[0]['full_cycles'])

    def test_raw_failed_counter_cannot_hide_an_unsigned_payload(self):
        blob = fixture(); struct.pack_into('<II',blob,256+168+24,1,6)
        with self.assertRaisesRegex(RuntimeError,'wire counter'):witness.decode(bytes(blob))

    def test_re_signed_first_failure_maximum_overflow_and_thread_attacks(self):
        attacks = ((16+9*8,'<Q',2),(208,'<Q',1),(16+6*8,'<Q',1),
                   (256+6*8,'<Q',45),(256+18*8,'<Q',524289),(256+168+16,'<Q',852))
        for offset,fmt,value in attacks:
            blob = fixture();struct.pack_into(fmt,blob,offset,value)
            with self.subTest(offset=offset),self.assertRaises(RuntimeError):witness.decode(bytes(blob))

    def test_sparse_maximum_selection_does_not_replace_the_first_tie(self):
        blob = fixture()
        for index,value in ((2,3),(3,3),(11,12),(13,0)):
            struct.pack_into('<Q',blob,16+8*index,value)
        struct.pack_into('<Q',blob,144,3)
        self.assertEqual(witness.decode(bytes(blob))[0]['max_ids'][0],2)
        struct.pack_into('<Q',blob,208,3)
        with self.assertRaisesRegex(RuntimeError,'Unobserved maximum'):witness.decode(bytes(blob))

    def test_record_extent_storage_reservation_and_version_fail_closed(self):
        for blob in (bytes(fixture())[:-1],bytes(fixture())+b'x',b'CAIRNOP2'+bytes(fixture())[8:]):
            with self.assertRaises(RuntimeError):witness.decode(blob)
        for offset,value in ((16,129),(16+12*8,65537),(240,1)):
            blob = fixture();struct.pack_into('<Q',blob,offset,value)
            with self.assertRaises(RuntimeError):witness.decode(bytes(blob))

    def test_counter_reversal_and_wall_overlap_cannot_be_a_measured_interval(self):
        blob = fixture();struct.pack_into('<Q',blob,256+168+2*32,0)
        with self.assertRaises(RuntimeError):witness.decode(bytes(blob))
        blob = fixture();struct.pack_into('<Q',blob,256+168+32+8,100)
        with self.assertRaisesRegex(RuntimeError,'enclosure'):witness.decode(bytes(blob))

    def test_operation_budget_change_and_double_charge_are_rejected(self):
        for index,value in ((12,752),(17,2001),(19,524289)):
            blob = fixture();struct.pack_into('<Q',blob,256+8*index,value)
            with self.assertRaises(RuntimeError):witness.decode(bytes(blob))


if __name__=='__main__': unittest.main()
