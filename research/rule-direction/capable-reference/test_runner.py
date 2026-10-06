"""Synthetic software fixtures only. No network or model observations are generated."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import analyze
import prepare
import runner


def response(text='yes', *, stop='end_turn', model=prepare.MODEL, usage=None, blocks=None, http=200):
    body = {'id': 'synthetic-message', 'type': 'message', 'role': 'assistant', 'model': model,
            'stop_reason': stop, 'content': blocks if blocks is not None else [{'type': 'text', 'text': text}],
            'usage': usage if usage is not None else {'input_tokens': 100, 'output_tokens': 20}}
    return {'http_status': http, 'request_id': 'synthetic-request', 'transport_error': None,
            'full_body': json.dumps(body), 'latency_seconds': 0.01}


def jobs(n=2):
    return {'jobs': [{'job_id': f'synthetic_{i}', 'payload': {'test_fixture': i}} for i in range(n)]}


class ParsingTests(unittest.TestCase):
    def parse(self, raw):
        return runner.classify(raw, runner.reservation(100))

    def test_only_exact_final_lowercase_labels(self):
        for text in ('yes', 'no', 'maybe', ' yes\n'):
            self.assertEqual(self.parse(response(text))['label'], text.strip())
        for text in ('YES', 'Yes', 'no.', 'answer: yes', 'yes no', '', 'yesterday'):
            result = self.parse(response(text))
            self.assertIsNone(result['label'])
            self.assertFalse(result['fatal_reasons'])

    def test_thinking_never_becomes_the_answer(self):
        blocks = [{'type': 'thinking', 'thinking': 'yes no maybe', 'signature': 'fixture'},
                  {'type': 'redacted_thinking', 'data': 'fixture'}, {'type': 'text', 'text': 'ma'},
                  {'type': 'text', 'text': 'ybe'}]
        self.assertEqual(self.parse(response(blocks=blocks))['label'], 'maybe')
        self.assertIsNone(self.parse(response(blocks=blocks[:2]))['label'])

    def test_refusal_is_invalid_but_does_not_halt(self):
        result = self.parse(response('yes', stop='refusal'))
        self.assertIsNone(result['label'])
        self.assertEqual(result['status'], 'refusal')
        self.assertFalse(result['fatal_reasons'])

    def test_truncation_cannot_be_scored_even_if_label_visible(self):
        result = self.parse(response('yes', stop='max_tokens'))
        self.assertIsNone(result['label'])
        self.assertIn('truncation', result['fatal_reasons'])

    def test_model_schema_http_and_usage_are_enforced(self):
        fixtures = [response(model='different-model'), response(http=429),
            response(usage={'input_tokens': True, 'output_tokens': 10}),
            response(usage={'input_tokens': 100, 'output_tokens': 10, 'cache_read_input_tokens': 1}),
            response(usage={'input_tokens': 2149, 'output_tokens': 10}),
            response(usage={'input_tokens': 100, 'output_tokens': 8193}),
            response(blocks=[{'type': 'text', 'text': 3}]),
            response(stop='tool_use')]
        bad_json = response()
        bad_json['full_body'] = '<error>'
        fixtures.append(bad_json)
        for raw in fixtures:
            with self.subTest(raw=raw):
                result = self.parse(raw)
                self.assertTrue(result['fatal_reasons'])
                self.assertIsNone(result['label'])
                self.assertEqual(result['status'], 'protocol_error')

    def test_transport_redacts_credential_echo_before_any_record_is_returned(self):
        key = 'synthetic-secret-for-offline-test'
        raw_body = json.loads(response()['full_body'])
        raw_body['provider_note'] = key
        fake_response = MagicMock()
        fake_response.status = 200
        fake_response.headers = {'request-id': 'echo-' + key}
        fake_response.read.return_value = json.dumps(raw_body).encode('utf-8')
        fake_response.__enter__.return_value = fake_response
        opener = MagicMock()
        opener.open.return_value = fake_response
        with patch.object(runner.urllib.request, 'build_opener', return_value=opener):
            result = runner.transport({'synthetic_fixture': True}, key)
        self.assertNotIn(key, json.dumps(result))
        self.assertTrue(result['credential_redacted'])
        self.assertIn('[REDACTED_SECRET]', result['full_body'])
        self.assertIn('credential_echo_redacted', self.parse(result)['fatal_reasons'])
        self.assertEqual(opener.open.call_count, 1)


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = jobs()
        self.estimates = {j['job_id']: 100 for j in self.plan['jobs']}
        self.path = self.root / 'results/journal.jsonl'

    def tearDown(self):
        self.temp.cleanup()

    def run_jobs(self, sender, plan=None, sleeper=lambda seconds: None):
        return runner.execute_jobs(self.root, plan or self.plan, self.estimates,
                                   'freeze-fixture', 'approval-fixture', 'software-test-only', sender, sleeper)

    def test_durable_start_precedes_call_and_completed_resume_does_not_repeat(self):
        seen = []
        sleeps = []
        def send(payload, key):
            events = runner.read_events(self.path)
            self.assertEqual(events[-1]['event'], 'start')
            seen.append(payload)
            return response('maybe')
        state = self.run_jobs(send, sleeper=sleeps.append)
        self.assertEqual(len(seen), 2)
        self.assertEqual(sleeps, [2.0])
        self.assertEqual(len(state['results']), 2)
        self.run_jobs(lambda *_: self.fail('Repeated completed request'))

    def test_resume_starts_only_unstarted_jobs(self):
        self.run_jobs(lambda *_: response(), plan={'jobs': self.plan['jobs'][:1]})
        seen = []
        self.run_jobs(lambda payload, key: (seen.append(payload) or response()))
        self.assertEqual(seen, [self.plan['jobs'][1]['payload']])

    def test_unresolved_start_never_retries(self):
        def interrupt(*args):
            raise RuntimeError('Synthetic interruption after durable start')
        with self.assertRaises(RuntimeError):
            self.run_jobs(interrupt)
        with self.assertRaises(ValueError):
            self.run_jobs(lambda *_: self.fail('Must not retry ambiguous outcome'))
        self.assertEqual(len(runner.read_events(self.path)), 1)

    def test_http_error_stops_with_reserve_retained_and_no_retry(self):
        calls = []
        def send(*args):
            calls.append(1)
            raw = response(http=429)
            raw['full_body'] = json.dumps({'type': 'error', 'error': {'type': 'rate_limit_error'}})
            return raw
        state = self.run_jobs(send)
        self.assertEqual(len(calls), 1)
        self.assertTrue(state['halted'])
        self.assertEqual(state['unknown_usage'], 1)
        self.assertEqual(state['cost_reserved_microusd'], runner.reservation(100)['cost_microusd'])
        with self.assertRaises(ValueError):
            self.run_jobs(send)
        self.assertEqual(len(calls), 1)

    def test_semantic_wrong_and_format_invalid_do_not_control_continuation(self):
        # This runner has no labels: a normal 'no' and malformed final answer both continue.
        answers = iter(['no', 'YES'])
        state = self.run_jobs(lambda *_: response(next(answers)))
        self.assertEqual(len(state['results']), 2)
        self.assertFalse(state['halted'])

    def test_cost_cap_checked_before_start(self):
        with patch.object(prepare, 'MAX_MICROUSD', 1):
            with self.assertRaises(ValueError):
                self.run_jobs(lambda *_: self.fail('Budget must block network'))
        self.assertFalse(self.path.exists())

    def test_input_and_attempt_caps(self):
        empty = runner.replay([], self.plan['jobs'], self.estimates, 'freeze-fixture')
        with patch.object(prepare, 'MAX_INPUT_RESERVE', 1):
            with self.assertRaises(ValueError):
                runner.check_next(empty, runner.reservation(100))
        with patch.object(prepare, 'MAX_ATTEMPTS', 0):
            with self.assertRaises(ValueError):
                runner.check_next(empty, runner.reservation(100))

    def test_corrupt_or_truncated_journal_cannot_resume(self):
        self.run_jobs(lambda *_: response())
        events = runner.read_events(self.path)
        events[1]['observation']['label'] = 'no'
        with self.assertRaises(ValueError):
            runner.replay(events, self.plan['jobs'], self.estimates, 'freeze-fixture')
        self.path.write_bytes(self.path.read_bytes().rstrip(b'\n'))
        with self.assertRaises(ValueError):
            runner.read_events(self.path)

    def test_changed_approval_is_not_silently_used_on_resume(self):
        self.run_jobs(lambda *_: response())
        events = runner.read_events(self.path)
        with self.assertRaises(ValueError):
            runner.replay(events, self.plan['jobs'], self.estimates, 'freeze-fixture', 'changed-approval')
        events[2]['approval_sha256_lf'] = 'changed-approval'
        with self.assertRaises(ValueError):
            runner.replay(events, self.plan['jobs'], self.estimates, 'freeze-fixture')

    def test_approval_binds_model_freeze_and_explicit_budget(self):
        approval = {'status': 'approved', 'model': prepare.MODEL, 'max_usd': 20,
                    'freeze_sha256': 'fixture', 'authorization_note': 'Synthetic test fixture only.'}
        (self.root / 'approval.json').write_text(json.dumps(approval), encoding='utf-8')
        runner.validate_approval(self.root, 'fixture', 20)
        for freeze, maximum in [('different', 20), ('fixture', None), ('fixture', 19)]:
            with self.assertRaises(ValueError):
                runner.validate_approval(self.root, freeze, maximum)

    def test_redirect_handler_never_creates_redirected_request(self):
        self.assertIsNone(runner.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.invalid'))


class OriginalContractTests(unittest.TestCase):
    def test_compiler_preserves_all_original_prompts_without_gold_in_payload(self):
        compiled = prepare.compile_requests()
        old = [j for j in prepare.load(prepare.OLD / 'request_plan.json')['jobs'] if j['backend'] == 'qwen']
        self.assertEqual(len(compiled['jobs']), 222)
        for source, job in zip(old, compiled['jobs']):
            self.assertEqual(job['job_id'], source['id'])
            self.assertEqual(job['payload']['messages'], [{'role': 'user', 'content': source['prompt']}])
            self.assertEqual(set(job['payload']), {'model', 'max_tokens', 'thinking', 'output_config', 'messages'})
            self.assertNotIn('reference', job)
            self.assertNotIn('expected_smoke_action', job)

    def test_reporting_preserves_full_controls_and_does_not_count_pending_as_correct(self):
        cases = prepare.load(prepare.OLD / 'cases.json')
        rows = [{'phase': 'main', 'item_id': c['id'], 'family_id': c['family_id'],
            'relation': c['relation'], 'fact_state': c['fact_state'], 'reference': c['reference'],
            'mapping': m, 'label': c['reference'], 'correct': True, 'executed': True, 'status': 'ok'}
            for m in (0, 1) for c in cases]
        report = analyze.summarize(rows)
        self.assertEqual(report['mappings']['0']['complete_nine_case_families_correct'], 12)
        self.assertEqual(report['mappings']['0']['critical_pairs_correct'], {'positive': 12, 'negative': 12})
        self.assertEqual(report['mappings']['0']['old_shared_error_cells']['resolved'], 24)
        self.assertEqual(report['mappings']['0']['previously_correct_controls']['correct'], 84)
        self.assertEqual(report['mappings']['0']['complete_biconditional_like_signature_families'], 0)
        self.assertEqual(report['mappings']['0']['always_maybe_control_correct'], 60)
        # Deliberately synthetic reproduction of the old two-cell error signature.
        for row in rows:
            if (row['relation'], row['fact_state']) == ('necessary', 'positive'):
                row.update(label='yes', correct=False)
            if (row['relation'], row['fact_state']) == ('sufficient', 'negative'):
                row.update(label='no', correct=False)
        report = analyze.summarize(rows)
        self.assertEqual(report['mappings']['0']['old_shared_error_cells']['valid_wrong'], 24)
        self.assertEqual(report['mappings']['0']['old_shared_error_cells']['resolved'], 0)
        self.assertEqual(report['mappings']['0']['previously_correct_controls']['new_valid_wrong'], 0)
        self.assertEqual(report['mappings']['0']['complete_biconditional_like_signature_families'], 12)
        rows[0].update(label=None, correct=False, status='invalid')
        report = analyze.summarize(rows)
        self.assertEqual(report['mappings']['0']['previously_correct_controls']['invalid'], 1)
        for row in rows:
            row.update(label=None, correct=False, executed=False, status='not_run')
        report = analyze.summarize(rows)
        self.assertEqual(report['both_mappings_executed'], 0)
        self.assertEqual(report['mappings']['0']['complete_nine_case_families_correct'], 0)
        self.assertEqual(report['mappings']['0']['invalid'], 0)
        self.assertEqual(report['mappings']['0']['old_shared_error_cells']['unrun'], 24)
        self.assertEqual(report['mappings']['0']['complete_biconditional_like_signature_families'], 0)


if __name__ == '__main__':
    unittest.main()
