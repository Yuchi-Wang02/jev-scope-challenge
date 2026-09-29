import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/fact-execution'))
from interface import compile_visible,execute,status_for,instruction
from data_tools import original_cases,material
from fact_run import queries,executor_audit
from fact_analyze import choose,softmax


class FactInterfaceTests(unittest.TestCase):
    def test_missing_is_not_negative_and_redundant_missing_can_still_deny(self):
        c=original_cases()[0];schema=compile_visible(c['state'],c['instruction'])
        self.assertEqual(execute(schema,{'review_a':'TRUE','review_b':'MISSING'}),'INSUFFICIENT')
        self.assertEqual(execute(schema,{'review_a':'MISSING','review_b':'FALSE'}),'DENY')
        self.assertEqual(execute(schema,{'review_a':'FALSE','review_b':'CONFLICT'}),'INSUFFICIENT')
        with self.assertRaises(ValueError):execute(schema,{'review_a':'TRUE'})

    def test_compile_uses_policy_header_not_evidence_values_or_hidden_metadata(self):
        c=original_cases()[0];s=compile_visible(c['state'],c['instruction'])
        changed=c['state'].splitlines()[0]+'\nArbitrary unparsed evidence; different values.'
        self.assertEqual(s,compile_visible(changed,c['instruction']))
        prompt=instruction(s,c['instruction'],'fact','review_a')
        self.assertNotIn(c['id'],prompt);self.assertNotIn('legal_worlds',prompt)

    def test_reference_spans_are_exact_and_rewrite_pack_is_unscored(self):
        cases,refs,pairs=material();lookup={c['id']:c for c in cases}
        self.assertEqual(len(refs),168);self.assertEqual(len(pairs),144)
        for r in refs:
            for span in r['evidence_spans']:
                self.assertEqual(lookup[r['source_id']]['state'][span['start']:span['end']],span['text'])
        self.assertTrue(all(p['representation']=='review_only' and not p['model_scored'] and not p['human_semantics_verified'] for p in pairs))

    def test_exhaustive_executor_and_rewrite_reserved_input_rejection(self):
        self.assertEqual(executor_audit()['states'],96)
        cases=original_cases();self.assertEqual(len(queries(cases)),552)
        for mutate in ('rewrite','reserved','gold'):
            changed=[dict(c) for c in cases]
            if mutate=='rewrite':changed[0]['state']+='\nA provisional rewrite.'
            elif mutate=='reserved':changed[0]['split']='reserved_test'
            else:changed[0]['gold']='NOT_A_DECISION'
            with self.assertRaises(ValueError):queries(changed)

    def test_four_state_alignment_cannot_average_positions(self):
        a={'order':['TRUE','FALSE','MISSING','CONFLICT'],'logits':[0,0,8,0]}
        b={'order':['CONFLICT','MISSING','FALSE','TRUE'],'logits':[0,8,0,0]}
        pred,probs=choose([a,b],['TRUE','FALSE','MISSING','CONFLICT'])
        self.assertEqual(pred,'MISSING');self.assertGreater(probs['MISSING'],.99)
        with self.assertRaises(ValueError):softmax([0,float('nan'),0,0])


if __name__=='__main__':unittest.main()
