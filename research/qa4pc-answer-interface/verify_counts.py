"""Independent source/raw-action count replay; optionally verify decoded token bytes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def verify(source_dir,model_dir=None):
    manifest=json.loads((HERE/'plan_manifest.json').read_bytes())
    cohort=json.loads((HERE/'cohort.json').read_bytes());report=json.loads((HERE/'report.json').read_bytes())
    for name,(sha,size) in cohort['source']['qa4pc_file_pins'].items():
        raw=(source_dir/name).read_bytes()
        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Source bytes drift')
    refs={r['utterance_id']:r['answer'] for r in json.loads((source_dir/'dev_entailment_qa4pc.json').read_bytes())}
    tokenizer=None
    if model_dir:
        # Tokenizer verification is independent of the result adapters and adds
        # no forwards; pinned byte checking uses existing compilation support.
        from compile_plan import checked_tokenizer
        tokenizer,_=checked_tokenizer(model_dir)
    actions={};observations={};totals={};decoded=0
    for backend in ('jev','qwen'):
        events=[json.loads(s) for s in (HERE/'results'/f'{backend}.jsonl').read_text(encoding='utf-8').splitlines()]
        starts=[e['job_id'] for e in events if e['event']=='call_start']
        finishes=[e for e in events if e['event']=='call_finish']
        expected=[j['id'] for j in manifest['jobs'] if j['backend']==backend]
        if starts!=expected or [e['job_id'] for e in finishes]!=expected:raise ValueError('Missing/repeated/reordered job')
        for e in finishes:observations[e['job_id']]=e['result']
        totals[backend]={k:sum(e['result'][k] for e in finishes) for k in ('input_tokens','output_tokens')}
        for k in totals[backend]:
            if totals[backend][k]!=report['cost'][backend][k]:raise ValueError('Cost mismatch')
    for j in manifest['jobs']:
        r=observations[j['id']];d=r['detail'];action=None
        if r['status']!='ok':raise ValueError('Independent complete-grid replay requires successful transport')
        if j['backend']=='jev':
            raw=d['raw_response'];choice=raw['answers']['decision']['choice']
            action=j['options']['ABC'.index(choice)]
        elif j['arm']=='finite':
            vals=d['first_candidate_logits'];winners=[i for i,v in enumerate(vals) if v==max(vals)]
            action=j['options'][winners[0]] if len(winners)==1 else None
        else:
            ids=d['output_ids'];ended=bool(ids and ids[-1]==248046 and ids.count(248046)==1)
            if ended!=d['ended_eos']:raise ValueError('EOS mismatch')
            if tokenizer:
                body_ids=ids[:-1] if ended else ids
                text=tokenizer.decode(body_ids,skip_special_tokens=False)
                bad=any(t in set(tokenizer.all_special_ids) for t in body_ids) or any(x in text for x in ('<|','|>','<think>','</think>'))
                if text!=d['decoded_body'] or bad!=d['unsupported_special']:raise ValueError('Decoded token mismatch')
                decoded+=1
            body=d['decoded_body'].strip()
            if ended and not d['unsupported_special']:
                if j['arm']=='letter' and body in ('A','B','C'):action=j['options']['ABC'.index(body)]
                if j['arm']=='semantic' and body in ('yes','no','maybe'):action=body
        if action!=r['action']:raise ValueError('Independent action differs')
        actions[j['id']]=action
    counts={};invalid={};aggregates={}
    for arm in ('native','finite','letter','semantic'):
        counts[arm]=[];invalid[arm]=[]
        for m in range(6):
            jobs=[j for j in manifest['jobs'] if j['phase']=='main' and j['arm']==arm and j['mapping']==m]
            correct=sum(actions[j['id']]==refs[j['item_id']] for j in jobs)
            bad=sum(actions[j['id']] is None for j in jobs)
            if correct!=report['per_mapping'][arm][m]['correct'] or bad!=report['per_mapping'][arm][m]['invalid']:
                raise ValueError('Independent counts differ')
            counts[arm].append(correct);invalid[arm].append(bad)
        correct=abstain=0
        for uid in {j['item_id'] for j in manifest['jobs'] if j['phase']=='main'}:
            votes=Counter(actions[j['id']] for j in manifest['jobs'] if j['item_id']==uid and j['arm']==arm)
            winners=[label for label,n in votes.items() if label is not None and n>=4]
            a=winners[0] if winners else None;correct+=a==refs[uid];abstain+=a is None
        aggregates[arm]={'correct':correct,'abstentions':abstain}
        if any(v!=report['strict_majority'][arm][k] for k,v in aggregates[arm].items()):raise ValueError('Independent aggregation differs')
    pairs=[(j['id'],j['id'].removesuffix('_finite')+'_letter') for j in manifest['jobs'] if j['arm']=='finite']
    same=sum(observations[a]['detail']['first_candidate_logits']==observations[b]['detail']['first_candidate_logits'] for a,b in pairs)
    main=[j for j in manifest['jobs'] if j['phase']=='main' and j['arm']=='finite']
    ties=sum(len([v for v in observations[j['id']]['detail']['first_candidate_logits'] if v==max(observations[j['id']]['detail']['first_candidate_logits'])])>1 for j in main)
    return {'verified_jobs':len(actions),'per_mapping_correct':counts,'per_mapping_invalid':invalid,
        'strict_majority':aggregates,'tokenizer_verified_generations':decoded,
        'letter_pair_count':len(pairs),'identical_letter_candidate_logits':same,'main_finite_ties':ties,
        'actual_token_totals':totals,'no_model_forwards':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path,required=True)
    p.add_argument('--model-dir',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();r=verify(a.source_dir,a.model_dir)
    if a.output:a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r))
