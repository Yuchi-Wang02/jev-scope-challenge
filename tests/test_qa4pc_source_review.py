import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'research/qa4pc-answer-interface'
spec=importlib.util.spec_from_file_location('review_validator_test',HERE/'validate_review.py')
validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)


def fixture():
    packet={'packet_sha256':'fixture','slot':'A','items':[{'review_id':'one'},{'review_id':'two'}]}
    reviewer={'name':'TEST FIXTURE NOT HUMAN','relationship':'software test','process_notes':'synthetic test'}
    reviewer.update({k:'no' for k in validator.PROCESS})
    payload={'schema_version':1,'packet_sha256':'fixture','slot':'A','submission_type':'completed',
        'exported_at_client':'2026-09-30T00:00:00Z','reviewer':reviewer,
        'responses':[{'review_id':i,'judgment':'maybe','evidence':'Synthetic fixture only.',
            'ambiguity':'unsure','missing_information':'','notes':''} for i in ('one','two')]}
    return packet,payload


class SourceReviewTests(unittest.TestCase):
    def test_audit_is_exhaustive_and_does_not_replace_scores(self):
        c=json.loads((HERE/'cohort.json').read_bytes());a=json.loads((HERE/'source_audit.json').read_bytes())
        expected=[r['utterance_id'] for t in c['selected'] for r in t['scenarios']]
        self.assertEqual([r['item_id'] for r in a['items']],expected)
        self.assertEqual(len(set(expected)),24)
        self.assertEqual(a['reference_updates'],0);self.assertFalse(a['rescored_or_filtered_metrics'])
        for name,sha in a['input_hashes_lf'].items():
            self.assertEqual(hashlib.sha256((HERE/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),sha)
        self.assertEqual(sum(not r['final_flags'] for r in a['items']),a['no_specific_final_flag_in_this_pass'])

    def test_valid_submission_never_certifies_human_independence(self):
        p,r=fixture();out=validator.validate(r,p)
        self.assertEqual(out['completed_items'],2)
        self.assertTrue(out['process_self_report_no_exposure_or_assistance'])
        self.assertFalse(out['human_identity_or_independence_verified'])
        r['reviewer']['used_ai']='yes';r['reviewer']['process_notes']=''
        out=validator.validate(r,p)
        self.assertFalse(out['process_self_report_no_exposure_or_assistance'])
        self.assertTrue(out['process_explanation_needed'])

    def test_missing_duplicate_foreign_and_incomplete_records_reject(self):
        p,base=fixture()
        for change in ('missing','duplicate','foreign','empty_evidence','bad_label','bad_slot','incomplete_process'):
            r=copy.deepcopy(base)
            if change=='missing':r['responses'].pop()
            if change=='duplicate':r['responses'][1]=r['responses'][0]
            if change=='foreign':r['responses'][0]['review_id']='unknown'
            if change=='empty_evidence':r['responses'][0]['evidence']=' '
            if change=='bad_label':r['responses'][0]['judgment']='YES'
            if change=='bad_slot':r['slot']='B'
            if change=='incomplete_process':r['reviewer']['seen_source_labels']=''
            with self.subTest(change=change),self.assertRaises(ValueError):validator.validate(r,p)
        with self.assertRaises(ValueError):json.loads('{"a":1,"a":2}',object_pairs_hook=validator.unique_object)

    def test_draft_keeps_missingness_and_is_not_promoted(self):
        p,r=fixture();r['submission_type']='draft';r['responses'][0]['judgment']=''
        r['reviewer']['seen_model_summaries']=''
        out=validator.validate(r,p)
        self.assertEqual(out['completed_items'],1);self.assertFalse(out['process_record_complete'])
        self.assertEqual(out['submission_type'],'draft');self.assertEqual(out['reference_updates'],0)


if __name__=='__main__':unittest.main()
