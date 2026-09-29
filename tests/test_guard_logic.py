import copy
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/evidence-guards'))
from guards import parse_visible,gates,decide
from gap_data import render


def case(family,records):
    c={'family':family,'target':'request-X','sites':['site-A','site-B'],'style':0,'records':records}
    state,policy=render(c)
    return parse_visible(state,policy)


def rec(field,value,scope='request-X'):return {'scope':scope,'field':field,'value':value}


class GuardLogicTests(unittest.TestCase):
    def test_explicit_rejection_makes_missing_approval_redundant(self):
        schema,policy=gates(case('joint_approval',[rec('review_b',False)]))
        self.assertFalse(schema['may_commit']);self.assertTrue(policy['may_commit'])
        self.assertEqual(policy['certificate_fields'],['review_b'])

    def test_route_checks_selected_site_and_agreement_across_possible_routes(self):
        schema,policy=gates(case('route_lookup',[rec('route',True),rec('site_b',True)]))
        self.assertFalse(schema['may_commit']);self.assertTrue(policy['may_commit'])
        for b,want in ((True,True),(False,False)):
            schema,policy=gates(case('route_lookup',[rec('site_a',True),rec('site_b',b)]))
            self.assertFalse(schema['may_commit']);self.assertEqual(policy['may_commit'],want)

    def test_other_request_does_not_fill_target_or_override_conflict(self):
        _,p=gates(case('joint_approval',[rec('review_a',True),rec('review_b',True,'other-X')]))
        self.assertFalse(p['may_commit'])
        _,p=gates(case('joint_approval',[rec('review_b',False),rec('review_b',True)]))
        self.assertFalse(p['may_commit']);self.assertEqual(p['reason'],'target_schema_conflict')

    def test_reserved_composed_and_unknown_grammar_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'reserved'):
            case('composed_route',[rec('route',True)])
        with self.assertRaises(ValueError):parse_visible('unknown','unknown')

    def test_policy_gate_never_repairs_a_wrong_action_or_forces_abstention_to_action(self):
        schema,policy=gates(case('joint_approval',[rec('review_a',True),rec('review_b',True)]))
        self.assertEqual(decide('DENY',[.1,.8,.1],['ALLOW','DENY','INSUFFICIENT'],schema,policy,'policy_determinacy')['prediction'],'DENY')
        self.assertEqual(decide('INSUFFICIENT',[.1,.1,.8],['ALLOW','DENY','INSUFFICIENT'],schema,policy,'policy_determinacy')['prediction'],'INSUFFICIENT')


if __name__=='__main__':unittest.main()
