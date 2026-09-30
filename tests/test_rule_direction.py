import importlib.util
import hashlib
import json
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/'research/rule-direction/specification.py'
spec=importlib.util.spec_from_file_location('rule_direction_spec',PATH)
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)


class RuleDirectionTests(unittest.TestCase):
    def test_public_requests_match_freeze_and_exclude_answer_fields(self):
        here=PATH.parent
        manifest=json.loads((here/'manifest.json').read_bytes())
        raw=(here/'request_plan.json').read_bytes().replace(b'\r\n',b'\n')
        self.assertEqual(hashlib.sha256(raw).hexdigest(),manifest['plan_sha256'])
        plan=json.loads(raw);self.assertEqual(len(plan['jobs']),444)
        self.assertEqual(len({j['id'] for j in plan['jobs']}),444)
        lookup={r['id']:r for r in S.cases()}
        for job in plan['jobs']:
            if job['phase']!='main':continue
            self.assertIsNone(job['expected_smoke_action'])
            if job['backend']=='jev':self.assertEqual(job['request']['state'],lookup[job['item_id']]['state'])
            else:
                self.assertNotIn('possible_worlds',job['prompt'])
                self.assertNotIn('reference',job['prompt'])

    def test_witnesses_and_independent_control_cover_all_cells(self):
        rows=S.cases();self.assertEqual(len(rows),108)
        self.assertEqual(len({r['id'] for r in rows}),108)
        for r in rows:
            self.assertEqual(S.grammar_control(r['state']),r['reference'])
            if r['reference']=='maybe':self.assertEqual({w['Q'] for w in r['possible_worlds']},{False,True})
            else:self.assertEqual({w['Q'] for w in r['possible_worlds']},{r['reference']=='yes'})

    def test_direction_pairs_change_only_rule_and_have_expected_effect(self):
        for family in S.FAMILIES:
            for fact,expected in [('positive',('yes','maybe')),('negative',('maybe','no')),('unknown',('maybe','maybe'))]:
                a=S.render(family,'sufficient',fact);b=S.render(family,'necessary',fact)
                self.assertEqual(a['scenario'],b['scenario']);self.assertEqual(a['question'],b['question'])
                self.assertEqual(a['policy'].replace(' if ',' only if '),b['policy'])
                self.assertEqual((S.grammar_control(a),S.grammar_control(b)),expected)

    def test_control_rejects_unmodeled_fact_and_policy_changes(self):
        state=S.render(S.FAMILIES[0],'necessary','positive')
        with self.assertRaises(ValueError):S.grammar_control({**state,'reference':'yes'})
        with self.assertRaises(ValueError):S.grammar_control({**state,'scenario':state['scenario']+' The opposite is also true.'})
        with self.assertRaises(ValueError):S.grammar_control({**state,'policy':state['policy'].replace('only if','unless')})
        with self.assertRaises(ValueError):S.witnesses('unsupported','positive')


if __name__=='__main__':unittest.main()
