"""Negative controls for scientific denominators and review/result separation."""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'research/candidate-completeness'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
saved={n:sys.modules.get(n) for n in ('study','local_run','run')}
try:
    S=load('candidate_analysis_study',P/'study.py');sys.modules['study']=S
    L=load('candidate_analysis_local',P/'local_run.py');sys.modules['local_run']=L
    R=load('candidate_analysis_api',P/'run.py');sys.modules['run']=R
    A=load('candidate_analysis',P/'analyze.py');V=load('candidate_review_tools',P/'review_tools.py')
finally:
    for n,m in saved.items():
        if m is None:sys.modules.pop(n,None)
        else:sys.modules[n]=m

class CoverageAnalysisTests(unittest.TestCase):
    def test_refusal_shortcut_does_not_receive_pair_credit(self):
        cases=S.rows(P/'data/cases.jsonl')
        pred={c['case_id']:'NOT_ESTABLISHED' for c in cases};m=A.endpoints(cases,pred)
        self.assertEqual(m['correct'],12);self.assertEqual(m['complete_parents'],0)
        self.assertEqual(m['false_commitments']['count'],0)
        self.assertEqual(m['unnecessary_deferrals']['count'],60)
        self.assertEqual(m['paired']['product_required_change']['both_correct'],0)
        self.assertFalse(m['screen_pass'])

    def test_missing_case_cannot_shrink_denominator(self):
        cases=S.rows(P/'data/cases.jsonl');pred={c['case_id']:c['reference'] for c in cases}
        pred.pop(cases[0]['case_id'])
        with self.assertRaises(AssertionError):A.endpoints(cases,pred)

    def test_duplicate_result_cannot_replace_missing_case(self):
        records=S.rows(P/'results/responses.jsonl');records[-1]=copy.deepcopy(records[0])
        with self.assertRaises(AssertionError):A.validate_records(S.rows(P/'plans/primary.jsonl'),records)

    def test_complete_public_evidence_recomputes(self):
        self.assertEqual(A.analyze(),S.read(P/'results/summary.json'))

    def test_review_package_does_not_include_output_or_pair_mapping(self):
        files,mapping=V.materials()
        self.assertNotIn('mapping.jsonl',files);self.assertEqual(len(mapping),72)
        inputs=[__import__('json').loads(x) for x in files['inputs.jsonl'].splitlines()]
        self.assertTrue(all(set(r)=={'review_id','state'} for r in inputs))
        self.assertTrue(all(not {'reference','prediction','parent_id','case_id'}&set(r['state']) for r in inputs))
        self.assertNotIn('results/',files['review.html'])
        self.assertEqual(V.validate(P/'review/reviewer.csv')['complete'],0)

if __name__=='__main__':unittest.main()
