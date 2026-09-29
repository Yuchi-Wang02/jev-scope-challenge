import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from line_plan_tools import MANIFEST, PLANS, expected, run


class LinePlanToolsTests(unittest.TestCase):
    def test_public_preparation_matches_generated_prompts_and_is_read_only(self):
        before = (PLANS.read_bytes(), MANIFEST.read_bytes())
        self.assertEqual(before, expected())
        report = run('verify')
        self.assertEqual(report['planned_queries'], 1096)
        self.assertEqual(report['model_forwards'], 0)
        self.assertEqual(before, (PLANS.read_bytes(), MANIFEST.read_bytes()))
        manifest = json.loads(before[1])
        self.assertEqual(manifest['status'], 'unscored_preparation_not_execution_freeze')
        self.assertEqual(manifest['rewrite_or_reserved_queries'], 0)


if __name__ == '__main__':
    unittest.main()
