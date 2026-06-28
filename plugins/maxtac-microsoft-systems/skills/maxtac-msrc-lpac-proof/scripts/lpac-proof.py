#!/usr/bin/env python3
"""Collect and lint MSRC LPAC proof evidence."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MANIFEST = "lpac-proof.json"
ELIGIBLE_SANDBOXES = {
    "edge-renderer",
    "msmpengcp",
    "wpad",
    "utcdecoderhost",
}
ALL_SANDBOXES = (*sorted(ELIGIBLE_SANDBOXES), "generic-lpac", "generic-appcontainer", "other")
ATTACK_SCENARIOS = ("sandbox-escape", "private-data-access")
TOOL_CHOICES = ("LaunchAppContainer", "EdgeSandboxTestTool", "real-product-sandbox", "other")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def generated_id(prefix: str = "lpac") -> str:
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
    return ensure_within(root, path, "LPAC proof case")


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


def run_capture(command: str, timeout: int = 20) -> dict[str, Any]:
    record: dict[str, Any] = {"time": now(), "command": command}
    try:
        completed = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except OSError as exc:
        record["error"] = str(exc)
        return record
    except subprocess.TimeoutExpired as exc:
        record["error"] = "timed out"
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


def capture_windows_build() -> dict[str, Any]:
    command = (
        "powershell -NoProfile -Command "
        "\"Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion' | "
        "Select-Object CurrentBuild,UBR,BuildLabEx | ConvertTo-Json -Compress\""
    )
    return run_capture(command)


def git_commit(repo: str | None) -> dict[str, Any] | None:
    if not repo:
        return None
    repo_path = Path(repo).expanduser().resolve()
    if not repo_path.exists():
        return {"repo": str(repo_path), "error": "repo not found"}
    result = run_capture(f"git -C \"{repo_path}\" rev-parse HEAD")
    result["repo"] = str(repo_path)
    return result


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_manifest(path: Path) -> dict[str, Any]:
    manifest_path = path / MANIFEST
    if not manifest_path.exists():
        raise SystemExit(f"LPAC proof manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"{manifest_path} must contain a JSON object")
    return payload


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now()
    write_json(path / MANIFEST, manifest)


def add_artifacts(manifest: dict[str, Any], proof_dir: Path, values: list[str] | None, category: str, copy: bool) -> None:
    for value in values or []:
        path = Path(value).expanduser().resolve()
        record = copy_artifact(path, proof_dir / "artifacts", category) if copy else path_record(path)
        manifest.setdefault("artifacts", []).append(record)


def cmd_init(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    case_id = args.case_id or generated_id()
    proof_dir = ensure_within(root, root / "proof" / case_id, "LPAC proof case")
    if proof_dir.exists() and not args.force:
        raise SystemExit(f"LPAC proof case already exists: {proof_dir}")
    (proof_dir / "artifacts").mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "version": 1,
        "case_id": case_id,
        "created_at": now(),
        "updated_at": now(),
        "attack_scenario": args.attack_scenario,
        "eligible_sandbox": args.eligible_sandbox,
        "sandbox_notes": args.sandbox_notes,
        "canary_build": args.canary_build,
        "build_lab_ex": args.build_lab_ex,
        "date_tested": args.date_tested or datetime.now(timezone.utc).date().isoformat(),
        "sandbox_security_tools": {
            "repo": str(Path(args.sandbox_tools_repo).expanduser().resolve()) if args.sandbox_tools_repo else None,
            "commit": args.sandbox_tools_commit,
            "git_capture": git_commit(args.sandbox_tools_repo) if args.sandbox_tools_repo else None,
            "tool_used": args.tool_used,
        },
        "launch_command": args.launch_command,
        "debugger": {
            "used": args.debugger_used,
            "dependency": args.debugger_dependency,
            "optional_steps": args.optional_debugger_steps,
        },
        "pov": {
            "build_instructions": args.build_instructions,
        },
        "proof": {
            "baseline_denied_operation": args.baseline_denied_operation,
            "exploit_success_operation": args.exploit_success_operation,
            "finishing_privilege_or_data": args.finishing_privilege_or_data,
            "shipped_windows_component": args.shipped_component,
            "vulnerability_path": args.vulnerability_path,
        },
        "environment": {
            "windows_build_capture": capture_windows_build() if args.capture_windows_build else None,
            "host": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME"),
        },
        "commands": [],
        "artifacts": [],
        "notes": [args.note] if args.note else [],
    }
    if args.pov_source:
        add_artifacts(manifest, proof_dir, args.pov_source, "pov-source", copy=not args.no_copy)
    if args.pov_binary:
        add_artifacts(manifest, proof_dir, args.pov_binary, "pov-binary", copy=not args.no_copy)
    if args.artifact:
        add_artifacts(manifest, proof_dir, args.artifact, "artifact", copy=not args.no_copy)
    if args.launch_command:
        manifest["commands"].append({"time": now(), "label": "launch-command", "command": args.launch_command})
    save_manifest(proof_dir, manifest)
    print(f"Initialized LPAC proof case: {proof_dir}")
    print(f"- manifest: {proof_dir / MANIFEST}")


def cmd_add_artifact(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    proof_dir = case_dir(root, args.case)
    manifest = read_manifest(proof_dir)
    add_artifacts(manifest, proof_dir, args.artifact, args.category, copy=not args.no_copy)
    if args.note:
        manifest.setdefault("notes", []).append(args.note)
    save_manifest(proof_dir, manifest)
    print(f"Added LPAC artifacts to {proof_dir}")


def cmd_capture(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    proof_dir = case_dir(root, args.case)
    manifest = read_manifest(proof_dir)
    result = run_capture(args.command, args.timeout)
    result["label"] = args.label or f"command-{len(manifest.get('commands', [])) + 1}"
    manifest.setdefault("commands", []).append(result)
    logs = proof_dir / "logs"
    logs.mkdir(exist_ok=True)
    log_path = logs / f"{result['label']}.txt"
    log_path.write_text(
        "\n".join(
            [
                f"$ {args.command}",
                "",
                "## stdout",
                result.get("stdout", ""),
                "",
                "## stderr",
                result.get("stderr", ""),
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifest.setdefault("artifacts", []).append(path_record(log_path) | {"category": "command-log"})
    save_manifest(proof_dir, manifest)
    print(f"Captured command evidence: {log_path}")


def artifact_categories(manifest: dict[str, Any]) -> set[str]:
    return {str(item.get("category")) for item in manifest.get("artifacts", []) if item.get("category")}


def filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def lint_manifest(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for key, label in (
        ("attack_scenario", "attack scenario"),
        ("eligible_sandbox", "eligible sandbox"),
        ("date_tested", "date tested"),
        ("launch_command", "exact launch command line"),
    ):
        if not filled(manifest.get(key)):
            errors.append(f"missing {label}")

    sandbox = manifest.get("eligible_sandbox")
    if sandbox not in ELIGIBLE_SANDBOXES:
        warnings.append("sandbox is not one of the listed local Attack Scenario eligible sandboxes")

    if not filled(manifest.get("canary_build")):
        errors.append("missing Canary build")
    if not filled(manifest.get("build_lab_ex")):
        capture = (manifest.get("environment") or {}).get("windows_build_capture") or {}
        if not capture.get("stdout"):
            errors.append("missing BuildLabEx or Windows build capture")

    tools = manifest.get("sandbox_security_tools") or {}
    if not filled(tools.get("commit")):
        git_capture = tools.get("git_capture") or {}
        if not git_capture.get("stdout"):
            errors.append("missing SandboxSecurityTools commit hash")
    if not filled(tools.get("tool_used")):
        errors.append("missing SandboxSecurityTools tool used")

    pov = manifest.get("pov") or {}
    proof = manifest.get("proof") or {}
    for key, label in (
        ("build_instructions", "PoV build instructions"),
    ):
        if not filled(pov.get(key)):
            errors.append(f"missing {label}")
    for key, label in (
        ("baseline_denied_operation", "baseline denied operation"),
        ("exploit_success_operation", "exploit success operation"),
        ("finishing_privilege_or_data", "finishing privilege or data accessed"),
        ("shipped_windows_component", "shipped Windows component"),
        ("vulnerability_path", "vulnerability path explanation"),
    ):
        if not filled(proof.get(key)):
            errors.append(f"missing {label}")

    debugger = manifest.get("debugger") or {}
    if debugger.get("used") is None:
        errors.append("missing debugger-used statement")
    if not filled(debugger.get("dependency")):
        errors.append("missing statement about debugger dependency")
    elif debugger.get("dependency") == "required":
        errors.append("proof is marked as requiring debugger actions")

    categories = artifact_categories(manifest)
    for category, label in (
        ("pov-source", "PoV source"),
        ("pov-binary", "PoV binary"),
        ("token-dump", "token/capability dump"),
        ("baseline-denied", "baseline denied evidence"),
        ("exploit-success", "exploit success evidence"),
        ("finishing-proof", "finishing privilege/data proof"),
    ):
        if category not in categories:
            errors.append(f"missing {label} artifact")

    if "command-log" not in categories:
        warnings.append("no captured command stdout/stderr log")
    if "debugger-steps" not in categories and debugger.get("used"):
        warnings.append("debugger was used but optional debugger steps artifact is missing")
    return errors, warnings


def cmd_lint(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    proof_dir = case_dir(root, args.case)
    manifest = read_manifest(proof_dir)
    errors, warnings = lint_manifest(manifest)
    status = "ok" if not errors and not (args.strict and warnings) else "invalid"
    print(f"{status}: {proof_dir}")
    for error in errors:
        print(f"- error: {error}")
    for warning in warnings:
        print(f"- warning: {warning}")
    if errors or (args.strict and warnings):
        raise SystemExit(1)


def cmd_summary(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    proof_dir = case_dir(root, args.case)
    manifest = read_manifest(proof_dir)
    errors, warnings = lint_manifest(manifest)
    if args.json:
        print(json.dumps({"case": str(proof_dir), "manifest": manifest, "errors": errors, "warnings": warnings}, indent=2))
        return
    print(f"# MSRC LPAC Proof Evidence: {manifest.get('case_id', proof_dir.name)}")
    print()
    print(f"- Case directory: `{proof_dir}`")
    print(f"- Attack scenario: {manifest.get('attack_scenario')}")
    print(f"- Sandbox: {manifest.get('eligible_sandbox')}")
    print(f"- Canary build: {manifest.get('canary_build')}")
    print(f"- BuildLabEx: {manifest.get('build_lab_ex')}")
    print(f"- Tool: {(manifest.get('sandbox_security_tools') or {}).get('tool_used')}")
    print(f"- Artifact categories: {', '.join(sorted(artifact_categories(manifest))) or 'none'}")
    print(f"- Lint: {'ok' if not errors else 'invalid'}")
    for error in errors:
        print(f"  - error: {error}")
    for warning in warnings:
        print(f"  - warning: {warning}")


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="Workspace root")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC MSRC LPAC proof evidence collector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create an LPAC proof evidence bundle")
    add_common(init)
    init.add_argument("--case-id")
    init.add_argument("--attack-scenario", choices=ATTACK_SCENARIOS, required=True)
    init.add_argument("--eligible-sandbox", choices=ALL_SANDBOXES, required=True)
    init.add_argument("--sandbox-notes")
    init.add_argument("--canary-build", required=True)
    init.add_argument("--build-lab-ex")
    init.add_argument("--capture-windows-build", action="store_true")
    init.add_argument("--date-tested")
    init.add_argument("--sandbox-tools-repo")
    init.add_argument("--sandbox-tools-commit")
    init.add_argument("--tool-used", choices=TOOL_CHOICES, required=True)
    init.add_argument("--launch-command", required=True)
    init.add_argument("--debugger-used", action=argparse.BooleanOptionalAction, default=None)
    init.add_argument("--debugger-dependency", choices=("none", "optional", "required"), required=True)
    init.add_argument("--optional-debugger-steps")
    init.add_argument("--pov-source", action="append")
    init.add_argument("--pov-binary", action="append")
    init.add_argument("--build-instructions", required=True)
    init.add_argument("--baseline-denied-operation", required=True)
    init.add_argument("--exploit-success-operation", required=True)
    init.add_argument("--finishing-privilege-or-data", required=True)
    init.add_argument("--shipped-component", required=True)
    init.add_argument("--vulnerability-path", required=True)
    init.add_argument("--artifact", action="append")
    init.add_argument("--note")
    init.add_argument("--no-copy", action="store_true")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    capture = subparsers.add_parser("capture", help="Run a command and persist stdout/stderr evidence")
    add_common(capture)
    capture.add_argument("case")
    capture.add_argument("--command", required=True)
    capture.add_argument("--label")
    capture.add_argument("--timeout", type=int, default=60)
    capture.set_defaults(func=cmd_capture)

    artifact = subparsers.add_parser("add-artifact", help="Attach LPAC proof artifacts")
    add_common(artifact)
    artifact.add_argument("case")
    artifact.add_argument("--category", required=True)
    artifact.add_argument("--artifact", action="append", required=True)
    artifact.add_argument("--note")
    artifact.add_argument("--no-copy", action="store_true")
    artifact.set_defaults(func=cmd_add_artifact)

    lint = subparsers.add_parser("lint", help="Check LPAC report-packet evidence completeness")
    add_common(lint)
    lint.add_argument("case")
    lint.add_argument("--strict", action="store_true")
    lint.set_defaults(func=cmd_lint)

    summary = subparsers.add_parser("summary", help="Print LPAC proof evidence summary")
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
