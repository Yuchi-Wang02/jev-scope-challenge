"""Negative controls for scientific denominators and review/result separation."""
import copy
import importlib.util
import sys
import tempfile
import io
import zipfile
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'research/candidate-completeness'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
saved={n:sys.modules.get(n) for n in ('study','local_run','run','analyze','reasoning_run','reasoning_greedy')}
try:
    S=load('candidate_analysis_study',P/'study.py');sys.modules['study']=S
    L=load('candidate_analysis_local',P/'local_run.py');sys.modules['local_run']=L
    R=load('candidate_analysis_api',P/'run.py');sys.modules['run']=R
    A=load('candidate_analysis',P/'analyze.py');V=load('candidate_review_tools',P/'review_tools.py')
    B=load('candidate_reasoning_run',P/'reasoning_run.py')
    sys.modules['analyze']=A;sys.modules['reasoning_run']=B
    G=load('candidate_reasoning_greedy',P/'reasoning_greedy.py');sys.modules['reasoning_greedy']=G
    RA=load('candidate_reasoning_analysis',P/'reasoning_analyze.py')
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

    def test_reasoning_batches_reserve_padding_and_all_decisions(self):
        f=B.verify();batches=S.rows(P/'plans/reasoning_batches.jsonl')
        self.assertEqual(len(batches),38)
        self.assertEqual(len({j for b in batches for j in b['job_ids']}),150)
        self.assertLessEqual(sum(b['reserved_token_positions'] for b in batches),f['max_processed_token_positions'])
        self.assertEqual(sum(b['reserved_forwards'] for b in batches),19494)
        official=S.read(P/'checkpoint_audit.json');local=S.read(P/'local_freeze.json')
        self.assertTrue(all(local['model_files_sha256'][n]==h for n,h in official['weight_lfs_sha256'].items()))

    def test_unfinished_reasoning_batch_is_not_replayed(self):
        old=(B.OUT,B.LEDGER)
        try:
            with tempfile.TemporaryDirectory() as d:
                B.OUT=Path(d)/'output.jsonl';B.LEDGER=Path(d)/'ledger.jsonl'
                S.write_rows(B.LEDGER,[{'event':'started','batch_id':'smoke_000'}])
                with self.assertRaises(RuntimeError):B.completion()
                S.write_rows(B.LEDGER,[{'event':'started','batch_id':'smoke_000'},
                    {'event':'finished','batch_id':'smoke_000','ok':True,'responses':[{'job_id':'mock-for-resume-test-only'}]}])
                with self.assertRaises(RuntimeError):B.completion()
        finally:B.OUT,B.LEDGER=old

    def test_review_zip_creator_is_not_content_but_corruption_is(self):
        expected={'README.md':'review only\n','reviewer.csv':'blank\n'}
        for system in (0,3):
            for corrupt in (False,True):
                data=io.BytesIO()
                with zipfile.ZipFile(data,'w') as z:
                    for name,text in expected.items():
                        entry=zipfile.ZipInfo(name);entry.create_system=system
                        z.writestr(entry,text+('changed' if corrupt else ''))
                data.seek(0)
                if corrupt:
                    with self.assertRaises(AssertionError):V.verify_archive(data,expected)
                else:V.verify_archive(data,expected)

    def test_complete_reasoning_grid_preserves_stop_and_work_accounting(self):
        s=RA.analyze()
        self.assertEqual(s,S.read(P/'results/reasoning_summary.json'))
        self.assertEqual(s['work']['decisions'],150)
        self.assertEqual(s['stopped_sampled_smoke_work']['decisions'],6)
        self.assertEqual(s['total_control_decisions_including_stopped'],156)
        self.assertEqual(sum(v['records'] for v in s['termination_strata'].values()),144)

if __name__=='__main__':unittest.main()
