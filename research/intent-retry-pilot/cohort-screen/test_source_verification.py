"""Software-only fixtures for explicit external-source verification semantics."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from verify_artifacts import verify_external_sources


class SourceVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = {"files": []}
        for name, contents in (("one.txt", b"first"), ("nested/two.txt", b"second")):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
            self.manifest["files"].append({
                "path": name, "bytes": len(contents),
                "sha256": hashlib.sha256(contents).hexdigest(),
            })

    def test_default_distinguishes_manifest_from_observation(self):
        report = verify_external_sources(self.manifest)
        self.assertFalse(report["source_cache_rechecked"])
        self.assertEqual(report["manifest_files"], 2)
        self.assertEqual(report["manifest_bytes"], 11)
        self.assertEqual(report["files_verified"], 0)
        self.assertEqual(report["bytes_verified"], 0)

    def test_explicit_good_directory_rechecks_every_file(self):
        report = verify_external_sources(self.manifest, self.root)
        self.assertTrue(report["source_cache_rechecked"])
        self.assertEqual(report["files_verified"], 2)
        self.assertEqual(report["bytes_verified"], 11)

    def test_explicit_missing_directory_fails(self):
        with self.assertRaises(FileNotFoundError):
            verify_external_sources(self.manifest, self.root / "absent")

    def test_explicit_missing_file_fails(self):
        (self.root / "one.txt").unlink()
        with self.assertRaises(FileNotFoundError):
            verify_external_sources(self.manifest, self.root)

    def test_explicit_same_size_corruption_fails_hash_check(self):
        (self.root / "one.txt").write_bytes(b"wrong")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verify_external_sources(self.manifest, self.root)

    def test_explicit_changed_size_fails(self):
        (self.root / "one.txt").write_bytes(b"truncated")
        with self.assertRaisesRegex(ValueError, "size mismatch"):
            verify_external_sources(self.manifest, self.root)


if __name__ == "__main__":
    unittest.main()
