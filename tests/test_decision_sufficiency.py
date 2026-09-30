"""Check semantic invariants and independent finite-world reconstruction."""
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]/'research/decision-sufficiency'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


saved = {n: sys.modules.get(n) for n in ('semantics', 'examples')}
try:
    S = load('sufficiency_semantics', ROOT/'semantics.py'); sys.modules['semantics'] = S
    E = load('sufficiency_examples', ROOT/'examples.py'); sys.modules['examples'] = E
    A = load('sufficiency_audit', ROOT/'audit.py')
finally:
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


class DecisionSufficiencyTests(unittest.TestCase):
    def test_independent_database_enumeration(self):
        audit = A.exhaustive()
        self.assertEqual(audit['valid_contracts_checked'], 730)
        self.assertEqual(audit['inconsistent_contracts_rejected'], 180)

    def test_authored_semantic_examples_and_no_execution(self):
        for case in E.cases():
            with self.subTest(case=case['case_id']):
                result = S.evaluate(case['contract'])
                for key, expected in case['expected'].items():
                    self.assertEqual(result[key], expected)
                self.assertFalse(result['execution_authorized'])
                for outcome, witness in result['witnesses_by_outcome'].items():
                    self.assertIn(witness, result['projected_worlds'])
                    self.assertEqual(witness['outcome'], outcome)

    def test_inconsistent_inputs_never_become_ordinary_unknown_or_true(self):
        for case in E.invalid_cases():
            with self.subTest(case=case['case_id']), self.assertRaises(S.ContractError):
                S.evaluate(case['contract'])

    def test_complete_no_target_and_possible_no_target_do_not_accept_gift(self):
        for case_id in ('s13', 's14'):
            result = S.evaluate(next(c['contract'] for c in E.cases() if c['case_id'] == case_id))
            self.assertEqual(result['predicate_only'], S.UNKNOWN)
            self.assertTrue(any(not w['target_exists'] for w in result['projected_worlds']))

    def test_irrelevant_records_and_record_order_cannot_change_certificate(self):
        for case in E.cases():
            state = copy.deepcopy(case['contract']); baseline = S.evaluate(state)
            state['records'].reverse()
            state['records'].append(E.record('new_irrelevant_id', ['card_A', 'card_B'], 'unused_product'))
            self.assertEqual(S.evaluate(state), baseline)

    def test_consistent_domain_refinement_cannot_reverse_certain_predicate(self):
        domains = [['card_A'], ['card_B'], ['card_A', 'card_B']]
        for ds, destination in itertools.product(itertools.product(domains, repeat=2), ('card_A', 'card_B', 'gift_G', None)):
            state = E.base(); state['records'] = [E.record(f'order_{i}', d) for i, d in enumerate(ds)]
            state['request']['destination_id'] = destination
            before = S.evaluate(state)['predicate_only']
            for actual in itertools.product(*ds):
                refined = copy.deepcopy(state)
                for record, method in zip(refined['records'], actual):
                    record['original_methods'] = [method]
                if before != S.UNKNOWN:
                    self.assertEqual(S.evaluate(refined)['predicate_only'], before)

    def test_unrecognized_fields_are_not_silently_ignored(self):
        state = E.base(); state['retrieval']['trusted_by_model'] = True
        with self.assertRaises(S.ContractError):
            S.evaluate(state)

    def test_cli_invalid_status_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'invalid.json'; path.write_text(json.dumps(E.invalid_cases()[0]['contract']))
            result = subprocess.run([sys.executable, str(ROOT/'semantics.py'), str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        body = json.loads(result.stdout)
        self.assertEqual(body['status'], 'INVALID_CONTRACT')
        self.assertNotIn('predicate_only', body)
        self.assertFalse(body['execution_authorized'])


if __name__ == '__main__':
    unittest.main()
