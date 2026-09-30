import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/external-validation'))
import run_comparison as runner
from comparison_backends import adapt_jev, decode_api_body
from action_interface import ACTIONS


def response():
    return {'model': 'jev-1.13.0', 'answers': {'decision': {'type': 'choice',
            'choice': 'A', 'confidence': .7, 'probabilities': {'A': .7, 'B': .1, 'C': .1, 'D': .1}}},
            'usage': {'input_tokens': 20, 'output_tokens': 5}}


class RuleComparisonRunnerTests(unittest.TestCase):
    def test_jev_keeps_probabilities_and_known_usage_on_schema_failure(self):
        raw = response()
        good = adapt_jev(raw, 200, ACTIONS, .25)
        self.assertEqual(good['status'], 'ok')
        self.assertEqual(good['action'], 'Yes')
        self.assertEqual(good['detail']['raw_response'], raw)
        raw['model'] = 'unexpected_model'
        bad = adapt_jev(raw, 200, ACTIONS, .25)
        self.assertEqual(bad['status'], 'protocol_error')
        self.assertIsNone(bad['action'])
        self.assertEqual(bad['input_tokens'], 20)
        self.assertEqual(adapt_jev(raw, 500, ACTIONS, .25)['detail']['error'], 'http_failure')

    def test_malformed_json_is_preserved_as_text_without_nonfinite_or_duplicate_values(self):
        for text in ('{"a": NaN}', '{"a": 1, "a": 2}', '<html>failure</html>'):
            decoded = decode_api_body(text)
            self.assertEqual(decoded, {'invalid_json_body': text})
            self.assertEqual(adapt_jev(decoded, 200, ACTIONS, 0)['status'], 'protocol_error')
        self.assertEqual(decode_api_body(json.dumps(response())), response())

    def test_missing_freeze_stops_cli_before_plan_or_backend(self):
        argv = ['runner', 'jev', '--review-a', 'absent-a', '--review-b', 'absent-b',
                '--adjudication', 'absent-adj', '--model-dir', 'absent-model']
        with patch.object(runner, 'FREEZE_PATH', Path('nonexistent_synthetic_freeze.json')), \
                patch.object(runner, 'verified_plan') as plan, patch.object(runner, 'execute') as execute, \
                patch.object(sys, 'argv', argv), redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit):
                runner.main()
            plan.assert_not_called(); execute.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())['stage'], 'freeze')

    def test_recomputed_plan_must_match_preserved_bytes_not_just_a_status_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan, refs = {'synthetic_plan': True}, ['SYNTHETIC_ONLY']
            saved_plan, saved_refs = runner.readable(plan), runner.readable(refs)
            (root / 'comparison_plan.json').write_bytes(saved_plan)
            (root / 'scoring_references.json').write_bytes(saved_refs)
            freeze = {'plan_sha256': runner.sha(saved_plan), 'references_sha256': runner.sha(saved_refs)}
            args = SimpleNamespace(plan_dir=root, review_a='a', review_b='b',
                                   adjudication='c', review_dir=root, model_dir=root)
            with patch.object(runner, 'private_directory', side_effect=lambda p: p), \
                    patch.object(runner, 'compile_reviewed', return_value=(plan, refs)) as compile:
                self.assertEqual(runner.verified_plan(args, freeze), plan)
                compile.return_value = ({'synthetic_plan': False}, refs)
                with self.assertRaisesRegex(ValueError, 'reproduced'):
                    runner.verified_plan(args, freeze)

    def test_freeze_requires_committed_protocol_and_exact_source_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source.py'; source.write_bytes(b'# synthetic source\n')
            protocol = root / 'protocol.md'; protocol.write_bytes(b'SYNTHETIC protocol\n')
            freeze_path = root / 'freeze.json'
            freeze = {'status': 'frozen_for_execution', 'study': runner.PLAN_ID,
                      'source_hashes_lf': {'source.py': runner.sha(source.read_bytes())},
                      'protocol_sha256_lf': runner.sha(protocol.read_bytes())}
            freeze_path.write_text(json.dumps(freeze), encoding='utf-8')
            committed = {'HEAD:freeze.json': freeze_path.read_bytes(), 'HEAD:protocol.md': protocol.read_bytes()}
            def git(args, **kwargs):
                return b'' if args[1] == 'status' else committed[args[2]]
            with patch.object(runner, 'ROOT', root), patch.object(runner, 'FREEZE_PATH', freeze_path), \
                    patch.object(runner, 'PROTOCOL_PATH', protocol), \
                    patch.object(runner, 'SOURCE_FILES', ('source.py',)), \
                    patch.object(runner.subprocess, 'check_output', side_effect=git):
                self.assertEqual(runner.check_freeze(), freeze)
                source.write_bytes(b'# changed synthetic source\n')
                with self.assertRaisesRegex(ValueError, 'source pins'):
                    runner.check_freeze()


if __name__ == '__main__':
    unittest.main()
