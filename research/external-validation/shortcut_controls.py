"""Transparent non-model controls, not general natural-language rule reasoning."""
from action_interface import ACTIONS

CONTROL_NAMES = tuple('constant_' + action for action in ACTIONS) + ('copy_last_history_answer',)


def last_answer(state):
    history = state['history']
    if not history:
        return 'ASK'
    value = history[-1]['follow_up_answer'].strip().casefold()
    return {'yes': 'Yes', 'no': 'No'}.get(value, 'ASK')


def predict_controls(items):
    """Input is ID plus visible state only. Return separate conditions, no scores.

    The last-answer shortcut deliberately ignores rule meaning and questions.
    Non-yes/no answers and empty history fall back to ASK. This is a heuristic,
    not an entailment judgment or an automatic reference label.
    """
    output = {name: [] for name in CONTROL_NAMES}
    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {'item_id', 'state'}:
            raise ValueError('Controls require only item_id and visible state')
        ident, state = item['item_id'], item['state']
        if not isinstance(ident, str) or not ident.strip() or ident in seen:
            raise ValueError('Missing or duplicate control item ID')
        if (not isinstance(state, dict) or set(state) != {'snippet', 'question', 'scenario', 'history'} or
                any(not isinstance(state[k], str) for k in ('snippet', 'question', 'scenario')) or
                not isinstance(state['history'], list)):
            raise ValueError('Invalid visible state')
        for turn in state['history']:
            if (not isinstance(turn, dict) or set(turn) != {'follow_up_question', 'follow_up_answer'} or
                    any(not isinstance(v, str) for v in turn.values())):
                raise ValueError('Invalid visible history')
        seen.add(ident)
        for action in ACTIONS:
            output['constant_' + action].append({'item_id': ident, 'action': action})
        output['copy_last_history_answer'].append({'item_id': ident, 'action': last_answer(state)})
    if not seen:
        raise ValueError('Empty control cohort')
    for rows in output.values():
        rows.sort(key=lambda row: row['item_id'])
    return output
