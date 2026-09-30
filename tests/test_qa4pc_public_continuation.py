import importlib.util
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parents[1]/'research/qa4pc-stage-attribution'
sys.path.insert(0,str(HERE))
import journal
import runner
sys.path.remove(str(HERE))


def read(name):return json.loads((HERE/name).read_bytes())


class PublicContinuationTests(unittest.TestCase):
    def test_public_journals_account_for_each_original_job_exactly_once(self):
        manifest=read('plan_manifest.json');successor=read('continuation_manifest.json')
        # Length-only public metadata validates accounting, not private token content.
        jobs=[{**j,'input_ids':[0]*j['input_tokens'],'max_new_tokens':0} for j in manifest['jobs'] if j['backend']=='qwen']
        first=journal.replay(journal.read_events(HERE/'results/qwen.jsonl'),
            plan_hash=manifest['plan_sha256'],backend='qwen',jobs=jobs)
        last=journal.replay(journal.read_events(HERE/'results/qwen_continuation.jsonl'),
            plan_hash=successor['plan_sha256'],backend='qwen',jobs=jobs[2:])
        self.assertTrue(first['halted']);self.assertFalse(last['halted'])
        self.assertEqual(first['started']+last['started'],[j['id'] for j in jobs])
        self.assertFalse(set(first['started'])&set(last['started']))
        self.assertEqual(first['input_tokens']+last['input_tokens'],sum(len(j['input_ids']) for j in jobs))
        self.assertEqual(first['output_tokens']+last['output_tokens'],0)
        for public,original in zip(successor['jobs'],jobs[2:]):
            self.assertEqual(public['job_sha256'],original['job_sha256'])

    def test_every_saved_successor_readout_and_smoke_annotation_recomputes(self):
        jobs={j['id']:j for j in read('plan_manifest.json')['jobs']}
        totals={'main':0,'smoke':0};ties=[]
        for event in journal.read_events(HERE/'results/qwen_continuation.jsonl'):
            if event['event']!='call_finish':continue
            r=event['result'];d=r['detail'];j=jobs[event['job_id']]
            p=runner.extract(d['candidate_logits'],d['full_logsumexp'],d['top_token_id'],d['top_logit'],j['options'])
            self.assertEqual(p['action'],r['action']);self.assertEqual(d['physical_forwards'],1)
            self.assertEqual(p['exact_tie'],d['parsed']['exact_tie'])
            totals[j['phase']]+=1
            if p['exact_tie']:ties.append(event['job_id'])
            if j['phase']=='smoke':
                s=d['amended_smoke_policy'];self.assertFalse(s['semantic_accuracy_is_gate'])
                self.assertEqual(s['observed'],p['action']);self.assertEqual(s['correct'],s['expected']==p['action'])
        self.assertEqual(totals,{'main':256,'smoke':4})
        report=read('continuation_report.json')
        self.assertEqual(set(ties),{x['job_id'] for x in report['qwen_readout_diagnostics']['main_exact_ties']})


if __name__=='__main__':unittest.main()
