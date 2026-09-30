"""Build a zero-model specification lab and its finite verification record."""
import argparse
import hashlib
import json
from pathlib import Path
from semantics import evaluate, ContractError
from examples import cases, invalid_cases
from audit import exhaustive

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


def payload():
    valid = []
    for case in cases():
        answer = evaluate(case['contract'])
        assert all(answer[k] == value for k, value in case['expected'].items()), case['case_id']
        valid.append({**case, 'result': answer})
    invalid = []
    for case in invalid_cases():
        try:
            evaluate(case['contract'])
        except ContractError as error:
            invalid.append({**case, 'error': str(error)})
        else:
            raise AssertionError('Invalid example accepted: ' + case['case_id'])
    return {'status': 'Specification prototype, not model evidence', 'model_calls': 0,
            'human_annotations': 0, 'authored_examples': valid, 'invalid_contract_examples': invalid,
            'finite_audit': exhaustive(),
            'source_sha256_lf': {name: hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                                 for name in ('semantics.py', 'examples.py', 'audit.py', 'CONTRACT.md')}}


def report(data):
    audit = data['finite_audit']
    lines = ['# Unknown order. Known answer?', '',
        '**Executable specification lab: zero model calls, zero independent human reviews.**', '',
        'Can a refund-destination restriction be determined before identifying exactly which order a user means? '
        'Sometimes, under a predicate-only contract. That still does not authorize a refund. '
        'This lab makes the distinction executable without changing the old experiments.', '',
        '[Interactive examples](https://yuchi-wang02.github.io/jev-scope-challenge/decision_sufficiency.html) · '
        '[Contract and projection argument](CONTRACT.md) · [Prior work and reuse](RELATED_WORK.md)', '',
        '## What ran', '',
        f'- {len(data["authored_examples"])} authored specification examples plus {len(data["invalid_contract_examples"])} malformed/inconsistent input examples.',
        f'- Independent complete-database enumeration agreed with the projection on {audit["valid_contracts_checked"]} finite contracts; '
        f'{audit["inconsistent_contracts_rejected"]} inconsistent contracts were rejected.',
        f'- {audit["contracts_where_interfaces_differ"]} of those constructed contracts distinguish predicate-only and identity-required outputs. '
        'This is a software test count, not empirical accuracy or a prevalence estimate.',
        '- Brute-force scope: two ordinary original methods, at most two visible and two omitted records, '
        'product/exact-ID selection, gift-card, ordinary, absent and unresolved destinations.',
        '- No Jev request, local model inference, model download, new human annotation, or live refund operation.', '',
        '## Inspect the contrast', '',
        '|Example|Predicate only|Unique target required|Why|', '|---|---|---|---|']
    for case in data['authored_examples']:
        r = case['result']
        lines.append(f'|{case["case_id"]}: {case["title"]}|{r["predicate_only"]}|{r["unique_target_required"]}|{case["explanation"]}|')
    lines += ['', '## Reproduce', '', 'From the repository root, using Python 3.10 or newer; only the standard library is needed:', '',
        '```powershell', 'python research/decision-sufficiency/build.py --verify',
        'python research/decision-sufficiency/semantics.py research/decision-sufficiency/example_contract.json',
        'python -m unittest discover -s tests -p test_decision_sufficiency.py -v', '```', '',
        'The CLI accepts one contract JSON object and returns both interpretations, the possible outcomes '
        'and concrete projected witnesses. An invalid contract exits with code 2 and does not invent a decision label. '
        'Use `build.py` without `--verify` to regenerate the checked artifacts.', '',
        '## Stage decision', '',
        'This branch has value as a task-definition and software-control example. Possible-world consensus, '
        'certain answers and query-scoped completeness have direct prior literature; they are not our inventions. '
        'The finite schema already has a complete program solution. Do not launch a new model leaderboard on '
        'these examples or present the audit as benchmark evidence.', '',
        'A next study requires a concrete user need for the predicate-only interface, independently reviewed '
        'language and an available capable ordinary-model comparator. If the actual operation always needs '
        'unique identity, keep this as documentation and continue the existing coverage-review path. '
        'Model experiments on the earlier 72 inputs remain closed. The current review package is '
        '[here](../candidate-completeness/review/README.md).', '',
        'All objects are artificial; domains and coverage assertions are provided by construction. '
        'They are not a deployed retrieval contract, real customer data, tau benchmark examples, or human-validated labels. '
        'The schema does not model split payments or full return policy. '
        'A machine-checked contract cannot certify its supplied facts.', '']
    return '\n'.join(lines)


def build(verify=False):
    data = payload()
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    files = {ROOT/'audit.json': json.dumps(data, indent=2, ensure_ascii=False)+'\n',
             ROOT/'example_contract.json': json.dumps(data['authored_examples'][5]['contract'], indent=2)+'\n',
             ROOT/'README.md': report(data),
             REPO/'docs/decision_sufficiency.html': (ROOT/'lab_template.html').read_text(encoding='utf-8').replace('__DATA__', encoded)}
    for path, text in files.items():
        if verify:
            assert path.read_text(encoding='utf-8') == text, str(path)
        else:
            path.write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps(data['finite_audit'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--verify', action='store_true')
    build(parser.parse_args().verify)
