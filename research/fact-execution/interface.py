"""Visible policy compilation and a strict four-state fact/execution contract."""
import re
import sys
from pathlib import Path
GAP=Path(__file__).resolve().parent.parent/'evidence-gap'
sys.path.insert(0,str(GAP))
from gap_data import keys, policy_for, world_truth

STATUSES=('TRUE','FALSE','MISSING','CONFLICT')
STATUS_ORDERS=[list(STATUSES),list(reversed(STATUSES))]
STATUS_OPTIONS={
    'TRUE':'Only the positive value for this target field is explicitly recorded.',
    'FALSE':'Only the negative value for this target field is explicitly recorded.',
    'MISSING':'Neither value for this target field is explicitly recorded.',
    'CONFLICT':'Both positive and negative values for this same target field are explicitly recorded.'}


def compile_visible(state,policy):
    target=re.fullmatch(r'Request: allow action for request (request-[A-Z]+)\.',state.splitlines()[0])
    if not target:raise ValueError('Unsupported request header')
    if 'Reviewer A rejection denies' in policy:raise ValueError('Reserved composed policy')
    route=re.search(r'The target route names either (site-[A-Z]+) or (site-[A-Z]+)\.',policy)
    if route:family,sites='route_lookup',list(route.groups())
    elif 'Allow exactly when both reviewer A and reviewer B approve.' in policy:
        family,sites='joint_approval',['site-UNUSED-A','site-UNUSED-B']
    elif 'Use the target base decision, except reverse ALLOW and DENY' in policy:
        family,sites='reversal_exception',['site-UNUSED-A','site-UNUSED-B']
    else:raise ValueError('Unsupported policy')
    if policy!=policy_for({'family':family,'sites':sites}):raise ValueError('Unknown policy wording')
    t=target.group(1);a,b=sites
    definitions={
        'review_a':(f'reviewer A approves request {t}',f'reviewer A rejects request {t}'),
        'review_b':(f'reviewer B approves request {t}',f'reviewer B rejects request {t}'),
        'base':(f'base decision for request {t} is ALLOW',f'base decision for request {t} is DENY'),
        'exception':(f'reversal exception for request {t} is active',f'reversal exception for request {t} is inactive'),
        'route':(f'request {t} routes to {b}',f'request {t} routes to {a}'),
        'site_a':(f'permission for site {a} in request {t} is allowed',f'permission for site {a} in request {t} is blocked'),
        'site_b':(f'permission for site {b} in request {t} is allowed',f'permission for site {b} in request {t} is blocked')}
    return {'policy_id':family,'target':t,'sites':sites,
            'fields':[{ 'name':k,'positive':definitions[k][0],'negative':definitions[k][1]} for k in keys(family)]}


def scaffold(schema,policy):
    lines=['Policy:\n'+policy,'Target-field definitions (program-provided, not observations):']
    for f in schema['fields']:lines.append(f"{f['name']}: positive = {f['positive']}; negative = {f['negative']}.")
    lines.append('Ignore records for other requests. A field definition or a policy is not evidence that its value exists. A missing value is not a negative value. Conflicting values are distinct from missing values.')
    return '\n'.join(lines)


def instruction(schema,policy,kind,field=None):
    base=scaffold(schema,policy)
    if kind=='direct':return base+'\nDetermine the requested action under the policy using only the supplied evidence.'
    if kind!='fact' or field not in {f['name'] for f in schema['fields']}:raise ValueError('Unknown query kind/field')
    return base+f'\nExtract only the observation status of target field {field}. Do not infer an observation from the final policy outcome. Choose TRUE, FALSE, MISSING or CONFLICT according to explicit positive/negative observations.'


def status_for(values):
    values=set(values)
    if not values:return 'MISSING'
    if values=={True}:return 'TRUE'
    if values=={False}:return 'FALSE'
    if values=={False,True}:return 'CONFLICT'
    raise ValueError('Non-binary fact')


def execute(schema,facts):
    expected={f['name'] for f in schema['fields']}
    if set(facts)!=expected or any(v not in STATUSES for v in facts.values()):raise ValueError('Invalid complete fact vector')
    records=[]
    for field,status in facts.items():
        values={'TRUE':[True],'FALSE':[False],'MISSING':[],'CONFLICT':[False,True]}[status]
        records.extend({'scope':schema['target'],'field':field,'value':v} for v in values)
    return world_truth({'family':schema['policy_id'],'target':schema['target'],'records':records})[0]
