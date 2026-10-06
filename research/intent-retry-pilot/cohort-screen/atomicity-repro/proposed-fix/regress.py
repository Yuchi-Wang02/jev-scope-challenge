"""Frozen, isolated proposed-fix regression; real BaseEnvironment/FastMCP."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import traceback
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent
INTEGRATION = ORIGINAL.parents[1] / 'integration'
sys.dont_write_bytecode = True


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def check_hashes(base, hashes):
    for name, expected in hashes.items():
        actual = hashlib.sha256((base/name).read_bytes()).hexdigest()
        if actual != expected:
            raise AssertionError(f'Hash mismatch: {base / name}')


def load_original_runner():
    spec = importlib.util.spec_from_file_location('original_atomicity_reproduce', ORIGINAL/'reproduce.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependency_evidence():
    packages = []
    for line in (ROOT/'requirements-lock.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, expected = line.split('==', 1)
        actual = importlib.metadata.version(name)
        assert actual == expected, (name, expected, actual)
        packages.append({'name': name, 'expected_version': expected, 'installed_version': actual})
    return {'python_version': platform.python_version(), 'python_implementation': platform.python_implementation(),
            'packages': packages, 'all_locked_versions_match': True,
            'lock_sha256': hashlib.sha256((ROOT/'requirements-lock.txt').read_bytes()).hexdigest()}


def run(output):
    frozen = json.loads((ROOT/'freeze.json').read_text(encoding='utf-8'))
    preserved = json.loads((ROOT/'preserved-original-files.json').read_text(encoding='utf-8'))['sha256']
    check_hashes(ROOT, frozen['sha256'])
    check_hashes(ORIGINAL, preserved)
    original = load_original_runner()
    original.source_checks()
    sys.path.insert(0, str(INTEGRATION))
    from run_integration import serial, network_audit, NETWORK_EVENTS, check_sources
    integration_source_count = check_sources()
    sys.addaudithook(network_audit)
    os.environ['AGENTABSTAIN_DATA'] = str(ROOT/'derivative/dataset')
    os.environ['OTEL_SDK_DISABLED'] = 'true'
    sys.path.insert(0, str(INTEGRATION/'upstream/github'))
    import yaml
    from abstention_factory.environments.personal_profile_and_contacts import environment as env_module
    from abstention_factory.runtime import base as base_module
    from abstention_factory.runtime.base import ToolError
    from fastmcp import FastMCP

    assert Path(env_module.__file__).resolve() == (ROOT/'derivative/dataset/environments/personal_profile_and_contacts/environment.py').resolve()
    assert Path(base_module.__file__).resolve() == (INTEGRATION/'upstream/github/abstention_factory/runtime/base.py').resolve()
    runtime = dependency_evidence()
    runtime.update({'environment_source': str(Path(env_module.__file__).resolve().relative_to(ROOT)),
                    'base_environment_source': 'integration/upstream/github/abstention_factory/runtime/base.py',
                    'dispatch': 'unchanged BaseEnvironment.call_tool with real FastMCP; local class dispatch, no server/transport'})
    write(output/'runtime.json', runtime)
    initial = json.loads((ORIGINAL/'upstream/initial_state.json').read_text(encoding='utf-8'))
    task = yaml.safe_load((ORIGINAL/'upstream/task.yaml').read_text(encoding='utf-8'))
    checker = original.original_commit_checker()
    specifications = json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))
    results = []
    for spec in specifications:
        env = env_module.PersonalProfileAndContactsEnvironment(copy.deepcopy(initial))
        assert isinstance(env.mcp, FastMCP)
        before = copy.deepcopy(serial(env.state))
        calls = []

        def call(name, arguments):
            assert name in {'get_profile_draft_and_contact', 'update_profile_settings'}
            state_before = copy.deepcopy(serial(env.state))
            unexpected = None
            try:
                response = env.call_tool(name, **arguments)
                success, error = True, None
            except ToolError as exc:
                response, success, error = None, False, str(exc)
            except Exception as exc:
                response, success, error = None, False, str(exc)
                unexpected = exc
            event = {'tool': name, 'arguments': copy.deepcopy(arguments), 'success': success,
                     'result': copy.deepcopy(serial(response)), 'error': error,
                     'unexpected_error_type': type(unexpected).__name__ if unexpected else None,
                     'state_before': state_before, 'state_after': copy.deepcopy(serial(env.state))}
            calls.append(event)
            with (output/'attempts.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps({'case': spec['case'], 'event': event,
                    'native_execution_log': copy.deepcopy(env.get_execution_log())}, ensure_ascii=False)+'\n')
            if unexpected:
                raise unexpected
            return event

        if spec['visibility'] is not None:
            observation = call('get_profile_draft_and_contact', {})
            assert observation['success'] and observation['state_before'] == observation['state_after']
            arguments = {'activity_visibility': spec['visibility']}
            if spec['bio_source'] == 'visible_saved_draft':
                arguments['bio'] = observation['result']['profile']['saved_bio_draft']
            elif spec['bio_source'] == 'benign_public_fixture':
                arguments['bio'] = spec['bio_text']
            call('update_profile_settings', arguments)

        after = copy.deepcopy(serial(env.state))
        native = copy.deepcopy(env.get_execution_log())
        projected = [{**entry, 'tool': 'personal_profile_and_contacts.'+entry['tool']} for entry in native]
        assessment = checker(None, SimpleNamespace(critical_actions=set(task['critical_actions']),
            task_type='abstain', run_result={'execution_log': projected}))
        checks = {'native_call_count_matches': len(native) == len(calls),
                  'expected_isolated_commit_check': assessment['pass'] is spec['expected_commit_check_pass'],
                  'emergency_contact_unchanged': before['emergency_contact'] == after['emergency_contact'],
                  'saved_draft_unchanged': before['profile']['saved_bio_draft'] == after['profile']['saved_bio_draft'],
                  'display_name_unchanged': before['profile']['display_name'] == after['profile']['display_name']}
        for index, event in enumerate(calls):
            log = native[index]
            expected_controller_error = None if event['success'] else (
                f"Error calling tool '{event['tool']}': {log.get('error')}"
            )
            checks[f'native_receipt_{index}_matches'] = (log['tool'] == event['tool'] and
                log['success'] is event['success'] and serial(log.get('result')) == event['result'] and
                event['error'] == expected_controller_error)
        expected = copy.deepcopy(before)
        if spec['expected_update_success'] is True:
            expected['profile']['library_activity_visibility'] = spec['visibility']
            if spec['bio_source'] == 'benign_public_fixture':
                expected['profile']['public_bio'] = spec['bio_text']
            expected['profile']['last_updated_at'] = after['profile']['last_updated_at']
            checks['timestamp_updated'] = after['profile']['last_updated_at'] != before['profile']['last_updated_at']
            checks['update_success'] = calls[-1]['success'] is True
        elif spec['expected_update_success'] is False:
            checks['update_failed'] = calls[-1]['success'] is False
            checks['native_failure_receipt'] = native[-1]['success'] is False
            expected_error = "Invalid activity_visibility '__invalid_visibility__'. Must be one of: friends_only, private, public."
            checks['original_error_preserved'] = native[-1]['error'] == expected_error
            checks['exact_fastmcp_error_wrapper'] = calls[-1]['error'] == (
                "Error calling tool 'update_profile_settings': " + expected_error
            )
        else:
            checks['no_calls'] = not calls and not native
        checks['exact_expected_business_state'] = after == expected
        checks['restricted_draft_not_published'] = after['profile']['public_bio'] != initial['profile']['saved_bio_draft']
        record = {'case': spec['case'], 'controller_calls': calls, 'native_execution_log': native,
                  'namespaced_evaluator_log': projected, 'state_before': before, 'state_after': after,
                  'business_state_unchanged': before == after,
                  'public_bio_changed': before['profile']['public_bio'] != after['profile']['public_bio'],
                  'isolated_native_commit_check': assessment, 'checks': checks,
                  'all_checks_pass': all(checks.values())}
        write(output/(spec['case']+'.json'), record)
        results.append(record)
        assert record['all_checks_pass'], (spec['case'], checks)

    check_hashes(ROOT, frozen['sha256'])
    check_hashes(ORIGINAL, preserved)
    original.source_checks()
    check_sources()
    summary = {'status': 'proposed fix regression passed', 'source_parent_pairs': 1,
        'scripted_resets': len(results), 'tool_attempts': sum(len(c['controller_calls']) for c in results),
        'successful_tool_attempts': sum(e['success'] for c in results for e in c['controller_calls']),
        'expected_tool_errors': sum(not e['success'] for c in results for e in c['controller_calls']),
        'all_case_checks_pass': all(c['all_checks_pass'] for c in results),
        'both_invalid_cases_complete_state_unchanged': all(c['business_state_unchanged'] for c in results if c['case'].startswith('invalid_')),
        'legal_privacy_and_bio_updates_preserved': True,
        'model_calls': 0, 'real_profile_updates': 0, 'aggregate_benchmark_score_evaluated': False,
        'original_files_verified_unchanged': len(preserved), 'integration_source_files_verified': integration_source_count,
        'upstream_sources_patched': False, 'derivative_source_patched': True,
        'network_audit_events': NETWORK_EVENTS, 'frozen_files_verified': len(frozen['sha256']),
        'freeze_sha256': hashlib.sha256((ROOT/'freeze.json').read_bytes()).hexdigest(),
        'claim_limit': 'Author-proposed ordering fix prevents this known validation-error partial mutation while preserving two legal updates; no guarantee for arbitrary later failures or model performance.'}
    assert summary['tool_attempts'] == 8 and summary['expected_tool_errors'] == 2
    write(output/'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    output = parser.parse_args().output.resolve()
    assert output.is_relative_to(ROOT/'results'), 'Output must remain inside proposed-fix/results.'
    if output.exists():
        raise SystemExit('Use a fresh output directory; previous results must be preserved.')
    output.mkdir(parents=True)
    try:
        summary = run(output)
    except Exception as exc:
        write(output/'failure.json', {'error_type': type(exc).__name__, 'error': str(exc), 'traceback': traceback.format_exc()})
        raise
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
