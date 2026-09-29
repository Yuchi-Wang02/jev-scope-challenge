import unittest
from pathlib import Path
from core import (MAPPINGS, grammar_reference, job_key, read_jsonl, request_for,
                  score_records, semantic_probs, validate_cases)
ROOT=Path(__file__).resolve().parents[1]

class ProbeTests(unittest.TestCase):
    def test_quartets_and_parser_labels(self):
        cases=read_jsonl(ROOT/'data/cases.jsonl')
        self.assertEqual(validate_cases(cases)['inputs'],48)
        for c in cases:
            self.assertEqual(grammar_reference({'target':c['target'],'customer_message':c['customer_message']}),c['gold'],c['id'])

    def test_gold_and_ids_are_not_sent(self):
        case=read_jsonl(ROOT/'data/cases.jsonl')[0]
        body=request_for(case,'cancel_first')
        self.assertEqual(set(body['state']),{'target','customer_message'})
        self.assertNotIn('gold',body['questions']['decision'])

    def test_mapping_is_in_cache_identity(self):
        self.assertNotEqual(job_key('config','S01-A','cancel_first',0),job_key('config','S01-A','keep_first',0))
        self.assertNotEqual(job_key('config','S01-A','cancel_first',0),job_key('config','S01-A','cancel_first',1))
        self.assertNotEqual(job_key('config','S01-A','cancel_first',0),job_key('config2','S01-A','cancel_first',0))

    def test_invalid_probabilities_fail(self):
        for bad in ({'A':float('nan'),'B':0.5},{'A':0.1,'B':0.1},{'A':-0.1,'B':1.1}):
            with self.assertRaises(AssertionError): semantic_probs(bad,'cancel_first')

    def test_stable_wrong_is_not_a_pass_and_missing_is_in_denominator(self):
        cases=read_jsonl(ROOT/'data/cases.jsonl')[:4]
        rows=[{'case_id':c['id'],'mapping':m,'replicate':0,'ok':True,'prediction':'KEEP'}
              for c in cases for m in MAPPINGS]
        score=score_records(cases,rows)
        self.assertEqual(score['robust_pass'],0)
        self.assertEqual(score['correct'],4)
        self.assertEqual(score['pairs']['flip']['correct_pairs'],0)
        score=score_records(cases,rows[:-1])
        self.assertEqual(score['expected'],8)
        self.assertEqual(score['missing'],1)
        self.assertEqual(score['robust_pass'],0)

    def test_parser_rejects_unsupported_or_conflicting_grammar(self):
        self.assertIsNone(grammar_reference({'target':'plan','customer_message':'Maybe I should leave.'}))
        self.assertIsNone(grammar_reference({'target':'plan','customer_message':'Cancel the plan. Keep the plan.'}))

if __name__=='__main__': unittest.main()

