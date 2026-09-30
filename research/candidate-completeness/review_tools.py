"""Create neutral review-only materials; validate submissions without adopting labels."""
import argparse
import csv
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from study import ROOT, LABELS, rows, canonical, sha

FIELDS=['review_id','reviewer_id','reviewed_at','target_order_id','destination_id','label','evidence_paths','ambiguous','notes']

def materials():
    ordered=sorted(rows(ROOT/'data/cases.jsonl'),key=lambda c:sha(('review-coverage-v1'+c['case_id']).encode()))
    inputs=[{'review_id':f'R{i+1:03d}','state':c['state']} for i,c in enumerate(ordered)]
    mapping=[{'review_id':r['review_id'],'case_id':c['case_id']} for r,c in zip(inputs,ordered)]
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=FIELDS,lineterminator='\n');w.writeheader()
    for r in inputs:w.writerow({'review_id':r['review_id']})
    instruction='''# Candidate coverage: independent semantic review

Review these 72 constructed items using only each visible state and its component
policy. This is new material; previous payment-study reviews do not cover it.
The task asks only whether the requested refund destination satisfies the stated
restriction, not whether a complete return is permitted. Coverage declarations
are supplied hypothetical premises. Do not consult the upstream database to
override them. If you find the premises unclear or inconsistent, record why.

For each item independently record target order ID or UNRESOLVED; destination ID
or UNRESOLVED; VALID_DESTINATION / INVALID_DESTINATION / NOT_ESTABLISHED; evidence
paths into the displayed state; ambiguous yes/no; a short reason; reviewer ID and
ISO date/time. Evidence paths can identify coverage_statement, customer_request,
component_policy, orders[0].order_id, or payment fields as appropriate.

Use review.html offline, or fill reviewer.csv. The interface saves locally under
your reviewer ID and exports CSV; export and keep a separate copy. Do not share a
browser profile and reviewer ID. Reviewers must work independently before seeing
another export or discussing case interpretations. Please complete cover_note.txt.
Do not consult model outputs, construction labels or other reviewers' judgments.
This ZIP excludes those fields; it cannot prevent access to the public repository.
Record any exposure rather than treating procedural blinding as guaranteed.

Preserve the original completed export. Format validation is not semantic
validation or verification of independence. Disagreements require documented
adjudication; no label is automatically replaced by an AI or by a majority vote.
This exploratory material cannot become untouched confirmation through later review.
Source records are simulated, from Sierra tau2-bench at pinned revision
5bfa7e37b36656b37dc6d022156be6563c1007f3. Source MIT license is included.
'''
    cover='''Reviewer name/identifier:
Relationship to the project / author role:
Start and finish dates (include timezone if time is provided):
Before/during review, exposure to model summaries or specific outputs:
Exposure to program labels or any previous review/discussion:
AI assistance (what and how), if any:
Discussion with others (what and when), if any:
Overall uncertainties or comments:
Permission for public attribution (name or reviewer ID preference):
'''
    html=(ROOT/'review_template.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(inputs,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
    files={'README.md':instruction,'cover_note.txt':cover,'reviewer.csv':stream.getvalue(),
           'inputs.jsonl':''.join(canonical(r)+'\n' for r in inputs),'review.html':html,
           'LICENSE':(ROOT/'vendor/LICENSE').read_text(encoding='utf-8')}
    return files,mapping

def package(verify=False):
    files,mapping=materials();base=ROOT/'review';base.mkdir(exist_ok=True)
    for name,text in files.items():
        if verify:assert (base/name).read_text(encoding='utf-8')==text,name
        else:(base/name).write_text(text,encoding='utf-8',newline='\n')
    maptext=''.join(canonical(r)+'\n' for r in mapping)
    if verify:assert (base/'mapping.jsonl').read_text()==maptext
    else:(base/'mapping.jsonl').write_text(maptext,encoding='utf-8',newline='\n')
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,text in files.items():
            info=zipfile.ZipInfo(name,date_time=(2026,9,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,text.encode())
    if verify:assert (base/'review_package.zip').read_bytes()==data.getvalue()
    else:(base/'review_package.zip').write_bytes(data.getvalue())
    return {'review_items':72,'submissions_received':0,'labels_or_outputs_in_package':False}

def validate(path):
    inputs={r['review_id']:r for r in rows(ROOT/'review/inputs.jsonl')}
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);assert reader.fieldnames==FIELDS;records=list(reader)
    assert len(records)==72 and len({r['review_id'] for r in records})==72
    assert {r['review_id'] for r in records}==set(inputs)
    complete=[]
    for r in records:
        if not any(r[k].strip() for k in FIELDS[1:]):continue
        assert all(r[k].strip() for k in FIELDS),r['review_id']
        assert r['label'] in LABELS and r['ambiguous'] in ('yes','no')
        datetime.fromisoformat(r['reviewed_at'].replace('Z','+00:00'))
        state=inputs[r['review_id']]['state']
        assert r['target_order_id']=='UNRESOLVED' or r['target_order_id'] in {o['order_id'] for o in state['orders']}
        assert r['destination_id']=='UNRESOLVED' or r['destination_id'] in state['user_profile']['payment_methods']
        complete.append(r)
    assert len({r['reviewer_id'] for r in complete})<=1
    return {'rows':72,'complete':len(complete),'remaining':72-len(complete),'labels_adopted':False,'independence_verified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');p.add_argument('--csv',type=Path);a=p.parse_args()
    print(json.dumps(validate(a.csv) if a.csv else package(a.verify),indent=2))
