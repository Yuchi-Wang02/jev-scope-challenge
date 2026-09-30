import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('qa4pc_cohort', Path(__file__).resolve().parents[1] / 'research/qa4pc-stage-attribution/cohort.py')
cohort = importlib.util.module_from_spec(spec); spec.loader.exec_module(cohort)


def fixture():
    trees = [dict(tree_id=f't{i}', policy=f'P{i}', questions={'Q0': 'A?'}) for i in range(4)]
    rows = [dict(tree_id=t['tree_id'], utterance_id=f"{t['tree_id']}-{j}",
                 policy=t['policy'], question='Main?', scenario=f'S{j}', answer='yes')
            for t in trees for j in range(3)]
    return trees, rows


class QA4PCCohortTests(unittest.TestCase):
    def test_selection_independent_of_row_order_and_labels(self):
        t,r = fixture(); a = cohort.choose(t,r,{},2,2)
        b = cohort.choose(list(reversed(t)),list(reversed(r)),{},2,2)
        self.assertEqual(a,b)
        changed = [{**x,'answer':'maybe'} for x in r]
        self.assertEqual(a['selected'],cohort.choose(t,changed,{},2,2)['selected'])

    def test_whole_tree_exclusion_and_union_counts(self):
        t,r = fixture(); x = cohort.choose(t,r,{'seen':{'t0'},'queue':{'t0','t1'}},2,2)
        self.assertEqual({p['tree_id'] for p in x['selected']},{'t2','t3'})
        self.assertEqual(x['excluded_union_trees'],2)
        self.assertEqual(x['excluded_union_scenarios'],6)
        self.assertEqual(x['selected_question_decisions_per_model_mapping'],4)
        self.assertEqual(x['selected_scenarios'],4)

    def test_duplicates_insufficient_data_and_duplicate_policies_reject(self):
        t,r = fixture()
        with self.assertRaises(ValueError): cohort.choose(t,r,{'all':{'t0','t1','t2'}},2,2)
        with self.assertRaises(ValueError): cohort.choose(t,r+[r[0]],{},2,2)
        t[1]['policy']=t[0]['policy']
        with self.assertRaises(ValueError): cohort.choose(t,r,{},2,2)


if __name__ == '__main__': unittest.main()
