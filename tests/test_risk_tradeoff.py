"""Scientific cost claims and visible-input-only controls, without inference."""
import unittest
from fractions import Fraction

from docs.build_risk_tradeoff import data, derived_records, lower_envelope


class RiskTradeoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = data()

    def test_line_never_wins_needless_cost_after_adding_constant_control(self):
        methods = self.payload['methods']
        envelope = self.payload['exact_envelopes_without_grammar']['needless_deferrals']
        self.assertEqual([s['winners'] for s in envelope['intervals']],
                         [['direct'], ['facts'], ['defer']])
        # Exact proof over the full nonnegative half-line, not a slider grid:
        # line - facts = 29 - 14r >= 1 for r <= 2;
        # line - defer = 6r - 11 >= 1 for r >= 2.
        line, facts, defer = [methods[k] for k in ('line', 'facts', 'defer')]
        self.assertLess(line['wrong_actions'] - facts['wrong_actions'], 0)
        self.assertEqual((line['wrong_actions'] - facts['wrong_actions']) * 2 +
                         line['needless_deferrals'] - facts['needless_deferrals'], 1)
        self.assertGreater(line['wrong_actions'] - defer['wrong_actions'], 0)
        self.assertEqual((line['wrong_actions'] - defer['wrong_actions']) * 2 +
                         line['needless_deferrals'] - defer['needless_deferrals'], 1)

    def test_all_deferral_interval_has_exact_endpoint_checks(self):
        envelope = self.payload['exact_envelopes_without_grammar']['all_deferrals']
        intervals = [s for s in envelope['intervals'] if s['winners'] == ['line']]
        self.assertEqual([(s['start'], s['end']) for s in intervals],
                         [('37/14', '17/6')])
        self.assertIn({'ratio': '37/14', 'winners': ['facts', 'line']},
                      envelope['boundaries'])
        self.assertIn({'ratio': '17/6', 'winners': ['line', 'defer']},
                      envelope['boundaries'])
        # Check the lines themselves at both boundaries, independently of the
        # interval search. The tailored grammar control beats all four there.
        for ratio in (Fraction(37, 14), Fraction(17, 6)):
            losses = {name: row['wrong_actions'] * ratio + row['all_deferrals']
                      for name, row in self.payload['methods'].items()}
            generic = {name: loss for name, loss in losses.items() if name != 'grammar'}
            self.assertEqual(losses['line'], min(generic.values()))
            self.assertLess(losses['grammar'], losses['line'])

    def test_cost_controls_are_derived_and_do_not_claim_cpu_measurement(self):
        for name, correct, all_deferrals in (('defer', 24, 72), ('grammar', 72, 24)):
            row = self.payload['methods'][name]
            self.assertEqual(row['kind'], 'derived_baseline')
            self.assertEqual((row['calls'], row['input_tokens']), (0, 0))
            self.assertIsNone(row['forward_seconds'])
            self.assertEqual((row['correct'], row['all_deferrals']),
                             (correct, all_deferrals))
        self.assertEqual(self.payload['new_model_forwards'], 0)

    def test_runtime_predictor_gets_visible_strings_not_gold_or_metadata(self):
        seen = []

        def predictor(state, policy):
            seen.append((state, policy))
            return 'ALLOW'

        cases = [{'id': 'a', 'parent': 'private-parent', 'family': 'family',
                  'variant': 'variant', 'state': 'visible state',
                  'instruction': 'visible policy', 'gold': 'DENY'},
                 {'id': 'b', 'parent': 'different-parent', 'family': 'family',
                  'variant': 'variant', 'state': 'visible state',
                  'instruction': 'visible policy', 'gold': 'ALLOW'}]
        records = derived_records(cases, predictor)
        self.assertEqual(seen, [('visible state', 'visible policy')] * 2)
        self.assertEqual(records['a']['prediction'], records['b']['prediction'])
        self.assertFalse(records['a']['correct'])
        self.assertTrue(records['b']['correct'])

    def test_nonwinning_intersections_and_parallel_curves_do_not_split_optimum(self):
        curves = {'falling_relative': {'wrong_actions': 0, 'cost': 6},
                  'rising': {'wrong_actions': 2, 'cost': 0},
                  'duplicate': {'wrong_actions': 2, 'cost': 0},
                  'dominated': {'wrong_actions': 2, 'cost': 1}}
        envelope = lower_envelope(curves, 'cost')
        self.assertEqual(envelope['intervals'], [
            {'start': '0', 'end': '3', 'winners': ['rising', 'duplicate']},
            {'start': '3', 'end': None, 'winners': ['falling_relative']}])
        self.assertEqual(envelope['boundaries'][-1],
                         {'ratio': '3', 'winners': ['falling_relative', 'rising', 'duplicate']})

    def test_zero_endpoint_ties_are_not_lost(self):
        envelope = lower_envelope({'a': {'wrong_actions': 1, 'cost': 0},
                                   'b': {'wrong_actions': 2, 'cost': 0}}, 'cost')
        self.assertEqual(envelope['boundaries'][0],
                         {'ratio': '0', 'winners': ['a', 'b']})
        self.assertEqual(envelope['intervals'],
                         [{'start': '0', 'end': None, 'winners': ['a']}])

    def test_loss_counts_reject_negative_fractional_and_boolean_values(self):
        for count in (-1, 0.5, True):
            with self.subTest(count=count), self.assertRaises(ValueError):
                lower_envelope({'a': {'wrong_actions': count, 'cost': 1}}, 'cost')
        with self.assertRaises(ValueError):
            lower_envelope({}, 'cost')


if __name__ == '__main__':
    unittest.main()
