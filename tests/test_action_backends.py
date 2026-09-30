import copy
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/action-backends'
spec = importlib.util.spec_from_file_location('four_action_adapters', HERE/'adapters.py')
adapters = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapters)


class TokenizerFixture:
    eos_token_id = 248046
    def decode(self, ids, **kwargs):
        table = {1:'{"action":"Yes"}', 2:'reason\n</think>\n', 3:'```json\n{"action":"ASK"}\n```',
                 4:'<think>', 5:'</think>', 6:'<|im_start|>', 248046:'<|im_end|>'}
        return ''.join(table[i] for i in ids)


class ActionBackendTests(unittest.TestCase):
    def fixture(self):
        return {'model':'jev-1.13.0','answers':{'decision':{'type':'choice','choice':'D',
                'probabilities':{'A':.1,'B':.1,'C':.1,'D':.7},'confidence':.5}},
                'usage':{'input_tokens':20,'output_tokens':4}}

    def test_semantic_remapping_preserves_every_probability(self):
        orders = [('Yes','No','Irrelevant','ASK'), ('ASK','Irrelevant','No','Yes')]
        for order in orders:
            parsed = adapters.jev_response(self.fixture(), order)
            self.assertEqual(parsed['action'], order[3])
            self.assertEqual(parsed['probabilities'], dict(zip(order, [.1,.1,.1,.7])))
            request = adapters.jev_request({'selected_action':'Yes'}, 'copy', order)
            self.assertEqual(list(request['questions']['decision']['criteria']), list('ABCD'))

    def test_reject_probability_nan_boolean_sum_and_wrong_choice(self):
        for value in (float('nan'), float('inf'), True, -1, 1.1):
            data = self.fixture(); data['answers']['decision']['probabilities']['A'] = value
            with self.assertRaises(ValueError): adapters.jev_response(data, ('Yes','No','Irrelevant','ASK'))
        for changes in ({'choice':'A'}, {'probabilities':{'A':.2,'B':.2,'C':.2,'D':.7}}, {'confidence':True}):
            data = self.fixture(); data['answers']['decision'].update(changes)
            with self.assertRaises(ValueError): adapters.jev_response(data, ('Yes','No','Irrelevant','ASK'))

    def test_reject_version_missing_labels_and_invalid_usage(self):
        for modify in (lambda d: d.update(model='jev-latest'),
                       lambda d: d['answers']['decision']['probabilities'].pop('A'),
                       lambda d: d['usage'].update(input_tokens=True),
                       lambda d: d['usage'].pop('output_tokens')):
            data = self.fixture(); modify(data)
            with self.assertRaises(ValueError): adapters.jev_response(data, ('Yes','No','Irrelevant','ASK'))

    def adapted(self, ids, thinking=False, cap=10):
        prompt = '<|im_start|>assistant\n<think>\n' + ('' if thinking else '\n</think>\n\n')
        return adapters.qwen_final(TokenizerFixture(), ids, thinking=thinking,
                                  rendered_prompt=prompt, max_new_tokens=cap)

    def test_final_boundary_excludes_reasoning_and_accepts_eos_at_cap(self):
        self.assertEqual(self.adapted([1,248046], cap=2)['parsed']['action'], 'Yes')
        result = self.adapted([2,3,248046], thinking=True)
        self.assertEqual(result['parsed']['action'], 'ASK')
        self.assertNotIn('reason', result['final_text'])

    def test_invalid_eos_and_boundary_never_yield_an_action(self):
        for ids, thinking in (([1],False), ([1,248046,1],False),
                              ([1,248046,248046],False), ([1,248046],True),
                              ([2,5,1,248046],True), ([4,2,1,248046],True),
                              ([2,1,248046],False), ([6,1,248046],False)):
            self.assertFalse(self.adapted(ids,thinking)['parsed']['accepted'], (ids,thinking))
        self.assertEqual(self.adapted([1],cap=1)['completion'], 'length')

    def test_unexpected_template_and_invalid_ids_rejected(self):
        with self.assertRaises(ValueError):
            adapters.qwen_final(TokenizerFixture(), [1,248046], thinking=False,
                                rendered_prompt='unverified prompt', max_new_tokens=8)
        for ids in ([True], [-1], [1,1,1]):
            with self.assertRaises(ValueError): self.adapted(ids,cap=2)


if __name__ == '__main__': unittest.main()
