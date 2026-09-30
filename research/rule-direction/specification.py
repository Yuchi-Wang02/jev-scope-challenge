"""Authored two-proposition constraints, exhaustive witnesses, and a grammar control."""
from itertools import product

# Positive P, negative P, Q, and question. No outside business rules are assumed.
FAMILIES = (
 ('The parcel carries a blue inspection seal','The parcel does not carry a blue inspection seal','The parcel qualifies for priority dispatch','Does the parcel qualify for priority dispatch?'),
 ('The repair request includes a valid receipt','The repair request does not include a valid receipt','The repair request qualifies for free service','Does the repair request qualify for free service?'),
 ('The booking has a flexible fare','The booking does not have a flexible fare','The booking qualifies for a date change','Does the booking qualify for a date change?'),
 ('The equipment has a current safety certificate','The equipment does not have a current safety certificate','The equipment qualifies for warehouse use','Does the equipment qualify for warehouse use?'),
 ('The supplier has a completed quality audit','The supplier does not have a completed quality audit','The supplier qualifies for the preferred list','Does the supplier qualify for the preferred list?'),
 ('The rental includes a protection package','The rental does not include a protection package','The rental qualifies for a fee waiver','Does the rental qualify for a fee waiver?'),
 ('The batch has a passing temperature report','The batch does not have a passing temperature report','The batch qualifies for cold-storage release','Does the batch qualify for cold-storage release?'),
 ('The account has a verified address','The account does not have a verified address','The account qualifies for invoice billing','Does the account qualify for invoice billing?'),
 ('The order contains a reusable container','The order does not contain a reusable container','The order qualifies for a packing discount','Does the order qualify for a packing discount?'),
 ('The device has an active maintenance plan','The device does not have an active maintenance plan','The device qualifies for a replacement unit','Does the device qualify for a replacement unit?'),
 ('The delivery has a confirmed appointment','The delivery does not have a confirmed appointment','The delivery qualifies for dock access','Does the delivery qualify for dock access?'),
 ('The purchase includes a loyalty voucher','The purchase does not include a loyalty voucher','The purchase qualifies for a handling rebate','Does the purchase qualify for a handling rebate?'),
)
RELATIONS=('sufficient','necessary','equivalent')
FACTS=('positive','negative','unknown')


def witnesses(relation, fact):
    if relation not in RELATIONS or fact not in FACTS:raise ValueError('Unknown finite contract')
    out=[]
    for p,q in product((False,True),repeat=2):
        rule={'sufficient':not p or q,'necessary':not q or p,'equivalent':p==q}[relation]
        visible={'positive':p,'negative':not p,'unknown':True}[fact]
        if rule and visible:out.append({'P':p,'Q':q})
    if not out:raise ValueError('Inconsistent contract must not be labeled')
    return out


def truth(relation,fact):
    values={w['Q'] for w in witnesses(relation,fact)}
    return 'yes' if values=={True} else 'no' if values=={False} else 'maybe'


def render(family,relation,fact):
    p,negative,q,question=family
    connector={'sufficient':' if ','necessary':' only if ','equivalent':' if and only if '}[relation]
    policy=q+connector+p[0].lower()+p[1:]+'.'
    scenario='The case was logged on Monday.'
    if fact!='unknown':scenario+=' '+(p if fact=='positive' else negative)+'.'
    return {'policy':policy,'question':question,'scenario':scenario}


def cases():
    return [{'id':f'r{n:02d}_{rel}_{fact}','family_id':f'r{n:02d}',
        'relation':rel,'fact_state':fact,'state':render(fam,rel,fact),
        'reference':truth(rel,fact),'possible_worlds':witnesses(rel,fact)}
        for n,fam in enumerate(FAMILIES,1) for rel in RELATIONS for fact in FACTS]


def grammar_control(state):
    """Parse only the known grammar; no case ID, formal relation or reference input.

    This lookup vocabulary is author-supplied grammar knowledge, not a general
    natural-language reasoner. Closed-form output is independent of enumeration.
    """
    if set(state)!={'policy','question','scenario'}:raise ValueError('State schema')
    for p,negative,q,question in FAMILIES:
        if state['question']!=question:continue
        prefix=q
        tail=p[0].lower()+p[1:]+'.'
        if state['policy']==prefix+' if and only if '+tail:mode='both'
        elif state['policy']==prefix+' only if '+tail:mode='requirement'
        elif state['policy']==prefix+' if '+tail:mode='guarantee'
        else:raise ValueError('Unsupported rule grammar')
        base='The case was logged on Monday.'
        if state['scenario']==base:return 'maybe'
        if state['scenario']==base+' '+p+'.':return 'yes' if mode in ('both','guarantee') else 'maybe'
        if state['scenario']==base+' '+negative+'.':return 'no' if mode in ('both','requirement') else 'maybe'
        raise ValueError('Unsupported evidence grammar')
    raise ValueError('Unsupported question vocabulary')
