import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/external-validation'
sys.path.insert(0, str(HERE))
from inspect_sharc_pairs import action, one_answer_difference


def item(answer='Yes', question='Can I apply?', scenario='Same scenario',
         history_answers=('Yes', 'No')):
    return {'tree_id': 'tree', 'snippet': 'One fixed rule.', 'question': question,
            'scenario': scenario, 'answer': answer,
            'history': [{'follow_up_question': f'Condition {i}?',
                         'follow_up_answer': value}
                        for i, value in enumerate(history_answers)]}


class SharcPairTests(unittest.TestCase):
    def test_one_history_answer_flip_keeps_other_visible_text_fixed(self):
        base = item()
        flipped = item(answer='No', history_answers=('Yes', 'Yes'))
        self.assertEqual(one_answer_difference(base, flipped), ('No', 'Yes'))
        self.assertIsNone(one_answer_difference(base, item(question='Different?',
                                                       history_answers=('Yes', 'Yes'))))
        self.assertIsNone(one_answer_difference(base, item(scenario='Different',
                                                       history_answers=('Yes', 'Yes'))))
        self.assertIsNone(one_answer_difference(base, item(history_answers=('No', 'Yes'))))
        self.assertIsNone(one_answer_difference(base, item(history_answers=('No',))))
        self.assertIsNone(one_answer_difference(base, item(history_answers=('Yes', 'Maybe'))))

    def test_freeform_answer_is_only_provisional_ask(self):
        self.assertEqual(action(item(answer='Do you meet the condition?')), 'ASK')
        self.assertEqual(action(item(answer='Irrelevant')), 'Irrelevant')
        with self.assertRaises(ValueError):
            action(item(answer=''))


if __name__ == '__main__':
    unittest.main()
