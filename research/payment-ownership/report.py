"""Offline analysis and self-contained viewers; never invokes a model."""
from __future__ import annotations
import argparse
import json
import statistics
from collections import Counter
from study import ROOT, LABELS, PRICE, canonical, read, rows, sha, parse_request, validate_response, verify_freeze, write
from run_api import accounting

def summarize():
    verify_freeze()
    cases=rows(ROOT/'data/cases.jsonl'); jobs=rows(ROOT/'plans/primary.jsonl')
    records=rows(ROOT/'results/responses.jsonl'); events=rows(ROOT/'results/attempts.jsonl')
    planned={j['job_id']:j for j in jobs}; seen=set()
    for r in records:
        assert r['job_id'] not in seen; seen.add(r['job_id']); j=planned[r['job_id']]
        assert r['request_sha256']==j['request_sha256']
        assert all(r[k]==j[k] for k in ['case_id','phase','input_view','option_order'])
        if r['ok']:
            parsed=validate_response(r['raw_response'],r['option_order'])
            assert all(r[k]==parsed[k] for k in parsed)
        matches=[e for e in events if e['event']=='finished' and e['attempt_id']==r['attempt_id']]
        assert len(matches)==1 and matches[0]['job_id']==r['job_id'] and matches[0]['raw_response']==r['raw_response']
    stats=accounting(events)
    stats['usage_estimated_cost_usd']=stats['known_input_tokens']*PRICE
    stats['usage_cost_is_invoice']=False
    parent_ids=sorted({c['parent_id'] for c in cases})
    index={(r['case_id'],r['input_view'],r['option_order']):r for r in records if r['phase']=='primary'}
    metrics={}; decisions={}
    for view in ['full','related']:
        for mapping in [0,1,'mean']:
            key=f'{view}_{mapping}'; pred={}
            for c in cases:
                rr=[index.get((c['case_id'],view,m)) for m in [0,1]]
                if mapping=='mean':
                    if not all(r and r['ok'] for r in rr): continue
                    probs={l:sum(r['probabilities'][l] for r in rr)/2 for l in LABELS}
                    pred[c['case_id']]=max(LABELS,key=lambda l:probs[l])
                elif rr[mapping] and rr[mapping]['ok']:
                    pred[c['case_id']]=rr[mapping]['prediction']
            decisions[key]=pred
            complete=sum(all(pred.get(c['case_id'])==c['reference'] for c in cases if c['parent_id']==p) for p in parent_ids)
            metrics[key]={'available':len(pred),'correct':sum(pred.get(c['case_id'])==c['reference'] for c in cases),
                'total':len(cases),'complete_four_view_parents':complete,'parents':12,
                'wrong_valid_among_invalid':sum(pred.get(c['case_id'])==LABELS[0] for c in cases if c['reference']==LABELS[1]),
                'invalid_reference_denominator':24,'needless_deferrals':sum(v==LABELS[2] for v in pred.values()),
                'determined_denominator':48,'unknown_reference_denominator':0,
                'by_style':{s:{'correct':sum(pred.get(c['case_id'])==c['reference'] for c in cases if c['style']==s),
                              'total':24,'complete_target_pairs':sum(all(pred.get(c['case_id'])==c['reference'] for c in cases if c['parent_id']==p and c['style']==s) for p in parent_ids)}
                            for s in ['explicit','item_reference']}}
    transitions=[]
    for c in cases:
        f=decisions['full_0'].get(c['case_id']);r=decisions['related_0'].get(c['case_id'])
        if f is not None and r is not None:
            transitions.append({'case_id':c['case_id'],'parent_id':c['parent_id'],'reference':c['reference'],
                                'full':f,'related':r,'full_correct':f==c['reference'],'related_correct':r==c['reference']})
    smoke=[r for r in records if r['phase']=='smoke']
    complete=len(records)==198 and all(r['ok'] for r in records) and not stats['unfinished']
    near_pass=complete and metrics['full_0']['correct']==48 and metrics['full_1']['correct']>=47
    verdict=('STOP_NO_FOLLOWUP' if near_pass else 'REVIEW_ONE_ERROR_CLASS' if complete else 'INCOMPLETE')
    lat=[r['latency_s'] for r in records if r['ok']]
    return {'status':'completed' if complete else 'incomplete','parents':12,'views':48,
        'main_reference_counts':dict(Counter(c['reference'] for c in cases)),
        'independent_human_annotations':0,'smoke':{'recorded':len(smoke),'correct':sum(r.get('prediction')==planned[r['job_id']]['reference'] for r in smoke)},
        'primary_recorded':sum(r['phase']=='primary' for r in records),'accounting':stats,'metrics':metrics,
        'primary_transitions':transitions,'full_order_disagreements':sum(decisions['full_0'].get(c['case_id'])!=decisions['full_1'].get(c['case_id']) for c in cases),
        'controls':{'finite_parser_correct':sum(parse_request(c['full'])['prediction']==c['reference'] for c in cases),
            'always_valid_correct':24,'always_invalid_correct':24,'always_defer_correct':0,
            'always_valid_complete_parents':3,'always_invalid_complete_parents':3,'always_defer_complete_parents':0},
        'median_request_latency_s':statistics.median(lat) if lat else None,
        'summed_successful_request_latency_s':sum(lat),
        'continuation':verdict,'followup_calls':0,
        'basis':'Exploratory constructed component test; program labels; review pending; no other model scored.'}

def result_markdown(s):
    lines=['# Right Payment, Wrong Order? — Jev results','',
        f"**Status: {s['status']}. Independent human annotations: 0.**",'',
        'This is a static diagnostic derived from a public simulated tau retail database.',
        'It is not a tau-bench agent score, real-customer evaluation, or confirmed generalization result.','',
        '|Condition|Correct views /48|Complete four-view parents /12|Wrong VALID /24 invalid|Needless deferrals /48|',
        '|---|---:|---:|---:|---:|']
    for key,m in s['metrics'].items():
        lines.append(f"|{key}|{m['correct']}|{m['complete_four_view_parents']}|{m['wrong_valid_among_invalid']}|{m['needless_deferrals']}|")
    lines += ['|Finite-language parser + rules|48|12|0|0|','|Always VALID|24|3|24|0|',
              '|Always INVALID|24|3|0|0|','|Always NOT_ESTABLISHED|0|0|0|48|','',
        '`0` is the prespecified primary option mapping; `1` is its reverse. `mean`',
        'averages semantic probabilities over those two mappings. Each condition has',
        '24 explicit-ID and 24 item-reference views. Detailed counts are in summary.json.','',
        'The related-evidence condition was selected using construction metadata. It',
        'remains pending independent review and is not a deployable repair method.',
        'All 48 main references are determined (24 VALID, 24 INVALID). There are zero',
        'main missing-evidence cases; unknown-state reliability cannot be estimated.','',
        '## Actual execution','',
        f"- Smoke: {s['smoke']['correct']}/{s['smoke']['recorded']}; main terminal records: {s['primary_recorded']}/192.",
        f"- HTTP attempts: {s['accounting']['attempts']}; retries: {s['accounting']['retries']}; unknown-usage attempts: {s['accounting']['unknown_usage_attempts']}.",
        f"- Provider-reported input tokens: {s['accounting']['known_input_tokens']:,}; conservative planned input units used: {s['accounting']['planned_input_units']:,}.",
        f"- Usage-estimated cost: ${s['accounting']['usage_estimated_cost_usd']:.8f}, at $0.042/M input tokens. This is not an invoice.",
        f"- Median successful request latency: {s['median_request_latency_s']} seconds; includes network/service latency.",
        f"- Full-input option-order disagreements: {s['full_order_disagreements']}/48.",'',
        'All raw responses, probabilities, timing, failures and accounting events are retained.',
        'The 192 calls are repeated measurements of 12 source-user groups, not 192 independent examples.','',
        '## Stage decision','',f"**{s['continuation']}**. Follow-up model calls: 0.",'']
    if s['continuation']=='STOP_NO_FOLLOWUP':
        lines += ['Jev meets the prespecified near-pass stopping rule on this construction.',
            'Do not add harder cases to force a failure or spend the unused follow-up allocation.',
            'The finite-language program also solves the task. This stage supplies a bounded',
            'negative result for the proposed failure hypothesis, not evidence that either',
            'Jev or a learned method is necessary. No ordinary-model comparison has run.','']
    else:
        lines += ['Inspect every error and provisional label before choosing at most one follow-up.',
                  'No follow-up is approved by this report alone; its exact inputs must first be frozen',
                  'under the existing user authorization and shared stage budget.','']
    lines += ['## Reproduce and audit','',
        'Run `python research/payment-ownership/study.py verify-freeze` and',
        '`python research/payment-ownership/report.py --verify` from the repository root.',
        'These checks are offline and never call a model. Open [the replay](../../docs/payment_ownership.html).',
        'See [the protocol](PROTOCOL.md), [data and source notes](README.md),',
        '[review instructions](review/README.md), and [nearest-work assessment](RELATED_WORK.md).','']
    return '\n'.join(lines)

STYLE='''body{font:16px/1.6 system-ui,sans-serif;margin:0;background:#f4f6f9;color:#18243a}main{max-width:1150px;margin:auto;padding:32px}h1{line-height:1.15;font-size:36px}select,button,input,textarea{font:inherit;padding:8px;max-width:100%}select{margin-right:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:18px;border:1px solid #d5ddea;border-radius:8px;font-size:13px}section{margin:20px 0}.tag{background:#e0e8f5;padding:8px;border-radius:6px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}label{display:inline-block;margin:8px 12px 8px 0}textarea{width:95%;min-height:70px}@media(max-width:760px){.grid{grid-template-columns:1fr}h1{font-size:28px}}'''

def replay_html(summary):
    payload={'summary':summary,'cases':rows(ROOT/'data/cases.jsonl'),'jobs':rows(ROOT/'plans/primary.jsonl'),
             'records':rows(ROOT/'results/responses.jsonl')}
    data=canonical(payload).replace('<','\\u003c')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Right Payment, Wrong Order?</title><style>'''+STYLE+'''</style><main>
<p>JEV SCOPE CHALLENGE · EXPLORATORY RESEARCH</p><h1>Right Payment, Wrong Order?</h1>
<p>Switch the target and inspect what Jev actually returned. Public simulated source records; AI-authored requests; independent human review pending.</p>
<p class="tag" id="summary"></p><p>This tests only a refund-destination restriction. A VALID result does not authorize a full return. No live API calls occur in this page.</p>
<section><label>Case <select id="case"></select></label><label>Evidence <select id="view"><option value="full">Full records</option><option value="related">Program-selected related records</option></select></label><label>Option mapping <select id="mapping"><option value="0">Primary</option><option value="1">Reverse</option></select></label></section>
<p id="outcome" class="tag"></p><div class="grid"><section><h2>Exact API request</h2><pre id="request"></pre></section><section><h2>Saved service response</h2><pre id="response"></pre><h2>Program reference — not a human label</h2><pre id="reference"></pre></section></div>
<p>Related evidence was chosen with construction metadata and has not been independently reviewed. It is a diagnostic condition, not deployable filtering. Only two option orders were tested.</p>
<p><a href="../research/payment-ownership/RESULTS.md">Complete report</a> · <a href="../research/payment-ownership/PROTOCOL.md">Frozen protocol</a> · <a href="../research/payment-ownership/README.md">Source and limitations</a></p></main>
<script>const data='''+data+'''; const el=id=>document.getElementById(id);
for(const c of data.cases){const o=document.createElement('option');o.value=c.case_id;o.textContent=c.case_id+' · '+c.kind;el('case').append(o)}
const s=data.summary;el('summary').textContent=`${s.status}: ${s.primary_recorded}/192 main responses · ${s.parents} source-user groups · ${s.accounting.known_input_tokens.toLocaleString()} input tokens · ${s.continuation}`;
function render(){const c=data.cases.find(x=>x.case_id===el('case').value),v=el('view').value,m=+el('mapping').value;
const j=data.jobs.find(x=>x.case_id===c.case_id&&x.input_view===v&&x.option_order===m),r=data.records.find(x=>x.job_id===j.job_id);
el('request').textContent=JSON.stringify(j.body,null,2);el('response').textContent=JSON.stringify(r?r.raw_response:{status:'Not run'},null,2);
el('reference').textContent=JSON.stringify({label:c.reference,target_order:c.target_id,destination:c.destination_id,provenance:c.reference_provenance},null,2);
el('outcome').textContent=r?`Observed: ${r.prediction||r.error} · Program reference: ${c.reference} · ${r.input_tokens} input tokens · ${r.latency_s.toFixed(3)} s`:'No model response recorded';}
for(const id of ['case','view','mapping'])el(id).addEventListener('change',render);render();</script></html>'''

def review_html():
    data=canonical(rows(ROOT/'review/inputs.jsonl')).replace('<','\\u003c')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Payment ownership independent review</title><style>'''+STYLE+'''</style><main><h1>Independent semantic review</h1><p>No model outputs, construction labels or pair IDs are embedded here. Review each item before discussing with another reviewer. Save and export your own CSV. This page does not certify independence.</p>
<label>Reviewer ID <input id="reviewer"></label><label>Item <select id="item"></select></label><button id="save">Save item</button> <button id="export">Export CSV</button><p id="status"></p><pre id="state"></pre>
<label>Target order ID <input id="target_order_id"></label><label>Destination ID <input id="destination_id"></label><label>Label <select id="label"><option value="">Choose…</option><option>VALID_DESTINATION</option><option>INVALID_DESTINATION</option><option>NOT_ESTABLISHED</option></select></label><label>Ambiguous <select id="ambiguous"><option value="">Choose…</option><option>yes</option><option>no</option></select></label>
<p>For an unresolvable identity, enter UNRESOLVED. Evidence paths can name multiple records; explain why they apply to this target.</p><label>Evidence paths<textarea id="evidence_paths"></textarea></label><label>Reason / ambiguity / notes<textarea id="notes"></textarea></label></main>
<script>const items='''+data+''';const el=id=>document.getElementById(id);const fields=['target_order_id','destination_id','label','evidence_paths','ambiguous','notes'];let saved={};
for(const r of items){const o=document.createElement('option');o.value=r.review_id;o.textContent=r.review_id;el('item').append(o)}
function key(){return 'payment-review-v1-'+el('reviewer').value.trim()}
function load(){el('state').textContent=JSON.stringify(items.find(r=>r.review_id===el('item').value).state,null,2);for(const f of fields)el(f).value=(saved[el('item').value]||{})[f]||'';}
el('reviewer').onchange=()=>{try{saved=JSON.parse(localStorage.getItem(key())||'{}')}catch(e){saved={}}load()};el('item').onchange=load;
el('save').onclick=()=>{if(!el('reviewer').value.trim()){el('status').textContent='Enter a reviewer ID first.';return}const r={review_id:el('item').value,reviewer_id:el('reviewer').value.trim(),reviewed_at:new Date().toISOString()};for(const f of fields)r[f]=el(f).value;saved[r.review_id]=r;try{localStorage.setItem(key(),JSON.stringify(saved));el('status').textContent='Saved locally. Export the CSV before leaving.'}catch(e){el('status').textContent='Browser storage unavailable. Export now to retain this session.'}};
el('export').onclick=()=>{const cols=['review_id','reviewer_id','reviewed_at',...fields],q=x=>'"'+String(x??'').replaceAll('"','""')+'"';const lines=[cols.map(q).join(',')];for(const i of items){const r=saved[i.review_id]||{review_id:i.review_id};lines.push(cols.map(c=>q(r[c])).join(','))}const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([lines.join('\\r\\n')],{type:'text/csv;charset=utf-8'}));a.download='payment_review.csv';a.click();URL.revokeObjectURL(a.href)};load();</script></html>'''

def publish(verify=False):
    s=summarize()
    outputs={ROOT/'results/summary.json':json.dumps(s,indent=2,ensure_ascii=False,allow_nan=False)+'\n',
             ROOT/'RESULTS.md':result_markdown(s),ROOT/'review/review.html':review_html(),
             ROOT.parents[1]/'docs/payment_ownership.html':replay_html(s)}
    for path,text in outputs.items():
        if verify:
            if not path.exists() or path.read_text(encoding='utf-8')!=text: raise ValueError('Generated artifact mismatch: '+str(path))
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    return {'status':'verified' if verify else 'written','primary':s['primary_recorded'],'decision':s['continuation'],'accounting':s['accounting']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true')
    print(json.dumps(publish(p.parse_args().verify),indent=2))
