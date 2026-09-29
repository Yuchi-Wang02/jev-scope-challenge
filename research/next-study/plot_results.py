"""Render counts from the verified real pilot, with denominators and limits."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze_study import analyze
from study import HERE

s=analyze(write=False)
arms=['N0','N1','K1']
labels=['Base + native','LoRA + native','LoRA + pointer']
colors=['#7b8c92','#187b68','#d37745']
stats=[s['results'][a]['splits']['exploratory_test']['raw'] for a in arms]
fig,axes=plt.subplots(1,3,figsize=(12,5.5))
fig.patch.set_facecolor('#faf8f3')
metrics=[('Correct decisions','correct','decisions'),('Correct on missing evidence',None,'missing_decisions'),('Complete parents','complete_parents','parents')]
for ax,(title,key,denom) in zip(axes,metrics):
    counts=[r[key] if key else r[denom]-r['missing_false_acceptance'] for r in stats]
    totals=[r[denom] for r in stats]
    values=[100*a/b for a,b in zip(counts,totals)]
    ax.set_facecolor('#faf8f3')
    bars=ax.bar(range(3),values,color=colors,width=.65)
    for bar,hit,total,value in zip(bars,counts,totals,values):
        ax.text(bar.get_x()+bar.get_width()/2,max(value,0)+3,f'{hit}/{total}\n{value:.1f}%',ha='center',fontsize=11)
    ax.set_ylim(0,112);ax.set_yticks([0,25,50,75,100],['0%','25%','50%','75%','100%'])
    ax.set_xticks(range(3),['Base\nnative','LoRA\nnative','LoRA\npointer'])
    ax.set_title(title,pad=15,fontsize=12)
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
fig.suptitle('One Base. Three Decision Paths.',fontsize=21,y=.98)
fig.text(.5,.88,'The same trained backbone feeds N1 and K1; representation and readout differ.',ha='center',fontsize=11)
fig.text(.5,.02,'12 exploratory-test parents · 4 evidence views · 3 candidate orders\nSynthetic rule labels; no independent human audit. Repeated decisions are not independent samples.',ha='center',fontsize=10,color='#555')
fig.tight_layout(rect=[0,.12,1,.84])
out=HERE/'assets';out.mkdir(exist_ok=True)
fig.savefig(out/'matched-base-results.png',dpi=180,facecolor=fig.get_facecolor())
fig.savefig(out/'matched-base-results.svg',facecolor=fig.get_facecolor())
plt.close(fig)
