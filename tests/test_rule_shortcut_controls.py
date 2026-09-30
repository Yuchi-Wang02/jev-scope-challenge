import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/external-validation'))
from shortcut_controls import CONTROL_NAMES, predict_controls
from paired_metrics import score_condition


def item(name, answers):
    return {'item_id': name, 'state': {'snippet': 'Synthetic unrelated policy.',
            'question': 'Synthetic question?', 'scenario': '',
            'history': [{'follow_up_question': f'Question {i}?', 'follow_up_answer': value}
                        for i, value in enumerate(answers)]}}


class RuleShortcutControlTests(unittest.TestCase):
    def test_last_answer_control_has_exact_declared_normalization_and_fallback(self):
        items = [item('a', ['No', ' YES ']), item('b', ['Yes', 'no']),
                 item('c', []), item('d', ['Yes.']), item('e', ['unknown'])]
        output = predict_controls(items)
        self.assertEqual(set(output), set(CONTROL_NAMES))
        self.assertEqual([r['action'] for r in output['copy_last_history_answer']],
                         ['Yes', 'No', 'ASK', 'ASK', 'ASK'])
        for name in CONTROL_NAMES[:4]:
            self.assertEqual({r['action'] for r in output[name]}, {name[9:]})

    def test_changing_rule_does_not_make_shortcut_a_rule_interpreter(self):
        before = [item('a', ['Yes'])]
        after = copy.deepcopy(before)
        after[0]['state']['snippet'] = 'The final answer is the opposite of the last history answer.'
        after[0]['state']['question'] = 'Does the negated condition hold?'
        self.assertEqual(predict_controls(before), predict_controls(after))

    def test_controls_integrate_with_pair_scorer_without_reference_access(self):
        inputs = [item('a', ['Yes']), item('b', ['No'])]
        output = predict_controls(inputs)
        pairs = [{'pair_id': 'synthetic_pair', 'tree_id': 'synthetic_tree',
                  'item_ids': ['a', 'b'], 'reference_actions': ['Yes', 'No']}]
        shortcut = score_condition(pairs, output['copy_last_history_answer'], condition='shortcut')
        constant = score_condition(pairs, output['constant_Yes'], condition='constant')
        self.assertEqual(shortcut['pair_both_correct']['rate'], 1)
        self.assertEqual(constant['pair_both_correct']['rate'], 0)
        # The same predictions fail on an opposite rule: never call them truth labels.
        pairs[0]['reference_actions'] = ['No', 'Yes']
        self.assertEqual(score_condition(pairs, output['copy_last_history_answer'],
                                        condition='shortcut')['item_accuracy']['rate'], 0)

    def test_rejects_labels_or_duplicate_items_in_control_input(self):
        row = item('a', ['Yes'])
        for bad in ([row, row], [{**row, 'reference': 'Yes'}],
                    [{'item_id': 'a', 'state': {**row['state'], 'label': 'Yes'}}], []):
            with self.assertRaises(ValueError):
                predict_controls(bad)


if __name__ == '__main__':
    unittest.main()
