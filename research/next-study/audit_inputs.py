"""Re-encode every saved input with the pinned cached tokenizer, without inference."""
import argparse
import json
import sys
from pathlib import Path
from transformers import AutoTokenizer
from study import HERE,BASE_REV,MAPS,OPTIONS,read_rows,native_prompt,write_json
sys.path.insert(0,str(HERE/'vendor'))
from kev.model import encode

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cache',default='G:/jev-lab/hf-cache')
args=parser.parse_args()
tok=AutoTokenizer.from_pretrained(Path(args.cache)/'models--Qwen--Qwen3-4B-Base/snapshots'/BASE_REV,local_files_only=True)
cases={c['id']:c for c in read_rows(HERE/'data/cases.jsonl')}
checked=0
for arm in ('N0','N1','K1'):
    for row in read_rows(HERE/f'results/{arm}.jsonl'):
        c=cases[row['id']];order=MAPS[row['mapping']]
        if arm=='K1':
            rec={'state':c['state'],'questions':[{'instr':c['instruction'],'options':[OPTIONS[x] for x in order],'label':0}]}
            e=encode(tok,rec,strict=True,option_isolation=False)
            assert row['token_ids']==e['ids'] and row['position_ids']==e['pos'] and row['segments']==e['seg']
            assert row['decide_idx']==e['decide_idx'] and row['option_idx']==e['opt_idx'] and not e['state_truncated']
        else:
            assert row['token_ids']==tok.encode(native_prompt(c,order),add_special_tokens=False)
            assert row['candidate_ids']==[tok.encode(' '+x,add_special_tokens=False)[0] for x in 'ABC']
        checked+=1
report={'status':'passed','checked_model_records':checked,'tokenizer_revision':BASE_REV,
        'scope':'post-run re-encoding audit; no model calls','no_truncation':True}
write_json(HERE/'provenance/postrun-input-audit.json',report)
print(json.dumps(report))
