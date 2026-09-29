import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/evidence-gap'))
from review_tools import material, files, validate_annotations, FIELDS


class ReviewTests(unittest.TestCase):
    def test_blind_pack_contains_no_truth_or_model_metadata(self):
        pack,key,starter=material()
        self.assertEqual(len(pack),288);self.assertEqual(len(set(starter)),6)
        for row in pack:self.assertEqual(set(row),{'review_id','state','policy'})
        self.assertEqual(len({k['review_id'] for k in key}),288)
        page=files()['review/review.html']
        self.assertNotIn('"program_gold"',page)
        self.assertNotIn('"split"',page)
        self.assertNotIn('"prediction"',page)

    def test_foreign_duplicate_and_empty_annotations_cannot_count_as_review(self):
        known={x['review_id']:x for x in material()[0]}
        row=dict(zip(FIELDS,[next(iter(known)),'ALLOW','reason',False,'','test_fixture','2026-09-29']))
        self.assertEqual(len(validate_annotations([row],known)),1)
        for bad in ([row,row],[{**row,'review_id':'foreign'}],[{**row,'reason':''}],
                    [{**row,'label':''}],[{**row,'ambiguity':True}]):
            with self.assertRaises(ValueError):validate_annotations(bad,known)


if __name__=='__main__':unittest.main()
