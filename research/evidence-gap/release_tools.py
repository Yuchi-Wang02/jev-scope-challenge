"""Post-run figures, exhaustive count tables and offline result replay."""
import argparse
import json
from gap_run import HERE, ARMS, read_rows
from gap_methods import METHODS
from gap_analyze import equal


def outputs():
    summary=json.loads((HERE/'results/summary.json').read_text(encoding='utf-8'))
    cases=[c for c in read_rows(HERE/'data/cases.jsonl') if c['split']=='development']
    rows=read_rows(HERE/'results/predictions.jsonl')
    raw=[r for arm in ARMS for r in read_rows(HERE/f'results/{arm}.jsonl')]
    # Embed development only. Token sequences remain in the auditable raw files.
    fields=('id','parent','family','variant','kind','mapping','order','arm','forward_id','logits','probabilities','prediction')
    replay={'summary':summary,'cases':[{k:c[k] for k in ('id','parent','family','variant','state','instruction','gold')} for c in cases],
            'predictions':rows,'raw':[{k:r[k] for k in fields} for r in raw]}
    text=['# Every development family, view and readout','',
          'Counts are descriptive: 12 parents, repeated under three candidate orders. No held-out scores or significance claims.','',
          '|Path|Readout|Family|All / 72|Full / 12|Reorder / 12|Flip / 12|Decisive missing / 12|Nondecisive missing / 12|Conflict / 12|',
          '|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for arm in ARMS:
        for method in METHODS:
            panel=summary['results'][arm]['methods'][method]
            for family,m in panel['families'].items():
                vals=[m['variants'][v]['correct'] for v in ('full','hold','flip','decisive_missing','nondecisive_missing','conflict')]
                text.append('|'+ '|'.join(map(str,[arm,method,family,m['correct'],*vals]))+'|')
    text+=['','## Corrections and regressions relative to raw','',
           '|Path|Readout|Corrected|Regressed|Unsupported commitments / 72|Order-sensitive inputs / 72|',
           '|---|---|---:|---:|---:|---:|']
    for arm in ARMS:
        for method in METHODS:
            p=summary['results'][arm]['methods'][method];change=p.get('vs_raw',{'corrected':0,'regressed':0})
            text.append(f"|{arm}|{method}|{change['corrected']}|{change['regressed']}|{p['all']['false_commitments']}|{p['all']['order_sensitive_inputs']}|")
    template=(HERE/'explorer_template.html').read_text(encoding='utf-8')
    page=template.replace('__REPLAY_DATA__',json.dumps(replay,ensure_ascii=False).replace('<','\\u003c'))
    plot={'raw_deletion':{a:{v:summary['results'][a]['methods']['raw']['all']['variants'][v]['correct'] for v in ('decisive_missing','nondecisive_missing')} for a in ARMS},
          'false_commitments':{a:{m:summary['results'][a]['methods'][m]['all']['false_commitments'] for m in METHODS} for a in ARMS},
          'deletion_denominator':36,'uncertain_denominator':72,'parents':12,'independent_human_reviewed':False}
    return {'results/ALL_COUNTS.md':'\n'.join(text)+'\n','docs/explorer.html':page,
            'assets/figure_data.json':json.dumps(plot,indent=2)+'\n'}


def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    data=json.loads((HERE/'assets/figure_data.json').read_text(encoding='utf-8'))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(13,5),layout='constrained')
    x=np.arange(3);names=['Base / native','Kev LoRA / native','Kev pointer']
    colors=['#315f87','#cb6632','#438675']
    for j,(v,label,color) in enumerate([('decisive_missing','Decisive evidence deleted → INSUFFICIENT',colors[1]),
                                      ('nondecisive_missing','Nondecisive evidence deleted → preserve',colors[2])]):
        vals=[data['raw_deletion'][a][v] for a in ARMS]
        bars=axes[0].bar(x+(j-.5)*.36,vals,.36,label=label,color=color)
        axes[0].bar_label(bars,labels=[f'{v}/36' for v in vals],padding=3,fontsize=10)
    axes[0].set(xticks=x,xticklabels=names,ylim=(0,42),ylabel='Correct decisions',title='Raw readout: two deletions, opposite obligations')
    axes[0].legend(loc='upper left',fontsize=8.5,frameon=False)
    for i,a in enumerate(ARMS):
        vals=[data['false_commitments'][a][m] for m in METHODS]
        bars=axes[1].bar(x+(i-1)*.24,vals,.24,color=colors[i],label=names[i])
        axes[1].bar_label(bars,padding=3,fontsize=10)
    axes[1].set(xticks=range(3),xticklabels=['Raw','Null subtraction','Two-order average'],ylim=(0,85),ylabel='Unsupported commitments / 72 (lower is better)',title='Extra readout computation can worsen abstention')
    axes[1].legend(loc='lower center',bbox_to_anchor=(.5,1.02),ncol=3,frameon=False,fontsize=9)
    axes[1].set_title('Extra readout computation can worsen abstention',pad=38)
    fig.suptitle('Missing Evidence Is Not Just Deleted Text',fontsize=19,fontweight='bold')
    fig.text(.5,-.025,'Exploratory development only · 12 parents × repeated orders · rule labels await human review · reserved splits unscored',ha='center',fontsize=10)
    fig.savefig(HERE/'assets/evidence-gap.png',dpi=180,bbox_inches='tight')
    fig.savefig(HERE/'assets/evidence-gap.svg',bbox_inches='tight')
    svg=HERE/'assets/evidence-gap.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    for name,payload in outputs().items():
        path=HERE/name
        if args.verify:
            if path.read_text(encoding='utf-8')!=payload:raise ValueError('Derived release artifact changed: '+name)
        else:path.parent.mkdir(exist_ok=True);path.write_text(payload,encoding='utf-8',newline='\n')
    if not args.verify:figures()
    print(json.dumps({'status':'passed','read_only':args.verify,'replay_inputs':72,'reserved_scores':0}))
