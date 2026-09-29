import csv
import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from review_pair_tools import fingerprint, inspect_csv
from review_starter import build


class ReviewStarterTests(unittest.TestCase):
    def test_starter_matches_frozen_pack_and_has_zero_judgments(self):
        outputs = build()
        for name, expected in outputs.items():
            actual = (HERE / 'review' / name).read_bytes().replace(b'\r\n', b'\n').decode('utf-8')
            self.assertEqual(actual, expected)
        blind = json.loads(outputs['starter_blind_pairs.json'])
        self.assertEqual(len(blind), 12)
        self.assertTrue(all(set(pair) == {'review_id', 'original_state', 'candidate_state', 'policy'}
                            for pair in blind))
        rows = list(csv.DictReader(io.StringIO(outputs['starter_blank.csv'])))
        self.assertEqual({row['review_id'] for row in rows},
                         {pair['review_id'] for pair in blind})
        self.assertEqual(inspect_csv(outputs['starter_blank.csv'], fingerprint())['submitted_rows'], 0)
        manifest = json.loads(outputs['starter_manifest.json'])
        self.assertFalse(manifest['statistical_sample'])
        self.assertEqual(manifest['model_scored_rewrites'], 0)


if __name__ == '__main__':
    unittest.main()
