import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/evidence-guards'))
import guard_study as study
from verify_guards import check


class GuardEvidenceTests(unittest.TestCase):
    def test_duplicate_reserved_and_foreign_grids_are_rejected(self):
        cases=study.read_rows(study.HERE/'development_cases.jsonl')
        raw=study.read_rows(study.GAP/'results/N0.jsonl')
        for mutation in ('duplicate','reserved','foreign'):
            bad=copy.deepcopy(raw);main=[r for r in bad if r['kind']=='main']
            if mutation=='duplicate':main[0].update(copy.deepcopy(main[1]))
            elif mutation=='reserved':main[0]['split']='reserved_test'
            else:main[0]['id']='foreign'
            with self.assertRaises(ValueError):study.grid(bad,cases,'N0')

    def test_gate_entry_point_receives_only_exact_visible_strings(self):
        original=study.parse_visible;seen=[]
        visible={(c['state'],c['instruction']) for c in study.read_rows(study.HERE/'development_cases.jsonl')}
        def checked(state,policy):
            self.assertIsInstance(state,str);self.assertIsInstance(policy,str)
            self.assertIn((state,policy),visible);seen.append((state,policy))
            return original(state,policy)
        with patch.object(study,'parse_visible',side_effect=checked):study.derive()
        self.assertEqual(len(seen),72)

    def test_zero_actions_has_undefined_risk_not_a_false_zero_error_guarantee(self):
        summary,*_=study.derive()
        for panels in summary['results'].values():
            self.assertEqual(panels['always_insufficient']['all']['actions'],0)
            self.assertIsNone(panels['always_insufficient']['all']['action_risk'])
            self.assertEqual(panels['always_insufficient']['all']['false_insufficient'],144)

    def test_verification_never_rewrites_scientific_or_followup_files(self):
        paths=[p for directory in (study.GAP,study.HERE) for p in directory.rglob('*')
               if p.is_file() and '__pycache__' not in p.parts]
        before={p:p.read_bytes() for p in paths}
        self.assertEqual(check()['new_model_forwards'],0)
        self.assertEqual(before,{p:p.read_bytes() for p in paths})


if __name__=='__main__':unittest.main()
