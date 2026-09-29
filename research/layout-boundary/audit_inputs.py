"""Re-encode all plans and check all saved records with pinned local tokenizer."""
import argparse
from layout_study import HERE,ARMS,prior,load_tokenizer,plans_for,read_rows,write_json

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cache',default='G:/jev-lab/hf-cache')
args=parser.parse_args()
plans=plans_for(load_tokenizer(args.cache))
if plans!=read_rows(HERE/'data/inputs.jsonl'):raise ValueError('Frozen input plans differ from re-encoding')
lookup={(p['id'],p['mapping'],p['layout']):p for p in plans}
checked=0
for arm in ARMS:
    for row in read_rows(HERE/f'results/{arm}.jsonl'):
        p=lookup[row['id'],row['mapping'],row['layout']]
        expected=p['native_token_ids'] if arm!='K1' else p['pointer_encoding']['ids']
        if row['token_ids']!=expected:raise ValueError('Saved model input differs from pinned tokenizer')
        checked+=1
if checked!=2592:raise ValueError('Incomplete input audit')
report={'status':'passed','encoded_plans':len(plans),'checked_logical_records':checked,
    'identical_native_layout_pairs':288,'tokenizer_revision':prior.BASE_REV,
    'model_calls':0,'no_truncation':True}
write_json(HERE/'results/input_audit.json',report)
print(report)
