"""Distribute only the frozen blinded ShARC pack, with explicit source credit."""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

from prepare_sharc_review import HERE, ROOT, STUDY, CSV_FIELDS, readable, review_page

OUT = HERE / 'public-review'
ATTRIBUTION = '''# ShARC source and package license

Source: ShARC — Shaping Answers with Rules through Conversation.
Creators: Marzieh Saeidi, Max Bartolo, Patrick Lewis, Sameer Singh,
Tim Rocktäschel, Mike Sheldon, Guillaume Bouchard, Sebastian Riedel.
Paper: Interpretation of Natural Language Rules in Conversational Machine Reading
(EMNLP 2018), https://aclanthology.org/D18-1233/
Project: https://sharc-data.github.io/
Official data/license notice: https://sharc-data.github.io/data.html
Source archive: https://sharc-data.github.io/data/sharc1-official.zip

License: Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0).
Deed: https://creativecommons.org/licenses/by-sa/3.0/
Legal code: https://creativecommons.org/licenses/by-sa/3.0/legalcode

This entire review package, including the source-derived selection, its
presentation and added instructions, is distributed under CC BY-SA 3.0.
The repository-wide MIT license does not replace this package license.
Keep attribution and license notices when redistributing; indicate adaptations
and distribute them under the same license. No additional legal restrictions
are imposed by our request to avoid source answers during independent review.

Changes by the Jev Scope Challenge project (AI-assisted), 2026-09-30:
selected 60 training inputs; retained snippet, question, scenario and history;
omitted source labels/evidence/metadata; assigned opaque review IDs; shuffled
items; added blank annotation fields and an offline review interface.
Visible source text is not rewritten. The package is not endorsed by the
ShARC authors. These historical rules are research material, not current advice.
No warranties are provided. The official archive had no separate license file;
the official data page supplies the distribution notice checked on this date.
'''
INSTRUCTIONS = '''# Independent rule-decision review

Extract this ZIP and open review.html locally. The page works without a server
and sends no answers anywhere. Enter your stable reviewer ID and Start / resume.
Use a separate browser profile from other reviewers. Download your CSV when
finished; browser storage is only a convenience, not a durable backup.

Judge all 60 items independently using only the visible snippet, question,
scenario and history. Choose Yes, No, Irrelevant, ASK or UNCLEAR and explain why.
ASK means a further question is needed; no particular wording must be generated.
Use UNCLEAR when conflicting or ambiguous text prevents a justified action.
Do not force an answer from outside knowledge. These are historical research
texts, not a request to apply today's law or policy. See ATTRIBUTION.md.

Do not inspect source answers, project analyses, or another person's review
before saving your initial answers. Work without AI assistance; disclose any
exposure, assistance or discussion that did occur in cover_note.txt. This is
a review procedure, not a restriction on your rights under the data license.
Return your exported CSV and cover note to the person who gave you this pack.
The blank_review.csv has the same IDs if you prefer a spreadsheet editor.
Do not change IDs or column names. Dates use YYYY-MM-DD.
'''
COVER = '''Reviewer ID:
Date completed:
Relationship to this project:
Before/during review, did you see source labels, model answers or summaries,
project discussions, or another review? Describe any exposure:
Did you use AI assistance or discuss judgments with anyone? Describe:
Anything unclear in the instructions or examples:
This is a reviewer self-report, not independently verified process evidence.
'''
MEMBERS = {'review.html', 'blank_review.csv', 'README.md', 'ATTRIBUTION.md', 'cover_note.txt'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_pack(pack, frozen):
    if sha(readable(pack)) != frozen['private_review_pack_sha256']:
        raise ValueError('Pack differs from the frozen visible inputs')
    if set(pack) != {'status', 'study', 'instructions', 'items'}:
        raise ValueError('Unexpected pack fields')
    if pack['study'] != STUDY or pack['status'] != 'blank_human_review_no_model_outputs':
        raise ValueError('Wrong study or review status')
    items = pack['items']
    if len(items) != 60 or len({x['item_id'] for x in items}) != 60:
        raise ValueError('Missing or duplicate items')
    for x in items:
        if set(x) != {'item_id', 'snippet', 'question', 'scenario', 'history'}:
            raise ValueError('Unexpected item fields')
        if not re.fullmatch('[0-9a-f]{24}', x['item_id']):
            raise ValueError('Unexpected review ID')
        if any(not isinstance(x[k], str) for k in ('snippet', 'question', 'scenario')):
            raise ValueError('Malformed visible text')
        for h in x['history']:
            if set(h) != {'follow_up_question', 'follow_up_answer'} or any(
                    not isinstance(v, str) for v in h.values()):
                raise ValueError('Unexpected history fields')


def page(pack, frozen):
    html = review_page(frozen, readable(pack)).decode('utf-8')
    html = html.replace('Rule decision review · private local page',
                        'Rule decision review · ShARC licensed review package')
    html = html.replace('Private · offline · blinded', 'Offline · independent review')
    html = html.replace('Private review data not loaded.', 'Review data not loaded.')
    html = html.replace('Generate this page from the pinned local ShARC pack. The public template intentionally contains no source examples.',
                        'Extract the complete review package and reopen this page in a browser with JavaScript enabled.')
    # The underlying frozen template and its private export stay unchanged.
    credit = ('<section aria-label="Source attribution" style="max-width:1100px;margin:24px auto;padding:20px;line-height:1.6"><h2>Source and license</h2>'
              '<p>ShARC — Saeidi, Bartolo, Lewis, Singh, Rocktäschel, Sheldon, '
              'Bouchard and Riedel (2018). '
              '<a href="https://sharc-data.github.io/data.html">Official source</a>. '
              'This adapted review package is licensed under '
              '<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>. '
              'Selection, opaque IDs and review presentation added; visible source text '
              'unchanged. See <a href="ATTRIBUTION.md">full attribution and changes</a>. '
              'No author endorsement.</p></section>')
    return html.replace('</main>', credit + '\n</main>').encode('utf-8')


def payloads(pack, csv_bytes, frozen):
    validate_pack(pack, frozen)
    if sha(csv_bytes) != frozen['private_blank_csv_sha256']:
        raise ValueError('CSV differs from the frozen blank')
    reader = csv.DictReader(io.StringIO(csv_bytes.decode('utf-8')))
    rows = list(reader)
    if tuple(reader.fieldnames or ()) != CSV_FIELDS or len(rows) != 60:
        raise ValueError('Wrong blank CSV shape')
    if [r['item_id'] for r in rows] != [x['item_id'] for x in pack['items']] or any(
            r[k] for r in rows for k in CSV_FIELDS[1:]):
        raise ValueError('Nonblank or reordered annotation template')
    return {'review.html': page(pack, frozen), 'blank_review.csv': csv_bytes,
            'README.md': INSTRUCTIONS.encode('utf-8'),
            'ATTRIBUTION.md': ATTRIBUTION.encode('utf-8'),
            'cover_note.txt': COVER.encode('utf-8')}


def archive(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 9, 30, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    return output.getvalue()


def manifest(files, bundle, frozen):
    return {'publication_date': '2026-09-30', 'study': STUDY,
            'license': 'CC-BY-SA-3.0', 'license_source': 'https://sharc-data.github.io/data.html',
            'source_archive_sha256': frozen['official_archive_sha256'],
            'frozen_selection_sha256': frozen['selection_sha256'],
            'frozen_visible_pack_sha256': frozen['private_review_pack_sha256'],
            'public_visible_items': 60, 'public_opaque_review_ids': 60,
            'public_source_ids': 0, 'public_source_labels': 0,
            'completed_human_reviews': 0, 'model_forwards': 0,
            'zip_sha256': sha(bundle), 'zip_bytes': len(bundle),
            'members': {n: sha(b) for n, b in sorted(files.items())}}


def verify():
    frozen = json.loads((HERE / 'sharc_review_manifest.json').read_text(encoding='utf-8'))
    bundle = (OUT / 'review_package.zip').read_bytes()
    with zipfile.ZipFile(io.BytesIO(bundle)) as z:
        if set(z.namelist()) != MEMBERS or len(z.namelist()) != len(MEMBERS):
            raise ValueError('Unexpected or duplicate ZIP members')
        files = {name: z.read(name) for name in MEMBERS}
    html = files['review.html'].decode('utf-8')
    matches = re.findall(r'<script id="review-data" type="application/json">(.*?)</script>', html, re.S)
    if len(matches) != 1:
        raise ValueError('Missing or duplicate embedded pack')
    embedded = json.loads(matches[0])
    if set(embedded) != {'pack_sha256', 'pack'} or embedded['pack_sha256'] != frozen['private_review_pack_sha256']:
        raise ValueError('Embedded metadata differs')
    expected = payloads(embedded['pack'], files['blank_review.csv'], frozen)
    if files != expected or bundle != archive(expected):
        raise ValueError('Public archive differs from declared licensed build')
    recorded = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    if recorded != manifest(expected, bundle, frozen):
        raise ValueError('Publication manifest mismatch')
    return {'status': 'passed', 'visible_items': 60, 'completed_reviews': 0,
            'model_forwards': 0, 'private_files_required': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('command', choices=['build', 'verify']); args = p.parse_args()
    if args.command == 'build':
        frozen = json.loads((HERE / 'sharc_review_manifest.json').read_text(encoding='utf-8'))
        private = ROOT / '.local' / STUDY
        pack = json.loads((private / 'review_items.json').read_text(encoding='utf-8'))
        files = payloads(pack, (private / 'blank_review.csv').read_bytes(), frozen)
        bundle = archive(files)
        OUT.mkdir(exist_ok=True)
        (OUT / 'review_package.zip').write_bytes(bundle)
        (OUT / 'manifest.json').write_bytes(readable(manifest(files, bundle, frozen)))
    print(json.dumps(verify(), indent=2))
