import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/source-label-screen'))
from decision_readout import adapt
from native_choice import adapt as native

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


class NativeChoiceTests(unittest.TestCase):
    def test_native_and_displayed_argmax_are_both_retained_not_substituted(self):
        raw = response()
        raw['answers']['decision'].update(choice='C', confidence=.19,
            probabilities={'C': .38, 'B': .39, 'A': .01, 'D': .22})
        result = native(raw, 200, ['Yes', 'No', 'Irrelevant', 'ASK'], .1)
        self.assertEqual(result['action'], 'Irrelevant')
        quality = result['detail']['metadata_quality']
        self.assertEqual(quality['unique_argmax_action'], 'No')
        self.assertFalse(quality['choice_is_displayed_argmax'])
        self.assertFalse(quality['all_original_metadata_checks_pass'])

    def test_invalid_or_tied_metadata_is_not_a_unique_argmax(self):
        for probs in (None, {'A': float('nan')}, {k: 0 for k in 'ABCD'}, {k: .25 for k in 'ABCD'}):
            raw = response(); raw['answers']['decision']['probabilities'] = probs
            result = native(raw, 200, OPTIONS, .1)
            self.assertEqual(result['action'], 'ASK')
            self.assertIsNone(result['detail']['metadata_quality']['unique_argmax_action'])

    def test_probability_metadata_failure_does_not_validate_the_contract(self):
        raw = response(); raw['answers']['decision'].pop('confidence')
        result = native(raw, 200, OPTIONS, .1)
        self.assertEqual(result['status'], 'ok')
        self.assertFalse(result['detail']['metadata_quality']['confidence_valid'])
        self.assertFalse(result['detail']['metadata_quality']['all_original_metadata_checks_pass'])

    def test_core_action_and_usage_failures_still_stop(self):
        for choice in ('', 'AB', 'E', None):
            raw = response(); raw['answers']['decision']['choice'] = choice
            self.assertEqual(native(raw, 200, OPTIONS, .1)['status'], 'protocol_error')
        raw = response(); raw.pop('usage')
        self.assertIsNone(native(raw, 200, OPTIONS, .1)['action'])

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
