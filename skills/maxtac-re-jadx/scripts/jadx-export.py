#!/usr/bin/env python3
"""Plan or run a repeatable JADX export with evidence metadata."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise SystemExit(f"Input file not found: {path}")
    return {"path": str(path.resolve()), "size": path.stat().st_size, "sha256": sha256_file(path)}


def resolve_jadx(value: str | None) -> str | None:
    if value:
        return str(Path(value).expanduser())
    return shutil.which("jadx") or shutil.which("jadx.bat")


def run_command(command: list[str], timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False, timeout=timeout)
    except OSError as exc:
        return {"command": subprocess.list2cmdline(command), "error": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": subprocess.list2cmdline(command),
            "error": "timed out",
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
        }
    return {
        "command": subprocess.list2cmdline(command),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def build_command(args: argparse.Namespace, jadx: str) -> list[str]:
    command = [jadx, "-d", str(Path(args.output_dir).expanduser().resolve())]
    if args.mode == "sources":
        command.append("--no-res")
    elif args.mode == "resources":
        command.append("--no-src")
    if args.export_gradle_type:
        command.extend(["--export-gradle-type", args.export_gradle_type])
    elif args.export_gradle:
        command.extend(["--export-gradle-type", "auto"])
    if args.deobf:
        command.append("--deobf")
    if args.show_bad_code:
        command.append("--show-bad-code")
    if args.cfg:
        command.append("--cfg")
    for value in args.plugin_option or []:
        command.append(f"-P{value}")
    for value in args.extra_arg or []:
        command.append(value)
    command.append(str(Path(args.input).expanduser().resolve()))
    return command


def output_records(output_dir: Path, limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not output_dir.exists():
        return records
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name in {"jadx-export.json", "command.txt", "run.log"}:
            continue
        records.append(file_record(path))
        if len(records) >= limit:
            break
    return records


def cmd_main(args: argparse.Namespace) -> None:
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    jadx = resolve_jadx(args.jadx)
    if not jadx:
        raise SystemExit("Could not find jadx. Pass --jadx.")

    command = build_command(args, jadx)
    version = run_command([jadx, "--version"], 20)
    manifest: dict[str, Any] = {
        "version": 1,
        "time": now(),
        "input": file_record(input_path),
        "output_dir": str(output_dir),
        "tool": {
            "path": jadx,
            "version_command": version,
        },
        "settings": {
            "mode": args.mode,
            "deobf": args.deobf,
            "show_bad_code": args.show_bad_code,
            "cfg": args.cfg,
            "export_gradle": args.export_gradle,
            "export_gradle_type": args.export_gradle_type,
            "plugin_options": args.plugin_option or [],
            "extra_args": args.extra_arg or [],
        },
        "command": subprocess.list2cmdline(command),
        "ran": False,
    }
    (output_dir / "command.txt").write_text(manifest["command"] + "\n", encoding="utf-8")
    if args.run:
        result = run_command(command, args.timeout)
        manifest["ran"] = True
        manifest["result"] = {key: value for key, value in result.items() if key not in {"stdout", "stderr"}}
        (output_dir / "run.log").write_text(
            "\n".join(
                [
                    f"$ {manifest['command']}",
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
        manifest["outputs_sample"] = output_records(output_dir, args.hash_limit)
        manifest["outputs_sample_limit"] = args.hash_limit

    manifest_path = output_dir / "jadx-export.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(manifest, indent=2))
    else:
        print(f"JADX export {'ran' if args.run else 'planned'}: {output_dir}")
        print(f"- manifest: {manifest_path}")
        print(f"- command: {output_dir / 'command.txt'}")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC JADX export planner/runner")
    parser.add_argument("input")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--jadx")
    parser.add_argument("--mode", choices=("all", "sources", "resources"), default="all")
    parser.add_argument("--deobf", action="store_true")
    parser.add_argument("--show-bad-code", action="store_true")
    parser.add_argument("--cfg", action="store_true")
    parser.add_argument("--export-gradle", action="store_true", help="Shortcut for --export-gradle-type auto")
    parser.add_argument("--export-gradle-type", choices=("auto", "android-app", "android-library", "simple-java"))
    parser.add_argument("--plugin-option", action="append")
    parser.add_argument("--extra-arg", action="append")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--hash-limit", type=int, default=500)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    cmd_main(args)


if __name__ == "__main__":
    main()
