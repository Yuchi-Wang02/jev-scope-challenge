"""Post-run known-grammar reference using the same rendered text as the models.

It knows the construction grammar. It is not an arbitrary-language parser and
was implemented after inspecting model outcomes, not a pre-run tuned baseline.
"""
import json
import re
from study import HERE,read_rows,write_json


def decide(state):
    target=re.match(r'Request: grant write access to repository (.+)\.',state)
    if target:
        matches=[a for name,a in re.findall(r'The owner of repository (.+?) says: (grant|deny) write access\.',state) if name==target.group(1)]
        return ('ALLOW' if matches[0]=='grant' else 'DENY') if len(matches)==1 else 'INSUFFICIENT' if not matches else None
    claim=re.match(r'Claim: item (.+?) has rank (\d+) in the supplied report\.',state)
    if claim:
        ranks=[rank for name,rank in re.findall(r'Report row: item (.+?); rank (\d+|not supplied)\.',state) if name==claim.group(1)]
        if not ranks or ranks==['not supplied']:
            return 'INSUFFICIENT'
        return ('ALLOW' if int(ranks[0])==int(claim.group(2)) else 'DENY') if len(ranks)==1 else None
    target=re.match(r'Request: enable notifications for account (.+)\.',state)
    if target:
        matches=[a for name,a in re.findall(r'Current instruction for account (.+?): (enable|disable) notifications\.',state) if name==target.group(1)]
        return ('ALLOW' if matches[0]=='enable' else 'DENY') if len(matches)==1 else 'INSUFFICIENT' if not matches else None
    return None


if __name__=='__main__':
    cases=read_rows(HERE/'data/cases.jsonl')
    rows=[{'id':c['id'],'parent':c['parent'],'split':c['split'],'state':c['state'],
           'prediction':decide(c['state']),'ok':decide(c['state']) is not None} for c in cases]
    (HERE/'results/C0_text.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8',newline='\n')
    summary={'reference':'post-run known-grammar text parser','model_calls':0,'human_reviewed':False,
             'uses_same_rendered_state':True,'knows_construction_grammar':True,'implemented_after_model_outcomes':True,'splits':{}}
    for split in ('development','calibration','exploratory_test'):
        panel=[c for c in cases if c['split']==split]
        parents={c['parent'] for c in panel}
        summary['splits'][split]={'inputs':len(panel),'correct':sum(decide(c['state'])==c['gold'] for c in panel),
                                'parents':len(parents),'complete_parents':sum(all(decide(c['state'])==c['gold'] for c in panel if c['parent']==p) for p in parents)}
    write_json(HERE/'results/C0_text_summary.json',summary)
    print(json.dumps(summary,indent=2))
