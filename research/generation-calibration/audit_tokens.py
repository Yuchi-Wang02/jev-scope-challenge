"""Optional local-tokenizer reconstruction; no weights, model forward or network."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--model-dir',type=Path,required=True)
    a=p.parse_args()
    os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
    from transformers import AutoTokenizer
    raw=(ROOT/'results/run.json').read_bytes(); run=json.loads(raw)
    plan=json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
    cases={c['id']:c for c in plan['cases']}
    t=AutoTokenizer.from_pretrained(a.model_dir,local_files_only=True,trust_remote_code=False)
    assert len(run['records'])==48
    for r in run['records']:
        assert t.decode(r['output_ids'],skip_special_tokens=False)==r['decoded_output']
        assert t(r['rendered_input'],add_special_tokens=False)['input_ids']==r['input_ids']
        assert t.apply_chat_template([{'role':'user','content':cases[r['case_id']]['prompt']}],
            tokenize=False,add_generation_prompt=True,enable_thinking=r['thinking'])==r['rendered_input']
    receipt=json.loads((ROOT/'token_audit.json').read_text(encoding='utf-8'))
    assert receipt['run_sha256']==hashlib.sha256(raw).hexdigest()
    print(json.dumps({'verified_records':48,'model_forwards':0,'network_requests':0}))
