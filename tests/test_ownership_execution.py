"""Execution guards only; no model, tokenizer, weight load or model fixtures."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1] / 'research/request-ownership'
DEFINITION = importlib.util.spec_from_file_location('ownership_execution_tests', HERE / 'execution.py')
execution = importlib.util.module_from_spec(DEFINITION)
DEFINITION.loader.exec_module(execution)


class OwnershipExecutionTests(unittest.TestCase):
    def test_exact_union_preserves_all_prepared_payload_and_budget(self):
        rows = execution.source_plans()
        originals = execution.read_rows(HERE / 'preparation/queries.jsonl')
        self.assertEqual(len(rows), 500)
        self.assertEqual(sum(r['input_tokens'] for r in rows), 188797)
        self.assertEqual({r['split'] for r in rows}, {'new_scene_development'})
        for row, original in zip(rows, originals):
            self.assertEqual({key: row[key] for key in original}, original)
            self.assertEqual(row['input_tokens'], len(row['token_ids']))
            self.assertNotIn('gold', row)

    def test_missing_or_old_approval_hash_refused_before_git_or_directory(self):
        for supplied in (None, '', 'old-study-hash'):
            with patch.object(execution, 'verify_frozen', return_value={'config_hash': 'new'}), \
                    patch.object(execution.subprocess, 'check_output') as git, \
                    tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / 'results'
                with self.assertRaisesRegex(ValueError, 'approved config hash'):
                    execution.reserve_output(supplied, out)
                git.assert_not_called()
                self.assertFalse(out.exists())

    def test_dirty_source_refused_before_output_reservation(self):
        with patch.object(execution, 'verify_frozen', return_value={'config_hash': 'new'}), \
                patch.object(execution.subprocess, 'check_output', return_value=b' M source.py'), \
                tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'results'
            with self.assertRaisesRegex(ValueError, 'Commit the complete'):
                execution.reserve_output('new', out)
            self.assertFalse(out.exists())

    def test_existing_empty_and_partial_directory_cannot_be_reused(self):
        for partial in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / 'results'
                out.mkdir()
                if partial:
                    (out / 'failure-note.txt').write_text('preserve me', encoding='utf-8')
                with patch.object(execution, 'verify_frozen', return_value={'config_hash': 'new'}), \
                        patch.object(execution.subprocess, 'check_output', side_effect=[b'', 'commit\n']):
                    with self.assertRaises(FileExistsError):
                        execution.reserve_output('new', out)
                if partial:
                    self.assertEqual((out / 'failure-note.txt').read_text(), 'preserve me')

    def test_fresh_reservation_is_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'results'
            with patch.object(execution, 'verify_frozen', return_value={'config_hash': 'new'}), \
                    patch.object(execution.subprocess, 'check_output', side_effect=[b'', 'commit\n']):
                manifest, commit, destination = execution.reserve_output('new', out)
            self.assertEqual((manifest['config_hash'], commit, destination), ('new', 'commit', out))
            self.assertTrue(out.is_dir())

    def test_invalid_numbers_cannot_be_serialized_as_success(self):
        execution.validate_values([1.0, 1.0], [.5, .5], .2, .01)
        invalid = [([float('nan')], [1.], .2, .01),
                   ([1.], [float('inf')], .2, .01),
                   ([1.], [.4], .2, .01), ([1.], [1.], 1.1, .01),
                   ([1.], [1.], .2, -1.)]
        for values in invalid:
            with self.assertRaises(ValueError):
                execution.validate_values(*values)

    def test_checkpoint_retains_attempt_count_distinct_from_saved_count(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            env = {'status': 'failed', 'attempted_scientific_forwards': 3, 'scientific_forwards': 2}
            execution.checkpoint(out, env)
            self.assertEqual(json.loads((out / 'runtime.json').read_text()), env)
            self.assertFalse((out / 'runtime.pending.json').exists())

    def test_freeze_rejects_changed_budget_even_with_rehashed_manifest(self):
        rows = execution.source_plans()
        support = dict.fromkeys(execution.SUPPORT_FILES, 'a' * 64)
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(execution, 'SOURCE_PATHS', ('prepare.py',)):
            manifest = execution.expected_manifest(rows, support)
            encoded = Path(directory) / 'queries.jsonl'
            path = Path(directory) / 'manifest.json'
            encoded.write_bytes(execution.packed(rows))
            path.write_bytes(execution.pretty(manifest))
            with patch.object(execution, 'ENCODED', encoded), patch.object(execution, 'MANIFEST', path):
                self.assertEqual(execution.verify_frozen(), manifest)
                manifest['scientific_forwards'] = 499
                del manifest['config_hash']
                manifest['config_hash'] = execution.sha(json.dumps(
                    manifest, sort_keys=True, separators=(',', ':')).encode())
                path.write_bytes(execution.pretty(manifest))
                with self.assertRaisesRegex(ValueError, 'freeze source, scope'):
                    execution.verify_frozen()

    def test_freeze_refuses_plan_change_with_same_record_count(self):
        rows = execution.source_plans()
        support = dict.fromkeys(execution.SUPPORT_FILES, 'b' * 64)
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(execution, 'SOURCE_PATHS', ('prepare.py',)):
            manifest = execution.expected_manifest(rows, support)
            encoded = Path(directory) / 'queries.jsonl'
            path = Path(directory) / 'manifest.json'
            rows[0]['token_ids'][0] += 1
            encoded.write_bytes(execution.packed(rows))
            path.write_bytes(execution.pretty(manifest))
            with patch.object(execution, 'ENCODED', encoded), patch.object(execution, 'MANIFEST', path):
                with self.assertRaisesRegex(ValueError, 'freeze source, scope'):
                    execution.verify_frozen()


if __name__ == '__main__':
    unittest.main()
