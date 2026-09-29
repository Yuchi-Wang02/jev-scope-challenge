import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/fact-execution'
sys.path.insert(0, str(HERE))
from publish_line import DEST, payload, render


class LineExplorerTests(unittest.TestCase):
    def test_complete_saved_grid_and_real_wrong_request_example(self):
        data = payload()
        self.assertEqual(len(data['cases']), 72)
        self.assertEqual(sum(len(f['lines']) for c in data['cases'] for f in c['fields']), 548)
        self.assertEqual(data['selected_line_judgments'], 407)
        case = next(c for c in data['cases'] if c['id'] == 'joint_approval-1-decisive_missing')
        field = next(f for f in case['fields'] if f['name'] == 'review_b')
        wrong = next(line for line in field['lines'] if line['index'] == 2)
        self.assertEqual((wrong['model'], wrong['construction_reference'], wrong['error']),
                         ('NEGATIVE', 'IRRELEVANT', 'other_request'))
        self.assertEqual((case['prediction'], case['gold']), ('DENY', 'INSUFFICIENT'))

    def test_published_page_rebuilds_exactly_without_inference(self):
        actual = DEST.read_bytes().replace(b'\r\n', b'\n').decode('utf-8')
        self.assertEqual(actual, render())
        self.assertNotIn('__LINE_DATA__', actual)
        self.assertIn('This method failed its prewritten screening rule', actual)


if __name__ == '__main__':
    unittest.main()
