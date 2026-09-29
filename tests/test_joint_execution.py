import copy
import json
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from data_tools import original_cases
from joint_analyze import (conditional_probabilities, direct_choice,
                           route_audit, validate_raw)
from joint_execution import ENCODED, SEED, verify_frozen
from joint_route import NO_OBSERVATION


class JointExecutionPreparationTests(unittest.TestCase):
    def test_source_and_encoded_grid_are_complete_without_inference(self):
        manifest = verify_frozen()
        self.assertEqual((manifest['scientific_forwards'], manifest['joint_input_tokens'],
                          manifest['direct_union_input_tokens']), (514, 95889, 95849))
        self.assertEqual(manifest['paid_api_calls'], 0)
        self.assertEqual(manifest['rewrite_model_records'], 0)
        rows = [json.loads(line) for line in ENCODED.read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len({row['query_id'] for row in rows}), 514)
        self.assertTrue(all(row['source_id'] not in row['prompt'] for row in rows))

    def test_direct_ensemble_aligns_semantics_not_letter_positions(self):
        rows = [{'order': ['ALLOW', 'DENY', 'INSUFFICIENT'],
                 'probabilities': [0.6, 0.3, 0.1]},
                {'order': ['DENY', 'INSUFFICIENT', 'ALLOW'],
                 'probabilities': [0.2, 0.1, 0.7]}]
        self.assertEqual(direct_choice(rows), 'ALLOW')

    def test_raw_validator_rejects_score_and_prompt_corruption(self):
        manifest = verify_frozen()
        encoded = [json.loads(line) for line in ENCODED.read_text(encoding='utf-8').splitlines()]
        ordered = copy.deepcopy(encoded)
        random.Random(SEED).shuffle(ordered)
        # Deliberate software fixtures; these are not run-model outputs.
        raw = []
        for number, plan in enumerate(ordered, 1):
            width = len(plan['order'])
            logits = [0.0] * width
            probs = conditional_probabilities(logits, width) if plan['arm'] == 'joint' else [1/3] * 3
            raw.append(plan | {'config_hash': manifest['config_hash'],
                               'forward_index': number, 'ok': True,
                               'input_tokens': len(plan['token_ids']),
                               'latency_s': 0.0, 'candidate_mass': 0.1,
                               'logits': logits, 'probabilities': probs,
                               'prediction': plan['order'][0]})
        validate_raw(raw, encoded, manifest)
        wrong = copy.deepcopy(raw)
        wrong[0]['prompt'] += ' altered'
        with self.assertRaises(ValueError):
            validate_raw(wrong, encoded, manifest)
        wrong = copy.deepcopy(raw)
        wrong[0]['logits'][0] = float('nan')
        with self.assertRaises(ValueError):
            validate_raw(wrong, encoded, manifest)

    def test_program_route_audit_keeps_distinct_error_classes(self):
        case = next(c for c in original_cases() if c['id'] == 'joint_approval-1-full')
        def audit(index, prediction):
            return route_audit(case, {'line_index': index, 'prediction': prediction,
                                      'evidence_span': {'text': 'fixture'}})['program_audit']
        self.assertEqual(audit(2, 'review_b:NEGATIVE'), 'wrong_request')
        self.assertEqual(audit(0, 'review_b:POSITIVE'), 'wrong_field')
        self.assertEqual(audit(0, 'review_a:NEGATIVE'), 'wrong_polarity')
        self.assertEqual(audit(0, NO_OBSERVATION), 'missed_relevant')
        self.assertEqual(audit(0, 'review_a:POSITIVE'), 'correct_route')


if __name__ == '__main__':
    unittest.main()
