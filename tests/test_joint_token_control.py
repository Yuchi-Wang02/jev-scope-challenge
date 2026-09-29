import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from data_tools import original_cases
from joint_route_plan import direct_queries
from joint_token_control import COSTS, SELECTED, expected, identity, run


class JointTokenControlTests(unittest.TestCase):
    def test_selected_plan_includes_call_matched_base_without_repeats(self):
        report = run('verify', 'unused-cache')
        self.assertEqual((report['direct_queries'], report['input_tokens'], report['gap'],
                          report['new_model_forwards']), (286, 95849, 40, 0))
        rows = [json.loads(line) for line in SELECTED.read_text(encoding='utf-8').splitlines()]
        ids = [identity(row) for row in rows]
        self.assertEqual(len(set(ids)), 286)
        self.assertTrue({identity(row) for row in direct_queries(original_cases())} <= set(ids))
        self.assertTrue(all(row['split'] == 'development' and
                            row['representation'] == 'original' and
                            row['source_id'] not in row['prompt'] for row in rows))

    def test_cost_ledger_rejects_foreign_prompt(self):
        costs = [json.loads(line) for line in COSTS.read_text(encoding='utf-8').splitlines()]
        costs[0]['prompt_sha256_lf'] = '0' * 64
        with self.assertRaises(ValueError):
            expected(costs)


if __name__ == '__main__':
    unittest.main()
