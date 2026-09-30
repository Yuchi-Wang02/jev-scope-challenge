import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/external-validation'))
from paired_metrics import score_condition


def pair(n, refs=('Yes', 'No')):
    return {'pair_id': f'p{n}', 'tree_id': f't{n}',
            'item_ids': [f'i{n}a', f'i{n}b'], 'reference_actions': list(refs)}


def run(pairs, actions):
    ids = [item for p in pairs for item in p['item_ids']]
    return score_condition(pairs, [dict(item_id=i, action=a) for i, a in zip(ids, actions)],
                           condition='SYNTHETIC_SOFTWARE_TEST')


class RulePairedMetricTests(unittest.TestCase):
    def test_equal_item_accuracy_can_hide_different_pair_success(self):
        pairs = [pair(0), pair(1)]
        a = run(pairs, ['Yes', 'No', 'No', 'Yes'])
        b = run(pairs, ['Yes', 'Yes', 'Yes', 'Yes'])
        self.assertEqual(a['item_accuracy']['rate'], 0.5)
        self.assertEqual(a['item_accuracy'], b['item_accuracy'])
        self.assertEqual(a['pair_both_correct']['rate'], 0.5)
        self.assertEqual(b['pair_both_correct']['rate'], 0)
        self.assertEqual(a['correctness_counts']['neither_correct'], 1)
        self.assertEqual(b['correctness_counts']['first_only'], 2)

    def test_changing_output_is_not_necessarily_correct(self):
        r = run([pair(0), pair(1, ('ASK', 'ASK'))], ['No', 'Yes', 'ASK', 'No'])
        self.assertEqual(r['change_strata']['reference_changed']['prediction_changed'], 1)
        self.assertEqual(r['change_strata']['reference_same']['prediction_changed'], 1)
        self.assertEqual(r['pair_both_correct']['numerator'], 0)
        self.assertEqual(r['decisive_when_reference_ask']['numerator'], 1)

    def test_failures_keep_denominators_and_are_not_ask_or_changes(self):
        r = run([pair(0, ('ASK', 'No')), pair(1, ('Irrelevant', 'Yes'))],
                [None, 'ASK', 'ASK', None])
        self.assertEqual(r['invalid_output'], {'numerator': 2, 'denominator': 4, 'rate': 0.5})
        self.assertEqual(r['pair_both_correct']['denominator'], 2)
        self.assertEqual(r['change_strata']['reference_changed']['incomplete_pair'], 2)
        self.assertEqual(r['change_strata']['reference_changed']['prediction_changed'], 0)
        self.assertEqual(r['ask_when_reference_decisive']['numerator'], 1)
        self.assertEqual(r['confusion']['Irrelevant']['ASK'], 1)
        self.assertEqual(r['decisive_when_reference_ask']['numerator'], 0)
        self.assertTrue(all(p['prediction_changed'] is None for p in r['pair_records']))

    def test_absent_reference_stratum_is_unavailable_not_zero_accuracy(self):
        r = run([pair(0)], ['Yes', 'No'])
        self.assertIsNone(r['change_strata']['reference_same']['pair_both_correct']['rate'])
        self.assertIsNone(r['decisive_when_reference_ask']['rate'])
        self.assertEqual(r['pair_both_correct']['rate'], 1)

    def test_integrity_rejects_missing_repeated_foreign_or_unresolved_rows(self):
        pairs = [pair(0), pair(1)]
        valid = [dict(item_id=i, action='Yes') for p in pairs for i in p['item_ids']]
        bad_predictions = [valid[:-1], valid + [valid[0]],
                           valid[:-1] + [dict(item_id='foreign', action='Yes')],
                           valid[:-1] + [dict(item_id='i1b', action='yes')]]
        for bad in bad_predictions:
            with self.assertRaises(ValueError):
                score_condition(pairs, bad, condition='test')
        for field, value in [('tree_id', 't0'), ('pair_id', 'p0'),
                             ('item_ids', ['i0a', 'i1b']),
                             ('reference_actions', ['UNCLEAR', 'No'])]:
            bad = copy.deepcopy(pairs)
            bad[1][field] = value
            with self.assertRaises(ValueError):
                score_condition(bad, valid, condition='test')
        with self.assertRaises(ValueError):
            score_condition([], [], condition='test')

    def test_order_independence_does_not_pool_repeated_measurements(self):
        pairs = [pair(0), pair(1)]
        predictions = [dict(item_id=i, action=a) for p in pairs
                       for i, a in zip(p['item_ids'], p['reference_actions'])]
        before = copy.deepcopy((pairs, predictions))
        a = score_condition(pairs, predictions, condition='mapping_1')
        b = score_condition(list(reversed(pairs)), list(reversed(predictions)), condition='mapping_1')
        self.assertEqual(a, b)
        self.assertEqual((pairs, predictions), before)
        with self.assertRaises(ValueError):
            score_condition(pairs, predictions + predictions, condition='pooled')


if __name__ == '__main__':
    unittest.main()
