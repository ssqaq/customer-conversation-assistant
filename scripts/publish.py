"""Upload to a draft, verify downloaded bytes, then publish. Used by tag CI only."""

import json
import os
from pathlib import Path
import subprocess
import tempfile

from release import NAME, REPO, require, validate, verify


def gh(*args):
    return subprocess.check_output(["gh", *args], text=True, encoding="utf-8").strip()


def main():
    tag = os.environ["RELEASE_TAG"]
    repo = os.environ["GITHUB_REPOSITORY"]
    commit = os.environ["GITHUB_SHA"]
    root = REPO / NAME
    version, _ = validate(root, tag)
    archive = REPO / "dist" / f"{NAME}-{version}.zip"
    manifest = REPO / "dist" / f"{NAME}-{version}-manifest.json"
    verify(root, archive, manifest, tag)
    releases = json.loads(gh("api", "--paginate", "--slurp", f"repos/{repo}/releases?per_page=100"))
    existing = [item for page in releases for item in page if item["tag_name"] == tag]
    require(len(existing) <= 1, "Ambiguous release")
    if existing:
        release = existing[0]
        require(release["draft"] and release["target_commitish"] == commit, "Refusing to change an existing published or unrelated release")
    else:
        with tempfile.TemporaryDirectory() as temporary:
            notes = Path(temporary) / "notes.md"
            notes.write_text(
                f"客户沟通助手 {version}\n\n"
                "客户回复支持自然表达与得体措辞，保留数字、条件、联系方式和真实处理状态。\n\n"
                "此版本由 GitHub Actions 校验、打包并下载回查后发布。"
                "包内只有三个 Skill 文件，无运行脚本依赖。自动校验不代替回复效果人工验收。\n\n"
                f"构建提交：`{commit}`\n",
                encoding="utf-8",
            )
            gh("release", "create", tag, "--repo", repo, "--draft", "--verify-tag", "--target", commit, "--title", f"客户沟通助手 {tag}", "--notes-file", str(notes))
    gh("release", "upload", tag, str(archive), str(manifest), "--repo", repo, "--clobber")
    with tempfile.TemporaryDirectory() as temporary:
        gh("release", "download", tag, "--repo", repo, "--dir", temporary, "--pattern", archive.name, "--pattern", manifest.name)
        downloaded = Path(temporary)
        verify(root, downloaded / archive.name, downloaded / manifest.name, tag)
        require((downloaded / archive.name).read_bytes() == archive.read_bytes(), "Downloaded ZIP differs")
        require((downloaded / manifest.name).read_bytes() == manifest.read_bytes(), "Downloaded manifest differs")
    assets = json.loads(gh("release", "view", tag, "--repo", repo, "--json", "assets"))["assets"]
    require({asset["name"] for asset in assets} == {archive.name, manifest.name}, "Unexpected release assets")
    gh("release", "edit", tag, "--repo", repo, "--draft=false", "--latest")
    result = json.loads(gh("release", "view", tag, "--repo", repo, "--json", "isDraft,url"))
    require(result["isDraft"] is False, "Release is still a draft")
    print(result["url"])


if __name__ == "__main__":
    main()
