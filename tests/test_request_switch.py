"""Prepared explorer input fidelity, safe embedding and no-inference boundary."""
import copy
import importlib.util
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('request_switch_builder_tests', ROOT / 'docs/build_request_switch.py')
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class RequestSwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = builder.payload()

    def test_every_frozen_visible_input_prompt_and_token_is_present_once(self):
        displayed = [view for scene in self.data['scenes'] for view in scene['views']]
        prepared = builder.read_rows(builder.STUDY / 'data/views.jsonl')
        encoded = builder.read_rows(builder.execution.ENCODED)
        self.assertEqual({view['view_id'] for view in displayed}, {view['view_id'] for view in prepared})
        for view in prepared:
            shown = next(row for row in displayed if row['view_id'] == view['view_id'])
            self.assertEqual((shown['state'], shown['policy']), (view['state'], view['policy']))
        queries = [query for view in displayed for query in view['queries']]
        self.assertEqual((len(queries), len({row['query_id'] for row in queries})), (500, 500))
        keys = ('query_id', 'arm', 'mapping', 'line_index', 'order', 'prompt', 'input_tokens')
        self.assertEqual({row['query_id']: row for row in queries},
                         {row['query_id']: {key: row[key] for key in keys} for row in encoded})
        self.assertEqual(sum(row['input_tokens'] for row in queries), 188797)

    def test_pairs_switch_only_target_and_program_action(self):
        self.assertEqual(len(self.data['scenes']), 24)
        for scene in self.data['scenes']:
            left, right = scene['views']
            self.assertNotEqual(left['target'], right['target'])
            self.assertNotEqual(left['program_reference'], right['program_reference'])
            self.assertEqual(left['policy'], right['policy'])
            self.assertEqual(left['state'].split('\n', 1)[1], right['state'].split('\n', 1)[1])
            self.assertEqual([line['text'] for line in left['lines']], [line['text'] for line in right['lines']])
            self.assertEqual([line['owner_id'] for line in left['lines']], [line['owner_id'] for line in right['lines']])
            self.assertTrue(all(a['status'] != b['status'] for a, b in zip(left['lines'], right['lines'])))
        lines = [line for scene in self.data['scenes'] for view in scene['views'] for line in view['lines']]
        self.assertEqual(Counter(line['status'] for line in lines), {'KEEP': 100, 'DROP': 100})

    def test_program_references_do_not_copy_prepared_gold_or_records(self):
        original_read = builder.read_rows

        def poisoned_read(path):
            rows = copy.deepcopy(original_read(path))
            if path == builder.STUDY / 'data/views.jsonl':
                for row in rows:
                    row['gold'] = 'UNTRUSTED_GOLD_SENTINEL'
            if path == builder.STUDY / 'data/scenes.jsonl':
                for row in rows:
                    row['records'] = [{'scope': 'UNTRUSTED_RECORD_SENTINEL'}]
            return rows

        with patch.object(builder, 'read_rows', side_effect=poisoned_read):
            self.assertEqual(builder.payload(), self.data)

    def test_script_embedding_escapes_closing_tag_without_changing_json(self):
        fixture = {'text': '</script><img src=x onerror=alert(1)>\u2028\u2029'}
        template = '<script type="application/json">' + builder.MARKER + '</script>'
        output = builder.render(template, fixture).decode('utf-8')
        self.assertEqual(output.count('</script>'), 1)
        self.assertNotIn('<img', output)
        embedded = output.split('>', 1)[1].rsplit('</script>', 1)[0]
        self.assertEqual(json.loads(embedded), fixture)
        self.assertIn('\\u003c', embedded)
        with self.assertRaises(ValueError):
            builder.render('No marker', fixture)
        with self.assertRaises(ValueError):
            builder.render(builder.MARKER * 2, fixture)

    def test_build_writes_only_destination_and_verify_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'request_switch.html'
            template = '<script type="application/json">' + builder.MARKER + '</script>'
            with patch.object(builder, 'OUTPUT', destination), patch.object(builder, 'render',
                                                                            return_value=builder.render(template, self.data)):
                builder.run('build')
                before = destination.read_bytes()
                with patch.object(Path, 'write_bytes', side_effect=AssertionError('verify attempted write')):
                    builder.run('verify')
                self.assertEqual(destination.read_bytes(), before)
                self.assertEqual([path.name for path in Path(directory).iterdir()], ['request_switch.html'])
                destination.write_bytes(before + b'changed')
                with self.assertRaises(ValueError):
                    builder.run('verify')

    def test_payload_reads_no_scientific_results_or_checkpoint_weights(self):
        original_bytes, original_text = Path.read_bytes, Path.read_text
        allowed_inventory = ROOT / 'research/next-study/results/weight_checksums.json'

        def guard(path):
            resolved = path.resolve()
            normalized = resolved.as_posix().lower()
            if '/results/' in normalized and resolved != allowed_inventory:
                raise AssertionError('Scientific result read: ' + str(path))
            if path.suffix in ('.safetensors', '.bin', '.pt'):
                raise AssertionError('Model weight read: ' + str(path))

        def read_bytes(path):
            guard(path)
            return original_bytes(path)

        def read_text(path, *args, **kwargs):
            guard(path)
            return original_text(path, *args, **kwargs)

        with patch.object(Path, 'read_bytes', read_bytes), patch.object(Path, 'read_text', read_text), \
                patch.object(Path, 'write_bytes', side_effect=AssertionError('payload attempted write')):
            self.assertEqual(builder.payload(), self.data)


if __name__ == '__main__':
    unittest.main()
