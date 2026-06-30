#!/usr/bin/env python3
"""Manage MaxTAC Source scan worklists and coverage receipts."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".m", ".mm",
    ".go", ".rs", ".java", ".kt", ".kts", ".scala", ".swift",
    ".py", ".rb", ".php", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".cs", ".fs", ".fsx", ".vb", ".erl", ".ex", ".exs", ".clj", ".cljs",
    ".sh", ".bash", ".zsh", ".ps1", ".psm1", ".sql", ".graphql",
    ".yaml", ".yml", ".json", ".toml", ".xml", ".proto", ".thrift",
    ".tf", ".bzl", ".gradle", ".cmake", ".mk", ".dockerfile",
}
SOURCE_FILENAMES = {
    "Dockerfile", "Makefile", "CMakeLists.txt", "BUILD", "WORKSPACE",
    "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json",
    "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "pom.xml",
    "build.gradle", "settings.gradle", "requirements.txt", "pyproject.toml",
}
EXCLUDED_PARTS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "third_party",
    "dist", "build", "out", "target", ".next", ".venv", "venv",
    "__pycache__", ".gradle", ".idea", ".vscode",
}
DISPOSITIONS = ("open", "reported", "no_issue_found", "rejected", "not_applicable", "needs_follow_up", "deferred")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(value: str, default: str = "scan") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._").lower()
    return cleaned or default


def run_git(repo: Path, args: list[str]) -> list[str]:
    command = ["git", "-C", str(repo), *args]
    try:
        completed = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise SystemExit(f"git command failed: {' '.join(command)}\n{detail}") from exc
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def is_source_like(path_text: str) -> bool:
    path = Path(path_text)
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.name in SOURCE_FILENAMES:
        return True
    if path.suffix.lower() in SOURCE_EXTENSIONS:
        return True
    return False


def normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/").lstrip("./")


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        normalized = normalize_path(value)
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def repo_files(repo: Path, scopes: list[str], include_non_source: bool) -> list[str]:
    scope_values = scopes or ["."]
    try:
        files = run_git(repo, ["ls-files", "--", *scope_values])
    except SystemExit:
        files = []
    for scope in scope_values:
        base = repo / scope
        if base.is_file():
            files.append(str(base.relative_to(repo)))
            continue
        normalized_scope = normalize_path(scope).rstrip("/")
        has_tracked_scope = normalized_scope in {"", "."} or any(
            normalize_path(path) == normalized_scope or normalize_path(path).startswith(f"{normalized_scope}/")
            for path in files
        )
        if base.exists() and not has_tracked_scope:
            for child in base.rglob("*"):
                if child.is_file():
                    files.append(str(child.relative_to(repo)))
    return unique([path for path in files if include_non_source or is_source_like(path)])


def diff_files(repo: Path, base: str | None, head: str | None, include_non_source: bool) -> list[str]:
    if base and head:
        files = run_git(repo, ["diff", "--name-only", "--diff-filter=ACMRT", base, head, "--"])
    elif base:
        files = run_git(repo, ["diff", "--name-only", "--diff-filter=ACMRT", base, "--"])
    else:
        files = run_git(repo, ["diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"])
        files.extend(run_git(repo, ["ls-files", "--others", "--exclude-standard"]))
    return unique([path for path in files if include_non_source or is_source_like(path)])


def scan_dir(root: Path, scan_id: str) -> Path:
    return root / "contracts" / "source-scans" / scan_id


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return payload


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(row, dict):
            raise SystemExit(f"{path}:{line_number}: expected object row")
        rows.append(row)
    return rows


def load_scan(scan_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    metadata = read_json(scan_path / "metadata.json")
    worklist = read_jsonl(scan_path / "worklist.jsonl")
    coverage = read_jsonl(scan_path / "coverage.jsonl")
    return metadata, worklist, coverage


def cmd_init(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    repo = Path(args.target_path).resolve()
    scan_id = args.scan_id or f"{args.mode}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    destination = scan_dir(root, scan_id)
    if destination.exists() and not args.force:
        raise SystemExit(f"scan already exists: {destination}")
    if args.mode in {"repo", "scoped"}:
        files = repo_files(repo, args.scope or ["."], args.include_non_source)
    else:
        files = diff_files(repo, args.base, args.head, args.include_non_source)
    rows = [
        {
            "row_id": f"src-{index + 1:04d}",
            "path": path,
            "kind": "source",
            "origin": args.mode,
        }
        for index, path in enumerate(files)
    ]
    coverage = [
        {
            "row_id": row["row_id"],
            "path": row["path"],
            "risk_area": "",
            "disposition": "open",
            "finding_ids": [],
            "receipt_ref": "",
            "notes": "",
        }
        for row in rows
    ]
    metadata = {
        "document_type": "maxtac.source_scan",
        "schema_version": "1.0",
        "scan_id": scan_id,
        "mode": args.mode,
        "target_path": str(repo),
        "base": args.base or "",
        "head": args.head or "",
        "scope": args.scope or ["."],
        "created_at": now(),
        "updated_at": now(),
        "worklist_count": len(rows),
    }
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "receipts").mkdir(exist_ok=True)
    write_json(destination / "metadata.json", metadata)
    write_jsonl(destination / "worklist.jsonl", rows)
    write_jsonl(destination / "coverage.jsonl", coverage)
    print(destination)


def row_matches(row: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.row_id and row.get("row_id") == args.row_id:
        return True
    if args.path and normalize_path(str(row.get("path", ""))) == normalize_path(args.path):
        return True
    return False


def cmd_receipt(args: argparse.Namespace) -> None:
    scan_path = Path(args.scan_dir)
    metadata, worklist, coverage = load_scan(scan_path)
    matches = [row for row in coverage if row_matches(row, args)]
    if not matches and args.add_supporting and args.path:
        next_index = len(coverage) + 1
        row = {
            "row_id": f"src-{next_index:04d}",
            "path": normalize_path(args.path),
            "risk_area": "",
            "disposition": "open",
            "finding_ids": [],
            "receipt_ref": "",
            "notes": "",
        }
        coverage.append(row)
        worklist.append({"row_id": row["row_id"], "path": row["path"], "kind": "supporting", "origin": "supporting"})
        matches = [row]
    if len(matches) != 1:
        raise SystemExit("receipt target must match exactly one coverage row; pass --row-id or --path")
    row = matches[0]
    receipt = {
        "row_id": row["row_id"],
        "path": row["path"],
        "disposition": args.disposition,
        "risk_area": args.risk_area,
        "finding_ids": args.finding_id or [],
        "notes": args.note,
        "evidence": args.evidence or [],
        "closed_at": now(),
    }
    receipt_ref = f"receipts/{row['row_id']}.json"
    write_json(scan_path / receipt_ref, receipt)
    row.update(
        {
            "risk_area": args.risk_area,
            "disposition": args.disposition,
            "finding_ids": args.finding_id or [],
            "receipt_ref": receipt_ref,
            "notes": args.note,
        }
    )
    metadata["updated_at"] = now()
    metadata["worklist_count"] = len(worklist)
    write_json(scan_path / "metadata.json", metadata)
    write_jsonl(scan_path / "worklist.jsonl", worklist)
    write_jsonl(scan_path / "coverage.jsonl", coverage)
    print(receipt_ref)


def cmd_thin_close(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    repo = Path(args.target_path).resolve()
    paths = unique(args.path or [])
    if not paths:
        raise SystemExit("thin-close requires at least one --path")
    default_id = f"thin-{slug(Path(paths[0]).stem)}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    scan_id = args.scan_id or default_id
    destination = scan_dir(root, scan_id)
    if destination.exists() and not args.force:
        raise SystemExit(f"scan already exists: {destination}")

    rows = [
        {
            "row_id": f"src-{index + 1:04d}",
            "path": path,
            "kind": "source",
            "origin": "thin-closure",
        }
        for index, path in enumerate(paths)
    ]
    coverage: list[dict[str, Any]] = []
    metadata = {
        "document_type": "maxtac.source_scan",
        "schema_version": "1.0",
        "scan_id": scan_id,
        "mode": "thin-closure",
        "target_path": str(repo),
        "base": "",
        "head": "",
        "scope": paths,
        "created_at": now(),
        "updated_at": now(),
        "worklist_count": len(rows),
        "closure_profile": "thin",
        "closure_rationale": args.note,
    }
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "receipts").mkdir(exist_ok=True)
    for row in rows:
        receipt_ref = f"receipts/{row['row_id']}.json"
        receipt = {
            "row_id": row["row_id"],
            "path": row["path"],
            "disposition": args.disposition,
            "risk_area": args.risk_area,
            "finding_ids": args.finding_id or [],
            "notes": args.note,
            "evidence": args.evidence or [],
            "closed_at": now(),
            "closure_profile": "thin",
        }
        write_json(destination / receipt_ref, receipt)
        coverage.append(
            {
                "row_id": row["row_id"],
                "path": row["path"],
                "risk_area": args.risk_area,
                "disposition": args.disposition,
                "finding_ids": args.finding_id or [],
                "receipt_ref": receipt_ref,
                "notes": args.note,
            }
        )
    write_json(destination / "metadata.json", metadata)
    write_jsonl(destination / "worklist.jsonl", rows)
    write_jsonl(destination / "coverage.jsonl", coverage)
    errors = validation_errors(destination)
    if errors:
        raise SystemExit("\n".join(errors))
    print(destination)
    for row in coverage:
        print(row["receipt_ref"])


def coverage_counts(coverage: list[dict[str, Any]]) -> dict[str, int]:
    counts = {disposition: 0 for disposition in DISPOSITIONS}
    for row in coverage:
        disposition = str(row.get("disposition") or "open")
        counts[disposition] = counts.get(disposition, 0) + 1
    return counts


def validation_errors(scan_path: Path) -> list[str]:
    _metadata, worklist, coverage = load_scan(scan_path)
    errors: list[str] = []
    worklist_ids = {row.get("row_id") for row in worklist}
    coverage_ids = {row.get("row_id") for row in coverage}
    for missing in sorted(worklist_ids - coverage_ids):
        errors.append(f"missing coverage row for {missing}")
    for row in coverage:
        row_id = str(row.get("row_id", ""))
        disposition = str(row.get("disposition") or "open")
        if disposition not in DISPOSITIONS:
            errors.append(f"{row_id}: unknown disposition {disposition}")
        if disposition == "open":
            errors.append(f"{row_id}: row is still open")
        if disposition in {"reported", "no_issue_found", "rejected", "not_applicable", "needs_follow_up", "deferred"}:
            receipt_ref = str(row.get("receipt_ref") or "")
            if not receipt_ref:
                errors.append(f"{row_id}: closed row missing receipt_ref")
            elif not (scan_path / receipt_ref).exists():
                errors.append(f"{row_id}: receipt file missing: {receipt_ref}")
            if not str(row.get("notes") or "").strip():
                errors.append(f"{row_id}: closed row missing notes")
    return errors


def cmd_status(args: argparse.Namespace) -> None:
    scan_path = Path(args.scan_dir)
    metadata, worklist, coverage = load_scan(scan_path)
    counts = coverage_counts(coverage)
    print(f"MaxTAC Source scan: {metadata.get('scan_id')} ({metadata.get('mode')})")
    print(f"- worklist rows: {len(worklist)}")
    for key in DISPOSITIONS:
        if counts.get(key):
            print(f"- {key}: {counts[key]}")


def cmd_validate(args: argparse.Namespace) -> None:
    scan_path = Path(args.scan_dir)
    errors = validation_errors(scan_path)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"validated {scan_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MaxTAC Source scan helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--root", default=".")
    init.add_argument("--target-path", default=".")
    init.add_argument("--mode", choices=("repo", "scoped", "diff", "working-tree"), required=True)
    init.add_argument("--scan-id")
    init.add_argument("--base")
    init.add_argument("--head")
    init.add_argument("--scope", action="append")
    init.add_argument("--include-non-source", action="store_true")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    receipt = subparsers.add_parser("receipt")
    receipt.add_argument("--scan-dir", required=True)
    receipt.add_argument("--row-id")
    receipt.add_argument("--path")
    receipt.add_argument("--disposition", choices=DISPOSITIONS[1:], required=True)
    receipt.add_argument("--risk-area", required=True)
    receipt.add_argument("--finding-id", action="append")
    receipt.add_argument("--note", required=True)
    receipt.add_argument("--evidence", action="append")
    receipt.add_argument("--add-supporting", action="store_true")
    receipt.set_defaults(func=cmd_receipt)

    thin_close = subparsers.add_parser("thin-close", help="Create and close an exact-path thin source scan")
    thin_close.add_argument("--root", default=".")
    thin_close.add_argument("--target-path", default=".")
    thin_close.add_argument("--scan-id")
    thin_close.add_argument("--path", action="append", required=True)
    thin_close.add_argument("--disposition", choices=DISPOSITIONS[1:], default="no_issue_found")
    thin_close.add_argument("--risk-area", required=True)
    thin_close.add_argument("--finding-id", action="append")
    thin_close.add_argument("--note", required=True)
    thin_close.add_argument("--evidence", action="append")
    thin_close.add_argument("--force", action="store_true")
    thin_close.set_defaults(func=cmd_thin_close)

    status = subparsers.add_parser("status")
    status.add_argument("--scan-dir", required=True)
    status.set_defaults(func=cmd_status)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--scan-dir", required=True)
    validate.add_argument("--allow-deferred", action="store_true", help="Compatibility no-op; explicit needs_follow_up and deferred receipts are already valid closures")
    validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
