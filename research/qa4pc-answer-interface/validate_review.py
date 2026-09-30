"""Validate exported review JSON without changing references or claiming human status."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PACKETS=ROOT/'.local'/'qa4pc-interface-review-v1'
PROCESS=('seen_model_summaries','seen_case_outputs','seen_source_labels','seen_other_review',
         'seen_audit_discussion','used_ai','discussed_with_others')


def unique_object(pairs):
    obj={}
    for key,value in pairs:
        if key in obj:raise ValueError('Duplicate JSON key')
        obj[key]=value
    return obj


def validate(payload,packet):
    required={'schema_version','packet_sha256','slot','submission_type','exported_at_client','reviewer','responses'}
    if not isinstance(payload,dict) or set(payload)!=required:raise ValueError('Unexpected submission schema')
    if type(payload['schema_version'])!=int or payload['schema_version']!=1:raise ValueError('Schema version')
    if payload['packet_sha256']!=packet['packet_sha256'] or payload['slot']!=packet['slot']:raise ValueError('Wrong packet/slot')
    if payload['submission_type'] not in ('draft','completed'):raise ValueError('Submission type')
    reviewer=payload['reviewer']
    if not isinstance(reviewer,dict) or set(reviewer)!={'name','relationship','process_notes',*PROCESS}:raise ValueError('Reviewer record schema')
    if any(not isinstance(v,str) for v in reviewer.values()):raise ValueError('Reviewer field type')
    if any(reviewer[k] not in ('','yes','no','unsure') for k in PROCESS):raise ValueError('Process value')
    responses=payload['responses'];expected={i['review_id'] for i in packet['items']}
    if not isinstance(responses,list) or len(responses)!=len(expected):raise ValueError('Response count')
    seen=set();complete=0
    for r in responses:
        if not isinstance(r,dict) or set(r)!={'review_id','judgment','evidence','ambiguity','missing_information','notes'}:raise ValueError('Response schema')
        if any(not isinstance(v,str) for v in r.values()):raise ValueError('Response field type')
        if r['review_id'] not in expected or r['review_id'] in seen:raise ValueError('Unknown/repeated review ID')
        seen.add(r['review_id'])
        if r['judgment'] not in ('','yes','no','maybe') or r['ambiguity'] not in ('','yes','no','unsure'):raise ValueError('Unknown judgment')
        complete+=bool(r['judgment'] and r['ambiguity'] and r['evidence'].strip())
    process_complete=bool(reviewer['name'].strip() and reviewer['relationship'].strip() and all(reviewer[k] for k in PROCESS))
    if payload['submission_type']=='completed' and (complete!=len(expected) or not process_complete):raise ValueError('Incomplete final submission')
    return {'submission_type':payload['submission_type'],'completed_items':complete,'expected_items':len(expected),
        'process_record_complete':process_complete,
        'process_self_report_no_exposure_or_assistance':process_complete and all(reviewer[k]=='no' for k in PROCESS),
        'process_explanation_needed':any(reviewer[k] in ('yes','unsure') for k in PROCESS) and not reviewer['process_notes'].strip(),
        'human_identity_or_independence_verified':False,'reference_updates':0,'model_calls':0}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('submission',type=Path);a=p.parse_args()
    raw=a.submission.read_bytes();payload=json.loads(raw,object_pairs_hook=unique_object)
    slot=payload.get('slot')
    if slot not in ('A','B'):raise ValueError('Unknown slot')
    packet=json.loads((PACKETS/f'packet_{slot}.json').read_bytes())
    result=validate(payload,packet);result['submission_sha256']=hashlib.sha256(raw).hexdigest()
    print(json.dumps(result))
