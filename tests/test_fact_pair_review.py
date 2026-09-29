import csv
import io
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/fact-execution'))
from review_pair_tools import HERE,FIELDS,fingerprint,inspect_csv


def csv_payload(rows):
    out=io.StringIO();w=csv.DictWriter(out,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows);return out.getvalue()


class FactPairReviewTests(unittest.TestCase):
    def fixture(self):
        first=next(csv.DictReader(io.StringIO((HERE/'review/blank.csv').read_text())))
        return first | {'same_facts_yes_no_unclear':'yes','reason':'Unit test fixture, not a semantic judgment.',
            'reviewer':'TEST_FIXTURE_NOT_HUMAN','reviewed_at':'2026-09-29'}

    def test_blank_template_is_zero_annotations(self):
        r=inspect_csv((HERE/'review/blank.csv').read_text(),fingerprint())
        self.assertEqual(r['submitted_rows'],0);self.assertEqual(r['unreviewed_pairs'],144)
        self.assertFalse(r['rewrite_inference_open'])

    def test_valid_syntax_never_certifies_independence_or_opens_inference(self):
        r=inspect_csv(csv_payload([self.fixture()]),fingerprint())
        self.assertEqual(r['submitted_rows'],1)
        self.assertFalse(r['reviewer_independence_verified']);self.assertFalse(r['semantic_truth_certified']);self.assertFalse(r['rewrite_inference_open'])

    def test_foreign_duplicate_incomplete_and_wrong_pack_fail(self):
        row=self.fixture()
        for rows in ([row,row],[row | {'review_id':'foreign'}],[row | {'reason':''}],[row | {'same_facts_yes_no_unclear':''}],[row | {'reviewed_at':'yesterday'}]):
            with self.assertRaises(ValueError):inspect_csv(csv_payload(rows),fingerprint())
        with self.assertRaises(ValueError):inspect_csv(csv_payload([row]),'0'*64)


if __name__=='__main__':unittest.main()
