"""Scientific evidence boundaries: corruption, input identity and read-only replay."""
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/fact-execution'))
from fact_run import HERE, read_rows
from fact_analyze import analyze, validate_records


@unittest.skipUnless((HERE/'results/summary.json').exists(),'Scoring has not been published')
class FactEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.plans=read_rows(HERE/'data/inputs.jsonl')
        self.config=json.loads((HERE/'manifest.json').read_text())['config_hash']

    def test_foreign_omitted_duplicate_and_wrong_score_width_fail(self):
        good=read_rows(HERE/'results/N0.jsonl')
        for mutation in ('foreign','duplicate','omitted','width','logit'):
            rows=copy.deepcopy(good)
            if mutation=='foreign':rows[0]['representation']='review_only'
            elif mutation=='duplicate':rows[-1]=copy.deepcopy(rows[0])
            elif mutation=='omitted':rows.pop()
            elif mutation=='width':rows[0]['probabilities'].pop()
            else:rows[0]['logits'][0]=float('inf')
            with self.assertRaises(ValueError):validate_records(rows,self.plans,'N0',self.config)

    def test_pointer_options_and_parity_are_evidence(self):
        good=read_rows(HERE/'results/K1.jsonl')
        for mutation in ('options','parity','tokens'):
            rows=copy.deepcopy(good)
            if mutation=='options':rows[0]['options'][0]='A different option'
            elif mutation=='parity':rows[0]['parity']['max_probability_delta']=float('nan')
            else:rows[0]['token_ids'][0]+=1
            with self.assertRaises(ValueError):validate_records(rows,self.plans,'K1',self.config)

    def test_full_recompute_preserves_files_and_never_invents_citations(self):
        protected=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
        before={p:p.read_bytes() for p in protected};s,rows,claims=analyze()
        self.assertTrue(all(p.read_bytes()==b for p,b in before.items()))
        self.assertEqual(s['reserved_model_records'],0);self.assertEqual(s['rewrite_model_records'],0)
        self.assertTrue(all(c['evidence_spans'] is None for c in claims))
        self.assertFalse(any(r.get('attribution')=='executor_defect' for r in rows))


if __name__=='__main__':unittest.main()
