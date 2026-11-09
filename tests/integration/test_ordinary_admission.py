from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from ordinary_admission import command_oracle
from test_frontier_reversal import fixture


class OrdinaryAdmission(unittest.TestCase):
    def test_unobserved_work_is_checked_by_the_existing_independent_route_oracle(self):
        rows=fixture()
        self.assertEqual(command_oracle(),rows[-1]['command_hash'])
        self.assertEqual(rows[-1]['accepted'],80)
        self.assertTrue(rows[899]['camera_reversed'])
        self.assertFalse(rows[898]['camera_reversed'])


if __name__=='__main__':unittest.main()
