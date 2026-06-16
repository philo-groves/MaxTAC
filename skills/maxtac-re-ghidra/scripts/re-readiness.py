#!/usr/bin/env python3
"""Check and record MaxTAC reverse-engineering tool readiness."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOL_CHOICES = ("ghidra", "radare2", "jadx")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def target_record(value: str) -> dict[str, Any]:
    path = Path(value).expanduser().resolve()
    if not path.exists():
        return {"path": str(path), "exists": False}
    record: dict[str, Any] = {"path": str(path), "exists": True}
    if path.is_file():
        record.update({"kind": "file", "size": path.stat().st_size, "sha256": sha256_file(path)})
    elif path.is_dir():
        record.update({"kind": "directory", "files": sum(1 for item in path.rglob("*") if item.is_file())})
    return record


def run_capture(command: list[str], timeout: int = 20) -> dict[str, Any]:
    command_line = subprocess.list2cmdline(command)
    record: dict[str, Any] = {"command": command_line}
    try:
        completed = subprocess.run(
            command_line,
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


def found_command(name: str, override: str | None = None) -> str | None:
    if override:
        return str(Path(override).expanduser())
    return shutil.which(name)


def maybe_tool(path: str | None, args: list[str], timeout: int = 20) -> dict[str, Any]:
    if not path:
        return {"found": False}
    record = {"found": True, "path": path}
    record["probe"] = run_capture([path, *args], timeout=timeout)
    return record


def ghidra_home_paths(ghidra_home: str | None) -> dict[str, str | None]:
    home_value = ghidra_home or os.environ.get("GHIDRA_HOME")
    home = Path(home_value).expanduser() if home_value else None
    if not home:
        return {
            "home": None,
            "analyze_headless": found_command("analyzeHeadless") or found_command("analyzeHeadless.bat"),
            "ghidra_run": found_command("ghidraRun") or found_command("ghidraRun.bat"),
            "pyghidra_run": found_command("pyghidraRun") or found_command("pyghidraRun.bat"),
        }
    support = home / "support"
    return {
        "home": str(home),
        "analyze_headless": str(support / ("analyzeHeadless.bat" if os.name == "nt" else "analyzeHeadless")),
        "ghidra_run": str(home / ("ghidraRun.bat" if os.name == "nt" else "ghidraRun")),
        "pyghidra_run": str(support / ("pyghidraRun.bat" if os.name == "nt" else "pyghidraRun")),
    }


def check_ghidra(args: argparse.Namespace) -> dict[str, Any]:
    paths = ghidra_home_paths(args.ghidra_home)
    analyze = paths.get("analyze_headless")
    result: dict[str, Any] = {
        "tool": "ghidra",
        "paths": paths,
        "java": maybe_tool(found_command("java", args.java), ["-version"]),
        "analyze_headless": maybe_tool(analyze, ["-help"]),
    }
    return result


def check_radare2(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "tool": "radare2",
        "r2": maybe_tool(found_command("r2", args.r2), ["-v"]),
        "rabin2": maybe_tool(found_command("rabin2", args.rabin2), ["-v"]),
        "rahash2": maybe_tool(found_command("rahash2", args.rahash2), ["-h"]),
        "rafind2": maybe_tool(found_command("rafind2", args.rafind2), ["-h"]),
        "radiff2": maybe_tool(found_command("radiff2", args.radiff2), ["-v"]),
    }


def check_jadx(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "tool": "jadx",
        "java": maybe_tool(found_command("java", args.java), ["-version"]),
        "jadx": maybe_tool(found_command("jadx", args.jadx), ["--version"]),
        "jadx_gui": maybe_tool(found_command("jadx-gui", args.jadx_gui), ["--help"]),
    }


def selected_tools(values: list[str] | None) -> list[str]:
    if not values or "all" in values:
        return list(TOOL_CHOICES)
    result: list[str] = []
    for value in values:
        if value not in TOOL_CHOICES:
            raise SystemExit(f"Unknown tool: {value}")
        if value not in result:
            result.append(value)
    return result


def probe_ok(value: dict[str, Any] | None) -> bool:
    if not value or not value.get("found"):
        return False
    probe = value.get("probe", {})
    return not probe.get("error") and probe.get("exit_code") in (0, None)


def readiness_status(check: dict[str, Any]) -> str:
    tool = check.get("tool")
    if tool == "ghidra":
        return "ready" if probe_ok(check.get("analyze_headless")) and probe_ok(check.get("java")) else "missing"
    if tool == "radare2":
        return "ready" if probe_ok(check.get("r2")) or probe_ok(check.get("rabin2")) else "missing"
    if tool == "jadx":
        return "ready" if probe_ok(check.get("jadx")) and probe_ok(check.get("java")) else "missing"
    return "missing"


def render_markdown(payload: dict[str, Any]) -> str:
    lines = ["# RE Readiness", ""]
    lines.append(f"- Time: {payload['time']}")
    lines.append(f"- Working directory: `{payload['cwd']}`")
    lines.append("")
    if payload["targets"]:
        lines.append("## Targets")
        lines.append("")
        for target in payload["targets"]:
            status = "ok" if target.get("exists") else "missing"
            detail = f" sha256={target.get('sha256')}" if target.get("sha256") else ""
            lines.append(f"- {status}: `{target['path']}`{detail}")
        lines.append("")
    lines.append("## Tools")
    lines.append("")
    for check in payload["checks"]:
        lines.append(f"### {check['tool']}")
        lines.append("")
        lines.append(f"- Status: {readiness_status(check)}")
        for key, value in check.items():
            if key in {"tool", "paths"} or not isinstance(value, dict):
                continue
            found = "found" if value.get("found") else "missing"
            lines.append(f"- {key}: {found} `{value.get('path', '')}`")
            probe = value.get("probe")
            if probe:
                lines.append(f"  - command: `{probe.get('command')}`")
                if "exit_code" in probe:
                    lines.append(f"  - exit: {probe.get('exit_code')}")
                output = probe.get("stdout") or probe.get("stderr") or probe.get("error")
                if output:
                    first_line = str(output).splitlines()[0]
                    lines.append(f"  - output: {first_line}")
        paths = check.get("paths")
        if paths:
            for key, value in paths.items():
                lines.append(f"- {key}: `{value}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_output(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    if args.json:
        text = json.dumps(payload, indent=2) + "\n"
    else:
        text = render_markdown(payload)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"Wrote readiness evidence: {output}")
    else:
        print(text, end="")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC RE readiness evidence collector")
    parser.add_argument("--tool", action="append", choices=("all", *TOOL_CHOICES), help="Tool to check; defaults to all")
    parser.add_argument("--target", action="append", help="Target binary/archive to hash")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--ghidra-home")
    parser.add_argument("--java")
    parser.add_argument("--r2")
    parser.add_argument("--rabin2")
    parser.add_argument("--rahash2")
    parser.add_argument("--rafind2")
    parser.add_argument("--radiff2")
    parser.add_argument("--jadx")
    parser.add_argument("--jadx-gui")
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    checks = []
    for tool in selected_tools(args.tool):
        if tool == "ghidra":
            checks.append(check_ghidra(args))
        elif tool == "radare2":
            checks.append(check_radare2(args))
        elif tool == "jadx":
            checks.append(check_jadx(args))
    payload = {
        "version": 1,
        "time": now(),
        "cwd": str(Path.cwd()),
        "targets": [target_record(value) for value in args.target or []],
        "checks": checks,
    }
    write_output(args, payload)


if __name__ == "__main__":
    main()
