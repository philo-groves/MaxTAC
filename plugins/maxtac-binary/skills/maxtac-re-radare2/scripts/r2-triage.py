#!/usr/bin/env python3
"""Collect repeatable radare2/rabin2 binary triage evidence."""

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
        raise SystemExit(f"Target file not found: {path}")
    return {"path": str(path.resolve()), "size": path.stat().st_size, "sha256": sha256_file(path)}


def resolve_tool(name: str, override: str | None) -> str | None:
    if override:
        return str(Path(override).expanduser())
    return shutil.which(name)


def run_command(command: list[str], timeout: int) -> dict[str, Any]:
    record: dict[str, Any] = {"command": subprocess.list2cmdline(command)}
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False, timeout=timeout)
    except OSError as exc:
        record["error"] = str(exc)
        return record
    except subprocess.TimeoutExpired as exc:
        record["error"] = "timed out"
        record["stdout"] = (exc.stdout or "").strip() if isinstance(exc.stdout, str) else ""
        record["stderr"] = (exc.stderr or "").strip() if isinstance(exc.stderr, str) else ""
        return record
    record.update({"exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    return record


def write_command_output(output_dir: Path, name: str, result: dict[str, Any]) -> dict[str, Any]:
    suffix = ".json" if name.endswith("-json") else ".txt"
    output_path = output_dir / f"{name}{suffix}"
    output_path.write_text(result.get("stdout", ""), encoding="utf-8")
    return {
        "name": name,
        "path": str(output_path),
        "command": result.get("command"),
        "exit_code": result.get("exit_code"),
        "error": result.get("error"),
        "stderr": result.get("stderr", ""),
    }


def collect_rabin2(target: Path, output_dir: Path, rabin2: str | None, timeout: int) -> list[dict[str, Any]]:
    commands = [
        ("rabin2-info", ["-I", str(target)]),
        ("rabin2-info-json", ["-Ij", str(target)]),
        ("rabin2-imports-json", ["-ij", str(target)]),
        ("rabin2-exports-json", ["-Ej", str(target)]),
        ("rabin2-sections-json", ["-Sj", str(target)]),
        ("rabin2-strings-json", ["-zj", str(target)]),
        ("rabin2-libs-json", ["-lj", str(target)]),
    ]
    records: list[dict[str, Any]] = []
    if not rabin2:
        return [{"name": "rabin2", "error": "rabin2 not found"}]
    version = run_command([rabin2, "-v"], timeout)
    records.append(write_command_output(output_dir, "rabin2-version", version))
    for name, args in commands:
        result = run_command([rabin2, *args], timeout)
        records.append(write_command_output(output_dir, name, result))
    return records


def collect_r2(target: Path, output_dir: Path, r2: str | None, timeout: int, deep: bool) -> list[dict[str, Any]]:
    if not r2:
        return [{"name": "r2", "error": "r2 not found"}]
    analysis = "aaaa" if deep else "aaa"
    commands = [
        ("r2-version", ["-v"]),
        (
            "r2-analysis-functions-json",
            [
                "-q",
                "-2",
                "-e",
                "scr.color=false",
                "-e",
                "io.cache=true",
                "-c",
                analysis,
                "-c",
                "aflj",
                "-c",
                "q",
                str(target),
            ],
        ),
        (
            "r2-analysis-xrefs-json",
            [
                "-q",
                "-2",
                "-e",
                "scr.color=false",
                "-e",
                "io.cache=true",
                "-c",
                analysis,
                "-c",
                "axgj",
                "-c",
                "q",
                str(target),
            ],
        ),
    ]
    records: list[dict[str, Any]] = []
    for name, args in commands:
        result = run_command([r2, *args], timeout)
        records.append(write_command_output(output_dir, name, result))
    return records


def collect_rahash2(target: Path, output_dir: Path, rahash2: str | None, timeout: int) -> list[dict[str, Any]]:
    if not rahash2:
        return [{"name": "rahash2", "error": "rahash2 not found"}]
    result = run_command([rahash2, "-a", "md5,sha1,sha256", str(target)], timeout)
    return [write_command_output(output_dir, "rahash2-hashes", result)]


def cmd_main(args: argparse.Namespace) -> None:
    target = Path(args.target).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    tools = {
        "r2": resolve_tool("r2", args.r2),
        "rabin2": resolve_tool("rabin2", args.rabin2),
        "rahash2": resolve_tool("rahash2", args.rahash2),
    }
    manifest: dict[str, Any] = {
        "version": 1,
        "time": now(),
        "target": file_record(target),
        "output_dir": str(output_dir),
        "tools": tools,
        "deep_analysis": args.deep,
        "outputs": [],
    }
    manifest["outputs"].extend(collect_rabin2(target, output_dir, tools["rabin2"], args.timeout))
    manifest["outputs"].extend(collect_rahash2(target, output_dir, tools["rahash2"], args.timeout))
    if not args.skip_r2:
        manifest["outputs"].extend(collect_r2(target, output_dir, tools["r2"], args.timeout, args.deep))

    manifest_path = output_dir / "r2-triage.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(manifest, indent=2))
    else:
        print(f"radare2 triage evidence: {output_dir}")
        print(f"- manifest: {manifest_path}")
        missing = [name for name, path in tools.items() if not path]
        if missing:
            print(f"- missing tools: {', '.join(missing)}")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC radare2 binary triage collector")
    parser.add_argument("target")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--r2")
    parser.add_argument("--rabin2")
    parser.add_argument("--rahash2")
    parser.add_argument("--skip-r2", action="store_true")
    parser.add_argument("--deep", action="store_true", help="Use deeper r2 analysis (aaaa instead of aaa)")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    cmd_main(args)


if __name__ == "__main__":
    main()
