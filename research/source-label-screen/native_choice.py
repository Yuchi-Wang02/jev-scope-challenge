"""Final native-choice policy with separate, non-corrective metadata diagnostics."""
from decision_readout import MODEL, probability, validate_option_order


def adapt(raw, http_status, options, latency):
    options = validate_option_order(options)
    detail = {'http_status': http_status, 'raw_response': raw, 'readout': 'native_choice_final_v1'}
    result = {'status': 'protocol_error', 'action': None, 'input_tokens': None,
              'output_tokens': None, 'latency_seconds': latency, 'detail': detail}
    usage = raw.get('usage', {}) if isinstance(raw, dict) else {}
    if isinstance(usage, dict):
        for key in ('input_tokens', 'output_tokens'):
            if type(usage.get(key)) == int and usage[key] >= 0:
                result[key] = usage[key]
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
        choice = answer.get('choice')
        if not isinstance(choice, str) or choice not in 'ABCD' or len(choice) != 1:
            raise ValueError('choice_key')
        if result['input_tokens'] is None or result['output_tokens'] is None:
            raise ValueError('usage')
        probs = answer.get('probabilities')
        keys = isinstance(probs, dict) and set(probs) == set('ABCD')
        values = keys and all(probability(v) for v in probs.values())
        total = sum(probs.values()) if values else None
        top = [k for k, v in probs.items() if v == max(probs.values())] if values else []
        argmax = options['ABCD'.index(top[0])] if total and len(top) == 1 else None
        confidence_valid = probability(answer.get('confidence'))
        quality = {'probability_keys_valid': keys, 'probability_values_valid': values,
            'raw_sum': total, 'positive_total': bool(total) if values else False,
            'within_original_sum_tolerance': abs(total - 1) <= 1e-4 if values else False,
            'choice_is_displayed_argmax': choice in top if total else None,
            'unique_argmax_action': argmax, 'displayed_top_tie': len(top) > 1 if total else None,
            'confidence_valid': confidence_valid, 'normalization_applied': False,
            'calibration_quality_established': False}
        quality['all_original_metadata_checks_pass'] = bool(
            values and total and quality['within_original_sum_tolerance'] and
            probs[choice] >= max(probs.values()) - 1e-6 and confidence_valid)
        detail['metadata_quality'] = quality
        result.update(status='ok', action=options['ABCD'.index(choice)])
    except (ValueError, TypeError, KeyError) as error:
        detail['error'] = 'schema_' + type(error).__name__
    return result
