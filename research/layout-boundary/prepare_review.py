"""Prepare blank blind annotation inputs, not completed human validation."""
import csv
import random
from layout_study import HERE,PRIOR,read_rows,write_json

rows=read_rows(PRIOR/'data/cases.jsonl')
random.Random(20260930).shuffle(rows)
out=HERE/'review';out.mkdir(exist_ok=True)
if (out/'blind_review.csv').exists():raise ValueError('Preserve existing review sheet/annotations')
key={}
with (out/'blind_review.csv').open('w',encoding='utf-8',newline='') as stream:
    w=csv.writer(stream);w.writerow(['review_id','evidence','policy','reviewer_label','reason','ambiguity_or_objection','reviewer','reviewed_at'])
    for number,c in enumerate(rows,1):
        review_id=f'B{number:03d}';key[review_id]={'case_id':c['id'],'rule_label':c['gold']}
        w.writerow([review_id,c['state'],c['instruction'],'','','','',''])
write_json(out/'answer_key.json',key)
write_json(out/'status.json',{'status':'prepared_not_annotated','inputs':len(rows),
    'independent_human_annotations':0,'adjudicated_inputs':0})
print('Prepared 96 blank review inputs; zero human annotations.')
