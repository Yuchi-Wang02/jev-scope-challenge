"""Coverage semantics, witness compatibility, and safe bounded execution checks."""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'research/candidate-completeness'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
C=load('coverage_study_test',P/'study.py')
saved=sys.modules.get('study');sys.modules['study']=C
try:R=load('coverage_run_test',P/'run.py')
finally:
    if saved is None:sys.modules.pop('study',None)
    else:sys.modules['study']=saved

class CandidateCompletenessTests(unittest.TestCase):
    def test_disjoint_reconstruction_pairs_and_opposite_worlds(self):
        self.assertEqual(C.verify_data()['cases'],72)

    def test_omission_matters_only_for_unresolved_product_target(self):
        base=copy.deepcopy(C.smokes()[0]['state'])
        base['coverage_statement']=C.COVERAGE['relevant_omission']
        self.assertEqual(C.resolve(base),'VALID_DESTINATION')
        base['customer_request']='For my Mug order, please refund to payment method card_a.'
        self.assertEqual(C.resolve(base),'NOT_ESTABLISHED')
        base['coverage_statement']=C.COVERAGE['irrelevant_omission']
        self.assertEqual(C.resolve(base),'VALID_DESTINATION')

    def test_payment_change_changes_determined_decision(self):
        s=copy.deepcopy(C.smokes()[0]['state'])
        s['orders'][0]['payment_history'][0]['payment_method_id']='card_b'
        self.assertEqual(C.resolve(s),'INVALID_DESTINATION')

    def test_missing_history_is_not_validated_by_coverage(self):
        s=copy.deepcopy(C.smokes()[0]['state']);s['orders'][0].pop('payment_history')
        self.assertEqual(C.resolve(s),'NOT_ESTABLISHED')

    def test_unknown_identity_and_duplicate_visible_match(self):
        s=copy.deepcopy(C.smokes()[2]['state']);s['coverage_statement']=C.COVERAGE['complete']
        extra=copy.deepcopy(s['orders'][0]);extra['order_id']='#SECOND';s['orders'].append(extra)
        self.assertEqual(C.resolve(s),'NOT_ESTABLISHED')

    def test_unknown_usage_and_unfinished_attempt_stop_resume(self):
        j={'planned_input_units':50};limits={'attempt_limit':155,'retry_limit':5,'planned_input_limit':1000}
        start={'event':'started','attempt_id':1,'retry_index':0,'planned_input_units':50}
        with self.assertRaises(RuntimeError):R.check_budget([start],j,0,limits)
        end={'event':'finished','attempt_id':1,'input_tokens':None}
        with self.assertRaises(RuntimeError):R.check_budget([start,end],j,0,limits)

    def test_limits_count_all_attempts_and_retries(self):
        j={'planned_input_units':50};limits={'attempt_limit':1,'retry_limit':0,'planned_input_limit':1000}
        events=[{'event':'started','attempt_id':1,'retry_index':0,'planned_input_units':50},
                {'event':'finished','attempt_id':1,'input_tokens':20}]
        with self.assertRaises(RuntimeError):R.check_budget(events,j,0,limits)
        limits['attempt_limit']=155
        with self.assertRaises(RuntimeError):R.check_budget(events,j,1,limits)
        limits['planned_input_limit']=99
        with self.assertRaises(RuntimeError):R.check_budget(events,j,0,limits)

    def test_three_class_mapping_is_reversed_without_label_leakage(self):
        s=C.smokes()[0]['state']
        for mapping in (0,1):
            b=C.request_body(s,mapping)
            self.assertEqual(list(b['questions']['decision']['criteria'].values()),[C.RUBRICS[x] for x in C.ORDERS[mapping]])
            self.assertNotIn('reference',b['state'])
        data={'model':C.MODEL,'usage':{'input_tokens':20},'answers':{'decision':{'type':'choice','choice':'A','probabilities':{'A':1.,'B':0.,'C':0.}}}}
        self.assertEqual(C.validate_response(data,1)['prediction'],'NOT_ESTABLISHED')

if __name__=='__main__':unittest.main()
