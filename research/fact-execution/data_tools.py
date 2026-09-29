"""Original-development fact references plus unscored candidate language rewrites."""
import csv
import io
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
GAP=HERE.parent/'evidence-gap'
sys.path.insert(0,str(GAP))
from gap_data import constraints, sentence
from gap_run import read_rows, write_json, sha
from interface import compile_visible, status_for, execute


def original_cases():
    rows=[c for c in read_rows(GAP/'data/cases.jsonl') if c['split']=='development']
    if len(rows)!=72 or len({c['id'] for c in rows})!=72 or any(c['family']=='composed_route' for c in rows):
        raise ValueError('Foreign development extraction')
    return rows


def candidate_sentence(record,case,style):
    k,v,t=record['field'],record['value'],record['scope'];a,b=case['sites']
    if k.startswith('review_'):
        role='A' if k=='review_a' else 'B'
        return (f"For request {t}, reviewer {role}'s recorded decision is "+('approval.' if v else 'rejection.')) if style==0 else f"Request {t} was "+('approved' if v else 'rejected')+f' by reviewer {role}.'
    if k=='base':return f'The recorded baseline outcome for request {t} is '+('ALLOW.' if v else 'DENY.')
    if k=='exception':return f'For request {t}, the reversal exception is '+('in force.' if v else 'not in force.') if style==0 else f'The reversal-exception status of request {t} is '+('ACTIVE.' if v else 'INACTIVE.')
    if k=='route':return f'Request {t} is assigned to '+(b if v else a)+'.' if style==0 else f'Route entry: request {t} -> '+(b if v else a)+'.'
    site=a if k=='site_a' else b
    return f'Under request {t}, site {site} has permission set to '+('allowed.' if v else 'blocked.') if style==0 else f'Permission entry for request {t} at {site}: '+('ALLOWED.' if v else 'BLOCKED.')


def material():
    cases=original_cases();references=[];candidates=[]
    for c in cases:
        schema=compile_visible(c['state'],c['instruction']);facts={}
        for field,values in constraints(c).items():
            status=status_for(values);facts[field]=status;spans=[]
            for r in c['records']:
                if r['scope']==c['target'] and r['field']==field:
                    quote=sentence(r,c);start=c['state'].find(quote)
                    if start<0:raise ValueError('Reference quote not found')
                    spans.append({'start':start,'end':start+len(quote),'text':quote,'value':r['value']})
            references.append({'id':c['id']+'/'+field,'source_id':c['id'],'field':field,'status':status,
                'evidence_spans':spans,'provenance':'program-derived construction reference, not human annotation'})
        if execute(schema,facts)!=c['gold']:raise ValueError('Interface execution changed truth')
        for style in range(2):
            state=c['state'].splitlines()[0]+'\nSupplied records:\n'+'\n'.join(candidate_sentence(r,c,style) for r in c['records'])
            ident='P-'+sha((c['id']+'/'+str(style)).encode())[:12]
            candidates.append({'review_id':ident,'source_id':c['id'],'parent':c['parent'],'representation':'review_only',
                'original_state':c['state'],'candidate_state':state,'policy':c['instruction'],
                'intended_same_facts':True,'human_semantics_verified':False,'model_scored':False})
    return cases,references,candidates


def files():
    cases,refs,candidates=material()
    outputs={name:''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows) for name,rows in [
        ('data/original_cases.jsonl',cases),('data/reference_facts.jsonl',refs),('review/candidate_rewrites.jsonl',candidates)]}
    blind=[{k:c[k] for k in ('review_id','original_state','candidate_state','policy')} for c in candidates]
    outputs['review/blind_pairs.json']=json.dumps(blind,ensure_ascii=False,indent=2)+'\n'
    buf=io.StringIO();w=csv.writer(buf,lineterminator='\n');w.writerow(['review_id','same_facts_yes_no_unclear','reason','correction','reviewer','reviewed_at'])
    for c in candidates:w.writerow([c['review_id'],'','','','',''])
    outputs['review/blank.csv']=buf.getvalue()
    outputs['review/manifest.json']=json.dumps({'status':'awaiting_independent_semantic_review','pairs':144,
        'annotations':0,'candidate_model_records':0,'reserved_inference_open':False,
        'blinding':'blind_pairs excludes intended equality/source metadata; public source mapping exists separately'},indent=2)+'\n'
    return outputs


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['build','verify']);args=parser.parse_args()
    for name,payload in files().items():
        path=HERE/name
        if args.command=='verify':
            if path.read_text(encoding='utf-8')!=payload:raise ValueError('Preparation artifact changed: '+name)
        else:path.parent.mkdir(exist_ok=True);path.write_text(payload,encoding='utf-8',newline='\n')
    print(json.dumps({'status':'passed','read_only':args.command=='verify','original_inputs':72,
        'reference_fields':168,'candidate_rewrite_pairs':144,'human_annotations':0,'candidate_model_records':0}))
