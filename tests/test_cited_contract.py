import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from cited_contract import _evidence_records, verify_claim
from data_tools import original_cases


class CitedContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = original_cases()

    def case(self, family, variant):
        return next(c for c in self.cases if c['family'] == family and
                    c['variant'] == variant and c['parent'].endswith('-1'))

    def claim(self, field, status, spans):
        return {'field': field, 'status': status, 'spans': spans,
                'inspected_scope': 'complete_visible_state'}

    def test_exact_target_binding_and_location(self):
        case = self.case('joint_approval', 'decisive_missing')
        _, entries = _evidence_records(case['state'], case['instruction'])
        other = next(span for record, span in entries if record['scope'] != case['target'])
        result = verify_claim(case['state'], case['instruction'],
                              self.claim('review_b', 'FALSE', [other]))
        self.assertEqual(result['reason'], 'wrong_target_or_field')
        source = self.case('joint_approval', 'full')
        _, records = _evidence_records(source['state'], source['instruction'])
        right = next(span for record, span in records if record['scope'] == source['target']
                     and record['field'] == 'review_a')
        self.assertEqual(verify_claim(source['state'], source['instruction'],
                                      self.claim('review_a', 'TRUE', [right]))['gate'], 'accepted')
        self.assertEqual(verify_claim(source['state'], source['instruction'],
                                      self.claim('review_b', 'TRUE', [right]))['reason'],
                         'wrong_target_or_field')
        self.assertEqual(verify_claim(source['state'], source['instruction'],
                                      self.claim('review_a', 'FALSE', [right]))['reason'],
                         'status_contradicts_visible_records')
        shifted = right | {'start': right['start'] + 1}
        self.assertEqual(verify_claim(source['state'], source['instruction'],
                                      self.claim('review_a', 'TRUE', [shifted]))['reason'],
                         'span_not_exact')

    def test_conflict_needs_both_values_and_definition_is_not_evidence(self):
        case = self.case('joint_approval', 'conflict')
        _, entries = _evidence_records(case['state'], case['instruction'])
        target = [span for record, span in entries if record['scope'] == case['target']
                  and record['field'] == 'review_b']
        self.assertEqual(len(target), 2)
        self.assertEqual(verify_claim(case['state'], case['instruction'],
                                      self.claim('review_b', 'CONFLICT', target[:1]))['reason'],
                         'citations_do_not_cover_status')
        self.assertEqual(verify_claim(case['state'], case['instruction'],
                                      self.claim('review_b', 'CONFLICT', target))['gate'], 'accepted')
        self.assertEqual(verify_claim(case['state'], case['instruction'],
                                      self.claim('review_b', 'CONFLICT', [target[0]] * 2))['reason'],
                         'duplicate_span')
        policy_text = case['instruction'][:20]
        self.assertEqual(verify_claim(case['state'], case['instruction'],
                                      self.claim('review_b', 'TRUE',
                                                 [{'start': 0, 'end': 20, 'text': policy_text}]))['gate'],
                         'rejected')

    def test_missing_requires_separate_absence_certification(self):
        case = self.case('joint_approval', 'decisive_missing')
        missing = self.claim('review_b', 'MISSING', [])
        self.assertEqual(verify_claim(case['state'], case['instruction'], missing)['gate'],
                         'absence_unverified')
        certified = verify_claim(case['state'], case['instruction'], missing,
                                 certify_absence_with_parser=True)
        self.assertEqual(certified['provenance'], 'pure_code_reference')
        self.assertEqual(certified['gate'], 'accepted')
        full = self.case('joint_approval', 'full')
        self.assertEqual(verify_claim(full['state'], full['instruction'], missing)['gate'],
                         'rejected')
        hidden_header = case['state'].replace('Evidence:',
            'Evidence: Reviewer B rejects request ' + case['target'] + '.')
        self.assertEqual(verify_claim(hidden_header, case['instruction'], missing,
                                      certify_absence_with_parser=True)['gate'],
                         'unsupported_grammar')

    def test_unknown_rewrite_grammar_is_explicit(self):
        pair = json.loads((HERE / 'review/candidate_rewrites.jsonl').read_text(encoding='utf-8').splitlines()[0])
        result = verify_claim(pair['candidate_state'], pair['policy'],
                              self.claim('review_a', 'TRUE', []))
        self.assertEqual(result['gate'], 'unsupported_grammar')

    def test_all_original_lines_have_exact_visible_spans(self):
        self.assertEqual(len(self.cases), 72)
        for case in self.cases:
            _, entries = _evidence_records(case['state'], case['instruction'])
            self.assertEqual(len(entries), len(case['records']))
            for _, span in entries:
                self.assertEqual(case['state'][span['start']:span['end']], span['text'])


if __name__ == '__main__':
    unittest.main()
