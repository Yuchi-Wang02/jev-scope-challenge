"""Offline verification and grouped analysis of actual matched-base records."""
import argparse
import csv
import html
import json
import math
from pathlib import Path
from study import HERE, MAPS, LABELS, OPTIONS, canonical, freeze, gold_for, native_prompt, read_rows, sha, validate, write_json

GRID = [.25,.5,.75,1,1.5,2,3,4,6,8]


def probabilities(z, temperature=1.):
    maximum = max(z)
    weights = [math.exp((v-maximum)/temperature) for v in z]
    return [v/sum(weights) for v in weights]


def stats(rows, cases, temperature=1.):
    correct, briers, nlls, accepted_errors = [], [], [], []
    parent_hits = {}
    grouped = {}
    for row in rows:
        gold = cases[row['id']]['gold']
        probs = probabilities(row['logits'], temperature)
        label = row['order'].index(gold)
        hit = row['prediction'] == gold
        correct.append(hit)
        briers.append(sum((p-int(i==label))**2 for i,p in enumerate(probs)))
        nlls.append(-math.log(max(probs[label],1e-30)))
        parent_hits.setdefault(row['parent'], []).append(hit)
        grouped.setdefault(row['id'], []).append(row['prediction'])
        if max(probs) >= .9:
            accepted_errors.append(not hit)
    missing = [r for r in rows if r['variant'] == 'missing']
    result = {'decisions':len(rows),'parents':len(parent_hits),'correct':sum(correct),
              'complete_parents':sum(all(v) and len(v)==12 for v in parent_hits.values()),
              'accuracy':sum(correct)/len(rows),'nll':sum(nlls)/len(rows),'brier_multiclass':sum(briers)/len(rows),
              'missing_false_acceptance':sum(r['prediction']!='INSUFFICIENT' for r in missing),
              'missing_decisions':len(missing),'order_sensitive_inputs':sum(len(set(v))>1 for v in grouped.values()),
              'temperature':temperature,'coverage_at_0_9':len(accepted_errors)/len(rows),
              'error_at_0_9':sum(accepted_errors)/len(accepted_errors) if accepted_errors else None}
    for kind in ('flip','hold'):
        pairs = []
        index = {(r['parent'],r['variant'],r['mapping']):r for r in rows}
        for parent in parent_hits:
            for mapping in range(3):
                a, b = index[parent,'full',mapping], index[parent,kind,mapping]
                pairs.append(a['prediction']==cases[a['id']]['gold'] and b['prediction']==cases[b['id']]['gold'])
        result[kind+'_correct_pairs'] = sum(pairs)
        result[kind+'_pairs'] = len(pairs)
    return result


def analyze(write=True):
    manifest = freeze()
    cases_list = read_rows(HERE/'data/cases.jsonl')
    validate(cases_list)
    cases = {c['id']:c for c in cases_list}
    expected = {(c['id'],m) for c in cases_list for m in range(3)}
    results, all_rows = {}, []
    for arm in ('N0','N1','K1'):
        path = HERE/f'results/{arm}.jsonl'
        rows = read_rows(path)
        keys = [(r['id'],r['mapping']) for r in rows]
        if len(keys) != len(expected) or set(keys) != expected:
            raise ValueError(f'{arm}: incomplete or duplicate grid')
        for row in rows:
            case = cases[row['id']]
            if row['config_hash'] != manifest['config_hash'] or row['arm'] != arm or not row['ok'] or row['order'] != MAPS[row['mapping']]:
                raise ValueError('Invalid record identity')
            for field in ('parent','family','variant','split'):
                if row[field] != case[field]:
                    raise ValueError('Record/data metadata mismatch')
            p = probabilities(row['logits'])
            if len(p) != 3 or len(row['probabilities']) != 3 or any(not math.isfinite(z) for z in row['logits']) or any(not math.isclose(a,b,rel_tol=2e-5,abs_tol=1e-7) for a,b in zip(p,row['probabilities'])):
                raise ValueError('Logit/probability mismatch')
            if row['prediction'] != row['order'][max(range(3),key=p.__getitem__)] or row['input_tokens'] != len(row['token_ids']):
                raise ValueError('Prediction/token mismatch')
            if arm in ('N0','N1'):
                if row['prompt'] != native_prompt(case,row['order']) or row['prompt_sha256'] != sha(row['prompt'].encode()):
                    raise ValueError('Native prompt mismatch')
            elif row['state'] != case['state'] or row['instruction'] != case['instruction'] or row['options'] != [OPTIONS[x] for x in row['order']]:
                raise ValueError('Pointer payload mismatch')
        calibration = [r for r in rows if r['split']=='calibration']
        chosen = min(GRID,key=lambda t:stats(calibration,cases,t)['nll'])
        results[arm] = {'file_sha256_lf':sha(path.read_bytes().replace(b'\r\n',b'\n')),
                        'calibration_temperature':chosen,'splits':{}}
        for split in ('development','calibration','exploratory_test'):
            panel = [r for r in rows if r['split']==split]
            results[arm]['splits'][split] = {'raw':stats(panel,cases),'calibrated':stats(panel,cases,chosen)}
        all_rows.extend(rows)
    # N0 and N1 must literally see the same token sequences, prompts and slots.
    a = {(r['id'],r['mapping']):r for r in all_rows if r['arm']=='N0'}
    b = {(r['id'],r['mapping']):r for r in all_rows if r['arm']=='N1'}
    for key in expected:
        if any(a[key][field] != b[key][field] for field in ('prompt','token_ids','candidate_ids','order')):
            raise ValueError('N0/N1 input or scoring slot changed')
    summary = {'status':'complete_exploratory_pilot','config_hash':manifest['config_hash'],'model_forward_records':len(all_rows),
               'independent_human_reviewed':False,'new_training':False,'paid_api_calls':0,'results':results,
               'C0':{'description':'structured-fact rule oracle, no natural-language parsing','parents':24,'complete_parents':24},
               'limitations':['Original synthetic facts and AI review only','12 exploratory-test parents; no confirmatory population inference',
                             'One historical adapter and one native prompt','K1 changes representation and readout','Calibration has only six parents']}
    if not write:
        return summary
    write_json(HERE/'results/summary.json',summary)
    with (HERE/'results/decisions.csv').open('w',encoding='utf-8',newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['arm','parent','id','split','variant','mapping','gold','prediction','correct'])
        for row in all_rows:
            writer.writerow([row['arm'],row['parent'],row['id'],row['split'],row['variant'],row['mapping'],cases[row['id']]['gold'],row['prediction'],row['prediction']==cases[row['id']]['gold']])
    text = ['# Is the Decision Model Better Than the Model It Came From?','',
            'Real local exploratory pilot. No new training or paid API. Gold labels are rule-generated and AI checked; no independent human audit.','',
            '## Exploratory test (12 parents, 144 decisions per model)','','|Arm|Complete parents|Correct decisions|Missing false acceptance|Order-sensitive inputs|Raw NLL|',
            '|---|---:|---:|---:|---:|---:|']
    for arm, values in results.items():
        s = values['splits']['exploratory_test']['raw']
        text.append(f"|{arm}|{s['complete_parents']}/{s['parents']}|{s['correct']}/{s['decisions']}|{s['missing_false_acceptance']}/{s['missing_decisions']}|{s['order_sensitive_inputs']}|{s['nll']:.3f}|")
    text.extend(['','N0 is the unchanged Base/native LM head. N1 adds the public LoRA through the same native path. K1 uses that adapted backbone with the trained historical pointer path.',
                 '', 'N0/N1 prompt, token and answer-slot identity is checked offline. K1 differs in layout and readout, so differences are system-level. Neither a small win nor a loss establishes general training necessity or model superiority.',
                 '', 'All development/calibration/test scores, raw and separately calibrated probability metrics are in summary.json. The .9 acceptance threshold was fixed before inference. An empty accepted set has undefined risk, not zero risk.',
                 '', 'The code oracle solves structured facts used to construct the labels; it is not a general parser. Parent groups and style splits, rather than individual decisions, define independent units.',
                 '', 'These results are an exploratory extension of upstream Kev diagnostics. A paper requires independent label review, new sources, matched interventions and broader validation.'])
    (HERE/'results/REPORT.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    payload = json.dumps({'cases':cases_list,'rows':all_rows,'summary':summary},ensure_ascii=False).replace('</','<\\/')
    template = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Same Base, Different Decisions</title>
<style>body{font:16px/1.5 system-ui;max-width:1100px;margin:auto;padding:24px;background:#faf8f3;color:#23332c}h1{font-size:36px}select{padding:10px;max-width:100%;font:inherit}article{background:white;padding:20px;border:1px solid #b9c9be;border-radius:12px;margin:15px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}.good{color:#137358}.bad{color:#bc4439}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:8px;border-bottom:1px solid #ddd}.wrap{overflow:auto}summary{cursor:pointer}</style>
<h1>Same Base. Different Decisions.</h1><p>Original LM head → trained LoRA → trained decision head.</p><p>Replay of 864 real saved model forwards. Synthetic exploratory pilot; no independent human labels. Changing a selector makes no model call.</p><div class="wrap"><table id="scores"></table></div><label>Parent <select id="parent"></select></label> <label>Candidate order <select id="mapping"><option value="0">ALLOW, DENY, INSUFFICIENT</option><option value="1">DENY, INSUFFICIENT, ALLOW</option><option value="2">INSUFFICIENT, ALLOW, DENY</option></select></label><div id="cards"></div>
<p>N0/N1 share identical inputs/readout. K1 changes representation and readout. Probabilities are conditional candidate distributions, not correctness guarantees. Data and raw records accompany this file.</p><script>const D=__PAYLOAD__;
const E=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const p=document.getElementById('parent'),m=document.getElementById('mapping');p.innerHTML=[...new Set(D.cases.map(c=>c.parent))].map(x=>`<option>${E(x)}</option>`).join('');
document.getElementById('scores').innerHTML='<tr><th>Exploratory test</th><th>Complete parents</th><th>Correct decisions</th></tr>'+Object.entries(D.summary.results).map(([a,v])=>{const s=v.splits.exploratory_test.raw;return `<tr><td>${a}</td><td>${s.complete_parents}/${s.parents}</td><td>${s.correct}/${s.decisions}</td></tr>`}).join('');
function render(){document.getElementById('cards').innerHTML=D.cases.filter(c=>c.parent===p.value).map(c=>`<article><h2>${E(c.variant)} · expected ${E(c.gold)}</h2><pre>${E(c.state)}</pre><p>${E(c.instruction)}</p><div class="wrap"><table><tr><th>Arm</th><th>Decision</th><th>ALLOW / DENY / INSUFFICIENT</th></tr>${D.rows.filter(r=>r.id===c.id&&r.mapping===Number(m.value)).map(r=>{const prob=Object.fromEntries(r.order.map((k,i)=>[k,r.probabilities[i]]));return `<tr><td>${r.arm}</td><td class="${r.prediction===c.gold?'good':'bad'}">${E(r.prediction)}</td><td>${['ALLOW','DENY','INSUFFICIENT'].map(k=>prob[k].toFixed(4)).join(' / ')}</td></tr>`}).join('')}</table></div><details><summary>Inspect exact saved records</summary><pre>${E(JSON.stringify(D.rows.filter(r=>r.id===c.id&&r.mapping===Number(m.value)),null,2))}</pre></details></article>`).join('');}p.onchange=m.onchange=render;render();</script></html>'''
    (HERE/'explorer.html').write_text(template.replace('__PAYLOAD__',payload),encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    args = parser.parse_args()
    prior = json.loads((HERE/'results/summary.json').read_text(encoding='utf-8')) if args.verify else None
    summary = analyze(write=not args.verify)
    if args.verify and prior != summary:
        raise ValueError('Stored study summary differs from independent recomputation')
    print(json.dumps({a:v['splits']['exploratory_test']['raw'] for a,v in summary['results'].items()},indent=2))
