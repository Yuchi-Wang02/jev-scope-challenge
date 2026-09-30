import copy
import importlib.util
import itertools
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('qa4pc_audit', Path(__file__).resolve().parents[1] / 'research/qa4pc-audit/audit.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


def fixture():
    trees = [dict(tree_id='t', question='Eligible?', logic='Q0 AND NOT Q1', difficult=False,
                  questions={'Q0': 'A?', 'Q1': 'B?'}, policy='Policy')]
    ent = [dict(tree_id='t', utterance_id='u', question='Eligible?', policy='Policy', scenario='State', answer='yes')]
    qa = [dict(tree_id='t', utterance_id='u', scenario='State', question=q, question_id=i, set_id=i, answer=a)
          for i, q, a in [('Q0', 'A?', 'yes'), ('Q1', 'B?', 'no')]]
    return trees, ent, qa


class QA4PCAuditTests(unittest.TestCase):
    def test_kleene_truth_tables_and_precedence(self):
        labels = ['no', 'maybe', 'yes']
        and_table = [['no', 'no', 'no'], ['no', 'maybe', 'maybe'], ['no', 'maybe', 'yes']]
        or_table = [['no', 'maybe', 'yes'], ['maybe', 'maybe', 'yes'], ['yes', 'yes', 'yes']]
        for i, j in itertools.product(range(3), repeat=2):
            facts = {'Q0': labels[i], 'Q1': labels[j]}
            self.assertEqual(audit.execute(audit.parse_logic('Q0 AND Q1'), facts), and_table[i][j])
            self.assertEqual(audit.execute(audit.parse_logic('Q0 or Q1'), facts), or_table[i][j])
        for value, expected in [('yes', 'no'), ('no', 'yes'), ('maybe', 'maybe')]:
            self.assertEqual(audit.execute(audit.parse_logic('NOT Q0'), {'Q0': value}), expected)
        self.assertEqual(audit.execute(audit.parse_logic('Q0 OR Q1 AND NOT Q2'), {'Q0': 'yes', 'Q1': 'no', 'Q2': 'yes'}), 'yes')

    def test_reject_code_and_missing_variables_even_if_short_circuited(self):
        for text in ['__import__("os")', 'Q0 == Q1', 'True', 'Q0[0]', 'Q0 + Q1', 'X', 'Q0 and']:
            with self.assertRaises(ValueError): audit.parse_logic(text)
        with self.assertRaises(ValueError): audit.execute(audit.parse_logic('Q0 AND Q1'), {'Q0': 'no'})
        with self.assertRaises(ValueError): audit.execute(audit.parse_logic('Q0'), {'Q0': 'unknown'})

    def test_exact_joins_and_order_invariance(self):
        t, e, q = fixture()
        report = audit.inspect(t, e, q)
        self.assertEqual(report, audit.inspect(t, e, list(reversed(q))))
        self.assertEqual(report['evaluable_scenarios'], 1)
        self.assertEqual(report['composition_mismatches'], [])
        self.assertEqual(report['evaluable_released_label_counts'], {'yes': 1})

    def test_incomplete_formula_retained_not_repaired(self):
        t, e, q = fixture(); del t[0]['questions']['Q1']; q = q[:1]
        report = audit.inspect(t, e, q)
        self.assertEqual(report['evaluable_scenarios'], 0)
        self.assertEqual(report['graph_inventory_issues'][0]['missing_variables'], ['Q1'])
        self.assertEqual(len(report['unavailable_scenarios']), 1)

    def test_mismatch_and_same_visible_conflict_reported(self):
        t, e, q = fixture(); e.append({**e[0], 'utterance_id': 'u2', 'answer': 'no'})
        q += [{**r, 'utterance_id': 'u2', 'set_id': r['set_id'] + '-2'} for r in q]
        result = audit.inspect(t, e, q)
        self.assertEqual(len(result['composition_mismatches']), 1)
        self.assertEqual(len(result['direct_visible_label_conflicts']), 1)
        self.assertEqual(result['distinct_direct_visible_inputs'], 1)

    def test_invalid_joins_and_schema_rejected(self):
        mutations = [lambda t,e,q: q.append(copy.deepcopy(q[0])),
                     lambda t,e,q: q.pop(),
                     lambda t,e,q: q[0].update(scenario='State '),
                     lambda t,e,q: e[0].update(policy='Changed'),
                     lambda t,e,q: q[0].update(answer='unknown'),
                     lambda t,e,q: t[0].update(extra='unexpected'),
                     lambda t,e,q: q[0].update(utterance_id='orphan')]
        for mutate in mutations:
            t,e,q = fixture(); mutate(t,e,q)
            with self.assertRaises(ValueError): audit.inspect(t,e,q)


if __name__ == '__main__': unittest.main()
