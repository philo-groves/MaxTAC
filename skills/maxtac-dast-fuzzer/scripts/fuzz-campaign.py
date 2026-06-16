#!/usr/bin/env python3
"""Collect and lint MaxTAC fuzzing campaign evidence."""

from __future__ import annotations

import argparse
import json
import re
import secrets
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MANIFEST = "campaign.json"
ARTIFACT_DIR = "artifacts"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def generated_id(prefix: str = "fuzz") -> str:
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


def campaign_dir(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        if len(path.parts) == 1:
            path = root / "fuzz" / path
        else:
            path = root / path
    return ensure_within(root, path, "campaign")


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
        files = [item for item in path.rglob("*") if item.is_file()]
        record.update({"kind": "directory", "files": len(files)})
    else:
        record["kind"] = "other"
    return record


def copy_artifact(path: Path, dest_dir: Path, category: str) -> dict[str, Any]:
    record = path_record(path)
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
    copied["source"] = record
    copied["category"] = category
    return copied


def parse_key_values(values: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise SystemExit(f"Expected KEY=VALUE: {value}")
        key, item = value.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"Empty key in: {value}")
        result[key] = item
    return result


def run_capture(command: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            shell=True,
            check=False,
            text=True,
            capture_output=True,
            timeout=20,
        )
    except OSError as exc:
        return {"command": command, "error": str(exc)}
    except subprocess.TimeoutExpired:
        return {"command": command, "error": "timed out"}
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_manifest(path: Path) -> dict[str, Any]:
    manifest_path = path / MANIFEST
    if not manifest_path.exists():
        raise SystemExit(f"Campaign manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"{manifest_path} must contain a JSON object")
    return payload


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now()
    write_json(path / MANIFEST, manifest)


def add_paths(
    manifest: dict[str, Any],
    campaign: Path,
    key: str,
    paths: list[str] | None,
    category: str,
    *,
    copy: bool,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for value in paths or []:
        path = Path(value).expanduser().resolve()
        record = copy_artifact(path, campaign / ARTIFACT_DIR, category) if copy else path_record(path)
        records.append(record)
    if records:
        manifest.setdefault(key, []).extend(records)
    return records


def command_record(command: str, env: dict[str, str] | None = None, **extra: Any) -> dict[str, Any]:
    record = {"time": now(), "command": command}
    if env:
        record["env"] = env
    for key, value in extra.items():
        if value is not None:
            record[key] = value
    return record


def cmd_init(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    campaign_id = args.campaign_id or generated_id()
    campaign = ensure_within(root, root / "fuzz" / campaign_id, "campaign")
    if campaign.exists() and not args.force:
        raise SystemExit(f"Campaign already exists: {campaign}")
    (campaign / ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)

    target_file = Path(args.target_file).expanduser().resolve() if args.target_file else None
    tool_version = args.tool_version
    version_capture = run_capture(args.version_command) if args.version_command else None
    if not tool_version and version_capture and version_capture.get("stdout"):
        tool_version = str(version_capture["stdout"]).splitlines()[0]

    manifest: dict[str, Any] = {
        "version": 1,
        "campaign_id": campaign_id,
        "created_at": now(),
        "updated_at": now(),
        "target": args.target,
        "target_version": args.target_version,
        "authorization_scope": args.scope,
        "rate_limits": args.rate_limits,
        "test_environment": args.environment,
        "tool": {
            "name": args.tool,
            "version": tool_version,
            "version_command": version_capture,
        },
        "instrumentation_mode": args.instrumentation,
        "commands": [],
        "build_flags": args.build_flag or [],
        "sanitizer_flags": args.sanitizer_flag or [],
        "runs": [],
        "notes": [args.note] if args.note else [],
    }
    if target_file:
        manifest["target_file"] = path_record(target_file)
    for command in args.command or []:
        manifest["commands"].append(command_record(command, parse_key_values(args.env)))

    copy = not args.no_copy
    add_paths(manifest, campaign, "harnesses", args.harness, "harness", copy=copy)
    add_paths(manifest, campaign, "grammars", args.grammar, "grammar", copy=copy)
    add_paths(manifest, campaign, "schemas", args.schema, "schema", copy=copy)
    add_paths(manifest, campaign, "models", args.model, "model", copy=copy)
    add_paths(manifest, campaign, "request_templates", args.request_template, "request-template", copy=copy)
    add_paths(manifest, campaign, "ui_scripts", args.ui_script, "ui-script", copy=copy)
    add_paths(manifest, campaign, "seed_corpora", args.seed_corpus, "seed-corpus", copy=copy)
    add_paths(manifest, campaign, "dictionaries", args.dictionary, "dictionary", copy=copy)
    add_paths(manifest, campaign, "artifacts", args.artifact, "artifact", copy=copy)

    save_manifest(campaign, manifest)
    print(f"Initialized fuzz campaign: {campaign}")
    print(f"- manifest: {campaign / MANIFEST}")


def cmd_add_run(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    campaign = campaign_dir(root, args.campaign)
    manifest = read_manifest(campaign)
    run: dict[str, Any] = {
        "time": now(),
        "kind": args.kind,
        "note": args.note,
        "command": command_record(args.command, parse_key_values(args.env), exit_code=args.exit_code)
        if args.command
        else None,
        "replay_command": args.replay_command,
        "api": {
            "auth_context": args.auth_context,
            "resource_ids": args.resource_id or [],
            "cleanup_actions": args.cleanup_action or [],
        },
        "logic": {
            "invariant": args.invariant,
            "expected_behavior": args.expected,
            "observed_behavior": args.observed,
            "replay_stability": args.replay_stability,
        },
        "artifacts": [],
    }
    run = {key: value for key, value in run.items() if value not in (None, [], {})}

    copy = not args.no_copy
    artifact_specs = [
        ("log", args.log),
        ("artifact", args.artifact),
        ("crash-input", args.crash_input),
        ("minimized-reproducer", args.minimized_reproducer),
        ("debugger-output", args.debugger_output),
        ("sanitizer-report", args.sanitizer_report),
        ("stack-trace", args.stack_trace),
        ("core-dump", args.core_dump),
        ("screenshot", args.screenshot),
        ("api-request-sequence", args.api_request_sequence),
    ]
    for category, values in artifact_specs:
        for value in values or []:
            path = Path(value).expanduser().resolve()
            record = copy_artifact(path, campaign / ARTIFACT_DIR, category) if copy else path_record(path)
            run.setdefault("artifacts", []).append(record)

    manifest.setdefault("runs", []).append(run)
    save_manifest(campaign, manifest)
    print(f"Added fuzz run to {campaign}")


def latest_kinds(manifest: dict[str, Any]) -> set[str]:
    kinds = set()
    for run in manifest.get("runs", []):
        kind = run.get("kind")
        if kind:
            kinds.add(str(kind))
    return kinds


def has_any(manifest: dict[str, Any], keys: list[str]) -> bool:
    for key in keys:
        if manifest.get(key):
            return True
    return False


def artifact_categories(manifest: dict[str, Any]) -> set[str]:
    categories: set[str] = set()
    for key in ("artifacts", "harnesses", "grammars", "schemas", "models", "request_templates", "ui_scripts", "seed_corpora", "dictionaries"):
        for artifact in manifest.get(key, []):
            if artifact.get("category"):
                categories.add(str(artifact["category"]))
            else:
                categories.add(key)
    for run in manifest.get("runs", []):
        for artifact in run.get("artifacts", []):
            category = artifact.get("category")
            if category:
                categories.add(str(category))
    return categories


def lint_manifest(manifest: dict[str, Any], kind: str | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    required = {
        "authorization_scope": "authorization scope",
        "test_environment": "test environment",
        "target": "target",
        "target_version": "target version",
        "rate_limits": "rate limits",
        "instrumentation_mode": "instrumentation mode",
    }
    for key, label in required.items():
        if not manifest.get(key):
            errors.append(f"missing {label}")

    tool = manifest.get("tool", {})
    if not tool.get("name"):
        errors.append("missing tool name")
    if not tool.get("version") and not tool.get("version_command"):
        errors.append("missing tool version or version command output")
    if not manifest.get("commands"):
        errors.append("missing campaign command line")
    if not manifest.get("target_file"):
        warnings.append("target file hash is not recorded")
    if not manifest.get("build_flags"):
        warnings.append("build flags are not recorded")
    if not manifest.get("sanitizer_flags"):
        warnings.append("sanitizer flags are not recorded")
    if not has_any(manifest, ["harnesses", "grammars", "schemas", "models", "request_templates", "ui_scripts"]):
        errors.append("missing harness, grammar, schema, model, request template, or UI script")
    if not has_any(manifest, ["seed_corpora", "dictionaries"]):
        warnings.append("seed corpus or dictionary is not recorded")

    categories = artifact_categories(manifest)
    kinds = latest_kinds(manifest)
    target_kinds = {kind} if kind else kinds
    if "crash" in target_kinds:
        for category in ("crash-input", "minimized-reproducer"):
            if category not in categories:
                errors.append(f"missing {category} artifact")
        if "debugger-output" not in categories and "sanitizer-report" not in categories and "stack-trace" not in categories:
            errors.append("missing debugger output, sanitizer report, or stack trace")
        if not any(run.get("replay_command") for run in manifest.get("runs", [])):
            errors.append("missing replay command for crash")
    if "api" in target_kinds:
        if "api-request-sequence" not in categories:
            errors.append("missing API request sequence artifact")
        if not any((run.get("api") or {}).get("auth_context") for run in manifest.get("runs", [])):
            errors.append("missing API auth context")
        if not any((run.get("api") or {}).get("cleanup_actions") for run in manifest.get("runs", [])):
            warnings.append("API cleanup actions are not recorded")
    if "logic" in target_kinds:
        logic_runs = [run.get("logic") or {} for run in manifest.get("runs", [])]
        for key, label in (
            ("invariant", "logic invariant"),
            ("expected_behavior", "expected behavior"),
            ("observed_behavior", "observed behavior"),
            ("replay_stability", "replay stability"),
        ):
            if not any(item.get(key) for item in logic_runs):
                errors.append(f"missing {label}")

    return errors, warnings


def cmd_lint(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    campaign = campaign_dir(root, args.campaign)
    manifest = read_manifest(campaign)
    errors, warnings = lint_manifest(manifest, args.kind)
    status = "ok" if not errors and not (args.strict and warnings) else "invalid"
    print(f"{status}: {campaign}")
    for error in errors:
        print(f"- error: {error}")
    for warning in warnings:
        print(f"- warning: {warning}")
    if errors or (args.strict and warnings):
        raise SystemExit(1)


def cmd_summary(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    campaign = campaign_dir(root, args.campaign)
    manifest = read_manifest(campaign)
    errors, warnings = lint_manifest(manifest, args.kind)
    if args.json:
        payload = {"campaign": str(campaign), "manifest": manifest, "errors": errors, "warnings": warnings}
        print(json.dumps(payload, indent=2))
        return

    print(f"# Fuzz Campaign Evidence: {manifest.get('campaign_id', campaign.name)}")
    print()
    print(f"- Campaign directory: `{campaign}`")
    print(f"- Target: {manifest.get('target')}")
    print(f"- Target version: {manifest.get('target_version')}")
    tool = manifest.get("tool", {})
    print(f"- Tool: {tool.get('name')} {tool.get('version') or ''}".rstrip())
    print(f"- Commands: {len(manifest.get('commands', []))}")
    print(f"- Runs: {len(manifest.get('runs', []))}")
    print(f"- Artifacts categories: {', '.join(sorted(artifact_categories(manifest))) or 'none'}")
    print(f"- Lint: {'ok' if not errors else 'invalid'}")
    for error in errors:
        print(f"  - error: {error}")
    for warning in warnings:
        print(f"  - warning: {warning}")


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="Workspace root")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC fuzz campaign evidence collector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a fuzz campaign evidence bundle")
    add_common(init)
    init.add_argument("--campaign-id")
    init.add_argument("--target", required=True)
    init.add_argument("--target-version", required=True)
    init.add_argument("--target-file")
    init.add_argument("--tool", required=True)
    init.add_argument("--tool-version")
    init.add_argument("--version-command")
    init.add_argument("--scope", required=True)
    init.add_argument("--environment", required=True)
    init.add_argument("--rate-limits", required=True)
    init.add_argument("--instrumentation", required=True)
    init.add_argument("--command", action="append")
    init.add_argument("--env", action="append", metavar="KEY=VALUE")
    init.add_argument("--build-flag", action="append")
    init.add_argument("--sanitizer-flag", action="append")
    init.add_argument("--harness", action="append")
    init.add_argument("--grammar", action="append")
    init.add_argument("--schema", action="append")
    init.add_argument("--model", action="append")
    init.add_argument("--request-template", action="append")
    init.add_argument("--ui-script", action="append")
    init.add_argument("--seed-corpus", action="append")
    init.add_argument("--dictionary", action="append")
    init.add_argument("--artifact", action="append")
    init.add_argument("--note")
    init.add_argument("--no-copy", action="store_true")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    add = subparsers.add_parser("add-run", help="Attach one fuzz run or reproduction result")
    add_common(add)
    add.add_argument("campaign")
    add.add_argument("--kind", choices=("campaign", "crash", "api", "logic"), default="campaign")
    add.add_argument("--command")
    add.add_argument("--env", action="append", metavar="KEY=VALUE")
    add.add_argument("--exit-code", type=int)
    add.add_argument("--replay-command")
    add.add_argument("--log", action="append")
    add.add_argument("--artifact", action="append")
    add.add_argument("--crash-input", action="append")
    add.add_argument("--minimized-reproducer", action="append")
    add.add_argument("--debugger-output", action="append")
    add.add_argument("--sanitizer-report", action="append")
    add.add_argument("--stack-trace", action="append")
    add.add_argument("--core-dump", action="append")
    add.add_argument("--screenshot", action="append")
    add.add_argument("--api-request-sequence", action="append")
    add.add_argument("--auth-context")
    add.add_argument("--resource-id", action="append")
    add.add_argument("--cleanup-action", action="append")
    add.add_argument("--invariant")
    add.add_argument("--expected")
    add.add_argument("--observed")
    add.add_argument("--replay-stability")
    add.add_argument("--note")
    add.add_argument("--no-copy", action="store_true")
    add.set_defaults(func=cmd_add_run)

    lint = subparsers.add_parser("lint", help="Check campaign evidence completeness")
    add_common(lint)
    lint.add_argument("campaign")
    lint.add_argument("--kind", choices=("campaign", "crash", "api", "logic"))
    lint.add_argument("--strict", action="store_true")
    lint.set_defaults(func=cmd_lint)

    summary = subparsers.add_parser("summary", help="Print campaign evidence summary")
    add_common(summary)
    summary.add_argument("campaign")
    summary.add_argument("--kind", choices=("campaign", "crash", "api", "logic"))
    summary.add_argument("--json", action="store_true")
    summary.set_defaults(func=cmd_summary)
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
