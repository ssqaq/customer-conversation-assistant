"""Validate and reproducibly package the three-file skill. No runtime dependency."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
from urllib.parse import unquote, urlsplit
import zipfile

import yaml

NAME = "customer-conversation-assistant"
FILES = ("SKILL.md", "agents/openai.yaml", "references/workflows.md")
REPO = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        require(key not in result, f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def headings(text):
    return {
        re.sub(r"[^\w\-\s]", "", line.lstrip("#").strip().lower()).replace(" ", "-")
        for line in text.splitlines() if re.match(r"^#{1,6} ", line)
    }


def validate(root, tag=None):
    root = Path(root)
    require(root.name == NAME and root.is_dir(), "Wrong or missing skill directory")
    entries = [root, *root.rglob("*")]
    require(all(not p.is_symlink() and not p.is_junction() for p in entries), "Links are not allowed")
    actual = {p.relative_to(root).as_posix() for p in entries[1:] if p.is_file()}
    require(actual == set(FILES), f"Unexpected or missing files: {actual ^ set(FILES)}")
    directories = {p.relative_to(root).as_posix() for p in entries[1:] if p.is_dir()}
    require(directories == {"agents", "references"}, "Unexpected directories")
    blobs = {name: (root / name).read_bytes() for name in FILES}
    texts = {}
    for name, data in blobs.items():
        require(data and not data.startswith(b"\xef\xbb\xbf"), f"Empty file or BOM: {name}")
        require(b"\r" not in data and b"\x00" not in data, f"Use LF text without NUL: {name}")
        texts[name] = data.decode("utf-8")
        require(not re.search(r"\b(?:TODO|FIXME|TBD)\b|\[INSERT[^\]]*\]", texts[name]), f"Placeholder: {name}")
    match = re.match(r"\A---\n(.*?)\n---\n", texts["SKILL.md"], re.S)
    require(match is not None, "Invalid frontmatter")
    front = yaml.load(match[1], Loader=UniqueLoader)
    require(isinstance(front, dict), "Frontmatter must be a mapping")
    require(front.get("name") == NAME, "Skill name mismatch")
    description = front.get("description")
    require(isinstance(description, str) and 1 <= len(description) <= 1024, "Invalid description")
    metadata = front.get("metadata")
    require(isinstance(metadata, dict), "Missing metadata")
    version = metadata.get("version")
    require(isinstance(version, str) and re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version), "Invalid version")
    require(tag is None or tag == f"v{version}", "Tag does not match skill version")
    ui = yaml.load(texts["agents/openai.yaml"], Loader=UniqueLoader)
    require(isinstance(ui, dict), "UI YAML must be a mapping")
    interface = ui.get("interface", {})
    require(isinstance(interface, dict), "Invalid interface")
    require(isinstance(interface.get("display_name"), str) and interface["display_name"].strip(), "Missing display name")
    short = interface.get("short_description", "")
    require(isinstance(short, str) and 25 <= len(short) <= 64, "UI description must have 25-64 characters")
    prompt = interface.get("default_prompt", "")
    require(isinstance(prompt, str) and f"${NAME}" in prompt, "Missing invocation example")
    require(ui.get("policy", {}).get("allow_implicit_invocation") is True, "Automatic invocation must remain enabled")
    for name, text in texts.items():
        if not name.endswith(".md"):
            continue
        for link in re.findall(r"\[[^\]\n]*\]\(([^)\s]+)\)", text):
            url = urlsplit(link)
            if url.scheme:
                require(url.scheme == "https" and bool(url.netloc), f"Unsupported link: {link}")
                continue
            require(not url.netloc and not url.query and "\\" not in link, f"Invalid local link: {link}")
            target = ((root / name).parent / unquote(url.path)).resolve() if url.path else (root / name).resolve()
            require(target.is_relative_to(root.resolve()) and target.is_file(), f"Broken local link: {link}")
            if url.fragment:
                require(unquote(url.fragment) in headings(target.read_text(encoding="utf-8")), f"Broken anchor: {link}")
    return version, blobs


def manifest_for(version, blobs, archive):
    return {
        "schema_version": 1,
        "name": NAME,
        "version": version,
        "archive": {"name": archive.name, "bytes": archive.stat().st_size, "sha256": digest(archive.read_bytes())},
        "files": [{"path": f"{NAME}/{name}", "bytes": len(data), "sha256": digest(data)} for name, data in sorted(blobs.items())],
    }


def build(root, out, tag=None):
    version, blobs = validate(root, tag)
    out = Path(out)
    require(not out.resolve().is_relative_to(Path(root).resolve()), "Build output must be outside the skill")
    out.mkdir(parents=True, exist_ok=True)
    archive = out / f"{NAME}-{version}.zip"
    manifest = out / f"{NAME}-{version}-manifest.json"
    for path in (archive, manifest):
        require(not path.exists(), f"Refusing to overwrite: {path}")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED) as bundle:
        for name, data in sorted(blobs.items()):
            info = zipfile.ZipInfo(f"{NAME}/{name}", (2020, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            bundle.writestr(info, data)
    manifest.write_text(json.dumps(manifest_for(version, blobs, archive), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    verify(root, archive, manifest, tag)
    return archive, manifest


def verify(root, archive, manifest, tag=None):
    version, blobs = validate(root, tag)
    archive, manifest = Path(archive), Path(manifest)
    require(archive.name == f"{NAME}-{version}.zip", "Wrong archive name")
    expected = {f"{NAME}/{name}": data for name, data in blobs.items()}
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        require(len(members) == len(expected) and {i.filename for i in members} == set(expected), "ZIP file list mismatch, duplicate or unsafe path")
        for info in members:
            require(stat.S_ISREG(info.external_attr >> 16), "ZIP entry is not a regular file")
            require(info.file_size == len(expected[info.filename]), "ZIP member size mismatch")
            require(bundle.read(info) == expected[info.filename], f"ZIP bytes differ from source: {info.filename}")
    actual = json.loads(manifest.read_text(encoding="utf-8"))
    require(actual == manifest_for(version, blobs, archive), "Manifest does not match source and ZIP")
    return version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build", "verify"))
    parser.add_argument("--root", type=Path, default=REPO / NAME)
    parser.add_argument("--tag")
    parser.add_argument("--out", type=Path, default=REPO / "dist")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        print(f"Valid skill: {validate(args.root, args.tag)[0]}")
    elif args.command == "build":
        for path in build(args.root, args.out, args.tag):
            print(path)
    else:
        require(args.archive and args.manifest, "verify requires --archive and --manifest")
        print(f"Verified package: {verify(args.root, args.archive, args.manifest, args.tag)}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, yaml.YAMLError, zipfile.BadZipFile) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        sys.exit(1)
