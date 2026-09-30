"""Three-class observations adapted from our frozen stage-attribution runner.

All six mappings are permitted. Semantic smoke correctness is not a gate.
"""
import math
from itertools import permutations
MODEL='jev-1.13.0'
LETTERS='ABC'
TOKEN_IDS=(32,33,34)
ORDERS=tuple(permutations(('yes','no','maybe')))
def options_checked(options):
    if tuple(options) not in ORDERS:raise ValueError('Unexpected mapping')
    return tuple(options)

def probability(x): return type(x) in (int,float) and math.isfinite(x) and 0<=x<=1


def adapt_jev(raw,status,options,latency):
    options=options_checked(options)
    detail={'http_status':status,'raw_response':raw,'readout':'three_class_native_choice_v1'}
    result={'status':'protocol_error','action':None,'input_tokens':None,'output_tokens':None,
            'latency_seconds':latency,'detail':detail}
    usage=raw.get('usage',{}) if isinstance(raw,dict) else {}
    if isinstance(usage,dict):
        for key in ('input_tokens','output_tokens'):
            if type(usage.get(key))==int and usage[key]>=0: result[key]=usage[key]
    try:
        if status!=200: raise ValueError('http_failure')
        if not isinstance(raw,dict) or raw.get('model')!=MODEL: raise ValueError('served_model')
        answers=raw.get('answers')
        if not isinstance(answers,dict) or set(answers)!={'decision'}: raise ValueError('answer_keys')
        answer=answers['decision']
        if not isinstance(answer,dict) or answer.get('type')!='choice': raise ValueError('answer_type')
        choice=answer.get('choice')
        if not isinstance(choice,str) or len(choice)!=1 or choice not in LETTERS: raise ValueError('choice')
        if result['input_tokens'] is None or result['output_tokens'] is None: raise ValueError('usage')
        p=answer.get('probabilities'); keys=isinstance(p,dict) and set(p)==set(LETTERS)
        valid=keys and all(probability(x) for x in p.values())
        total=sum(p.values()) if valid else None
        top=[l for l,v in p.items() if v==max(p.values())] if valid and total else []
        detail['metadata_quality']={'probability_keys_valid':keys,'probability_values_valid':valid,
            'raw_sum':total,'normalization_applied':False,'calibration_quality_established':False,
            'unique_argmax_action':options[LETTERS.index(top[0])] if len(top)==1 else None,
            'choice_is_displayed_argmax':choice in top if top else None,
            'displayed_top_tie':len(top)>1 if top else None,
            'confidence_valid':probability(answer.get('confidence'))}
        result.update(status='ok',action=options[LETTERS.index(choice)])
    except (ValueError,KeyError,TypeError) as error:
        detail['error']=str(error) if isinstance(error,ValueError) else type(error).__name__
    return result


def extract(values,norm,top_id,top_logit,options):
    options=options_checked(options)
    if len(values)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in [*values,norm,top_logit]) or type(top_id)!=int or top_id<0:
        raise ValueError('Invalid logit metadata')
    maximum=max(values)
    if norm<top_logit-1e-9 or top_logit<maximum-1e-9: raise ValueError('Impossible normalizer')
    if top_id in TOKEN_IDS and top_logit!=values[TOKEN_IDS.index(top_id)]: raise ValueError('Top mismatch')
    z=sum(math.exp(v-maximum) for v in values); mass=math.exp(maximum+math.log(z)-norm)
    if mass>1+1e-9: raise ValueError('Impossible candidate mass')
    winners=[i for i,v in enumerate(values) if v==maximum]
    winner=winners[0] if len(winners)==1 else None
    return {'action':options[winner] if winner is not None else None,
        'letter':LETTERS[winner] if winner is not None else None,'exact_tie':winner is None,
        'conditional_probabilities':{l:math.exp(v-maximum)/z for l,v in zip(LETTERS,values)},
        'full_vocabulary_candidate_mass':mass,'unconstrained_top_is_candidate':top_id in TOKEN_IDS}


