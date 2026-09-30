"""Read-only consistency checks of real records, both freezes and public history."""
import json
import subprocess
import zipfile
from study import ROOT, REPO, rows, canonical, read, sha, verify_freeze
from run_api_v02 import verify_execution
from report import summarize
from publish_v02 import publish
from review_pair import compare as verify_review

def verify():
    verify_freeze();verify_execution();publish(True);review_status=verify_review()
    assert read(ROOT/'review/comparison.json')==review_status
    records=rows(ROOT/'results/responses.jsonl');events=rows(ROOT/'results/attempts.jsonl')
    summary=summarize()
    assert summary['status']=='completed' and len(records)==198
    assert summary['smoke']=={'recorded':6,'correct':5}
    assert summary['continuation']=='STOP_NO_FOLLOWUP'
    assert all(m['correct']==48 for m in summary['metrics'].values())
    starts=[r for r in events if r['event']=='started'];ends=[r for r in events if r['event']=='finished']
    assert len(starts)==len(ends)==len(records)==198
    assert {r['attempt_id'] for r in starts}=={r['attempt_id'] for r in ends}=={r['attempt_id'] for r in records}
    assert all(r['execution_protocol']=='EXECUTION_V02.md' for r in records if r['phase']=='primary')
    freeze_old=json.loads(subprocess.check_output(['git','show','0569f8d:research/payment-ownership/freeze.json'],cwd=REPO))
    assert freeze_old==read(ROOT/'freeze.json')
    old=subprocess.check_output(['git','show','08fdda6:research/payment-ownership/results/responses.jsonl'],cwd=REPO).decode()
    assert [json.loads(line) for line in old.splitlines()]==records[:6]
    amendment=json.loads(subprocess.check_output(['git','show','08fdda6:research/payment-ownership/execution_v02.json'],cwd=REPO))
    assert amendment==read(ROOT/'execution_v02.json')
    assert amendment['created_at_utc']<min(r['ts_utc'] for r in starts if r['phase']=='primary')
    jobs={r['job_id']:r for r in rows(ROOT/'plans/primary.jsonl')}
    for start,end in zip(starts,ends):
        assert start['attempt_id']==end['attempt_id'] and start['job_id']==end['job_id']
        job=jobs[start['job_id']]
        assert start['request_sha256']==sha(canonical(job['body']).encode())
        assert start['planned_input_units']==job['planned_input_units']
    assert summary['accounting']['known_input_tokens']==sum(r['input_tokens'] for r in records)==245241
    with zipfile.ZipFile(ROOT/'review/review_package.zip') as package:
        assert set(package.namelist())=={'README.md','inputs.jsonl','reviewer_A.csv','reviewer_B.csv','review.html'}
        for name in package.namelist():
            assert package.read(name).replace(b'\r\n',b'\n')==(ROOT/'review'/name).read_bytes().replace(b'\r\n',b'\n')
    return {'status':'passed','actual_requests':198,'main_correct':192,'smoke_correct':5,
            'source_freeze':'0569f8d','execution_amendment':'08fdda6','followup_calls':0,
            'author_review_items':review_status['author_review_items'],
            'non_author_review_submissions':review_status['non_author_review_submissions'],
            'adjudicated_reference_updates':0,
            'scope':'Artifact consistency, not independent model replication or label validity'}

if __name__=='__main__':print(json.dumps(verify(),indent=2))
