"""Fixed ordinary readout baselines over real saved main/reference logits."""
import math
from gap_data import LABELS

METHODS=('raw','null_subtract','two_order')


def softmax(values):
    if len(values)!=3 or any(not math.isfinite(v) for v in values):raise ValueError('Invalid three-way scores')
    weights=[math.exp(v-max(values)) for v in values];total=sum(weights)
    return [v/total for v in weights]


def semantic_probs(row):
    return dict(zip(row['order'],softmax(row['logits'])))


def readout(main,null,neighbor,method):
    if main['order']!=null['order'] or main['parent']!=null['parent']:raise ValueError('Mismatched null reference')
    if main['id']!=neighbor['id'] or neighbor['mapping']!=(main['mapping']+1)%3:raise ValueError('Mismatched order neighbor')
    if method=='raw':p=softmax(main['logits']);sources=[main['forward_id']]
    elif method=='null_subtract':
        p=softmax([a-b for a,b in zip(main['logits'],null['logits'])]);sources=[main['forward_id'],null['forward_id']]
    elif method=='two_order':
        a,b=semantic_probs(main),semantic_probs(neighbor)
        p=[(a[k]+b[k])/2 for k in main['order']];sources=[main['forward_id'],neighbor['forward_id']]
    else:raise ValueError('Unknown readout')
    return {'prediction':main['order'][max(range(3),key=p.__getitem__)],
        'scores':dict(zip(main['order'],p)),'source_forward_ids':sources,
        'nominal_calls':1 if method=='raw' else 2}
