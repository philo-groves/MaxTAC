#!/usr/bin/env python3
"""Collect and lint ASB IPSW build/hash/tool provenance."""

from __future__ import annotations

import argparse
import json
import secrets
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


MANIFEST = "ipsw-provenance.json"
FACT_SOURCES = (
    "archive-metadata",
    "extracted-file",
    "reconstructed-macho",
    "later-re-tooling",
    "diff-output",
    "runtime-device",
    "other",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def generated_id(prefix: str = "ipsw") -> str:
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
            path = root / "research" / "apple-firmware" / value
        else:
            path = root / path
    return ensure_within(root, path, "IPSW provenance case")


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "ftp"}


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


def source_record(value: str | None, provided_sha256: str | None) -> dict[str, Any]:
    if not value:
        return {"kind": None, "sha256": provided_sha256}
    if is_url(value):
        return {"kind": "url", "url": value, "sha256": provided_sha256}
    path = Path(value).expanduser().resolve()
    record = path_record(path)
    if provided_sha256:
        record["provided_sha256"] = provided_sha256
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


def ipsw_version_capture(entrypoint: str | None) -> dict[str, Any] | None:
    if not entrypoint:
        entrypoint = shutil.which("ipsw") or shutil.which("ipsw.exe")
    if not entrypoint:
        return None
    return run_capture(f"\"{entrypoint}\" version")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_manifest(path: Path) -> dict[str, Any]:
    manifest_path = path / MANIFEST
    if not manifest_path.exists():
        raise SystemExit(f"IPSW provenance manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"{manifest_path} must contain a JSON object")
    return payload


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now()
    write_json(path / MANIFEST, manifest)


def add_artifacts(
    manifest: dict[str, Any],
    provenance_dir: Path,
    values: list[str] | None,
    category: str,
    fact_source: str,
    command: str | None,
    copy: bool,
) -> None:
    for value in values or []:
        path = Path(value).expanduser().resolve()
        record = copy_artifact(path, provenance_dir / "artifacts", category) if copy else path_record(path)
        record["fact_source"] = fact_source
        if command:
            record["command"] = command
        manifest.setdefault("artifacts", []).append(record)


def cmd_init(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    case_id = args.case_id or generated_id()
    provenance_dir = ensure_within(root, root / "research" / "apple-firmware" / case_id, "IPSW provenance case")
    if provenance_dir.exists() and not args.force:
        raise SystemExit(f"IPSW provenance case already exists: {provenance_dir}")
    (provenance_dir / "artifacts").mkdir(parents=True, exist_ok=True)

    version_capture = ipsw_version_capture(args.ipsw)
    manifest: dict[str, Any] = {
        "version": 1,
        "case_id": case_id,
        "created_at": now(),
        "updated_at": now(),
        "firmware": {
            "device_product_type": args.device,
            "model": args.model,
            "board": args.board,
            "product_version": args.product_version,
            "build_number": args.build,
            "source": source_record(args.firmware_source, args.firmware_sha256),
            "selected_restore_identity": args.restore_identity,
            "architecture": args.architecture,
            "artifact_type": args.artifact_type,
        },
        "ipsw": {
            "entrypoint": args.ipsw,
            "version": args.ipsw_version,
            "version_command": version_capture,
        },
        "commands": [],
        "artifacts": [],
        "notes": [args.note] if args.note else [],
    }
    for command in args.command or []:
        manifest["commands"].append({"time": now(), "command": command, "fact_source": args.fact_source})
    add_artifacts(
        manifest,
        provenance_dir,
        args.artifact,
        "artifact",
        args.fact_source,
        None,
        copy=not args.no_copy,
    )
    save_manifest(provenance_dir, manifest)
    print(f"Initialized IPSW provenance case: {provenance_dir}")
    print(f"- manifest: {provenance_dir / MANIFEST}")


def cmd_add_artifact(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    provenance_dir = case_dir(root, args.case)
    manifest = read_manifest(provenance_dir)
    add_artifacts(
        manifest,
        provenance_dir,
        args.artifact,
        args.category,
        args.fact_source,
        args.command,
        copy=not args.no_copy,
    )
    if args.note:
        manifest.setdefault("notes", []).append(args.note)
    save_manifest(provenance_dir, manifest)
    print(f"Added IPSW provenance artifacts to {provenance_dir}")


def cmd_record_command(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    provenance_dir = case_dir(root, args.case)
    manifest = read_manifest(provenance_dir)
    record: dict[str, Any] = {"time": now(), "command": args.command, "fact_source": args.fact_source}
    if args.capture:
        result = run_capture(args.command, args.timeout)
        record["capture"] = result
        logs = provenance_dir / "logs"
        logs.mkdir(exist_ok=True)
        label = args.label or f"command-{len(manifest.get('commands', [])) + 1}"
        log_path = logs / f"{label}.txt"
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
        manifest.setdefault("artifacts", []).append(path_record(log_path) | {"category": "command-log", "fact_source": args.fact_source})
    manifest.setdefault("commands", []).append(record)
    save_manifest(provenance_dir, manifest)
    print(f"Recorded IPSW command for {provenance_dir}")


def filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def artifact_categories(manifest: dict[str, Any]) -> set[str]:
    return {str(item.get("category")) for item in manifest.get("artifacts", []) if item.get("category")}


def fact_sources(manifest: dict[str, Any]) -> set[str]:
    sources = {str(item.get("fact_source")) for item in manifest.get("artifacts", []) if item.get("fact_source")}
    sources.update(str(item.get("fact_source")) for item in manifest.get("commands", []) if item.get("fact_source"))
    return sources


def lint_manifest(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    firmware = manifest.get("firmware") or {}
    for key, label in (
        ("device_product_type", "device product type"),
        ("product_version", "product version"),
        ("build_number", "build number"),
        ("selected_restore_identity", "selected restore identity"),
        ("architecture", "architecture"),
    ):
        if not filled(firmware.get(key)):
            errors.append(f"missing {label}")
    if not filled(firmware.get("model")) and not filled(firmware.get("board")):
        warnings.append("neither model nor board is recorded")
    source = firmware.get("source") or {}
    if not filled(source.get("path")) and not filled(source.get("url")):
        errors.append("missing firmware URL or local source path")
    if not filled(source.get("sha256")) and not filled(source.get("provided_sha256")):
        errors.append("missing original firmware source hash")

    ipsw = manifest.get("ipsw") or {}
    version_capture = ipsw.get("version_command") or {}
    if not filled(ipsw.get("version")) and not filled(version_capture.get("stdout")):
        errors.append("missing ipsw version")

    if not manifest.get("commands"):
        errors.append("missing ipsw or downstream tool command line")
    if not fact_sources(manifest):
        errors.append("missing fact source classification")
    if "archive-metadata" not in fact_sources(manifest):
        warnings.append("archive metadata provenance is not recorded")
    if not manifest.get("artifacts"):
        warnings.append("no extracted, metadata, diff, or RE artifacts are attached")
    if "command-log" not in artifact_categories(manifest):
        warnings.append("no captured command output log")
    return errors, warnings


def cmd_lint(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    provenance_dir = case_dir(root, args.case)
    manifest = read_manifest(provenance_dir)
    errors, warnings = lint_manifest(manifest)
    status = "ok" if not errors and not (args.strict and warnings) else "invalid"
    print(f"{status}: {provenance_dir}")
    for error in errors:
        print(f"- error: {error}")
    for warning in warnings:
        print(f"- warning: {warning}")
    if errors or (args.strict and warnings):
        raise SystemExit(1)


def cmd_summary(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    provenance_dir = case_dir(root, args.case)
    manifest = read_manifest(provenance_dir)
    errors, warnings = lint_manifest(manifest)
    if args.json:
        print(json.dumps({"case": str(provenance_dir), "manifest": manifest, "errors": errors, "warnings": warnings}, indent=2))
        return
    firmware = manifest.get("firmware") or {}
    print(f"# ASB IPSW Provenance: {manifest.get('case_id', provenance_dir.name)}")
    print()
    print(f"- Case directory: `{provenance_dir}`")
    print(f"- Device: {firmware.get('device_product_type')}")
    print(f"- Version/build: {firmware.get('product_version')} / {firmware.get('build_number')}")
    print(f"- Restore identity: {firmware.get('selected_restore_identity')}")
    print(f"- Architecture: {firmware.get('architecture')}")
    print(f"- Fact sources: {', '.join(sorted(fact_sources(manifest))) or 'none'}")
    print(f"- Artifact categories: {', '.join(sorted(artifact_categories(manifest))) or 'none'}")
    print(f"- Lint: {'ok' if not errors else 'invalid'}")
    for error in errors:
        print(f"  - error: {error}")
    for warning in warnings:
        print(f"  - warning: {warning}")


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="Workspace root")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC ASB IPSW provenance collector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create an IPSW provenance bundle")
    add_common(init)
    init.add_argument("--case-id")
    init.add_argument("--device", required=True, help="Product type, such as iPhone16,1")
    init.add_argument("--model")
    init.add_argument("--board")
    init.add_argument("--product-version", required=True)
    init.add_argument("--build", required=True)
    init.add_argument("--firmware-source", required=True, help="Firmware URL or local source path")
    init.add_argument("--firmware-sha256")
    init.add_argument("--restore-identity", required=True)
    init.add_argument("--architecture", required=True)
    init.add_argument("--artifact-type", default="IPSW/OTA")
    init.add_argument("--ipsw")
    init.add_argument("--ipsw-version")
    init.add_argument("--command", action="append")
    init.add_argument("--fact-source", choices=FACT_SOURCES, default="archive-metadata")
    init.add_argument("--artifact", action="append")
    init.add_argument("--note")
    init.add_argument("--no-copy", action="store_true")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    artifact = subparsers.add_parser("add-artifact", help="Attach build-specific IPSW evidence artifacts")
    add_common(artifact)
    artifact.add_argument("case")
    artifact.add_argument("--artifact", action="append", required=True)
    artifact.add_argument("--category", required=True)
    artifact.add_argument("--fact-source", choices=FACT_SOURCES, required=True)
    artifact.add_argument("--command")
    artifact.add_argument("--note")
    artifact.add_argument("--no-copy", action="store_true")
    artifact.set_defaults(func=cmd_add_artifact)

    command = subparsers.add_parser("record-command", help="Record or capture an ipsw/downstream RE command")
    add_common(command)
    command.add_argument("case")
    command.add_argument("--command", required=True)
    command.add_argument("--fact-source", choices=FACT_SOURCES, required=True)
    command.add_argument("--capture", action="store_true")
    command.add_argument("--label")
    command.add_argument("--timeout", type=int, default=120)
    command.set_defaults(func=cmd_record_command)

    lint = subparsers.add_parser("lint", help="Check IPSW provenance completeness")
    add_common(lint)
    lint.add_argument("case")
    lint.add_argument("--strict", action="store_true")
    lint.set_defaults(func=cmd_lint)

    summary = subparsers.add_parser("summary", help="Print IPSW provenance summary")
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
