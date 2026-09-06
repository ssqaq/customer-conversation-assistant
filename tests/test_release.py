import json
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / release.NAME
        shutil.copytree(release.REPO / release.NAME, self.root)
        self.version, _ = release.validate(self.root)

    def edit(self, filename, transform):
        path = self.root / filename
        path.write_text(transform(path.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")

    def package(self):
        return release.build(self.root, self.base / "dist")

    def rewrite_zip(self, change):
        archive, manifest = self.package()
        with zipfile.ZipFile(archive) as bundle:
            entries = [(info, bundle.read(info)) for info in bundle.infolist()]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(archive, "w") as bundle:
                for info, data in change(entries):
                    bundle.writestr(info, data)
        # Even an attacker-updated checksum cannot replace comparison to source.
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["archive"]["sha256"] = release.digest(archive.read_bytes())
        data["archive"]["bytes"] = archive.stat().st_size
        manifest.write_text(json.dumps(data), encoding="utf-8")
        return archive, manifest

    def test_valid_build_and_tag(self):
        archive, manifest = self.package()
        self.assertEqual(release.verify(self.root, archive, manifest, f"v{self.version}"), self.version)

    def test_reproducible_build(self):
        first = self.package()
        second = release.build(self.root, self.base / "second")
        self.assertEqual([p.read_bytes() for p in first], [p.read_bytes() for p in second])

    def test_wrong_tag(self):
        with self.assertRaisesRegex(ValueError, "Tag"):
            release.validate(self.root, "v99.0.0")

    def test_invalid_version(self):
        self.edit("SKILL.md", lambda s: s.replace(self.version, "01.1.0"))
        with self.assertRaisesRegex(ValueError, "version"):
            release.validate(self.root)

    def test_missing_file(self):
        (self.root / "agents/openai.yaml").unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            release.validate(self.root)

    def test_customer_file_excluded(self):
        (self.root / "customer.md").write_text("customer data", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            release.validate(self.root)

    def test_empty_directory_excluded(self):
        (self.root / "customers").mkdir()
        with self.assertRaisesRegex(ValueError, "directories"):
            release.validate(self.root)

    def test_crlf_rejected(self):
        path = self.root / "SKILL.md"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        with self.assertRaisesRegex(ValueError, "LF"):
            release.validate(self.root)

    def test_invalid_utf8(self):
        (self.root / "SKILL.md").write_bytes(b"\xff")
        with self.assertRaises(UnicodeDecodeError):
            release.validate(self.root)

    def test_placeholder(self):
        self.edit("SKILL.md", lambda s: s + "\n[TODO: fill this]\n")
        with self.assertRaisesRegex(ValueError, "Placeholder"):
            release.validate(self.root)

    def test_duplicate_yaml_key(self):
        self.edit("agents/openai.yaml", lambda s: s + "\npolicy: {}\n")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            release.validate(self.root)

    def test_broken_reference(self):
        self.edit("SKILL.md", lambda s: s + "\n[missing](references/missing.md)\n")
        with self.assertRaisesRegex(ValueError, "Broken local"):
            release.validate(self.root)

    def test_broken_anchor(self):
        self.edit("SKILL.md", lambda s: s + "\n[missing](references/workflows.md#nonexistent-anchor)\n")
        with self.assertRaisesRegex(ValueError, "Broken anchor"):
            release.validate(self.root)

    def test_link_path_escape(self):
        (self.base / "outside.md").write_text("outside", encoding="utf-8")
        self.edit("SKILL.md", lambda s: s + "\n[outside](../outside.md)\n")
        with self.assertRaisesRegex(ValueError, "Broken local"):
            release.validate(self.root)

    def test_symlink_rejected(self):
        path = self.root / "SKILL.md"
        outside = self.base / "outside.md"
        path.replace(outside)
        try:
            path.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"Symlink creation unavailable: {error}")
        with self.assertRaisesRegex(ValueError, "Links"):
            release.validate(self.root)

    def test_build_cannot_overwrite(self):
        self.package()
        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.package()

    def test_build_cannot_pollute_skill(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            release.build(self.root, self.root / "dist")

    def test_tampered_zip_with_updated_checksum(self):
        archive, manifest = self.rewrite_zip(lambda entries: [(i, b"x" * len(b)) for i, b in entries])
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            release.verify(self.root, archive, manifest)

    def test_missing_zip_member(self):
        archive, manifest = self.rewrite_zip(lambda entries: entries[:-1])
        with self.assertRaisesRegex(ValueError, "file list"):
            release.verify(self.root, archive, manifest)

    def test_duplicate_zip_member(self):
        archive, manifest = self.rewrite_zip(lambda entries: entries + [entries[0]])
        with self.assertRaisesRegex(ValueError, "file list"):
            release.verify(self.root, archive, manifest)

    def test_unsafe_zip_path(self):
        def change(entries):
            entries[0][0].filename = "../outside.md"
            return entries
        archive, manifest = self.rewrite_zip(change)
        with self.assertRaisesRegex(ValueError, "file list"):
            release.verify(self.root, archive, manifest)

    def test_zip_symlink(self):
        def change(entries):
            entries[0][0].external_attr = (stat.S_IFLNK | 0o777) << 16
            return entries
        archive, manifest = self.rewrite_zip(change)
        with self.assertRaisesRegex(ValueError, "regular file"):
            release.verify(self.root, archive, manifest)

    def test_wrong_manifest(self):
        archive, manifest = self.package()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["version"] = "99.0.0"
        manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Manifest"):
            release.verify(self.root, archive, manifest)


if __name__ == "__main__":
    unittest.main()
