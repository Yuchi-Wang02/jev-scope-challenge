import copy
import hashlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'research/external-validation'
sys.path.insert(0, str(HERE))
import publish_review as public
from prepare_sharc_review import readable


class SharcPublicReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = json.loads((HERE / 'sharc_review_manifest.json').read_text(encoding='utf-8'))
        with zipfile.ZipFile(HERE / 'public-review/review_package.zip') as z:
            cls.files = {n: z.read(n) for n in z.namelist()}
        import re
        embedded = re.search(r'<script id="review-data" type="application/json">(.*?)</script>',
                             cls.files['review.html'].decode(), re.S)
        cls.pack = json.loads(embedded[1])['pack']

    def test_public_bundle_verifies_without_private_source(self):
        self.assertEqual(public.verify()['visible_items'], 60)
        self.assertEqual(set(self.files), public.MEMBERS)

    def test_reject_label_leak_even_if_caller_rehashes_manifest(self):
        for field in ('answer', 'evidence', 'tree_id', 'pair_id', 'role', 'stratum', 'model_output'):
            pack = copy.deepcopy(self.pack)
            pack['items'][0][field] = 'MUST_NOT_PUBLISH'
            frozen = dict(self.frozen, private_review_pack_sha256=public.sha(readable(pack)))
            with self.assertRaises(ValueError):
                public.validate_pack(pack, frozen)

    def test_visible_input_drift_rejected(self):
        pack = copy.deepcopy(self.pack)
        pack['items'][0]['scenario'] += ' extra condition'
        with self.assertRaises(ValueError):
            public.validate_pack(pack, self.frozen)

    def test_completed_annotation_cannot_be_packaged_even_if_rehashed(self):
        data = self.files['blank_review.csv'].replace(b',,,,\n', b',Yes,reason,human,2026-09-30\n', 1)
        frozen = dict(self.frozen, private_blank_csv_sha256=public.sha(data))
        with self.assertRaises(ValueError):
            public.payloads(self.pack, data, frozen)

    def test_rebuild_is_identical_and_attribution_travels_with_html(self):
        rebuilt = public.payloads(self.pack, self.files['blank_review.csv'], self.frozen)
        self.assertEqual(self.files, rebuilt)
        self.assertEqual(public.archive(rebuilt), (HERE / 'public-review/review_package.zip').read_bytes())
        self.assertIn(b'CC BY-SA 3.0', rebuilt['review.html'])
        self.assertIn(b'ATTRIBUTION.md', rebuilt['review.html'])
        self.assertIn(b'creativecommons.org/licenses/by-sa/3.0/legalcode', rebuilt['ATTRIBUTION.md'])


if __name__ == '__main__':
    unittest.main()
