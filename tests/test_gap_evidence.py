import copy
import json
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/evidence-gap'))
import gap_analyze
from gap_run import HERE, read_rows
from verify_gap import extra_record_checks, text_reference, verify


class GapEvidenceTests(unittest.TestCase):
    def test_foreign_reserved_record_is_rejected(self):
        original=gap_analyze.read_rows
        def changed(path):
            rows=original(path)
            if path==HERE/'results/N0.jsonl':
                rows=copy.deepcopy(rows); rows[0]['split']='reserved_test'
            return rows
        with patch.object(gap_analyze,'read_rows',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'Reserved'):
                gap_analyze.analyze()

    def test_logit_corruption_is_rejected(self):
        original=gap_analyze.read_rows
        def changed(path):
            rows=original(path)
            if path==HERE/'results/N1.jsonl':
                rows=copy.deepcopy(rows); rows[0]['logits'][0]+=5
            return rows
        with patch.object(gap_analyze,'read_rows',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'logit/probability'):
                gap_analyze.analyze()

    def test_nonfinite_parity_and_wrong_option_text_are_rejected(self):
        r=read_rows(HERE/'results/K1.jsonl')[0]
        p=next(p for p in read_rows(HERE/'data/inputs.jsonl') if (p['id'],p['mapping'])==(r['id'],r['mapping']))
        for field in ('nan','options'):
            bad=copy.deepcopy(r)
            if field=='nan':bad['parity']['max_probability_delta']=math.nan
            else:bad['options'][0]='Other decision'
            with self.assertRaises(ValueError):extra_record_checks(bad,p)

    def test_reference_needs_only_text_and_rejects_unknown_policy(self):
        for c in read_rows(HERE/'data/cases.jsonl'):
            self.assertEqual(text_reference(c['state'],c['instruction']),c['gold'])
        with self.assertRaises(ValueError):text_reference('anything','unrecognized rule')

    def test_full_verification_is_read_only(self):
        paths=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
        before={p:p.read_bytes() for p in paths}
        self.assertEqual(verify()['reserved_model_records'],0)
        self.assertEqual(before,{p:p.read_bytes() for p in paths})


if __name__=='__main__':unittest.main()
