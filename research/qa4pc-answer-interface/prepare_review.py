"""Build local-only blinded forms from pinned source; never read model outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DEST=ROOT/'.local'/'qa4pc-interface-review-v1'


def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=raw:raise ValueError('Existing review package differs; preserve original')
    path.write_bytes(raw)


def build(source_dir):
    cohort=json.loads((HERE/'cohort.json').read_bytes())
    for name,(digest,size) in cohort['source']['qa4pc_file_pins'].items():
        raw=(source_dir/name).read_bytes()
        if len(raw)!=size or sha(raw)!=digest:raise ValueError('Pinned source differs')
    rows={r['utterance_id']:r for r in json.loads((source_dir/'dev_entailment_qa4pc.json').read_bytes())}
    # Obtain the exact original instruction as a literal; no runtime imports,
    # model/reference files or query plans are read by the package builder.
    import ast
    code=ast.parse((HERE/'compile_plan.py').read_text(encoding='utf-8'))
    rule=next(ast.literal_eval(n.value) for n in code.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RULE' for t in n.targets))
    instruction=rule+' Answer the main question under the policy.'
    items=[];mapping={}
    for tree in cohort['selected']:
        for ref in tree['scenarios']:
            uid=ref['utterance_id'];row=rows[uid]
            content={k:row[k] for k in ('policy','question','scenario')}
            if sha(canonical(content))!=ref['direct_visible_sha256']:raise ValueError('Visible content drift')
            ident='review-'+sha(canonical(['qa4pc-interface-review-v1',uid]))[:16]
            items.append({'review_id':ident,**content});mapping[ident]={'item_id':uid,'tree_id':tree['tree_id']}
    template=(HERE/'review_form.html').read_text(encoding='utf-8')
    if template.count('__PACKET_JSON__')!=1:raise ValueError('Template placeholder mismatch')
    manifest={'study':'qa4pc-interface-review-v1','human_submissions':0,'reference_updates':0,'items':24,'slots':{}}
    for slot in ('A','B'):
        ordered=sorted(items,key=lambda x:sha(canonical([slot,x['review_id']])))
        base={'schema_version':1,'slot':slot,'instruction':instruction,'items':ordered}
        packet={**base,'packet_sha256':sha(canonical(base))}
        data=json.dumps(packet,ensure_ascii=False).replace('<','\\u003c')
        html=template.replace('__PACKET_JSON__',data).encode('utf-8')
        path=DEST/('reviewer_'+slot)/'review.html';save(path,html)
        save(DEST/('packet_'+slot+'.json'),canonical(packet)+b'\n')
        zip_path=DEST/('reviewer_'+slot+'_package.zip')
        import io
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
            info=zipfile.ZipInfo('review.html',date_time=(2026,9,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,html)
        save(zip_path,stream.getvalue())
        manifest['slots'][slot]={'packet_sha256':packet['packet_sha256'],'html_sha256':sha(html),'zip_sha256':sha(stream.getvalue()),'items':len(ordered)}
    save(DEST/'private_item_mapping.json',canonical(mapping)+b'\n')
    save(DEST/'manifest.json',canonical(manifest)+b'\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.source_dir)))
