"""Publish the completed frozen joint pilot, its controls and every saved query."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from data_tools import HERE, original_cases
from gap_analyze import equal
from joint_analyze import analyze, score_method
from joint_execution import OUT
from line_evidence import visible_lines
from verify_gap import text_reference

ROOT = HERE.parents[1]
TEMPLATE = HERE / 'joint_explorer_template.html'
PAGES = (HERE / 'docs/joint_explorer.html', ROOT / 'docs/joint_route.html')
REPORT = HERE / 'JOINT_RESULTS.md'
FIGURE_DATA = HERE / 'assets/joint_figure_data.json'
METHODS = ('direct_single', 'direct_call_matched', 'direct_token_matched', 'joint')
NAMES = {'direct_single': 'Direct: one call',
         'direct_call_matched': 'Direct: call-matched',
         'direct_token_matched': 'Direct: input-token-matched',
         'joint': 'Joint route + code',
         'always_defer': 'Always defer: offline control',
         'known_grammar': 'Known grammar: offline control'}


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()
            if line.strip()]


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def controls(cases):
    """Predict from visible inputs only; construction labels grade afterwards."""
    result = {}
    for name in ('always_defer', 'known_grammar'):
        decisions = []
        for case in cases:
            prediction = ('INSUFFICIENT' if name == 'always_defer' else
                          text_reference(case['state'], case['instruction']))
            decisions.append({'method': name, 'source_id': case['id'],
                              'parent': case['parent'], 'variant': case['variant'],
                              'gold': case['gold'], 'prediction': prediction,
                              'correct': prediction == case['gold'],
                              'model_calls': 0, 'input_tokens': 0,
                              'summed_forward_latency_s': 0})
        result[name] = score_method(name, decisions)
        result[name]['summed_forward_latency_s'] = None
    return result


def payload():
    summary, decisions, claims, audits = analyze()
    for name, fresh in (('summary.json', summary), ('decisions.jsonl', decisions),
                        ('fact_claims.jsonl', claims), ('line_audits.jsonl', audits)):
        saved = (json.loads((OUT / name).read_text(encoding='utf-8'))
                 if name.endswith('.json') else rows(OUT / name))
        equal(fresh, saved, name)
    raw = rows(OUT / 'N1.jsonl')
    cases = original_cases()
    methods = dict(summary['methods']) | controls(cases)
    expected = {'direct_single': (31, 23, 30, 5, 13, 72, 23523),
                'direct_call_matched': (31, 23, 30, 5, 13, 228, 76855),
                'direct_token_matched': (31, 23, 30, 5, 13, 286, 95849),
                'joint': (34, 11, 21, 27, 0, 228, 95889),
                'always_defer': (24, 0, 0, 48, 0, 0, 0),
                'known_grammar': (72, 0, 48, 0, 0, 0, 0)}
    keys = ('correct_decisions', 'false_commitments', 'determined_correct',
            'false_insufficient', 'wrong_supported_actions', 'model_calls', 'input_tokens')
    if {name: tuple(m[k] for k in keys) for name, m in methods.items()} != expected:
        raise ValueError('Joint publication headline or control drift')
    scope = {}
    for name, predicate in (('target', lambda r: r['construction_reference_route'] != 'OTHER_REQUEST'),
                            ('other_request', lambda r: r['construction_reference_route'] == 'OTHER_REQUEST')):
        selected = [row for row in audits if predicate(row)]
        scope[name] = {'lines': len(selected),
                       'correct_routes': sum(row['program_audit'] == 'correct_route' for row in selected),
                       'errors': dict(sorted(Counter(row['program_audit'] for row in selected
                                                   if row['program_audit'] != 'correct_route').items()))}
    if scope != {'target': {'lines': 162, 'correct_routes': 160, 'errors': {'wrong_field': 2}},
                 'other_request': {'lines': 66, 'correct_routes': 6, 'errors': {'wrong_request': 60}}}:
        raise ValueError('Request-scope denominator drift')
    # Exact historical input/output anchor, checked without calling either model.
    old = {r['source_id']: r for r in rows(HERE / 'results/N1.jsonl')
           if r['kind'] == 'direct' and r['mapping'] == 0}
    new = [r for r in raw if r['arm'] == 'direct' and r['mapping'] == 0]
    anchor = {'queries': len(new), 'identical_encoded_inputs': 0,
              'prediction_differences': 0, 'max_abs_logit_delta': 0.0,
              'max_abs_candidate_probability_delta': 0.0}
    if len(new) != 72 or len(old) != 72:
        raise ValueError('Historical direct anchor grid drift')
    for row in new:
        before = old[row['source_id']]
        anchor['identical_encoded_inputs'] += all(row[k] == before[k] for k in
                                                 ('prompt', 'token_ids', 'candidate_ids', 'order'))
        anchor['prediction_differences'] += row['prediction'] != before['prediction']
        anchor['max_abs_logit_delta'] = max(anchor['max_abs_logit_delta'],
                                          *(abs(x - y) for x, y in zip(row['logits'], before['logits'])))
        anchor['max_abs_candidate_probability_delta'] = max(
            anchor['max_abs_candidate_probability_delta'],
            *(abs(x - y) for x, y in zip(row['probabilities'], before['probabilities'])))
    if anchor != {'queries': 72, 'identical_encoded_inputs': 72,
                   'prediction_differences': 0, 'max_abs_logit_delta': 0.0,
                   'max_abs_candidate_probability_delta': 0.0}:
        raise ValueError('Historical direct anchor no longer reproduces exactly')
    lookup = {(r['method'], r['source_id']): r for r in decisions}
    parents = []
    paired = Counter()
    for case in cases:
        before, after = lookup['direct_call_matched', case['id']], lookup['joint', case['id']]
        paired[('correct' if before['correct'] else 'wrong',
                'correct' if after['correct'] else 'wrong')] += 1
    for parent in sorted({case['parent'] for case in cases}):
        ids = [case['id'] for case in cases if case['parent'] == parent]
        parents.append({'parent': parent, 'views': len(ids),
                        'direct_correct': sum(lookup['direct_call_matched', i]['correct'] for i in ids),
                        'joint_correct': sum(lookup['joint', i]['correct'] for i in ids)})
    if (paired != {('correct', 'wrong'): 17, ('wrong', 'correct'): 20,
                   ('correct', 'correct'): 14, ('wrong', 'wrong'): 21} or
            Counter((p['joint_correct'] > p['direct_correct']) -
                    (p['joint_correct'] < p['direct_correct']) for p in parents) !=
            {-1: 4, 0: 4, 1: 4}):
        raise ValueError('Paired comparison headline drift')
    if (sum(lookup['direct_call_matched', c['id']]['prediction'] !=
            lookup['direct_token_matched', c['id']]['prediction'] for c in cases) != 0 or
            sum(lookup['direct_single', c['id']]['prediction'] !=
                lookup['direct_call_matched', c['id']]['prediction'] for c in cases) != 3):
        raise ValueError('Shared direct-control predictions drifted')
    if (summary['joint_correct_fields'], summary['joint_exact_fact_vectors'],
            summary['joint_missing_as_reported_value'], summary['joint_missed_conflicts']) != (130, 34, 11, 0):
        raise ValueError('Field-status headline drift')
    case_rows = []
    # Omit repeated token ID arrays from the viewer; exact arrays remain in raw JSONL.
    raw_keys = ('query_id', 'arm', 'mapping', 'order', 'prediction', 'logits',
                'probabilities', 'candidate_mass', 'input_tokens', 'latency_s', 'prompt')
    for case in cases:
        source_id = case['id']
        case_audits = [r for r in audits if r['source_id'] == source_id]
        if [r['evidence_span']['text'] for r in case_audits] != [
                line['text'] for line in visible_lines(case['state'])]:
            raise ValueError('Explorer visible line/audit alignment drift')
        case_rows.append({'id': source_id, 'parent': case['parent'],
                          'family': case['family'], 'variant': case['variant'],
                          'state': case['state'], 'policy': case['instruction'], 'gold': case['gold'],
                          'decisions': {m: lookup[m, source_id] for m in METHODS},
                          'fields': [r for r in claims if r['source_id'] == source_id],
                          'lines': case_audits,
                          'queries': [{k: r[k] for k in raw_keys} for r in raw
                                      if r['source_id'] == source_id]})
    if len(case_rows) != 72 or sum(len(c['queries']) for c in case_rows) != 514:
        raise ValueError('Explorer lost a scored case or saved query')
    return {'status': summary['status'], 'summary': summary, 'methods': methods,
            'method_order': list(METHODS) + ['always_defer', 'known_grammar'],
            'names': NAMES, 'scope': scope, 'anchor': anchor,
            'paired_transitions': {'correct_to_wrong': paired['correct', 'wrong'],
                                   'wrong_to_correct': paired['wrong', 'correct'],
                                   'correct_to_correct': paired['correct', 'correct'],
                                   'wrong_to_wrong': paired['wrong', 'wrong']},
            'parents': parents, 'cases': case_rows,
            'default_case': 'joint_approval-1-full',
            'runtime': json.loads((OUT / 'runtime.json').read_text(encoding='utf-8')),
            'source_sha256_lf': {str(path.relative_to(ROOT)).replace('\\', '/'): digest(path)
                                for path in (OUT / 'N1.jsonl', OUT / 'runtime.json',
                                             HERE / 'data/original_cases.jsonl',
                                             HERE / 'preparation/joint_execution_manifest.json')},
            'publisher_model_forwards': 0}


def report(data):
    s, r = data['summary'], data['runtime']
    lines = ['# Joint routing results and request scope errors', '',
             '**The frozen joint-routing candidate failed both parts of its development screen.**',
             'It reached 34/72 correct decisions, 11/24 false commitments and 21/48 correct',
             'determined decisions. The fixed direct controls each reached 31/72. Joint routing',
             'correctly labeled 160/162 target-request lines, but turned 60/66 other-request',
             'lines into target-field evidence. These are the same 72 public synthetic',
             'development views in 12 parent groups, with program-derived labels and zero',
             'independent human annotations. This is not a new Jev measurement.', '',
             '![Decision outcomes and separate request-scope denominators](assets/joint-routing.png)', '',
             '## Every fixed method and the offline controls', '',
             '|Path|Correct /72|False commitments /24|Determined correct /48|Needless deferrals /48|Wrong determined actions /48|Complete parents /12|Calls|Input tokens|Summed forward seconds|',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name in data['method_order']:
        m = data['methods'][name]
        values = [NAMES[name]] + [m[k] for k in ('correct_decisions', 'false_commitments',
                  'determined_correct', 'false_insufficient', 'wrong_supported_actions',
                  'complete_parents', 'model_calls', 'input_tokens')]
        values.append('Not measured' if m['summed_forward_latency_s'] is None else
                      f"{m['summed_forward_latency_s']:.2f}")
        lines.append('|' + '|'.join(map(str, values)) + '|')
    lines += ['', 'The two offline controls are recomputed from visible state and policy, then graded;',
              'they are not new model forwards or empirical extraction improvements. The parser',
              'knows the declared grammar. Zero model calls does not mean measured zero CPU time.', '',
              'Call-matched direct uses 228 calls but 19,034 fewer input tokens than joint.',
              'Input-token-matched direct uses 95,849 tokens, 40 fewer than joint, but 58 more calls.',
              'The direct single/call/token rows reuse one 286-query union; do not sum their',
              'deployment call counts to infer experiment size. Actual execution was 228 + 286',
              '= **514 unique scientific forwards**, 191,738 input tokens and two warmups.',
              'The two matched direct methods have identical predictions on all 72 views.',
              'Their 31/72 totals match the single-call total, but the single-call predictions',
              'differ on three views: one correction, one regression and one wrong-to-wrong',
              'action change. Equal totals do not mean every prediction is unchanged.', '',
              '## The gate failed and the error source remains', '',
              'The published screen required at most 7/24 false commitments **and** at least',
              '34/48 correct determined decisions. Joint produced 11 and 21 respectively.',
              'Its unchanged form should not advance to confirmation. Correct field statuses',
              'were 130/168; exact fact vectors were 34/72. It asserted values for 11/18 truly',
              'missing fields. Fourteen TRUE and thirteen FALSE fields became CONFLICT;',
              'all twelve reference CONFLICT fields were retained.', '',
              '|Reference request scope|Lines|Exact route correct|Observed routing errors|',
              '|---|---:|---:|---|',
              '|Target request|162|160|2 wrong-field labels|',
              '|Other request|66|6|60 labels that filled a target field|', '',
              'The 60 wrong-request and two wrong-field labels account for all 62 routing',
              'errors. These are correlated line judgments, not 228 independent examples.',
              'The output pattern identifies a scope error; it does not reveal an internal',
              'model mechanism or establish that more training is necessary.', '',
              'For `joint_approval-1-full`, both target reviewers approve. A different',
              'request has a reviewer B rejection. The model labeled that distractor',
              '`review_b:NEGATIVE`, creating a target B CONFLICT and changing the final',
              'action from the program-reference ALLOW to INSUFFICIENT. This trace uses',
              'the saved selected label and unchanged executor, not a simulated model repair.', '',
              '## Paired comparison at the parent unit', '',
              'Against call-matched direct, joint corrected 20 wrong views but regressed',
              '17 correct views; 14 stayed correct and 21 stayed wrong. Joint had more',
              'correct views in four parent groups, fewer in four and tied in four.',
              'These descriptive counts do not establish statistical significance or',
              'population generalization on a constructed, inspected development corpus.', '',
              '|Parent|Views|Call-matched direct correct|Joint correct|',
              '|---|---:|---:|---:|']
    for parent in data['parents']:
        lines.append('|{parent}|{views}|{direct_correct}|{joint_correct}|'.format(**parent))
    lines += ['', '## Runtime and historical anchor', '',
              f"Execution commit: [`{r['execution_commit']}`](https://github.com/Yuchi-Wang02/jev-scope-challenge/commit/{r['execution_commit']}).",
              f"UTC start: `{r['start_utc']}`. Recorded run duration: {r['elapsed_s']:.2f} seconds;",
              f"peak allocated GPU memory: {r['peak_allocated_mib']:.2f} MiB on an RTX 5070 Ti.",
              'Run duration includes loading and audits; summed table latency measures individual',
              'scientific forwards, not a deployment benchmark. The stack was Python 3.10.18,',
              'torch 2.8.0+cu128, Transformers 4.55.4 and PEFT 0.17.1, BF16/math-only SDPA.',
              'Cached weight hashes and all 504 adapter tensors matched the pinned artifacts.',
              'The existing PEFT warning about newer optional adapter-config fields reappeared;',
              'the exact loaded-tensor checks still passed. No package upgrade was performed.', '',
              'All 72 single-direct prompts, token arrays, candidate arrays and option orders',
              'matched the earlier N1 run. Predictions, logits and conditional candidate',
              'probabilities reproduced exactly, with maximum absolute deltas of zero.',
              'This is a local repeat check, not independent inference replication.', '',
              'No new training, model download, paid API, cloud job, Jev call, rewrite score',
              'or reserved score occurred. This uses the historical upstream Kev LoRA;',
              'no new training does not mean an untrained adapter.', '',
              '## Inspect or reproduce offline', '',
              '[Open the complete saved-query viewer online](https://yuchi-wang02.github.io/jev-scope-challenge/joint_route.html)',
              'or download [the identical standalone copy](docs/joint_explorer.html). It contains',
              'all 72 texts, 228 route decisions, 286 direct judgments and the exact prompts.',
              'Candidate distributions are conditional over the listed answer slots, not',
              'calibrated correctness probabilities; route and direct spaces have different widths.', '',
              'Raw evidence: [forwards](joint_results/v0.1/N1.jsonl),',
              '[decisions](joint_results/v0.1/decisions.jsonl),',
              '[field claims](joint_results/v0.1/fact_claims.jsonl),',
              '[line audits](joint_results/v0.1/line_audits.jsonl),',
              '[summary](joint_results/v0.1/summary.json) and',
              '[runtime](joint_results/v0.1/runtime.json). Use full Git history for source checks.', '',
              '```bash', 'python research/fact-execution/joint_execution.py verify-freeze',
              'python research/fact-execution/joint_analyze.py --verify',
              'python research/fact-execution/publish_joint.py --verify', '```', '',
              'The pre-inference [execution protocol](JOINT_EXECUTION_PROTOCOL.md) and its source',
              'hashes stay unchanged. This report and viewer were created after the run.',
              'The separate [multi-fact line stress](MULTIFACT_LINE_STRESS.md) remains software-only;',
              'this run scored no packed line, so it does not address that interface limit.',
              'Further scope tests or nonexclusive extraction need a new frozen protocol and',
              'independently reviewed language variation. See [upstream credits](../../THIRD_PARTY_NOTICES.md).', '']
    return '\n'.join(lines)


def figure_data(data):
    return {'status': 'post_hoc_original_development_only', 'views': 72, 'parents': 12,
            'independent_human_annotations': 0,
            'outcomes': [{'name': NAMES[name], 'correct': m['correct_decisions'],
                          'wrong_actions': m['false_commitments'] + m['wrong_supported_actions'],
                          'needless_deferrals': m['false_insufficient'],
                          'calls': m['model_calls'], 'tokens': m['input_tokens']}
                         for name in data['method_order'] for m in [data['methods'][name]]],
            'scope': data['scope']}


def artifacts():
    data = payload()
    template = TEMPLATE.read_text(encoding='utf-8')
    if template.count('__JOINT_DATA__') != 1:
        raise ValueError('Joint explorer data marker drift')
    page = template.replace('__JOINT_DATA__', json.dumps(data, ensure_ascii=False,
                            separators=(',', ':')).replace('<', '\\u003c'))
    return {REPORT: report(data), FIGURE_DATA: json.dumps(figure_data(data), indent=2) + '\n',
            **{path: page for path in PAGES}}


def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from matplotlib.ticker import PercentFormatter
    data = json.loads(FIGURE_DATA.read_text(encoding='utf-8'))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'svg.hashsalt': 'joint-route-v0.1'})
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.7), layout='constrained',
                             gridspec_kw={'width_ratios': [1.55, 1]})
    colors = {'correct': '#376b89', 'wrong_actions': '#b36b43', 'needless_deferrals': '#bfc4c8'}
    for i, row in enumerate(data['outcomes']):
        left = 0
        for key, label in (('correct', 'Correct'), ('wrong_actions', 'Wrong action'),
                           ('needless_deferrals', 'Needless deferral')):
            value = row[key]
            axes[0].barh(i, value, left=left, color=colors[key], height=.6,
                         label=label if i == 0 else None)
            if value:
                axes[0].text(left + value / 2, i, str(value), ha='center', va='center',
                             color='white' if key != 'needless_deferrals' else '#25323c', fontsize=10)
            left += value
        if left != 72:
            raise ValueError('Figure outcomes fail partition')
    axes[0].set(yticks=range(6), yticklabels=[row['name'] for row in data['outcomes']],
                xlim=(0, 72), xlabel='Decisions on the same 72 views',
                title='Decision outcomes across methods and controls')
    axes[0].invert_yaxis()
    axes[0].legend(loc='lower left', bbox_to_anchor=(0, -.27), ncol=3, frameon=False)
    for i, (key, label) in enumerate((('target', 'Target request (162 lines)'),
                                     ('other_request', 'Other request (66 lines)'))):
        row = data['scope'][key]
        correct = row['correct_routes'] / row['lines']
        axes[1].barh(i, correct, color=colors['correct'], height=.45)
        axes[1].barh(i, 1 - correct, left=correct, color=colors['wrong_actions'], height=.45)
        axes[1].text(.5, i + .36, f"{row['correct_routes']}/{row['lines']} exact routes correct",
                     ha='center', va='center', fontsize=10)
    axes[1].set(yticks=[0, 1], yticklabels=['Target', 'Other request'], xlim=(0, 1),
                ylim=(-.6, 1.65), xlabel='Share of routes within each scope',
                title='Joint routing: request scope matters')
    axes[1].invert_yaxis()
    axes[1].xaxis.set_major_formatter(PercentFormatter(1))
    axes[1].legend(handles=[Patch(color=colors['correct'], label='Exact route'),
                            Patch(color=colors['wrong_actions'], label='Route error')],
                   loc='lower left', bbox_to_anchor=(0, -.27), ncol=2, frameon=False)
    for ax in axes:
        ax.grid(axis='x', alpha=.15)
        ax.set_axisbelow(True)
    fig.suptitle('Joint routing: 60 of 66 distractor lines became target evidence',
                 fontsize=18, fontweight='bold')
    fig.text(.5, -.045, 'Historical Kev-LoRA N1 · 12 constructed parents · program labels · no independent human review\n'
             '514 unique forwards + 2 warmups; shared direct subsets are not extra samples · both screening conditions failed',
             ha='center', fontsize=10)
    for ext in ('png', 'svg'):
        path = HERE / f'assets/joint-routing.{ext}'
        fig.savefig(path, dpi=170, bbox_inches='tight',
                    metadata={'Creator': 'Matplotlib', 'Date': None} if ext == 'svg' else None)
        if ext == 'svg':
            # Matplotlib path lines contain trailing spaces; keep the source tidy.
            path.write_bytes(('\n'.join(line.rstrip() for line in
                                       path.read_text(encoding='utf-8').splitlines()) + '\n').encode('utf-8'))
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--figure', action='store_true')
    args = parser.parse_args()
    if args.verify and args.figure:
        parser.error('Read-only verification cannot regenerate figures')
    for path, value in artifacts().items():
        content = value.encode('utf-8')
        if args.verify:
            if path.read_bytes().replace(b'\r\n', b'\n') != content:
                raise ValueError('Joint publication drift: ' + str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if args.figure:
        figures()
    print(json.dumps({'status': 'verified' if args.verify else 'published',
                      'views': 72, 'saved_forwards': 514, 'publisher_model_forwards': 0}))


if __name__ == '__main__':
    main()
