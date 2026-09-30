import math
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/finite-choice-readout'))
import finite_readout as finite


class FakeTokenizer:
    """Character encoder for compiler tests only; not model tokenization evidence."""
    def encode(self,text,add_special_tokens=False):
        return [finite.TOKEN_IDS[finite.LETTERS.index(c)] if c in finite.LETTERS else ord(c)+100 for c in text]
    def apply_chat_template(self,messages,**kwargs):
        return messages[0]['content']+'\nassistant\n'


class FiniteReadoutTests(unittest.TestCase):
    def test_conditional_confidence_is_not_full_vocabulary_mass(self):
        x=finite.extract([10.,0.,0.,0.],20.,99,19.,finite.ORDERS[0])
        self.assertGreater(x['conditional_probabilities']['A'],.999)
        self.assertLess(x['full_vocabulary_candidate_mass'],.0001)
        self.assertFalse(x['unconstrained_top_is_candidate'])
        self.assertEqual(x['action'],'Yes')
        shifted=finite.extract([110.,100.,100.,100.],120.,99,119.,finite.ORDERS[0])
        self.assertAlmostEqual(x['full_vocabulary_candidate_mass'],shifted['full_vocabulary_candidate_mass'])
        self.assertEqual(x['conditional_probabilities'],shifted['conditional_probabilities'])

    def test_mapping_and_tie_are_explicit(self):
        a=finite.extract([2.,1.,0.,-1.],3.,32,2.,finite.ORDERS[0])
        b=finite.extract([2.,1.,0.,-1.],3.,32,2.,finite.ORDERS[1])
        self.assertEqual((a['action'],b['action']),('Yes','ASK'))
        tie=finite.extract([2.,2.,0.,0.],4.,32,2.,finite.ORDERS[0])
        self.assertTrue(tie['exact_tie']);self.assertIsNone(tie['action'])

    def test_nonfinite_or_impossible_metadata_rejected(self):
        for values,norm,tid,top in [([math.nan,0,0,0],4,32,2),([2,1,0,0],1,32,2),
                                   ([2,1,0,0],4,32,3),([2,2,2,2],2,32,2)]:
            with self.assertRaises(ValueError):finite.extract(values,norm,tid,top,finite.ORDERS[0])

    def test_compiler_has_smoke_first_and_same_visible_cohort(self):
        # A character encoder is deliberately longer than the real tokenizer;
        # relax only this synthetic fixture's token limit, never the real plan.
        with patch.dict(finite.LIMITS,local_input_tokens=500000):
            p=finite.build(FakeTokenizer(),[])
            repeated=finite.build(FakeTokenizer(),[])
        self.assertEqual(len(p['jobs']),56)
        self.assertEqual([j['phase'] for j in p['jobs'][:8]],['smoke']*8)
        mains=p['jobs'][8:]
        self.assertEqual(len({j['item_id'] for j in mains}),24)
        self.assertTrue(all(j['expected_smoke_action'] is None and j['max_new_tokens']==0 for j in mains))
        self.assertTrue(all(set(j['state'])=={'snippet','question','scenario','history'} for j in mains))
        self.assertEqual({j['condition'] for j in mains},{'prefill_order0','prefill_order1'})
        self.assertEqual(p,repeated)


if __name__=='__main__':unittest.main()
