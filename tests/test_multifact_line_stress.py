import sys
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from data_tools import original_cases
from multifact_line_stress import artifacts, build, pack


class MultiFactLineStressTests(unittest.TestCase):
    def test_published_data_recomputes_exactly(self):
        for path, payload in artifacts():
            self.assertEqual(path.read_bytes().replace(b'\r\n', b'\n'),
                             payload.encode('utf-8'))

    def test_paired_interface_limit_and_control(self):
        rows, summary = build()
        self.assertEqual((len(rows), summary['parent_clusters']), (112, 12))
        self.assertEqual(Counter(r['packing'] for r in rows),
                         {'cross_field': 56, 'mixed_scope_control': 56})
        self.assertEqual(summary['by_packing']['cross_field'],
                         {'items': 56, 'exact_fact_vector_reachable': 0,
                          'gold_decision_reachable': 30})
        self.assertEqual(summary['by_packing']['mixed_scope_control'],
                         {'items': 56, 'exact_fact_vector_reachable': 56,
                          'gold_decision_reachable': 56})
        for source in {r['source_id'] for r in rows}:
            pair = [r for r in rows if r['source_id'] == source]
            self.assertEqual({r['packing'] for r in pair},
                             {'cross_field', 'mixed_scope_control'})
            self.assertEqual(len({r['program_gold'] for r in pair}), 1)
            self.assertTrue(all(r['model_scored'] is False and
                                r['independent_human_reviewed'] is False
                                for r in pair))

    def test_concrete_allow_case_and_source_alignment(self):
        rows, _ = build()
        cross = next(r for r in rows if r['stress_id'] ==
                     'joint_approval-1-full/cross_field')
        control = next(r for r in rows if r['stress_id'] ==
                       'joint_approval-1-full/mixed_scope_control')
        self.assertEqual(cross['program_gold'], 'ALLOW')
        self.assertEqual(cross['faithful_possible_decisions'], ['INSUFFICIENT'])
        self.assertEqual(control['faithful_gold_decision_reachable'], True)
        self.assertIn('Reviewer A approves request request-GZYYS. '
                      'Reviewer B approves request request-GZYYS.', cross['state'])
        case = next(c for c in original_cases() if c['id'] == 'joint_approval-1-full')
        changed = dict(case, state=case['state'].replace('Reviewer A approves',
                                                        'Reviewer A maybe approves'))
        with self.assertRaises(ValueError):
            pack(changed, (0, 1))


if __name__ == '__main__':
    unittest.main()
