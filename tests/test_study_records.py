import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/next-study'))
import analyze_study
from study import HERE,read_rows
from verify_study import verify


@unittest.skipUnless((HERE/'results/N0.jsonl').exists(),'Completed pilot records not yet present')
class StudyRecordTests(unittest.TestCase):
    def test_bad_logits_and_foreign_token_sequence_are_rejected(self):
        for defect in ('logits','token_ids'):
            def broken(path):
                rows=copy.deepcopy(read_rows(path))
                if path.name=='N1.jsonl':
                    if defect=='logits':
                        rows[0]['logits']=[0.,0.,0.]
                    else:
                        rows[0]['token_ids'][0]+=1
                return rows
            with patch.object(analyze_study,'read_rows',side_effect=broken):
                with self.assertRaises(ValueError):
                    verify()

    def test_duplicate_or_missing_scientific_record_is_rejected(self):
        def duplicate(path):
            rows=copy.deepcopy(read_rows(path))
            if path.name=='K1.jsonl':
                rows[0]=copy.deepcopy(rows[1])
            return rows
        with patch.object(analyze_study,'read_rows',side_effect=duplicate):
            with self.assertRaisesRegex(ValueError,'incomplete or duplicate'):
                verify()

    def test_verification_leaves_evidence_and_manifest_untouched(self):
        paths=[HERE/'manifest.json',HERE/'results/summary.json']+[HERE/f'results/{a}.jsonl' for a in ('N0','N1','K1')]
        before={str(p):(p.stat().st_mtime_ns,p.read_bytes()) for p in paths}
        verify()
        self.assertEqual(before,{str(p):(p.stat().st_mtime_ns,p.read_bytes()) for p in paths})


if __name__=='__main__':unittest.main()
