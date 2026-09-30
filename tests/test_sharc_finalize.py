import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/external-validation'
sys.path.insert(0, str(HERE))
from prepare_sharc_review import item_id, pair_id
from review_finalize import (
    ADJUDICATION_FIELDS, apply_frozen_reserves, reviewed_manifest,
    validate_adjudication_rows,
)


def candidate(name, role):
    rows = [{'tree_id': name, 'utterance_id': name + suffix}
            for suffix in ('a', 'b')]
    return {'tree_id': name, 'ids': (name + 'a', name + 'b'),
            'stratum': 'No/Yes', 'role': role, 'rows': rows}


def judgment(candidate_row, validity='VALID', actions=('Yes', 'No')):
    return {'item_ids': [item_id(row) for row in candidate_row['rows']],
            'actions': list(actions), 'validity': validity,
            'reason': 'Reviewed visible facts', 'adjudicator': 'adjudicator',
            'date': '2026-09-29'}


class SharcFinalizationTests(unittest.TestCase):
    def test_invalid_primary_uses_first_valid_frozen_reserve(self):
        primary_a = candidate('primary-a', 'primary')
        primary_b = candidate('primary-b', 'primary')
        reserve_a = candidate('reserve-a', 'reserve')
        reserve_b = candidate('reserve-b', 'reserve')
        selected = [primary_a, primary_b, reserve_a, reserve_b]
        labels = {pair_id(item): judgment(item) for item in selected}
        labels[pair_id(primary_a)] = judgment(primary_a, 'INVALID', ('UNCLEAR', 'No'))
        labels[pair_id(primary_b)] = judgment(primary_b, 'VALID', ('Yes', 'Yes'))
        final, replaced, skipped = apply_frozen_reserves(selected, labels)
        self.assertEqual([pair_id(item) for item in final],
                         [pair_id(reserve_a), pair_id(primary_b)])
        self.assertEqual(replaced, [{'primary': pair_id(primary_a),
                                     'reserve': pair_id(reserve_a)}])
        self.assertEqual(skipped, [])
        result = reviewed_manifest(selected, labels, 'selection-digest',
                                   ('review-a-hash', 'review-b-hash'), 'adj-hash')
        self.assertEqual(result['adjudicated_action_flips'], 1)
        self.assertFalse(result['model_inference_open'])

    def test_invalid_reserve_is_skipped_and_exhaustion_stops(self):
        primary = candidate('primary', 'primary')
        reserve_a = candidate('reserve-a', 'reserve')
        reserve_b = candidate('reserve-b', 'reserve')
        selected = [primary, reserve_a, reserve_b]
        labels = {pair_id(item): judgment(item) for item in selected}
        labels[pair_id(primary)] = judgment(primary, 'INVALID')
        labels[pair_id(reserve_a)] = judgment(reserve_a, 'INVALID')
        final, replaced, skipped = apply_frozen_reserves(selected, labels)
        self.assertEqual([pair_id(item) for item in final], [pair_id(reserve_b)])
        self.assertEqual(skipped, [pair_id(reserve_a)])
        labels[pair_id(reserve_b)] = judgment(reserve_b, 'INVALID')
        with self.assertRaises(ValueError):
            apply_frozen_reserves(selected, labels)

    def test_adjudication_requires_exact_pairs_and_clear_valid_labels(self):
        item = candidate('tree', 'primary')
        ids = [item_id(row) for row in item['rows']]
        queue = {'pairs': [{'pair_id': pair_id(item),
                            'items': [{'item_id': ids[0]}, {'item_id': ids[1]}]}]}
        row = dict(zip(ADJUDICATION_FIELDS, (
            pair_id(item), ids[0], ids[1], 'Yes', 'No', 'VALID',
            'Rule applies', 'adjudicator', '2026-09-29')))
        result = validate_adjudication_rows(ADJUDICATION_FIELDS, [row], queue)
        self.assertEqual(result[pair_id(item)]['actions'], ['Yes', 'No'])
        unclear = {**row, 'final_action_1': 'UNCLEAR'}
        with self.assertRaises(ValueError):
            validate_adjudication_rows(ADJUDICATION_FIELDS, [unclear], queue)
        wrong_item = {**row, 'item_1_id': 'foreign'}
        with self.assertRaises(ValueError):
            validate_adjudication_rows(ADJUDICATION_FIELDS, [wrong_item], queue)


if __name__ == '__main__':
    unittest.main()
