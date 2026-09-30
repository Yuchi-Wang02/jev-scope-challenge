"""Reuse pinned audited backends and durable journal; never revise the old study."""
import argparse
import json
from pathlib import Path
from plan import CACHE,existing,verify

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=('jev','qwen'),required=True)
    p.add_argument('--model-dir',type=Path,required=True);a=p.parse_args()
    grid,manifest=verify(a.model_dir)
    factory=existing.jev_backend if a.backend=='jev' else lambda:existing.qwen_backend(a.model_dir)
    result=existing.journal.execute(CACHE/('execution-'+manifest['plan_sha256']),grid,
        manifest['plan_sha256'],a.backend,factory)
    print(json.dumps({'backend':a.backend,'status':result['status'],'attempts':len(result['state']['started']),
        'finished':len(result['state']['results']),'input_tokens':result['state']['input_tokens'],
        'output_tokens':result['state']['output_tokens'],'overruns':result['overruns']}))
