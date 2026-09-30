"""Prospective decision-only Jev readout; raw probability anomalies stay visible."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'action-backends'))
from adapters import MODEL, probability, validate_option_order


def adapt(raw, http_status, options, latency):
    options = validate_option_order(options)
    detail = {'http_status': http_status, 'raw_response': raw,
              'readout': 'native_choice_with_separate_probability_quality_v1'}
    result = {'status': 'protocol_error', 'action': None, 'input_tokens': None,
              'output_tokens': None, 'latency_seconds': latency, 'detail': detail}
    usage = raw.get('usage', {}) if isinstance(raw, dict) else {}
    if isinstance(usage, dict):
        for name in ('input_tokens', 'output_tokens'):
            if type(usage.get(name)) == int and usage[name] >= 0:
                result[name] = usage[name]
    if http_status != 200:
        detail['error'] = 'http_failure'
        return result
    try:
        if not isinstance(raw, dict) or raw.get('model') != MODEL:
            raise ValueError('served_model_mismatch')
        answers = raw.get('answers')
        if not isinstance(answers, dict) or set(answers) != {'decision'}:
            raise ValueError('answer_keys')
        answer = answers['decision']
        if not isinstance(answer, dict) or answer.get('type') != 'choice':
            raise ValueError('choice_type')
        probs = answer.get('probabilities')
        if not isinstance(probs, dict) or set(probs) != set('ABCD'):
            raise ValueError('probability_keys')
        if not all(probability(v) for v in probs.values()) or sum(probs.values()) <= 0:
            raise ValueError('probability_values')
        choice = answer.get('choice')
        if not isinstance(choice, str) or choice not in probs or probs[choice] < max(probs.values()) - 1e-6:
            raise ValueError('choice_not_argmax')
        if not probability(answer.get('confidence')):
            raise ValueError('confidence')
        if result['input_tokens'] is None or result['output_tokens'] is None:
            raise ValueError('usage')
        total = sum(probs.values())
        detail['probability_quality'] = {'raw_sum': total,
            'within_original_sum_tolerance': abs(total - 1) <= 1e-4,
            'normalization_applied': False,
            'calibration_quality_established': False}
        detail['parsed'] = {'action': options['ABCD'.index(choice)],
            'probabilities': dict(zip(options, (probs[k] for k in 'ABCD'))),
            'confidence': answer['confidence'], 'input_tokens': result['input_tokens'],
            'output_tokens': result['output_tokens']}
        result.update(status='ok', action=detail['parsed']['action'])
    except (ValueError, TypeError, KeyError) as error:
        detail['error'] = 'schema_' + type(error).__name__
    return result
