"""Fixed label-copy interface checks; no ShARC records or research labels."""
import json
from pathlib import Path
from adapters import jev_request

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ACTIONS = ('Yes', 'No', 'Irrelevant', 'ASK')
INSTRUCTIONS = ('This is a technical label-copy check, not a policy judgment. '
                'Read the field selected_action in state and return exactly that action. '
                'Ignore the distractor_action field.')


def material():
    cases = [{'id': f'copy_{i}', 'state': {'selected_action': action,
              'distractor_action': ACTIONS[(i + 1) % 4]}, 'reference': action}
             for i, action in enumerate(ACTIONS)]
    jev = [{'id': f'{c["id"]}_order_{i}', 'case_id': c['id'], 'options': list(order),
            'request': jev_request(c['state'], INSTRUCTIONS, order)}
           for c in cases for i, order in enumerate((ACTIONS, tuple(reversed(ACTIONS))))]
    qwen = [{'id': f'{c["id"]}_{mode}', 'case_id': c['id'], 'thinking': thinking,
             'seed': 17, 'max_new_tokens': 2048 if thinking else 256,
             'prompt': INSTRUCTIONS + '\nstate: ' + json.dumps(c['state'], separators=(',', ':')) +
                '\nReturn only a JSON object with exactly one key "action" whose value is '
                'Yes, No, Irrelevant, or ASK. Put the object in your final answer.'}
            for c in cases for mode, thinking in (('direct', False), ('thinking', True))]
    return {'purpose': 'technical label-copy integration only; not research evaluation',
            'cases': cases, 'jev_calls': jev, 'qwen_calls': qwen,
            'max_http_attempts': 8, 'retries': 0, 'max_jev_input_tokens': 50000,
            'max_jev_planning_units': 50000,
            'planned_jev_utf8_bytes_plus_256': sum(len(json.dumps(j['request']).encode())+256 for j in jev),
            'max_local_calls': 8, 'max_local_input_tokens': 50000,
            'max_generated_tokens': 9216, 'local_generation_deadline_seconds': 600,
            'human_reviews': 0, 'source_dataset_items': 0}


if __name__ == '__main__':
    import sys
    if '--write' in sys.argv:
        (HERE/'plan.json').write_text(json.dumps(material(), indent=2)+'\n', encoding='utf-8', newline='\n')
    assert json.loads((HERE/'plan.json').read_text()) == material()
    print(json.dumps({'status': 'verified', 'http_attempt_cap': 8, 'local_call_cap': 8,
                      'purpose': 'technical interface only'}))
