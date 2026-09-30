import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/external-validation'))
from action_interface import ACTIONS, parse_final, validate_option_order


class RuleActionInterfaceTests(unittest.TestCase):
    def parse(self, text, completion='natural_eos'):
        return parse_final(text, completion=completion)

    def test_all_actions_and_allowed_wrappers_have_same_semantics(self):
        for action in ACTIONS:
            raw = '{"action":"' + action + '"}'
            for text in (raw, ' \n' + raw + '\t', '```json\n' + raw + '\n```',
                         '\n```json\r\n' + raw + '\r\n```\n'):
                result = self.parse(text)
                self.assertTrue(result.accepted, text)
                self.assertEqual(result.action, action)
                self.assertEqual(result.strict_json, not text.strip().startswith('```'))

    def test_does_not_pick_answer_from_reasoning_or_multiple_candidates(self):
        for text in ('I think Yes. {"action":"Yes"}',
                     '<think>{"action":"No"}</think>{"action":"Yes"}',
                     '{"action":"Yes"}\n{"action":"No"}',
                     '```json\n{"action":"Yes"}\n```\nActually No.',
                     '```json\n{"action":"Yes"}\n```\n```json\n{"action":"No"}\n```'):
            self.assertFalse(self.parse(text).accepted, text)

    def test_schema_cannot_coerce_or_discard_information(self):
        for text in ('{"action":"Yes","action":"No"}',
                     '{"action":"Yes","action":"Yes"}',
                     '{"action":"Yes","reason":"x"}', '[{"action":"Yes"}]',
                     '"Yes"', 'null', '{}', '{"action":true}', '{"action":1}',
                     '{"action":NaN}', '{"action":["Yes"]}', '{"action":" yes "}',
                     '{"action":"YES"}', '{"action":"UNCLEAR"}'):
            self.assertFalse(self.parse(text).accepted, text)

    def test_incomplete_and_unknown_termination_never_accepts_valid_json(self):
        for completion in ('length', 'error', 'unknown', 'stop', None, True):
            self.assertFalse(self.parse('{"action":"Yes"}', completion).accepted)
        for text in ('{"action":"Yes"', '```json\n{"action":"Yes"}', ''):
            self.assertFalse(self.parse(text).accepted)

    def test_fence_contract_does_not_repair_other_markup(self):
        for text in ('```\n{"action":"Yes"}\n```',
                     '```JSON\n{"action":"Yes"}\n```',
                     '```json {"action":"Yes"}```',
                     '~~~json\n{"action":"Yes"}\n~~~'):
            self.assertFalse(self.parse(text).accepted, text)

    def test_mapping_validates_full_semantic_permutation(self):
        self.assertEqual(validate_option_order(list(reversed(ACTIONS))), tuple(reversed(ACTIONS)))
        for values in (['Yes'] * 4, ['Yes', 'No', 'ASK'], 'Yes,No,Irrelevant,ASK',
                       ['Yes', 'No', 'Irrelevant', 'UNCLEAR'], ['Yes', 'No', 'ASK', None]):
            with self.assertRaises(ValueError):
                validate_option_order(values)


if __name__ == '__main__':
    unittest.main()
