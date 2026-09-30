"""Completed-run checks: scope denominators, shared controls and raw trace."""
import hashlib
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from joint_analyze import analyze
from joint_execution import OUT
from publish_joint import PAGES, artifacts, payload


class JointResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = payload()

    def test_scope_errors_use_the_distractor_denominator_and_keep_target_errors(self):
        lines = [line for case in self.data['cases'] for line in case['lines']]
        distractors = [line for line in lines if line['construction_reference_route'] == 'OTHER_REQUEST']
        targets = [line for line in lines if line['construction_reference_route'] != 'OTHER_REQUEST']
        self.assertEqual((len(targets), len(distractors), len(lines)), (162, 66, 228))
        self.assertEqual(Counter(line['program_audit'] for line in distractors),
                         {'wrong_request': 60, 'correct_route': 6})
        self.assertEqual(Counter(line['program_audit'] for line in targets),
                         {'correct_route': 160, 'wrong_field': 2})

    def test_saved_scope_error_creates_the_visible_target_conflict(self):
        case = next(c for c in self.data['cases'] if c['id'] == 'joint_approval-1-full')
        wrong = case['lines'][2]
        self.assertEqual(wrong['evidence_span']['text'], 'Reviewer B rejects request other-SVNUU.')
        self.assertEqual((wrong['model_route'], wrong['construction_reference_route']),
                         ('review_b:NEGATIVE', 'OTHER_REQUEST'))
        self.assertEqual((case['gold'], case['decisions']['joint']['prediction']),
                         ('ALLOW', 'INSUFFICIENT'))
        self.assertEqual(case['decisions']['joint']['facts']['review_b'], 'CONFLICT')

    def test_physical_grid_and_shared_control_counts_are_not_added_as_samples(self):
        queries = [q for c in self.data['cases'] for q in c['queries']]
        self.assertEqual((len(queries), len({q['query_id'] for q in queries})), (514, 514))
        self.assertEqual(Counter(q['arm'] for q in queries), {'joint': 228, 'direct': 286})
        self.assertEqual(sum(q['input_tokens'] for q in queries), 191738)
        for case in self.data['cases']:
            self.assertEqual(case['decisions']['direct_call_matched']['prediction'],
                             case['decisions']['direct_token_matched']['prediction'])
        self.assertEqual(self.data['anchor']['max_abs_logit_delta'], 0)
        self.assertEqual(self.data['anchor']['identical_encoded_inputs'], 72)

    def test_joint_screen_fails_both_parts_and_known_controls_stay_offline(self):
        m = self.data['summary']['methods']['joint']
        screen = self.data['summary']['fixed_development_screening_rule']
        self.assertGreater(m['false_commitments'], screen['max_false_commitments'])
        self.assertLess(m['determined_correct'], screen['min_determined_correct'])
        self.assertFalse(screen['passed'])
        for name in ('always_defer', 'known_grammar'):
            self.assertEqual(self.data['methods'][name]['model_calls'], 0)
            self.assertIsNone(self.data['methods'][name]['summed_forward_latency_s'])

    def test_read_only_recompute_preserves_all_run_files_and_viewers_match(self):
        paths = list(OUT.iterdir())
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        analyze()
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
        for path, expected in artifacts().items():
            self.assertEqual(path.read_bytes().replace(b'\r\n', b'\n'), expected.encode('utf-8'))
        self.assertEqual(PAGES[0].read_bytes(), PAGES[1].read_bytes())
        self.assertNotIn('__JOINT_DATA__', PAGES[0].read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
