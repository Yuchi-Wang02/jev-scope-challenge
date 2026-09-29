"""Create scientific count figure and saved-record replay from verified evidence."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from layout_analyze import analyze,check_equal
from layout_study import HERE,PRIOR,ARMS,LAYOUTS,read_rows


def main():
    s,rows=analyze()
    check_equal(s,json.loads((HERE/'results/summary.json').read_text(encoding='utf-8')))
    fig,axes=plt.subplots(1,3,figsize=(13,5.7))
    fig.patch.set_facecolor('#faf8f3')
    metrics=[('Correct decisions','correct','decisions'),('Correct missing-evidence decisions',None,'missing_decisions'),('Complete parents','complete_parents','parents')]
    for ax,(title,key,denom) in zip(axes,metrics):
        counts=np.zeros((3,3));totals=np.zeros((3,3))
        for i,a in enumerate(ARMS):
            for j,l in enumerate(LAYOUTS):
                v=s['results'][a][l]['exploratory_test']['raw']
                counts[i,j]=v[key] if key else v['variant_correct']['missing']
                totals[i,j]=v[denom]
        values=100*counts/totals
        ax.imshow(values,cmap='YlGnBu',vmin=0,vmax=100,aspect='auto')
        for i in range(3):
            for j in range(3):
                ax.text(j,i,f'{int(counts[i,j])}/{int(totals[i,j])}\n{values[i,j]:.1f}%',
                    ha='center',va='center',color='white' if values[i,j]>65 else '#193037',fontsize=12)
        ax.set_xticks(range(3),['L0\nOriginal','L1\nPolicy+evidence\nin state','L2\nEvidence\nin question'],fontsize=9)
        ax.set_yticks(range(3),['Base\nnative','LoRA\nnative','LoRA\npointer'],fontsize=10)
        ax.set_title(title,fontsize=11,pad=14)
        ax.tick_params(length=0)
        for spine in ax.spines.values():spine.set_visible(False)
    fig.suptitle('Same Native Tokens. Different Pointer Boundaries.',fontsize=19,y=.97)
    fig.text(.5,.87,'L1/L2 are identical native inputs; pointer field allocation and delimiter positions change.',ha='center',fontsize=10)
    fig.text(.5,.025,'12 previously inspected test parents · all layouts reported · rule labels, no independent human audit\n2592 logical records ≠ independent trials: 2016 scientific forwards + 576 shared native records; 864 parity forwards.',ha='center',fontsize=9,color='#555')
    fig.tight_layout(rect=[0,.14,1,.82])
    assets=HERE/'assets';assets.mkdir(exist_ok=True)
    fig.savefig(assets/'boundary-results.png',dpi=180,facecolor=fig.get_facecolor())
    fig.savefig(assets/'boundary-results.svg',facecolor=fig.get_facecolor())
    plt.close(fig)
    fig,axes=plt.subplots(1,4,figsize=(14.5,4.8))
    fig.patch.set_facecolor('#faf8f3')
    for ax,split,title in zip(axes,('development','calibration','exploratory_test','all'),
                            ('Development (6 parents)','Calibration (6 parents)','Old test panel (12 parents)','All pilot (24 parents)')):
        for i,a in enumerate(ARMS):
            for j,l in enumerate(LAYOUTS):
                panels=s['results'][a][l]
                vs=[x['raw'] for x in panels.values()] if split=='all' else [panels[split]['raw']]
                hit=sum(x['correct'] for x in vs);total=sum(x['decisions'] for x in vs)
                if i==0 and j==0: vals=np.zeros((3,3));texts={}
                vals[i,j]=100*hit/total;texts[i,j]=f'{hit}/{total}\n{100*hit/total:.1f}%'
        ax.imshow(vals,cmap='YlGnBu',vmin=0,vmax=100,aspect='auto')
        for (i,j),text in texts.items():
            ax.text(j,i,text,ha='center',va='center',color='white' if vals[i,j]>65 else '#193037',fontsize=10)
        ax.set_xticks(range(3),LAYOUTS,fontsize=10)
        ax.set_yticks(range(3),['Base\nnative','LoRA\nnative','LoRA\npointer'],fontsize=9)
        ax.set_title(title,fontsize=10,pad=12);ax.tick_params(length=0)
        for spine in ax.spines.values():spine.set_visible(False)
    fig.suptitle('The Ranking Reversal Does Not Hold Across Every Split.',fontsize=18,y=.96)
    fig.text(.5,.04,'Correct-decision counts · same 0–100% scale · all data previously inspected\nL2 pointer trails native on development/calibration; the complete-pilot totals differ by one decision.',ha='center',fontsize=10,color='#555')
    fig.tight_layout(rect=[0,.16,1,.87])
    fig.savefig(assets/'split-results.png',dpi=180,facecolor=fig.get_facecolor())
    fig.savefig(assets/'split-results.svg',facecolor=fig.get_facecolor())
    plt.close(fig)
    payload=json.dumps({'cases':read_rows(PRIOR/'data/cases.jsonl'),
        'plans':read_rows(HERE/'data/inputs.jsonl'),'rows':rows,'summary':s},ensure_ascii=False).replace('</','<\\/')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Same Native Tokens, Different Pointer Boundaries</title>
<style>body{font:16px/1.5 system-ui;background:#faf8f3;color:#23332c;max-width:1100px;margin:auto;padding:24px}h1{font-size:32px;line-height:1.15}select{font:inherit;max-width:100%;padding:8px;margin:5px 0}article{background:white;border:1px solid #bbcabc;border-radius:12px;padding:18px;margin:18px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}.state,.question{padding:12px;background:#edf3ec}.question{background:#f7eee4}.wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;padding:9px;border-bottom:1px solid #ddd}.good{color:#137358}.bad{color:#a1382b}summary{cursor:pointer}label{display:inline-block;margin-right:12px}</style>
<h1>Same Native Tokens.<br>Different Pointer Boundaries.</h1><p>Saved real outputs on inspected synthetic data. L1/L2 have identical native prompts/tokens; the pointer state/question boundary moves.</p><p>2016 scientific forwards + 576 shared native records. 864 extra causal-path parity checks. No independent human labels, new training or model calls from this page.</p><label>Score panel <select id="panel"><option value="all">All pilot (24 parents)</option><option value="development">Development (6 parents)</option><option value="calibration">Calibration (6 parents)</option><option value="exploratory_test">Old test panel (12 parents)</option></select></label><div class="wrap"><table id="scores"></table></div>
<label>Parent<br><select id="parent"></select></label><label>Evidence view<br><select id="variant"><option>full</option><option>hold</option><option>flip</option><option>missing</option></select></label><label>Candidate order<br><select id="mapping"><option value="0">ALLOW / DENY / INSUFFICIENT</option><option value="1">DENY / INSUFFICIENT / ALLOW</option><option value="2">INSUFFICIENT / ALLOW / DENY</option></select></label><div id="cards"></div>
<p>All layouts are shown, including corrections and regressions. The test panel contains 12 old parent groups; this is exploratory diagnosis, not new confirmation. Boundary changes include delimiter positions and whitespace tokens, not an isolated head intervention.</p>
<script>const D=__PAYLOAD__;const E=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const p=document.getElementById('parent'),v=document.getElementById('variant'),m=document.getElementById('mapping'),panel=document.getElementById('panel');
p.innerHTML=[...new Set(D.cases.map(c=>c.parent))].map(x=>`<option>${E(x)}</option>`).join('');
function score(){document.getElementById('scores').innerHTML='<tr><th>Path</th><th>Layout</th><th>Correct decisions</th><th>Complete parents</th><th>Missing correct</th></tr>'+Object.entries(D.summary.results).flatMap(([a,ls])=>Object.entries(ls).map(([l,x])=>{const ss=(panel.value==='all'?Object.values(x):[x[panel.value]]).map(y=>y.raw);const sum=k=>ss.reduce((n,y)=>n+y[k],0);const missing=ss.reduce((n,y)=>n+y.variant_correct.missing,0);return `<tr><td>${a}</td><td>${l}</td><td>${sum('correct')}/${sum('decisions')}</td><td>${sum('complete_parents')}/${sum('parents')}</td><td>${missing}/${sum('missing_decisions')}</td></tr>`})).join('');}panel.onchange=score;score();
function render(){const c=D.cases.find(c=>c.parent===p.value&&c.variant===v.value);document.getElementById('cards').innerHTML=['L0','L1','L2'].map(l=>{const plan=D.plans.find(x=>x.id===c.id&&x.mapping===Number(m.value)&&x.layout===l);const rs=D.rows.filter(r=>r.id===c.id&&r.mapping===Number(m.value)&&r.layout===l);return `<article><h2>${l} · rule label ${E(c.gold)}</h2><p>State field</p><pre class="state">${E(plan.state)}</pre><p>Question instruction</p><pre class="question">${E(plan.instruction)}</pre><div class="wrap"><table><tr><th>Path</th><th>Decision</th><th>ALLOW / DENY / INSUFFICIENT</th><th>Execution</th></tr>${rs.map(r=>{const ps=Object.fromEntries(r.order.map((k,i)=>[k,r.probabilities[i]]));return `<tr><td>${r.arm}</td><td class="${r.prediction===c.gold?'good':'bad'}">${E(r.prediction)}</td><td>${['ALLOW','DENY','INSUFFICIENT'].map(k=>ps[k].toFixed(4)).join(' / ')}</td><td>${r.executed_forward?'forward':'shared L1 forward'}</td></tr>`}).join('')}</table></div><details><summary>Exact native prompt, encoded plan and saved records</summary><pre>${E(JSON.stringify({plan,records:rs},null,2))}</pre></details></article>`}).join('');}
for(const e of [p,v,m])e.onchange=render;render();</script></html>'''
    (HERE/'explorer.html').write_text(html.replace('__PAYLOAD__',payload),encoding='utf-8',newline='\n')
    print('Verified figure and saved-record explorer written.')


if __name__=='__main__':main()
