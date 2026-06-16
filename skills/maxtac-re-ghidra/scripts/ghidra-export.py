#!/usr/bin/env python3
"""Plan or run a repeatable Ghidra headless export."""

from __future__ import annotations

import argparse
import json
import os
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


def analyze_headless_path(args: argparse.Namespace) -> str | None:
    if args.analyze_headless:
        return str(Path(args.analyze_headless).expanduser())
    home_value = args.ghidra_home or os.environ.get("GHIDRA_HOME")
    if home_value:
        home = Path(home_value).expanduser()
        return str(home / "support" / ("analyzeHeadless.bat" if os.name == "nt" else "analyzeHeadless"))
    return shutil.which("analyzeHeadless") or shutil.which("analyzeHeadless.bat")


def build_command(args: argparse.Namespace, analyze_headless: str) -> list[str]:
    command = [
        analyze_headless,
        str(Path(args.project_dir).expanduser().resolve()),
        args.project_name,
        "-import",
        str(Path(args.input).expanduser().resolve()),
    ]
    if args.processor:
        command.extend(["-processor", args.processor])
    if args.compiler:
        command.extend(["-cspec", args.compiler])
    if args.loader:
        command.extend(["-loader", args.loader])
    for value in args.loader_arg or []:
        command.extend(["-loader-arg", value])
    if args.no_analysis:
        command.append("-noanalysis")
    if args.overwrite:
        command.append("-overwrite")
    if args.read_only:
        command.append("-readOnly")
    if args.log:
        command.extend(["-log", args.log])
    if args.script_log:
        command.extend(["-scriptlog", args.script_log])
    if args.analysis_timeout:
        command.extend(["-analysisTimeoutPerFile", str(args.analysis_timeout)])
    for value in args.script_path or []:
        command.extend(["-scriptPath", value])
    for value in args.pre_script or []:
        command.extend(["-preScript", value])
    for value in args.post_script or []:
        command.extend(["-postScript", value])
    for value in args.extra_arg or []:
        command.append(value)
    return command


def run_command(command: list[str], timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False, timeout=timeout)
    except OSError as exc:
        return {"error": str(exc), "command": subprocess.list2cmdline(command)}
    except subprocess.TimeoutExpired as exc:
        return {
            "error": "timed out",
            "command": subprocess.list2cmdline(command),
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
        }
    return {
        "command": subprocess.list2cmdline(command),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def output_file_records(output_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not output_dir.exists():
        return records
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name not in {"ghidra-export.json", "command.txt", "run.log"}:
            records.append(file_record(path))
    return records


def cmd_main(args: argparse.Namespace) -> None:
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    project_dir = Path(args.project_dir).expanduser().resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    args.project_dir = str(project_dir)
    if not args.project_name:
        args.project_name = input_path.stem

    analyze_headless = analyze_headless_path(args)
    if not analyze_headless:
        raise SystemExit("Could not find analyzeHeadless. Pass --ghidra-home or --analyze-headless.")

    command = build_command(args, analyze_headless)
    command_line = subprocess.list2cmdline(command)
    manifest: dict[str, Any] = {
        "version": 1,
        "time": now(),
        "input": file_record(input_path),
        "output_dir": str(output_dir),
        "project_dir": str(project_dir),
        "project_name": args.project_name,
        "settings": {
            "processor": args.processor,
            "compiler": args.compiler,
            "loader": args.loader,
            "loader_args": args.loader_arg or [],
            "analysis_timeout": args.analysis_timeout,
            "no_analysis": args.no_analysis,
            "overwrite": args.overwrite,
            "read_only": args.read_only,
            "log": args.log,
            "script_log": args.script_log,
            "script_paths": args.script_path or [],
            "pre_scripts": args.pre_script or [],
            "post_scripts": args.post_script or [],
            "extra_args": args.extra_arg or [],
        },
        "command": command_line,
        "ran": False,
    }
    (output_dir / "command.txt").write_text(command_line + "\n", encoding="utf-8")

    if args.run:
        result = run_command(command, args.timeout)
        manifest["ran"] = True
        manifest["result"] = {
            key: value for key, value in result.items() if key not in {"stdout", "stderr"}
        }
        (output_dir / "run.log").write_text(
            "\n".join(
                [
                    f"$ {command_line}",
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
        manifest["outputs"] = output_file_records(output_dir)

    manifest_path = output_dir / "ghidra-export.json"
    write_json(manifest_path, manifest)
    if args.json:
        print(json.dumps(manifest, indent=2))
    else:
        print(f"Ghidra export {'ran' if args.run else 'planned'}: {output_dir}")
        print(f"- manifest: {manifest_path}")
        print(f"- command: {output_dir / 'command.txt'}")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC Ghidra export planner/runner")
    parser.add_argument("input")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--project-name")
    parser.add_argument("--ghidra-home")
    parser.add_argument("--analyze-headless")
    parser.add_argument("--processor")
    parser.add_argument("--compiler")
    parser.add_argument("--loader")
    parser.add_argument("--loader-arg", action="append")
    parser.add_argument("--analysis-timeout", type=int)
    parser.add_argument("--script-path", action="append")
    parser.add_argument("--pre-script", action="append")
    parser.add_argument("--post-script", action="append")
    parser.add_argument("--extra-arg", action="append")
    parser.add_argument("--no-analysis", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--read-only", action="store_true")
    parser.add_argument("--log")
    parser.add_argument("--script-log")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    cmd_main(args)


if __name__ == "__main__":
    main()
