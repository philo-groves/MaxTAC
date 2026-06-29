#!/usr/bin/env python3
"""Diff directories or common package archives for supply-chain artifact review."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ARCHIVE_SUFFIXES = (".zip", ".whl", ".jar", ".nupkg", ".tgz", ".tar.gz", ".tar.bz2", ".tar.xz", ".tar")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_archive(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in ARCHIVE_SUFFIXES)


def safe_destination(root: Path, member_name: str) -> Path:
    destination = (root / member_name).resolve()
    root_resolved = root.resolve()
    if destination != root_resolved and root_resolved not in destination.parents:
        raise SystemExit(f"archive path escapes extraction root: {member_name}")
    return destination


def extract_zip(path: Path, root: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            safe_destination(root, member.filename)
        archive.extractall(root)


def extract_tar(path: Path, root: Path) -> None:
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            safe_destination(root, member.name)
            if member.issym() or member.islnk():
                linkname = Path(member.linkname)
                if linkname.is_absolute() or ".." in linkname.parts:
                    raise SystemExit(f"archive link escapes extraction root: {member.name} -> {member.linkname}")
        archive.extractall(root)


def materialize(input_path: Path, work_root: Path, label: str) -> Path:
    if input_path.is_dir():
        return input_path
    if not input_path.is_file():
        raise SystemExit(f"input does not exist: {input_path}")
    target = work_root / label
    target.mkdir(parents=True, exist_ok=True)
    if is_archive(input_path):
        if zipfile.is_zipfile(input_path):
            extract_zip(input_path, target)
        elif tarfile.is_tarfile(input_path):
            extract_tar(input_path, target)
        else:
            raise SystemExit(f"unsupported archive format: {input_path}")
        return target
    shutil.copy2(input_path, target / input_path.name)
    return target


def posix_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def file_entry(path: Path, root: Path) -> dict[str, Any]:
    info = path.lstat()
    mode = stat.S_IMODE(info.st_mode)
    rel = posix_rel(path, root)
    if path.is_symlink():
        return {
            "path": rel,
            "type": "symlink",
            "mode": oct(mode),
            "target": os.readlink(path),
        }
    if path.is_file():
        return {
            "path": rel,
            "type": "file",
            "mode": oct(mode),
            "size": info.st_size,
            "sha256": sha256_file(path),
        }
    if path.is_dir():
        return {
            "path": rel,
            "type": "directory",
            "mode": oct(mode),
        }
    return {
        "path": rel,
        "type": "other",
        "mode": oct(mode),
    }


def inventory(root: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        rel = posix_rel(path, root)
        if rel:
            records[rel] = file_entry(path, root)
    return records


def comparable(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key not in {"path"}}


def diff_records(left: dict[str, dict[str, Any]], right: dict[str, dict[str, Any]]) -> dict[str, Any]:
    left_paths = set(left)
    right_paths = set(right)
    added = sorted(right_paths - left_paths)
    removed = sorted(left_paths - right_paths)
    common = sorted(left_paths & right_paths)
    changed = [path for path in common if comparable(left[path]) != comparable(right[path])]
    unchanged = [path for path in common if comparable(left[path]) == comparable(right[path])]
    return {
        "summary": {
            "left_files": len(left),
            "right_files": len(right),
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "unchanged": len(unchanged),
        },
        "added": [right[path] for path in added],
        "removed": [left[path] for path in removed],
        "changed": [{"path": path, "left": left[path], "right": right[path]} for path in changed],
        "unchanged": unchanged,
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    summary = result["summary"]
    lines = [
        "# Supply-Chain Artifact Diff",
        "",
        f"- Left: {result['left_input']}",
        f"- Right: {result['right_input']}",
        f"- Added: {summary['added']}",
        f"- Removed: {summary['removed']}",
        f"- Changed: {summary['changed']}",
        f"- Unchanged: {summary['unchanged']}",
        "",
    ]
    for section in ["added", "removed"]:
        entries = result[section]
        if entries:
            lines.extend([f"## {section.title()}", ""])
            for item in entries[:200]:
                lines.append(f"- `{item.get('path')}` {item.get('type')} {item.get('sha256', item.get('target', ''))}")
            if len(entries) > 200:
                lines.append(f"- ... {len(entries) - 200} more")
            lines.append("")
    if result["changed"]:
        lines.extend(["## Changed", ""])
        for item in result["changed"][:200]:
            left = item["left"]
            right = item["right"]
            lines.append(f"- `{item['path']}` {left.get('type')} -> {right.get('type')} {left.get('sha256', left.get('target', ''))} -> {right.get('sha256', right.get('target', ''))}")
        if len(result["changed"]) > 200:
            lines.append(f"- ... {len(result['changed']) - 200} more")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def command_diff(args: argparse.Namespace) -> None:
    left_input = Path(args.left)
    right_input = Path(args.right)
    with tempfile.TemporaryDirectory(prefix="maxtac-artifact-diff-") as temp_dir:
        work_root = Path(temp_dir)
        left_root = materialize(left_input, work_root, "left")
        right_root = materialize(right_input, work_root, "right")
        result = diff_records(inventory(left_root), inventory(right_root))
        result["left_input"] = str(left_input)
        result["right_input"] = str(right_input)
        if args.case_id:
            result["case_id"] = args.case_id
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.markdown:
            write_markdown(Path(args.markdown), result)
        summary = result["summary"]
        print(f"added={summary['added']} removed={summary['removed']} changed={summary['changed']} unchanged={summary['unchanged']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    diff = subparsers.add_parser("diff", help="diff two directories or archives")
    diff.add_argument("--left", required=True)
    diff.add_argument("--right", required=True)
    diff.add_argument("--output", required=True)
    diff.add_argument("--markdown")
    diff.add_argument("--case-id")
    diff.set_defaults(func=command_diff)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
