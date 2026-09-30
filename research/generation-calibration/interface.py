"""Strict final-answer parsing and standard generated-token presence penalty."""
import json


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def parse_final(text, thinking, ended_with_eos):
    if not ended_with_eos:
        return {'status': 'incomplete', 'answer': None}
    if not text.endswith('<|im_end|>') or text.count('<|im_end|>') != 1:
        return {'status': 'bad_termination_text', 'answer': None}
    body = text[:-len('<|im_end|>')]
    if thinking:
        if body.count('</think>') != 1 or '<think>' in body:
            return {'status': 'bad_thinking_boundary', 'answer': None}
        body = body.split('</think>', 1)[1]
    elif '<think>' in body or '</think>' in body:
        return {'status': 'unexpected_thinking', 'answer': None}
    try:
        obj = json.loads(body.strip(), object_pairs_hook=unique_object)
    except (ValueError, TypeError):
        return {'status': 'invalid_json', 'answer': None}
    if not isinstance(obj, dict) or set(obj) != {'answer'} or obj['answer'] not in ('A', 'B', 'C'):
        return {'status': 'invalid_schema', 'answer': None}
    return {'status': 'valid', 'answer': obj['answer']}


class GeneratedPresencePenalty:
    """Subtract alpha once per distinct generated token, excluding the prompt.

    Standard presence-penalty semantics, independently implemented. See vLLM
    v0.11.0 model_executor/layers/utils.py apply_penalties as a semantic reference.
    No upstream source is copied. Batch support is tested; this run uses batch 1.
    """
    def __init__(self, prompt_length, alpha=1.5):
        if prompt_length < 0 or not 0 <= alpha <= 2:
            raise ValueError('Invalid presence-penalty configuration')
        self.prompt_length = prompt_length
        self.alpha = alpha

    def __call__(self, input_ids, scores):
        import torch
        updated = scores.clone()
        for row in range(input_ids.shape[0]):
            seen = torch.unique(input_ids[row, self.prompt_length:])
            updated[row, seen] -= self.alpha
        return updated
