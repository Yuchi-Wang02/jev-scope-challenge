"""Offline packet integrity and source-fact checks; no model or network access.

Optional --source-dir points to the inspection cache containing retrieval.json
and the exact files listed by sources.json. Nothing is imported from upstream.
This checks preservation and arithmetic, not semantic labels or research value.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(source_dir=None):
    checks = []

    def check(name, condition):
        if not condition:
            raise ValueError(name)
        checks.append(name)

    spec = read(HERE / 'screen_spec.json')
    packet = read(HERE / 'case_packet.json')
    ledger = read(HERE / 'sources.json')
    check('six papers and two research implementation chains',
          len(spec['papers']) == 6 and len(spec['implementations']) == 2)
    check('packet revision matches selection specification',
          packet['source_revision'] == spec['source']['revision'])
    expected_ids = [f'{d}/{i}' for d in ('retail', 'airline') for i in range(3)]
    check('six fixed source tasks without replacement',
          [c['case_id'] for c in packet['cases']] == expected_ids)
    check('four distinct user contexts; independence not claimed',
          len({c['user_context_group'] for c in packet['cases']}) == 4
          and packet['counts'] == {'source_tasks': 6, 'task_families': 2,
              'distinct_user_contexts': 4, 'independent_sample_size_established': False})
    for case in packet['cases']:
        check(f'{case["case_id"]}: visibility and non-evaluation status',
              set(case['visibility']) == {'user_scenario', 'description_and_evaluation_criteria', 'records', 'policy'}
              and case['human_review_status'] == 'not reviewed'
              and case['model_run_status'] == 'not run')
    records = packet['records']
    check('packet record counts',
          {d: {k: len(v) for k, v in r.items()} for d, r in records.items()} == {
              'retail': {'products': 9, 'users': 1, 'orders': 5},
              'airline': {'flights': 29, 'users': 3, 'reservations': 11}})
    for domain, section in [('retail', 'orders'), ('airline', 'reservations')]:
        db = records[domain]
        ids = {rid for user in db['users'].values() for rid in user[section]}
        check(f'{domain}: all selected user records retained', ids == set(db[section]))
        for uid, user in db['users'].items():
            check(f'{domain}/{uid}: record ownership retained',
                  all(db[section][rid]['user_id'] == uid for rid in user[section]))
        for case in [c for c in packet['cases'] if c['case_id'].startswith(domain + '/')]:
            uid = case['user_context_group'].split('/')[1]
            check(f'{case["case_id"]}: exact record pointers',
                  case['record_pointers'] == [f'/{section}/{rid}' for rid in db['users'][uid][section]] + [f'/users/{uid}'])
        if domain == 'retail':
            needed = {it['product_id'] for row in db['orders'].values() for it in row['items']}
            check('all ordered retail products retained', needed <= set(db['products']))
        else:
            needed = {f['flight_number'] for row in db['reservations'].values() for f in row['flights']}
            check('exact related flight objects retained', needed == set(db['flights']))
            check('every reservation flight date exists', all(
                leg['date'] in db['flights'][leg['flight_number']]['dates']
                for row in db['reservations'].values() for leg in row['flights']))

    products = records['retail']['products']
    keyboard = products['1656367028']['variants']

    def matches(backlight):
        return [k for k, v in keyboard.items() if v['options'] == {
            'switch type': 'clicky', 'backlight': backlight, 'size': 'full size'}]

    check('requested keyboard unavailable; accepted fallback available',
          matches('RGB') == ['9025753381'] and not keyboard['9025753381']['available']
          and matches('none') == ['7706410293'] and keyboard['7706410293']['available'])
    thermostat = products['4896585277']['variants']['7747408585']
    check('thermostat source fields; no automatic Home/Assistant synonym validation',
          thermostat['available'] and thermostat['options'] == {'compatibility': 'Google Assistant', 'color': 'black'})
    tshirts = products['9523456873']['variants']
    check('T-shirt availability count', len(tshirts) == 12 and sum(v['available'] for v in tshirts.values()) == 10)
    missing = []
    for case in packet['cases'][:3]:
        for a in case['source_task']['evaluation_criteria']['actions']:
            pid = a['arguments'].get('product_id')
            if pid and pid not in products:
                missing.append({'case': case['case_id'], 'action_id': a['action_id'],
                    'path': f'/products/{pid}', 'kind': 'reference_action_argument_absent_in_pinned_database'})
    check('known reference anomaly preserved', missing == packet['source_anomalies'] == [{
        'case': 'retail/2', 'action_id': '2_1', 'path': '/products/6086499569',
        'kind': 'reference_action_argument_absent_in_pinned_database'}])

    reservations = records['airline']['reservations']
    raj = reservations['Q69X3R']
    elapsed = datetime(2024, 5, 15, 15) - datetime.fromisoformat(raj['created_at'])
    check('Raj fixed-policy-time elapsed arithmetic and target fields',
          elapsed.total_seconds() == 104842 and raj['insurance'] == 'no'
          and raj['cabin'] == 'economy' and (raj['origin'], raj['destination']) == ('PHL', 'LGA'))
    emma = reservations['EHGLP3']
    check('Emma target fields', emma['insurance'] == 'no' and emma['cabin'] == 'basic_economy')
    check('Emma and Raj dated flights available', all(
        records['airline']['flights'][leg['flight_number']]['dates'][leg['date']]['status'] == 'available'
        for row in [emma, raj] for leg in row['flights']))
    noah_ids = records['airline']['users']['noah_muller_9847']['reservations']
    latest = max(noah_ids, key=lambda k: datetime.fromisoformat(reservations[k]['created_at']))
    delayed = [rid for rid in noah_ids if any(
        records['airline']['flights'][leg['flight_number']]['dates'][leg['date']]['status'] == 'delayed'
        for leg in reservations[rid]['flights'])]
    check('Noah latest-created and delayed-trip cues differ',
          latest == 'SDZQKO' and delayed == ['4OG6T3']
          and len(reservations[latest]['passengers']) == 2
          and len(reservations['4OG6T3']['passengers']) == 1)

    traces = read(HERE / 'paper_traces.json')
    check('exactly two declared paper diagnostics',
          [t['id'] for t in traces['traces']] == ['relation_change', 'irrelevant_records']
          and traces['source_revision'] == packet['source_revision'])
    relation, irrelevant = traces['traces']
    variant_copy = deepcopy(packet)
    for op in relation['operations']:
        keys = op['path'].strip('/').split('/')
        parent = variant_copy
        for key in keys[:-1]:
            parent = parent[key]
        check(f'counterfactual precondition: {op["path"]}', parent[keys[-1]] is op['before'])
        parent[keys[-1]] = op['after']

    def changed_leaves(a, b, prefix=''):
        if isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
            return [leaf for key in a for leaf in changed_leaves(a[key], b[key], prefix + '/' + key)]
        return [] if a == b else [prefix]

    check('counterfactual changes exactly two declared availability bindings',
          sorted(changed_leaves(packet, variant_copy)) == sorted([
              '/records/retail/products/1656367028/variants/9025753381/available',
              '/records/retail/products/1656367028/variants/6342039236/available']))
    changed_keyboard = variant_copy['records']['retail']['products']['1656367028']['variants']
    check('available/unavailable marginals unchanged',
          sorted(v['available'] for v in keyboard.values()) == sorted(v['available'] for v in changed_keyboard.values()))

    def choose_variant(variants):
        # Conditional on already understood preferences; not a language parser.
        for backlight in ['RGB', 'none']:
            ids = [key for key, value in variants.items() if value['available'] and value['options'] == {
                'switch type': 'clicky', 'backlight': backlight, 'size': 'full size'}]
            if len(ids) > 1:
                raise ValueError('Paper trace no longer has unique preferred variant')
            if ids:
                return ids[0]
        return None

    check('native complete-object selection changes with the relation',
          choose_variant(keyboard) == relation['conditional_selection_before'] == '7706410293'
          and choose_variant(changed_keyboard) == relation['conditional_selection_after'] == '9025753381')

    def cancellation_grounds(mapping):
        # Limited paper calculation after target resolution. The no-insurance
        # records make covered-reason parsing unnecessary; no full action check.
        target = mapping[irrelevant['target_reservation']]
        if target['insurance'] != 'no':
            raise ValueError('Paper calculation requires separate reason analysis')
        age = (datetime(2024, 5, 15, 15) - datetime.fromisoformat(target['created_at'])).total_seconds()
        statuses = [records['airline']['flights'][leg['flight_number']]['dates'][leg['date']]['status'] for leg in target['flights']]
        return [0 <= age <= 86400, 'cancelled' in statuses, target['cabin'] == 'business', False]

    check('unrelated-record removal preserves bounded cancellation grounds',
          cancellation_grounds(reservations) == irrelevant['ground_presence_before'] == [False] * 4
          and cancellation_grounds({'Q69X3R': raj}) == irrelevant['ground_presence_after'] == [False] * 4)

    for row in ledger['distributed_artifacts']:
        check(f'artifact hash: {row["path"]}', digest(HERE / row['path']) == row['sha256'])
    for name in ['README.md', 'EVIDENCE.md', 'CASES.md', 'COMPLETION_AUDIT.md']:
        text = (HERE / name).read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^\s)]+)\)', text):
            if '://' not in target and not target.startswith('#'):
                check(f'local link: {name} -> {target}', (HERE / target.split('#')[0]).is_file())

    exact_tasks = exact_objects = cache_hashes = 0
    if source_dir is not None:
        for row in ledger['retrievals']:
            if row['status'] == 'downloaded':
                check(f'pinned cache hash: {row["key"]}', digest(source_dir / row['key']) == row['sha256'])
                cache_hashes += 1
        for domain in ['retail', 'airline']:
            base = source_dir / f'tau/data/tau2/domains/{domain}'
            tasks, db = read(base / 'tasks.json'), read(base / 'db.json')
            selected = sorted(tasks, key=lambda x: int(x['id']))[:3]
            cases = [c for c in packet['cases'] if c['case_id'].startswith(domain + '/')]
            check(f'{domain}: original task objects exactly preserved', [c['source_task'] for c in cases] == selected)
            check(f'{domain}: source indices accurate', all(tasks[c['source_task_index']] == c['source_task'] for c in cases))
            exact_tasks += len(cases)
            for section, rows in records[domain].items():
                for key, value in rows.items():
                    check(f'original object: {domain}/{section}/{key}', db[section][key] == value)
                    exact_objects += 1
            check(f'{domain}: policy byte-preserved', (base / 'policy.md').read_bytes() == (HERE / f'{domain}_policy.source.md').read_bytes())
        check('missing reference truly absent in full pinned database',
              '6086499569' not in read(source_dir / 'tau/data/tau2/domains/retail/db.json')['products'])
        check('MIT notice byte-preserved', (source_dir / 'tau/LICENSE').read_bytes() == (HERE / 'TAU_LICENSE').read_bytes())
    return {
        'verified_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'passed', 'check_count': len(checks), 'checks': checks,
        'source_comparison_performed': source_dir is not None,
        'exact_source_tasks_compared': exact_tasks, 'exact_source_objects_compared': exact_objects,
        'pinned_cache_files_hashed': cache_hashes,
        'not_established': ['semantic correctness of user intent or policy interpretation',
            'independent human review', 'sample independence', 'new method novelty',
            'model performance or causal attribution'],
        'verifier_network_calls': 0, 'verifier_model_calls': 0,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.source_dir), indent=2))
