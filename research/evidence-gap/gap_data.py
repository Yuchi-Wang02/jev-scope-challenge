"""Original finite-policy candidate corpus: possible-world truth, not human labels."""
from __future__ import annotations
import copy
import itertools
import json
import random
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
FAMILIES=('joint_approval','reversal_exception','route_lookup','composed_route')
VARIANTS=('full','hold','flip','decisive_missing','nondecisive_missing','conflict')
LABELS=['ALLOW','DENY','INSUFFICIENT']
SEED=20261001


def keys(family):
    return {'joint_approval':('review_a','review_b'),
        'reversal_exception':('base','exception'),
        'route_lookup':('route','site_a','site_b'),
        'composed_route':('route','site_a','site_b','review_a','exception')}[family]


def complete_decision(family,world):
    if family=='joint_approval':return world['review_a'] and world['review_b']
    if family=='reversal_exception':return world['base'] != world['exception']
    route=world['site_b'] if world['route'] else world['site_a']
    return route if family=='route_lookup' else world['review_a'] and (route != world['exception'])


def constraints(case):
    return {k:{r['value'] for r in case['records'] if r['field']==k and r['scope']==case['target']} for k in keys(case['family'])}


def world_truth(case):
    """Enumerate complete legal policy states consistent with available records."""
    names=keys(case['family']);known=constraints(case);outcomes=set();legal=0
    for values in itertools.product((False,True),repeat=len(names)):
        world=dict(zip(names,values))
        if all(all(world[k]==v for v in observations) for k,observations in known.items()):
            legal+=1;outcomes.add(bool(complete_decision(case['family'],world)))
    if legal==0 or len(outcomes)!=1:return 'INSUFFICIENT',legal
    return ('ALLOW' if next(iter(outcomes)) else 'DENY'),legal


def direct_truth(case):
    """Separate short-circuit/three-valued implementation for an exhaustive cross-check."""
    observed=constraints(case)
    if any(len(v)>1 for v in observed.values()):return 'INSUFFICIENT'
    values={k:next(iter(v)) if v else None for k,v in observed.items()}
    f=case['family']
    if f=='joint_approval':
        if False in values.values():return 'DENY'
        return 'ALLOW' if all(v is True for v in values.values()) else 'INSUFFICIENT'
    if f=='reversal_exception':
        if any(v is None for v in values.values()):return 'INSUFFICIENT'
        return 'ALLOW' if values['base']!=values['exception'] else 'DENY'
    route=values['route']
    if route is None:
        a,b=values['site_a'],values['site_b']
        permission=a if a is not None and a==b else None
    else:permission=values['site_b'] if route else values['site_a']
    if f=='route_lookup':return 'INSUFFICIENT' if permission is None else ('ALLOW' if permission else 'DENY')
    if values['review_a'] is False:return 'DENY'
    if values['exception'] is None or permission is None:return 'INSUFFICIENT'
    if permission==values['exception']:return 'DENY'
    return 'ALLOW' if values['review_a'] is True else 'INSUFFICIENT'


def names_for(family,index):
    rng=random.Random(f'{SEED}/{family}/{index}')
    def name(prefix):return prefix+'-'+''.join(rng.choice('ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(5))
    return name('request'),name('other'),name('site'),name('site')


def policy_for(case):
    a,b=case['sites']
    intro='Use only the supplied records for the requested target. Records for another request do not establish target facts. If target-schema records give opposite values for the same field, choose INSUFFICIENT. '
    f=case['family']
    if f=='joint_approval':
        return intro+'Allow exactly when both reviewer A and reviewer B approve. Any explicit rejection denies even when the other reviewer decision is absent. With no rejection, a missing required reviewer decision is INSUFFICIENT.'
    if f=='reversal_exception':
        return intro+'Use the target base decision, except reverse ALLOW and DENY when the target reversal exception is active. An inactive exception keeps the base decision. Missing base decision or exception status is INSUFFICIENT.'
    rule=f'The target route names either {a} or {b}. Use the permission recorded for that selected site; a missing route or missing selected-site permission is INSUFFICIENT unless every possible route yields the same decision. Missing permission for an unselected site does not affect a known route. '
    if f=='route_lookup':return intro+rule+'Allowed site permission supports the request; blocked site permission denies it.'
    return intro+rule+'Reverse the selected-site permission when the target reversal exception is active; inactive keeps it. Reviewer A rejection denies regardless of other missing facts. A determined blocked permission after reversal also denies even when reviewer A approval is missing. Otherwise allow only if reviewer A approves and the possibly reversed site permission allows. If the remaining facts do not determine one decision, choose INSUFFICIENT.'


def sentence(record,case):
    scope,key,value=record['scope'],record['field'],record['value'];a,b=case['sites']
    if key.startswith('review_'):
        role='A' if key=='review_a' else 'B';v='approves' if value else 'rejects'
        return f'Reviewer {role} {v} request {scope}.'
    if key=='base':return f'Base decision for request {scope}: '+('ALLOW.' if value else 'DENY.')
    if key=='exception':return f'Reversal exception for request {scope}: '+('active.' if value else 'inactive.')
    if key=='route':return f'Route for request {scope}: '+(b if value else a)+'.'
    site=a if key=='site_a' else b
    return f'Permission for site {site} in request {scope}: '+('allowed.' if value else 'blocked.')


def render(case):
    header=f"Request: allow action for request {case['target']}."
    lines=[sentence(r,case) for r in case['records']]
    style=case['style']
    prefix=['Evidence:','Available records:','Decision notes:','Supplied facts:',
            'Record extract:','Case file:','Policy evidence:','Source lines:',
            'Audit fragment:','Statement log:','Input report:','Fact register:'][style]
    if style<4:body='\n'.join(lines)
    elif style<8:body='\n'.join(f'[{i+1}] {line}' for i,line in enumerate(lines))
    else:body='\n'.join(f'- {line}' for line in lines)
    return header+'\n'+prefix+'\n'+body,policy_for(case)


def parse_text(state,policy,family,sites):
    """Known-grammar same-text reference; no supplied construction facts or gold."""
    lines=state.splitlines()
    m=re.fullmatch(r'Request: allow action for request (request-[A-Z]+)\.',lines[0])
    if not m:raise ValueError('Unknown request grammar')
    target=m.group(1);records=[]
    for line in lines[2:]:
        line=re.sub(r'^(?:\[\d+\] |- )','',line)
        matches=[
            ('review',re.fullmatch(r'Reviewer ([AB]) (approves|rejects) request (request-[A-Z]+|other-[A-Z]+)\.',line)),
            ('base',re.fullmatch(r'Base decision for request (request-[A-Z]+|other-[A-Z]+): (ALLOW|DENY)\.',line)),
            ('exception',re.fullmatch(r'Reversal exception for request (request-[A-Z]+|other-[A-Z]+): (active|inactive)\.',line)),
            ('route',re.fullmatch(r'Route for request (request-[A-Z]+|other-[A-Z]+): (site-[A-Z]+)\.',line)),
            ('site',re.fullmatch(r'Permission for site (site-[A-Z]+) in request (request-[A-Z]+|other-[A-Z]+): (allowed|blocked)\.',line))]
        matched=[(k,m) for k,m in matches if m]
        if len(matched)!=1:raise ValueError('Unknown evidence grammar')
        kind,m=matched[0]
        if kind=='review':role,v,scope=m.groups();key='review_a' if role=='A' else 'review_b';value=v=='approves'
        elif kind in ('base','exception'):
            scope,v=m.groups();key=kind;value=v in ('ALLOW','active')
        elif kind=='route':
            scope,site=m.groups()
            if site not in sites:raise ValueError('Unknown route site')
            key='route';value=site==sites[1]
        else:
            site,scope,v=m.groups()
            if site not in sites:raise ValueError('Unknown permission site')
            key='site_a' if site==sites[0] else 'site_b';value=v=='allowed'
        records.append({'scope':scope,'field':key,'value':value})
    case={'target':target,'family':family,'sites':sites,'records':records}
    if policy!=policy_for(case):raise ValueError('Unknown policy grammar')
    return case


def build_rows():
    rows=[]
    for family in FAMILIES:
        for index in range(12):
            target,other,a,b=names_for(family,index);desired=index%2==0
            if family=='joint_approval':values={'review_a':True,'review_b':desired};key='review_b'
            elif family=='reversal_exception':
                base=index//2%2==0;values={'base':base,'exception':base!=desired};key='exception'
            else:
                route=bool(index//2%2);exc=bool(index//4%2)
                selected=desired if family=='route_lookup' else desired!=exc
                values={'route':route,'site_a':selected if not route else not selected,'site_b':selected if route else not selected}
                if family=='composed_route':values.update(review_a=True,exception=exc)
                key='route'
            initial=[{'scope':target,'field':k,'value':v} for k,v in values.items()]
            initial.append({'scope':other,'field':key,'value':not values[key]})
            for variant in VARIANTS:
                records=copy.deepcopy(initial)
                if variant=='hold':records.reverse()
                elif variant=='flip':next(r for r in records if r['scope']==target and r['field']==key)['value']=not values[key]
                elif variant=='decisive_missing':records=[r for r in records if not (r['scope']==target and r['field']==key)]
                elif variant=='nondecisive_missing':
                    if family=='joint_approval' and not desired:drop='review_a';scope=target
                    elif family in ('route_lookup','composed_route'):drop='site_a' if values['route'] else 'site_b';scope=target
                    else:drop=key;scope=other
                    records=[r for r in records if not (r['field']==drop and r['scope']==scope)]
                elif variant=='conflict':records.append({'scope':target,'field':key,'value':not values[key]})
                split='reserved_test' if family=='composed_route' else 'development' if index<4 else 'calibration_reserved' if index<8 else 'reserved_test'
                row={'id':f'{family}-{index+1}-{variant}','parent':f'{family}-{index+1}',
                    'family':family,'variant':variant,'split':split,'style':index,'target':target,
                    'sites':[a,b],'records':records,'source':'original synthetic finite-policy cases',
                    'independent_human_reviewed':False}
                row['state'],row['instruction']=render(row)
                row['gold'],row['legal_worlds']=world_truth(row)
                if direct_truth(row)!=row['gold']:raise ValueError('Two policy solvers disagree')
                parsed=parse_text(row['state'],row['instruction'],family,row['sites'])
                if world_truth(parsed)!=world_truth(row):raise ValueError('Text roundtrip changed policy facts')
                rows.append(row)
    validate(rows)
    return rows


def validate(rows):
    if len(rows)!=288 or len({r['id'] for r in rows})!=288:raise ValueError('Expected 48 six-view parents')
    for parent in {r['parent'] for r in rows}:
        group={r['variant']:r for r in rows if r['parent']==parent}
        if set(group)!=set(VARIANTS) or len({r['split'] for r in group.values()})!=1:raise ValueError('Invalid grouped grid')
        full=group['full']['gold']
        if full=='INSUFFICIENT' or any(group[v]['gold']!=full for v in ('hold','nondecisive_missing')):
            raise ValueError('Invalid invariance labels')
        if group['flip']['gold'] not in ('ALLOW','DENY') or group['flip']['gold']==full:
            raise ValueError('Invalid decisive flip')
        if any(group[v]['gold']!='INSUFFICIENT' for v in ('decisive_missing','conflict')):
            raise ValueError('Invalid uncertainty labels')
    for r in rows:
        if (r['state'],r['instruction'])!=render(r) or (r['gold'],r['legal_worlds'])!=world_truth(r):raise ValueError('Facts/gold/rendering drift')
    if any(r['split']!='reserved_test' for r in rows if r['family']=='composed_route'):
        raise ValueError('Composed mechanism leaked out of reserved test')


def exhaustive_solver_audit():
    checked=0
    for family in FAMILIES:
        for status in itertools.product(((),(False,),(True,),(False,True)),repeat=len(keys(family))):
            records=[{'scope':'request-X','field':k,'value':v} for k,observations in zip(keys(family),status) for v in observations]
            case={'family':family,'target':'request-X','records':records}
            if world_truth(case)[0]!=direct_truth(case):raise ValueError('Exhaustive policy solver disagreement')
            checked+=1
    return {'status':'passed','partial_or_conflicting_states':checked,
            'scope':'finite structured policy truth; not independent natural-language annotation'}


if __name__=='__main__':
    from pathlib import Path
    path=HERE/'data/cases.jsonl';audit=exhaustive_solver_audit();rows=build_rows()
    payload=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
    if path.exists() and path.read_text(encoding='utf-8')!=payload:raise ValueError('Preserve existing corpus; version changes')
    path.parent.mkdir(exist_ok=True)
    path.write_text(payload,encoding='utf-8',newline='\n')
    (HERE/'data/solver_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Built 288 inputs / 48 parents; structured solver audit passed; human annotations=0.')
