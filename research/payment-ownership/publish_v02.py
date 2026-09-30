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
    audit=('**2026-09-30 author-review update:** one author completed 96 review items; '
           'no second reviewer or adjudicated reference update. The submission agrees '
           'with original references but raises an unresolved candidate-scope issue '
           'for 48 product-reference review items (24 underlying inputs). Explicit-ID '
           'inputs remain 24/24 per condition. Full-grid scores below use original '
           'references; product-reference correctness is conditional on a displayed-candidate '
           'interpretation. Read the [review audit and preserved submission](REVIEW_AUDIT.md).\n\n')
    md=md.replace('**Status: completed. Independent human annotations: 0.**',
                  '**Execution: completed. One author review received; independent two-reviewer adjudication pending.**')
    md=md.replace('This is a static diagnostic',audit+'This is a static diagnostic',1)
    html=report.replay_html(s)
    html=html.replace('href="../research/',f'href="{GITHUB}research/')
    html=html.replace('RESULTS.md"','RESULTS_V02.md"')
    html=html.replace('independent human review pending.',
                      'one author review received; second review and adjudication pending.')
    html=html.replace('has not been independently reviewed.',
                      'has one author review with a scope objection; independent adjudication remains pending.')
    review_banner='''<section class="tag"><strong>Author review received; candidate scope unresolved.</strong>
<p>One author completed 96 review items. All agree with original references, with a cover-note objection affecting 48 product-reference items (24 underlying inputs). The input says the displayed orders are a selected subset without guaranteeing that the target is among them. No second review or reference update is complete.</p>
<p>Explicit-ID inputs remain 24/24 in each condition. Product-reference correctness depends on interpreting the displayed orders as the candidate set. The saved full-grid scores and embedded freeze-time metadata are historical, not unconditional human validation. <a href="'''+GITHUB+'''research/payment-ownership/REVIEW_AUDIT.md">Read the audit</a></p></section>'''
    html=html.replace('<section><label>Case',review_banner+'<section><label>Case',1)
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
