import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1] / 'research/external-validation'
sys.path.insert(0, str(HERE))
import comparison_plan as planner
from prepare_sharc_review import CSV_FIELDS, STRATA, item_id, pair_id, readable, review_pack
from review_reconcile import ADJUDICATION_FIELDS, blank_adjudication_csv, reconciliation
from review_finalize import reviewed_manifest, validate_adjudication_rows


def fixtures():
    selected = []
    for stratum in STRATA:
        for i in range(10):
            name = f'SYNTHETIC_{stratum}_{i}'
            rows = [{'tree_id': name, 'utterance_id': name + suffix,
                     'snippet': 'Synthetic software fixture, not a human review.',
                     'question': 'Is the test flag enabled?', 'scenario': '',
                     'history': [{'follow_up_question': 'Is the flag set?',
                                  'follow_up_answer': ans}],
                     'answer': 'SOURCE_LABEL_SECRET', 'evidence': 'SOURCE_EVIDENCE_SECRET'}
                    for suffix, ans in [('a', 'Yes'), ('b', 'No')]]
            selected.append({'tree_id': name, 'ids': tuple(r['utterance_id'] for r in rows),
                             'stratum': stratum, 'role': 'primary' if i < 8 else 'reserve',
                             'rows': rows})
    pack = review_pack(selected)
    judgments = {pair_id(c): {'item_ids': [item_id(r) for r in c['rows']],
                             'actions': ['Yes', 'No'], 'validity': 'VALID',
                             'reason': 'SYNTHETIC_ONLY', 'adjudicator': 'TEST_ONLY',
                             'date': '2026-09-30'} for c in selected}
    final = reviewed_manifest(selected, judgments, 'selection', ('a', 'b'), 'c')
    return selected, pack, final


def renderer(prompt, thinking, cap):
    return 'SYNTHETIC_RENDER\n' + prompt, [10, 11, 12]


class SharcComparisonPlanTests(unittest.TestCase):
    def test_full_grid_and_budgets_with_no_source_or_review_label_leak(self):
        selected, pack, final = fixtures()
        # Inject at the compiler boundary, not just before the earlier review-pack
        # filter, to prove the request allowlist itself excludes metadata.
        for entry in pack['items']:
            entry['answer'] = 'SOURCE_LABEL_SECRET'
            entry['human_reason'] = 'REVIEW_REASON_SECRET'
            entry['history'][0]['review_label'] = 'HISTORY_LABEL_SECRET'
        plan, references = planner.material(pack, selected, final, renderer)
        self.assertEqual(plan['counts']['jev_calls'], 96)
        self.assertEqual(plan['counts']['local_generations'], 192)
        self.assertEqual(plan['counts']['local_generated_token_cap'], 221184)
        self.assertEqual(len(references), 24)
        self.assertEqual(len({j['id'] for j in plan['jobs']}), 288)
        self.assertEqual(len({j['condition'] for j in plan['jobs']}), 6)
        self.assertEqual(plan['model_calls_executed'], 0)
        raw = json.dumps(plan)
        self.assertNotIn('SOURCE_LABEL_SECRET', raw)
        self.assertNotIn('SOURCE_EVIDENCE_SECRET', raw)
        self.assertNotIn('REVIEW_REASON_SECRET', raw)
        self.assertNotIn('HISTORY_LABEL_SECRET', raw)
        for job in plan['jobs']:
            state = job['request']['state'] if job['backend'] == 'jev' else json.loads(
                job['prompt'].split('\nstate: ', 1)[1].split('\nReturn only ', 1)[0])
            self.assertEqual(set(state), {'snippet', 'question', 'scenario', 'history'})

    def test_reference_changes_do_not_change_prompts_order_or_budget(self):
        selected, pack, final = fixtures()
        a, refs_a = planner.material(pack, selected, final, renderer)
        changed = copy.deepcopy(final)
        for row in changed['selected']:
            row['adjudicated_actions'] = ['ASK', 'ASK']
        b, refs_b = planner.material(pack, selected, changed, renderer)
        self.assertEqual(a, b)
        self.assertNotEqual(refs_a, refs_b)

    def test_foreign_unresolved_duplicate_and_oversized_material_stop(self):
        selected, pack, final = fixtures()
        for field, value in [('pair_id', 'foreign'), ('item_ids', ['x', 'y']),
                             ('adjudicated_actions', ['UNCLEAR', 'No'])]:
            bad = copy.deepcopy(final)
            bad['selected'][0][field] = value
            with self.assertRaises(ValueError):
                planner.material(pack, selected, bad, renderer)
        bad = copy.deepcopy(final)
        bad['selected'].append(bad['selected'][0])
        with self.assertRaises(ValueError):
            planner.material(pack, selected, bad, renderer)
        with self.assertRaises(ValueError):
            planner.material(pack, selected, final, lambda *args: ('x', [1] * 32768))
        with self.assertRaises(ValueError):
            planner.material(pack, selected, final, lambda *args: ('x', [True]))

    def test_missing_reviews_fail_before_source_or_tokenizer_access(self):
        with patch.object(planner, 'prepare_with_selection') as source:
            with self.assertRaises(ValueError):
                planner.verified_review_inputs('missing-a', 'missing-b', 'missing-c', '.local')
            source.assert_not_called()

    def test_saved_reviews_are_recomputed_and_tampering_is_rejected(self):
        selected, pack, _ = fixtures()
        local = planner.ROOT / '.local'
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local, prefix='comparison-test-') as temp:
            path = Path(temp)
            reviews = []
            review_paths = []
            for identity in ('SYNTHETIC_REVIEW_A', 'SYNTHETIC_REVIEW_B'):
                rows = [dict(item_id=i['item_id'], action='Yes', reason='SOFTWARE_TEST_ONLY',
                             reviewer=identity, date='2026-09-30') for i in pack['items']]
                target = path / (identity + '.csv')
                with target.open('w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                    writer.writeheader(); writer.writerows(rows)
                reviews.append(rows); review_paths.append(target)
            hashes = tuple(planner.sha(p.read_bytes()) for p in review_paths)
            queue = reconciliation(pack, selected, *reviews)
            queue.update(selection_sha256='selection', review_a_sha256=hashes[0], review_b_sha256=hashes[1])
            (path / 'adjudication_queue.json').write_bytes(readable(queue))
            (path / 'adjudication_blank.csv').write_bytes(blank_adjudication_csv(queue))
            rows = [dict(zip(ADJUDICATION_FIELDS, (p['pair_id'],
                        p['items'][0]['item_id'], p['items'][1]['item_id'],
                        'Yes', 'No', 'VALID', 'SOFTWARE_TEST_ONLY', 'TEST_ADJUDICATOR', '2026-09-30')))
                    for p in queue['pairs']]
            adj = path / 'adjudicated.csv'
            with adj.open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=ADJUDICATION_FIELDS)
                writer.writeheader(); writer.writerows(rows)
            judgments = validate_adjudication_rows(ADJUDICATION_FIELDS, rows, queue)
            final = reviewed_manifest(selected, judgments, 'selection', hashes, planner.sha(adj.read_bytes()))
            (path / 'reviewed_selection.json').write_bytes(readable(final))
            source_result = ({'selection_sha256': 'selection'}, readable(pack), b'', selected)
            with patch.object(planner, 'prepare_with_selection', return_value=source_result), \
                    patch.object(planner, 'verify_manifest'):
                result = planner.verified_review_inputs(*review_paths, adj, path)
                self.assertEqual(result[2], final)
                tampered = copy.deepcopy(final)
                tampered['selected'][0]['adjudicated_actions'] = ['No', 'No']
                (path / 'reviewed_selection.json').write_bytes(readable(tampered))
                with self.assertRaisesRegex(ValueError, 'final cohort differs'):
                    planner.verified_review_inputs(*review_paths, adj, path)

    def test_private_output_is_repeatable_and_never_overwrites_partial_data(self):
        local = planner.ROOT / '.local'
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local, prefix='comparison-output-test-') as temp:
            p = Path(temp)
            self.assertEqual(planner.preserve(p, {'synthetic': True}, []), 'created')
            self.assertEqual(planner.preserve(p, {'synthetic': True}, []), 'verified_existing')
            with self.assertRaises(ValueError):
                planner.preserve(p, {'synthetic': False}, [])
            partial = p / 'partial'
            partial.mkdir()
            (partial / 'comparison_plan.json').write_text('preserve me')
            with self.assertRaises(ValueError):
                planner.preserve(partial, {}, [])
            self.assertEqual((partial / 'comparison_plan.json').read_text(), 'preserve me')


if __name__ == '__main__':
    unittest.main()
