"""Deterministic candidate-coverage diagnostic; preparation contains no inference."""
import argparse
import copy
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
OLD=REPO/'research/payment-ownership'
spec=importlib.util.spec_from_file_location('payment_coverage_source',OLD/'study.py')
LEGACY=importlib.util.module_from_spec(spec);spec.loader.exec_module(LEGACY)
LABELS=LEGACY.LABELS
ORDERS=LEGACY.ORDERS
MODEL=LEGACY.MODEL
PRICE=LEGACY.PRICE
canonical=LEGACY.canonical
read=LEGACY.read
rows=LEGACY.rows
write=LEGACY.write
write_rows=LEGACY.write_rows
sha=LEGACY.sha
utc=LEGACY.utc
validate_response=LEGACY.validate_response

POLICY=("Judge only the refund-destination restriction. Authentication, delivery, item eligibility, "
        "confirmation and permission to execute a return are outside this task. A determined judgment "
        "requires a uniquely identified target order and destination. If target identity or the necessary "
        "payment evidence is not established, select NOT_ESTABLISHED. A refund must use the target's "
        "original payment method or an existing gift card in this user's payment_methods. Another "
        "ordinary payment method of the same user is not enough. Exact order IDs are unique. "
        "Displayed payment histories are complete, and the user payment_methods list is complete. "
        "Only the displayed records and the supplied coverage statement may be used.")
COVERAGE={
 'complete': 'The displayed orders include every order of this user containing the product named in the request.',
 'relevant_omission': 'At least one order containing the product named in the request is not displayed. Its payment history is not provided. A product-name request does not distinguish the displayed match from an omitted match.',
 'irrelevant_omission': 'At least one order containing a different product is not displayed. Every order containing the product named in the request is displayed; no omitted order contains that product.',
}
RUBRICS={LABELS[0]:'A unique target and destination are established, and the destination satisfies the refund-destination rule.',
         LABELS[1]:'A unique target and destination are established, and the destination violates the refund-destination rule.',
         LABELS[2]:'The target or destination is not uniquely established, or necessary payment evidence is missing.'}


def request_body(state, order):
    return {'model':MODEL,'state':state,'questions':{'decision':{
        'type':'choice','instructions':'Resolve customer_request using visible records and coverage_statement, then apply component_policy. Select exactly one outcome.',
        'criteria':{k:RUBRICS[v] for k,v in zip('ABC',ORDERS[order])}}}}


def select(db):
    excluded={c['source_user_id'] for c in rows(OLD/'data/cases.jsonl')}
    pool=[]
    for uid,user in sorted(db['users'].items()):
        if uid in excluded:continue
        methods=user['payment_methods']
        ordinary=sorted(k for k,v in methods.items() if v['source'] in ('credit_card','paypal'))
        if len(ordinary)<2:continue
        orders=sorted((o for o in db['orders'].values() if o['user_id']==uid and LEGACY.original(o) in ordinary),key=lambda x:x['order_id'])
        for a in orders:
            for b in orders:
                if a['order_id']==b['order_id']:continue
                item=LEGACY.unique_item(a,b)
                if item:
                    pool.append({'user':user,'target':a,'other':b,'product':item,
                                 'alternative':next(k for k in ordinary if k!=LEGACY.original(a))})
    pool.sort(key=lambda x:sha(canonical([x['user']['user_id'],x['target']['order_id'],x['other']['order_id'],'coverage-20260930-v1']).encode()))
    selected=[];used=set()
    for p in pool:
        uid=p['user']['user_id']
        if uid in used:continue
        used.add(uid);selected.append(p)
        if len(selected)==12:break
    if len(selected)!=12:raise ValueError('Insufficient disjoint eligible users')
    return selected,len({p['user']['user_id'] for p in pool})


def build(selection):
    result=[];witnesses=[]
    for n,s in enumerate(selection):
        parent=f'c{n+1:02d}';user=s['user'];target=s['target'];other=s['other']
        destination=LEGACY.original(target) if n%2==0 else s['alternative']
        determined=LABELS[0] if n%2==0 else LABELS[1]
        visible=[target,other] if n%2==0 else [other,target]
        visible=[{k:copy.deepcopy(o[k]) for k in ('order_id','user_id','items','payment_history')} for o in visible]
        for style in ('explicit','product'):
            request=(f"For order {target['order_id']}, please refund to payment method {destination}. Does this destination satisfy the rule?"
                     if style=='explicit' else
                     f"For my {s['product']} order, please refund to payment method {destination}. Does this destination satisfy the rule?")
            # Explicit controls also name the relevant product without altering target identity.
            if style=='explicit': request+=f" The product is {s['product']}."
            for coverage,text in COVERAGE.items():
                state={'component_policy':POLICY,'customer_request':request,'coverage_statement':text,
                       'orders':copy.deepcopy(visible),'user_profile':{k:copy.deepcopy(user[k]) for k in ('user_id','payment_methods')}}
                label=LABELS[2] if style=='product' and coverage=='relevant_omission' else determined
                result.append({'case_id':f'{parent}_{style}_{coverage}','parent_id':parent,
                               'source_user_id':user['user_id'],'style':style,'coverage':coverage,
                               'visible_target_id':target['order_id'],'destination_id':destination,
                               'product':s['product'],'reference':label,'human_reviewed':False,'state':state})
        alternatives=[destination,next(k for k,v in user['payment_methods'].items() if v['source'] in ('credit_card','paypal') and k!=destination)]
        worlds=[]
        for outcome,pid in zip(LABELS[:2],alternatives):
            hidden=copy.deepcopy(next(o for o in visible if o['order_id']==target['order_id']))
            hidden['order_id']='#SYNTHETIC_'+parent.upper()
            hidden['payment_history'][0]['payment_method_id']=pid
            worlds.append({'target_id':hidden['order_id'],'omitted_order':hidden,'destination_rule_outcome':outcome})
        witnesses.append({'parent_id':parent,'case_id':f'{parent}_product_relevant_omission',
                          'origin':'Synthetic auditor-only possible worlds, not source database facts',
                          'visible_records_unchanged':True,'worlds':worlds})
    return result,witnesses


def resolve(state, mode='scope_aware'):
    text=state['customer_request'];methods=state['user_profile']['payment_methods']
    explicit=[o for o in state['orders'] if o['order_id'] in text]
    if explicit:targets=explicit
    else:
        import re
        match=re.search(r'For my (.+?) order,',text)
        targets=[o for o in state['orders'] if match and any(i['name']==match[1] for i in o['items'])]
    dest=[k for k in methods if ('payment method '+k+'.') in text]
    if mode=='keyword_all' and 'not displayed' in state['coverage_statement']:return LABELS[2]
    if mode=='keyword_product' and not explicit and 'not displayed' in state['coverage_statement']:return LABELS[2]
    if len(targets)!=1 or len(dest)!=1:return LABELS[2]
    if mode=='scope_aware' and not explicit and state['coverage_statement']==COVERAGE['relevant_omission']:return LABELS[2]
    if LEGACY.original(targets[0]) is None:return LABELS[2]
    return LABELS[0] if methods[dest[0]]['source']=='gift_card' or LEGACY.original(targets[0])==dest[0] else LABELS[1]


def smokes():
    user={'user_id':'smoke','payment_methods':{'card_a':{'id':'card_a','source':'credit_card'},'card_b':{'id':'card_b','source':'credit_card'}}}
    order={'order_id':'#SMOKE_C','user_id':'smoke','items':[{'name':'Mug'}],
           'payment_history':[{'transaction_type':'payment','amount':20,'payment_method_id':'card_a'}]}
    specs=[('original',True,'card_a','complete',False,LABELS[0]),
           ('foreign',True,'card_b','complete',False,LABELS[1]),
           ('product_missing',False,'card_a','relevant_omission',False,LABELS[2]),
           ('missing_history',True,'card_a','complete',True,LABELS[2]),
           ('irrelevant_valid',False,'card_a','irrelevant_omission',False,LABELS[0]),
           ('irrelevant_invalid',False,'card_b','irrelevant_omission',False,LABELS[1])]
    result=[]
    for name,explicit,dest,coverage,missing,label in specs:
        o=copy.deepcopy(order)
        if missing:o.pop('payment_history')
        request=(f'For order #SMOKE_C, please refund to payment method {dest}. The product is Mug.' if explicit else f'For my Mug order, please refund to payment method {dest}.')
        result.append({'case_id':'smoke_'+name,'reference':label,'state':{'component_policy':POLICY,
                       'customer_request':request,'coverage_statement':COVERAGE[coverage],'orders':[o],'user_profile':user}})
    return result


def plan(cases):
    jobs=[]
    for c in smokes():
        jobs.append({'job_id':c['case_id'],'case_id':c['case_id'],'phase':'smoke','option_order':0,
                     'reference':c['reference'],'body':request_body(c['state'],0)})
    main=[{'job_id':c['case_id']+'__'+str(m),'case_id':c['case_id'],'phase':'primary','option_order':m,
           'body':request_body(c['state'],m)} for c in cases for m in range(2)]
    jobs+=sorted(main,key=lambda j:sha((j['job_id']+'coverage-schedule-v1').encode()))
    for j in jobs:
        j['request_sha256']=sha(canonical(j['body']).encode())
        j['planned_input_units']=len(canonical(j['body']).encode())+256
    return jobs


def prepare():
    if (ROOT/'freeze.json').exists():raise RuntimeError('Existing freeze; preparation overwrite refused')
    data=(REPO/'.local/payment-source/db.json').read_bytes()
    assert sha(data)==read(OLD/'source_manifest.json')['db_sha256']
    selection,eligible=select(json.loads(data));cases,witnesses=build(selection)
    write(ROOT/'source_manifest.json',{'revision':LEGACY.REV,'db_sha256':sha(data),
          'db_url':read(OLD/'source_manifest.json')['db_url'],'eligible_disjoint_users':eligible,
          'selection':'Deterministic SHA256 rank with coverage-20260930-v1 salt, unique users; alternating valid/invalid destinations',
          'source_type':'Public simulated data; task coverage declarations and omitted worlds are synthetic',
          'source_license':'MIT; see vendor/LICENSE and payment-ownership source register',
          'human_reviews':0,'authorship':'AI-authored deterministic task and witnesses'})
    write(ROOT/'vendor/selected_records.json',selection)
    (ROOT/'vendor/LICENSE').write_bytes((OLD/'vendor/LICENSE').read_bytes())
    write_rows(ROOT/'data/cases.jsonl',cases);write_rows(ROOT/'data/witnesses.jsonl',witnesses)
    write_rows(ROOT/'plans/primary.jsonl',plan(cases))
    return verify_data()


def verify_data():
    cases=rows(ROOT/'data/cases.jsonl');witnesses=rows(ROOT/'data/witnesses.jsonl')
    selection=read(ROOT/'vendor/selected_records.json')
    assert (cases,witnesses)==build(selection)
    assert len(cases)==72 and len({c['parent_id'] for c in cases})==12
    assert Counter(c['reference'] for c in cases)=={LABELS[0]:30,LABELS[1]:30,LABELS[2]:12}
    assert not {c['source_user_id'] for c in cases}&{c['source_user_id'] for c in rows(OLD/'data/cases.jsonl')}
    assert len({c['source_user_id'] for c in cases})==12
    for c in cases:
        assert resolve(c['state'])==c['reference']
        assert all(k not in c['state'] for k in ('reference','parent_id','visible_target_id'))
    for parent in {c['parent_id'] for c in cases}:
        for style in ('explicit','product'):
            states=[copy.deepcopy(c['state']) for c in cases if c['parent_id']==parent and c['style']==style]
            for s in states:s.pop('coverage_statement')
            assert states[0]==states[1]==states[2]
    for w in witnesses:
        c=next(c for c in cases if c['case_id']==w['case_id']);visible=c['state']['orders'];methods=c['state']['user_profile']['payment_methods']
        for world in w['worlds']:
            o=world['omitted_order'];assert o['order_id'] not in {x['order_id'] for x in visible}
            assert o['user_id']==c['state']['user_profile']['user_id']
            assert any(i['name']==c['product'] for i in o['items'])
            assert LEGACY.original(o) in methods
            expected=LABELS[0] if LEGACY.original(o)==c['destination_id'] else LABELS[1]
            assert expected==world['destination_rule_outcome']
        assert {w['worlds'][0]['destination_rule_outcome'],w['worlds'][1]['destination_rule_outcome']}==set(LABELS[:2])
    for s in smokes():assert resolve(s['state'])==s['reference']
    jobs=plan(cases);assert rows(ROOT/'plans/primary.jsonl')==jobs and len(jobs)==150
    total=sum(j['planned_input_units'] for j in jobs)
    assert total+5*max(j['planned_input_units'] for j in jobs)<=1_000_000
    scores={m:sum(resolve(c['state'],m)==c['reference'] for c in cases) for m in ('scope_aware','ignore_scope','keyword_all','keyword_product')}
    return {'cases':72,'parents':12,'planned_calls':150,'planned_input_units':total,
            'software_baseline_correct':scores,'human_reviewed':0,'new_model_calls':0}


def file_hash(path):return sha(Path(path).read_bytes().replace(b'\r\n',b'\n'))


def freeze():
    if (ROOT/'freeze.json').exists():raise RuntimeError('Cannot overwrite freeze')
    check=verify_data()
    names=['study.py','run.py','PROTOCOL.md','data/cases.jsonl','data/witnesses.jsonl',
           'source_manifest.json','vendor/selected_records.json','vendor/LICENSE','plans/primary.jsonl']
    write(ROOT/'freeze.json',{'created_at_utc':utc(),'model':MODEL,'attempt_limit':155,'retry_limit':5,
          'planned_input_limit':1_000_000,'sha256_lf':{n:file_hash(ROOT/n) for n in names},
          'dependencies_sha256_lf':{'research/payment-ownership/study.py':file_hash(OLD/'study.py')},
          'data_checks':check,'review_status':'exploratory, before independent human review'})


def verify_freeze():
    f=read(ROOT/'freeze.json')
    for n,h in f['sha256_lf'].items():assert file_hash(ROOT/n)==h,n
    for n,h in f['dependencies_sha256_lf'].items():assert file_hash(REPO/n)==h,n
    return verify_data()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','verify','freeze','verify-freeze']);a=p.parse_args()
    print(json.dumps({'prepare':prepare,'verify':verify_data,'freeze':freeze,'verify-freeze':verify_freeze}[a.command](),indent=2))
