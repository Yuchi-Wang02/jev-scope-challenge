import copy
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/source-label-screen'))
import report as screen_report
from action_interface import parse_final
from test_rule_comparison_analysis import setup_grid, synthetic_token_checker
from analyze_comparison import analyze


class SourceScreenReportTests(unittest.TestCase):
    def test_repaired_view_does_not_replace_strict_failure_or_duplicate_cost(self):
        plan, refs, journals = setup_grid()
        # Synthetic old strict prefix only. No actual model or human reference.
        journals['jev'] = journals['jev'][:4]
        strict = analyze(plan, refs, journals, 'synthetic_hash', qwen_checker=synthetic_token_checker)
        api = {'records': [], 'total_http_attempts': 8}
        for j in plan['jobs']:
            if j['backend'] == 'jev':
                api['records'].append({'job_id': j['id'], 'native_action': 'Yes',
                    'quality': {'unique_argmax_action': 'No', 'all_original_metadata_checks_pass': False},
                    'input_tokens': 10, 'output_tokens': 3, 'latency_seconds': .1})
        plan['reference_basis'] = 'synthetic labels only'
        result = screen_report.combine(strict, plan, refs, api)
        self.assertEqual(result['original_strict_status'], 'incomplete_grid')
        self.assertTrue(all(c['metric'] is None for c in result['original_strict_jev_conditions'].values()))
        self.assertEqual(result['status'], 'complete_repaired_decision_grid')
        self.assertEqual(result['resources']['jev_all_phases']['total_http_attempts'], 8)
        self.assertEqual(len(result['conditions']), 8)
        native = result['conditions']['jev_native_order0']['metric']['pair_records']
        alternative = result['conditions']['jev_unique_argmax_order0']['metric']['pair_records']
        self.assertNotEqual(native[0]['predictions'], alternative[0]['predictions'])
        self.assertEqual(result['conditions']['jev_native_order0']['resources'],
                         result['conditions']['jev_unique_argmax_order0']['resources'])
        missing = copy.deepcopy(api); missing['records'].pop()
        with self.assertRaisesRegex(ValueError, 'cohort'):
            screen_report.combine(strict, plan, refs, missing)

    def test_saved_text_parsing_detects_changed_actions_and_preserves_invalid_output(self):
        for text, completion in [('{"action":"Yes"}', 'natural_eos'), ('unfinished', 'length')]:
            parsed = asdict(parse_final(text, completion=completion))
            r = {'status': 'ok', 'detail': {'adapted': {'boundary_error': None,
                'completion': completion, 'final_text': text, 'parsed': parsed}}}
            got = screen_report.stored_extraction_check({}, r)
            self.assertEqual(got['action'], 'Yes' if completion == 'natural_eos' else None)
            r['detail']['adapted']['parsed']['action'] = 'ASK'
            with self.assertRaisesRegex(ValueError, 'final text'):
                screen_report.stored_extraction_check({}, r)


if __name__ == '__main__':
    unittest.main()
