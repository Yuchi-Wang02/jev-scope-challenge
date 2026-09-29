import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from line_oracle_decomposition import compute, relation


class LineOracleDecompositionTests(unittest.TestCase):
    def test_priority_distinguishes_request_field_and_polarity(self):
        case = {'target': 'request-A', 'records': [
            {'scope': 'request-B', 'field': 'review_b', 'value': False},
            {'scope': 'request-A', 'field': 'review_b', 'value': False},
            {'scope': 'request-A', 'field': 'review_a', 'value': False}]}
        self.assertEqual(relation({'line_index': 0, 'prediction': 'NEGATIVE'},
                                  case, 'review_a'), ('wrong_request', 'IRRELEVANT'))
        self.assertEqual(relation({'line_index': 1, 'prediction': 'NEGATIVE'},
                                  case, 'review_a'), ('wrong_field', 'IRRELEVANT'))
        self.assertEqual(relation({'line_index': 2, 'prediction': 'POSITIVE'},
                                  case, 'review_a'), ('wrong_polarity', 'NEGATIVE'))
        self.assertEqual(relation({'line_index': 2, 'prediction': 'IRRELEVANT'},
                                  case, 'review_a'), ('missed_relevant', 'NEGATIVE'))

    def test_saved_pilot_and_oracle_interactions(self):
        result = compute()
        rows = {tuple(row['replaced_categories']): row for row in result['counterfactuals']}
        self.assertEqual(len(rows), 16)
        self.assertEqual(result['new_model_forwards'], 0)
        self.assertEqual([result['error_categories'][k]['line_judgments'] for k in
                          ('wrong_request', 'wrong_field', 'wrong_polarity', 'missed_relevant')],
                         [73, 172, 4, 0])
        self.assertEqual((rows[()]['correct_decisions'], rows[()]['correct_fields']), (29, 60))
        binding = rows[('wrong_request', 'wrong_field')]
        self.assertEqual((binding['correct_decisions'], binding['false_commitments'],
                          binding['determined_correct'], binding['baseline_correct_regressed']),
                         (68, 1, 45, 1))
        self.assertEqual(rows[('wrong_field',)]['baseline_correct_regressed'], 4)
        self.assertEqual((rows[tuple(result['category_priority'])]['correct_decisions'],
                          rows[tuple(result['category_priority'])]['correct_fields']),
                         (72, 168))


if __name__ == '__main__':
    unittest.main()
