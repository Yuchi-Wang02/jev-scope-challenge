import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from data_tools import original_cases
from interface import compile_visible, execute
from joint_route import OTHER_REQUEST, aggregate, plan_queries
from joint_route_plan import direct_queries, run


class JointRoutePreparationTests(unittest.TestCase):
    def test_complete_original_only_prompts_and_distinct_direct_orders(self):
        cases = original_cases()
        planned = plan_queries(cases)
        direct = direct_queries(cases)
        self.assertEqual((len(planned), len(direct)), (456, 228))
        self.assertEqual(len({(r['source_id'], r['line_index'], r['mapping'])
                              for r in planned}), 456)
        self.assertTrue(all(r['split'] == 'development' and
                            r['representation'] == 'original' and
                            r['source_id'] not in r['prompt'] for r in planned + direct))
        self.assertTrue(all('Evidence line under inspection:' in r['prompt']
                            for r in planned))
        self.assertEqual(run('verify')['actual_model_forwards'], 0)

    def test_program_routes_are_software_oracle_only(self):
        for case in original_cases():
            schema = compile_visible(case['state'], case['instruction'])
            choices = {
                i: (OTHER_REQUEST if record['scope'] != case['target'] else
                    record['field'] + (':POSITIVE' if record['value'] else ':NEGATIVE'))
                for i, record in enumerate(case['records'])}
            result = aggregate(case['state'], schema, choices)
            self.assertEqual(execute(schema, result['facts']), case['gold'])
            self.assertFalse(result['absence_certified'])
        case = original_cases()[0]
        schema = compile_visible(case['state'], case['instruction'])
        with self.assertRaises(ValueError):
            aggregate(case['state'], schema, {0: 'review_a:POSITIVE'})


if __name__ == '__main__':
    unittest.main()
