import importlib.util
import json
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'research/qa4pc-answer-interface'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
cohort=load('answer_interface_cohort_tests','cohort.py')
readout=load('answer_interface_readout_tests','readout.py')
observations=load('answer_interface_observations_tests','observations.py')


class AnswerInterfaceTests(unittest.TestCase):
    def test_published_journals_cover_each_job_once_and_match_report(self):
        folder=ROOT/'research/qa4pc-answer-interface'
        report_path=folder/'report.json'
        if not report_path.exists():self.skipTest('Results not published at execution freeze')
        report=json.loads(report_path.read_bytes());manifest=json.loads((folder/'plan_manifest.json').read_bytes())
        results={}
        for backend in ('jev','qwen'):
            events=[json.loads(s) for s in (folder/'results'/f'{backend}.jsonl').read_text().splitlines()]
            jobs=[j for j in manifest['jobs'] if j['backend']==backend]
            self.assertEqual([e['job_id'] for e in events if e['event']=='call_start'],[j['id'] for j in jobs])
            finishes=[e for e in events if e['event']=='call_finish']
            self.assertEqual([e['job_id'] for e in finishes],[j['id'] for j in jobs])
            self.assertEqual(events[-1]['event'],'session_end')
            results.update({e['job_id']:e['result'] for e in finishes})
            for field in ('input_tokens','output_tokens'):
                self.assertEqual(sum(e['result'][field] for e in finishes),report['cost'][backend][field])
        for row in report['observations']:
            self.assertTrue(row['executed']);self.assertEqual(row['action'],results[row['job_id']]['action'])
        for j in manifest['jobs']:
            if j['arm']=='finite':
                d=results[j['id']]['detail']
                bridge=results[j['id'].removesuffix('_finite')+'_letter']['detail']
                self.assertEqual(d['first_candidate_logits'],bridge['first_candidate_logits'])
                if not d['first_letter_readout']['exact_tie']:
                    self.assertEqual(d['first_letter_readout']['action'],bridge['generated']['action'])
        for arm,summary in report['strict_majority'].items():
            self.assertEqual(sum(readout.strict_majority(item['actions']) is None for item in summary['items'].values()),summary['abstentions'])

    def test_compiled_inputs_do_not_depend_on_reference_label(self):
        compiler=load('answer_interface_compiler_tests','compile_plan.py')
        class Tokenizer:
            def apply_chat_template(self,messages,**kwargs):return messages[0]['content']+'\nASSISTANT:'
            def encode(self,text,**kwargs):
                if text.endswith(('ASSISTANT:A','ASSISTANT:B','ASSISTANT:C')):
                    return self.encode(text[:-1])+[32+'ABC'.index(text[-1])]
                return [100+ord(c) for c in text]
        row={'tree_id':'t','utterance_id':'u','policy':'A policy','question':'A question','scenario':'A scenario','answer':'yes'}
        state={k:row[k] for k in ('policy','question','scenario')}
        selection={'selected':[{'tree_id':'t','scenarios':[{'utterance_id':'u',
            'direct_visible_sha256':cohort.audit.digest(cohort.audit.encoded(state))}]}]}
        a,refs,_=compiler.compile_grid([row],selection,Tokenizer())
        b,new_refs,_=compiler.compile_grid([{**row,'answer':'no'}],selection,Tokenizer())
        self.assertEqual(a,b);self.assertNotEqual(refs,new_refs)
        for j in a['jobs']:
            if j['backend']=='jev':self.assertEqual(set(j['request']['state']),{'policy','question','scenario'})
        import ast
        previous=ast.parse((ROOT/'research/qa4pc-stage-attribution/plan.py').read_text(encoding='utf-8'))
        old_rule=next(ast.literal_eval(n.value) for n in previous.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RULE' for t in n.targets))
        self.assertEqual(compiler.RULE,old_rule)

    def test_public_grid_covers_six_permutations_and_exact_letter_bridge(self):
        manifest=json.loads((ROOT/'research/qa4pc-answer-interface/plan_manifest.json').read_bytes())
        jobs=manifest['jobs'];self.assertEqual(len(jobs),648)
        self.assertEqual(len({j['id'] for j in jobs}),648)
        self.assertEqual(sum(j['backend']=='jev' for j in jobs),162)
        self.assertEqual(sum(j['backend']=='qwen' for j in jobs),486)
        for uid in {j['item_id'] for j in jobs if j['phase']=='main'}:
            for arm in ('native','finite','letter','semantic'):
                part=[j for j in jobs if j['item_id']==uid and j['arm']==arm]
                self.assertEqual({tuple(j['options']) for j in part},set(readout.ORDERS))
                self.assertEqual(len(part),6)
        lookup={j['id']:j for j in jobs}
        for j in jobs:
            if j['arm']=='finite':
                bridge=lookup[j['id'].removesuffix('_finite')+'_letter']
                self.assertEqual(j['input_ids_sha256'],bridge['input_ids_sha256'])
                self.assertEqual(j['input_tokens'],bridge['input_tokens'])
        self.assertEqual(sum(j['input_tokens'] or 0 for j in jobs),manifest['planned_local_input_tokens'])

    def test_native_and_logit_mapping_all_six_and_retained_anomalies(self):
        raw={'model':observations.MODEL,'usage':{'input_tokens':1,'output_tokens':0},
            'answers':{'decision':{'type':'choice','choice':'A','probabilities':{'A':.2,'B':.4,'C':.39},'confidence':.2}}}
        for order in readout.ORDERS:
            r=observations.adapt_jev(raw,200,order,0)
            self.assertEqual(r['action'],order[0]);self.assertEqual(r['status'],'ok')
            self.assertFalse(r['detail']['metadata_quality']['normalization_applied'])
            self.assertAlmostEqual(r['detail']['metadata_quality']['raw_sum'],.99)
            self.assertEqual(observations.extract([1,2,3],math.log(sum(math.exp(x) for x in (1,2,3))+1),34,3,order)['action'],order[2])
        self.assertIsNone(observations.extract([1,3,3],math.log(math.exp(1)+2*math.exp(3)),34,3,readout.LABELS)['action'])
        raw['model']='unexpected-version'
        self.assertEqual(observations.adapt_jev(raw,200,readout.LABELS,0)['status'],'protocol_error')

    def test_selection_ignores_labels_input_order_and_excludes_whole_tree(self):
        trees=[{'tree_id':str(i),'policy':f'P{i}'} for i in range(5)]
        rows=[{**t,'utterance_id':f"{t['tree_id']}-{j}",'question':'Q','scenario':f'S{j}','answer':'yes'} for t in trees for j in range(3)]
        a=cohort.choose(trees,rows,{'old':{'0'},'queue':{'1'}},2,2)
        b=cohort.choose(trees[::-1],[{**r,'answer':'no'} for r in rows[::-1]],{'old':{'0'},'queue':{'1'}},2,2)
        self.assertEqual(a['selected'],b['selected'])
        self.assertFalse({'0','1'} & {t['tree_id'] for t in a['selected']})
        self.assertEqual(a['eligible_trees'],3)
        with self.assertRaises(ValueError):cohort.choose(trees,rows+rows[:1],{},2,2)
        with self.assertRaises(ValueError):cohort.choose(trees,rows,{'all':set('01234')},2,2)

    def test_generated_contract_preserves_invalid_and_never_mines_label(self):
        for order in readout.ORDERS:
            for letter,label in zip('ABC',order):
                self.assertEqual(readout.parse_generated(' '+letter+'\n',arm='letter',options=order,ended_eos=True)['action'],label)
                self.assertEqual(readout.parse_generated(label,arm='semantic',options=order,ended_eos=True)['action'],label)
        for text in ('YES','yes.','The answer is yes.','{"action":"yes"}','yes no',''):
            self.assertIsNone(readout.parse_generated(text,arm='semantic',options=readout.LABELS,ended_eos=True)['action'])
        for kwargs in ({'ended_eos':False},{'ended_eos':True,'unsupported_special':True}):
            self.assertIsNone(readout.parse_generated('yes',arm='semantic',options=readout.LABELS,**kwargs)['action'])

    def test_majority_does_not_treat_invalid_as_maybe_or_shrink_denominator(self):
        self.assertIsNone(readout.strict_majority(['yes']*3+[None]*3))
        self.assertIsNone(readout.strict_majority(['yes']*3+['no']*3))
        self.assertEqual(readout.strict_majority(['maybe']*4+[None]*2),'maybe')
        with self.assertRaises(ValueError):readout.strict_majority(['yes']*5)


if __name__=='__main__':unittest.main()
