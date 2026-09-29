import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from core import read_jsonl
from run import ROOT
from replicate import execute, ledger_state, Jev
from verify_evidence import verify_row, verify_fingerprint
import json


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        cls.cases = {c['id']: c for c in read_jsonl(ROOT / 'data/cases.jsonl')}

    def test_raw_choice_and_probabilities_cannot_drift(self):
        row = copy.deepcopy(read_jsonl(ROOT / 'results/jev_formal.jsonl')[0])
        row['raw_response']['answers']['decision']['choice'] = 'A' if row['letter'] == 'B' else 'B'
        with self.assertRaisesRegex(ValueError, 'Raw choice'):
            verify_row(row, self.cases[row['case_id']], self.manifest, 'jev', 'formal')

    def test_logits_cannot_drift_from_reported_probabilities(self):
        row = copy.deepcopy(read_jsonl(ROOT / 'results/qwen_formal.jsonl')[0])
        row['candidate_logits'] = {'A': 0., 'B': 0.}
        with self.assertRaisesRegex(ValueError, 'Logit-to'):
            verify_row(row, self.cases[row['case_id']], self.manifest, 'qwen', 'formal')

    def test_prompt_and_manifest_tampering_are_rejected(self):
        row = copy.deepcopy(read_jsonl(ROOT / 'results/qwen_formal.jsonl')[0])
        row['prompt'] += 'Guess instead.'
        with self.assertRaisesRegex(ValueError, 'prompt mismatch'):
            verify_row(row, self.cases[row['case_id']], self.manifest, 'qwen', 'formal')
        manifest = {**self.manifest, 'thinking': True}
        with self.assertRaisesRegex(ValueError, 'self-fingerprint'):
            verify_fingerprint(manifest)

    def test_full_cache_never_constructs_backend_or_overwrites_runtime(self):
        args = SimpleNamespace(backend='qwen', phase='formal', output=str(ROOT / 'results'), limit=None, dry_run=False)
        # Published evidence is protected even on a cache-only invocation.
        with self.assertRaises(ValueError):
            execute(args)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / 'qwen_formal.jsonl').write_bytes((ROOT / 'results/qwen_formal.jsonl').read_bytes())
            runtime = output / 'qwen_formal_runtime.json'
            runtime.write_text('historical runtime', encoding='utf-8')
            args.output = temp
            factory = Mock(side_effect=AssertionError('Must not load a model'))
            status = execute(args, factory)
            self.assertEqual(status['pending'], 0)
            factory.assert_not_called()
            self.assertEqual(runtime.read_text(), 'historical runtime')
            self.assertFalse((output / 'sessions').exists())

    def test_resume_caps_attempts_and_accounts_for_orphans(self):
        rows = []
        for number in (1, 2):
            rows.extend([{'event':'attempt_started','job_key':'job','attempt':number},
                         {'event':'attempt_finished','job_key':'job','attempt':number,'cost_known':True,'known_cost_usd':.01}])
        counts, attempts, cost = ledger_state(rows)
        self.assertEqual((counts['job'], attempts, cost), (2, 2, .02))
        with tempfile.TemporaryDirectory() as temp:
            from core import append_jsonl
            path = Path(temp) / 'ledger.jsonl'
            for row in rows:
                append_jsonl(path, row)
            backend = object.__new__(Jev)
            backend.ledger_path = path
            with self.assertRaisesRegex(RuntimeError, 'Persistent per-job'):
                backend.ask({}, 'job')
        with self.assertRaisesRegex(RuntimeError, 'unknown cost'):
            ledger_state(rows + [{'event':'attempt_started','job_key':'orphan','attempt':1}])
        with self.assertRaisesRegex(RuntimeError, 'unknown cost'):
            ledger_state([{'event':'attempt_started','job_key':'job','attempt':1},
                          {'event':'attempt_finished','job_key':'job','attempt':1,'cost_known':False}])


if __name__ == '__main__':
    unittest.main()
