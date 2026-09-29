import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from data_tools import original_cases
from gap_data import policy_for
from interface import compile_visible, execute
from joint_route import aggregate, plan_queries


class JointRouteScopeTests(unittest.TestCase):
    def test_one_line_two_facts_cannot_fill_both_fields(self):
        case = {'family': 'joint_approval', 'sites': ['site-AAAAA', 'site-BBBBB'],
                'target': 'request-AAAAA'}
        policy = policy_for(case)
        state = ('Request: allow action for request request-AAAAA.\nEvidence:\n'
                 'Reviewer A approves request request-AAAAA and '
                 'Reviewer B approves request request-AAAAA.')
        schema = compile_visible(state, policy)
        a = aggregate(state, schema, {0: 'review_a:POSITIVE'})
        b = aggregate(state, schema, {0: 'review_b:POSITIVE'})
        self.assertEqual(a['facts'], {'review_a': 'TRUE', 'review_b': 'MISSING'})
        self.assertEqual(b['facts'], {'review_a': 'MISSING', 'review_b': 'TRUE'})
        self.assertEqual(execute(schema, a['facts']), 'INSUFFICIENT')
        self.assertEqual(execute(schema, b['facts']), 'INSUFFICIENT')

    def test_frozen_plan_refuses_altered_text(self):
        cases = original_cases()
        changed = [dict(case) for case in cases]
        changed[0]['state'] += '\nOne extra line.'
        with self.assertRaises(ValueError):
            plan_queries(changed)


if __name__ == '__main__':
    unittest.main()
