"""Post-run publication artifacts, with all methods and explicit extraction provenance."""
import argparse
import json
from fact_run import HERE, ARMS, read_rows


def artifacts():
    summary=json.loads((HERE/'results/summary.json').read_text(encoding='utf-8'))
    missing=summary['methods']['N0']['facts_0']['extraction']['missing_fields']
    conflicts=summary['methods']['N0']['facts_0']['extraction']['conflict_fields']
    lines=['# Every fixed fact/execution and direct control result','',
        'Exploratory original development only: 72 texts in 12 parent groups, not 72 independent trials.',
        'Scaffolded direct and extraction receive the same explicit field definitions and policy.',
        'Legacy rows use previous scores without those definitions. No independent labels or rewrite/test results.','',
        '|Path|Method|Correct /72|Complete /12|Deletion pair /12|Unsupported /24|False I /48|Wrong supported /48|Actions|Action errors|Calls /72|Input tokens|Corrected vs direct0|Regressed vs direct0|',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm,panels in summary['methods'].items():
        for method,panel in panels.items():
            m=panel['all'];vs=panel['vs_scaffolded_direct_0']
            values=[arm,method]+[m[k] for k in ('correct','complete_parents','deletion_pair_correct','false_commitments','false_insufficient','wrong_supported_actions','actions','action_errors','model_calls','input_tokens')]+[vs['corrected'],vs['regressed']]
            lines.append('|'+ '|'.join(map(str,values))+'|')
    lines+=['','Known-grammar full solver: 72/72 decisions, zero model calls; exact synthetic grammar only.',
        'Calls and tokens describe each hypothetical deployment method. Shared-grid reuse does not make a deployment call free.',
        'Actual new execution: 1656 scientific forwards, 552 additional pointer parity forwards, six warmups. Legacy rows created no new forwards.',
        'Latency sums are recorded serial forward times, excluding parity/load; they are not a fresh end-to-end deployment benchmark.','',
        '## Extraction: correct actions need not mean correct facts','',
        f'|Path|Method|Correct fields /168|Exact vectors /72|Missing -> value /{missing}|Missing -> conflict /{missing}|Missed conflicts /{conflicts}|Wrong facts masked|Wrong facts, wrong action|Executor defects|',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm,panels in summary['methods'].items():
        for method,panel in panels.items():
            if 'extraction' not in panel:continue
            e=panel['extraction'];a=e['attribution']
            values=[arm,method,e['correct_fields'],e['exact_vectors'],e['missing_as_reported_value'],e['missing_as_conflict'],e['missed_conflicts'],a.get('wrong_facts_masked',0),a.get('wrong_facts_wrong_action',0),a.get('executor_defect',0)]
            lines.append('|'+ '|'.join(map(str,values))+'|')
    lines+=['','The extractor chooses four statuses; it does not produce quotes. Every predicted evidence_spans is null.',
        'Construction reference quotes are stored separately and must not be described as model-generated citations.','',
        '## Family and view counts','',
        '|Path|Method|Family|Correct /24|Full /4|Reorder /4|Flip /4|Decisive missing /4|Nondecisive missing /4|Conflict /4|Calls /24|',
        '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm,panels in summary['methods'].items():
        for method,panel in panels.items():
            for family,m in panel['families'].items():
                values=[arm,method,family,m['correct']]+[m['variants'][v]['correct'] for v in ('full','hold','flip','decisive_missing','nondecisive_missing','conflict')]+[m['model_calls']]
                lines.append('|'+ '|'.join(map(str,values))+'|')
    lines+=['','Full four-state confusion matrices and field/family/view extraction counts are in summary.json.',
        'All per-input regressions, fact vectors and attributions are in decisions.jsonl. All status probabilities are in fact_claims.jsonl.']
    cases=read_rows(HERE/'data/original_cases.jsonl')
    payload={'summary':summary,'cases':cases,'decisions':read_rows(HERE/'results/decisions.jsonl'),'claims':read_rows(HERE/'results/fact_claims.jsonl'),
        'references':read_rows(HERE/'data/reference_facts.jsonl')}
    page=(HERE/'explorer_template.html').read_text(encoding='utf-8').replace('__FACT_DATA__',json.dumps(payload,ensure_ascii=False).replace('<','\\u003c'))
    plot={arm:{method:{'correct':p['all']['correct'],'calls':p['all']['model_calls'],
        'fields':p.get('extraction',{}).get('correct_fields'),'vectors':p.get('extraction',{}).get('exact_vectors')}
        for method,p in panels.items()} for arm,panels in summary['methods'].items()}
    return {'results/ALL_COUNTS.md':'\n'.join(lines)+'\n','assets/figure_data.json':json.dumps(plot,indent=2)+'\n','docs/explorer.html':page}


def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    data=json.loads((HERE/'assets/figure_data.json').read_text(encoding='utf-8'))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(14,5.7),layout='constrained');x=np.arange(3)
    methods=[('direct_0','Direct: 1 call','#a9b7c6'),('direct_two_01','Direct: 2 calls','#668cac'),('direct_three','Direct: 3 calls','#365e80'),('facts_0','Facts + code: 2/3 calls','#ad683e'),('facts_two','Facts ensemble + code: 4/6 calls','#d4a47b')]
    for i,(method,label,color) in enumerate(methods):
        vals=[data[a][method]['correct'] for a in ARMS];pos=x+(i-2)*.155
        axes[0].bar(pos,vals,width=.15,color=color,label=label)
        for p,v in zip(pos,vals):axes[0].text(p,v+1,str(v),ha='center',fontsize=9)
    axes[0].set(ylim=(0,81),ylabel='Correct final decisions /72',xticks=x,xticklabels=['Base native','Kev LoRA native','Kev pointer'],title='Decision accuracy and call budget')
    for i,(key,label,color,denom) in enumerate([('fields','Correct fields /168','#477e90',168),('vectors','Exact fact vectors /72','#ad683e',72),('correct','Correct final decisions /72','#56795d',72)]):
        vals=[data[a]['facts_0'][key]/denom*100 for a in ARMS];pos=x+(i-1)*.24
        axes[1].bar(pos,vals,width=.23,color=color,label=label)
        for p,a,v in zip(pos,ARMS,vals):axes[1].text(p,v+1,f"{data[a]['facts_0'][key]}/{denom}",ha='center',fontsize=9)
    axes[1].set(ylim=(0,110),ylabel='Percent correct',xticks=x,xticklabels=['Base native','Kev LoRA native','Kev pointer'],title='Primary facts pipeline: error attribution')
    for ax in axes:ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.10),frameon=False,fontsize=9)
    fig.suptitle('Correct Code, Wrong Facts',fontsize=20,fontweight='bold')
    fig.text(.5,-.18,'Original development · 12 grouped parents · known policy/schema · no human labels · rewrites and reserved splits unscored',ha='center',fontsize=10)
    for ext in ('png','svg'):fig.savefig(HERE/f'assets/fact-execution.{ext}',dpi=170,bbox_inches='tight',metadata={'Creator':'Matplotlib'} if ext=='svg' else None)
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');parser.add_argument('--figure',action='store_true');a=parser.parse_args()
    if a.verify and a.figure:parser.error('Read-only verification does not render or overwrite figures')
    for name,payload in artifacts().items():
        path=HERE/name
        if a.verify:
            if path.read_text(encoding='utf-8')!=payload:raise ValueError('Publication drift: '+name)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(payload,encoding='utf-8',newline='\n')
    if a.figure:figures()
    print(json.dumps({'status':'passed','read_only':a.verify,'all_methods':True}))
