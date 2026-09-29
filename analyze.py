"""Recompute the release from real saved records; no model/API calls."""
from __future__ import annotations
import argparse
import csv
import html
import json
from pathlib import Path
import numpy as np
from core import (MAPPINGS, SEED, grammar_reference, keyword_reference, read_jsonl,
                  request_for, score_records)
from run import ROOT, sha_file, verify_manifest

def references(cases):
    rows={name:[] for name in ['always_keep','keyword','known_grammar']}
    for case in cases:
        state={'target':case['target'],'customer_message':case['customer_message']}
        outputs={'always_keep':'KEEP','keyword':keyword_reference(state),'known_grammar':grammar_reference(state)}
        for name,prediction in outputs.items():
            for rep in [0,1]:
                for mapping in MAPPINGS:
                    rows[name].append({'case_id':case['id'],'mapping':mapping,'replicate':rep,
                                     'ok':prediction is not None,'prediction':prediction})
    return rows

def recompute():
    manifest=verify_manifest()
    cases=read_jsonl(ROOT/'data/cases.jsonl')
    predictions={b:read_jsonl(ROOT/f'results/{b}_formal.jsonl') for b in ['jev','qwen']}
    for backend,rows in predictions.items():
        assert len(rows)==192, f'{backend}: incomplete formal run, {len(rows)}/192'
        expected={(c['id'],m,r) for c in cases for m in MAPPINGS for r in [0,1]}
        actual={(r['case_id'],r['mapping'],r['replicate']) for r in rows}
        assert actual==expected and len(actual)==len(rows)
        for row in rows:
            assert row['config_hash']==manifest['config_hash']
            case=next(c for c in cases if c['id']==row['case_id'])
            assert row['request']==request_for(case,row['mapping'])
            if row['ok']:
                assert row['prediction']==MAPPINGS[row['mapping']][row['letter']]
                assert abs(sum(row['probabilities'].values())-1)<1e-4
    all_predictions={**predictions,**references(cases)}
    summary={'experiment':manifest['experiment'],'config_hash':manifest['config_hash'],
             'data_sha256':manifest['data_sha256'],'models':{},'references':{},
             'human_reviewed':False,'round0_primary':True}
    for name,rows in all_predictions.items():
        scores={str(rep):score_records(cases,rows,rep) for rep in [0,1]}
        where='models' if name in predictions else 'references'
        entry={'rounds':scores}
        if name in predictions:
            index={(r['case_id'],r['mapping'],r['replicate']):r for r in rows}
            entry['repeat_disagreements']=sum(
                index[c['id'],m,0].get('prediction')!=index[c['id'],m,1].get('prediction')
                for c in cases for m in MAPPINGS)
            times=[r['latency_s'] for r in rows if r.get('ok') and 'latency_s' in r]
            entry['latency_s']={k:float(np.percentile(times,q)) for k,q in [('median',50),('p95',95)]}
            entry['total_decision_time_s']=sum(times)
            entry['formal_input_tokens']=sum(r.get('input_tokens') or 0 for r in rows)
            entry['missing_usage']=sum(r.get('input_tokens') is None for r in rows)
            if name=='qwen':
                mass=[r['candidate_mass'] for r in rows if r.get('ok')]
                entry['candidate_mass']={'min':min(mass),'median':float(np.median(mass)),
                                         'low_mass_under_0.01':sum(v<0.01 for v in mass)}
        summary[where][name]=entry
    ledger=read_jsonl(ROOT/'results/jev_attempts.jsonl')
    finished=[r for r in ledger if r['event']=='attempt_finished']
    summary['jev_usage']={'http_attempts':sum(r['event']=='attempt_started' for r in ledger),
        'finished_attempts':len(finished),'known_input_tokens':sum(r.get('input_tokens') or 0 for r in finished),
        'unknown_cost_attempts':sum(not r['cost_known'] for r in finished),
        'usage_estimated_usd':sum(r['known_cost_usd'] for r in finished),
        'includes_smoke':True,'account_bill_verified':False}
    parents=sorted({c['parent_id'] for c in cases})
    diff=np.array([int(summary['models']['qwen']['rounds']['0']['parent_pass'][p])-
                   int(summary['models']['jev']['rounds']['0']['parent_pass'][p]) for p in parents])
    rng=np.random.default_rng(SEED)
    samples=diff[rng.integers(0,len(parents),size=(10000,len(parents)))].mean(axis=1)
    summary['within_probe_reweighting']={'qwen_minus_jev_pass_rate':float(diff.mean()),
        'percentile_95':np.percentile(samples,[2.5,97.5]).tolist(),
        'interpretation':'Within these purposively constructed cases only; not population CI or equivalence.'}
    signs=[]
    for rep in ['0','1']:
        for mapping in MAPPINGS:
            q=summary['models']['qwen']['rounds'][rep]['mapping_pass'][mapping]
            j=summary['models']['jev']['rounds'][rep]['mapping_pass'][mapping]
            signs.append(int(np.sign(q-j)))
    summary['ranking_signs_by_round_and_mapping']=signs
    summary['stable_strict_direction']=signs[0] if signs[0]!=0 and all(s==signs[0] for s in signs) else 0
    summary['result_files_sha256']={f'{b}_formal.jsonl':sha_file(ROOT/f'results/{b}_formal.jsonl') for b in predictions}
    return cases,predictions,all_predictions,summary

def figure(cases,predictions,summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    parents=sorted({c['parent_id'] for c in cases})
    fig,axes=plt.subplots(1,2,figsize=(12,7),sharey=True)
    fig.patch.set_facecolor('#faf8f3')
    for ax,backend,label in zip(axes,['jev','qwen'],['Jev 1.13.0','Frozen Qwen3-4B']):
        index={(r['case_id'],r['mapping']):r for r in predictions[backend] if r['replicate']==0}
        matrix=[]
        for p in parents:
            row=[]
            for m in MAPPINGS:
                for v in 'ABCD':
                    r=index[(p+'-'+v,m)]
                    c=next(c for c in cases if c['id']==p+'-'+v)
                    row.append(int(r['ok'] and r.get('prediction')==c['gold']))
            matrix.append(row)
        ax.imshow(matrix,cmap=ListedColormap(['#e66c5c','#278578']),vmin=0,vmax=1,aspect='auto')
        for y,row in enumerate(matrix):
            for x,v in enumerate(row): ax.text(x,y,'OK' if v else 'X',ha='center',va='center',color='white',fontsize=9)
        score=summary['models'][backend]['rounds']['0']
        ax.set_title(f'{label}\n{score["robust_pass"]}/12 complete cases | {score["correct"]}/96 decisions',fontsize=13,pad=15)
        ax.set_xticks(range(8),['A','B','C','D','A','B','C','D'])
        ax.set_yticks(range(len(parents)),parents)
        ax.set_xlabel('A=CANCEL, B=KEEP       A=KEEP, B=CANCEL',fontsize=9,labelpad=12)
        ax.axvline(3.5,color='#faf8f3',linewidth=3)
        for s in ax.spines.values(): s.set_visible(False)
    axes[0].set_ylabel('Predefined case (Q: quote, S: object, T: current request)')
    fig.suptitle('Cancel the Right Thing\nSame words. Different scope. Opposite decisions.',fontsize=19,y=0.99)
    fig.legend(handles=[Patch(color='#278578',label='Correct'),Patch(color='#e66c5c',label='Incorrect or failed')],
               loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(0.5,0.055))
    fig.text(0.5,0.015,'Primary round only. Four variants x two mappings per case. Synthetic probe; no independent human audit.',
             ha='center',fontsize=9,color='#555555')
    fig.tight_layout(rect=[0,0.10,1,0.90])
    (ROOT/'assets').mkdir(exist_ok=True)
    fig.savefig(ROOT/'assets/scope-results.png',dpi=180,facecolor=fig.get_facecolor())
    fig.savefig(ROOT/'assets/scope-results.svg',facecolor=fig.get_facecolor())
    plt.close(fig)

def write_tables(cases,predictions,summary):
    parents=sorted({c['parent_id'] for c in cases})
    with (ROOT/'results/case_scores.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['parent','family','jev_round0_complete','qwen_round0_complete','jev_round1_complete','qwen_round1_complete'])
        for p in parents:
            family=next(c['family'] for c in cases if c['parent_id']==p)
            writer.writerow([p,family]+[int(summary['models'][b]['rounds'][r]['parent_pass'][p])
                                      for r in ['0','1'] for b in ['jev','qwen']])
    with (ROOT/'results/decisions.csv').open('w',encoding='utf-8',newline='') as f:
        fields=['backend','case_id','replicate','mapping','gold','prediction','correct','p_cancel','p_keep','candidate_mass','latency_s','ok']
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        golds={c['id']:c['gold'] for c in cases}
        for b,rows in predictions.items():
            for r in rows:
                writer.writerow({'backend':b,'case_id':r['case_id'],'replicate':r['replicate'],'mapping':r['mapping'],
                    'gold':golds[r['case_id']],'prediction':r.get('prediction'),
                    'correct':r['ok'] and r.get('prediction')==golds[r['case_id']],
                    'p_cancel':r.get('probabilities',{}).get('CANCEL'),'p_keep':r.get('probabilities',{}).get('KEEP'),
                    'candidate_mass':r.get('candidate_mass'),'latency_s':r.get('latency_s'),'ok':r['ok']})

def explorer(cases,predictions,summary):
    payload=json.dumps({'cases':cases,'predictions':predictions,'summary':summary},ensure_ascii=False).replace('</','<\/')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cancel the Right Thing — saved result explorer</title><style>
body{font:16px/1.5 system-ui;background:#faf8f3;color:#202924;max-width:1100px;margin:auto;padding:25px}
h1{font-size:36px;line-height:1.1}h2{font-size:20px}select{padding:9px;margin:5px;font:inherit;border:1px solid #a5b8ae;border-radius:6px}
.note{color:#59655e}.grid{display:grid;grid-template-columns:1fr 1fr;gap:15px}.card{background:white;border:1px solid #cdd8d0;border-radius:12px;padding:20px}
.good{color:#127467}.bad{color:#c34a3b}.model{display:flex;justify-content:space-between;border-top:1px solid #ddd;padding:12px 0}
table{border-collapse:collapse;width:100%}td,th{padding:8px;border-bottom:1px solid #ddd;text-align:left}pre{overflow:auto;font-size:12px;background:#f0f3ef;padding:10px}
@media(max-width:700px){.grid{grid-template-columns:1fr}h1{font-size:28px}}
</style><h1>Cancel the Right Thing</h1><p>Same words. Different scope. Opposite decisions.</p>
<p class="note">Replay of real saved runs. No live inference, API requests, or simulated scores. Synthetic probe; no independent human label audit.</p>
<p id="scores"></p><label>Case <select id="parent"></select></label><label>Round <select id="round"><option value="0">0 — primary</option><option value="1">1 — repeat</option></select></label>
<label>Mapping <select id="mapping"><option value="cancel_first">A=CANCEL, B=KEEP</option><option value="keep_first">A=KEEP, B=CANCEL</option></select></label>
<div id="cards" class="grid"></div><h2>All predefined cases — complete passes</h2><div id="all"></div>
<p class="note">Probabilities are backend-specific candidate distributions, not guarantees of correctness. Local and hosted latency conditions differ.</p>
<script>const D=__DATA__;
const $=id=>document.getElementById(id);const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const parents=[...new Set(D.cases.map(x=>x.parent_id))].sort();parents.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p+' — '+D.cases.find(x=>x.parent_id===p).family;$('parent').append(o)});$('parent').value='S01';
$('scores').textContent='Primary complete cases: Jev '+D.summary.models.jev.rounds['0'].robust_pass+'/12 · Frozen 4B '+D.summary.models.qwen.rounds['0'].robust_pass+'/12';
function render(){const rep=Number($('round').value),map=$('mapping').value;const cases=D.cases.filter(c=>c.parent_id===$('parent').value);$('cards').innerHTML=cases.map(c=>{
let text='<article class="card"><h2>'+esc(c.variant)+' · Target: '+esc(c.target)+'</h2><p>'+esc(c.customer_message)+'</p><p>Expected: <b>'+esc(c.gold)+'</b></p>';
for(const b of ['jev','qwen']){const r=D.predictions[b].find(x=>x.case_id===c.id&&x.mapping===map&&x.replicate===rep);const good=r.ok&&r.prediction===c.gold;text+='<div class="model"><b>'+ (b==='jev'?'Jev':'Frozen 4B')+'</b><span class="'+(good?'good':'bad')+'">'+esc(r.prediction||'FAILED')+' · '+(good?'correct':'incorrect')+'</span></div>';if(r.probabilities)text+='<p class="note">P(CANCEL) '+r.probabilities.CANCEL.toFixed(4)+' · P(KEEP) '+r.probabilities.KEEP.toFixed(4)+(r.candidate_mass!==undefined?' · candidate mass '+r.candidate_mass.toFixed(4):'')+'</p>';text+='<details><summary>Exact request and saved output</summary><pre>'+esc(JSON.stringify(r,null,2))+'</pre></details>'}return text+'</article>'}).join('');}
['parent','round','mapping'].forEach(id=>$(id).addEventListener('change',render));render();
$('all').innerHTML='<table><tr><th>Case</th><th>Jev round 0</th><th>4B round 0</th><th>Jev round 1</th><th>4B round 1</th></tr>'+parents.map(p=>'<tr><td>'+p+'</td>'+['0','1'].map(rep=>['jev','qwen'].map(b=>'<td>'+ (D.summary.models[b].rounds[rep].parent_pass[p]?'PASS':'FAIL')+'</td>').join('')).join('')+'</tr>').join('')+'</table>';
</script></html>'''
    (ROOT/'docs').mkdir(exist_ok=True)
    (ROOT/'docs/explorer.html').write_text(page.replace('__DATA__',payload),encoding='utf-8')

def documents(cases,predictions,summary):
    j,q=(summary['models'][b]['rounds']['0'] for b in ['jev','qwen'])
    usage=summary['jev_usage']
    model_table='| System | Complete cases | Correct decisions | Wrong cancellations |\n|---|---:|---:|---:|\n'
    for name,label,entry in [('jev','Jev 1.13.0',summary['models']['jev']),('qwen','Frozen Qwen3-4B',summary['models']['qwen'])]+[(n,n,e) for n,e in summary['references'].items()]:
        r=entry['rounds']['0']
        model_table+=f'| {label} | {r["robust_pass"]}/12 | {r["correct"]}/96 | {r["wrong_cancel"]}/48 |\n'
    if j['robust_pass']==q['robust_pass']==12:
        hook='**Both passed all 12 cases. The known-grammar parser passed too.**'
        finding='This probe did not distinguish the two models. A dedicated model was not required to solve these controlled inputs, but this says nothing about replacing Jev in general.'
    elif summary['stable_strict_direction']>0:
        hook=f'**A frozen 4B outscored Jev on this small scope probe: {q["robust_pass"]}/12 vs {j["robust_pass"]}/12 complete cases.**'
        finding='The direction persisted across both candidate mappings and the repeat. This is a narrow behavioral result, not a general replacement or training claim.'
    elif summary['stable_strict_direction']<0:
        hook=f'**Jev led this probe: {j["robust_pass"]}/12 vs {q["robust_pass"]}/12 complete cases.**'
        finding='The direction persisted across both candidate mappings and the repeat. This identifies a gap for this frozen readout on these inputs, not all open models.'
    else:
        hook=f'**Primary complete cases: Jev {j["robust_pass"]}/12; frozen 4B {q["robust_pass"]}/12. No stable strict lead across all checks.**'
        finding='Read the mapping and repeat breakdown before interpreting a winner. This probe does not support a broad model ranking.'
    readme=f'''# Cancel the Right Thing: Jev vs a Frozen 4B

**Same words. Different scope. Opposite decisions.**

Can an off-the-shelf 4B handle the same cancellation decisions as Jev without fine-tuning?
We ran a direct live comparison on 12 predefined four-way cases. Swap the action's
target or the instruction's role, then swap the clause order. Every input, prompt,
prediction and failure is inspectable.

{hook}

{finding}

![All predefined case results](assets/scope-results.png)

## The four-line challenge

Target: **mobile plan**. All four messages have the same word multiset.

| Version | Customer message | Correct decision |
|---|---|---|
| A | Cancel the phone insurance. Keep the mobile plan active. | KEEP |
| B | Cancel the mobile plan. Keep the phone insurance active. | CANCEL |
| C | Keep the mobile plan active. Cancel the phone insurance. | KEEP |
| D | Keep the phone insurance active. Cancel the mobile plan. | CANCEL |

A/B must flip correctly; A/C must hold correctly. A keyword count cannot tell
them apart. There are also quoted-example and superseded-request cases.

## Actual results — primary round

{model_table}

A complete case requires **8/8 correct decisions**: four messages under both
A/B candidate mappings. The 96 decisions are repeated measurements of 48 texts,
not 96 independent samples. Round 1 is a repeat check, never selected over round 0.
Both models produced 192 formal records; see [full results](results/REPORT.md),
[decision CSV](results/decisions.csv), and [raw records](results/).

The known-grammar parser is explicitly tailored to this controlled grammar;
it is not a general natural-language replacement. Its success is part of the result.

## Inspect or reproduce without an API key

Use Python 3.10 (the executed environment was Python 3.10.18):

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python analyze.py --verify
python analyze.py
```

This checks and recomputes the committed real results; it makes no model calls.
Download/open [the standalone result explorer](docs/explorer.html) to inspect
all four variants, mappings, rounds, probabilities and exact requests offline.
It replays saved results; changing a selector does not run a model.

## Run your own live comparison

```bash
python run.py run --backend jev --phase smoke --dry-run
# Set TYPESAFE_API_KEY privately in your shell, then:
python run.py run --backend jev --phase smoke
python run.py run --backend jev --phase formal
```

Existing successful records are cached. For a genuinely new replication, preserve
this published evidence and use a separate copy/output directory after archiving
the included results. Do not edit frozen files or overwrite earlier runs.

For Qwen, install the CUDA-compatible PyTorch 2.8.0 build for your platform
([official instructions](https://pytorch.org/get-started/locally/)) plus
`transformers==4.55.4` and `accelerate==1.10.1`; then:

```bash
python run.py run --backend qwen --phase smoke
python run.py run --backend qwen --phase formal
```

The pinned weights require about 8 GB on disk and were already cached for our
run. They are not included. With no local override, the runner resolves the pinned
HF revision. `--model-path` accepts that pinned snapshot directory for local use.
Actual runtime versions, tokenizer/template hashes and hardware are in `results/`.
Fresh installations and other hardware have not been independently reproduced.

## Cost, scope and provenance

- Live Jev: `jev-1.13.0`; frozen Qwen: `Qwen/Qwen3-4B` at revision
  `1cfa9a7208912126459214e8b04321603b3df60c`, BF16, thinking disabled, native
  next-token A/B readout. No fine-tuning, teacher, calibration or test-time search.
- Jev used {usage['http_attempts']} HTTP attempts including smoke,
  {usage['known_input_tokens']:,} known input tokens, and
  **USD {usage['usage_estimated_usd']:.6f} usage-estimated API cost**.
  This is not an account invoice. Local GPU time/memory are reported separately.
- Short, original, synthetic English messages; **no independent human label audit**.
  Labels were constructed from rules and AI reviewed. Approval to execute does
  not mean a human audited every label.
- Purposive templates and explicit markers make this a small diagnostic probe.
  It does not establish production safety, equivalence, general model superiority,
  or whether dedicated training is necessary. Hosted/local latency is not a
  controlled architecture comparison.
- [Protocol](PROTOCOL.md) and [freeze manifest](manifest.json) were saved before
  live calls. The data were not made harder after inspecting predictions.

## Extend the challenge

Recompute the published results first. A useful contribution is a new clear
four-way case, a label objection with its reasoning, or results from another
backend with exact prompts and costs. New cases belong in a separately versioned
extension; this v0.1 test stays fixed. Report wins, losses and mapping sensitivity.

The series asks *You Might Not Need Jev*; this release does not announce that
Jev is useless. Independent project, not affiliated with or endorsed by TypeSafe.
Paired behavior tests and native logits are established ideas; see
[CheckList](https://aclanthology.org/2020.acl-main.442/) and
[SemIf](https://github.com/TheoLeeCJ/SemIf-OpenJev).

Created by Yuchi Wang with AI-assisted experiment design, implementation and
analysis. Code: [MIT](LICENSE). Original data: [CC BY 4.0](data/README.md).
Upstream models and components retain their own licenses.
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    lines=['# Full result report','',hook,'',finding,'',model_table,
           '## Round and candidate-mapping breakdown','',
           '| Model | Round | Complete cases | A=CANCEL mapping | A=KEEP mapping | Correct /96 | Mapping disagreements /48 | Wrong semantics under both mappings /48 |',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for b in ['jev','qwen']:
        for rep in ['0','1']:
            r=summary['models'][b]['rounds'][rep]
            lines.append(f'| {b} | {rep} | {r["robust_pass"]}/12 | {r["mapping_pass"]["cancel_first"]}/12 | {r["mapping_pass"]["keep_first"]}/12 | {r["correct"]} | {r["mapping_disagreements"]} | {r["semantic_errors_both_mappings"]} |')
    lines+=['','## Complete case table','',
            '| Case | Family | Jev round 0 | Qwen round 0 | Jev round 1 | Qwen round 1 |',
            '|---|---|---|---|---|---|']
    for p in sorted({c['parent_id'] for c in cases}):
        family=next(c['family'] for c in cases if c['parent_id']==p)
        cells=['PASS' if summary['models'][b]['rounds'][rep]['parent_pass'][p] else 'FAIL'
               for rep in ['0','1'] for b in ['jev','qwen']]
        lines.append('| '+ ' | '.join([p,family]+cells)+' |')
    lines+=['','## Probability quality, repeat stability and cost','',
            'Binary Brier uses P(CANCEL); NLL uses the assigned gold probability. These are descriptive on this tiny selected probe.',
            '', '| Model | Round-0 Brier | Round-0 NLL | Repeat disagreement /96 | Formal median latency (s) | Formal p95 (s) |',
            '|---|---:|---:|---:|---:|---:|']
    for b in ['jev','qwen']:
        r=summary['models'][b]['rounds']['0']; e=summary['models'][b]
        lines.append(f'| {b} | {r["brier"]:.6f} | {r["nll"]:.6f} | {e["repeat_disagreements"]} | {e["latency_s"]["median"]:.4f} | {e["latency_s"]["p95"]:.4f} |')
    lines+=['','Jev latency includes network and hosted service; Qwen is local single-input execution after smoke. No latency-normalized architectural winner is inferred.',
            '', 'Jev usage including smoke: `'+json.dumps(usage,sort_keys=True)+'`.',
            '', 'Qwen candidate mass: `'+json.dumps(summary['models']['qwen']['candidate_mass'],sort_keys=True)+'`.',
            '', 'Within-probe reweighting sensitivity: `'+json.dumps(summary['within_probe_reweighting'],sort_keys=True)+'`. This is not a population confidence interval or equivalence proof.',
            '', '## All errors — no selected failure montage','']
    golds={c['id']:c['gold'] for c in cases}
    errors=[]
    for b,rows in predictions.items():
        for r in rows:
            if not r['ok'] or r.get('prediction')!=golds[r['case_id']]:
                errors.append((b,r))
    if not errors: lines.append('No incorrect or failed formal decisions in either round.')
    else:
        lines+=['| Model | Case | Round | Mapping | Gold | Prediction | P(gold) |','|---|---|---:|---|---|---|---:|']
        for b,r in errors:
            prob=r.get('probabilities',{}).get(golds[r['case_id']])
            lines.append(f'| {b} | {r["case_id"]} | {r["replicate"]} | {r["mapping"]} | {golds[r["case_id"]]} | {r.get("prediction","FAILED")} | {prob if prob is not None else "unknown"} |')
    lines+=['','## Limits','',
            '48 artificial inputs, 12 related templates, no independent human audit. Code with the declared grammar can solve them. Model readout, training histories and hosting differ. The results are a narrow probe, not a causal test of training, general ranking, production replacement or proof of equivalence. All extensions must be separately versioned.','']
    (ROOT/'results/REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    zh=f'''# 这一期你可以怎样解释

我们固定了 12 个四格案例，共 48 条英文消息。每组使用相同的词，但交换取消/保留的对象或实际/引用、当前/旧请求的归属。
Jev 与冻结 Qwen3-4B 接受相同语义任务，各跑两种 A/B 答案映射、两轮。第一轮为主，第二轮检查稳定性。

实测第一轮完整通过：**Jev {j['robust_pass']}/12；4B {q['robust_pass']}/12**。逐次正确：Jev {j['correct']}/96；4B {q['correct']}/96。
已知语法解析器也公布，不把简单规则可以解决的合成输入包装成现实世界测试。

最值得解释的四点：为什么同词不等于同义；为什么该变时要变、只换展示顺序时要稳；为什么更换 A/B 映射也要测；为什么 48 条人为设计样本不足以宣布模型整体胜负。
没有独立人工标签审核。所有真实输出可在 explorer.html 查看，页面回放已保存结果，不运行模型。
Jev 用量估算为 ${usage['usage_estimated_usd']:.6f}，不是账户账单。结果与局限见 ../results/REPORT.md。
'''
    (ROOT/'docs/README.zh-CN.md').write_text(zh,encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    cases,predictions,all_predictions,summary=recompute()
    if args.verify:
        saved=json.loads((ROOT/'results/summary.json').read_text(encoding='utf-8'))
        assert saved==summary, 'Saved summary does not reproduce'
        print('Verified frozen inputs/config, 192 unique records per model, exact requests, and full summary recomputation.')
        return
    (ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    write_tables(cases,predictions,summary);figure(cases,predictions,summary);explorer(cases,predictions,summary);documents(cases,predictions,summary)
    print(json.dumps({b:{rep:entry['rounds'][rep]['robust_pass'] for rep in ['0','1']}
                      for b,entry in summary['models'].items()},indent=2))
    print('Generated full report, figures, CSVs, README and standalone explorer from real records.')

if __name__=='__main__': main()
