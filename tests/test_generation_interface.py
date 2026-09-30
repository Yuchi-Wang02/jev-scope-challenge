"""Reject incomplete thoughts, ambiguous JSON, and bad development fixtures."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]/'research/generation-calibration'


def load(name):
    spec = importlib.util.spec_from_file_location('generation_calibration_'+name, ROOT/(name+'.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


I = load('interface'); P = load('prepare')


class GenerationInterfaceTests(unittest.TestCase):
    def test_no_credit_for_json_inside_unfinished_thought(self):
        self.assertEqual(I.parse_final('{"answer":"A"}', True, False)['status'], 'incomplete')
        self.assertIsNone(I.parse_final('{"answer":"A"}<|im_end|>', True, True)['answer'])

    def test_only_final_region_is_parsed(self):
        self.assertEqual(I.parse_final('{"answer":"B"}</think>\n{"answer":"A"}<|im_end|>', True, True)['answer'], 'A')
        self.assertEqual(I.parse_final('{"answer":"C"}<|im_end|>', False, True)['answer'], 'C')

    def test_reject_ambiguous_or_unrequested_json(self):
        bad = ['{"answer":"A","answer":"B"}', '{"answer":"A","reason":"x"}',
               '```json\n{"answer":"A"}\n```', '{"answer":"A"} trailing',
               '{"answer":"A"}{"answer":"B"}', '{"answer":null}',
               '[{"answer":"A"}]', '{"answer":"D"}']
        for text in bad:
            with self.subTest(text=text):
                self.assertIsNone(I.parse_final(text+'<|im_end|>', False, True)['answer'])

    def test_reject_extra_thinking_and_termination_markers(self):
        for text, thinking in [('</think>{"answer":"A"}', False),
                               ('</think></think>{"answer":"A"}', True),
                               ('<think>x</think>{"answer":"A"}', True),
                               ('{"answer":"A"}<|im_end|>', False)]:
            self.assertIsNone(I.parse_final(text+'<|im_end|>', thinking, True)['answer'])

    def test_references_and_fixed_budget(self):
        material = P.material()
        expected = dict(zip(['copy','threshold','missing','sum','intersection','latest',
                            'conjunction','minimum','lookup','count','alphabetical','nested'],
                           ['C','B','C','A','B','A','B','A','C','C','A','B']))
        self.assertEqual({x['id']: x['reference'] for x in material['cases']}, expected)
        self.assertEqual(len(material['calls']), len({x['id'] for x in material['calls']}))
        self.assertEqual(material['max_generated_tokens'], 55296)
        for c in material['cases']:
            self.assertEqual(c['prompt'].count(P.FORMAT), 1)
        self.assertEqual(material, json.loads((ROOT/'plan.json').read_text(encoding='utf-8')))
