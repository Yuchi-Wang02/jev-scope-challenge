import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import contextmanager

HERE=Path(__file__).resolve().parents[1]/'research/qa4pc-stage-attribution'
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('qa4pc_continuation',HERE/'continuation.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
import journal
sys.path.remove(str(HERE))


class ContinuationTests(unittest.TestCase):
    def test_amendment_only_changes_internal_phase_not_model_input(self):
        seen=[]
        def call(job,remaining):
            seen.append(job)
            return {'status':'ok','action':'maybe','detail':{},'input_tokens':3,'output_tokens':0,'latency_seconds':0}
        job={'id':'s','phase':'smoke','expected_smoke_action':'no','input_ids':[1,2,3],'prompt':'unchanged'}
        r=c.amended_call(call,job,10)
        self.assertEqual(r['status'],'ok');self.assertEqual(r['action'],'maybe')
        self.assertFalse(r['detail']['amended_smoke_policy']['correct'])
        self.assertEqual(seen[0]['input_ids'],job['input_ids']);self.assertEqual(seen[0]['prompt'],job['prompt'])
        self.assertEqual(job['phase'],'smoke');self.assertEqual(seen[0]['phase'],'diagnostic_smoke')
        main={**job,'phase':'main'};c.amended_call(call,main,10);self.assertIs(seen[-1],main)

    def test_structural_failure_is_never_promoted(self):
        def broken(job,remaining):return {'status':'protocol_error','action':None,'detail':{'error':'nonfinite'}}
        r=c.amended_call(broken,{'phase':'smoke','expected_smoke_action':'no'},1)
        self.assertEqual(r['status'],'protocol_error');self.assertIsNone(r['action'])

    def test_exact_suffix_and_resolved_stop_required(self):
        jobs=[{'id':f'j{i}','backend':'qwen','phase':'smoke' if i<6 else 'main',
               'expected_smoke_action':'maybe' if i==0 else 'no','options':['yes','no','maybe'],
               'input_ids':[1]*(189 if i<2 else 291 if i<261 else 1781),'max_new_tokens':0} for i in range(262)]
        limits={**c.LIMITS,'local_generations':262,'local_input_tokens':77528}
        parent={'jobs':jobs,'limits':limits};ph=c.audit.digest(c.readable(parent));count=[0]
        @contextmanager
        def factory():
            def call(job,remaining):
                parsed=c.extract([1.,2.,3.],4.,34,3.,job['options']);count[0]+=1
                d={'candidate_logits':[1.,2.,3.],'full_logsumexp':4.,'top_token_id':34,'top_logit':3.,'physical_forwards':1,'parsed':parsed}
                if count[0]==2:d.update(smoke_gate_failed=True,smoke_observed_action='maybe')
                return {'status':'ok' if count[0]==1 else 'protocol_error','action':'maybe' if count[0]==1 else None,
                    'input_tokens':189,'output_tokens':0,'latency_seconds':0,'detail':d}
            yield call,{}
        with tempfile.TemporaryDirectory() as temp:
            journal.execute(temp,parent,ph,'qwen',factory)
            events=journal.read_events(Path(temp)/'qwen.jsonl')
            successor=c.make_plan(parent,events)
            self.assertEqual(successor['jobs'],jobs[2:]);self.assertEqual(len(successor['jobs']),260)
            self.assertEqual(sum(len(j['input_ids']) for j in successor['jobs']),77150)
            with self.assertRaises(ValueError):c.predecessor(parent,events[:-1])
            with self.assertRaises(ValueError):c.predecessor(parent,[])


if __name__=='__main__':unittest.main()
