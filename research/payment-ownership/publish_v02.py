"""Publication layer for the explicit execution amendment; frozen analysis unchanged."""
import argparse
import json
from study import ROOT, rows
import report

GITHUB='https://github.com/Yuchi-Wang02/jev-scope-challenge/blob/main/'

def publish(verify=False):
    report.publish(verify)
    s=report.summarize()
    note=('**Execution history:** the original all-correct smoke prerequisite failed (5/6). '
          'The [v0.2 amendment](EXECUTION_V02.md) was published before any main-grid call; '
          'it changed only that launch prerequisite. Original inputs and scoring were retained. '
          'Read the [smoke stop audit](SMOKE_AUDIT.md). This is outcome-aware exploratory work.\n\n')
    md=report.result_markdown(s).replace('**Status:',note+'**Status:',1)
    md=md.replace('../../docs/payment_ownership.html','../../docs/payment_ownership_v02.html')
    html=report.replay_html(s)
    html=html.replace('href="../research/',f'href="{GITHUB}research/')
    html=html.replace('RESULTS.md"','RESULTS_V02.md"')
    banner='''<section class="tag"><strong>Smoke: 5/6, including one ambiguity error.</strong>
<p>Two orders both contain a Mug; the request does not identify which order. Jev returned VALID_DESTINATION with probability 0.97; the provisional reference is NOT_ESTABLISHED. This single constructed case awaits independent review.</p>
<p>The original launch prerequisite stopped the run. An explicit amendment was published before the 192 main calls. Main inputs and scoring did not change. <a href="'''+GITHUB+'''research/payment-ownership/SMOKE_AUDIT.md">Inspect the stopped run</a> · <a href="'''+GITHUB+'''research/payment-ownership/EXECUTION_V02.md">Execution amendment</a></p>
<details><summary>All six smoke requests and actual responses</summary><pre id="smoke-records"></pre></details></section>'''
    html=html.replace('<section><label>Case',banner+'<section><label>Case',1)
    script="el('smoke-records').textContent=JSON.stringify(data.jobs.filter(j=>j.phase==='smoke').map(j=>({request:j.body,program_reference:j.reference,response:data.records.find(r=>r.job_id===j.job_id)?.raw_response})),null,2);"
    html=html.replace('for(const c of data.cases)',script+'\nfor(const c of data.cases)',1)
    outputs={ROOT/'RESULTS_V02.md':md,ROOT.parents[1]/'docs/payment_ownership_v02.html':html}
    for path,text in outputs.items():
        if verify:
            if path.read_text(encoding='utf-8')!=text: raise ValueError('Publication mismatch: '+str(path))
        else:path.write_text(text,encoding='utf-8')
    return {'status':'verified' if verify else 'written','primary':s['primary_recorded'],'followup_calls':0}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true')
    print(json.dumps(publish(p.parse_args().verify),indent=2))
