"""Audit the completed ownership evidence and the consequential reported contrasts."""
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/request-ownership'
SPEC = importlib.util.spec_from_file_location('completed_ownership_analysis', HERE / 'analyze.py')
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


class CompletedOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = analysis.analyze()

    def test_complete_paired_screen_and_zero_model_controls(self):
        summary = self.result['summary']
        self.assertEqual((summary['scientific_forwards'], summary['warmup_forwards']), (500, 2))
        self.assertEqual(summary['unique_scientific_input_tokens'], 188797)
        expected = {'joint_full': (2, 17, 7), 'joint_gated': (23, 47, 0),
                    'direct_full': (2, 20, 9), 'direct_filtered': (2, 21, 10),
                    'single_full': (3, 21, 9), 'single_filtered': (3, 22, 10),
                    'known_grammar': (24, 48, 0), 'always_defer': (0, 12, 0)}
        for method, counts in expected.items():
            row = summary['methods'][method]
            self.assertEqual((row['complete_pairs_correct'], row['correct_decisions'], row['false_commitments']), counts)
            self.assertEqual((row['parent_pairs'], row['views'], row['uncertain_views']), (24, 48, 12))
        self.assertTrue(summary['directional_diagnostic']['passed'])
        self.assertFalse(summary['directional_diagnostic']['confirmation'])

    def test_gate_preserves_residual_field_error_and_all_action_transitions(self):
        changes = [r for r in self.result['case_changes']
                   if r['candidate'] == 'joint_gated' and r['baseline'] == 'joint_full']
        self.assertEqual(len(changes), 30)
        self.assertTrue(all(r['transition'] == 'correction' for r in changes))
        failed = [r for r in self.result['decisions'] if r['method'] == 'joint_gated' and not r['correct']]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]['view_id'], 'ownership-route_lookup-01/target-1')
        self.assertEqual((failed[0]['prediction'], failed[0]['gold']), ('INSUFFICIENT', 'DENY'))
        routes = [r for r in self.result['line_audits'] if r['method'] == 'joint_gated' and r['program_audit'] != 'correct_route']
        self.assertEqual(len(routes), 1)
        self.assertEqual((routes[0]['gate']['status'], routes[0]['program_audit']), ('KEEP', 'wrong_field'))
        self.assertEqual(routes[0]['evidence_span']['text'], 'Route for request request-RGGPM: site-GHCQC.')

    def test_direct_filter_regressions_are_not_hidden_by_small_net_gain(self):
        compared, changed = analysis.compare(
            [r for r in self.result['decisions'] if r['method'] == 'direct_filtered'],
            [r for r in self.result['decisions'] if r['method'] == 'direct_full'])
        self.assertEqual(compared['view_transitions']['correction'], 4)
        self.assertEqual(compared['view_transitions']['regression'], 3)
        self.assertEqual((compared['complete_pair_gains'], compared['complete_pair_losses']), (2, 2))
        self.assertEqual(sum(r['transition'] == 'regression' for r in changed), 3)

    def test_saved_gate_cost_is_not_replaced_by_projected_prefilter_cost(self):
        costs = self.result['summary']['joint_gated_cost']
        self.assertEqual((costs['underlying_saved_forwards'], costs['underlying_saved_input_tokens']), (200, 85214))
        self.assertEqual((costs['projected_retained_forwards'], costs['projected_retained_input_tokens']), (100, 42627))
        self.assertFalse(costs['projected_latency_measured'])
        self.assertFalse(costs['new_skipped_inference_run'])


if __name__ == '__main__':
    unittest.main()
