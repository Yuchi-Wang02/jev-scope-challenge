"""Frozen, offline-replayable tau retail component diagnostic. No inference here."""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import itertools
import json
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
REV = '5bfa7e37b36656b37dc6d022156be6563c1007f3'
BASE = f'https://raw.githubusercontent.com/sierra-research/tau2-bench/{REV}/'
MODEL = 'jev-1.13.0'
LABELS = ['VALID_DESTINATION', 'INVALID_DESTINATION', 'NOT_ESTABLISHED']
ORDERS = [LABELS, list(reversed(LABELS))]
PRICE = 0.042 / 1_000_000
SCOPE = ('Evaluate only the refund destination restriction, not permission to execute a return. '
         'Authentication, delivery status, item eligibility and user confirmation are outside this component. '
         'A refund must go to the target order\'s original payment method or an existing gift card '
         'in this user\'s payment_methods. Another payment method belonging to the same user '
         'is not sufficient. Use only visible records. Displayed payment histories, when present, '
         'are complete. The orders shown are a selected subset; the user payment_methods list is complete.')
RUBRICS = {
    'VALID_DESTINATION': 'The supplied evidence establishes that the requested destination satisfies the target order refund-destination restriction.',
    'INVALID_DESTINATION': 'The supplied evidence establishes that the requested destination violates the target order refund-destination restriction.',
    'NOT_ESTABLISHED': 'The target order or destination is ambiguous, or necessary evidence is missing; neither validity nor invalidity is established.'}

def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def sha(x):
    return hashlib.sha256(x).hexdigest()

def file_hash(path):
    return sha(Path(path).read_bytes().replace(b'\r\n', b'\n'))

def utc():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def rows(path):
    p = Path(path)
    return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s] if p.exists() else []

def write(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')

def write_rows(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(canonical(x)+'\n' for x in obj), encoding='utf-8')

def original(order):
    history = order.get('payment_history')
    if not isinstance(history, list) or len(history) != 1 or history[0].get('transaction_type') != 'payment':
        return None
    return history[0].get('payment_method_id')

def destination_name(method):
    if method['source'] == 'credit_card':
        return f"the {method['brand']} credit card ending in {method['last_four']}"
    return f"the PayPal account {method['id']}"

def unique_item(a, b):
    other = {i['name'].lower() for i in b['items']}
    names = sorted({i['name'] for i in a['items'] if i['name'].lower() not in other})
    return names[0] if names else None

def source_selection(db):
    pools = {'flip': [], 'stable_valid': [], 'stable_invalid': []}
    for uid, user in sorted(db['users'].items()):
        methods = user['payment_methods']
        eligible = [o for o in db['orders'].values() if o['user_id'] == uid
                    and original(o) in methods and methods[original(o)]['source'] in ('credit_card','paypal')]
        for a, b in itertools.combinations(sorted(eligible, key=lambda o:o['order_id']), 2):
            if not unique_item(a,b) or not unique_item(b,a): continue
            pa, pb = original(a), original(b)
            if pa != pb:
                pools['flip'].append((uid,a,b,pa))
            else:
                pools['stable_valid'].append((uid,a,b,pa))
                for pid, method in sorted(methods.items()):
                    if pid != pa and method['source'] in ('credit_card','paypal'):
                        pools['stable_invalid'].append((uid,a,b,pid))
    chosen, used = [], set()
    for kind, count in [('flip',6),('stable_invalid',3),('stable_valid',3)]:
        candidates = sorted(pools[kind], key=lambda r:sha(canonical([r[0],r[1]['order_id'],r[2]['order_id'],r[3],'20260930']).encode()))
        selected = 0
        for uid,a,b,pid in candidates:
            if uid in used: continue
            method = db['users'][uid]['payment_methods'][pid]
            if method['source'] == 'credit_card':
                matches = [m for m in db['users'][uid]['payment_methods'].values()
                           if m.get('brand') == method['brand'] and m.get('last_four') == method['last_four']]
                if len(matches) != 1: continue
            used.add(uid); selected += 1
            chosen.append({'kind':kind, 'user':db['users'][uid], 'orders':[a,b], 'destination_id':pid})
            if selected == count: break
        if selected != count: raise ValueError(f'Insufficient independent eligible users: {kind} {selected}/{count}')
    return chosen, {k:len({r[0] for r in v}) for k,v in pools.items()}

def reference(state, target_id, destination_id):
    methods = state['user_profile']['payment_methods']
    if destination_id not in methods: return 'INVALID_DESTINATION'
    if methods[destination_id]['source'] == 'gift_card': return 'VALID_DESTINATION'
    targets = [o for o in state['orders'] if o['order_id'] == target_id]
    if len(targets) != 1 or original(targets[0]) is None: return 'NOT_ESTABLISHED'
    return LABELS[0] if original(targets[0]) == destination_id else LABELS[1]

def parse_request(state):
    """Transparent finite-language reference, not a general semantic parser."""
    text = state['customer_request'].lower()
    orders = state['orders']; methods = state['user_profile']['payment_methods']
    targets = [o['order_id'] for o in orders if o['order_id'].lower() in text]
    if not targets:
        match = re.search(r'refund on my (.+?) order', text)
        if match:
            targets = [o['order_id'] for o in orders if any(i['name'].lower() == match[1] for i in o['items'])]
    dests = [pid for pid in methods if pid.lower() in text]
    if not dests:
        match = re.search(r'the (.+?) credit card ending in (\d{4})', text)
        if match:
            dests = [pid for pid,m in methods.items() if m.get('brand','').lower() == match[1]
                     and m.get('last_four') == match[2]]
    if len(targets) != 1 or len(dests) != 1:
        return {'covered':False, 'prediction':'NOT_ESTABLISHED', 'target_id':None, 'destination_id':None}
    return {'covered':True, 'prediction':reference(state,targets[0],dests[0]),
            'target_id':targets[0], 'destination_id':dests[0]}

def build_cases(selection):
    cases = []
    for n, scene in enumerate(selection):
        user, orders, pid = scene['user'], scene['orders'], scene['destination_id']
        # Counterbalance which order appears first without modifying source fields.
        visible = orders if n % 2 == 0 else list(reversed(orders))
        projected = [{k:copy.deepcopy(o[k]) for k in ['order_id','user_id','items','payment_history']} for o in visible]
        state_base = {'component_policy':SCOPE,
                      'user_profile':{k:copy.deepcopy(user[k]) for k in ['user_id','payment_methods']},
                      'orders':projected}
        for target_slot, order in enumerate(orders):
            other = orders[1-target_slot]
            for style in ['explicit','item_reference']:
                request = (f"For order {order['order_id']}, please refund to payment method {pid}. Is that destination eligible?"
                           if style == 'explicit' else
                           f"Please use {destination_name(user['payment_methods'][pid])} for the refund on my {unique_item(order,other)} order. Does that destination satisfy the refund rule?")
                full = dict(copy.deepcopy(state_base), customer_request=request)
                related = copy.deepcopy(full)
                related['orders'] = [o for o in related['orders'] if o['order_id'] == order['order_id']]
                gold = reference(full,order['order_id'],pid)
                cases.append({'case_id':f'p{n+1:02d}_{target_slot}_{style}', 'parent_id':f'p{n+1:02d}',
                    'kind':scene['kind'], 'style':style, 'target_slot':target_slot,
                    'target_id':order['order_id'], 'destination_id':pid, 'reference':gold,
                    'reference_provenance':'program-derived; AI-authored requests; zero independent human reviews',
                    'human_reviewed':False, 'full':full, 'related':related,
                    'source_user_id':user['user_id'],
                    'source_order_ids':[o['order_id'] for o in orders]})
    return cases

def smoke_cases():
    methods = {'card_a':{'source':'credit_card','id':'card_a','brand':'visa','last_four':'1111'},
               'card_b':{'source':'credit_card','id':'card_b','brand':'visa','last_four':'2222'},
               'gift_a':{'source':'gift_card','id':'gift_a','balance':0}}
    order = {'order_id':'#SMOKE_A','user_id':'synthetic_smoke','items':[{'name':'Mug'}],
             'payment_history':[{'transaction_type':'payment','amount':10,'payment_method_id':'card_a'}]}
    base = {'component_policy':SCOPE, 'user_profile':{'user_id':'synthetic_smoke','payment_methods':methods},'orders':[order]}
    out = []
    specs = [('original','card_a',LABELS[0]),('foreign','card_b',LABELS[1]),('gift','gift_a',LABELS[0]),
             ('missing','card_b',LABELS[2]),('ambiguous','card_a',LABELS[2]),('unknown','unlisted_card',LABELS[1])]
    for name,pid,gold in specs:
        state = copy.deepcopy(base)
        state['customer_request'] = f'For order #SMOKE_A, please refund to payment method {pid}. Is that destination eligible?'
        if name == 'missing': state['orders'][0].pop('payment_history')
        if name == 'ambiguous':
            extra = copy.deepcopy(order); extra['order_id']='#SMOKE_B'
            extra['payment_history'][0]['payment_method_id']='card_b'
            state['orders'].append(extra)
            state['customer_request']='Please refund on my Mug order to payment method card_a. Is that destination eligible?'
        out.append({'case_id':'smoke_'+name,'state':state,'reference':gold})
    return out

def request_body(state, order):
    return {'model':MODEL, 'state':state, 'questions':{'decision':{'type':'choice',
        'instructions':'Resolve the order and payment method named in customer_request, then evaluate component_policy. Do not use another order\'s original payment as evidence about the target order. Select exactly one outcome.',
        'criteria':{letter:RUBRICS[label] for letter,label in zip('ABC',ORDERS[order])}}}}

def make_plan(cases):
    out=[]
    for row in smoke_cases():
        body=request_body(row['state'],0)
        out.append({'job_id':row['case_id'],'phase':'smoke','case_id':row['case_id'],'reference':row['reference'],
                    'input_view':'smoke','option_order':0,'body':body})
    formal=[]
    for row in cases:
        for view in ['full','related']:
            for option_order in range(2):
                body=request_body(row[view],option_order)
                formal.append({'job_id':f"{row['case_id']}__{view}__{option_order}", 'phase':'primary',
                    'case_id':row['case_id'],'input_view':view,'option_order':option_order,'body':body})
    # Stable randomized schedule, preserving separate smoke phase.
    out += sorted(formal,key=lambda x:sha((x['job_id']+'20260930').encode()))
    for job in out:
        job['request_sha256']=sha(canonical(job['body']).encode())
        # Conservative planning proxy, not an exact tokenizer or billing claim.
        job['planned_input_units']=len(canonical(job['body']).encode('utf-8'))+256
    return out

def validate_response(data, option_order):
    if data.get('model') != MODEL: raise ValueError('served_model_mismatch')
    ans=data['answers']['decision']; probs=ans['probabilities']
    if ans['type'] != 'choice' or set(probs) != set('ABC'): raise ValueError('choice_schema')
    if not all(type(v) in (int,float) and 0 <= v <= 1 for v in probs.values()): raise ValueError('probability_range')
    if abs(sum(probs.values())-1)>1e-4: raise ValueError('probability_sum')
    chosen=ans['choice']
    if chosen not in probs or probs[chosen] < max(probs.values())-1e-6: raise ValueError('choice_not_argmax')
    tokens=data.get('usage',{}).get('input_tokens')
    if type(tokens) != int or tokens < 0: raise ValueError('missing_usage')
    return {'prediction':ORDERS[option_order]['ABC'.index(chosen)],
            'probabilities':{label:probs[letter] for letter,label in zip('ABC',ORDERS[option_order])},
            'input_tokens':tokens}

def prepare():
    if (ROOT/'freeze.json').exists(): raise ValueError('Frozen preparation exists; verify it, do not overwrite')
    cache=REPO/'.local/payment-source/db.json'
    db_bytes=cache.read_bytes() if cache.exists() else urllib.request.urlopen(BASE+'data/tau2/domains/retail/db.json').read()
    db=json.loads(db_bytes); selection, counts=source_selection(db)
    vendor=ROOT/'vendor'; vendor.mkdir(parents=True,exist_ok=True)
    source_files={}
    for remote,local in [('LICENSE','LICENSE'),('data/tau2/domains/retail/policy.md','policy.md'),
                         ('src/tau2/domains/retail/tools.py','tools.py')]:
        payload=urllib.request.urlopen(BASE+remote).read(); (vendor/local).write_bytes(payload)
        source_files[local]={'url':BASE+remote,'sha256_lf':file_hash(vendor/local)}
    write(vendor/'selected_records.json',selection)
    write(ROOT/'source_manifest.json',{'revision':REV,'db_url':BASE+'data/tau2/domains/retail/db.json',
        'db_sha256':sha(db_bytes),'source_files':source_files,'eligible_user_counts':counts,
        'selection':'SHA256 seeded lexicographic pair ranking; unique users across strata; no model-based selection',
        'selected_users':12,'source_type':'public simulated database, not real customer records',
        'projection':'user_id/payment_methods; order_id/user_id/items/payment_history. Other source keys excluded uniformly.',
        'text_authorship':'AI-authored deterministic English requests; explicit IDs and unique-item/card-descriptor references',
        'retrieved_at_utc':utc()})
    cases=build_cases(selection); write_rows(ROOT/'data/cases.jsonl',cases)
    plan=make_plan(cases); write_rows(ROOT/'plans/primary.jsonl',plan)
    review=[]; mapping=[]
    for case in cases:
        for view in ['full','related']:
            rid='r_'+sha((case['case_id']+view+'review-v1').encode())[:12]
            review.append({'review_id':rid,'state':case[view]})
            mapping.append({'review_id':rid,'case_id':case['case_id'],'input_view':view})
    review.sort(key=lambda x:x['review_id'])
    write_rows(ROOT/'review/inputs.jsonl',review); write_rows(ROOT/'review/mapping.jsonl',mapping)
    fields=['review_id','reviewer_id','reviewed_at','target_order_id','destination_id','label','evidence_paths','ambiguous','notes']
    for reviewer in ['A','B']:
        with (ROOT/f'review/reviewer_{reviewer}.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
            writer.writerows({'review_id':r['review_id']} for r in review)
    return {'cases':len(cases),'parents':12,'labels':dict(Counter(c['reference'] for c in cases)),
            'planned_calls':len(plan),'planned_input_units':sum(j['planned_input_units'] for j in plan),
            'review_items_including_related_views':len(review),'eligible_users':counts}

def verify_data():
    cases=rows(ROOT/'data/cases.jsonl'); selection=read(ROOT/'vendor/selected_records.json')
    if cases != build_cases(selection): raise ValueError('Data regeneration mismatch')
    if rows(ROOT/'plans/primary.jsonl') != make_plan(cases): raise ValueError('Plan regeneration mismatch')
    assert len(cases)==48 and len({c['source_user_id'] for c in cases})==12
    assert Counter(c['reference'] for c in cases)=={LABELS[0]:24,LABELS[1]:24}
    for case in cases:
        assert not case['human_reviewed']
        for view in ['full','related']:
            parsed=parse_request(case[view])
            assert parsed['covered'] and parsed['target_id']==case['target_id'] and parsed['destination_id']==case['destination_id']
            assert parsed['prediction']==case['reference']
        full=case['full']; related=case['related']
        assert all(related[k]==full[k] for k in full if k!='orders')
        assert len(related['orders'])==1 and related['orders'][0] in full['orders']
    for parent in {c['parent_id'] for c in cases}:
        group=[c for c in cases if c['parent_id']==parent]
        assert all(c['full']['orders']==group[0]['full']['orders'] for c in group)
        assert len({c['reference'] for c in group})==(2 if group[0]['kind']=='flip' else 1)
    src=read(ROOT/'source_manifest.json')
    for name,rec in src['source_files'].items(): assert file_hash(ROOT/'vendor'/name)==rec['sha256_lf']
    return {'status':'passed','parents':12,'cases':48,'primary_calls':192,'smoke_calls':6,
            'program_parser_correct':48,'independent_human_annotations':0}

def freeze():
    verify_data()
    files=['study.py','run_api.py','report.py','PROTOCOL.md','source_manifest.json','data/cases.jsonl',
           'plans/primary.jsonl','review/inputs.jsonl','review/mapping.jsonl','vendor/selected_records.json',
           'vendor/LICENSE','vendor/policy.md','vendor/tools.py','review/reviewer_A.csv','review/reviewer_B.csv']
    payload={'study':'payment-ownership-v0.1','model':MODEL,'sha256_lf':{p:file_hash(ROOT/p) for p in files},
        'attempt_limit':405,'retry_limit':15,'planned_input_limit':2_000_000,'price_per_million_input_tokens':0.042,
        'primary_plan_units':sum(j['planned_input_units'] for j in rows(ROOT/'plans/primary.jsonl')),
        'human_reviews_at_freeze':0,'created_at_utc':utc()}
    assert payload['primary_plan_units']<payload['planned_input_limit']
    path=ROOT/'freeze.json'
    if path.exists(): return verify_freeze()
    write(path,payload); return payload

def verify_freeze():
    f=read(ROOT/'freeze.json')
    for name,h in f['sha256_lf'].items():
        if file_hash(ROOT/name)!=h: raise ValueError('Freeze mismatch: '+name)
    verify_data()
    return {'status':'passed','frozen_files':len(f['sha256_lf']),'model':f['model']}

def verify_source():
    manifest=read(ROOT/'source_manifest.json')
    payload=urllib.request.urlopen(manifest['db_url']).read()
    if sha(payload)!=manifest['db_sha256']: raise ValueError('Pinned upstream database hash mismatch')
    selection,counts=source_selection(json.loads(payload))
    assert selection==read(ROOT/'vendor/selected_records.json')
    assert counts==manifest['eligible_user_counts']
    for name,entry in manifest['source_files'].items():
        source=urllib.request.urlopen(entry['url']).read().replace(b'\r\n',b'\n')
        assert sha(source)==entry['sha256_lf']
    return {'status':'passed','source_revision':REV,'selected_users':12,'source_files':4}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','verify','freeze','verify-freeze','verify-source'])
    action={'prepare':prepare,'verify':verify_data,'freeze':freeze,'verify-freeze':verify_freeze,'verify-source':verify_source}[p.parse_args().command]
    print(json.dumps(action(),indent=2))
