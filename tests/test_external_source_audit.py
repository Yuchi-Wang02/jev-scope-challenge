import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/external-validation'
sys.path.insert(0, str(HERE))
from inspect_sharc import describe


def row(utterance, tree, answer, history=None):
    return {'utterance_id': utterance, 'tree_id': tree, 'source_url': 'https://example.org',
            'snippet': 'A short conditional rule.', 'question': 'Does it apply?',
            'scenario': '', 'history': [] if history is None else history,
            'answer': answer, 'evidence': []}


class SharcSourceAuditTests(unittest.TestCase):
    def test_counts_freeform_answer_without_calling_it_insufficient(self):
        result = describe([row('a', 'tree-1', 'Yes'),
                           row('b', 'tree-1', 'What is your status?', ['prior']),
                           row('c', 'tree-2', 'Irrelevant')])
        self.assertEqual(result['rows'], 3)
        self.assertEqual(result['unique_tree_ids'], 2)
        self.assertEqual(result['trees_with_multiple_rows'], 1)
        self.assertEqual(result['other_answer_rows'], 1)
        self.assertEqual(result['nonempty_history_rows'], 1)
        self.assertEqual(result['fixed_answers'],
                         {'Yes': 1, 'No': 0, 'Irrelevant': 1})

    def test_duplicate_or_incomplete_source_row_is_rejected(self):
        with self.assertRaises(ValueError):
            describe([row('a', 'tree-1', 'Yes'), row('a', 'tree-2', 'No')])
        incomplete = row('a', 'tree-1', 'Yes')
        del incomplete['evidence']
        with self.assertRaises(ValueError):
            describe([incomplete])


if __name__ == '__main__':
    unittest.main()
