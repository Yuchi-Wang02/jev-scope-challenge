"""Offline publication checks: local links, pinned attribution, and review gates.

This checks technical consistency, not legal completeness, novelty or human truth.
"""
import hashlib
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()


class Links(HTMLParser):
    def __init__(self):super().__init__();self.targets=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('href','src') and v:self.targets.append(v)


def check_link(path,target):
    target=target.strip().strip('<>');url=urlsplit(target)
    if url.scheme or url.netloc or not url.path:return False
    resolved=(path.parent/unquote(url.path)).resolve()
    if ROOT not in resolved.parents and resolved!=ROOT:raise ValueError(f'Nonportable local link: {path.relative_to(ROOT)} -> {target}')
    if not resolved.exists():raise ValueError(f'Broken local link: {path.relative_to(ROOT)} -> {target}')
    return True


def verify():
    names=set(subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=ROOT).decode().split('\0'))-{''}
    counts={'markdown_files':0,'html_files':0,'html_templates_skipped':0,'local_links':0};suspicious=[];weights=[]
    secret=re.compile(r'(?:apikey_[a-fA-F0-9]{20,}|hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{25,}|sk-[A-Za-z0-9_-]{30,})')
    for name in sorted(names):
        path=ROOT/name
        if not path.is_file():continue
        if path.suffix in ('.safetensors','.pt','.pth','.gguf'):weights.append(name)
        try:text=path.read_text(encoding='utf-8')
        except UnicodeDecodeError:continue
        if secret.search(text):suspicious.append(name)
        targets=[]
        if path.suffix=='.md':
            counts['markdown_files']+=1;text=re.sub(r'```.*?```','',text,flags=re.S)
            targets=[m.group(1) for m in re.finditer(r'!?\[[^\]]*\]\(([^)]+)\)',text)]
        elif path.suffix=='.html':
            if path.name.endswith('_template.html'):
                counts['html_templates_skipped']+=1;continue
            counts['html_files']+=1;parser=Links();parser.feed(text);targets=parser.targets
        for target in targets:counts['local_links']+=check_link(path,target)
    if suspicious:raise ValueError('Credential-like text found in files (values suppressed): '+', '.join(suspicious))
    if weights:raise ValueError('Unexpected public weight files: '+', '.join(weights))
    audit=json.loads((ROOT/'provenance/attribution_audit_2026-09-29.json').read_text(encoding='utf-8'))
    prior=json.loads((ROOT/'research/next-study/manifest.json').read_text(encoding='utf-8'))
    if audit['kev']['revision']!=prior['source_revision']:raise ValueError('Attribution/source revision mismatch')
    for entry in audit['kev']['source_files']:
        for local in entry['local_paths']:
            if digest(ROOT/local)!=entry['sha256_lf']:raise ValueError('Vendored source/license changed: '+local)
    if digest(ROOT/'CITATION.cff')!=audit['citation']['sha256_lf']:raise ValueError('Citation changed since recorded schema validation; revalidate and update audit')
    credits=(ROOT/'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')
    if any(pin not in credits for pin in (prior['source_revision'],prior['base_revision'],prior['adapter_revision'])):raise ValueError('Missing visible upstream pin')
    for directory in ('evidence-gap','fact-execution'):
        manifest=json.loads((ROOT/f'research/{directory}/review/manifest.json').read_text(encoding='utf-8'))
        if manifest['annotations']!=0 or manifest['reserved_inference_open']:raise ValueError('Review status changed; update the study-wide publication audit explicitly')
    return {'status':'passed','read_only':True,**counts,'vendored_source_and_license_copies_checked':6,
        'citation_matches_schema_validated_bytes':True,'credential_pattern_matches':0,'public_weight_files':0,
        'independent_human_annotations':0,'scope':'technical consistency, not a legal or scientific certification'}


if __name__=='__main__':print(json.dumps(verify(),indent=2))
