"""Post-run tables, tradeoff figure and replay from every frozen grid point."""
import argparse
import json
from guard_study import HERE, GAP, read_rows, ARMS
from guards import methods, MAX_THRESHOLDS, MARGIN_THRESHOLDS


def artifacts():
    summary=json.loads((HERE/'results/summary.json').read_text(encoding='utf-8'))
    text=['# All fixed guard and score-grid results','',
          'Post-hoc development only; no threshold fitting or selection, no new model forwards, no held-out results.','',
          '|Path|Method|Correct /216|Pair /36|Unsupported /72|False INSUFFICIENT /144|Wrong supported actions /144|Complete /12|Actions /216|Action errors|Action risk|Corrected|Regressed|',
          '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm,panels in summary['results'].items():
        for method,panel in panels.items():
            m=panel['all'];risk=f"{m['action_risk']:.6f}" if m['action_risk'] is not None else 'undefined'
            values=[arm,method]+[m[k] for k in ('correct','deletion_pair_correct','false_commitments','false_insufficient',
                'supported_wrong_actions','complete_parents','actions','action_errors')]+[risk]+[
                m[k] for k in ('corrected_vs_raw','regressed_vs_raw')]
            text.append('|'+ '|'.join(map(str,values))+'|')
    text+=['','Known-grammar full solver: 216/216, 36/36 deletion pairs, 12/12 complete parents; zero model calls.',
           'All method rows repeat the same 12 parent groups under three option orders. These are not independent trials.',
           '', '## Every family and view','',
           '|Path|Method|Family|Correct /72|Full /12|Reorder /12|Flip /12|Decisive missing /12|Nondecisive missing /12|Conflict /12|False INSUFFICIENT /48|Wrong supported actions /48|',
           '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm,panels in summary['results'].items():
        for method,panel in panels.items():
            for family,m in panel['families'].items():
                values=[arm,method,family,m['correct']]+[m['variants'][v]['correct'] for v in (
                    'full','hold','flip','decisive_missing','nondecisive_missing','conflict')]+[
                    m['false_insufficient'],m['supported_wrong_actions']]
                text.append('|'+ '|'.join(map(str,values))+'|')
    plot={arm:{method:{k:p['all'][k] for k in ('false_commitments','false_insufficient','action_risk','action_coverage',
                                            'deletion_pair_correct','correct')} for method,p in panels.items()}
          for arm,panels in summary['results'].items()}
    cases=[{k:c[k] for k in ('id','parent','family','variant','state','instruction','gold')}
           for c in read_rows(HERE/'development_cases.jsonl')]
    payload={'summary':summary,'cases':cases,'predictions':read_rows(HERE/'results/predictions.jsonl'),
             'gates':read_rows(HERE/'results/gates.jsonl'),'methods':methods()}
    page=(HERE/'explorer_template.html').read_text(encoding='utf-8').replace(
        '__GUARD_DATA__',json.dumps(payload,ensure_ascii=False).replace('<','\\u003c'))
    return {'results/ALL_COUNTS.md':'\n'.join(text)+'\n','assets/figure_data.json':json.dumps(plot,indent=2)+'\n',
            'docs/explorer.html':page}


def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    data=json.loads((HERE/'assets/figure_data.json').read_text(encoding='utf-8'))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained')
    names=['Base / native','Kev LoRA / native','Kev pointer']
    for axis,arm,name in zip(axes,ARMS,names):
        p=data[arm]
        for prefix,thresholds,color,marker,label in [('maxprob',MAX_THRESHOLDS,'#38688d','o','Max-probability grid (5)'),
                                                    ('margin',MARGIN_THRESHOLDS,'#8d639b','v','Margin grid (4)')]:
            panels=[p[f'{prefix}_{t:g}'] for t in thresholds]
            axis.plot([m['false_insufficient'] for m in panels],[m['false_commitments'] for m in panels],
                      color=color,marker=marker,label=label,linewidth=1.3,markersize=6)
        for method,label,color,marker,offset in [
            ('raw','Raw','#b24735','X',(4,5)),('schema_presence','Schema gate','#cf913e','s',(5,9)),
            ('policy_determinacy','Policy gate','#268477','D',(5,28)),
            ('always_insufficient','Always I','#666666','P',(-48,12))]:
            m=p[method];x,y=m['false_insufficient'],m['false_commitments']
            axis.scatter([x],[y],c=color,marker=marker,s=70,zorder=4,label=label)
            axis.annotate(label+f' ({x},{y})',(x,y),xytext=offset,textcoords='offset points',fontsize=8,color=color)
        axis.set(xlim=(-5,150),ylim=(-5,82),xticks=[0,36,72,108,144],yticks=[0,18,36,54,72],
                 xlabel='False INSUFFICIENT /144 determined decisions',title=name)
        axis.grid(alpha=.15)
    axes[0].set_ylabel('Unsupported commitments /72 uncertain decisions')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,-.10),ncol=6,frameon=False,fontsize=9)
    fig.suptitle('Missing fields are not always missing deciding evidence',fontsize=19,fontweight='bold')
    fig.text(.5,-.145,'Post-hoc development · 12 parents / repeated orders · fixed grids, no calibration · hand-coded grammar/logic · reserved splits unscored',ha='center',fontsize=10)
    fig.savefig(HERE/'assets/guard-tradeoffs.png',dpi=180,bbox_inches='tight')
    fig.savefig(HERE/'assets/guard-tradeoffs.svg',bbox_inches='tight')
    path=HERE/'assets/guard-tradeoffs.svg'
    path.write_text('\n'.join(x.rstrip() for x in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    for name,payload in artifacts().items():
        path=HERE/name
        if args.verify:
            if path.read_text(encoding='utf-8')!=payload:raise ValueError('Published artifact differs: '+name)
        else:path.parent.mkdir(exist_ok=True);path.write_text(payload,encoding='utf-8',newline='\n')
    if not args.verify:figures()
    print(json.dumps({'status':'passed','read_only':args.verify,'all_model_paths':3,'methods_per_path':13,'reserved_scores':0}))
