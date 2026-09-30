import copy
import json
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/external-validation'))
from execution_journal import append, execute, exclusive_lock, read_events, replay


def plan(backend='jev'):
    return {'jobs': [{'id': f'synthetic_{i}', 'backend': backend,
                      'input_ids': [1, 2], 'max_new_tokens': 10} for i in range(3)],
            'limits': {'http_attempts': 3, 'local_generations': 3,
                       'jev_actual_input_tokens': 100, 'local_input_tokens': 100,
                       'local_generated_tokens': 30, 'local_generation_wall_seconds': 60}}


def result(action='No', usage=2):
    return {'status': 'ok', 'action': action, 'input_tokens': usage,
            'output_tokens': 3, 'latency_seconds': 0.1, 'detail': {'synthetic': True}}


class RuleJournalTests(unittest.TestCase):
    def test_closed_partial_session_resumes_only_remaining_jobs(self):
        calls = []
        @contextmanager
        def factory():
            yield lambda job, remaining: (calls.append(job['id']) or result()), {}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'jev.jsonl'
            events = []
            for event in (
                {'event': 'header', 'version': 1, 'plan_sha256': 'hash', 'backend': 'jev',
                 'job_ids': [j['id'] for j in plan()['jobs']]},
                {'event': 'session_start', 'session': 0},
                {'event': 'call_start', 'job_id': 'synthetic_0'},
                {'event': 'call_finish', 'job_id': 'synthetic_0', 'result': result()},
                {'event': 'session_end', 'session': 0, 'elapsed_seconds': 7.0},
            ):
                append(path, events, event)
            r = execute(temp, plan(), 'hash', 'jev', factory)
            self.assertEqual(calls, ['synthetic_1', 'synthetic_2'])
            self.assertEqual(r['status'], 'complete')
            self.assertEqual(r['state']['input_tokens'], 6)
            self.assertGreaterEqual(r['state']['session_seconds'], 7)

    def test_completed_resume_never_repeats_calls_or_enters_backend(self):
        called = []
        @contextmanager
        def factory():
            called.append('factory')
            yield lambda job, remaining: (called.append(job['id']) or result()), {'synthetic': True}
        with tempfile.TemporaryDirectory() as temp:
            first = execute(temp, plan(), 'synthetic_hash', 'jev', factory)
            before = list(called)
            second = execute(temp, plan(), 'synthetic_hash', 'jev', factory)
            self.assertEqual(first['status'], 'complete')
            self.assertEqual(second['status'], 'complete')
            self.assertEqual(called, before)
            self.assertEqual(first['state']['input_tokens'], 6)

    def test_result_unknown_after_interruption_is_not_retried(self):
        called = []
        @contextmanager
        def factory():
            def call(job, remaining):
                called.append(job['id'])
                raise KeyboardInterrupt()
            yield call, {}
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(KeyboardInterrupt):
                execute(temp, plan(), 'synthetic_hash', 'jev', factory)
            resumed = execute(temp, plan(), 'synthetic_hash', 'jev', factory)
            self.assertEqual(resumed['status'], 'unresolved_interruption')
            self.assertEqual(called, ['synthetic_0'])
            self.assertEqual(len(resumed['state']['started']), 1)

    def test_uncertain_usage_and_transport_failure_halt_with_redacted_exception(self):
        @contextmanager
        def factory():
            def call(*args):
                raise RuntimeError('DO_NOT_PERSIST_EXCEPTION_MESSAGE')
            yield call, {}
        with tempfile.TemporaryDirectory() as temp:
            r = execute(temp, plan(), 'synthetic_hash', 'jev', factory)
            self.assertEqual(r['status'], 'recorded_failure_requires_repair')
            self.assertTrue(r['state']['unknown_usage'])
            self.assertEqual(len(r['state']['started']), 1)
            self.assertNotIn('DO_NOT_PERSIST_EXCEPTION_MESSAGE', (Path(temp) / 'jev.jsonl').read_text())

    def test_malformed_generated_output_is_scored_failure_not_selective_stop(self):
        @contextmanager
        def factory():
            yield lambda *args: result(action=None), {}
        with tempfile.TemporaryDirectory() as temp:
            r = execute(temp, plan('qwen'), 'synthetic_hash', 'qwen', factory)
            self.assertEqual(r['status'], 'complete')
            self.assertEqual(len(r['state']['results']), 3)
            self.assertTrue(all(v['action'] is None for v in r['state']['results'].values()))

    def test_usage_crossing_stops_before_next_attempt_and_reports_overrun(self):
        @contextmanager
        def factory():
            yield lambda *args: result(usage=110), {}
        with tempfile.TemporaryDirectory() as temp:
            r = execute(temp, plan(), 'synthetic_hash', 'jev', factory)
            self.assertEqual(r['status'], 'input_budget')
            self.assertEqual(r['overruns']['input_tokens'], 10)
            self.assertEqual(len(r['state']['started']), 1)

    def test_local_cap_reserved_before_start_and_elapsed_budget_not_reset(self):
        clock_value = [0.0]
        @contextmanager
        def factory():
            def call(*args):
                clock_value[0] += 61
                return result()
            yield call, {}
        with tempfile.TemporaryDirectory() as temp:
            r = execute(temp, plan('qwen'), 'synthetic_hash', 'qwen', factory, clock=lambda: clock_value[0])
            self.assertEqual(r['status'], 'time_budget')
            self.assertEqual(len(r['state']['started']), 1)
            r2 = execute(temp, plan('qwen'), 'synthetic_hash', 'qwen', factory, clock=lambda: clock_value[0])
            self.assertEqual(r2['state']['session_seconds'], 61)
        small = plan('qwen'); small['limits']['local_generated_tokens'] = 9
        with tempfile.TemporaryDirectory() as temp:
            r = execute(temp, small, 'synthetic_hash', 'qwen', factory)
            self.assertEqual(r['status'], 'output_budget')
            self.assertEqual(r['state']['started'], [])

    def test_partial_tail_mismatched_plan_and_unclosed_session_are_not_repaired(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'jev.jsonl'
            path.write_bytes(b'{"seq":0')
            with self.assertRaises(ValueError):
                read_events(path)
            self.assertEqual(path.read_bytes(), b'{"seq":0')
        events = []
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'jev.jsonl'
            append(path, events, {'event': 'header', 'version': 1, 'plan_sha256': 'hash',
                                 'backend': 'jev', 'job_ids': [j['id'] for j in plan()['jobs']]})
            append(path, events, {'event': 'session_start', 'session': 0})
            @contextmanager
            def forbidden():
                raise AssertionError('Must not enter backend')
                yield
            r = execute(temp, plan(), 'hash', 'jev', forbidden)
            self.assertEqual(r['status'], 'unresolved_interruption')
            with self.assertRaises(ValueError):
                execute(temp, plan(), 'another_hash', 'jev', forbidden)

    def test_duplicate_finish_corrupt_sequence_and_concurrent_lock_are_rejected(self):
        @contextmanager
        def factory():
            yield lambda *args: result(), {}
        with tempfile.TemporaryDirectory() as temp:
            execute(temp, plan(), 'hash', 'jev', factory)
            path = Path(temp) / 'jev.jsonl'
            events = read_events(path)
            repeated = next(e for e in events if e['event'] == 'call_finish')
            with self.assertRaises(ValueError):
                replay(events + [repeated], plan_hash='hash', backend='jev', jobs=plan()['jobs'])
            with exclusive_lock(Path(temp) / 'other.lock'):
                with self.assertRaises(OSError):
                    with exclusive_lock(Path(temp) / 'other.lock'):
                        pass


if __name__ == '__main__':
    unittest.main()
