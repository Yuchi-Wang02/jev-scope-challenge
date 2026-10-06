"""Offline structural checks, not validation of natural-language gold labels."""
import json
from collections import Counter, defaultdict
from pathlib import Path

from build_pilot import LABELS, ORDERS, canon, digest, make_body
from analyze_pilot import effect_record

ROOT = Path(__file__).resolve().parent


def main():
    visible = json.loads((ROOT/'data/visible.json').read_text(encoding='utf-8'))
    refs = json.loads((ROOT/'data/references.json').read_text(encoding='utf-8'))
    jobs = [json.loads(x) for x in (ROOT/'plans/jev.jsonl').read_text(encoding='utf-8').splitlines()]
    states = {x['item_id']:x['model_input'] for x in visible}
    assert len(states)==len(visible)==len(refs)==72
    assert set(states)=={r['item_id'] for r in refs}
    assert Counter(r['label'] for r in refs)=={label:24 for label in LABELS}
    assert Counter(r['stratum'] for r in refs)=={'clear_authorization':48,'explicit_deferral':12,'unresolved_reference':12}
    grouped = defaultdict(list)
    oracle_worlds = 0
    for r in refs:
        s=states[r['item_id']]
        grouped[r['parent_id']].append((r,s))
        assert set(s)=={'dialogue','existing_operation'}
        assert set(s['existing_operation'])=={'handle','payload','status','receipt','elapsed_since_request'}
        for committed in r['hidden_committed_worlds']:
            result=effect_record(s,r,r['label'],committed)
            assert result['scope_and_effect_success']
            if r['label']=='CLARIFY':
                assert result['write_attempts']==0 and result['effects_added']==0
            else:
                assert result['missing_original']==result['missing_additional']==result['extra_effects']==0
            oracle_worlds+=1
    assert len(grouped)==12 and oracle_worlds==90
    for group in grouped.values():
        assert len(group)==6
        assert Counter(r['label'] for r,s in group)=={label:2 for label in LABELS}
        assert len({canon(s['dialogue'][:-1]) for r,s in group})==1
        assert len({canon(s['existing_operation']) for r,s in group})==1
    primary=[j for j in jobs if j['phase']=='primary']
    assert len(primary)==144 and len(jobs)==147
    assert len({j['job_id'] for j in jobs})==147
    by_item=defaultdict(list)
    for j in primary:
        assert j['body']==make_body(states[j['item_id']],j['option_order'])
        assert j['request_sha256']==digest(j['body'])
        assert j['planned_input_units']==len(canon(j['body']).encode())+256
        assert j['smoke_reference'] is None
        by_item[j['item_id']].append(j['option_order'])
    for orders in by_item.values():
        assert sorted(orders)==sorted(ORDERS)
    # Score logical cases known by construction, rather than only replaying gold.
    additional=next(r for r in refs if r['label']=='START_ADDITIONAL' and r['history']=='timeout')
    for world in (False,True):
        wrong=effect_record(states[additional['item_id']],additional,'RESUME_EXISTING',world)
        assert wrong['missing_original']==0 and wrong['missing_additional']==1 and wrong['false_merge_decision']
    resume=next(r for r in refs if r['label']=='RESUME_EXISTING')
    wrong=effect_record(states[resume['item_id']],resume,'START_ADDITIONAL',True)
    assert wrong['extra_effects']==1 and not wrong['scope_and_effect_success']
    print(json.dumps({'structural_checks':'passed','visible':72,'parents':12,'primary_requests':144,
                      'reference_assisted_worlds':oracle_worlds,'human_label_validation':False,'model_calls':0}))


if __name__=='__main__':
    main()
