import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/source-label-screen'))
import screen
from source_inventory import eligible_rows


def data():
    rows = []
    for group, answers in [('same', ('Yes', 'Yes')), ('ask', ('No', 'Need more?')),
                           ('decisive', ('No', 'Yes'))]:
        for n in range(2):
            for i, history_answer in enumerate(('No', 'Yes')):
                tree = group + str(n)
                rows.append({'tree_id': tree, 'utterance_id': tree + str(i),
                    'snippet': 'Rule ' + tree, 'question': 'Am I eligible?', 'scenario': '',
                    'history': [{'follow_up_question': 'A?', 'follow_up_answer': history_answer}],
                    'answer': answers[i], 'evidence': 'MUST_NOT_REACH_MODEL', 'source_url': 'synthetic'})
    return rows


def render(prompt, thinking, cap):
    return 'synthetic:' + prompt, [1, 2, 3]


class SourceLabelScreenTests(unittest.TestCase):
    def test_deterministic_distinct_tree_selection_is_input_order_independent(self):
        rows = data()
        chosen = screen.choose([], rows, per_group=1)
        self.assertEqual(chosen, screen.choose([], list(reversed(rows)), per_group=1))
        self.assertEqual([c['group'] for c in chosen], list(screen.GROUPS))
        self.assertEqual(len({c['tree_id'] for c in chosen}), 3)
        with self.assertRaisesRegex(ValueError, 'Insufficient'):
            screen.choose([], rows, per_group=3)

    def test_overlap_excludes_entire_tree_even_when_another_row_has_other_text(self):
        train = [{'tree_id': 'train_tree', 'snippet': 'Same Rule'}]
        dev = [{'tree_id': 'shared', 'snippet': ' SAME   rule '},
               {'tree_id': 'shared', 'snippet': 'Different text'},
               {'tree_id': 'train_tree', 'snippet': 'Another text'},
               {'tree_id': 'safe', 'snippet': 'Unrelated rule'}]
        self.assertEqual(eligible_rows(train, dev), [dev[-1]])

    def test_conflicting_visible_labels_and_duplicate_rules_cannot_add_units(self):
        rows = data()
        conflict = copy.deepcopy(rows[0]); conflict['utterance_id'] = 'conflict'; conflict['answer'] = 'No'
        chosen = screen.choose([], rows + [conflict], per_group=1)
        self.assertNotIn('same0', {c['tree_id'] for c in chosen})
        rows[2]['snippet'] = rows[3]['snippet'] = rows[0]['snippet']
        with self.assertRaisesRegex(ValueError, 'Insufficient'):
            screen.choose([], rows, per_group=2)

    def test_labels_and_hidden_evidence_stay_outside_requests(self):
        selected = screen.choose([], data(), per_group=1)
        plan, refs = screen.assemble(selected, render)
        self.assertEqual(len(plan['jobs']), 36)
        for job in plan['jobs']:
            self.assertNotIn('MUST_NOT_REACH_MODEL', str(job))
            if job['backend'] == 'jev':
                self.assertEqual(set(job['request']['state']), {'snippet', 'question', 'scenario', 'history'})
        changed = copy.deepcopy(selected)
        changed[0]['rows'][0]['answer'] = 'Irrelevant'
        another, other_refs = screen.assemble(changed, render)
        self.assertEqual(plan, another)
        self.assertNotEqual(refs, other_refs)

    def test_context_overflow_and_missing_freeze_fail_without_inference(self):
        selected = screen.choose([], data(), per_group=1)
        with self.assertRaisesRegex(ValueError, 'Context'):
            screen.assemble(selected, lambda *args: ('too long', [1] * 32768))
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(screen, 'HERE', Path(directory)):
                with self.assertRaisesRegex(ValueError, 'freeze missing'):
                    screen.check_freeze()


if __name__ == '__main__':
    unittest.main()
