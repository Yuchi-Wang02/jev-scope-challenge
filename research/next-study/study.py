"""Exploratory matched-base diagnostic. No paid APIs and no new training."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = 'Qwen/Qwen3-4B-Base'
BASE_REV = '906bfd4b4dc7f14ee4320094d8b41684abff8539'
ADAPTER = 'jaredpalmer/kev-4b'
ADAPTER_REV = 'c4bfa11b0dc07691884f2d97f1c4c4c05c92e416'
SOURCE_REV = '29d71c78368657b3a522729a01c748ea15272abc'
LABELS = ['ALLOW', 'DENY', 'INSUFFICIENT']
OPTIONS = {
    'ALLOW': 'The supplied evidence supports the requested action or stated claim.',
    'DENY': 'The supplied evidence contradicts the requested action or stated claim.',
    'INSUFFICIENT': 'The supplied evidence does not determine whether to allow or deny.'}
MAPS = [LABELS, LABELS[1:] + LABELS[:1], LABELS[2:] + LABELS[:2]]
SEED = 20260929


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def read_rows(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x] if path.exists() else []


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def gold_for(case):
    evidence, target = case['evidence'], case['target']
    if case['family'] == 'owner_scope':
        values = [x['action'] for x in evidence if x['repository'] == target and x['speaker_role'] == 'owner']
        return LABELS[0 if values[0] == 'grant' else 1] if len(values) == 1 else 'INSUFFICIENT'
    if case['family'] == 'claim_binding':
        rows = [x for x in evidence if x['item'] == target]
        if len(rows) != 1 or 'rank' not in rows[0]:
            return 'INSUFFICIENT'
        return 'ALLOW' if rows[0]['rank'] == case['claim_rank'] else 'DENY'
    values = [x['action'] for x in evidence if x['account'] == target and x['status'] == 'current']
    return LABELS[0 if values[0] == 'enable' else 1] if len(values) == 1 else 'INSUFFICIENT'


def state_for(case):
    e, target = case['evidence'], case['target']
    if case['family'] == 'owner_scope':
        intro = f'Request: grant write access to repository {target}.'
        lines = [f"The {x['speaker_role']} of repository {x['repository']} says: {x['action']} write access." for x in e]
        instruction = 'Only the repository owner can authorize write access for that repository. Owner grant supports the request; owner deny contradicts it. An instruction for a different repository or from a guest gives no authorization. If the owner decision for the target is absent, choose insufficient. Use only this evidence.'
    elif case['family'] == 'claim_binding':
        intro = f"Claim: item {target} has rank {case['claim_rank']} in the supplied report."
        lines = [f"Report row: item {x['item']}; rank {x.get('rank', 'not supplied')}." for x in e]
        instruction = 'Verify the stated item-rank claim against the report. Exact match supports it, a different rank for that item contradicts it, and an absent rank for that item is insufficient. Rows about other items do not establish the target rank. Use only this evidence.'
    else:
        intro = f'Request: enable notifications for account {target}.'
        lines = [f"{x['status'].capitalize()} instruction for account {x['account']}: {x['action']} notifications." for x in e]
        instruction = 'Only the instruction explicitly marked current determines the request. Current enable supports it; current disable contradicts it. Superseded instructions do not control the decision even when no current instruction is supplied. If the target current instruction is absent, choose insufficient. Use only this evidence.'
    # Distinct presentation styles are grouped across families in dev/cal/test.
    style = case['style']
    rendered = '\n'.join(lines) if style % 2 == 0 else '\n'.join(f'{i+1}) {line}' for i, line in enumerate(lines))
    prefix = ['Evidence:', 'Records:', 'Supplied notes:', 'Decision record:', 'Source extract:', 'Case evidence:', 'Available statements:', 'Report extract:'][style]
    return intro + '\n' + prefix + '\n' + rendered, instruction


def build():
    rows = []
    for family in ('owner_scope', 'claim_binding', 'current_request'):
        for i in range(8):
            target, other = f'{family}-target-{i+1}', f'{family}-other-{i+1}'
            initial = i % 2 == 0
            if family == 'owner_scope':
                evidence = [{'repository':target,'speaker_role':'owner','action':'grant' if initial else 'deny'},
                            {'repository':other,'speaker_role':'owner','action':'deny' if initial else 'grant'},
                            {'repository':target,'speaker_role':'guest','action':'deny' if initial else 'grant'}]
            elif family == 'claim_binding':
                evidence = [{'item':target,'rank':2 if initial else 7}, {'item':other,'rank':7 if initial else 2}]
            else:
                evidence = [{'account':target,'status':'current','action':'enable' if initial else 'disable'},
                            {'account':target,'status':'superseded','action':'disable' if initial else 'enable'},
                            {'account':other,'status':'current','action':'disable' if initial else 'enable'}]
            import copy
            for variant in ('full', 'hold', 'flip', 'missing'):
                changed = copy.deepcopy(evidence)
                if variant == 'hold':
                    changed.reverse()
                elif variant == 'flip':
                    if family == 'owner_scope':
                        changed[0]['repository'], changed[1]['repository'] = changed[1]['repository'], changed[0]['repository']
                    elif family == 'claim_binding':
                        changed[0]['rank'], changed[1]['rank'] = changed[1]['rank'], changed[0]['rank']
                    else:
                        changed[0]['status'], changed[1]['status'] = changed[1]['status'], changed[0]['status']
                elif variant == 'missing':
                    if family == 'claim_binding':
                        del changed[0]['rank']
                    else:
                        changed.pop(0)
                row = {'id':f'{family}-{i+1}-{variant}','parent':f'{family}-{i+1}', 'family':family,
                       'variant':variant,'split':'development' if i < 2 else 'calibration' if i < 4 else 'exploratory_test',
                       'style':i, 'source':'original synthetic structured facts', 'target':target,
                       'evidence':changed, 'claim_rank':2, 'independent_human_reviewed':False}
                row['gold'] = gold_for(row)
                row['state'], row['instruction'] = state_for(row)
                rows.append(row)
    validate(rows)
    path = HERE / 'data/cases.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in rows)
    if path.exists() and path.read_text(encoding='utf-8') != payload:
        raise ValueError('Existing study data differ; version rather than replace')
    path.write_text(payload, encoding='utf-8', newline='\n')
    freeze()


def validate(rows):
    if len(rows) != 96 or len({r['id'] for r in rows}) != 96:
        raise ValueError('Expected 24 complete four-view parents')
    for parent in {r['parent'] for r in rows}:
        group = {r['variant']:r for r in rows if r['parent'] == parent}
        if set(group) != {'full','hold','flip','missing'} or len({r['split'] for r in group.values()}) != 1:
            raise ValueError('Invalid grouped split')
        if group['hold']['gold'] != group['full']['gold'] or group['flip']['gold'] == group['full']['gold'] or group['missing']['gold'] != 'INSUFFICIENT':
            raise ValueError('Invalid intervention labels')
    for row in rows:
        if row['gold'] != gold_for(row) or (row['state'], row['instruction']) != state_for(row):
            raise ValueError('Gold or rendered facts differ from rule')


def freeze():
    paths = ['data/cases.jsonl','study.py','analyze_study.py','PROTOCOL.md','vendor/kev/model.py']
    obj = {'study':'matched-base-pilot-v0.1', 'base':BASE, 'base_revision':BASE_REV,
           'adapter':ADAPTER,'adapter_revision':ADAPTER_REV,'source_revision':SOURCE_REV,
           'arms':['N0','N1','K1','C0'],'candidate_orders':MAPS,'seed':SEED,
           'backbone_dtype':'bfloat16','head_dtype':'float32','adapter_mode':'unmerged',
           'tf32':False,'quantization':None,'new_training':False,'independent_human_reviewed':False,
           'file_sha256_lf':{p:sha((HERE/p).read_bytes().replace(b'\r\n',b'\n')) for p in paths}}
    obj['config_hash'] = sha(canonical(obj).encode())
    path = HERE / 'manifest.json'
    if path.exists() and json.loads(path.read_text(encoding='utf-8')) != obj:
        raise ValueError('Existing freeze differs; preserve it and version changes')
    write_json(path, obj)
    return obj


def jobs_for(rows):
    jobs = [(r, index, order) for r in rows for index, order in enumerate(MAPS)]
    random.Random(SEED).shuffle(jobs)
    return jobs


def native_prompt(row, order):
    return row['state'] + '\n\n' + row['instruction'] + '\n' + '\n'.join(f'{chr(65+i)}. {OPTIONS[label]}' for i,label in enumerate(order)) + '\nAnswer:'


def run(cache):
    import gc
    import importlib.metadata
    import platform
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from huggingface_hub import snapshot_download, HfApi
    from peft import PeftModel
    manifest = freeze()
    rows = read_rows(HERE / 'data/cases.jsonl')
    validate(rows)
    out = HERE / 'results'
    out.mkdir(exist_ok=True)
    if any((out/f'{a}.jsonl').exists() for a in ('N0','N1','K1')):
        raise ValueError('Existing run records found; preserve rather than rerun/select')
    torch.manual_seed(SEED)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.cuda.reset_peak_memory_stats()
    environment = {'python':platform.python_version(),'gpu':torch.cuda.get_device_name(0),'cuda':torch.version.cuda,
                   'packages':{p:importlib.metadata.version(p) for p in ('torch','transformers','peft','huggingface-hub','numpy')},
                   'config_hash':manifest['config_hash'], 'status':'loading', 'backbone_dtype':'bfloat16', 'head_dtype':'float32',
                   'new_training':False,'paid_api_calls':0}
    write_json(out/'runtime.json',environment)
    base_path = snapshot_download(BASE, revision=BASE_REV, cache_dir=cache, local_files_only=True)
    adapter_path = snapshot_download(ADAPTER, revision=ADAPTER_REV, cache_dir=cache, local_files_only=True)
    # Verify downloaded LFS objects against the pinned Hub metadata before load.
    checked = {}
    for repo, rev, path in ((BASE,BASE_REV,base_path),(ADAPTER,ADAPTER_REV,adapter_path)):
        info = HfApi().model_info(repo, revision=rev, files_metadata=True)
        for file in info.siblings:
            if file.rfilename.endswith(('.safetensors','.pt')):
                local = Path(path)/file.rfilename
                h = hashlib.sha256()
                with local.open('rb') as stream:
                    for chunk in iter(lambda:stream.read(8*1024*1024), b''):
                        h.update(chunk)
                if file.lfs and h.hexdigest() != file.lfs.sha256:
                    raise ValueError('Downloaded model checksum mismatch')
                checked[f'{repo}@{rev}/{file.rfilename}'] = h.hexdigest()
    write_json(out/'weight_checksums.json',checked)
    tok = AutoTokenizer.from_pretrained(base_path, local_files_only=True)
    meta = torch.load(Path(adapter_path)/'head.pt',map_location='cpu',weights_only=True)
    if meta['base'] != BASE or meta.get('base_revision') not in (None,BASE_REV) or meta.get('option_isolation',False):
        raise ValueError('Checkpoint architecture/base mismatch')
    write_json(out/'checkpoint_metadata.json',{k:v for k,v in meta.items() if k != 'head'})
    started = time.perf_counter()
    lm = AutoModelForCausalLM.from_pretrained(base_path,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True).to('cuda').eval()
    environment['load_s'] = time.perf_counter()-started
    sys.path.insert(0,str(HERE/'vendor'))
    from kev.model import DecisionModel, PointerHead, encode
    jobs = jobs_for(rows)
    for arm in ('N0','N1','K1'):
        if arm == 'N1':
            lm.model = PeftModel.from_pretrained(lm.model,adapter_path,is_trainable=False)
            lm.eval()
            environment['adapter_base_parameters_bf16'] = all(p.dtype == torch.bfloat16 for n,p in lm.model.named_parameters() if 'lora_' not in n)
        if arm == 'K1':
            # Attach the exact historical pointer implementation to the very same
            # adapted backbone used in N1; avoid a second 8 GB model allocation.
            pointer = DecisionModel.__new__(DecisionModel)
            torch.nn.Module.__init__(pointer)
            pointer.lm, pointer.device = lm.model, 'cuda'
            pointer.pad_id = tok.pad_token_id if tok.pad_token_id is not None else 0
            pointer.head = PointerHead(lm.config.hidden_size,dp=meta.get('head_dim',256)).to('cuda')
            pointer.head.load_state_dict(meta['head'])
            pointer.eval()
            # Independent one-question causal-path check: no branch isolation is
            # needed when only one question exists, so compare against standard
            # causal attention rather than a duplicate of the packed-mask code.
            rec = {'state':'Engineering check: account demo has a current enable instruction.',
                   'questions':[{'instr':'Does the current instruction enable notifications?',
                                 'options':['Yes','No'],'label':0}]}
            enc = encode(tok,rec,strict=True)
            with torch.inference_mode():
                packed = pointer.forward(enc)[0]
                hidden = pointer.lm(input_ids=torch.tensor([enc['ids']],device='cuda'),
                    position_ids=torch.tensor([enc['pos']],device='cuda')).last_hidden_state[0].float()
                causal = pointer.head(hidden[enc['decide_idx'][0]],hidden[torch.tensor(enc['opt_idx'][0],device='cuda')])
                delta = (torch.softmax(packed,-1)-torch.softmax(causal,-1)).abs().max().item()
            write_json(out/'pointer_parity.json',{'status':'passed' if delta < 1e-4 else 'failed','max_probability_delta':delta,
                        'scope':'one engineering question, packed versus standard causal path; not historical published scores'})
            if delta >= 1e-4:
                raise ValueError('Pointer path parity failed')
        # Warm up on an engineering-only input, excluding it from scientific rows.
        for _ in range(2):
            with torch.inference_mode():
                lm(input_ids=torch.tensor([[tok.eos_token_id]],device='cuda'))
        torch.cuda.synchronize()
        for number,(row,mapping,order) in enumerate(jobs,1):
            artifact = {'id':row['id'],'parent':row['parent'],'family':row['family'],'variant':row['variant'],
                        'split':row['split'],'arm':arm,'mapping':mapping,'order':order,'config_hash':manifest['config_hash']}
            if arm in ('N0','N1'):
                prompt = native_prompt(row,order)
                ids = tok.encode(prompt,add_special_tokens=False)
                candidates = [tok.encode(' '+letter,add_special_tokens=False) for letter in 'ABC']
                if any(len(x) != 1 for x in candidates) or len({x[0] for x in candidates}) != 3:
                    raise ValueError('Invalid answer slot tokenization')
                for letter,candidate in zip('ABC',candidates):
                    if tok.encode(prompt+' '+letter,add_special_tokens=False) != ids+candidate:
                        raise ValueError('Answer slot boundary mismatch')
                tensor = torch.tensor([ids],device='cuda')
                torch.cuda.synchronize(); tick = time.perf_counter()
                with torch.inference_mode():
                    logits = lm(input_ids=tensor).logits[0,-1].float()
                    z = logits[[x[0] for x in candidates]]
                    p = torch.softmax(z,-1)
                    full = torch.softmax(logits,-1)
                    artifact.update(prompt=prompt,prompt_sha256=sha(prompt.encode()),token_ids=ids,
                                    candidate_ids=[x[0] for x in candidates],candidate_mass=full[[x[0] for x in candidates]].sum().item())
            else:
                rec = {'state':row['state'],'questions':[{'instr':row['instruction'],'options':[OPTIONS[x] for x in order],'label':0}]}
                enc = encode(tok,rec,strict=True,option_isolation=False)
                if enc['state_truncated']:
                    raise ValueError('Truncated pointer state')
                artifact.update(token_ids=enc['ids'],position_ids=enc['pos'],segments=enc['seg'],decide_idx=enc['decide_idx'],option_idx=enc['opt_idx'],
                                state=row['state'],instruction=row['instruction'],options=[OPTIONS[x] for x in order])
                torch.cuda.synchronize(); tick = time.perf_counter()
                with torch.inference_mode():
                    z = pointer.forward(enc)[0]
                    p = torch.softmax(z,-1)
            torch.cuda.synchronize()
            artifact.update(ok=True,latency_s=time.perf_counter()-tick,input_tokens=len(artifact['token_ids']),
                            logits=z.detach().cpu().tolist(),probabilities=p.detach().cpu().tolist(),prediction=order[int(p.argmax())],
                            temperature=1.,peak_allocated_mib=torch.cuda.max_memory_allocated()/1024**2)
            with (out/f'{arm}.jsonl').open('a',encoding='utf-8',newline='\n') as stream:
                stream.write(json.dumps(artifact,ensure_ascii=False,allow_nan=False)+'\n'); stream.flush()
            if number % 48 == 0:
                print(f'{arm}: {number}/{len(jobs)} real forward passes',flush=True)
        environment[arm] = {'records':len(jobs),'status':'complete'}
        write_json(out/'runtime.json',environment)
    environment.update(status='complete',peak_allocated_mib=torch.cuda.max_memory_allocated()/1024**2)
    write_json(out/'runtime.json',environment)
    print('All three model arms completed.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['build','run'])
    parser.add_argument('--cache',default='G:/jev-lab/hf-cache')
    args = parser.parse_args()
    build() if args.command == 'build' else run(args.cache)
