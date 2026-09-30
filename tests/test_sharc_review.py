import json
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/external-validation'
sys.path.insert(0, str(HERE))
from prepare_sharc_review import (
    CSV_FIELDS, PRIMARY_EACH, RESERVE_EACH, ROOT, STRATA,
    choose, export_private, review_pack, validate_review_rows,
)


def row(utterance_id, answer, history_answer):
    return {
        'tree_id': 'tree', 'utterance_id': utterance_id,
        'snippet': 'Visible rule', 'question': 'Visible question?',
        'scenario': 'Visible scenario', 'answer': answer,
        'evidence': 'EVIDENCE_MUST_NOT_LEAK',
        'source_url': 'SOURCE_URL_MUST_NOT_LEAK',
        'history': [{'follow_up_question': 'Visible condition?',
                     'follow_up_answer': history_answer,
                     'extra': 'EXTRA_MUST_NOT_LEAK'}],
    }


class SharcReviewPreparationTests(unittest.TestCase):
    def test_selection_uses_distinct_trees_and_balances_strata(self):
        candidates = defaultdict(list)
        for index, stratum in enumerate(STRATA):
            tree_names = ['shared-tree'] + [f'tree-{index}-{i}' for i in range(12)]
            for order, tree_id in enumerate(tree_names):
                candidates[stratum].append({
                    'tree_id': tree_id, 'ids': (f'{tree_id}-a', f'{tree_id}-b'),
                    'stratum': stratum, 'rows': [], 'rank': f'{order:03}',
                })
        selected = choose(candidates)
        self.assertEqual(len(selected), 30)
        self.assertEqual(len({item['tree_id'] for item in selected}), 30)
        self.assertEqual(Counter((item['stratum'], item['role'])
                                 for item in selected),
                         Counter({(stratum, 'primary'): PRIMARY_EACH
                                  for stratum in STRATA} |
                                 {(stratum, 'reserve'): RESERVE_EACH
                                  for stratum in STRATA}))

    def test_blind_export_omits_source_labels_and_pair_links(self):
        selected = [{
            'tree_id': 'tree', 'ids': ('a', 'b'), 'stratum': 'No/Yes',
            'rows': [row('a', 'LABEL_A_MUST_NOT_LEAK', 'No'),
                     row('b', 'LABEL_B_MUST_NOT_LEAK', 'Yes')],
            'rank': '0', 'role': 'primary',
        }]
        pack = review_pack(selected)
        self.assertEqual(len(pack['items']), 2)
        for item in pack['items']:
            self.assertEqual(set(item), {'item_id', 'snippet', 'question',
                                         'scenario', 'history'})
            self.assertEqual(set(item['history'][0]),
                             {'follow_up_question', 'follow_up_answer'})
        payload = json.dumps(pack)
        for forbidden in ('LABEL_A_MUST_NOT_LEAK', 'LABEL_B_MUST_NOT_LEAK',
                          'EVIDENCE_MUST_NOT_LEAK', 'SOURCE_URL_MUST_NOT_LEAK',
                          'EXTRA_MUST_NOT_LEAK'):
            self.assertNotIn(forbidden, payload)

    def test_export_rejects_public_repository_paths(self):
        for directory in (ROOT, ROOT / 'research', ROOT.parent / 'elsewhere'):
            with self.assertRaises(ValueError):
                export_private(directory, b'private', b'blank')

    def test_review_checker_requires_exact_ids_and_complete_rows(self):
        pack = {'items': [{'item_id': 'a'}, {'item_id': 'b'}]}
        blank = [dict.fromkeys(CSV_FIELDS, '') for _ in range(2)]
        blank[0]['item_id'], blank[1]['item_id'] = 'a', 'b'
        self.assertEqual(validate_review_rows(CSV_FIELDS, blank, pack)['pending'], 2)
        blank[0].update(action='ASK', reason='Condition is unresolved',
                        reviewer='reviewer-1', date='2026-09-29')
        self.assertEqual(validate_review_rows(CSV_FIELDS, blank, pack)['completed'], 1)
        blank[1]['item_id'] = 'a'
        with self.assertRaises(ValueError):
            validate_review_rows(CSV_FIELDS, blank, pack)
        blank[1]['item_id'] = 'b'
        blank[1]['action'] = 'Yes'
        with self.assertRaises(ValueError):
            validate_review_rows(CSV_FIELDS, blank, pack)


if __name__ == '__main__':
    unittest.main()
