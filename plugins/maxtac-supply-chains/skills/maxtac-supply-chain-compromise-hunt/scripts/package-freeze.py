#!/usr/bin/env python3
"""Create and maintain a local supply-chain evidence freeze manifest."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_manifest_path(case_id: str) -> Path:
    return Path("audits") / "supply-chain" / case_id / "freeze" / "manifest.json"


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid manifest JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("manifest root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path, *, category: str, label: str | None) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"artifact must be a file: {path}")
    stat = path.stat()
    return {
        "label": label or path.name,
        "category": category,
        "path": str(path),
        "size": stat.st_size,
        "sha256": sha256_file(path),
        "mtime_utc": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "captured_at": utc_now(),
    }


def make_manifest(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "case_id": args.case_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "target": args.target or "",
        "ecosystem": args.ecosystem or "",
        "coordinates": args.coordinates or "",
        "version": args.version or "",
        "source_url": args.source_url or "",
        "artifact_url": args.artifact_url or "",
        "observed_at": args.observed_at or utc_now(),
        "artifacts": [],
        "metadata": {},
        "notes": [],
    }


def command_create(args: argparse.Namespace) -> None:
    output = Path(args.output) if args.output else default_manifest_path(args.case_id)
    manifest = make_manifest(args)
    write_json(output, manifest)
    print(output)


def command_add_artifact(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest)
    manifest = read_json(manifest_path)
    artifacts = manifest.setdefault("artifacts", [])
    if not isinstance(artifacts, list):
        raise SystemExit("manifest field artifacts must be a list")
    artifacts.append(file_record(Path(args.path), category=args.category, label=args.label))
    manifest["updated_at"] = utc_now()
    write_json(manifest_path, manifest)
    print(f"added {args.path}")


def command_note(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest)
    manifest = read_json(manifest_path)
    notes = manifest.setdefault("notes", [])
    if not isinstance(notes, list):
        raise SystemExit("manifest field notes must be a list")
    notes.append({"at": utc_now(), "text": args.text})
    manifest["updated_at"] = utc_now()
    write_json(manifest_path, manifest)
    print("noted")


def lint_manifest(manifest: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for field in ["case_id", "target", "ecosystem", "coordinates"]:
        if not str(manifest.get(field, "")).strip():
            warnings.append(f"missing {field}")
    if not str(manifest.get("source_url", "")).strip() and not str(manifest.get("artifact_url", "")).strip():
        warnings.append("missing both source_url and artifact_url")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        warnings.append("no artifacts recorded")
        return warnings
    seen: set[str] = set()
    for index, item in enumerate(artifacts, start=1):
        if not isinstance(item, dict):
            warnings.append(f"artifact {index} is not an object")
            continue
        digest = str(item.get("sha256", ""))
        if len(digest) != 64:
            warnings.append(f"artifact {index} missing valid sha256")
        if digest in seen:
            warnings.append(f"artifact {index} duplicates sha256 {digest}")
        seen.add(digest)
        if not item.get("path"):
            warnings.append(f"artifact {index} missing path")
        if not item.get("category"):
            warnings.append(f"artifact {index} missing category")
    return warnings


def command_lint(args: argparse.Namespace) -> None:
    warnings = lint_manifest(read_json(Path(args.manifest)))
    if warnings:
        for warning in warnings:
            print(f"WARN: {warning}")
        raise SystemExit(1)
    print("OK")


def command_summary(args: argparse.Namespace) -> None:
    manifest = read_json(Path(args.manifest))
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []
    print(f"# Evidence Freeze: {manifest.get('case_id', '')}")
    print()
    print(f"- Target: {manifest.get('target', '')}")
    print(f"- Ecosystem: {manifest.get('ecosystem', '')}")
    print(f"- Coordinates: {manifest.get('coordinates', '')}")
    print(f"- Version: {manifest.get('version', '')}")
    print(f"- Observed: {manifest.get('observed_at', '')}")
    print(f"- Artifacts: {len(artifacts)}")
    for item in artifacts:
        if not isinstance(item, dict):
            continue
        print(f"  - {item.get('label', '')}: {item.get('category', '')} {item.get('sha256', '')} {item.get('path', '')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="create a new evidence freeze manifest")
    create.add_argument("--case-id", required=True)
    create.add_argument("--target")
    create.add_argument("--ecosystem")
    create.add_argument("--coordinates")
    create.add_argument("--version")
    create.add_argument("--source-url")
    create.add_argument("--artifact-url")
    create.add_argument("--observed-at")
    create.add_argument("--output")
    create.set_defaults(func=command_create)

    add = subparsers.add_parser("add-artifact", help="hash and add a local artifact file")
    add.add_argument("--manifest", required=True)
    add.add_argument("--path", required=True)
    add.add_argument("--category", default="artifact")
    add.add_argument("--label")
    add.set_defaults(func=command_add_artifact)

    note = subparsers.add_parser("note", help="append an evidence note")
    note.add_argument("--manifest", required=True)
    note.add_argument("--text", required=True)
    note.set_defaults(func=command_note)

    lint = subparsers.add_parser("lint", help="validate a manifest for common proof gaps")
    lint.add_argument("--manifest", required=True)
    lint.set_defaults(func=command_lint)

    summary = subparsers.add_parser("summary", help="print a markdown summary")
    summary.add_argument("--manifest", required=True)
    summary.set_defaults(func=command_summary)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
