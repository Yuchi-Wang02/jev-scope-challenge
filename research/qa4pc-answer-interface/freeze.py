"""Commit-checkable execution freeze; verification performs no model forwards."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from compile_plan import ROOT,HERE,CACHE,readable,lfhash,audit,preserve
from generation_config import audit_config


def source_pins():
    files=[HERE/n for n in ('cohort.py','compile_plan.py','observations.py','readout.py',
        'generation_config.py','runner.py','freeze.py','cohort.json','DESIGN.md',
        'PROTOCOL.md','generation_audit.json')]
    files+=list((ROOT/'research/external-validation').glob('*.py'))
    files += [ROOT/p for p in ('research/qa4pc-stage-attribution/journal.py',
        'research/action-backends/adapters.py','research/qa4pc-audit/audit.py',
        'research/payment-ownership/run_api_v02.py','research/payment-ownership/study.py',
        'research/baseline-readiness/qwen35-smoke-repaired/run.json')]
    return {p.relative_to(ROOT).as_posix():lfhash(p) for p in sorted(set(files))}


def prepare(source_dir,model_dir):
    subprocess.run([sys.executable,'-X','utf8',str(HERE/'compile_plan.py'),'verify',
        '--source-dir',str(source_dir),'--model-dir',str(model_dir)],cwd=ROOT,check=True,capture_output=True)
    configuration=audit_config(model_dir)
    preserve(HERE/'generation_audit.json',readable(configuration))
    manifest=json.loads((HERE/'plan_manifest.json').read_bytes())
    record={'study':manifest['study'],'plan_sha256':manifest['plan_sha256'],
        'manifest_sha256':lfhash(HERE/'plan_manifest.json'),'source_hashes_lf':source_pins(),
        'status_at_freeze':'zero calls; execution allowed only after clean committed verification'}
    preserve(HERE/'freeze.json',readable(record))
    return record


def verify(source_dir,model_dir):
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip():raise ValueError('Need clean committed freeze')
    saved=json.loads((HERE/'freeze.json').read_bytes())
    if saved['source_hashes_lf']!=source_pins():raise ValueError('Frozen source drift')
    for name in ('freeze.json','plan_manifest.json'):
        raw=subprocess.check_output(['git','show','HEAD:'+(HERE/name).relative_to(ROOT).as_posix()],cwd=ROOT)
        if raw.replace(b'\r\n',b'\n')!=(HERE/name).read_bytes().replace(b'\r\n',b'\n'):raise ValueError('Uncommitted artifact')
    if prepare(source_dir,model_dir)!=saved:raise ValueError('Freeze recomputation mismatch')
    plan=json.loads((CACHE/'plan.json').read_bytes());manifest=json.loads((HERE/'plan_manifest.json').read_bytes())
    if audit.digest(readable(plan))!=saved['plan_sha256']:raise ValueError('Private plan mismatch')
    return plan,manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','verify'))
    p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--model-dir',type=Path,required=True)
    a=p.parse_args()
    if a.command=='prepare':record=prepare(a.source_dir,a.model_dir)
    else:_,record=verify(a.source_dir,a.model_dir)
    print(json.dumps({'plan_sha256':record['plan_sha256'],'model_forwards':0,'http_requests':0}))


if __name__=='__main__':main()
