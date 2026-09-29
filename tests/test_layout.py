import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/layout-boundary'))
from layout_study import fields,prompt_for,freeze,HERE,PRIOR,read_rows
from layout_analyze import check_equal
import layout_analyze
from verify_layout import verify
import study as prior


class LayoutTests(unittest.TestCase):
    def test_boundary_pair_native_prompts_are_identical_without_gold(self):
        for c in read_rows(PRIOR/'data/cases.jsonl'):
            for order in prior.MAPS:
                self.assertEqual(prompt_for(c,'L1',order),prompt_for(c,'L2',order))
                changed=copy.deepcopy(c);changed.update(gold='SECRET',split='SECRET',id='SECRET')
                for layout in ('L0','L1','L2'):
                    self.assertEqual(prompt_for(c,layout,order),prompt_for(changed,layout,order))
            for layout in ('L1','L2'):
                state,instruction=fields(c,layout)
                self.assertEqual((state+'\n\n'+instruction).count(c['state']),1)
                self.assertEqual((state+'\n\n'+instruction).count(c['instruction']),1)

    def test_summary_tolerance_is_float_only_and_rejects_real_changes(self):
        check_equal({'n':1,'metric':.3},{'n':1,'metric':.30000000000000004})
        for actual in ({'n':2,'metric':.3},{'n':1.,'metric':.3},{'n':1,'metric':.300001}):
            with self.assertRaises(ValueError): check_equal(actual,{'n':1,'metric':.3})

    def test_freeze_is_read_only(self):
        if not (HERE/'manifest.json').exists(): self.skipTest('Not frozen yet')
        p=HERE/'manifest.json';before=(p.read_bytes(),p.stat().st_mtime_ns)
        freeze();self.assertEqual(before,(p.read_bytes(),p.stat().st_mtime_ns))


@unittest.skipUnless((HERE/'results/summary.json').exists(),'Completed diagnostic not present')
class LayoutEvidenceTests(unittest.TestCase):
    def test_complete_offline_check_never_writes_evidence(self):
        paths=[HERE/'manifest.json',HERE/'results/summary.json']+[HERE/f'results/{a}.jsonl' for a in ('N0','N1','K1')]
        before={str(p):(p.read_bytes(),p.stat().st_mtime_ns) for p in paths}
        summary=verify()
        import json
        check_equal(summary,json.loads((HERE/'results/summary.json').read_text(encoding='utf-8')))
        self.assertEqual(before,{str(p):(p.read_bytes(),p.stat().st_mtime_ns) for p in paths})

    def test_shared_record_and_parity_corruption_are_rejected(self):
        for defect in ('sharing','parity','duplicate'):
            def broken(path):
                rows=copy.deepcopy(read_rows(path))
                if path==HERE/'results/N0.jsonl' and defect=='sharing':
                    next(r for r in rows if r['layout']=='L2')['executed_forward']=True
                if path==HERE/'results/K1.jsonl':
                    if defect=='parity': rows[0]['parity']['causal_logits']=[0.,0.,0.]
                    if defect=='duplicate': rows[0]=copy.deepcopy(rows[1])
                return rows
            with patch.object(layout_analyze,'read_rows',side_effect=broken):
                with self.assertRaises(ValueError): layout_analyze.analyze()


if __name__=='__main__':unittest.main()
