"""Synthetic in-memory tests only: these fixtures are never model results."""
import copy
import importlib.util
import json
import random
import sys
import types
import unittest
from unittest.mock import patch
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/request-ownership'
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location('ownership_analyzer_tests', HERE / 'analyze.py')
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def synthetic_fixture():
    """Invent logits in memory for software checks, never save them to results/."""
    scenes, views = analysis.prepare.material()
    plans = analysis.prepare.plans(views)
    encoded = [json.loads(line) for line in (HERE / 'preparation/encoded_queries.jsonl').read_text(encoding='utf-8').splitlines()]
    expected = [plan | tokens | {'split': 'new_scene_development'} for plan, tokens in zip(plans, encoded)]
    scene_index = {scene['parent']: scene for scene in scenes}
    view_index = {view['view_id']: view for view in views}
    raw = []
    ordered = list(expected)
    random.Random(20261007).shuffle(ordered)
    for number, plan in enumerate(ordered, 1):
        view = view_index[plan['view_id']]
        if plan['arm'] == 'joint_full':
            record = scene_index[view['parent']]['records'][plan['line_index']]
            # Deliberately ignore ownership: gate should remove these invented wrong routes.
            prediction = record['field'] + (':POSITIVE' if record['value'] else ':NEGATIVE')
        else:
            prediction = 'ALLOW' if plan['arm'] == 'direct_full' else view['gold']
        logits = [-4.0] * len(plan['order'])
        logits[plan['order'].index(prediction)] = 4.0
        raw.append(plan | {'config_hash': 'SYNTHETIC_UNIT_TEST_ONLY', 'forward_index': number,
                           'ok': True, 'logits': logits,
                           'probabilities': analysis.probabilities(logits, len(logits)),
                           'prediction': prediction, 'candidate_mass': 0.1, 'latency_s': 0.001})
    return scenes, views, expected, raw


def replace_prediction(row, prediction):
    row['prediction'] = prediction
    row['logits'] = [-4.0] * len(row['order'])
    row['logits'][row['order'].index(prediction)] = 4.0
    row['probabilities'] = analysis.probabilities(row['logits'], len(row['logits']))


class OwnershipAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes, cls.views, cls.expected, cls.raw = synthetic_fixture()
        cls.manifest = {'config_hash': 'SYNTHETIC_UNIT_TEST_ONLY',
                        'scientific_forwards': 500, 'planned_input_tokens': 188797}

    def test_complete_grid_validation_rejects_scope_score_and_order_corruption(self):
        analysis.validate_raw(self.raw, self.expected, self.manifest)
        with self.assertRaises(ValueError):
            analysis.validate_raw(self.raw[:-1], self.expected, self.manifest)
        for key, value in (('query_id', self.raw[1]['query_id']), ('config_hash', 'wrong'),
                           ('split', 'reserved_test'),
                           ('candidate_mass', float('nan')), ('latency_s', -1),
                           ('probabilities', [float('nan')] * len(self.raw[0]['order'])),
                           ('prediction', 'FOREIGN'), ('forward_index', 99), ('ok', False)):
            corrupted = [dict(row) for row in self.raw]
            corrupted[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                analysis.validate_raw(corrupted, self.expected, self.manifest)
        swapped = list(self.raw)
        swapped[0], swapped[1] = swapped[1], swapped[0]
        with self.assertRaises(ValueError):
            analysis.validate_raw(swapped, self.expected, self.manifest)

    def test_direct_means_align_semantics_and_ties_use_declared_action_order(self):
        rows = [{'order': ['ALLOW', 'DENY', 'INSUFFICIENT'], 'probabilities': [.1, .8, .1]},
                {'order': ['DENY', 'INSUFFICIENT', 'ALLOW'], 'probabilities': [.8, .1, .1]}]
        distribution = analysis.direct_distribution(rows)
        self.assertEqual(max(analysis.ACTION_ORDER, key=distribution.get), 'DENY')
        self.assertAlmostEqual(distribution['DENY'], .8)
        tie = analysis.direct_distribution([{'order': list(reversed(analysis.ACTION_ORDER)),
                                            'probabilities': [1 / 3] * 3}])
        self.assertEqual(max(analysis.ACTION_ORDER, key=tie.get), 'ALLOW')

    def test_paired_endpoints_controls_and_cost_sharing_are_not_raw_count_accuracy(self):
        result = analysis.derive(self.raw, self.scenes, self.views)
        summary = result['summary']
        self.assertEqual(summary['status'], 'in_memory_derivation_provenance_not_yet_validated')
        self.assertEqual((summary['parent_pairs'], summary['views'], summary['scientific_forwards']), (24, 48, 500))
        self.assertEqual(summary['unique_scientific_input_tokens'], 188797)
        self.assertEqual(summary['methods']['joint_gated']['complete_pairs_correct'], 24)
        self.assertEqual(summary['methods']['known_grammar']['complete_pairs_correct'], 24)
        self.assertEqual(summary['methods']['always_defer']['correct_decisions'], 12)
        self.assertEqual(summary['methods']['always_defer']['complete_pairs_correct'], 0)
        self.assertIsNone(summary['methods']['known_grammar']['summed_saved_forward_latency_s'])
        self.assertEqual(summary['joint_gated_cost']['underlying_saved_forwards'], 200)
        self.assertEqual(summary['joint_gated_cost']['projected_retained_forwards'], 100)
        self.assertEqual(summary['joint_gated_cost']['projected_retained_input_tokens'], 42627)
        self.assertFalse(summary['joint_gated_cost']['new_skipped_inference_run'])
        self.assertEqual(summary['gate_audit']['target_retained'], 100)
        self.assertEqual(summary['gate_audit']['foreign_accepted'], 0)
        self.assertEqual((len(result['decisions']), len(result['fact_claims']), len(result['line_audits']),
                          len(result['pair_outcomes'])), (384, 224, 400, 192))
        self.assertTrue(all(not row['absence_certified'] for row in result['fact_claims']))
        for relation in summary['strata']['id_relation'].values():
            self.assertEqual(relation['joint_full']['parent_pairs'], 12)
            self.assertEqual(relation['joint_full']['views'], 24)

    def test_gate_regression_is_retained_when_foreign_evidence_compensates_a_target_error(self):
        raw = copy.deepcopy(self.raw)
        view = next(v for v in self.views if v['family'] == 'route_lookup'
                    and v['pair_kind'] == 'determined_determined' and v['target_slot'] == 0)
        scene = next(s for s in self.scenes if s['parent'] == view['parent'])
        target = scene['ids'][view['target_slot']]
        for row in raw:
            if row['view_id'] != view['view_id'] or row['arm'] != 'joint_full':
                continue
            record = scene['records'][row['line_index']]
            if record['scope'] == target and record['field'] == 'route':
                # Miss the real route; the foreign route temporarily supplies the same value.
                replacement = analysis.NO_OBSERVATION
            elif record['scope'] != target and record['field'] != 'route':
                replacement = analysis.OTHER_REQUEST
            else:
                replacement = record['field'] + (':POSITIVE' if record['value'] else ':NEGATIVE')
            replace_prediction(row, replacement)
        result = analysis.derive(raw, self.scenes, self.views)
        changed = [row for row in result['case_changes'] if row['view_id'] == view['view_id']
                   and row['candidate'] == 'joint_gated' and row['baseline'] == 'joint_full']
        self.assertEqual(len(changed), 1)
        self.assertEqual(changed[0]['transition'], 'regression')
        self.assertEqual(changed[0]['after'], 'INSUFFICIENT')

    def test_construction_metadata_changes_grading_not_visible_predictions(self):
        original = analysis.derive(self.raw, self.scenes, self.views)
        poisoned = copy.deepcopy(self.scenes)
        for scene in poisoned:
            for record in scene['records']:
                record['value'] = not record['value']
        altered = analysis.derive(self.raw, poisoned, self.views)
        self.assertEqual([(r['method'], r['view_id'], r['prediction']) for r in original['decisions']],
                         [(r['method'], r['view_id'], r['prediction']) for r in altered['decisions']])
        self.assertNotEqual([r['reference_status'] for r in original['fact_claims']],
                            [r['reference_status'] for r in altered['fact_claims']])

    def test_fixture_helpers_do_not_write_scientific_results(self):
        out = HERE / 'results/v0.1'
        before = {p.name: p.read_bytes() for p in out.iterdir()} if out.exists() else None
        result = analysis.derive(self.raw, self.scenes, self.views)
        content = analysis.serialized(result)
        self.assertEqual(set(content), {'summary.json', 'decisions.jsonl', 'fact_claims.jsonl',
                                        'line_audits.jsonl', 'pair_outcomes.jsonl', 'case_changes.jsonl'})
        after = {p.name: p.read_bytes() for p in out.iterdir()} if out.exists() else None
        self.assertEqual(before, after)

    def test_pair_guard_rejects_wrong_units_before_prediction(self):
        analysis.validate_pairs(self.scenes, self.views)
        invalid = []
        duplicate_scene = copy.deepcopy(self.scenes)
        duplicate_scene[1] = copy.deepcopy(duplicate_scene[0])
        invalid.append((duplicate_scene, self.views))
        for mutation in ('duplicate_id', 'duplicate_target', 'different_records', 'wrong_parent', 'same_action'):
            views = copy.deepcopy(self.views)
            if mutation == 'duplicate_id':
                views[1]['view_id'] = views[0]['view_id']
            elif mutation == 'duplicate_target':
                views[1]['state'] = views[0]['state']
            elif mutation == 'different_records':
                views[1]['state'] += '\nReviewer A approves request request-ABCDE.'
            elif mutation == 'wrong_parent':
                views[1]['parent'] = views[2]['parent']
            else:
                # Swap labels across parents to preserve overall label denominators.
                views[1]['gold'], views[3]['gold'] = views[3]['gold'], views[1]['gold']
            invalid.append((self.scenes, views))
        for index, (scenes, views) in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(ValueError):
                # Empty raw input proves the pair guard fires before score lookup.
                analysis.derive([], scenes, views)

    def test_generic_module_names_cannot_shadow_ownership_dependencies(self):
        with patch.dict(sys.modules, {'prepare': types.ModuleType('unrelated_prepare'),
                                      'execution': types.ModuleType('unrelated_execution')}):
            definition = importlib.util.spec_from_file_location('ownership_isolated_test', HERE / 'analyze.py')
            module = importlib.util.module_from_spec(definition)
            definition.loader.exec_module(module)
            self.assertEqual(module.execution.HERE, HERE)
            self.assertEqual(module.prepare.HERE, HERE)
            self.assertEqual(len(module.prepare.material()[1]), 48)


if __name__ == '__main__':
    unittest.main()
