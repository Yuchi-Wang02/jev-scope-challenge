import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('extra_audit', Path(__file__).resolve().parents[1] / 'research/implementation-audit/extra_audit.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


def row(ident, answer='No', scenario='Visible'):
    return dict(utterance_id=ident, tree_id='one-tree', snippet='Rule', question='Question',
                scenario=scenario, history=[], answer=answer, evidence=[])


class ExtraAuditTests(unittest.TestCase):
    def test_pair_by_id_not_row_order_and_hidden_only_conflict(self):
        a, b = row('a'), row('b', 'Yes', 'Other')
        modified = {**a, 'answer': 'Yes', 'evidence': [{'hidden': 'Yes'}]}
        result = audit.inspect([a, b], [b, modified])
        self.assertEqual(result['unchanged_visible_conflicts'], 1)
        self.assertEqual(result['tree_units'], 1)
        self.assertEqual(result['unchanged_full_records'], 1)
        self.assertEqual(result['deterministic_source_agreement_ceiling']['numerator'], 3)

    def test_text_change_is_not_normalized_and_followups_map_to_ask(self):
        a = row('a', 'What is missing?'); b = row('a', 'Which item?', 'Visible ')
        result = audit.inspect([a], [b])
        self.assertEqual(result['visible_change_patterns'], {'scenario': 1})
        self.assertEqual(result['changed_semantic_actions'], 0)
        self.assertTrue(result['pair_records'][0]['source_answer_text_changed'])
        self.assertNotEqual(*result['pair_records'][0]['visible_sha256'])

    def test_duplicates_missing_pairs_and_tree_changes_rejected(self):
        for a, b in [([row('a'), row('a')], [row('a')]), ([row('a')], [row('b')]),
                     ([row('a')], [{**row('a'), 'tree_id': 'another-tree'}])]:
            with self.assertRaises(ValueError): audit.inspect(a, b)


if __name__ == '__main__': unittest.main()
