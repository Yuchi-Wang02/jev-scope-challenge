"""Four-way Jev validation and token-grounded Qwen3.5 final extraction."""
import math
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'external-validation'))
from action_interface import parse_final, validate_option_order

MODEL = 'jev-1.13.0'


def jev_request(state, instructions, options):
    options = validate_option_order(options)
    return {'model': MODEL, 'state': state,
            'questions': {'decision': {'type': 'choice', 'instructions': instructions,
                          'criteria': {key: f'The selected action is exactly {value}.'
                                       for key, value in zip('ABCD', options)}}}}


def probability(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def jev_response(data, options):
    options = validate_option_order(options)
    if not isinstance(data, dict) or data.get('model') != MODEL:
        raise ValueError('served_model_mismatch')
    answers = data.get('answers')
    if not isinstance(answers, dict) or set(answers) != {'decision'}:
        raise ValueError('answer_keys')
    ans = answers['decision']
    if not isinstance(ans, dict) or ans.get('type') != 'choice':
        raise ValueError('choice_type')
    probs = ans.get('probabilities')
    if not isinstance(probs, dict) or set(probs) != set('ABCD'):
        raise ValueError('probability_keys')
    if not all(probability(v) for v in probs.values()) or abs(sum(probs.values()) - 1) > 1e-4:
        raise ValueError('probability_values')
    choice = ans.get('choice')
    if not isinstance(choice, str) or choice not in probs or probs[choice] < max(probs.values()) - 1e-6:
        raise ValueError('choice_not_argmax')
    if not probability(ans.get('confidence')):
        raise ValueError('confidence')
    usage = data.get('usage')
    if not isinstance(usage, dict) or any(type(usage.get(k)) != int or usage[k] < 0
                                        for k in ('input_tokens', 'output_tokens')):
        raise ValueError('usage')
    return {'action': options['ABCD'.index(choice)],
            'probabilities': dict(zip(options, (probs[k] for k in 'ABCD'))),
            'confidence': ans['confidence'], 'input_tokens': usage['input_tokens'],
            'output_tokens': usage['output_tokens']}


def qwen_final(tokenizer, output_ids, *, thinking, rendered_prompt, max_new_tokens):
    """One sequence, no padded batch. Pinned Qwen3.5 template/token boundaries.

    An EOS at the last allowed token counts as natural completion. The caller
    must not pass prompt IDs or a cleaned transcript as generated output.
    """
    ids = output_ids
    if not isinstance(thinking, bool) or type(max_new_tokens) != int or max_new_tokens < 1:
        raise ValueError('invalid_generation_metadata')
    if not isinstance(ids, list) or any(type(x) != int or x < 0 for x in ids) or len(ids) > max_new_tokens:
        raise ValueError('invalid_output_ids')
    eos = tokenizer.eos_token_id
    if eos != 248046 or tokenizer.decode([eos], skip_special_tokens=False) != '<|im_end|>':
        raise ValueError('unexpected_tokenizer_eos')
    suffix = '<|im_start|>assistant\n<think>\n' if thinking else '<|im_start|>assistant\n<think>\n\n</think>\n\n'
    if not rendered_prompt.endswith(suffix):
        raise ValueError('unexpected_generation_prompt')
    completion = 'natural_eos' if ids and ids[-1] == eos and ids.count(eos) == 1 else (
        'length' if len(ids) == max_new_tokens and eos not in ids else 'unknown')
    decoded = tokenizer.decode(ids, skip_special_tokens=False)
    result = {'completion': completion, 'boundary_error': None, 'final_text': None,
              'decoded_output': decoded, 'parsed': asdict(parse_final('', completion=completion))}
    if completion != 'natural_eos':
        return result
    body = tokenizer.decode(ids[:-1], skip_special_tokens=False)
    if thinking:
        if body.count('</think>') != 1 or '<think>' in body:
            result['boundary_error'] = 'invalid_thinking_boundary'
        else:
            body = body.split('</think>', 1)[1]
    elif '<think>' in body or '</think>' in body:
        result['boundary_error'] = 'unexpected_thinking_boundary'
    # Reject any unexpected special-token strings rather than deleting them.
    if result['boundary_error'] is None and any(marker in body for marker in ('<|', '|>')):
        result['boundary_error'] = 'unexpected_special_marker'
    if result['boundary_error']:
        result['parsed'] = asdict(parse_final('', completion='unknown'))
    else:
        result['final_text'] = body
        result['parsed'] = asdict(parse_final(body, completion=completion))
    return result
