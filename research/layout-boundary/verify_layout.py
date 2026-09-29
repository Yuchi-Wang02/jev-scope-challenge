"""Post-run read-only delivery audit, including the previous derived summary."""
import json
import math
from layout_study import HERE,PRIOR,ARMS,read_rows
from layout_analyze import analyze,check_equal
from verify_study import verify as verify_previous


def verify():
    # The frozen boundary manifest includes prior raw records, but not their
    # derived summary. Recompute that summary before accepting transferred T.
    verify_previous()
    summary,rows=analyze()
    check_equal(summary,json.loads((HERE/'results/summary.json').read_text(encoding='utf-8')))
    for row in rows:
        if row['arm']=='K1':
            causal=row['parity']['causal_logits']
            if len(causal)!=3 or any(not math.isfinite(v) for v in causal):
                raise ValueError('Invalid engineering causal logits')
    expected=json.loads((PRIOR/'results/weight_checksums.json').read_text(encoding='utf-8'))
    if json.loads((HERE/'results/weight_checksums.json').read_text(encoding='utf-8'))!=expected:
        raise ValueError('Weight provenance differs from pinned cached objects')
    adapter=json.loads((HERE/'results/adapter_audit.json').read_text(encoding='utf-8'))
    if adapter!={'status':'passed','exact_tensors':504,'parameters':33030144}:
        raise ValueError('Adapter load audit incomplete')
    audit=json.loads((HERE/'results/input_audit.json').read_text(encoding='utf-8'))
    if audit['status']!='passed' or audit['checked_logical_records']!=2592 or audit['encoded_plans']!=864 or audit['model_calls']!=0:
        raise ValueError('Post-run input audit incomplete')
    return summary


if __name__=='__main__':
    s=verify()
    print(json.dumps({'status':'passed','logical_records':s['logical_records'],
        'scientific_forwards':s['scientific_forwards'],'parity_forwards':s['parity_forwards'],
        'original_anchor_records':s['original_anchor_records'],'read_only':True}))
