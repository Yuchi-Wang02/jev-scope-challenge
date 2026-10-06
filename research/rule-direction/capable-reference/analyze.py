"""Offline report from the immutable prompts, original references and real journal."""
from __future__ import annotations

import argparse
from collections import Counter
import json

import prepare
import runner


def summarize(observations):
    main = [o for o in observations if o['phase'] == 'main']
    mappings = {}
    for mapping in (0, 1):
        rows = [o for o in main if o['mapping'] == mapping]
        by_id = {o['item_id']: o for o in rows}
        cells = {}
        for relation in ('sufficient', 'necessary', 'equivalent'):
            cells[relation] = {}
            for fact in ('positive', 'negative', 'unknown'):
                cell = [o for o in rows if o['relation'] == relation and o['fact_state'] == fact]
                cells[relation][fact] = {'correct': sum(o['correct'] for o in cell),
                    'planned_denominator': len(cell), 'executed': sum(o['executed'] for o in cell),
                    'actions': dict(Counter(str(o['label']) for o in cell if o['executed']))}
        pairs = {fact: sum(all(by_id[f'r{n:02d}_{rel}_{fact}']['correct']
            for rel in ('sufficient', 'necessary')) for n in range(1, 13))
            for fact in ('positive', 'negative')}
        families = [f'r{n:02d}' for n in range(1, 13)]
        old_error_cells = {('sufficient', 'negative'), ('necessary', 'positive')}
        old_errors = [o for o in rows if (o['relation'], o['fact_state']) in old_error_cells]
        controls = [o for o in rows if (o['relation'], o['fact_state']) not in old_error_cells]
        mappings[str(mapping)] = {'correct': sum(o['correct'] for o in rows),
            'planned_denominator': 108, 'executed': sum(o['executed'] for o in rows),
            'invalid': sum(o['executed'] and o['label'] is None for o in rows),
            'truncated': sum(o['status'] == 'truncated' for o in rows),
            'refusals': sum(o['status'] == 'refusal' for o in rows), 'cells': cells,
            'old_shared_error_cells': {'planned': 24,
                'resolved': sum(o['correct'] for o in old_errors),
                'valid_wrong': sum(o['label'] is not None and not o['correct'] for o in old_errors),
                'invalid': sum(o['executed'] and o['label'] is None for o in old_errors),
                'unresolved': sum(o['status'] == 'unresolved' for o in old_errors),
                'unrun': sum(o['status'] == 'not_run' for o in old_errors)},
            'previously_correct_controls': {'planned': 84,
                'correct': sum(o['correct'] for o in controls),
                'new_valid_wrong': sum(o['label'] is not None and not o['correct'] for o in controls),
                'invalid': sum(o['executed'] and o['label'] is None for o in controls),
                'unresolved': sum(o['status'] == 'unresolved' for o in controls),
                'unrun': sum(o['status'] == 'not_run' for o in controls)},
            'critical_pairs_correct': pairs, 'critical_pairs_denominator_each': 12,
            'complete_nine_case_families_correct': sum(
                all(o['correct'] for o in rows if o['family_id'] == f) for f in families),
            'complete_biconditional_like_signature_families': sum(
                all(o['label'] == {'positive': 'yes', 'negative': 'no', 'unknown': 'maybe'}[o['fact_state']]
                    for o in rows if o['family_id'] == f) for f in families),
            'always_maybe_control_correct': sum(o['reference'] == 'maybe' for o in rows),
            'unknown_fact_triples_correct': sum(all(by_id[f'{f}_{rel}_unknown']['correct']
                for rel in ('sufficient', 'necessary', 'equivalent')) for f in families),
            'false_commitments': sum(o['reference'] == 'maybe' and o['label'] in ('yes', 'no') for o in rows),
            'false_commitment_reference_denominator': 60,
            'unnecessary_deferrals': sum(o['reference'] != 'maybe' and o['label'] == 'maybe' for o in rows),
            'determined_reference_denominator': 48}
    by_key = {(o['item_id'], o['mapping']): o for o in main}
    ids = sorted({o['item_id'] for o in main})
    both_executed = [i for i in ids if all(by_key[i, m]['executed'] for m in (0, 1))]
    both_valid = [i for i in both_executed if all(by_key[i, m]['label'] is not None for m in (0, 1))]
    return {'mappings': mappings, 'both_mappings_executed': len(both_executed),
        'both_mappings_valid': len(both_valid),
        'mapping_disagreements_among_valid_pairs': sum(by_key[i, 0]['label'] != by_key[i, 1]['label'] for i in both_valid),
        'both_mappings_correct': sum(all(by_key[i, m]['correct'] for m in (0, 1)) for i in ids)}


def build(root=prepare.HERE, old=prepare.OLD):
    requests, estimates, budget = prepare.verify(root, old)
    freeze_hash = prepare.lfhash(root / 'freeze.json')
    journal = root / 'results' / 'journal.jsonl'
    events = runner.read_events(journal)
    approval = root / 'approval.json'
    if events and not approval.exists():
        raise ValueError('Model journal has no corresponding approval artifact')
    state = runner.replay(events, requests['jobs'], estimates, freeze_hash,
                          prepare.lfhash(approval) if approval.exists() else None)
    cases = {c['id']: c for c in prepare.load(old / 'cases.json')}
    source_jobs = {j['id']: j for j in prepare.load(old / 'request_plan.json')['jobs'] if j['backend'] == 'qwen'}
    observations = []
    for job in requests['jobs']:
        result = state['results'].get(job['job_id'])
        observation = result['observation'] if result else None
        case = cases.get(job['item_id'])
        reference = case['reference'] if case else source_jobs[job['job_id']]['expected_smoke_action']
        label = observation['label'] if observation else None
        observations.append({'job_id': job['job_id'], 'item_id': job['item_id'],
            'phase': job['phase'], 'mapping': job['mapping'], 'family_id': job['tree_id'],
            'relation': case['relation'] if case else None, 'fact_state': case['fact_state'] if case else None,
            'reference': reference, 'attempted': job['job_id'] in state['started'],
            'result_received': result is not None, 'executed': result is not None, 'label': label,
            'correct': label == reference,
            'status': observation['status'] if observation else ('unresolved' if job['job_id'] in state['started'] else 'not_run')})
    complete = (len(state['results']) == len(requests['jobs']) and state['active'] is None and not state['halted'])
    phases = {}
    for phase in ('smoke', 'main'):
        results = [state['results'][j['job_id']] for j in requests['jobs']
                   if j['phase'] == phase and j['job_id'] in state['results']]
        usage = [r['observation']['usage'] for r in results if r['observation']['usage'] is not None]
        phases[phase] = {'results': len(results), 'known_usage_results': len(usage),
            'input_tokens': sum(u['input_tokens'] for u in usage),
            'output_tokens': sum(u['output_tokens'] for u in usage),
            'cost_microusd': sum(u['cost_microusd'] for u in usage),
            'summed_latency_seconds': sum(r['raw']['latency_seconds'] for r in results)}
    return {'study': requests['study'], 'complete': complete, 'model': prepare.MODEL,
        'freeze_sha256_lf': freeze_hash, 'journal_sha256_lf': prepare.lfhash(journal) if journal.exists() else None,
        'attempts': len(state['started']), 'terminal_results': len(state['results']),
        'unresolved_start': state['active'], 'halted': state['halted'],
        'unknown_usage_terminal_results': state['unknown_usage'],
        'unresolved_usage_attempts': state['unknown_usage'] + int(state['active'] is not None),
        'planned_budget': budget, 'started_input_reserve_tokens': state['input_reserved'],
        'started_cost_reserve_microusd': state['cost_reserved_microusd'], 'actual_usage_by_phase': phases,
        'smoke_correct': sum(o['correct'] for o in observations if o['phase'] == 'smoke'),
        'smoke_planned_denominator': 6,
        'historical_known_grammar_control': {'correct_per_mapping': 108, 'denominator': 108,
            'source': '../RESULTS.md (covered by old_contracts_sha256_lf)',
            'rerun_in_this_arm': False},
        'scope': {'vocabulary_families': 12, 'shared_logical_patterns': 3,
            'independent_confirmation': False, 'independent_human_reviews': 0,
            'note': 'Original synthetic inputs; repeated mappings and 12 lexical families are not independent task samples. A historical cross-provider capability reference, not matched compute or a general model ranking.'},
        **summarize(observations), 'observations': observations}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('build', 'verify'))
    args = parser.parse_args()
    report = build()
    path = prepare.HERE / 'results' / 'report.json'
    if args.command == 'build':
        if not report['attempts']:
            raise ValueError('No model journal: do not create an apparent model-results artifact')
        prepare.preserve(path, report)
    elif prepare.load(path) != report:
        raise ValueError('Report differs from current immutable journal')
    print(json.dumps({k: report[k] for k in ('complete', 'attempts', 'terminal_results', 'halted')}))
