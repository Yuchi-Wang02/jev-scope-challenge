import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/finite-choice-readout'))
import finite_readout as study
import analyze_finite as analysis


def fixture():
    """Synthetic results over the frozen plan: never model evaluation evidence."""
    plan=study.read(study.HERE/'plan.json')
    freeze={'plan_sha256':'synthetic','parent_hashes_lf':study.parent_pins()}
    events=[{'event':'header','version':1,'plan_sha256':'synthetic','backend':'qwen',
             'job_ids':[j['id'] for j in plan['jobs']]},
            {'event':'session_start','session':0,'backend_metadata':{'synthetic':True}}]
    for j in plan['jobs']:
        action=j['expected_smoke_action'] if j['phase']=='smoke' else 'Yes'
        index=j['options'].index(action);values=[0.0]*4;values[index]=8.0
        parsed=study.extract(values,10.0,study.TOKEN_IDS[index],8.0,j['options'])
        result={'status':'ok','action':action,'input_tokens':len(j['input_ids']),
                'output_tokens':0,'latency_seconds':.01,
                'detail':{'candidate_logits':values,'full_logsumexp':10.0,'top_token_id':study.TOKEN_IDS[index],
                          'top_logit':8.0,'parsed':parsed,'physical_forwards':1,'use_cache':True,'logits_to_keep':1}}
        events += [{'event':'call_start','job_id':j['id']},
                   {'event':'call_finish','job_id':j['id'],'result':result}]
    events.append({'event':'session_end','session':0,'elapsed_seconds':1.0})
    for i,e in enumerate(events):e['seq']=i
    return plan,freeze,events


class FiniteAnalysisTests(unittest.TestCase):
    def test_complete_fixture_and_truncated_grid_keep_distinct_denominators(self):
        p,f,e=fixture();r=analysis.analyze(p,f,e)
        self.assertEqual(r['status'],'complete')
        self.assertEqual(r['smoke']['passed'],8)
        self.assertEqual(r['resources']['physical_forwards_reported'],56)
        self.assertEqual(r['conditions']['prefill_order0']['metric']['item_accuracy']['numerator'],10)
        self.assertIn(b'prefill_order0|24/24|10/24|2/12|0/24',analysis.markdown(r))
        partial=e[:20]+[{'event':'session_end','session':0,'elapsed_seconds':.1,'seq':20}]
        r=analysis.analyze(p,f,partial)
        self.assertEqual(sum(c['finished'] for c in r['conditions'].values()),1)
        self.assertTrue(all(c['metric'] is None for c in r['conditions'].values()))

    def test_tampered_action_or_parsed_probability_is_rejected(self):
        p,f,e=fixture();bad=copy.deepcopy(e)
        bad[19]['result']['action']='No'
        with self.assertRaises(ValueError):analysis.analyze(p,f,bad)
        bad=copy.deepcopy(e);bad[19]['result']['detail']['parsed']['conditional_probabilities']['A']=.123
        with self.assertRaises(ValueError):analysis.analyze(p,f,bad)


if __name__=='__main__':unittest.main()
