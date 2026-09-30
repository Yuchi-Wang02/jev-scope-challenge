"""Ownership-switch construction, leakage boundary and unique query accounting."""
import importlib.util
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/request-ownership'
MODULE_SPEC = importlib.util.spec_from_file_location('ownership_prepare', HERE / 'prepare.py')
ownership = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(ownership)


class OwnershipPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes, cls.views = ownership.material()
        cls.queries = ownership.plans(cls.views)

    def test_target_switch_keeps_record_block_and_policy_and_changes_reference(self):
        self.assertEqual((len(self.scenes), len(self.views)), (24, 48))
        for scene in self.scenes:
            a, b = [v for v in self.views if v['parent'] == scene['parent']]
            self.assertEqual(a['state'].split('\n', 1)[1], b['state'].split('\n', 1)[1])
            self.assertEqual(a['policy'], b['policy'])
            self.assertNotEqual(a['gold'], b['gold'])
            self.assertNotEqual(a['state'].splitlines()[0], b['state'].splitlines()[0])
            for view in (a, b):
                parsed = ownership.parse_text(view['state'], view['policy'], scene['family'], scene['sites'])
                self.assertEqual(ownership.world_truth(parsed), (view['gold'], view['legal_worlds']))
                self.assertEqual(ownership.direct_truth(parsed), view['gold'])

    def test_same_prefix_similarity_and_action_balance_are_not_owner_shortcuts(self):
        for family in ownership.FAMILIES:
            scenes = [s for s in self.scenes if s['family'] == family]
            self.assertEqual(Counter(s['pair_kind'] for s in scenes),
                             {'determined_determined': 4, 'determined_insufficient': 4})
            self.assertEqual(Counter(s['first_owner_slot'] for s in scenes), {0: 4, 1: 4})
            self.assertEqual(Counter(s['id_relation'] for s in scenes),
                             {'one_character_near': 4, 'all_characters_distant': 4})
            for relation in ('one_character_near', 'all_characters_distant'):
                self.assertEqual(Counter(s['first_owner_slot'] for s in scenes
                                         if s['id_relation'] == relation), {0: 2, 1: 2})
            determined = [s for s in scenes if s['pair_kind'] == 'determined_determined']
            self.assertEqual(Counter(s['construction_actions'][s['first_owner_slot']]
                                     for s in determined), {'ALLOW': 2, 'DENY': 2})
            for slot in (0, 1):
                self.assertEqual(Counter(v['gold'] for v in self.views
                                         if v['family'] == family and v['target_slot'] == slot),
                                 {'ALLOW': 3, 'DENY': 3, 'INSUFFICIENT': 2})
        for scene in self.scenes:
            a, b = scene['ids']
            self.assertTrue(a.startswith('request-') and b.startswith('request-'))
            self.assertEqual(len(a), len(b))
            self.assertEqual(sum(x != y for x, y in zip(a, b)),
                             1 if scene['id_relation'] == 'one_character_near' else 5)

    def test_visible_filter_uses_exact_owner_and_preserves_reference_action(self):
        totals = Counter()
        for view in self.views:
            filtered, gates = ownership.filtered_state(view['state'])
            totals.update(gate['status'] for gate in gates)
            scene = next(s for s in self.scenes if s['parent'] == view['parent'])
            parsed = ownership.parse_text(filtered, view['policy'], scene['family'], scene['sites'])
            self.assertEqual(ownership.world_truth(parsed)[0], view['gold'])
            self.assertTrue(all(record['scope'] == parsed['target'] for record in parsed['records']))
        self.assertEqual(totals, {'KEEP': 100, 'DROP': 100})

    def test_similarity_is_crossed_with_first_action_and_observation_pattern(self):
        for family in ownership.FAMILIES:
            for kind in ('determined_determined', 'determined_insufficient'):
                expected_first = ({'ALLOW': 1, 'DENY': 1} if kind == 'determined_determined'
                                  else {'DENY': 1, 'INSUFFICIENT': 1})
                missing_by_relation = {}
                routes_by_relation = {}
                for relation in ('one_character_near', 'all_characters_distant'):
                    group = [s for s in self.scenes if s['family'] == family
                             and s['pair_kind'] == kind and s['id_relation'] == relation]
                    self.assertEqual(len(group), 2)
                    self.assertEqual(Counter(s['construction_actions'][s['first_owner_slot']]
                                             for s in group), expected_first)
                    self.assertEqual(Counter(s['observation_pattern'] for s in group), {0: 1, 1: 1})
                    # Read actual constructed records, not just pattern metadata.
                    if kind == 'determined_insufficient':
                        missing = Counter()
                        for scene in group:
                            uncertain_id = scene['ids'][scene['construction_actions'].index('INSUFFICIENT')]
                            present = {r['field'] for r in scene['records'] if r['scope'] == uncertain_id}
                            fields = {'joint_approval': {'review_a', 'review_b'},
                                      'reversal_exception': {'base', 'exception'},
                                      'route_lookup': {'route', 'site_a', 'site_b'}}[family]
                            missing.update(fields - present)
                        missing_by_relation[relation] = missing
                    if family == 'route_lookup':
                        routes_by_relation[relation] = Counter(r['value'] for s in group
                                                               for r in s['records'] if r['field'] == 'route')
                if kind == 'determined_insufficient':
                    self.assertEqual(missing_by_relation['one_character_near'],
                                     missing_by_relation['all_characters_distant'])
                    expected_missing = {'joint_approval': {'review_a': 1, 'review_b': 1},
                                        'reversal_exception': {'base': 1, 'exception': 1},
                                        'route_lookup': {'route': 2}}[family]
                    self.assertEqual(missing_by_relation['one_character_near'], expected_missing)
                if family == 'route_lookup':
                    self.assertEqual(routes_by_relation['one_character_near'],
                                     routes_by_relation['all_characters_distant'])
                    n = 2 if kind == 'determined_determined' else 1
                    self.assertEqual(routes_by_relation['one_character_near'], {True: n, False: n})

    def test_prompt_builder_does_not_accept_or_use_gold_metadata(self):
        original = ownership.plans(self.views)
        poisoned = [dict(view, gold='SECRET_GOLD_SENTINEL', target_slot=-999,
                         family='SECRET_FAMILY_SENTINEL', pair_kind='SECRET_PAIR_SENTINEL',
                         records=[{'scope': 'SECRET_SCOPE_SENTINEL'}]) for view in self.views]
        self.assertEqual(original, ownership.plans(poisoned))
        for view in self.views:
            visible = ownership.visible_plans(view['state'], view['policy'])
            self.assertTrue(visible)
            for row in visible:
                for forbidden in ('gold', 'family', 'pair_kind', 'parent', 'target_slot', 'records'):
                    self.assertNotIn(forbidden, row)
                self.assertNotIn(view['view_id'], row['prompt'])

    def test_unique_query_grid_and_single_anchors_are_subsets(self):
        self.assertEqual(len(self.queries), 500)
        self.assertEqual(len({q['query_id'] for q in self.queries}), 500)
        self.assertEqual(Counter(q['arm'] for q in self.queries),
                         {'joint_full': 200, 'direct_full': 200, 'direct_filtered': 100})
        for view in self.views:
            rows = [q for q in self.queries if q['view_id'] == view['view_id']]
            self.assertEqual(sum(q['arm'] == 'joint_full' for q in rows),
                             sum(q['arm'] == 'direct_full' for q in rows))
            for arm in ('direct_full', 'direct_filtered'):
                subset = [q for q in rows if q['arm'] == arm]
                self.assertEqual(sum(q['mapping'] == 0 for q in subset), 1)
                self.assertEqual(len({tuple(q['order']) for q in subset}), len(subset))

    def test_generated_artifacts_and_optional_token_encodings_are_unscored(self):
        data, manifest = ownership.artifacts()
        ownership.check_or_write(data, False)
        self.assertFalse(manifest['execution_ready'])
        self.assertEqual(manifest['actual_model_forwards'], 0)
        self.assertEqual(manifest['independent_human_annotations'], 0)
        if (HERE / 'preparation/encoded_queries.jsonl').exists():
            encoded, token_manifest = ownership.encoded_artifacts()
            ownership.check_or_write(encoded, False)
            self.assertEqual(token_manifest['planned_queries'], 500)
            self.assertEqual(token_manifest['actual_model_forwards'], 0)


if __name__ == '__main__':
    unittest.main()
