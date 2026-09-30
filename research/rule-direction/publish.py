"""Build an offline replay from all saved cases and observations."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def build():
    cases=json.loads((HERE/'cases.json').read_bytes());report=json.loads((HERE/'report.json').read_bytes())
    if not report['complete'] or len(report['observations'])!=444:raise ValueError('Incomplete result')
    if any(b['mapping'][str(m)]['correct']!=84 for b in report['backends'].values() for m in (0,1)):raise ValueError('Update public headline for changed evidence')
    data=json.dumps({'cases':cases,'observations':report['observations']},ensure_ascii=False).replace('<','\\u003c')
    template=(HERE/'replay_template.html').read_text(encoding='utf-8')
    if template.count('__DATA__')!=1:raise ValueError('Template mismatch')
    return template.replace('__DATA__',data).encode('utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('build','verify'));a=p.parse_args()
    raw=build();out=ROOT/'docs/rule_direction.html'
    if a.command=='build':out.write_bytes(raw)
    elif out.read_bytes().replace(b'\r\n',b'\n')!=raw:raise ValueError('Replay drift')
    print(json.dumps({'visible_cases':108,'recorded_observations':444,'new_model_calls':0}))
