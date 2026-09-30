"""Visible-ID replay boundaries and preservation of the failed original result."""
import hashlib
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from scope_gate import gate_line
from scope_gate_audit import audit, artifacts, contract_cases, replay
from joint_execution import OUT


class ScopeGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary, cls.decisions, cls.lines, cls.fields, cls.names = audit()

    def test_whole_ids_and_declared_record_slots_define_ownership(self):
        header = 'Request: allow action for request request-ABC.'
        self.assertEqual(gate_line(header, 'Reviewer A approves request request-ABCD.')['status'], 'DROP')
        self.assertEqual(gate_line(header, 'Route for request request-ABC: request-ABCD.')['status'], 'KEEP')
        self.assertEqual(gate_line(header, 'Permission for site request-ABC in request request-XYZ: allowed.')['status'], 'DROP')
        self.assertEqual(gate_line('Request: allow action for request other-ABC.',
                                  'Reviewer A rejects request other-ABC.')['status'], 'KEEP')

    def test_unsupported_text_is_explicit_and_never_silently_dropped(self):
        cases = contract_cases()
        self.assertEqual(len(cases), 16)
        self.assertTrue(all(c['model_output'] is None for c in cases))
        for name in ('mixed_owner_line', 'two_target_facts', 'quoted_target', 'implicit_reference', 'unfamiliar_id_syntax'):
            self.assertEqual(next(c['gate']['status'] for c in cases if c['id'] == name), 'UNKNOWN')
        from data_tools import original_cases
        source = original_cases()[0]
        state = source['state'].rsplit('\n', 1)[0] + '\nReviewer B rejects that request.'
        output = replay(state, source['instruction'], {0:'review_a:POSITIVE', 1:'review_b:POSITIVE', 2:'review_b:NEGATIVE'})
        self.assertEqual(output['gates'][2]['status'], 'UNKNOWN')
        self.assertEqual(output['routes'][2], 'review_b:NEGATIVE')
        self.assertEqual(output['facts']['review_b'], 'CONFLICT')

    def test_cleanup_keeps_both_action_regressions_and_original_failure(self):
        self.assertEqual(self.summary['transitions'],
                         {'wrong_to_correct':38, 'correct_to_correct':32, 'correct_to_wrong':2})
        regressions = [r for r in self.decisions if r['original_correct'] and not r['correct']]
        self.assertEqual({r['source_id'] for r in regressions},
                         {'route_lookup-4-flip', 'route_lookup-4-conflict'})
        for row in regressions:
            reference = {f['field']:f['reference'] for f in self.fields if f['source_id'] == row['source_id']}
            self.assertEqual(row['original_facts'], reference)
            self.assertNotEqual(row['facts'], reference)
        self.assertFalse(self.summary['original_joint_screen_passed'])
        self.assertFalse(self.summary['replay_has_prospective_screen'])
        self.assertEqual(self.summary['new_model_forwards'], 0)
        self.assertEqual(self.summary['replay_method']['model_calls'], 228)
        self.assertFalse(self.summary['projected_unchanged_query_subset']['measured_new_deployment'])

    def test_renaming_checks_are_software_only_and_expose_prefix_shortcuts(self):
        self.assertEqual(len(self.names), 216)
        self.assertTrue(all(r['model_output'] is None for r in self.names))
        for row in self.names:
            self.assertEqual(row['exact_id_scope'], row['expected_scope'])
        self.assertEqual(self.summary['name_checks']['swapped_prefix']['prefix_shortcut']['correct'], 0)
        self.assertEqual(self.summary['name_checks']['prefix_collision']['substring_shortcut']['false_keep'], 66)
        self.assertEqual(self.summary['gate_counts'], {'KEEP':162, 'DROP':66})
        self.assertEqual(self.summary['original_prefix_scope_agreement'], 228)

    def test_recomputation_is_read_only_and_all_derived_files_match(self):
        before = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir()}
        for path, content in artifacts().items():
            self.assertEqual(path.read_bytes().replace(b'\r\n',b'\n'), content.encode('utf-8'))
        self.assertEqual(before, {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir()})


if __name__ == '__main__':
    unittest.main()
