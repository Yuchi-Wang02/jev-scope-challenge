"""Synthetic in-memory evidence tampering checks; no model result is fabricated."""
import copy
import math
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from fact_run import read_rows
from line_analyze import validate_raw
from line_run import ENCODED, SEED, verify_frozen


class LinePilotTests(unittest.TestCase):
    def test_committed_pre_inference_freeze_is_read_only(self):
        before = ENCODED.read_bytes()
        manifest = verify_frozen()
        self.assertEqual(manifest['planned_forwards'], 548)
        self.assertEqual(manifest['planned_input_tokens'], 133977)
        self.assertEqual(before, ENCODED.read_bytes())

    def test_raw_grid_rejects_prompt_logit_and_cost_tampering(self):
        manifest = verify_frozen()
        plans = read_rows(ENCODED)
        ordered = list(plans)
        random.Random(SEED).shuffle(ordered)
        values = [math.exp(1) / (math.exp(1) + 2),
                  1 / (math.exp(1) + 2), 1 / (math.exp(1) + 2)]
        synthetic = [p | {'arm': 'N1', 'config_hash': manifest['config_hash'],
                          'forward_index': i, 'ok': True,
                          'input_tokens': len(p['token_ids']), 'latency_s': 0.1,
                          'candidate_mass': 0.5, 'logits': [1, 0, 0],
                          'probabilities': values, 'prediction': p['order'][0]}
                     for i, p in enumerate(ordered, 1)]
        validate_raw(synthetic, plans, manifest)
        for key, bad in (('prompt', 'Changed prompt'), ('logits', [float('nan'), 0, 0]),
                         ('input_tokens', -1), ('forward_index', 9)):
            changed = copy.deepcopy(synthetic)
            changed[0][key] = bad
            with self.assertRaises(ValueError):
                validate_raw(changed, plans, manifest)
        with self.assertRaises(ValueError):
            validate_raw(synthetic[:-1], plans, manifest)


if __name__ == '__main__':
    unittest.main()
