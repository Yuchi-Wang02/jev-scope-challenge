import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/next-study'))
from study import HERE, MAPS, gold_for, read_rows, validate, native_prompt


class StudyTests(unittest.TestCase):
    def test_interventions_and_groups(self):
        rows = read_rows(HERE/'data/cases.jsonl')
        validate(rows)
        for variant in ('full','hold','flip'):
            self.assertEqual(sum(r['gold']=='ALLOW' for r in rows if r['variant']==variant),12)
            self.assertEqual(sum(r['gold']=='DENY' for r in rows if r['variant']==variant),12)
        self.assertEqual(sum(r['gold']=='INSUFFICIENT' for r in rows),24)
        self.assertEqual(len({r['parent'] for r in rows if r['split']=='exploratory_test'}),12)

    def test_missing_authority_does_not_fall_back_to_guest_or_old_request(self):
        rows = read_rows(HERE/'data/cases.jsonl')
        for row in rows:
            if row['variant']=='missing':
                self.assertEqual(gold_for(row),'INSUFFICIENT')

    def test_no_gold_or_split_is_inserted_in_native_prompt(self):
        import copy
        row = read_rows(HERE/'data/cases.jsonl')[0]
        altered = copy.deepcopy(row)
        altered.update(gold='SECRET_ANSWER',split='SECRET_SPLIT',id='SECRET_ID')
        self.assertEqual(native_prompt(row,MAPS[0]),native_prompt(altered,MAPS[0]))


if __name__ == '__main__': unittest.main()
