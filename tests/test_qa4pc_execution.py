import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import contextmanager

HERE=Path(__file__).resolve().parents[1]/'research/qa4pc-stage-attribution'
sys.path.insert(0,str(HERE))
import plan as qplan
import runner as qrunner
import journal as qjournal
sys.path.remove(str(HERE))


class FakeTokenizer:
    def apply_chat_template(self,messages,**kwargs): return messages[0]['content']+'\nASSISTANT:'
    def encode(self,text,**kwargs):
        if text.endswith(('ASSISTANT:A','ASSISTANT:B','ASSISTANT:C')):
            return self.encode(text[:-1])+[qplan.TOKEN_IDS[qplan.LETTERS.index(text[-1])]]
        return [100+ord(c) for c in text]


def compiled():
    t=[dict(tree_id='t',question='Eligible?',logic='Q0 AND Q1',difficult=False,
            questions={'Q0':'A?','Q1':'B?'},policy='Policy')]
    e=[dict(tree_id='t',utterance_id='u',question='Eligible?',policy='Policy',scenario='Unique scenario',answer='maybe')]
    q=[dict(tree_id='t',utterance_id='u',scenario='Unique scenario',question=question,question_id=qid,set_id=qid,answer=answer)
       for qid,question,answer in [('Q0','A?','yes'),('Q1','B?','maybe')]]
    direct={k:e[0][k] for k in ('policy','question','scenario')}
    c={'selected':[{'tree_id':'t','question_ids':['Q0','Q1'],'scenarios':[{'utterance_id':'u',
        'direct_visible_sha256':qplan.audit.digest(qplan.audit.encoded(direct))}]}]}
    return qplan.compile_grid(t,e,q,c,FakeTokenizer())


def good(action='yes'):
    return dict(status='ok',action=action,input_tokens=1,output_tokens=0,latency_seconds=0,detail={})


class QA4PCExecutionTests(unittest.TestCase):
    def test_compiler_preserves_help_contract_and_no_reference_leak(self):
        p,r,m=compiled()
        main=[j for j in p['jobs'] if j['phase']=='main' and j['backend']=='jev' and j['mapping']==0]
        self.assertEqual(len(main),5)
        for j in main:
            state=j['request']['state']
            if j['arm']=='L': self.assertEqual(set(state),{'expression','facts'})
            else:
                self.assertNotIn('facts',state);self.assertNotIn('answer',state)
                self.assertEqual(state['scenario'],'Unique scenario')
            if j['arm']=='D': self.assertEqual(set(state),{'policy','question','scenario'})
            if j['arm']=='F': self.assertIn('selected_condition_id',state)
        self.assertEqual(r[0]['label'],'maybe')
        self.assertFalse(any('scenario' in j or 'request' in j for j in m['jobs']))

    def test_readout_remapping_and_metadata_noncorrection(self):
        raw={'model':qplan.MODEL,'usage':{'input_tokens':1,'output_tokens':0},
             'answers':{'decision':{'type':'choice','choice':'A','probabilities':{'A':.2,'B':.4,'C':.39},'confidence':.2}}}
        for options in qplan.ORDERS:
            r=qrunner.adapt_jev(raw,200,options,0)
            self.assertEqual(r['action'],options[0]);self.assertEqual(r['status'],'ok')
            self.assertFalse(r['detail']['metadata_quality']['choice_is_displayed_argmax'])
            self.assertAlmostEqual(r['detail']['metadata_quality']['raw_sum'],.99)
        raw['answers']['decision']['choice']='D'
        self.assertEqual(qrunner.adapt_jev(raw,200,qplan.ORDERS[0],0)['status'],'protocol_error')
        raw['answers']['decision']['choice']='A';raw['usage']['input_tokens']=True
        self.assertEqual(qrunner.adapt_jev(raw,200,qplan.ORDERS[0],0)['status'],'protocol_error')

    def test_logits_ties_mass_mapping_and_impossible_values(self):
        values=[1.,2.,3.];norm=math.log(sum(math.exp(x) for x in values)+1)
        for options in qplan.ORDERS:
            r=qrunner.extract(values,norm,34,3.,options)
            self.assertEqual(r['action'],options[2]);self.assertLess(r['full_vocabulary_candidate_mass'],1)
        self.assertIsNone(qrunner.extract([1.,3.,3.],math.log(math.exp(1)+2*math.exp(3)),34,3.,qplan.ORDERS[0])['action'])
        for invalid in [float('nan'),float('inf')]:
            with self.assertRaises(ValueError): qrunner.extract([1.,2.,invalid],norm,34,3.,qplan.ORDERS[0])
        with self.assertRaises(ValueError):qrunner.extract(values,1.,34,3.,qplan.ORDERS[0])

    def test_journal_resume_counts_and_unresolved_attempt_rejected(self):
        p={'jobs':[{'id':'one','backend':'jev'}],'limits':dict(qplan.LIMITS)}
        calls=[]
        @contextmanager
        def factory():
            def call(job,remaining):calls.append(job['id']);return good('maybe')
            yield call,{}
        with tempfile.TemporaryDirectory() as temp:
            a=qjournal.execute(temp,p,'hash','jev',factory)
            b=qjournal.execute(temp,p,'hash','jev',factory)
            self.assertEqual(a['status'],'complete');self.assertEqual(b['status'],'complete');self.assertEqual(calls,['one'])
            path=Path(temp)/'jev.jsonl';events=qjournal.read_events(path)
            pending=events[:3]
            state=qjournal.replay(pending,plan_hash='hash',backend='jev',jobs=p['jobs'])
            self.assertEqual(qjournal.stop_reason(state,'jev',p['jobs'],p['limits'],0),'unresolved_interruption')
            with self.assertRaises(ValueError):qjournal.replay(events,plan_hash='different',backend='jev',jobs=p['jobs'])

    def test_smoke_and_unknown_usage_stop_without_retries(self):
        result=qrunner.smoke_gate({'phase':'smoke','expected_smoke_action':'yes'},good('no'))
        self.assertEqual(result['status'],'protocol_error');self.assertIsNone(result['action'])
        p={'jobs':[{'id':'one','backend':'jev'},{'id':'two','backend':'jev'}],'limits':dict(qplan.LIMITS)}
        @contextmanager
        def factory():
            yield lambda job,remaining:{'status':'execution_error','action':None,'input_tokens':None,
                'output_tokens':None,'latency_seconds':0,'detail':{}},{}
        with tempfile.TemporaryDirectory() as temp:
            r=qjournal.execute(temp,p,'hash','jev',factory)
            self.assertEqual(len(r['state']['started']),1)
            self.assertEqual(r['status'],'recorded_failure_requires_repair')


if __name__=='__main__':unittest.main()
