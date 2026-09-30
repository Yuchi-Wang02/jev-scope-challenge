import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]/'research/qa4pc-stage-attribution'
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('qa4pc_analyze',HERE/'analyze.py')
analyze=importlib.util.module_from_spec(spec);spec.loader.exec_module(analyze)
sys.path.remove(str(HERE))
from test_qa4pc_execution import compiled


class QA4PCResultTests(unittest.TestCase):
    def test_no_outputs_is_not_zero_accuracy_or_model_invalidity(self):
        p,r,_=compiled()
        with tempfile.TemporaryDirectory() as temp:
            paths={b:Path(temp)/(b+'.jsonl') for b in ('jev','qwen')}
            report=analyze.summarize(p,r,paths)
        for key in ('jev_mapping0_D','qwen_mapping1_F','qwen_mapping0_facts'):
            m=report['metrics'][key]
            self.assertIsNone(m['correct']);self.assertEqual(m['evaluated'],0)
            self.assertEqual(m['invalid'],0);self.assertEqual(m['unexecuted'],m['total'])
        self.assertFalse(report['transitions']['qwen_mapping0']['comparison_available'])
        self.assertIsNone(report['transitions']['qwen_mapping0']['G_to_F_improved'])
        self.assertEqual(report['order_sensitivity']['qwen_D']['invalid_either'],0)
        self.assertEqual(report['order_sensitivity']['qwen_D']['unexecuted_either'],1)

    def test_tolerance_only_applies_to_finite_floats(self):
        self.assertTrue(analyze.equivalent({'sum':1.0},{'sum':.9999999999999999}))
        self.assertFalse(analyze.equivalent({'action':'yes'},{'action':'no'}))
        self.assertFalse(analyze.equivalent(1,True))
        self.assertFalse(analyze.equivalent(1.0,1.01))
        self.assertFalse(analyze.equivalent(float('nan'),float('nan')))


if __name__=='__main__':unittest.main()
