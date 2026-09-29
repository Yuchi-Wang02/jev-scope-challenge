"""Post-run integrity checks, including the review boundary and CSV evidence."""
import csv
import json
from guard_study import HERE, GAP, read_rows, verify


def check():
    outcome=verify()
    runtime=json.loads((HERE/'results/runtime.json').read_text(encoding='utf-8'))
    if runtime['execution_commit']!='48e8d95d9632c1858017af6e251fd9ca98edad6d':
        raise ValueError('Foreign execution source')
    review=json.loads((GAP/'review/manifest.json').read_text(encoding='utf-8'))
    if review['annotations']!=0 or review['reserved_inference_open']:
        raise ValueError('Deferred human-review state changed; version the follow-up')
    rows=read_rows(HERE/'results/predictions.jsonl')
    with (HERE/'results/decisions.csv').open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;actual=list(reader)
    wanted=['arm','method','id','parent','variant','mapping','raw_prediction','prediction','changed','nominal_model_calls','uses_known_grammar']
    if fields!=wanted or actual!=[{k:str(r[k]) for k in wanted} for r in rows]:
        raise ValueError('Decision CSV differs from saved method rows')
    return outcome


if __name__=='__main__':print(json.dumps(check()))
