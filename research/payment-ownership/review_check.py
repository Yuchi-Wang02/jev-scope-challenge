"""Read-only review export validation; no automatic label adoption."""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from study import ROOT, LABELS, rows

def validate(path):
    expected={r['review_id'] for r in rows(ROOT/'review/inputs.jsonl')}
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        records=list(csv.DictReader(f))
    ids=[r.get('review_id') for r in records]
    if len(ids)!=len(set(ids)) or set(ids)!=expected: raise ValueError('Missing/extra/duplicate review IDs')
    complete=[]; reviewers=set()
    for r in records:
        fields=['reviewer_id','reviewed_at','target_order_id','destination_id','label','evidence_paths','ambiguous','notes']
        if not any(r.get(k,'').strip() for k in fields): continue
        if not all(r.get(k,'').strip() for k in fields): raise ValueError('Partially completed item: '+r['review_id'])
        if r['label'] not in LABELS or r['ambiguous'] not in ['yes','no']: raise ValueError('Invalid category')
        datetime.fromisoformat(r['reviewed_at'].replace('Z','+00:00'))
        reviewers.add(r['reviewer_id']);complete.append(r)
    if len(reviewers)>1: raise ValueError('One export must identify one reviewer')
    return {'items':len(records),'complete':len(complete),'remaining':len(records)-len(complete),
            'reviewer_ids':sorted(reviewers),'independence_verified':False,'labels_adopted':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('csv');print(json.dumps(validate(p.parse_args().csv),indent=2))
