"""Read-only validation of later rewrite-review CSVs; never certifies human independence."""
import argparse
import csv
import hashlib
import io
import json
from datetime import date
from pathlib import Path

HERE=Path(__file__).resolve().parent
FIELDS=('review_id','same_facts_yes_no_unclear','reason','correction','reviewer','reviewed_at')


def fingerprint():
    return hashlib.sha256((HERE/'review/blind_pairs.json').read_bytes().replace(b'\r\n',b'\n')).hexdigest()


def inspect_csv(payload,pack_sha256):
    if pack_sha256!=fingerprint():raise ValueError('Review pack fingerprint mismatch')
    pairs=json.loads((HERE/'review/blind_pairs.json').read_text(encoding='utf-8'))
    known={p['review_id'] for p in pairs};reader=csv.DictReader(io.StringIO(payload))
    if reader.fieldnames!=list(FIELDS):raise ValueError('Unexpected review CSV columns')
    seen=set();submitted=[]
    for row in reader:
        if set(row)!=set(FIELDS) or any(v is None for v in row.values()):raise ValueError('Malformed review row')
        ident=row['review_id']
        if ident not in known or ident in seen:raise ValueError('Unknown or duplicate review ID')
        seen.add(ident)
        if all(not row[k].strip() for k in FIELDS[1:]):continue
        decision=row['same_facts_yes_no_unclear'].strip()
        if decision not in ('yes','no','unclear'):raise ValueError('Incomplete or invalid same-facts decision')
        if any(not row[k].strip() for k in ('reason','reviewer','reviewed_at')):raise ValueError('Reason, reviewer and review date required')
        try:date.fromisoformat(row['reviewed_at'].strip())
        except ValueError:raise ValueError('Review date must be YYYY-MM-DD') from None
        submitted.append(row)
    counts={label:sum(r['same_facts_yes_no_unclear'].strip()==label for r in submitted) for label in ('yes','no','unclear')}
    return {'status':'awaiting_independent_review' if not submitted else 'export_requires_provenance_and_adjudication',
        'read_only':True,'pack_sha256_lf':pack_sha256,'candidate_pairs':len(pairs),'submitted_rows':len(submitted),
        'unreviewed_pairs':len(pairs)-len(submitted),'decisions':counts,
        'adjudication_ids':[r['review_id'] for r in submitted if r['same_facts_yes_no_unclear'].strip()!='yes' or r['correction'].strip()],
        'reviewer_independence_verified':False,'semantic_truth_certified':False,'rewrite_inference_open':False,
        'note':'CSV syntax and declared identity do not establish human authorship, independence or semantic correctness.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,default=HERE/'review/blank.csv')
    parser.add_argument('--pack-sha256',help='Required for a submitted CSV; omitted only for the committed blank template')
    args=parser.parse_args()
    if args.pack_sha256 is None and args.input.resolve()!=(HERE/'review/blank.csv').resolve():parser.error('A submitted file requires --pack-sha256 from its original review pack')
    print(json.dumps(inspect_csv(args.input.read_text(encoding='utf-8-sig'),args.pack_sha256 or fingerprint()),indent=2))
