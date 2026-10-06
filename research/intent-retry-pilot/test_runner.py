"""Offline contract tests. Synthetic fixtures here are never model results."""
import copy
from contextlib import contextmanager, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

import run_jev as runner


def response(choice='A', probabilities=None, model=runner.MODEL):
    return {'model': model, 'answers': {'decision': {'type': 'choice', 'choice': choice,
        'confidence': 0.8, 'probabilities': probabilities or {'A': .8, 'B': .1, 'C': .1}}},
        'usage': {'input_tokens': 20, 'output_tokens': 8}}


def result(options=runner.LABELS, status=200, choice='A'):
    value = runner.adapt_response(response(choice), status, options)
    return {**value, 'http_status': status, 'latency_s': .01, 'retry_after_s': 0, 'ts_utc': 'synthetic-test'}


class Fixture:
    def __init__(self, root, *, attempt_limit=5, retry_limit=2):
        self.root = Path(root)
        (self.root / 'plans').mkdir()
        (self.root / 'run_jev.py').write_bytes(Path(runner.__file__).read_bytes())
        self.jobs = []
        for i, phase in enumerate(('smoke', 'primary')):
            body = {'model': runner.MODEL, 'state': {'fixture': i}, 'questions': {'decision': {
                'type': 'choice', 'instructions': 'Synthetic fixture',
                'criteria': dict(zip('ABC', runner.LABELS))}}}
            self.jobs.append({'job_id': phase, 'phase': phase, 'item_id': 'item-' + str(i),
                'option_order': list(runner.LABELS), 'body': body,
                'request_sha256': runner.digest(runner.canonical(body).encode()),
                'planned_input_units': len(runner.canonical(body).encode()) + 256,
                'smoke_reference': runner.LABELS[0] if phase == 'smoke' else None})
        self.freeze = {'model': runner.MODEL, 'attempt_limit': attempt_limit, 'retry_limit': retry_limit,
                       'planned_input_limit': 10000}
        self.freeze_files()

    def freeze_files(self):
        plan = self.root / 'plans/jev.jsonl'
        plan.write_text(''.join(runner.canonical(j) + '\n' for j in self.jobs), encoding='utf-8', newline='\n')
        self.freeze['sha256'] = {name: runner.digest((self.root / name).read_bytes())
                                 for name in ('plans/jev.jsonl', 'run_jev.py')}
        (self.root / 'freeze.json').write_text(runner.canonical(self.freeze), encoding='utf-8')

    def factory(self, outputs):
        queue = iter(outputs)
        self.calls = []
        @contextmanager
        def factory():
            def call(job):
                self.calls.append(job['job_id'])
                value = next(queue)
                if isinstance(value, Exception):
                    raise value
                return copy.deepcopy(value)
            yield call
        return factory

    def run(self, phase, outputs):
        with redirect_stdout(io.StringIO()):
            return runner.run(phase, self.root, self.factory(outputs), sleep=lambda seconds: None)


class ResponseTests(unittest.TestCase):
    def test_native_choice_maps_under_permutation(self):
        order = ('CLARIFY', 'START_ADDITIONAL', 'RESUME_EXISTING')
        parsed = runner.adapt_response(response('A'), 200, order)
        self.assertTrue(parsed['ok'])
        self.assertEqual(parsed['prediction'], 'CLARIFY')

    def test_probability_rounding_and_argmax_do_not_rewrite_native_choice(self):
        raw = response('B', {'A': .8, 'B': .1, 'C': .099})
        parsed = runner.adapt_response(raw, 200, runner.LABELS)
        self.assertTrue(parsed['ok'])
        self.assertEqual(parsed['prediction'], 'START_ADDITIONAL')
        self.assertFalse(parsed['metadata_quality']['within_sum_tolerance'])
        self.assertFalse(parsed['metadata_quality']['choice_is_displayed_argmax'])
        self.assertIs(parsed['raw_response'], raw)

    def test_wrong_version_choice_usage_and_mapping(self):
        raws = [response(model='jev-latest'), response('A_extra'), response()]
        raws[-1]['usage']['input_tokens'] = True
        for raw in raws:
            self.assertFalse(runner.adapt_response(raw, 200, runner.LABELS)['ok'])
        with self.assertRaises(ValueError):
            runner.adapt_response(response(), 200, ['CLARIFY'] * 3)

    def test_invalid_probability_metadata_is_visible_without_invented_keys(self):
        raw = response(probabilities={'A_extra': .8, 'B': .1, 'C': .1})
        parsed = runner.adapt_response(raw, 200, runner.LABELS)
        self.assertTrue(parsed['ok'])
        self.assertFalse(parsed['metadata_quality']['probability_keys_valid'])
        self.assertIsNone(parsed['metadata_quality']['raw_sum'])

    def test_json_rejects_duplicate_keys_and_nonfinite_constants(self):
        for raw in ('{"choice":"A","choice":"B"}', '{"probability":NaN}'):
            with self.assertRaises(ValueError):
                runner.decode_json(raw)

    def test_redaction_recurses_and_removes_headers(self):
        key = 'synthetic-private-token'
        raw = {'headers': {'Authorization': key}, 'message': key, 'nested': ['apikey_fixture_123']}
        cleaned = runner.sanitize(raw, key)
        self.assertNotIn(key, runner.canonical(cleaned))
        self.assertNotIn('headers', cleaned)
        self.assertEqual(cleaned['nested'], ['[REDACTED]'])


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture = Fixture(self.temp.name)

    def test_smoke_gate_then_resume_without_reissue(self):
        with self.assertRaisesRegex(RuntimeError, 'smoke_gate'):
            self.fixture.run('primary', [])
        self.assertEqual(self.fixture.calls, [])
        self.fixture.run('smoke', [result()])
        first = self.fixture.run('primary', [result()])
        second = self.fixture.run('primary', [])
        self.assertEqual(first['attempts'], 2)
        self.assertEqual(second['attempts'], 2)
        self.assertEqual(self.fixture.calls, [])

    def test_wrong_smoke_blocks_primary_but_is_preserved(self):
        self.fixture.run('smoke', [result(choice='B')])
        with self.assertRaisesRegex(RuntimeError, 'smoke_gate'):
            self.fixture.run('primary', [])
        rows = runner.read_rows(Path(self.temp.name) / 'results/jev_responses.jsonl')
        self.assertFalse(rows[0]['smoke_correct'])
        self.assertTrue(rows[0]['ok'])

    def test_successful_finish_missing_terminal_recovers_without_request(self):
        self.fixture.run('smoke', [result()])
        path = Path(self.temp.name) / 'results/jev_responses.jsonl'
        saved = path.read_bytes()
        path.unlink()
        summary = self.fixture.run('smoke', [])
        self.assertEqual(path.read_bytes(), saved)
        self.assertEqual(self.fixture.calls, [])
        self.assertEqual(summary['attempts'], 1)

    def test_incomplete_attempt_never_auto_replays(self):
        with self.assertRaisesRegex(RuntimeError, 'synthetic_interruption'):
            self.fixture.run('smoke', [RuntimeError('synthetic_interruption')])
        with self.assertRaisesRegex(RuntimeError, 'unfinished_attempt'):
            self.fixture.run('smoke', [])
        self.assertEqual(self.fixture.calls, [])

    def test_retry_counts_both_attempts_and_unknown_usage(self):
        failure = result(status=503)
        failure.update(input_tokens=None, output_tokens=None)
        summary = self.fixture.run('smoke', [failure, result()])
        self.assertEqual(summary['attempts'], 2)
        self.assertEqual(summary['retries'], 1)
        self.assertEqual(summary['unknown_usage_attempts'], 1)
        self.assertEqual(summary['planned_input_units'], 2 * self.fixture.jobs[0]['planned_input_units'])

    def test_only_one_retry_per_job_and_terminal_failure_stays_terminal(self):
        with self.assertRaisesRegex(RuntimeError, 'persisted_terminal_failure'):
            self.fixture.run('smoke', [result(status=503), result(status=503)])
        self.assertEqual(self.fixture.calls, ['smoke', 'smoke'])
        with self.assertRaisesRegex(RuntimeError, 'terminal_failure_requires_reconciliation'):
            self.fixture.run('smoke', [])
        self.assertEqual(self.fixture.calls, [])

    def test_retry_cap_shared_between_phases(self):
        self.fixture.freeze['retry_limit'] = 1
        self.fixture.freeze_files()
        self.fixture.run('smoke', [result(status=503), result()])
        with self.assertRaisesRegex(RuntimeError, 'persisted_terminal_failure'):
            self.fixture.run('primary', [result(status=503)])
        self.assertEqual(self.fixture.calls, ['primary'])

    def test_caps_are_checked_before_next_attempt(self):
        job = self.fixture.jobs[0]
        stats = {'unfinished': None, 'attempts': 5, 'retries': 0,
                 'planned_input_units': 0, 'known_input_tokens': 0}
        with self.assertRaisesRegex(RuntimeError, 'attempt_cap'):
            runner.check_budget(stats, job, 0, self.fixture.freeze)
        stats.update(attempts=0, known_input_tokens=10000)
        with self.assertRaisesRegex(RuntimeError, 'input_cap'):
            runner.check_budget(stats, job, 0, self.fixture.freeze)
        stats.update(known_input_tokens=0, retries=2)
        with self.assertRaisesRegex(RuntimeError, 'retry_cap'):
            runner.check_budget(stats, job, 1, self.fixture.freeze)

    def test_freeze_drift_rejected_without_calls(self):
        with (Path(self.temp.name) / 'plans/jev.jsonl').open('ab') as target:
            target.write(b'\n')
        with self.assertRaisesRegex(ValueError, 'frozen_file_mismatch'):
            self.fixture.run('smoke', [])
        self.assertEqual(self.fixture.calls, [])

    def test_partial_journal_tail_is_not_truncated(self):
        self.fixture.run('smoke', [result()])
        ledger = Path(self.temp.name) / 'results/jev_attempts.jsonl'
        with ledger.open('ab') as target:
            target.write(b'{"event":')
        saved = ledger.read_bytes()
        with self.assertRaisesRegex(ValueError, 'partial_jsonl_tail'):
            self.fixture.run('primary', [])
        self.assertEqual(ledger.read_bytes(), saved)

    def test_duplicate_finish_and_negative_usage_are_rejected(self):
        self.fixture.run('smoke', [result()])
        jobs, _, freeze_hash = runner.verify(self.temp.name)
        events = runner.read_rows(Path(self.temp.name) / 'results/jev_attempts.jsonl')
        with self.assertRaisesRegex(ValueError, 'invalid_finish_sequence'):
            runner.accounting(events + [events[-1]], jobs, freeze_hash)
        corrupt = copy.deepcopy(events)
        corrupt[-1]['result']['input_tokens'] = -1
        with self.assertRaisesRegex(ValueError, 'invalid_result_usage'):
            runner.accounting(corrupt, jobs, freeze_hash)

    def test_pending_retry_resumes_as_retry_not_new_attempt_zero(self):
        self.fixture.run('smoke', [result(status=503), result()])
        directory = Path(self.temp.name) / 'results'
        events = runner.read_rows(directory / 'jev_attempts.jsonl')
        # Simulated crash checkpoint inside a disposable test directory.
        (directory / 'jev_attempts.jsonl').write_text(''.join(runner.canonical(e) + '\n' for e in events[:2]), encoding='utf-8', newline='\n')
        (directory / 'jev_responses.jsonl').unlink()
        summary = self.fixture.run('smoke', [result()])
        self.assertEqual(summary['attempts'], 2)
        self.assertEqual(summary['retries'], 1)
        self.assertEqual(self.fixture.calls, ['smoke'])

    def test_nested_lock_refuses_concurrent_writer(self):
        path = Path(self.temp.name) / 'lock'
        with runner.exclusive_lock(path):
            with self.assertRaises(OSError):
                with runner.exclusive_lock(path):
                    self.fail('Second writer unexpectedly owns the same lock')


if __name__ == '__main__':
    unittest.main()
