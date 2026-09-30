"""Pure generated-output contract; no tokenizer, model or network imports."""
from collections import Counter
from itertools import permutations

LABELS=('yes','no','maybe')
ORDERS=tuple(permutations(LABELS))


def parse_generated(body, *, arm, options, ended_eos, unsupported_special=False):
    if arm not in ('letter','semantic') or tuple(options) not in ORDERS:
        raise ValueError('Unknown output contract')
    if not isinstance(body,str) or type(ended_eos)!=bool or type(unsupported_special)!=bool:
        raise ValueError('Invalid adapter inputs')
    if not ended_eos:return {'action':None,'invalid_reason':'not_eos_terminated'}
    if unsupported_special:return {'action':None,'invalid_reason':'unsupported_special_token'}
    value=body.strip()
    if arm=='letter' and value in ('A','B','C'):
        return {'action':options['ABC'.index(value)],'invalid_reason':None}
    if arm=='semantic' and value in LABELS:
        return {'action':value,'invalid_reason':None}
    return {'action':None,'invalid_reason':'exact_output_contract'}


def strict_majority(actions):
    if len(actions)!=6 or any(x is not None and x not in LABELS for x in actions):
        raise ValueError('Need six mapped decisions including invalids')
    counts=Counter(x for x in actions if x is not None)
    winners=[x for x,n in counts.items() if n>=4]
    return winners[0] if winners else None
