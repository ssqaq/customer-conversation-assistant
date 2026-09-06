import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import publish
import release


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        shutil.copytree(release.REPO / release.NAME, self.repo / release.NAME)
        self.archive, self.manifest = release.build(self.repo / release.NAME, self.repo / "dist")
        version, _ = release.validate(self.repo / release.NAME)
        self.tag = f"v{version}"
        self.commit = "a" * 40
        self.calls = []
        self.existing = []
        self.corrupt = False
        self.fail_upload = False
        self.addCleanup(patch.stopall)
        patch.object(publish, "REPO", self.repo).start()
        patch.dict(os.environ, RELEASE_TAG=self.tag, GITHUB_REPOSITORY="example/test", GITHUB_SHA=self.commit).start()
        patch.object(publish, "gh", side_effect=self.fake_gh).start()

    def fake_gh(self, *args):
        self.calls.append(args)
        if args[0] == "api":
            return json.dumps([self.existing])
        if args[:2] == ("release", "upload") and self.fail_upload:
            raise RuntimeError("simulated upload failure")
        if args[:2] == ("release", "download"):
            folder = Path(args[args.index("--dir") + 1])
            shutil.copy2(self.archive, folder)
            shutil.copy2(self.manifest, folder)
            if self.corrupt:
                (folder / self.manifest.name).write_text("{}", encoding="utf-8")
        if args[:2] == ("release", "view"):
            if args[-1] == "assets":
                return json.dumps({"assets": [{"name": p.name} for p in (self.archive, self.manifest)]})
            return json.dumps({"isDraft": False, "url": "https://example.test/release"})
        return ""

    def assert_not_published(self):
        self.assertFalse(any(args[:2] == ("release", "edit") for args in self.calls))

    def test_publish_only_after_download(self):
        publish.main()
        operations = [args[:2] for args in self.calls]
        self.assertLess(operations.index(("release", "download")), operations.index(("release", "edit")))

    def test_corrupted_download_stays_draft(self):
        self.corrupt = True
        with self.assertRaisesRegex(ValueError, "Manifest"):
            publish.main()
        self.assert_not_published()

    def test_upload_failure_stays_draft(self):
        self.fail_upload = True
        with self.assertRaisesRegex(RuntimeError, "upload"):
            publish.main()
        self.assert_not_published()

    def test_published_version_cannot_be_overwritten(self):
        self.existing = [{"tag_name": self.tag, "draft": False, "target_commitish": self.commit}]
        with self.assertRaisesRegex(ValueError, "Refusing"):
            publish.main()
        self.assertFalse(any(args[:2] == ("release", "upload") for args in self.calls))

    def test_draft_for_other_commit_cannot_be_overwritten(self):
        self.existing = [{"tag_name": self.tag, "draft": True, "target_commitish": "b" * 40}]
        with self.assertRaisesRegex(ValueError, "Refusing"):
            publish.main()
        self.assert_not_published()

    def test_retry_same_draft(self):
        self.existing = [{"tag_name": self.tag, "draft": True, "target_commitish": self.commit}]
        publish.main()
        self.assertFalse(any(args[:2] == ("release", "create") for args in self.calls))
        self.assertTrue(any(args[:2] == ("release", "edit") for args in self.calls))


if __name__ == "__main__":
    unittest.main()
