import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/next-study'))
from code_reference import decide
from study import HERE,read_rows


class TextReferenceTests(unittest.TestCase):
    def test_parser_matches_structured_truth_on_all_frozen_renderings(self):
        for c in read_rows(HERE/'data/cases.jsonl'):
            self.assertEqual(decide(c['state']),c['gold'],c['id'])

    def test_unknown_and_conflicting_syntax_is_not_silently_accepted(self):
        self.assertIsNone(decide('Maybe grant access later; owner unclear.'))
        self.assertIsNone(decide('Request: enable notifications for account demo.\nCurrent instruction for account demo: enable notifications.\nCurrent instruction for account demo: disable notifications.'))


if __name__=='__main__':unittest.main()
