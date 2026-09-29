"""Create blank procedural-blind review material and validate later human exports.

This tool never supplies labels or opens reserved model inference.
"""
import argparse
import csv
import hashlib
import io
import json
import random
from gap_run import HERE, read_rows, sha

FIELDS=('review_id','label','reason','ambiguity','ambiguity_reason','reviewer','reviewed_at')


def material():
    cases=read_rows(HERE/'data/cases.jsonl')
    random.Random(20261002).shuffle(cases)
    pack=[];key=[]
    for c in cases:
        ident='R-'+hashlib.sha256(('gap-review-v1/'+c['id']).encode()).hexdigest()[:12]
        pack.append({'review_id':ident,'state':c['state'],'policy':c['instruction']})
        key.append({'review_id':ident,'id':c['id'],'parent':c['parent'],'split':c['split'],
                    'family':c['family'],'variant':c['variant'],'program_gold':c['gold']})
    starter_ids={c['id'] for c in cases if c['parent'] in
                 ('joint_approval-1','reversal_exception-1','route_lookup-1') and
                 c['variant'] in ('decisive_missing','nondecisive_missing')}
    starter=[p['review_id'] for p,k in zip(pack,key) if k['id'] in starter_ids]
    return pack,key,starter


def files():
    pack,key,starter=material()
    manifest={'status':'awaiting_independent_human_review','annotations':0,
              'case_sha256_lf':sha((HERE/'data/cases.jsonl').read_bytes().replace(b'\r\n',b'\n')),
              'candidate_inputs':288,'starter_inputs':6,'starter_ids':starter,
              'reserved_inference_open':False,'blinding':'procedural only; public key exists separately'}
    buf=io.StringIO(newline='');writer=csv.writer(buf,lineterminator='\n')
    writer.writerow(FIELDS)
    for row in pack:writer.writerow([row['review_id'],'','','','','',''])
    page=(HERE/'review_template.html').read_text(encoding='utf-8')
    payload=json.dumps({'items':pack,'starter':starter,'case_sha256_lf':manifest['case_sha256_lf']},ensure_ascii=False).replace('<','\\u003c')
    return {'review/review.html':page.replace('__REVIEW_DATA__',payload),
            'review/pack.json':json.dumps(pack,ensure_ascii=False,indent=2)+'\n',
            'review/answer_key.json':json.dumps(key,indent=2)+'\n',
            'review/manifest.json':json.dumps(manifest,indent=2)+'\n',
            'review/blank.csv':buf.getvalue()}


def validate_annotations(rows,known):
    seen=set()
    for row in rows:
        if set(row)!=set(FIELDS):raise ValueError('Annotation field mismatch')
        if row['review_id'] not in known or row['review_id'] in seen:raise ValueError('Foreign or duplicate review item')
        seen.add(row['review_id'])
        if row['label'] not in ('ALLOW','DENY','INSUFFICIENT'):raise ValueError('Missing or invalid human label')
        if any(not isinstance(row[k],str) or not row[k].strip() for k in ('reason','reviewer','reviewed_at')):
            raise ValueError('Reason, reviewer and date required')
        if type(row['ambiguity'])!=bool:raise ValueError('Ambiguity must be boolean')
        if not isinstance(row['ambiguity_reason'],str) or (row['ambiguity'] and not row['ambiguity_reason'].strip()):
            raise ValueError('Explain flagged ambiguity')
    return seen


def ingest(path):
    obj=json.loads(path.read_text(encoding='utf-8'));pack,key,_=material()
    fingerprint=json.loads((HERE/'review/manifest.json').read_text(encoding='utf-8'))['case_sha256_lf']
    if obj.get('case_sha256_lf')!=fingerprint:raise ValueError('Foreign corpus annotation export')
    rows=obj['annotations'];known={k['review_id']:k for k in key}
    reviewed=validate_annotations(rows,known)
    disagreements=[r['review_id'] for r in rows if r['label']!=known[r['review_id']]['program_gold']]
    ambiguous=[r['review_id'] for r in rows if r['ambiguity']]
    return {'status':'human_export_requires_provenance_and_adjudication',
            'submitted_annotations':len(rows),'candidate_inputs':len(pack),'unreviewed_inputs':len(pack)-len(reviewed),
            'program_label_disagreements':disagreements,'flagged_ambiguities':ambiguous,
            'reviewer_names':sorted({r['reviewer'] for r in rows}),
            'independence_verified':False,'reserved_inference_open':False,
            'note':'A syntactically valid export does not certify reviewer independence or resolve disagreements.'}


if __name__=='__main__':
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['build','verify','ingest'])
    parser.add_argument('--input',type=Path)
    args=parser.parse_args()
    if args.command=='ingest':
        if not args.input:parser.error('--input required for ingest')
        print(json.dumps(ingest(args.input),indent=2))
    else:
        for name,payload in files().items():
            path=HERE/name
            if args.command=='build':
                path.parent.mkdir(exist_ok=True);path.write_text(payload,encoding='utf-8',newline='\n')
            elif path.read_text(encoding='utf-8')!=payload:raise ValueError('Review artifact changed: '+name)
        print(json.dumps({'status':'passed','candidate_inputs':288,'starter_inputs':6,'annotations':0,
                          'reserved_inference_open':False,'read_only':args.command=='verify'}))
