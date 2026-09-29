import copy
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research/evidence-gap'))
from gap_methods import readout,softmax
from gap_run import null_text,development_plans,read_rows,HERE
from gap_data import build_rows


class GapMethodTests(unittest.TestCase):
    def test_ensemble_maps_semantic_labels_instead_of_slot_indices(self):
        a={'id':'x','parent':'p','mapping':0,'order':['ALLOW','DENY','INSUFFICIENT'],'logits':[3.,0.,0.],'forward_id':'a'}
        b={'id':'x','parent':'p','mapping':1,'order':['DENY','INSUFFICIENT','ALLOW'],'logits':[0.,0.,3.],'forward_id':'b'}
        null={**a,'id':'p-null','logits':[0.,0.,0.],'forward_id':'n'}
        r=readout(a,null,b,'two_order')
        self.assertEqual(r['prediction'],'ALLOW');self.assertAlmostEqual(r['scores']['ALLOW'],softmax(a['logits'])[0])
        self.assertEqual(r['nominal_calls'],2)

    def test_null_control_ignores_truth_and_removed_key_metadata(self):
        row=build_rows()[0];changed=copy.deepcopy(row)
        changed.update(gold='SECRET',legal_worlds=999,variant='SECRET',records=[],split='reserved_test')
        self.assertEqual(null_text(row),null_text(changed))
        self.assertNotIn('SECRET',null_text(changed)[0])

    def test_reserved_plans_cannot_be_smuggled_into_development(self):
        plans=read_rows(HERE/'data/inputs.jsonl')
        if not plans:self.skipTest('Not encoded yet')
        self.assertEqual(len(development_plans(plans)),252)
        altered=copy.deepcopy(plans);next(p for p in altered if p['family']=='composed_route')['split']='development'
        with self.assertRaises(ValueError):development_plans(altered)


if __name__=='__main__':unittest.main()
