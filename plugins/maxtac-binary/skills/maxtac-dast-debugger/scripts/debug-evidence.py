#!/usr/bin/env python3
"""Collect MaxTAC debugger and runtime instrumentation evidence."""

from __future__ import annotations

import argparse
import json
import secrets
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MANIFEST = "debug-evidence.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def generated_id(prefix: str = "debug") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{timestamp}-{secrets.token_hex(3)}"


def root_path(value: str | None) -> Path:
    root = Path(value or ".").expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Workspace root is not a directory: {root}")
    return root


def ensure_within(root: Path, path: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise SystemExit(f"{label} escapes workspace root: {resolved_path}") from exc
    return resolved_path


def case_dir(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        if len(path.parts) == 1:
            path = root / "proof" / value
        else:
            path = root / path
    return ensure_within(root, path, "debug evidence case")


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_record(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Artifact not found: {path}")
    record: dict[str, Any] = {"path": str(path.resolve())}
    if path.is_file():
        record.update({"kind": "file", "size": path.stat().st_size, "sha256": sha256_file(path)})
    elif path.is_dir():
        record.update({"kind": "directory", "files": sum(1 for item in path.rglob("*") if item.is_file())})
    else:
        record["kind"] = "other"
    return record


def copy_artifact(path: Path, dest_dir: Path, category: str) -> dict[str, Any]:
    source = path_record(path)
    category_dir = dest_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)
    destination = category_dir / path.name
    if destination.exists():
        destination = category_dir / f"{path.stem}-{secrets.token_hex(3)}{path.suffix}"
    if path.is_dir():
        shutil.copytree(path, destination)
    else:
        shutil.copy2(path, destination)
    copied = path_record(destination)
    copied["source"] = source
    copied["category"] = category
    return copied


def parse_key_values(values: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise SystemExit(f"Expected KEY=VALUE: {value}")
        key, item = value.split("=", 1)
        if not key.strip():
            raise SystemExit(f"Empty key in: {value}")
        result[key.strip()] = item
    return result


def run_capture(command: str, timeout: int) -> dict[str, Any]:
    record: dict[str, Any] = {"time": now(), "command": command}
    try:
        completed = subprocess.run(
            command,
            shell=True,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except OSError as exc:
        record["error"] = str(exc)
        return record
    except subprocess.TimeoutExpired as exc:
        record["error"] = "timed out"
        record["timeout_seconds"] = timeout
        record["stdout"] = (exc.stdout or "").strip() if isinstance(exc.stdout, str) else ""
        record["stderr"] = (exc.stderr or "").strip() if isinstance(exc.stderr, str) else ""
        return record
    record.update(
        {
            "exit_code": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    )
    return record


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_manifest(path: Path) -> dict[str, Any]:
    manifest_path = path / MANIFEST
    if not manifest_path.exists():
        raise SystemExit(f"Debug evidence manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"{manifest_path} must contain a JSON object")
    return payload


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now()
    write_json(path / MANIFEST, manifest)


def add_artifacts(
    manifest: dict[str, Any],
    evidence_dir: Path,
    values: list[str] | None,
    category: str,
    *,
    copy: bool,
) -> None:
    for value in values or []:
        path = Path(value).expanduser().resolve()
        record = copy_artifact(path, evidence_dir / "artifacts", category) if copy else path_record(path)
        manifest.setdefault("artifacts", []).append(record)


def cmd_init(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    evidence_id = args.case_id or generated_id()
    evidence_dir = ensure_within(root, root / "proof" / evidence_id, "debug evidence case")
    if evidence_dir.exists() and not args.force:
        raise SystemExit(f"Debug evidence case already exists: {evidence_dir}")
    (evidence_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (evidence_dir / "logs").mkdir(exist_ok=True)

    target_file = Path(args.target_file).expanduser().resolve() if args.target_file else None
    version_capture = run_capture(args.version_command, args.timeout) if args.version_command else None
    tool_version = args.tool_version
    if not tool_version and version_capture and version_capture.get("stdout"):
        tool_version = str(version_capture["stdout"]).splitlines()[0]

    manifest: dict[str, Any] = {
        "version": 1,
        "case_id": evidence_id,
        "created_at": now(),
        "updated_at": now(),
        "tool": {
            "name": args.tool,
            "version": tool_version,
            "version_command": version_capture,
        },
        "target": args.target,
        "target_version": args.target_version,
        "authorization_scope": args.scope,
        "test_environment": args.environment,
        "commands": [],
        "artifacts": [],
        "notes": [args.note] if args.note else [],
    }
    if target_file:
        manifest["target_file"] = path_record(target_file)
    if args.command_line:
        manifest["commands"].append(
            {
                "time": now(),
                "label": "initial-command-line",
                "command": args.command_line,
                "env": parse_key_values(args.env),
                "record_only": True,
            }
        )
    add_artifacts(manifest, evidence_dir, args.artifact, "artifact", copy=not args.no_copy)
    save_manifest(evidence_dir, manifest)
    print(f"Initialized debug evidence case: {evidence_dir}")
    print(f"- manifest: {evidence_dir / MANIFEST}")


def cmd_capture(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    evidence_dir = case_dir(root, args.case)
    manifest = read_manifest(evidence_dir)
    label = args.label or f"command-{len(manifest.get('commands', [])) + 1}"
    command_record = run_capture(args.command, args.timeout)
    command_record["label"] = label
    command_record["env"] = parse_key_values(args.env)
    manifest.setdefault("commands", []).append(command_record)

    log_path = evidence_dir / "logs" / f"{label}.txt"
    log_path.write_text(
        "\n".join(
            [
                f"$ {args.command}",
                "",
                "## stdout",
                command_record.get("stdout", ""),
                "",
                "## stderr",
                command_record.get("stderr", ""),
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifest.setdefault("artifacts", []).append(path_record(log_path) | {"category": "command-log"})
    save_manifest(evidence_dir, manifest)
    print(f"Captured command evidence: {log_path}")


def cmd_add_artifact(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    evidence_dir = case_dir(root, args.case)
    manifest = read_manifest(evidence_dir)
    add_artifacts(manifest, evidence_dir, args.artifact, args.category, copy=not args.no_copy)
    if args.note:
        manifest.setdefault("notes", []).append(args.note)
    save_manifest(evidence_dir, manifest)
    print(f"Added artifacts to {evidence_dir}")


def artifact_categories(manifest: dict[str, Any]) -> set[str]:
    return {str(item.get("category")) for item in manifest.get("artifacts", []) if item.get("category")}


def lint_manifest(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    tool = manifest.get("tool", {})
    if not tool.get("name"):
        errors.append("missing debugger or instrumentation tool name")
    if not tool.get("version") and not tool.get("version_command"):
        errors.append("missing tool version or version command output")
    for key, label in (
        ("target", "target"),
        ("target_version", "target version"),
        ("authorization_scope", "authorization scope"),
        ("test_environment", "test environment"),
    ):
        if not manifest.get(key):
            errors.append(f"missing {label}")
    if not manifest.get("target_file"):
        warnings.append("target file hash is not recorded")
    if not manifest.get("commands"):
        errors.append("missing debugger, replay, or instrumentation command line")
    categories = artifact_categories(manifest)
    if "command-log" not in categories:
        warnings.append("no captured command stdout/stderr log")
    if not categories & {"crash-log", "trace", "screenshot", "recording", "core-dump", "bugreport", "artifact"}:
        warnings.append("no runtime evidence artifact beyond command logs")
    return errors, warnings


def cmd_lint(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    evidence_dir = case_dir(root, args.case)
    manifest = read_manifest(evidence_dir)
    errors, warnings = lint_manifest(manifest)
    status = "ok" if not errors and not (args.strict and warnings) else "invalid"
    print(f"{status}: {evidence_dir}")
    for error in errors:
        print(f"- error: {error}")
    for warning in warnings:
        print(f"- warning: {warning}")
    if errors or (args.strict and warnings):
        raise SystemExit(1)


def cmd_summary(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    evidence_dir = case_dir(root, args.case)
    manifest = read_manifest(evidence_dir)
    errors, warnings = lint_manifest(manifest)
    if args.json:
        print(json.dumps({"case": str(evidence_dir), "manifest": manifest, "errors": errors, "warnings": warnings}, indent=2))
        return
    print(f"# Debug Evidence: {manifest.get('case_id', evidence_dir.name)}")
    print()
    print(f"- Evidence directory: `{evidence_dir}`")
    print(f"- Target: {manifest.get('target')}")
    print(f"- Target version: {manifest.get('target_version')}")
    tool = manifest.get("tool", {})
    print(f"- Tool: {tool.get('name')} {tool.get('version') or ''}".rstrip())
    print(f"- Commands: {len(manifest.get('commands', []))}")
    print(f"- Artifact categories: {', '.join(sorted(artifact_categories(manifest))) or 'none'}")
    print(f"- Lint: {'ok' if not errors else 'invalid'}")
    for error in errors:
        print(f"  - error: {error}")
    for warning in warnings:
        print(f"  - warning: {warning}")


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="Workspace root")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC debugger evidence collector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a debug evidence bundle")
    add_common(init)
    init.add_argument("--case-id")
    init.add_argument("--tool", required=True)
    init.add_argument("--tool-version")
    init.add_argument("--version-command")
    init.add_argument("--target", required=True)
    init.add_argument("--target-version", required=True)
    init.add_argument("--target-file")
    init.add_argument("--scope", required=True)
    init.add_argument("--environment", required=True)
    init.add_argument("--command-line")
    init.add_argument("--env", action="append", metavar="KEY=VALUE")
    init.add_argument("--artifact", action="append")
    init.add_argument("--note")
    init.add_argument("--timeout", type=int, default=20)
    init.add_argument("--no-copy", action="store_true")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    capture = subparsers.add_parser("capture", help="Run a command and persist stdout/stderr evidence")
    add_common(capture)
    capture.add_argument("case")
    capture.add_argument("--command", required=True)
    capture.add_argument("--label")
    capture.add_argument("--env", action="append", metavar="KEY=VALUE")
    capture.add_argument("--timeout", type=int, default=60)
    capture.set_defaults(func=cmd_capture)

    artifact = subparsers.add_parser("add-artifact", help="Attach runtime evidence artifacts")
    add_common(artifact)
    artifact.add_argument("case")
    artifact.add_argument("--artifact", action="append", required=True)
    artifact.add_argument("--category", default="artifact")
    artifact.add_argument("--note")
    artifact.add_argument("--no-copy", action="store_true")
    artifact.set_defaults(func=cmd_add_artifact)

    lint = subparsers.add_parser("lint", help="Check debugger evidence completeness")
    add_common(lint)
    lint.add_argument("case")
    lint.add_argument("--strict", action="store_true")
    lint.set_defaults(func=cmd_lint)

    summary = subparsers.add_parser("summary", help="Print debugger evidence summary")
    add_common(summary)
    summary.add_argument("case")
    summary.add_argument("--json", action="store_true")
    summary.set_defaults(func=cmd_summary)
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
