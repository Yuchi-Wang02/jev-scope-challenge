import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from data_tools import original_cases
from interface import compile_visible, execute, status_for
from line_evidence import (aggregate_line_choices, audit_claim_known_grammar,
                           audit_plan, plan_queries, visible_lines)


class LineEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = original_cases()

    def test_dry_plan_is_original_only_and_model_prompt_has_no_truth_metadata(self):
        audit = audit_plan()
        self.assertEqual(audit['per_order_model_queries'], 548)
        self.assertEqual(audit['two_order_planned_queries'], 1096)
        self.assertEqual(audit['actual_model_forwards'], 0)
        plans = plan_queries(self.cases)
        by_id = {case['id']: case for case in self.cases}
        self.assertEqual(len(plans), 1096)
        for item in plans:
            case = by_id[item['source_id']]
            span = item['evidence_span']
            self.assertEqual(case['state'][span['start']:span['end']], span['text'])
            self.assertNotIn(case['id'], item['prompt'])
            self.assertNotIn(case['parent'], item['prompt'])
            self.assertNotIn('legal_worlds', item['prompt'])
            self.assertEqual(item['split'], 'development')
            self.assertEqual(item['representation'], 'original')
        altered = [dict(case) for case in self.cases]
        altered[0]['state'] += '\nA provisional rewrite.'
        with self.assertRaises(ValueError):
            plan_queries(altered)
        reserved = [dict(case) for case in self.cases]
        reserved[0]['split'] = 'reserved_test'
        with self.assertRaises(ValueError):
            plan_queries(reserved)

    def test_oracle_line_labels_reconstruct_original_policy_truth(self):
        """Software property only: oracle labels are never presented as model results."""
        for case in self.cases:
            schema = compile_visible(case['state'], case['instruction'])
            lines = visible_lines(case['state'])
            self.assertEqual(len(lines), len(case['records']))
            statuses = {}
            for field in schema['fields']:
                labels = {}
                for line, record in zip(lines, case['records']):
                    labels[line['line_index']] = (
                        'POSITIVE' if record['scope'] == schema['target'] and
                        record['field'] == field['name'] and record['value'] else
                        'NEGATIVE' if record['scope'] == schema['target'] and
                        record['field'] == field['name'] else 'IRRELEVANT')
                claim = aggregate_line_choices(case['state'], field['name'], labels)
                truth = status_for(record['value'] for record in case['records']
                                   if record['scope'] == schema['target'] and
                                   record['field'] == field['name'])
                self.assertEqual(claim['status'], truth)
                statuses[field['name']] = claim['status']
            self.assertEqual(execute(schema, statuses), case['gold'])

    def test_aggregation_does_not_silently_repair_wrong_line_classification(self):
        case = next(c for c in self.cases if c['id'] == 'joint_approval-1-decisive_missing')
        lines = visible_lines(case['state'])
        self.assertEqual(len(lines), 2)
        wrong = aggregate_line_choices(case['state'], 'review_b', {0: 'IRRELEVANT', 1: 'NEGATIVE'})
        self.assertEqual(wrong['status'], 'FALSE')
        self.assertIn('other-', wrong['evidence_spans'][0]['text'])
        self.assertEqual(wrong['provenance'], 'model_line_classification_with_program_offsets')
        self.assertEqual(audit_claim_known_grammar(case['state'], case['instruction'], wrong)['reason'],
                         'wrong_target_or_field')
        self.assertEqual(wrong['status'], 'FALSE')  # The audit does not repair the model claim.
        with self.assertRaises(ValueError):
            aggregate_line_choices(case['state'], 'review_b', {0: 'IRRELEVANT'})


if __name__ == '__main__':
    unittest.main()
