import copy
import sys
import unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/evidence-gap'))
from gap_data import build_rows,world_truth,direct_truth,exhaustive_solver_audit,parse_text


class GapDataTests(unittest.TestCase):
    def test_possible_worlds_and_direct_short_circuit_agree_exhaustively(self):
        self.assertEqual(exhaustive_solver_audit()['partial_or_conflicting_states'],1120)

    def test_reserved_composed_mechanism_and_balanced_development(self):
        rows=build_rows();dev=[r for r in rows if r['split']=='development']
        self.assertEqual(len(dev),72)
        self.assertEqual(Counter(r['gold'] for r in dev),{'ALLOW':24,'DENY':24,'INSUFFICIENT':24})
        self.assertTrue(all(r['split']=='reserved_test' for r in rows if r['family']=='composed_route'))
        self.assertEqual(len({r['parent'] for r in rows}),48)

    def test_redundant_missing_approval_does_not_force_unknown(self):
        row=next(r for r in build_rows() if r['family']=='joint_approval' and r['variant']=='nondecisive_missing' and r['gold']=='DENY')
        self.assertFalse(any(r['field']=='review_a' and r['scope']==row['target'] for r in row['records']))
        self.assertEqual(world_truth(row)[0],'DENY')
        decisive=copy.deepcopy(row);decisive['records']=[r for r in decisive['records'] if not (r['field']=='review_b' and r['scope']==row['target'])]
        self.assertEqual(world_truth(decisive)[0],'INSUFFICIENT')

    def test_unknown_grammar_is_rejected_and_rendering_preserves_truth(self):
        rows=build_rows()
        for row in rows:
            parsed=parse_text(row['state'],row['instruction'],row['family'],row['sites'])
            self.assertEqual(world_truth(parsed),world_truth(row))
        r=rows[0]
        with self.assertRaises(ValueError):parse_text(r['state']+'\nUnknown claim.',r['instruction'],r['family'],r['sites'])


if __name__=='__main__':unittest.main()
