import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/external-validation'))
from analyze_comparison import analyze
from comparison_plan import material
from comparison_backends import adapt_jev
from test_sharc_comparison_plan import fixtures, renderer


def setup_grid():
    selected, pack, final = fixtures()
    final['selected'] = final['selected'][:2]
    plan, refs = material(pack, selected, final, renderer)
    labels = {i: a for p in refs for i, a in zip(p['item_ids'], p['reference_actions'])}
    journals = {}
    for backend in ('jev', 'qwen'):
        jobs = [j for j in plan['jobs'] if j['backend'] == backend]
        events = [{'event': 'header', 'version': 1, 'plan_sha256': 'synthetic_hash',
                   'backend': backend, 'job_ids': [j['id'] for j in jobs]},
                  {'event': 'session_start', 'session': 0, 'backend_metadata': {'synthetic': True}}]
        for job in jobs:
            action = labels[job['item_id']]
            if backend == 'jev':
                key = 'ABCD'[job['options'].index(action)]
                raw = {'model': 'jev-1.13.0', 'usage': {'input_tokens': 10, 'output_tokens': 3},
                       'answers': {'decision': {'type': 'choice', 'choice': key, 'confidence': .7,
                        'probabilities': {k: .7 if k == key else .1 for k in 'ABCD'}}}}
                result = adapt_jev(raw, 200, job['options'], .1)
            else:
                result = {'status': 'ok', 'action': action, 'input_tokens': len(job['input_ids']),
                          'output_tokens': 1, 'latency_seconds': .1,
                          'detail': {'output_ids': [100 if action == 'Yes' else 101]}}
            events += [{'event': 'call_start', 'job_id': job['id']},
                       {'event': 'call_finish', 'job_id': job['id'], 'result': result}]
        events.append({'event': 'session_end', 'session': 0, 'elapsed_seconds': 2})
        journals[backend] = [{**event, 'seq': i} for i, event in enumerate(events)]
    return plan, refs, journals


def synthetic_token_checker(job, result):
    # Not a tokenizer or model result: the real CLI requires a pinned tokenizer.
    action = {100: 'Yes', 101: 'No', 102: None}[result['detail']['output_ids'][0]]
    return {'action': action, 'strict_json': action is not None, 'completion': 'synthetic'}


class RuleComparisonAnalysisTests(unittest.TestCase):
    def run_grid(self, plan, refs, journals):
        return analyze(plan, refs, journals, 'synthetic_hash', qwen_checker=synthetic_token_checker)

    def test_complete_grid_preserves_all_conditions_controls_and_resources(self):
        plan, refs, journals = setup_grid()
        report = self.run_grid(plan, refs, journals)
        self.assertEqual(report['status'], 'complete_grid')
        self.assertTrue(report['complete_grid_within_recorded_budgets'])
        self.assertTrue(report['complete_grid_without_execution_or_protocol_errors'])
        self.assertEqual(len(report['conditions']), 6)
        self.assertEqual(len(report['controls']), 5)
        self.assertEqual(report['tree_units'], 2)
        self.assertTrue(all(c['metric']['pair_both_correct']['rate'] == 1
                            for c in report['conditions'].values()))
        self.assertEqual(report['resources']['jev']['known_input_tokens'], 80)
        self.assertEqual(report['resources']['qwen']['known_input_tokens'], 48)
        self.assertEqual(report['order_effects']['jev']['changed_valid_action'], 0)

    def test_partial_grid_has_no_full_condition_score_or_order_claim(self):
        plan, refs, journals = setup_grid()
        journals['qwen'] = journals['qwen'][:4]  # One finished callback; session still open.
        report = self.run_grid(plan, refs, journals)
        self.assertEqual(report['status'], 'incomplete_grid')
        self.assertFalse(report['complete_grid_within_recorded_budgets'])
        self.assertTrue(report['resources']['qwen']['session_time_incomplete'])
        for name, condition in report['conditions'].items():
            if name.startswith('qwen'):
                self.assertIsNone(condition['metric'])
                self.assertFalse(condition['grid_complete'])
        self.assertFalse(report['order_effects']['qwen_direct']['available'])

    def test_unknown_started_request_does_not_become_zero_usage_or_a_prediction(self):
        plan, refs, journals = setup_grid()
        journals['jev'] = journals['jev'][:3]  # Started; outcome unknown.
        report = self.run_grid(plan, refs, journals)
        self.assertTrue(report['resources']['jev']['usage_incomplete'])
        self.assertEqual(report['resources']['jev']['unresolved_attempts'], 1)
        self.assertTrue(all(c['metric'] is None for n, c in report['conditions'].items() if n.startswith('jev')))

    def test_invalid_local_answer_keeps_denominator_and_is_not_an_order_change(self):
        plan, refs, journals = setup_grid()
        event = next(e for e in journals['qwen'] if e['event'] == 'call_finish')
        event['result']['action'] = None
        event['result']['detail']['output_ids'] = [102]
        job = next(j for j in plan['jobs'] if j['id'] == event['job_id'])
        report = self.run_grid(plan, refs, journals)
        metric = report['conditions'][job['condition']]['metric']
        self.assertEqual(metric['invalid_output']['numerator'], 1)
        self.assertEqual(metric['item_accuracy']['denominator'], 4)
        model = 'qwen_thinking' if job['thinking'] else 'qwen_direct'
        self.assertEqual(report['order_effects'][model]['invalid_in_either'], 1)
        self.assertEqual(report['order_effects'][model]['changed_valid_action'], 0)

    def test_stored_action_tampering_is_rejected_for_both_backends(self):
        for backend in ('jev', 'qwen'):
            plan, refs, journals = setup_grid()
            event = next(e for e in journals[backend] if e['event'] == 'call_finish')
            event['result']['action'] = 'ASK'
            with self.assertRaises(ValueError):
                self.run_grid(plan, refs, journals)

    def test_foreign_or_missing_cohort_and_visible_input_drift_are_rejected(self):
        plan, refs, journals = setup_grid()
        bad = copy.deepcopy(plan)
        bad['jobs'].pop()
        with self.assertRaises(ValueError):
            self.run_grid(bad, refs, journals)
        bad = copy.deepcopy(plan)
        job = next(j for j in bad['jobs'] if j['backend'] == 'qwen')
        job['prompt'] += ' Extra help not shared with Jev.'
        with self.assertRaisesRegex(ValueError, 'common task'):
            self.run_grid(bad, refs, journals)

    def test_returned_local_tokens_require_a_checker_and_overruns_remain_visible(self):
        plan, refs, journals = setup_grid()
        with self.assertRaisesRegex(ValueError, 'tokenizer audit'):
            analyze(plan, refs, journals, 'synthetic_hash')
        plan['limits']['jev_actual_input_tokens'] = 79
        report = self.run_grid(plan, refs, journals)
        self.assertEqual(report['status'], 'complete_grid')
        self.assertFalse(report['complete_grid_within_recorded_budgets'])
        self.assertEqual(report['resources']['jev']['overruns']['input_tokens'], 1)

    def test_final_protocol_error_is_distinct_from_grid_and_budget_completion(self):
        plan, refs, journals = setup_grid()
        event = [e for e in journals['jev'] if e['event'] == 'call_finish'][-1]
        raw = copy.deepcopy(event['result']['detail']['raw_response'])
        raw['model'] = 'unexpected-model'
        job = next(j for j in plan['jobs'] if j['id'] == event['job_id'])
        event['result'] = adapt_jev(raw, 200, job['options'], .1)
        report = self.run_grid(plan, refs, journals)
        self.assertEqual(report['status'], 'complete_grid')
        self.assertTrue(report['complete_grid_within_recorded_budgets'])
        self.assertFalse(report['complete_grid_without_execution_or_protocol_errors'])
        self.assertEqual(report['resources']['jev']['result_status_counts']['protocol_error'], 1)
        self.assertEqual(report['conditions'][job['condition']]['metric']['invalid_output']['numerator'], 1)


if __name__ == '__main__':
    unittest.main()
