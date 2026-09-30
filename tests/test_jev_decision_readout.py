import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/source-label-screen'))
from decision_readout import adapt

OPTIONS = ['ASK', 'Irrelevant', 'No', 'Yes']


def response():
    return {'model': 'jev-1.13.0', 'usage': {'input_tokens': 618, 'output_tokens': 45},
        'answers': {'decision': {'type': 'choice', 'choice': 'A', 'confidence': .91,
            'probabilities': {'D': .01, 'C': .05, 'A': .93, 'B': 0.0}}}}


class JevDecisionReadoutTests(unittest.TestCase):
    def test_native_choice_survives_nonunit_sum_without_normalization(self):
        raw = response(); original = copy.deepcopy(raw)
        result = adapt(raw, 200, OPTIONS, .14)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['action'], 'ASK')
        self.assertFalse(result['detail']['probability_quality']['within_original_sum_tolerance'])
        self.assertFalse(result['detail']['probability_quality']['normalization_applied'])
        self.assertEqual(result['detail']['parsed']['probabilities']['ASK'], .93)
        self.assertEqual(raw, original)

    def test_quality_flag_is_not_a_rounding_exception_or_calibration_claim(self):
        raw = response()
        raw['answers']['decision']['probabilities'] = {k: .1 for k in 'ABCD'}
        result = adapt(raw, 200, OPTIONS, .1)
        self.assertEqual(result['status'], 'ok')
        self.assertAlmostEqual(result['detail']['probability_quality']['raw_sum'], .4)
        self.assertFalse(result['detail']['probability_quality']['calibration_quality_established'])
        raw['answers']['decision']['probabilities']['A'] = .7
        result = adapt(raw, 200, OPTIONS, .1)
        self.assertTrue(result['detail']['probability_quality']['within_original_sum_tolerance'])

    def test_invalid_values_and_nonargmax_choice_still_halt(self):
        for value in (float('nan'), float('inf'), -.1, 1.1, True):
            raw = response(); raw['answers']['decision']['probabilities']['A'] = value
            self.assertEqual(adapt(raw, 200, OPTIONS, .1)['status'], 'protocol_error')
        raw = response(); raw['answers']['decision']['choice'] = 'C'
        self.assertIsNone(adapt(raw, 200, OPTIONS, .1)['action'])
        raw['answers']['decision']['probabilities'] = {k: 0 for k in 'ABCD'}
        self.assertEqual(adapt(raw, 200, OPTIONS, .1)['status'], 'protocol_error')

    def test_http_schema_model_and_usage_failures_remain_distinct_from_valid_choice(self):
        raw = response()
        bad = adapt(raw, 500, OPTIONS, .1)
        self.assertEqual(bad['status'], 'protocol_error')
        self.assertEqual(bad['input_tokens'], 618)
        for field in ('model', 'usage', 'answers'):
            raw = response(); raw.pop(field)
            self.assertEqual(adapt(raw, 200, OPTIONS, .1)['status'], 'protocol_error')
        raw = response(); raw['answers']['decision']['probabilities'].pop('B')
        self.assertEqual(adapt(raw, 200, OPTIONS, .1)['status'], 'protocol_error')


if __name__ == '__main__':
    unittest.main()
