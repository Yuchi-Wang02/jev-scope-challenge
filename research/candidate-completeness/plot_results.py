"""Static scientific figure from verified recorded endpoints; no inference."""
import argparse
import hashlib
import io
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from study import ROOT, read, write, file_hash
from analyze import analyze
from reasoning_analyze import analyze as reasoning

def figure_bytes():
    a=analyze();b=reasoning()
    methods=[('Jev',a['jev']),('Qwen native',a['qwen_native']),('Qwen + 512-token deliberation',b)]
    matrix=[];labels=[]
    cells=['explicit__complete','explicit__relevant_omission','explicit__irrelevant_omission',
           'product__complete','product__relevant_omission','product__irrelevant_omission']
    for name,s in methods:
        for mapping in ('0','1'):
            row=s['mappings'][mapping]
            labels.append(name+' / map '+mapping)
            matrix.append([row['cells'][c]['correct'] for c in cells]+[row['complete_parents']])
    labels.append('Known-grammar code')
    row=a['baselines']['scope_aware'];matrix.append([row['cells'][c]['correct'] for c in cells]+[row['complete_parents']])
    data=np.array(matrix)
    with plt.rc_context({'font.family':'DejaVu Sans','font.size':10,'svg.hashsalt':'coverage-result-v1'}):
        fig,ax=plt.subplots(figsize=(13.2,6.2));fig.subplots_adjust(left=.30,right=.96,bottom=.25,top=.77)
        ax.imshow(data,cmap='YlGnBu',vmin=0,vmax=12,aspect='auto')
        for i in range(len(labels)):
            for k in range(7):ax.text(k,i,f'{data[i,k]}/12',ha='center',va='center',color='white' if data[i,k]>=8 else '#172b3c',fontweight='bold')
        ax.set_yticks(range(len(labels)),labels)
        ax.set_xticks(range(7),['ID\ncomplete','ID\nrelevant\nomission','ID\nirrelevant\nomission',
                      'Product\ncomplete','Product\nrelevant\nomission','Product\nirrelevant\nomission','Complete\n6-input\nparents'])
        ax.tick_params(length=0,pad=9)
        ax.axvline(5.5,color='white',linewidth=4)
        for spine in ax.spines.values():spine.set_visible(False)
        fig.text(.025,.93,'One visible match: when is caution wrong?',fontsize=19,fontweight='bold',color='#173546')
        fig.text(.025,.875,'Correct decisions by evidence condition; all cells have 12 parent scenarios. Higher is better.',fontsize=11)
        fig.text(.025,.10,'Exploratory: 72 constructed inputs, two option orders; zero independent reviews of these new inputs.',fontsize=10)
        fig.text(.025,.06,'Deliberation is an outcome-aware, extra-compute control with a 512-token cap and forced final boundary; all truncations retained.',fontsize=9)
        fig.text(.025,.025,'Source: Jev Scope Challenge / candidate-completeness. Program-derived references; a template-aware program solves all cases.',fontsize=9)
        output={}
        for fmt in ('png','svg'):
            buf=io.BytesIO();meta={'Software':'Jev Scope Challenge'} if fmt=='png' else {'Date':None,'Creator':'Jev Scope Challenge'}
            fig.savefig(buf,format=fmt,dpi=180,facecolor='white',metadata=meta);output[fmt]=buf.getvalue()
            if fmt=='svg':
                output[fmt]=('\n'.join(line.rstrip() for line in output[fmt].decode('utf-8').splitlines())+'\n').encode('utf-8')
        plt.close(fig)
    return output

def build(verify=False):
    # Rendering bytes can vary with Matplotlib/font versions. Verify chart data
    # independently and require artifacts; the publication manifest preserves bytes.
    if verify:
        analyze();reasoning()
        m=read(ROOT/'figures/manifest.json')
        for n,h in m['source_sha256_lf'].items():assert file_hash(ROOT/n)==h
        for n,h in m['artifact_sha256'].items():assert hashlib.sha256((ROOT/'figures'/n).read_bytes()).hexdigest()==h
        return
    out=figure_bytes();folder=ROOT/'figures';folder.mkdir(exist_ok=True)
    for fmt,data in out.items():(folder/('coverage_cells.'+fmt)).write_bytes(data)
    write(folder/'manifest.json',{'matplotlib_version':matplotlib.__version__,
        'source_sha256_lf':{n:file_hash(ROOT/n) for n in ('results/summary.json','results/reasoning_summary.json','plot_results.py')},
        'artifact_sha256':{'coverage_cells.'+fmt:hashlib.sha256(data).hexdigest() for fmt,data in out.items()}})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');build(p.parse_args().verify)
    print('Coverage figure inputs verified / figures generated.')
