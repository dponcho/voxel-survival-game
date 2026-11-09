"""Destruction is distinct from close/join, and absent/error is distinct from zero."""
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/qa'))
import observer_disposal as disposal
from test_cpu_cycle_capability import boundary
from test_shipping_observer import record, encode, metadata


def release(status='disposed'):
    return dict(schema=disposal.DISPOSAL, status=status, disposed=status == 'disposed', qualified=False,
                counter_start=boundary(10, 2**63, 100), counter_end=boundary(30, 2**63+100, 150),
                storage_before=dict(record_count=1, lane_count=1, open_spans=0,
                                    record_capacity_bytes=192, lane_capacity_bytes=512, object_bytes=600),
                storage_after=0 if status == 'disposed' else None, failure_code=0, strong_owners=1)


class DisposalTests(unittest.TestCase):
    def test_last_owner_release_requires_destruction_and_empty_scope_stack(self):
        good = release()
        disposal.disposal(good, 'disposed')
        for key, value in (('disposed', False), ('strong_owners', 2), ('storage_after', None)):
            bad = copy.deepcopy(good); bad[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError): disposal.disposal(bad, 'disposed')
        bad = copy.deepcopy(good); bad['storage_before']['open_spans'] = 1
        with self.assertRaises(RuntimeError): disposal.disposal(bad, 'disposed')

    def test_join_or_seal_cannot_turn_retained_storage_into_freed_storage(self):
        retained = release('retained_owner'); retained['strong_owners'] = 2
        disposal.disposal(retained, 'retained_owner')
        retained['storage_after'] = 0
        with self.assertRaises(RuntimeError): disposal.disposal(retained, 'retained_owner')
        retained['storage_after'] = None; retained['strong_owners'] = 1
        with self.assertRaises(RuntimeError): disposal.disposal(retained, 'retained_owner')

    def test_absent_and_foreign_thread_refusals_retain_nulls(self):
        absent = release('absent')
        for key in ('storage_before', 'storage_after', 'failure_code', 'strong_owners'): absent[key] = None
        disposal.disposal(absent, 'absent')
        absent['failure_code'] = 0
        with self.assertRaises(RuntimeError): disposal.disposal(absent, 'absent')
        absent['failure_code'] = None; absent['status'] = 'wrong_thread'
        absent['counter_start'] = absent['counter_end'] = None
        disposal.disposal(absent, 'wrong_thread')
        absent['counter_start'] = 0
        with self.assertRaises(RuntimeError): disposal.disposal(absent, 'wrong_thread')

    def test_disposal_counter_failures_unsigned_rounding_and_wrong_thread_reject(self):
        changes = [lambda v: v['counter_end']['reads'][1].__setitem__('success', False),
                   lambda v: v['counter_end']['reads'][1].__setitem__('cycles', 2**53+1),
                   lambda v: v['counter_end']['reads'][1].__setitem__('cycles', '00'),
                   lambda v: v['counter_end'].__setitem__('thread_id', '2'),
                   lambda v: v['counter_end']['reads'][1].__setitem__('cycles', '0')]
        for change in changes:
            value = release(); change(value)
            with self.subTest(change=change), self.assertRaises(RuntimeError): disposal.disposal(value, 'disposed')

    def test_missing_or_fractional_storage_is_not_an_allocation_witness(self):
        for key in release()['storage_before']:
            value = release(); value['storage_before'][key] = 1.0
            with self.subTest(key=key), self.assertRaises(RuntimeError): disposal.disposal(value, 'disposed')
        value = release(); del value['storage_before']['record_capacity_bytes']
        with self.assertRaises(RuntimeError): disposal.disposal(value, 'disposed')

    def test_open_or_active_state_cannot_be_claimed_without_corresponding_stack(self):
        value = release('open_spans')
        with self.assertRaises(RuntimeError): disposal.disposal(value, 'open_spans')
        value['storage_before']['open_spans'] = 1
        disposal.disposal(value, 'open_spans')
        value['status'] = 'active'
        with self.assertRaises(RuntimeError): disposal.disposal(value, 'active')

    def test_failed_counter_prefix_preserves_flagged_nulls_and_rejects_successful_zero(self):
        rows = [record(1, 0, 2, 1, 77, [0, 0, 0, 0])]
        for stamp in rows[0]['reads']: stamp.update(flags=1, error=6)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'trace.bin'; path.write_bytes(encode(rows, failure=4, lanes=1))
            meta = metadata(rows, failure=4, lanes=1)
            self.assertEqual(disposal.failed_prefix(path, meta, 4)['failure_code'], 4)
            rows[0]['reads'][0].update(flags=3, error=0)
            path.write_bytes(encode(rows, failure=4, lanes=1))
            with self.assertRaises(RuntimeError): disposal.failed_prefix(path, meta, 4)

    def test_finite_cap_fixture_keeps_its_actual_cap_without_relaxing_old_codec(self):
        rows = [record(1, 0, 2, 1, 77, [100, 110, 140, 150])]
        data = bytearray(encode(rows, failure=1, lanes=1)); struct.pack_into('<Q', data, 16, len(data))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'trace.bin'; path.write_bytes(data)
            meta = metadata(rows, failure=1, lanes=1); meta['cap_bytes'] = len(data)
            self.assertEqual(disposal.failed_prefix(path, meta, 1)['bytes'], 232)
            with self.assertRaises(RuntimeError): disposal.observer.decode(data)
            path.write_bytes(data[:-1])
            with self.assertRaises(RuntimeError): disposal.failed_prefix(path, meta, 1)


if __name__ == '__main__': unittest.main()
