"""Meaningful source, semantic, accounting and redaction checks. No network."""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'research/payment-ownership'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

S=load('payment_study_tests',P/'study.py')
old=sys.modules.get('study');sys.modules['study']=S
try:
    R=load('payment_api_tests',P/'run_api.py')
    V=load('payment_review_tests',P/'review_check.py')
finally:
    if old is None: sys.modules.pop('study',None)
    else: sys.modules['study']=old

class PaymentOwnershipTests(unittest.TestCase):
    def test_reproducible_source_projection_and_pairs(self):
        self.assertEqual(S.verify_data()['program_parser_correct'],48)

    def test_source_records_preserved(self):
        selection=S.read(P/'vendor/selected_records.json')
        for c in S.rows(P/'data/cases.jsonl'):
            source=next(s for s in selection if s['user']['user_id']==c['source_user_id'])
            self.assertEqual(c['full']['user_profile']['payment_methods'],source['user']['payment_methods'])
            for order in c['full']['orders']:
                original=next(o for o in source['orders'] if o['order_id']==order['order_id'])
                for key,value in order.items(): self.assertEqual(value,original[key])

    def test_gift_exception_and_foreign_method(self):
        state=S.smoke_cases()[0]['state']
        self.assertEqual(S.reference(state,'#SMOKE_A','gift_a'),S.LABELS[0])
        self.assertEqual(S.reference(state,'#SMOKE_A','card_b'),S.LABELS[1])

    def test_missing_payment_history_is_unknown(self):
        state=S.smoke_cases()[3]['state']
        self.assertEqual(S.reference(state,'#SMOKE_A','card_b'),S.LABELS[2])

    def test_ambiguous_request_parser_abstains(self):
        parsed=S.parse_request(S.smoke_cases()[4]['state'])
        self.assertFalse(parsed['covered']);self.assertEqual(parsed['prediction'],S.LABELS[2])

    def test_parser_does_not_receive_gold_metadata(self):
        c=S.rows(P/'data/cases.jsonl')[0]
        state=copy.deepcopy(c['full']);state['customer_request']='Please choose the one I mean.'
        self.assertFalse(S.parse_request(state)['covered'])
        for job in S.rows(P/'plans/primary.jsonl'):
            self.assertNotIn('reference',job['body']['state']);self.assertNotIn('parent_id',job['body']['state'])

    def test_unlisted_destination_invalid(self):
        self.assertEqual(S.reference(S.smoke_cases()[0]['state'],'#SMOKE_A','absent'),S.LABELS[1])

    def test_response_mapping_and_rejections(self):
        data={'model':S.MODEL,'answers':{'decision':{'type':'choice','choice':'A',
              'probabilities':{'A':0.8,'B':0.1,'C':0.1}}},'usage':{'input_tokens':40}}
        self.assertEqual(S.validate_response(data,1)['prediction'],S.LABELS[2])
        bad=copy.deepcopy(data);bad['model']='unexpected'
        with self.assertRaises(ValueError):S.validate_response(bad,0)
        for probs in [{'A':0.8,'B':0.8,'C':0.1},{'A':float('nan'),'B':0.1,'C':0.1},
                      {'A':True,'B':0,'C':0},{'A':0.8,'B':0.2}]:
            bad=copy.deepcopy(data);bad['answers']['decision']['probabilities']=probs
            with self.assertRaises(ValueError):S.validate_response(bad,0)
        bad=copy.deepcopy(data);bad['answers']['decision']['choice']='B'
        with self.assertRaises(ValueError):S.validate_response(bad,0)

    def test_pending_attempt_prevents_reissue(self):
        start={'event':'started','attempt_id':1,'retry_index':0,'planned_input_units':100}
        self.assertEqual(R.accounting([start])['unfinished'],[1])
        with self.assertRaises(RuntimeError): R.check_budget([start],{'planned_input_units':100},0,
            {'attempt_limit':405,'retry_limit':15,'planned_input_limit':2_000_000})

    def test_budget_reserves_before_call_and_counts_failed_attempt(self):
        events=[{'event':'started','attempt_id':1,'retry_index':0,'planned_input_units':100},
                {'event':'finished','attempt_id':1,'input_tokens':None}]
        self.assertEqual(R.accounting(events)['unknown_usage_attempts'],1)
        limits={'attempt_limit':2,'retry_limit':0,'planned_input_limit':150}
        with self.assertRaises(RuntimeError):R.check_budget(events,{'planned_input_units':51},0,limits)
        with self.assertRaises(RuntimeError):R.check_budget(events,{'planned_input_units':1},1,limits)
        self.assertEqual(R.check_budget(events,{'planned_input_units':50},0,limits)['attempts'],1)

    def test_redaction(self):
        secret='private_test_value'
        self.assertEqual(R.sanitize({'Authorization':secret,'message':'prefix '+secret},secret),{'message':'prefix [REDACTED]'})

    def test_review_blinding_and_blank_templates(self):
        items=S.rows(P/'review/inputs.jsonl')
        self.assertEqual(len(items),96)
        for item in items:self.assertEqual(set(item),{'review_id','state'})
        self.assertEqual(V.validate(P/'review/reviewer_A.csv')['complete'],0)

    def test_plan_caps_and_labels(self):
        jobs=S.rows(P/'plans/primary.jsonl')
        self.assertEqual(len(jobs),198);self.assertEqual(len({j['job_id'] for j in jobs}),198)
        self.assertLess(sum(j['planned_input_units'] for j in jobs),2_000_000)
        self.assertEqual(sorted(c['reference'] for c in S.smoke_cases()),sorted(S.LABELS*2))

if __name__=='__main__':unittest.main()
