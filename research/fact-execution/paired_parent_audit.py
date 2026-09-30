"""Recompute the saved N1 whole-state versus line-wise parent contrasts."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD_PATH = HERE / 'results' / 'decisions.jsonl'
LINE_PATH = HERE / 'line_results' / 'v0.1' / 'decisions.jsonl'
OLD_SUMMARY = HERE / 'results' / 'summary.json'
LINE_SUMMARY = HERE / 'line_results' / 'v0.1' / 'summary.json'
REPORT = HERE / 'PARENT_PAIRED_AUDIT.md'


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()
            if line.strip()]


def selected(records, method):
    picked = [row for row in records if row.get('arm') == 'N1'
              and row.get('method') == method]
    if len(picked) != 72:
        raise ValueError(f'Expected 72 N1 {method} decisions')
    return indexed(picked)


def indexed(records):
    by_id = {row['source_id']: row for row in records}
    if len(records) != 72 or len(by_id) != 72:
        raise ValueError('Expected 72 unique source IDs')
    for row in records:
        if row['correct'] is not (row['prediction'] == row['gold']):
            raise ValueError('Saved correctness disagrees with decision')
    return by_id


def measures(records):
    return {
        'correct': sum(row['correct'] for row in records),
        'determined_correct': sum(row['correct'] for row in records
                                  if row['gold'] != 'INSUFFICIENT'),
        'false_commitments': sum(row['gold'] == 'INSUFFICIENT' and
                                 row['prediction'] != 'INSUFFICIENT'
                                 for row in records),
    }


def audit():
    old = selected(rows(OLD_PATH), 'facts_0')
    line = indexed(rows(LINE_PATH))
    if set(old) != set(line):
        raise ValueError('The compared methods do not cover identical IDs')
    groups = defaultdict(list)
    transitions = {'determined': Counter(), 'uncertain': Counter()}
    for source_id in sorted(old):
        before, after = old[source_id], line[source_id]
        if any(before[key] != after[key] for key in
               ('parent', 'family', 'variant', 'gold')):
            raise ValueError(f'Paired input metadata differs: {source_id}')
        groups[before['parent']].append((before, after))
        kind = 'uncertain' if before['gold'] == 'INSUFFICIENT' else 'determined'
        transitions[kind][(before['correct'], after['correct'])] += 1
    if len(groups) != 12:
        raise ValueError('Expected 12 parent groups')
    parent_rows = []
    for parent, pairs in sorted(groups.items()):
        if len(pairs) != 6 or sum(a['gold'] == 'INSUFFICIENT' for a, _ in pairs) != 2:
            raise ValueError(f'Unexpected views for {parent}')
        before = measures([a for a, _ in pairs])
        after = measures([b for _, b in pairs])
        parent_rows.append((parent, before, after))
    before = measures(list(old.values()))
    after = measures(list(line.values()))
    old_summary = json.loads(OLD_SUMMARY.read_text(encoding='utf-8'))
    line_summary = json.loads(LINE_SUMMARY.read_text(encoding='utf-8'))
    old_saved = old_summary['methods']['N1']['facts_0']['all']
    for key, value in (('correct', before['correct']),
                       ('false_commitments', before['false_commitments'])):
        if old_saved[key] != value:
            raise ValueError(f'Whole-state summary mismatch: {key}')
    for key, value in (('correct_decisions', after['correct']),
                       ('determined_correct', after['determined_correct']),
                       ('false_commitments', after['false_commitments'])):
        if line_summary[key] != value:
            raise ValueError(f'Line summary mismatch: {key}')
    if before != {'correct': 44, 'determined_correct': 34,
                  'false_commitments': 14} or after != {
                      'correct': 29, 'determined_correct': 11,
                      'false_commitments': 6}:
        raise ValueError('Published headline counts drifted')
    route = [(before, line[source_id]) for source_id, before in old.items()
             if before['family'] == 'route_lookup' and
             before['gold'] != 'INSUFFICIENT']
    diagnostics = {
        'route_determined': len(route),
        'route_old_correct': sum(before['correct'] for before, _ in route),
        'route_line_correct': sum(after['correct'] for _, after in route),
        'line_false_insufficient': sum(row['gold'] != 'INSUFFICIENT' and
                                       row['prediction'] == 'INSUFFICIENT'
                                       for row in line.values()),
        'conflict_views': sum(row['variant'] == 'conflict'
                              for row in line.values()),
        'conflict_correct': sum(row['variant'] == 'conflict' and row['correct']
                                for row in line.values()),
    }
    if diagnostics != {'route_determined': 16, 'route_old_correct': 13,
                       'route_line_correct': 0, 'line_false_insufficient': 37,
                       'conflict_views': 12, 'conflict_correct': 12}:
        raise ValueError('Diagnostic outcome counts drifted')
    if line_summary['false_insufficient'] != diagnostics['line_false_insufficient']:
        raise ValueError('Line false-INSUFFICIENT summary mismatch')
    return parent_rows, transitions, old_saved, line_summary, diagnostics


def comparisons(parent_rows, key, lower_is_better=False):
    changes = [after[key] - before[key] for _, before, after in parent_rows]
    if lower_is_better:
        changes = [-value for value in changes]
    return (sum(value > 0 for value in changes),
            sum(value < 0 for value in changes),
            sum(value == 0 for value in changes))


def report():
    parent_rows, transitions, old_saved, line_saved, diagnostics = audit()
    det = transitions['determined']
    uncertain = transitions['uncertain']
    lines = [
        '# Parent-paired audit: safer abstention, lost determined decisions',
        '',
        'This is a **derived, post-hoc description** of the same 72 public',
        'original-development texts. It adds zero model calls and zero human',
        'annotations. Both methods use the historical pinned Kev-LoRA N1/native',
        'path, but different prompts and budgets. The 12 six-view parents are',
        'the paired units; 72 views and 548 line queries are not independent',
        'research samples.',
        '',
        '|Saved method|Correct /72|Determined correct /48|False commitments /24 uncertain|Forwards|Input tokens|',
        '|---|---:|---:|---:|---:|---:|',
        f"|Whole-state facts + code|44|34|14|{old_saved['model_calls']}|{old_saved['input_tokens']:,}|",
        f"|Line-by-line facts + code|29|11|6|{line_saved['model_calls']}|{line_saved['input_tokens']:,}|",
        '',
        '## Matched views within each parent',
        '',
        'Each cell reads **whole-state → line-by-line**. Every parent has four',
        'determined and two uncertain views. Smaller false-commitment counts are',
        'better; larger correct counts are better.',
        '',
        '|Parent|Correct /6|Determined correct /4|False commitments /2|',
        '|---|---:|---:|---:|',
    ]
    for parent, before, after in parent_rows:
        lines.append('|{}|{} → {}|{} → {}|{} → {}|'.format(
            parent, before['correct'], after['correct'],
            before['determined_correct'], after['determined_correct'],
            before['false_commitments'], after['false_commitments']))
    overall = comparisons(parent_rows, 'correct')
    determined = comparisons(parent_rows, 'determined_correct')
    fewer = comparisons(parent_rows, 'false_commitments', lower_is_better=True)
    lines.extend([
        '',
        'At the parent level, overall correctness improved / worsened / tied in',
        f'**{overall[0]} / {overall[1]} / {overall[2]}** groups. Determined correctness',
        f'improved / worsened / tied in **{determined[0]} / {determined[1]} / {determined[2]}**.',
        'False commitments decreased / increased / tied in',
        f'**{fewer[0]} / {fewer[1]} / {fewer[2]}**.',
        '',
        'On the 48 determined views, the old method was correct and the line',
        f'method wrong on **{det[(True, False)]}**; the reverse occurred on',
        f'**{det[(False, True)]}**. Both were correct on **{det[(True, True)]}**',
        f'and both wrong on **{det[(False, False)]}**. On the 24 uncertain views,',
        f'the line method repaired **{uncertain[(False, True)]}** old errors and',
        f'created **{uncertain[(True, False)]}** new ones. This is a real',
        'abstention tradeoff on these saved decisions, not a single-parent artifact.',
        '',
        f"The line method correctly chose all {diagnostics['conflict_views']} conflict views but chose",
        f"INSUFFICIENT on {diagnostics['line_false_insufficient']} determined views. In the route-lookup family it",
        f"got **{diagnostics['route_line_correct']}/{diagnostics['route_determined']} determined** views right versus **{diagnostics['route_old_correct']}/{diagnostics['route_determined']}** for whole-state",
        'facts + code. The mechanism remains a hypothesis: these outcome counts',
        'do not reveal why the model selected a line or field.',
        '',
        'There is no p-value or population confidence interval here. The',
        'parents were synthetically constructed and repeatedly inspected during',
        'development; the line method was designed after prior results. Calls',
        'and input-token budgets differ substantially, and no Jev or held-out',
        'ShARC result enters this audit. The prewritten line-method screening',
        'rule remains failed; parent pairing sharpens that negative finding',
        'without turning it into a generalization claim.',
        '',
        '## Source integrity',
        '',
        'The script requires matching IDs, parent/family/variant/gold fields,',
        'one record per method and view, six views per parent, and agreement',
        'with both saved summaries. LF-normalized SHA-256 of the two decision',
        'files:',
        '',
        f'- Whole-state decisions: `{digest(OLD_PATH)}`',
        f'- Line-by-line decisions: `{digest(LINE_PATH)}`',
        '',
        'Recompute the report without models, credentials, or writes:',
        '',
        '```bash',
        'python research/fact-execution/paired_parent_audit.py verify',
        '```',
        '',
    ])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    args = parser.parse_args()
    expected = report()
    if args.command == 'build' and not REPORT.exists():
        REPORT.write_text(expected, encoding='utf-8', newline='\n')
    if REPORT.read_bytes().replace(b'\r\n', b'\n') != expected.encode('utf-8'):
        raise ValueError('Parent-paired report differs from saved decisions')
    print(json.dumps({'status': 'passed', 'paired_parents': 12,
                      'model_forwards_added': 0, 'report': str(REPORT)}))


if __name__ == '__main__':
    main()
