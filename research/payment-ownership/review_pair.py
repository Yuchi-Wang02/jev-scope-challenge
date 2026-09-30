"""Compare preserved submissions without changing model references. Offline only."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from study import ROOT, rows, read
from review_check import validate
from audit_review import verify as verify_author, resolve

B = ROOT / 'review/submissions/tiancheng'
OUTPUT = ROOT / 'review/comparison.json'


def records(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def compare():
    verify_author()  # Original first-receipt status is a historical snapshot.
    receipt = read(B / 'receipt.json')
    original = B / 'payment_review_tianchengi.csv'
    normalized = B / 'validation_copy_iso_date.csv'
    for path, key in [(original, 'original_sha256'), (normalized, 'validation_copy_sha256')]:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt[key]
    original_rows, b = records(original), records(normalized)
    differences = [{'review_id':x['review_id'], 'column':k, 'original':x[k], 'normalized':y[k]}
                   for x,y in zip(original_rows,b) for k in x if x[k] != y[k]]
    assert len(original_rows) == len(b) == 96
    assert differences == [{k:change[k] for k in ('review_id','column','original','normalized')}
                           for change in receipt['normalizations']]
    assert differences == [{'review_id':'r_0468aabda298', 'column':'reviewed_at',
                            'original':'9/30/2026', 'normalized':'2026-09-30'}]
    assert validate(normalized)['complete'] == 96
    a = {r['review_id']:r for r in records(ROOT / 'review/submissions/yuchi/payment_review_yuchi_excel.csv')}
    inputs = {r['review_id']:r['state'] for r in rows(ROOT / 'review/inputs.jsonl')}
    mapping = {r['review_id']:r for r in rows(ROOT / 'review/mapping.jsonl')}
    cases = {r['case_id']:r for r in rows(ROOT / 'data/cases.jsonl')}
    output=[]; paths=0
    for r in b:
        rid=r['review_id']; state=inputs[rid]; c=cases[mapping[rid]['case_id']]
        for p in r['evidence_paths'].split(';'):
            p=p.strip()
            if p.startswith('state.'):p=p[6:]
            assert resolve([state], re.findall(r'[^.\[\]]+',p)); paths+=1
        conditional=c['style']=='item_reference'
        assert r['ambiguous']==('yes' if conditional else 'no')
        assert ('AMBIGUITY:' in r['notes'])==conditional
        if conditional:assert 'UNRESOLVED/NOT_ESTABLISHED' in r['notes']
        same={k:r[k]==a[rid][k] for k in ('target_order_id','destination_id','label','ambiguous')}
        output.append({'review_id':rid, **mapping[rid], 'style':c['style'],
                       'yuchi_label':a[rid]['label'],'tiancheng_label':r['label'],
                       'yuchi_ambiguous':a[rid]['ambiguous'],'tiancheng_ambiguous':r['ambiguous'],
                       'same':same,'scope_objection':conditional,
                       'reporting_status':'conditional_reference' if conditional else 'no_scope_objection'})
    agreements={k:sum(r['same'][k] for r in output) for k in output[0]['same']}
    assert agreements=={'target_order_id':96,'destination_id':96,'label':96,'ambiguous':48}
    assert paths==336
    return {'status':'two submissions received; scope objection retained',
            'author_review_items':96,'non_author_review_submissions':1,
            'non_author_relationship_basis':'user-relayed self-report, not independently verified',
            'total_annotation_rows':192,'distinct_review_items':96,'base_inputs':48,'parent_scenes':12,
            'agreements':agreements,'tiancheng_evidence_paths_resolved':paths,
            'conditional_review_items':48,'conditional_base_inputs':24,
            'adjudicated_reference_updates':0,'reviewer_endorsed_adjudication':False,
            'new_model_calls':0,'items':output}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args()
    result=compare()
    if args.verify:assert read(OUTPUT)==result
    else:OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='items'},indent=2))
