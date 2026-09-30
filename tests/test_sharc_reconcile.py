import csv
import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/external-validation'
sys.path.insert(0, str(HERE))
from prepare_sharc_review import ROOT, review_pack
from review_reconcile import (
    ADJUDICATION_FIELDS, blank_adjudication_csv, private_directory,
    reconciliation,
)


def source_row(ident, source_answer, history_answer):
    return {
        'tree_id': 'tree', 'utterance_id': ident,
        'snippet': 'Rule visible to reviewers',
        'question': 'Question visible to reviewers?', 'scenario': '',
        'history': [{'follow_up_question': 'Condition?',
                     'follow_up_answer': history_answer}],
        'answer': source_answer,
        'evidence': 'SOURCE_EVIDENCE_MUST_NOT_LEAK',
    }


def fixture():
    pair = {
        'tree_id': 'tree', 'ids': ('a', 'b'), 'stratum': 'No/Yes',
        'rows': [source_row('a', 'SOURCE_ANSWER_A_MUST_NOT_LEAK', 'No'),
                 source_row('b', 'SOURCE_ANSWER_B_MUST_NOT_LEAK', 'Yes')],
        'role': 'primary', 'rank': '0',
    }
    pack = review_pack([pair])
    a = []
    b = []
    for index, item in enumerate(pack['items']):
        ident = item['item_id']
        a.append({'item_id': ident, 'action': 'Yes' if index else 'No',
                  'reason': 'Based on visible rule', 'reviewer': 'alice',
                  'date': '2026-09-29'})
        b.append({'item_id': ident, 'action': 'Yes',
                  'reason': 'My independent reading', 'reviewer': 'bob',
                  'date': '2026-09-29'})
    return pack, [pair], a, b


class SharcReconciliationTests(unittest.TestCase):
    def test_complete_reviews_unblind_pairs_without_source_labels(self):
        pack, selected, a, b = fixture()
        report = reconciliation(pack, selected, a, b)
        self.assertEqual(report['individual_items'], 2)
        self.assertEqual(report['item_level_agreement'], 1)
        self.assertEqual(report['item_level_disagreement'], 1)
        self.assertEqual(len(report['pairs']), 1)
        self.assertNotIn('stratum', report['pairs'][0])
        self.assertNotIn('role', report['pairs'][0])
        payload = json.dumps(report)
        for forbidden in ('SOURCE_ANSWER_A_MUST_NOT_LEAK',
                          'SOURCE_ANSWER_B_MUST_NOT_LEAK',
                          'SOURCE_EVIDENCE_MUST_NOT_LEAK'):
            self.assertNotIn(forbidden, payload)
        blank = list(csv.DictReader(io.StringIO(
            blank_adjudication_csv(report).decode('utf-8'))))
        self.assertEqual(len(blank), 1)
        self.assertEqual(tuple(blank[0]), ADJUDICATION_FIELDS)
        self.assertFalse(blank[0]['final_action_1'])
        self.assertFalse(blank[0]['pair_validity'])

    def test_incomplete_or_same_identity_rejected(self):
        pack, selected, a, b = fixture()
        b[0]['reviewer'] = 'alice'
        b[1]['reviewer'] = 'alice'
        with self.assertRaises(ValueError):
            reconciliation(pack, selected, a, b)
        b[0]['reviewer'] = 'bob'
        b[1]['reviewer'] = 'bob'
        b[0]['action'] = ''
        b[0]['reason'] = ''
        b[0]['reviewer'] = ''
        b[0]['date'] = ''
        with self.assertRaises(ValueError):
            reconciliation(pack, selected, a, b)

    def test_adjudication_export_must_stay_private(self):
        with self.assertRaises(ValueError):
            private_directory(ROOT / 'research')


if __name__ == '__main__':
    unittest.main()
