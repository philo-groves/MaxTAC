#!/usr/bin/env python3
"""MaxTAC MCP server exposing deterministic workflow helpers."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, Callable


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ".maxtac-workspace.json"
WORKSPACE_DIRS = {
    "research": "scalable markdown research library",
    "debates": "debater subagent results",
    "audits": "auditor subagent results",
    "proof": "proof-of-vulnerability development",
    "fuzz": "fuzzing inputs, scripts, and artifacts",
    "tmp": "temporary files that can be deleted between sessions",
    "reporting": "submission-ready reports and evidence indexes",
}
LEDGER_FILES = {
    "primitive": Path("primitives.json"),
    "chain": Path("chains.json"),
}
LEDGER_TYPES = (*LEDGER_FILES, "all")
STATES = (
    "discovered",
    "confident",
    "validated",
    "proofed",
    "duplicate",
    "limited",
    "de-escalated",
)
PHASES = (
    "prepare",
    "scan",
    "validation",
    "primitive-proof",
    "chain-proof",
    "reporting",
)
PHASE_ALIASES = {
    "prep": "prepare",
    "validate": "validation",
    "primitive": "primitive-proof",
    "primitiveproof": "primitive-proof",
    "primitive-proofing": "primitive-proof",
    "proof": "primitive-proof",
    "chain": "chain-proof",
    "chainproof": "chain-proof",
    "chain-proofing": "chain-proof",
    "report": "reporting",
}
PACKET_TYPES = ("auto", "surface", "cfg", "opengrep")


class ToolFailure(Exception):
    """A user-facing tool failure."""

    def __init__(self, message: str, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.payload = payload


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def generated_id(prefix: str, seed: str | None = None) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if seed:
        suffix = hashlib.sha256(seed.encode("utf-8", errors="replace")).hexdigest()[:8]
    else:
        suffix = secrets.token_hex(3)
    return f"{prefix}-{timestamp}-{suffix}"


def slugify(value: str, default: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or default


def load_script(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ToolFailure(f"Could not load helper script: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def ledger_module() -> ModuleType:
    return load_script("maxtac_ledger_helper", PLUGIN_ROOT / "skills" / "maxtac-core-ledger" / "scripts" / "ledger.py")


def workspace_module() -> ModuleType:
    return load_script("maxtac_workspace_helper", PLUGIN_ROOT / "skills" / "maxtac-core-workflow" / "scripts" / "workspace.py")


def packet_module() -> ModuleType:
    return load_script("maxtac_packet_helper", PLUGIN_ROOT / "skills" / "maxtac-sast-surface-triage" / "scripts" / "packet.py")


HELPER_SCRIPTS = {
    "workspace": PLUGIN_ROOT / "skills" / "maxtac-core-workflow" / "scripts" / "workspace.py",
    "readiness": PLUGIN_ROOT / "skills" / "maxtac-core-subagents" / "scripts" / "readiness-check.py",
    "debug_evidence": PLUGIN_ROOT / "skills" / "maxtac-dast-debugger" / "scripts" / "debug-evidence.py",
    "fuzz_campaign": PLUGIN_ROOT / "skills" / "maxtac-dast-fuzzer" / "scripts" / "fuzz-campaign.py",
    "lpac_proof": PLUGIN_ROOT / "skills" / "maxtac-msrc-lpac-proof" / "scripts" / "lpac-proof.py",
    "ipsw_provenance": PLUGIN_ROOT / "skills" / "maxtac-asb-ipsw" / "scripts" / "ipsw-provenance.py",
    "re_readiness": PLUGIN_ROOT / "skills" / "maxtac-re-ghidra" / "scripts" / "re-readiness.py",
    "ghidra_export": PLUGIN_ROOT / "skills" / "maxtac-re-ghidra" / "scripts" / "ghidra-export.py",
    "jadx_export": PLUGIN_ROOT / "skills" / "maxtac-re-jadx" / "scripts" / "jadx-export.py",
    "r2_triage": PLUGIN_ROOT / "skills" / "maxtac-re-radare2" / "scripts" / "r2-triage.py",
}


def resolve_workspace_root(value: str | None = None, *, must_exist: bool = True) -> Path:
    raw = value or os.environ.get("MAXTAC_WORKSPACE_ROOT") or os.getcwd()
    root = Path(raw).expanduser().resolve()
    if must_exist and not root.exists():
        raise ToolFailure(f"Workspace root does not exist: {root}")
    if must_exist and not root.is_dir():
        raise ToolFailure(f"Workspace root is not a directory: {root}")
    return root


def ensure_within(root: Path, path: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ToolFailure(f"{label} escapes workspace root: {resolved_path}") from exc
    return resolved_path


def workspace_path(root: Path, value: str | Path, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return ensure_within(root, path, label)


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ToolFailure(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ToolFailure(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ToolFailure(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    raise ToolFailure("Expected a string array")


def require_text(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if value is None or not str(value).strip():
        raise ToolFailure(f"Missing required field: {key}")
    return str(value)


def kebab(value: str) -> str:
    return value.replace("_", "-")


def append_option(argv: list[str], key: str, value: Any, *, flag: str | None = None) -> None:
    if value is None:
        return
    if isinstance(value, str) and not value.strip():
        return
    argv.extend([flag or f"--{kebab(key)}", str(value)])


def append_many(argv: list[str], key: str, value: Any, *, flag: str | None = None) -> None:
    for item in as_list(value):
        argv.extend([flag or f"--{kebab(key)}", item])


def append_flag(argv: list[str], key: str, value: Any, *, flag: str | None = None) -> None:
    if bool(value):
        argv.append(flag or f"--{kebab(key)}")


def append_boolean_optional(argv: list[str], key: str, value: Any) -> None:
    if value is None:
        return
    argv.append(f"--{kebab(key)}" if bool(value) else f"--no-{kebab(key)}")


def parse_stdout_json(stdout: str) -> Any | None:
    text = stdout.strip()
    if not text or text[0] not in "[{":
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def run_helper_script(script_key: str, argv: list[str], *, cwd: Path | None = None, timeout: int = 3600) -> dict[str, Any]:
    script = HELPER_SCRIPTS[script_key]
    command = [sys.executable, str(script), *argv]
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd or PLUGIN_ROOT),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        payload = {
            "script": str(script.relative_to(PLUGIN_ROOT)),
            "argv": argv,
            "timeout_seconds": timeout,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
        }
        raise ToolFailure(f"Helper script timed out: {script.name}", payload) from exc

    payload: dict[str, Any] = {
        "script": str(script.relative_to(PLUGIN_ROOT)),
        "argv": argv,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
    parsed = parse_stdout_json(completed.stdout)
    if parsed is not None:
        payload["json"] = parsed
    if completed.returncode != 0:
        raise ToolFailure(f"Helper script failed: {script.name}", payload)
    return payload


def selected_ledger_types(raw_type: str | None, *, allow_all: bool, default_type: str = "primitive") -> list[str]:
    selection = raw_type or ("all" if allow_all else default_type)
    if selection not in LEDGER_TYPES:
        raise ToolFailure(f"Unknown ledger type: {selection}")
    if selection == "all":
        if not allow_all:
            raise ToolFailure("This operation requires type primitive or chain")
        return ["primitive", "chain"]
    return [selection]


def selected_ledger_types_for_args(args: dict[str, Any], *, allow_all: bool, default_type: str = "primitive") -> list[str]:
    selected = selected_ledger_types(args.get("type"), allow_all=allow_all, default_type=default_type)
    if args.get("file") and len(selected) > 1:
        raise ToolFailure("file requires type primitive or chain")
    return selected


def ledger_path(root: Path, ledger_type: str, override_file: str | None = None) -> Path:
    if override_file:
        return workspace_path(root, override_file, "ledger file")
    return root / LEDGER_FILES[ledger_type]


def query_namespace(args: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(
        title=args.get("title"),
        target=args.get("target"),
        category=args.get("category"),
        location=as_list(args.get("locations") or args.get("location")),
        evidence=args.get("evidence"),
        related=as_list(args.get("related")),
    )


def tool_ledger_init(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    force = bool(args.get("force", False))
    selected = selected_ledger_types_for_args(args, allow_all=True)
    mod = ledger_module()
    results: list[dict[str, Any]] = []
    for ledger_type in selected:
        path = ledger_path(root, ledger_type, args.get("file"))
        if path.exists() and not force:
            ledger = mod.load_ledger(path, ledger_type)
            status = "exists"
        else:
            ledger = {"version": 1, "type": ledger_type, "findings": []}
            mod.save_ledger(path, ledger, ledger_type)
            status = "created"
        results.append({"type": ledger_type, "path": str(path), "status": status, "findings": len(ledger.get("findings", []))})
    return {"workspace_root": str(root), "ledgers": results}


def tool_ledger_search(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    limit = int(args.get("limit", 10))
    selected = selected_ledger_types_for_args(args, allow_all=True)
    mod = ledger_module()
    query = query_namespace(args)
    matches: list[dict[str, Any]] = []
    for ledger_type in selected:
        path = ledger_path(root, ledger_type, args.get("file"))
        ledger = mod.load_ledger(path, ledger_type)
        for score, finding in mod.search_findings(ledger, query)[:limit]:
            matches.append({"type": ledger_type, "path": str(path), "score": score, "finding": finding})
    matches.sort(key=lambda item: (item["score"], item["finding"].get("id", "")), reverse=True)
    return {"workspace_root": str(root), "matches": matches[:limit]}


def tool_ledger_add(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    ledger_type = selected_ledger_types_for_args(args, allow_all=False)[0]
    mod = ledger_module()
    required = ("title", "target", "category", "summary", "evidence")
    missing = [key for key in required if not args.get(key)]
    if missing:
        raise ToolFailure(f"Missing required ledger fields: {', '.join(missing)}")
    path = ledger_path(root, ledger_type, args.get("file"))
    ledger = mod.load_ledger(path, ledger_type)
    add_args = SimpleNamespace(
        title=str(args["title"]),
        target=str(args["target"]),
        category=str(args["category"]),
        location=as_list(args.get("locations") or args.get("location")),
        evidence=as_list(args.get("evidence")),
        related=as_list(args.get("related")),
    )
    duplicates = mod.search_findings(ledger, add_args)
    if duplicates and not args.get("allow_duplicate", False):
        score, finding = duplicates[0]
        raise ToolFailure(f"Likely duplicate in {ledger_type} ledger: {finding.get('id')} score={score} title={finding.get('title')}")
    state = str(args.get("state") or "discovered")
    if state not in STATES:
        raise ToolFailure(f"Unknown finding state: {state}")
    timestamp = mod.now()
    primitive_refs = mod.parse_csv(as_list(args.get("primitives") or args.get("primitive")))
    related = mod.unique(mod.parse_csv(add_args.related) + primitive_refs)
    finding = {
        "id": mod.next_id(ledger["findings"]),
        "type": ledger_type,
        "title": add_args.title,
        "target": add_args.target,
        "category": add_args.category,
        "locations": mod.parse_csv(add_args.location),
        "summary": str(args["summary"]),
        "evidence": mod.parse_repeated(add_args.evidence),
        "state": state,
        "related": related,
        "milestones": [{"time": timestamp, "note": str(args.get("note") or "Finding added.")}],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    if ledger_type == "chain":
        finding["primitives"] = primitive_refs
    ledger["findings"].append(finding)
    mod.save_ledger(path, ledger, ledger_type)
    return {"workspace_root": str(root), "path": str(path), "finding": finding}


def find_ledger_finding(root: Path, args: dict[str, Any], finding_id: str) -> tuple[str, Path, dict[str, Any], dict[str, Any]]:
    mod = ledger_module()
    matches = []
    for ledger_type in selected_ledger_types_for_args(args, allow_all=True):
        path = ledger_path(root, ledger_type, args.get("file"))
        ledger = mod.load_ledger(path, ledger_type)
        for finding in ledger.get("findings", []):
            if str(finding.get("id", "")).lower() == finding_id.lower():
                matches.append((ledger_type, path, ledger, finding))
    if not matches:
        raise ToolFailure(f"Finding not found: {finding_id}")
    if len(matches) > 1:
        locations = ", ".join(f"{item[0]}:{item[1]}" for item in matches)
        raise ToolFailure(f"Finding id exists in multiple ledgers; pass type. Matches: {locations}")
    return matches[0]


def tool_ledger_update(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    finding_id = str(args.get("finding_id") or "")
    if not finding_id:
        raise ToolFailure("Missing required field: finding_id")
    mod = ledger_module()
    ledger_type, path, ledger, finding = find_ledger_finding(root, args, finding_id)
    if args.get("state"):
        state = str(args["state"])
        if state not in STATES:
            raise ToolFailure(f"Unknown finding state: {state}")
        finding["state"] = state
    for key in ("title", "target", "category", "summary"):
        if args.get(key) is not None:
            finding[key] = str(args[key])
    if args.get("locations") is not None or args.get("location") is not None:
        finding["locations"] = mod.parse_csv(as_list(args.get("locations") or args.get("location")))
    if args.get("evidence") is not None:
        finding["evidence"] = mod.parse_repeated(as_list(args.get("evidence")))
    if args.get("related") is not None:
        finding["related"] = mod.parse_csv(as_list(args.get("related")))
    if args.get("primitives") is not None or args.get("primitive") is not None:
        primitives = mod.parse_csv(as_list(args.get("primitives") or args.get("primitive")))
        finding["primitives"] = primitives
        finding["related"] = mod.unique(finding.get("related", []) + primitives)
    if args.get("note"):
        finding.setdefault("milestones", []).append({"time": mod.now(), "note": str(args["note"])})
    finding["type"] = ledger_type
    finding["updated_at"] = mod.now()
    mod.save_ledger(path, ledger, ledger_type)
    return {"workspace_root": str(root), "path": str(path), "finding": finding}


def tool_ledger_summary(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    mod = ledger_module()
    result = []
    for ledger_type in selected_ledger_types_for_args(args, allow_all=True):
        path = ledger_path(root, ledger_type, args.get("file"))
        ledger = mod.load_ledger(path, ledger_type)
        counts: dict[str, int] = {state: 0 for state in STATES}
        for finding in ledger.get("findings", []):
            state = str(finding.get("state") or "unknown")
            counts[state] = counts.get(state, 0) + 1
        active = [finding for finding in ledger.get("findings", []) if finding.get("state") not in {"duplicate", "de-escalated"}]
        result.append(
            {
                "type": ledger_type,
                "path": str(path),
                "total": len(ledger.get("findings", [])),
                "active": len(active),
                "counts": {state: count for state, count in counts.items() if count},
                "active_findings": active,
            }
        )
    return {"workspace_root": str(root), "ledgers": result}


def tool_ledger_list(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    state = args.get("state")
    if state and state not in STATES:
        raise ToolFailure(f"Unknown finding state: {state}")
    limit = int(args.get("limit") or 0)
    mod = ledger_module()
    findings = []
    for ledger_type in selected_ledger_types_for_args(args, allow_all=True):
        path = ledger_path(root, ledger_type, args.get("file"))
        ledger = mod.load_ledger(path, ledger_type)
        selected = ledger.get("findings", [])
        if state:
            selected = [finding for finding in selected if finding.get("state") == state]
        if limit:
            selected = selected[:limit]
        for finding in selected:
            findings.append({"type": ledger_type, "path": str(path), "finding": finding})
    return {"workspace_root": str(root), "findings": findings}


def tool_ledger_milestone(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    finding_id = require_text(args, "finding_id")
    note = require_text(args, "note")
    mod = ledger_module()
    ledger_type, path, ledger, finding = find_ledger_finding(root, args, finding_id)
    finding.setdefault("milestones", []).append({"time": mod.now(), "note": note})
    finding["type"] = ledger_type
    finding["updated_at"] = mod.now()
    mod.save_ledger(path, ledger, ledger_type)
    return {"workspace_root": str(root), "path": str(path), "finding": finding}


def tool_workspace_init(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    mod = workspace_module()
    phase = mod.normalize_phase(str(args.get("phase") or "prepare"))
    created_dirs: list[str] = []
    for dirname in WORKSPACE_DIRS:
        path = root / dirname
        path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(path))
    program_info = root / "program-info.md"
    program_info_status = "skipped"
    if not args.get("no_program_info", False):
        if program_info.exists() and not args.get("force_program_info", False):
            program_info_status = "exists"
        else:
            template = mod.read_template(mod.PROGRAM_INFO_TEMPLATE, "# [program name]\n[description of the program]\n")
            program_info.write_text(template.rstrip() + "\n", encoding="utf-8")
            program_info_status = "created"
    ledger_results = []
    for ledger_type, relative_path in LEDGER_FILES.items():
        status = mod.create_ledger(root / relative_path, ledger_type, force=bool(args.get("force_ledgers", False)))
        ledger_results.append({"type": ledger_type, "path": str(root / relative_path), "status": status})
    state = mod.load_state(root)
    if state and not args.get("force_state", False):
        state_status = "exists"
    else:
        state = mod.initial_state(phase, str(args.get("note") or "Workspace initialized."))
        mod.save_state(root, state)
        state_status = "initialized"
    return {
        "workspace_root": str(root),
        "directories": created_dirs,
        "program_info": {"path": str(program_info), "status": program_info_status},
        "ledgers": ledger_results,
        "state": {"path": str(root / STATE_FILE), "status": state_status, "phase": state.get("current_phase")},
    }


def tool_workspace_status(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    mod = workspace_module()
    state = mod.load_state(root)
    max_lines = int(args.get("max_lines") or mod.LARGE_MARKDOWN_LINES)
    payload: dict[str, Any] = {
        "workspace_root": str(root),
        "phase": state.get("current_phase") if state else None,
        "files": {},
        "directories": {},
        "ledgers": {},
        "large_markdown": [],
        "report_ready": mod.report_readiness(root, args.get("chain")),
    }
    for filename in mod.WORKSPACE_FILES:
        payload["files"][filename] = (root / filename).exists()
    for dirname in WORKSPACE_DIRS:
        payload["directories"][dirname] = (root / dirname).is_dir()
    for ledger_type in LEDGER_FILES:
        path, ledger, error = mod.load_ledger(root, ledger_type)
        payload["ledgers"][ledger_type] = {
            "path": str(path),
            "error": error,
            "counts": mod.ledger_counts(ledger) if ledger else {},
        }
    payload["large_markdown"] = [
        {"path": mod.relative_to(path, root), "lines": lines}
        for path, lines in mod.large_markdown_files(root, max_lines)
    ]
    return payload


def tool_workspace_phase(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    mod = workspace_module()
    if args.get("list"):
        return {
            "workspace_root": str(root),
            "phases": [
                {"phase": phase, "next": sorted(mod.PHASE_TRANSITIONS[phase])}
                for phase in mod.PHASES
            ],
        }
    state = mod.load_state(root)
    if state is None:
        state = mod.initial_state("prepare", "Workspace phase initialized.")
    current = str(state.get("current_phase", "prepare"))
    target_raw = args.get("phase")
    if not target_raw:
        return {"workspace_root": str(root), "current_phase": current, "allowed_next": sorted(mod.PHASE_TRANSITIONS[current])}
    target = mod.normalize_phase(str(target_raw))
    if target == current:
        mod.save_state(root, state)
        return {"workspace_root": str(root), "current_phase": current, "changed": False}
    allowed = mod.PHASE_TRANSITIONS[current]
    if target not in allowed and not args.get("force", False):
        raise ToolFailure(f"Invalid transition {current} -> {target}. Allowed: {', '.join(sorted(allowed))}. Use force to override.")
    timestamp = mod.now()
    state["current_phase"] = target
    state["updated_at"] = timestamp
    state.setdefault("phase_history", []).append(
        {
            "time": timestamp,
            "from": current,
            "to": target,
            "note": str(args.get("note") or ""),
        }
    )
    mod.save_state(root, state)
    return {"workspace_root": str(root), "previous_phase": current, "current_phase": target, "changed": True}


def tool_workspace_new_submodule(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    argv = ["new-submodule", "--root", str(root), require_text(args, "name")]
    append_option(argv, "parent", args.get("parent"))
    append_many(argv, "markdown", args.get("markdown"))
    append_option(argv, "title", args.get("title"))
    append_flag(argv, "no_artifacts", args.get("no_artifacts"))
    append_flag(argv, "force", args.get("force"))
    append_flag(argv, "overwrite", args.get("overwrite"))
    result = run_helper_script("workspace", argv, cwd=root)
    result["workspace_root"] = str(root)
    return result


def tool_workspace_split_large_markdown(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    argv = ["split-large-markdown", "--root", str(root), require_text(args, "markdown_file")]
    append_option(argv, "submodule", args.get("submodule"))
    append_option(argv, "large_threshold", args.get("large_threshold"))
    append_option(argv, "max_lines", args.get("max_lines"))
    append_many(argv, "copy_artifact", args.get("copy_artifact"))
    append_flag(argv, "delete_source", args.get("delete_source"))
    append_flag(argv, "delete_artifacts", args.get("delete_artifacts"))
    append_flag(argv, "verified", args.get("verified"))
    append_flag(argv, "force", args.get("force"))
    result = run_helper_script("workspace", argv, cwd=root)
    result["workspace_root"] = str(root)
    return result


def tool_workspace_report_ready(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    mod = workspace_module()
    return {
        "workspace_root": str(root),
        **mod.report_readiness(root, args.get("chain"), require_report_file=bool(args.get("require_report_file", False))),
    }


def read_optional_prompt(root: Path, args: dict[str, Any]) -> str:
    pieces: list[str] = []
    if args.get("prompt_file"):
        path = workspace_path(root, str(args["prompt_file"]), "prompt file")
        if not path.exists():
            raise ToolFailure(f"Prompt file not found: {path}")
        pieces.append(path.read_text(encoding="utf-8", errors="replace").rstrip())
    if args.get("prompt_text"):
        pieces.append(str(args["prompt_text"]).rstrip())
    return "\n\n".join(piece for piece in pieces if piece.strip())


def persist_audit_prompt(root: Path, raw_prompt: str) -> dict[str, Any]:
    audit_id = generated_id("audit", raw_prompt)
    audit_dir = ensure_within(root, root / "audits" / audit_id, "audit directory")
    if audit_dir.exists():
        audit_id = generated_id("audit")
        audit_dir = ensure_within(root, root / "audits" / audit_id, "audit directory")
    audit_dir.mkdir(parents=True, exist_ok=False)
    assessment_path = audit_dir / "assessment.md"
    prompt_path = audit_dir / "prompt.md"
    enriched = f"""## Codex Goal Instructions

Before doing any audit work, start the Codex goal mechanism using `/goal` in chat or `create_goal` when available. Use this goal prompt:

Positive objective: produce a focused MaxTAC audit assessment for the supplied hypothesis, auditor specialty, and evidence, then persist it to `{assessment_path}`.

Negative end outcome: if the supplied context, directly referenced files, or available tools are insufficient to decide the hypothesis within a bounded pass, stop broadening scope and persist an assessment with blockers, missing evidence, and the safest recommended next step.

Bounds: inspect the supplied packet/evidence, directly referenced files/functions, and immediately necessary callers/callees only. Do not start broad repo discovery, fuzzing, PoV construction, or unrelated refactors unless this prompt explicitly grants that scope. Do not complete the subagent run until the goal is either achieved or ended with the negative outcome above.

## Audit Task

{raw_prompt.rstrip()}

---

## MaxTAC Audit Persistence Instructions

Audit ID: `{audit_id}`
Audit directory: `{audit_dir}`

Persist the final audit assessment to `{assessment_path}` before completing the subagent run. Use Markdown. Include the vulnerability hypothesis or audit focus, method, reviewed files or components, findings, evidence, exploitability notes, blockers, and a clear conclusion. Persist supporting evidence files in the same audit directory when useful.
"""
    prompt_path.write_text(enriched, encoding="utf-8")
    return {"audit_id": audit_id, "audit_dir": str(audit_dir), "prompt_path": str(prompt_path), "assessment_path": str(assessment_path), "prompt": enriched}


def build_packet_auditor_prompt(root: Path, args: dict[str, Any]) -> str:
    packet_paths = as_list(args.get("packet_paths"))
    if not packet_paths:
        return ""
    mod = packet_module()
    resolved = [str(workspace_path(root, value, "packet")) for value in packet_paths]
    results = mod.load_results(resolved, str(args.get("packet_type") or "auto"))
    invalid = [result for result in results if result.get("errors")]
    if invalid and not args.get("allow_invalid_packets", False):
        messages = []
        for result in invalid:
            messages.extend(result.get("errors", []))
        raise ToolFailure("Invalid packet(s): " + "; ".join(messages))
    namespace = SimpleNamespace(
        auditor=args.get("auditor"),
        focus=args.get("focus"),
        auditor_filter=as_list(args.get("auditor_filters") or args.get("auditor_filter")),
    )
    return mod.render_auditor_prompt(results, namespace).rstrip()


def tool_audit_prompt_create(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    pieces = []
    raw = read_optional_prompt(root, args)
    if raw:
        pieces.append(raw)
    packet_prompt = build_packet_auditor_prompt(root, args)
    if packet_prompt:
        pieces.append(packet_prompt)
    if args.get("focus") and not pieces:
        pieces.append(f"# MaxTAC Audit Prompt\n\n- Focus: {args['focus']}")
    if not pieces:
        raise ToolFailure("Provide prompt_text, prompt_file, focus, or packet_paths")
    return persist_audit_prompt(root, "\n\n".join(pieces))


def persist_debate_prompt(root: Path, raw_prompt: str) -> dict[str, Any]:
    debate_id = generated_id("debate", raw_prompt)
    debate_dir = ensure_within(root, root / "debates" / debate_id, "debate directory")
    if debate_dir.exists():
        debate_id = generated_id("debate")
        debate_dir = ensure_within(root, root / "debates" / debate_id, "debate directory")
    debate_dir.mkdir(parents=True, exist_ok=False)
    prompt_path = debate_dir / "prompt.md"
    enriched = f"""## Codex Goal Instructions

Before doing any debate work, start the Codex goal mechanism using `/goal` in chat or `create_goal` when available. Use this goal prompt:

Positive objective: evaluate the single binary debate proposition from the supplied evidence and persist one well-supported ballot to `{debate_dir}`.

Negative end outcome: if the proposition cannot be judged from the supplied or directly referenced evidence within a bounded pass, stop broadening scope and persist a ballot with low confidence, explicit blockers, and the side defined by the proposition as not-proven; when unclear, choose `no`.

Bounds: review only the debate prompt, supplied evidence, directly referenced files/artifacts, and immediately necessary context needed to cast the ballot. Do not launch new audits, fuzzing, PoV construction, or broad discovery. Do not complete the subagent run until the goal is either achieved or ended with the negative outcome above.

## Debate Task

{raw_prompt.rstrip()}

---

## MaxTAC Debate Persistence Instructions

Debate ID: `{debate_id}`
Debate directory: `{debate_dir}`

Persist your ballot before completing the subagent run. Choose a stable subagent name for yourself, then write your ballot to `ballot-<subagent-name>.json` in the debate directory. Use this exact JSON structure:

```json
{{
  "debate": "{debate_id}",
  "subagent": "<subagent-name>",
  "choice": "yes",
  "confidence": 85,
  "reasoning": "detailed reasoning for the choice",
  "evidence": "detailed evidence supporting the reasoning",
  "blockers": null
}}
```

The `choice` value must be either `yes` or `no`. The `confidence` value must be an integer from 0 to 100. Use `blockers` for blockers or concerns about the debate topic, otherwise use null.
"""
    prompt_path.write_text(enriched, encoding="utf-8")
    return {"debate_id": debate_id, "debate_dir": str(debate_dir), "prompt_path": str(prompt_path), "prompt": enriched}


def tool_debate_prompt_create(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    raw = read_optional_prompt(root, args)
    proposition = args.get("proposition")
    if proposition:
        yes_means = args.get("yes_means")
        no_means = args.get("no_means")
        if not yes_means or not no_means:
            raise ToolFailure("proposition requires yes_means and no_means")
        context = str(args.get("context") or "").strip()
        lines = [
            "# MaxTAC Debate Prompt",
            "",
            f"Proposition: {proposition}",
            "",
            f"Yes means: {yes_means}",
            "",
            f"No means: {no_means}",
        ]
        if context:
            lines.extend(["", "Context:", "", context])
        raw = (raw + "\n\n" if raw else "") + "\n".join(lines)
    if not raw:
        raise ToolFailure("Provide prompt_text, prompt_file, or proposition with yes_means/no_means")
    return persist_debate_prompt(root, raw)


def load_ballot(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    choice = str(payload.get("choice", "")).lower()
    if choice not in {"yes", "no"}:
        raise ToolFailure(f"{path} ballot choice must be yes or no")
    confidence = payload.get("confidence")
    if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
        raise ToolFailure(f"{path} ballot confidence must be an integer from 0 to 100")
    return payload


def render_tally_markdown(debate_id: str, debate_dir: Path, ballots: list[tuple[Path, dict[str, Any]]], result: dict[str, Any]) -> str:
    lines = [
        f"# Debate Tally: {debate_id}",
        "",
        f"- Debate directory: `{debate_dir}`",
        f"- Ballots: {len(ballots)}",
        f"- Winner: {result['winner']}",
        f"- Yes: {result['counts'].get('yes', 0)}",
        f"- No: {result['counts'].get('no', 0)}",
        "",
    ]
    for path, ballot in ballots:
        subagent = str(ballot.get("subagent") or path.stem.removeprefix("ballot-"))
        lines.extend(
            [
                f"## {subagent}",
                "",
                f"- Ballot file: `{path}`",
                f"- Choice: {ballot.get('choice')}",
                f"- Confidence: {ballot.get('confidence')}",
                "",
                "### Reasoning",
                "",
                str(ballot.get("reasoning") or ""),
                "",
                "### Evidence",
                "",
                str(ballot.get("evidence") or ""),
                "",
            ]
        )
        if ballot.get("blockers"):
            lines.extend(["### Blockers", "", str(ballot["blockers"]), ""])
    return "\n".join(lines).rstrip() + "\n"


def tool_debate_tally(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    debate_id = str(args.get("debate_id") or "")
    if not debate_id:
        raise ToolFailure("Missing required field: debate_id")
    debate_dir = ensure_within(root, root / "debates" / debate_id, "debate directory")
    if not debate_dir.exists():
        raise ToolFailure(f"Debate not found: {debate_id}")
    ballot_paths = sorted(debate_dir.glob("ballot-*.json"))
    if not ballot_paths:
        raise ToolFailure(f"No ballots found for debate: {debate_id}")
    ballots = [(path, load_ballot(path)) for path in ballot_paths]
    counts: dict[str, int] = {"yes": 0, "no": 0}
    confidence_totals: dict[str, int] = {"yes": 0, "no": 0}
    for _, ballot in ballots:
        choice = str(ballot["choice"]).lower()
        counts[choice] += 1
        confidence_totals[choice] += int(ballot["confidence"])
    if counts["yes"] > counts["no"]:
        winner = "yes"
    elif counts["no"] > counts["yes"]:
        winner = "no"
    else:
        winner = "tie"
    average_confidence = {
        choice: (confidence_totals[choice] / counts[choice] if counts[choice] else 0)
        for choice in ("yes", "no")
    }
    result = {
        "debate_id": debate_id,
        "debate_dir": str(debate_dir),
        "ballots": len(ballots),
        "counts": counts,
        "average_confidence": average_confidence,
        "winner": winner,
    }
    if args.get("write_tally", True):
        tally_path = debate_dir / "tally.md"
        tally_path.write_text(render_tally_markdown(debate_id, debate_dir, ballots, result), encoding="utf-8")
        result["tally_path"] = str(tally_path)
    result["ballot_files"] = [str(path) for path, _ in ballots]
    return result


def tool_packet_validate(args: dict[str, Any]) -> dict[str, Any]:
    mod = packet_module()
    packet_type = str(args.get("packet_type") or args.get("type") or "auto")
    if packet_type not in PACKET_TYPES:
        raise ToolFailure(f"Unknown packet type: {packet_type}")
    results = []
    root = resolve_workspace_root(args.get("workspace_root")) if args.get("workspace_root") else None
    for index, text in enumerate(as_list(args.get("packet_texts") or args.get("packet_text"))):
        results.append(mod.lint_packet(text, packet_type=packet_type, source=f"<packet_text:{index}>"))
    for value in as_list(args.get("packet_paths") or args.get("packet")):
        path = workspace_path(root, value, "packet") if root else Path(value).expanduser().resolve()
        if not path.exists():
            raise ToolFailure(f"Packet file not found: {path}")
        results.append(mod.lint_packet(path.read_text(encoding="utf-8", errors="replace"), packet_type=packet_type, source=str(path)))
    if not results:
        raise ToolFailure("Provide packet_paths or packet_texts")
    strict = bool(args.get("strict", False))
    ok = all(result.get("ok") and (not strict or not result.get("warnings")) for result in results)
    return {"ok": ok, "strict": strict, "results": results}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_destination(directory: Path, name: str) -> Path:
    candidate = directory / name
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    for index in range(2, 10000):
        next_candidate = directory / f"{stem}-{index}{suffix}"
        if not next_candidate.exists():
            return next_candidate
    raise ToolFailure(f"Could not create unique artifact name for {name}")


def file_record(source: Path, stored: Path | None = None) -> dict[str, Any]:
    stat = source.stat()
    return {
        "source": str(source),
        "stored": str(stored) if stored else None,
        "kind": "file",
        "size": stat.st_size,
        "sha256": sha256_file(source),
    }


def directory_record(source: Path, stored: Path | None = None) -> dict[str, Any]:
    files = []
    for path in sorted(source.rglob("*")):
        if path.is_file():
            files.append({"path": str(path.relative_to(source)).replace("\\", "/"), "size": path.stat().st_size, "sha256": sha256_file(path)})
    return {"source": str(source), "stored": str(stored) if stored else None, "kind": "directory", "files": files}


def copy_artifact(source: Path, artifact_dir: Path) -> tuple[Path, dict[str, Any]]:
    destination = unique_destination(artifact_dir, source.name)
    if source.is_dir():
        shutil.copytree(source, destination)
        return destination, directory_record(source, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination, file_record(source, destination)


def tool_evidence_pack(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    title = str(args.get("title") or "evidence pack")
    case_id = slugify(str(args.get("case_id") or generated_id("evidence", title)), "evidence")
    pack_dir = ensure_within(root, root / "proof" / case_id, "evidence pack")
    if pack_dir.exists() and not args.get("force", False):
        raise ToolFailure(f"Evidence pack already exists: {pack_dir}")
    artifact_dir = pack_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    no_copy = bool(args.get("no_copy", False))
    artifact_records = []
    for value in as_list(args.get("artifacts") or args.get("artifact")):
        source = Path(value).expanduser()
        if not source.is_absolute():
            source = root / source
        source = source.resolve()
        if not source.exists():
            raise ToolFailure(f"Artifact not found: {source}")
        if no_copy:
            record = directory_record(source) if source.is_dir() else file_record(source)
        else:
            _, record = copy_artifact(source, artifact_dir)
        artifact_records.append(record)
    manifest = {
        "version": 1,
        "case_id": case_id,
        "title": title,
        "evidence_type": args.get("evidence_type") or args.get("type") or "generic",
        "created_at": utc_now(),
        "tool_versions": args.get("tool_versions") or {},
        "command_lines": as_list(args.get("command_lines") or args.get("commands") or args.get("command")),
        "export_settings": args.get("export_settings") or {},
        "related_findings": as_list(args.get("related_findings") or args.get("related")),
        "notes": str(args.get("notes") or ""),
        "artifacts": artifact_records,
    }
    manifest_path = pack_dir / "evidence-pack.json"
    write_json(manifest_path, manifest)
    return {"workspace_root": str(root), "pack_dir": str(pack_dir), "manifest_path": str(manifest_path), "manifest": manifest}


def require_items(args: dict[str, Any], key: str) -> list[str]:
    items = as_list(args.get(key))
    if not items:
        raise ToolFailure(f"Missing required field: {key}")
    return items


def tool_subagent_readiness(args: dict[str, Any]) -> dict[str, Any]:
    count = int(args.get("subagents") or 1)
    if count < 1 or count > 6:
        raise ToolFailure("subagents must be between 1 and 6")
    return run_helper_script("readiness", ["--subagents", str(count)], timeout=30)


def tool_debug_evidence(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    action = require_text(args, "action")
    argv = [action, "--root", str(root)]
    if action == "init":
        for key in ("tool", "target", "target_version", "scope", "environment"):
            require_text(args, key)
        for key in ("case_id", "tool", "tool_version", "version_command", "target", "target_version", "target_file", "scope", "environment", "command_line", "note", "timeout"):
            append_option(argv, key, args.get(key))
        append_many(argv, "env", args.get("env"))
        append_many(argv, "artifact", args.get("artifacts") or args.get("artifact"))
        append_flag(argv, "no_copy", args.get("no_copy"))
        append_flag(argv, "force", args.get("force"))
    elif action == "capture":
        argv.append(require_text(args, "case"))
        append_option(argv, "command", require_text(args, "command"))
        append_option(argv, "label", args.get("label"))
        append_many(argv, "env", args.get("env"))
        append_option(argv, "timeout", args.get("timeout"))
    elif action == "add-artifact":
        argv.append(require_text(args, "case"))
        require_items(args, "artifacts")
        append_many(argv, "artifact", args.get("artifacts"))
        append_option(argv, "category", args.get("category"))
        append_option(argv, "note", args.get("note"))
        append_flag(argv, "no_copy", args.get("no_copy"))
    elif action == "lint":
        argv.append(require_text(args, "case"))
        append_flag(argv, "strict", args.get("strict"))
    elif action == "summary":
        argv.append(require_text(args, "case"))
        argv.append("--json")
    else:
        raise ToolFailure(f"Unknown debug evidence action: {action}")
    result = run_helper_script("debug_evidence", argv, cwd=root, timeout=int(args.get("mcp_timeout_seconds") or 3600))
    result["workspace_root"] = str(root)
    return result


def tool_fuzz_campaign(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    action = require_text(args, "action")
    argv = [action, "--root", str(root)]
    if action == "init":
        for key in ("target", "target_version", "tool", "scope", "environment", "rate_limits", "instrumentation"):
            require_text(args, key)
        for key in ("campaign_id", "target", "target_version", "target_file", "tool", "tool_version", "version_command", "scope", "environment", "rate_limits", "instrumentation", "note"):
            append_option(argv, key, args.get(key))
        for key in ("command", "env", "build_flag", "sanitizer_flag", "harness", "grammar", "model", "artifact"):
            append_many(argv, key, args.get(f"{key}s") or args.get(key))
        append_many(argv, "schema", args.get("schemas") or args.get("schema"))
        append_many(argv, "request_template", args.get("request_templates") or args.get("request_template"))
        append_many(argv, "ui_script", args.get("ui_scripts") or args.get("ui_script"))
        append_many(argv, "seed_corpus", args.get("seed_corpora") or args.get("seed_corpus"))
        append_many(argv, "dictionary", args.get("dictionaries") or args.get("dictionary"))
        append_flag(argv, "no_copy", args.get("no_copy"))
        append_flag(argv, "force", args.get("force"))
    elif action == "add-run":
        argv.append(require_text(args, "campaign"))
        append_option(argv, "kind", args.get("kind"))
        append_option(argv, "command", args.get("command"))
        append_many(argv, "env", args.get("env"))
        append_option(argv, "exit_code", args.get("exit_code"))
        append_option(argv, "replay_command", args.get("replay_command"))
        for key in ("log", "artifact", "crash_input", "minimized_reproducer", "debugger_output", "sanitizer_report", "stack_trace", "core_dump", "screenshot", "api_request_sequence"):
            append_many(argv, key, args.get(f"{key}s") or args.get(key))
        append_option(argv, "auth_context", args.get("auth_context"))
        append_many(argv, "resource_id", args.get("resource_ids") or args.get("resource_id"))
        append_many(argv, "cleanup_action", args.get("cleanup_actions") or args.get("cleanup_action"))
        for key in ("invariant", "expected", "observed", "replay_stability", "note"):
            append_option(argv, key, args.get(key))
        append_flag(argv, "no_copy", args.get("no_copy"))
    elif action == "lint":
        argv.append(require_text(args, "campaign"))
        append_option(argv, "kind", args.get("kind"))
        append_flag(argv, "strict", args.get("strict"))
    elif action == "summary":
        argv.append(require_text(args, "campaign"))
        append_option(argv, "kind", args.get("kind"))
        argv.append("--json")
    else:
        raise ToolFailure(f"Unknown fuzz campaign action: {action}")
    result = run_helper_script("fuzz_campaign", argv, cwd=root, timeout=int(args.get("mcp_timeout_seconds") or 3600))
    result["workspace_root"] = str(root)
    return result


def tool_lpac_proof(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    action = require_text(args, "action")
    argv = [action, "--root", str(root)]
    if action == "init":
        for key in (
            "attack_scenario",
            "eligible_sandbox",
            "canary_build",
            "tool_used",
            "launch_command",
            "debugger_dependency",
            "build_instructions",
            "baseline_denied_operation",
            "exploit_success_operation",
            "finishing_privilege_or_data",
            "shipped_component",
            "vulnerability_path",
        ):
            require_text(args, key)
        for key in (
            "case_id",
            "attack_scenario",
            "eligible_sandbox",
            "sandbox_notes",
            "canary_build",
            "build_lab_ex",
            "date_tested",
            "sandbox_tools_repo",
            "sandbox_tools_commit",
            "tool_used",
            "launch_command",
            "debugger_dependency",
            "optional_debugger_steps",
            "build_instructions",
            "baseline_denied_operation",
            "exploit_success_operation",
            "finishing_privilege_or_data",
            "shipped_component",
            "vulnerability_path",
            "note",
        ):
            append_option(argv, key, args.get(key))
        append_flag(argv, "capture_windows_build", args.get("capture_windows_build"))
        append_boolean_optional(argv, "debugger_used", args.get("debugger_used"))
        append_many(argv, "pov_source", args.get("pov_source"))
        append_many(argv, "pov_binary", args.get("pov_binary"))
        append_many(argv, "artifact", args.get("artifacts") or args.get("artifact"))
        append_flag(argv, "no_copy", args.get("no_copy"))
        append_flag(argv, "force", args.get("force"))
    elif action == "capture":
        argv.append(require_text(args, "case"))
        append_option(argv, "command", require_text(args, "command"))
        append_option(argv, "label", args.get("label"))
        append_option(argv, "timeout", args.get("timeout"))
    elif action == "add-artifact":
        argv.append(require_text(args, "case"))
        append_option(argv, "category", require_text(args, "category"))
        require_items(args, "artifacts")
        append_many(argv, "artifact", args.get("artifacts"))
        append_option(argv, "note", args.get("note"))
        append_flag(argv, "no_copy", args.get("no_copy"))
    elif action == "lint":
        argv.append(require_text(args, "case"))
        append_flag(argv, "strict", args.get("strict"))
    elif action == "summary":
        argv.append(require_text(args, "case"))
        argv.append("--json")
    else:
        raise ToolFailure(f"Unknown LPAC proof action: {action}")
    result = run_helper_script("lpac_proof", argv, cwd=root, timeout=int(args.get("mcp_timeout_seconds") or 3600))
    result["workspace_root"] = str(root)
    return result


def tool_ipsw_provenance(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root"))
    action = require_text(args, "action")
    argv = [action, "--root", str(root)]
    if action == "init":
        for key in ("device", "product_version", "build", "firmware_source", "restore_identity", "architecture"):
            require_text(args, key)
        for key in (
            "case_id",
            "device",
            "model",
            "board",
            "product_version",
            "build",
            "firmware_source",
            "firmware_sha256",
            "restore_identity",
            "architecture",
            "artifact_type",
            "ipsw",
            "ipsw_version",
            "fact_source",
            "note",
        ):
            append_option(argv, key, args.get(key))
        append_many(argv, "command", args.get("commands") or args.get("command"))
        append_many(argv, "artifact", args.get("artifacts") or args.get("artifact"))
        append_flag(argv, "no_copy", args.get("no_copy"))
        append_flag(argv, "force", args.get("force"))
    elif action == "record-command":
        argv.append(require_text(args, "case"))
        append_option(argv, "command", require_text(args, "command"))
        append_option(argv, "fact_source", require_text(args, "fact_source"))
        append_flag(argv, "capture", args.get("capture"))
        append_option(argv, "label", args.get("label"))
        append_option(argv, "timeout", args.get("timeout"))
    elif action == "add-artifact":
        argv.append(require_text(args, "case"))
        require_items(args, "artifacts")
        append_many(argv, "artifact", args.get("artifacts"))
        append_option(argv, "category", require_text(args, "category"))
        append_option(argv, "fact_source", require_text(args, "fact_source"))
        append_option(argv, "command", args.get("command"))
        append_option(argv, "note", args.get("note"))
        append_flag(argv, "no_copy", args.get("no_copy"))
    elif action == "lint":
        argv.append(require_text(args, "case"))
        append_flag(argv, "strict", args.get("strict"))
    elif action == "summary":
        argv.append(require_text(args, "case"))
        argv.append("--json")
    else:
        raise ToolFailure(f"Unknown IPSW provenance action: {action}")
    result = run_helper_script("ipsw_provenance", argv, cwd=root, timeout=int(args.get("mcp_timeout_seconds") or 3600))
    result["workspace_root"] = str(root)
    return result


def tool_re_readiness_check(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root")) if args.get("workspace_root") else PLUGIN_ROOT
    argv: list[str] = []
    append_many(argv, "tool", args.get("tools") or args.get("tool"))
    append_many(argv, "target", args.get("targets") or args.get("target"))
    for key in ("output", "ghidra_home", "java", "r2", "rabin2", "rahash2", "rafind2", "radiff2", "jadx", "jadx_gui"):
        append_option(argv, key, args.get(key))
    argv.append("--json")
    result = run_helper_script("re_readiness", argv, cwd=root, timeout=int(args.get("mcp_timeout_seconds") or 120))
    if args.get("output"):
        output_path = Path(str(args["output"])).expanduser()
        if not output_path.is_absolute():
            output_path = root / output_path
        if output_path.exists():
            try:
                result["output_json"] = json.loads(output_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                result["output_text"] = output_path.read_text(encoding="utf-8", errors="replace")
    result["workspace_root"] = str(root)
    return result


def tool_ghidra_export(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root")) if args.get("workspace_root") else PLUGIN_ROOT
    argv = [require_text(args, "input")]
    for key in ("output_dir", "project_dir"):
        append_option(argv, key, require_text(args, key))
    for key in ("project_name", "ghidra_home", "analyze_headless", "processor", "compiler", "loader", "analysis_timeout", "log", "script_log", "timeout"):
        append_option(argv, key, args.get(key))
    for key in ("loader_arg", "script_path", "pre_script", "post_script", "extra_arg"):
        append_many(argv, key, args.get(f"{key}s") or args.get(key))
    for key in ("no_analysis", "overwrite", "read_only", "run"):
        append_flag(argv, key, args.get(key))
    argv.append("--json")
    wait = int(args.get("timeout") or 3600) + 60
    result = run_helper_script("ghidra_export", argv, cwd=root, timeout=int(args.get("mcp_timeout_seconds") or wait))
    result["workspace_root"] = str(root)
    return result


def tool_jadx_export(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root")) if args.get("workspace_root") else PLUGIN_ROOT
    argv = [require_text(args, "input")]
    append_option(argv, "output_dir", require_text(args, "output_dir"))
    for key in ("jadx", "mode", "export_gradle_type", "timeout", "hash_limit"):
        append_option(argv, key, args.get(key))
    append_many(argv, "plugin_option", args.get("plugin_options") or args.get("plugin_option"))
    append_many(argv, "extra_arg", args.get("extra_args") or args.get("extra_arg"))
    for key in ("deobf", "show_bad_code", "cfg", "export_gradle", "run"):
        append_flag(argv, key, args.get(key))
    argv.append("--json")
    wait = int(args.get("timeout") or 3600) + 60
    result = run_helper_script("jadx_export", argv, cwd=root, timeout=int(args.get("mcp_timeout_seconds") or wait))
    result["workspace_root"] = str(root)
    return result


def tool_r2_triage(args: dict[str, Any]) -> dict[str, Any]:
    root = resolve_workspace_root(args.get("workspace_root")) if args.get("workspace_root") else PLUGIN_ROOT
    argv = [require_text(args, "target")]
    append_option(argv, "output_dir", require_text(args, "output_dir"))
    for key in ("r2", "rabin2", "rahash2", "timeout"):
        append_option(argv, key, args.get(key))
    append_flag(argv, "skip_r2", args.get("skip_r2"))
    append_flag(argv, "deep", args.get("deep"))
    argv.append("--json")
    wait = int(args.get("timeout") or 120) + 60
    result = run_helper_script("r2_triage", argv, cwd=root, timeout=int(args.get("mcp_timeout_seconds") or wait))
    result["workspace_root"] = str(root)
    return result


def schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required or [], "additionalProperties": False}


TOOLS: dict[str, dict[str, Any]] = {
    "ledger_init": {
        "description": "Initialize MaxTAC primitive and/or chain ledgers in a workspace.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string", "description": "Workspace root; defaults to the server working directory."},
                "type": {"type": "string", "enum": list(LEDGER_TYPES), "default": "all"},
                "file": {"type": "string", "description": "Optional ledger file override inside the workspace."},
                "force": {"type": "boolean", "default": False},
            }
        ),
        "handler": tool_ledger_init,
    },
    "ledger_search": {
        "description": "Search MaxTAC ledgers for likely matching findings.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "type": {"type": "string", "enum": list(LEDGER_TYPES), "default": "all"},
                "file": {"type": "string"},
                "title": {"type": "string"},
                "target": {"type": "string"},
                "category": {"type": "string"},
                "locations": {"type": "array", "items": {"type": "string"}},
                "evidence": {"type": "string"},
                "related": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "minimum": 1, "default": 10},
            }
        ),
        "handler": tool_ledger_search,
    },
    "ledger_add": {
        "description": "Add a primitive or chain finding to a MaxTAC ledger after duplicate search.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "type": {"type": "string", "enum": ["primitive", "chain"], "default": "primitive"},
                "file": {"type": "string"},
                "title": {"type": "string"},
                "target": {"type": "string"},
                "category": {"type": "string"},
                "locations": {"type": "array", "items": {"type": "string"}},
                "summary": {"type": "string"},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "related": {"type": "array", "items": {"type": "string"}},
                "primitives": {"type": "array", "items": {"type": "string"}},
                "state": {"type": "string", "enum": list(STATES), "default": "discovered"},
                "allow_duplicate": {"type": "boolean", "default": False},
                "note": {"type": "string"},
            },
            ["title", "target", "category", "summary", "evidence"],
        ),
        "handler": tool_ledger_add,
    },
    "ledger_update": {
        "description": "Update a MaxTAC finding by id in primitive or chain ledgers.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "type": {"type": "string", "enum": list(LEDGER_TYPES), "default": "all"},
                "file": {"type": "string"},
                "finding_id": {"type": "string"},
                "state": {"type": "string", "enum": list(STATES)},
                "title": {"type": "string"},
                "target": {"type": "string"},
                "category": {"type": "string"},
                "locations": {"type": "array", "items": {"type": "string"}},
                "summary": {"type": "string"},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "related": {"type": "array", "items": {"type": "string"}},
                "primitives": {"type": "array", "items": {"type": "string"}},
                "note": {"type": "string"},
            },
            ["finding_id"],
        ),
        "handler": tool_ledger_update,
    },
    "ledger_summary": {
        "description": "Summarize primitive and/or chain ledgers with state counts and active findings.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "type": {"type": "string", "enum": list(LEDGER_TYPES), "default": "all"},
                "file": {"type": "string"},
            }
        ),
        "handler": tool_ledger_summary,
    },
    "ledger_list": {
        "description": "List MaxTAC findings from primitive and/or chain ledgers, optionally filtered by state.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "type": {"type": "string", "enum": list(LEDGER_TYPES), "default": "all"},
                "file": {"type": "string"},
                "state": {"type": "string", "enum": list(STATES)},
                "limit": {"type": "integer", "minimum": 0, "default": 0},
            }
        ),
        "handler": tool_ledger_list,
    },
    "ledger_milestone": {
        "description": "Append a timestamped milestone note to a MaxTAC primitive or chain finding.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "type": {"type": "string", "enum": list(LEDGER_TYPES), "default": "all"},
                "file": {"type": "string"},
                "finding_id": {"type": "string"},
                "note": {"type": "string"},
            },
            ["finding_id", "note"],
        ),
        "handler": tool_ledger_milestone,
    },
    "workspace_init": {
        "description": "Initialize canonical MaxTAC workspace directories, ledgers, program info, and phase state.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "phase": {"type": "string", "enum": list(PHASES), "default": "prepare"},
                "note": {"type": "string"},
                "no_program_info": {"type": "boolean", "default": False},
                "force_program_info": {"type": "boolean", "default": False},
                "force_ledgers": {"type": "boolean", "default": False},
                "force_state": {"type": "boolean", "default": False},
            }
        ),
        "handler": tool_workspace_init,
    },
    "workspace_status": {
        "description": "Inspect MaxTAC workspace health, phase state, ledger counts, large markdown files, and report readiness.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "chain": {"type": "string"},
                "max_lines": {"type": "integer", "minimum": 1, "default": 300},
            }
        ),
        "handler": tool_workspace_status,
    },
    "workspace_phase": {
        "description": "Show, list, or update the current MaxTAC workflow phase with transition validation.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "phase": {"type": "string", "enum": list(PHASES)},
                "list": {"type": "boolean", "default": False},
                "force": {"type": "boolean", "default": False},
                "note": {"type": "string"},
            }
        ),
        "handler": tool_workspace_phase,
    },
    "workspace_new_submodule": {
        "description": "Create a research submodule under research/ with optional artifacts/ and subsystem markdown files.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "name": {"type": "string"},
                "parent": {"type": "string"},
                "markdown": {"type": "array", "items": {"type": "string"}},
                "title": {"type": "string"},
                "no_artifacts": {"type": "boolean", "default": False},
                "force": {"type": "boolean", "default": False},
                "overwrite": {"type": "boolean", "default": False},
            },
            ["name"],
        ),
        "handler": tool_workspace_new_submodule,
    },
    "workspace_split_large_markdown": {
        "description": "Split an oversized research markdown file into a submodule and write a split manifest.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "markdown_file": {"type": "string"},
                "submodule": {"type": "string"},
                "large_threshold": {"type": "integer", "minimum": 1, "default": 300},
                "max_lines": {"type": "integer", "minimum": 1, "default": 220},
                "copy_artifact": {"type": "array", "items": {"type": "string"}},
                "delete_source": {"type": "boolean", "default": False},
                "delete_artifacts": {"type": "boolean", "default": False},
                "verified": {"type": "boolean", "default": False},
                "force": {"type": "boolean", "default": False},
            },
            ["markdown_file"],
        ),
        "handler": tool_workspace_split_large_markdown,
    },
    "workspace_report_ready": {
        "description": "Check whether selected proofed chains have the required scope, ledger, proof, phase, and report evidence.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "chain": {"type": "string"},
                "require_report_file": {"type": "boolean", "default": False},
            }
        ),
        "handler": tool_workspace_report_ready,
    },
    "audit_prompt_create": {
        "description": "Create and persist a goal-bounded MaxTAC auditor prompt under audits/<audit-id>/.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "prompt_text": {"type": "string"},
                "prompt_file": {"type": "string", "description": "Prompt draft path inside the workspace; normally under tmp/."},
                "focus": {"type": "string"},
                "auditor": {"type": "string"},
                "auditor_filters": {"type": "array", "items": {"type": "string"}},
                "packet_paths": {"type": "array", "items": {"type": "string"}},
                "packet_type": {"type": "string", "enum": list(PACKET_TYPES), "default": "auto"},
                "allow_invalid_packets": {"type": "boolean", "default": False},
            }
        ),
        "handler": tool_audit_prompt_create,
    },
    "debate_prompt_create": {
        "description": "Create and persist a goal-bounded MaxTAC binary debate prompt under debates/<debate-id>/.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "prompt_text": {"type": "string"},
                "prompt_file": {"type": "string", "description": "Prompt draft path inside the workspace; normally under tmp/."},
                "proposition": {"type": "string"},
                "yes_means": {"type": "string"},
                "no_means": {"type": "string"},
                "context": {"type": "string"},
            }
        ),
        "handler": tool_debate_prompt_create,
    },
    "debate_tally": {
        "description": "Validate debate ballots, tally yes/no votes, and write debates/<debate-id>/tally.md.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "debate_id": {"type": "string"},
                "write_tally": {"type": "boolean", "default": True},
            },
            ["debate_id"],
        ),
        "handler": tool_debate_tally,
    },
    "subagent_readiness": {
        "description": "Check whether the requested number of MaxTAC subagents should run in parallel or sequentially.",
        "inputSchema": schema(
            {
                "subagents": {"type": "integer", "minimum": 1, "maximum": 6},
            },
            ["subagents"],
        ),
        "handler": tool_subagent_readiness,
    },
    "packet_validate": {
        "description": "Validate MaxTAC SAST surface, CFG, or OpenGrep packets and return lint results.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "packet_paths": {"type": "array", "items": {"type": "string"}},
                "packet_texts": {"type": "array", "items": {"type": "string"}},
                "packet_type": {"type": "string", "enum": list(PACKET_TYPES), "default": "auto"},
                "strict": {"type": "boolean", "default": False},
            }
        ),
        "handler": tool_packet_validate,
    },
    "evidence_pack": {
        "description": "Create a generic MaxTAC proof evidence pack with artifact copies, SHA-256 hashes, commands, tool versions, and export settings.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "case_id": {"type": "string"},
                "title": {"type": "string"},
                "evidence_type": {"type": "string"},
                "artifacts": {"type": "array", "items": {"type": "string"}},
                "tool_versions": {"type": "object"},
                "command_lines": {"type": "array", "items": {"type": "string"}},
                "export_settings": {"type": "object"},
                "related_findings": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string"},
                "no_copy": {"type": "boolean", "default": False},
                "force": {"type": "boolean", "default": False},
            }
        ),
        "handler": tool_evidence_pack,
    },
    "debug_evidence": {
        "description": "Run the debugger/runtime evidence helper actions: init, capture, add-artifact, lint, or summary.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "action": {"type": "string", "enum": ["init", "capture", "add-artifact", "lint", "summary"]},
                "case": {"type": "string"},
                "case_id": {"type": "string"},
                "tool": {"type": "string"},
                "tool_version": {"type": "string"},
                "version_command": {"type": "string"},
                "target": {"type": "string"},
                "target_version": {"type": "string"},
                "target_file": {"type": "string"},
                "scope": {"type": "string"},
                "environment": {"type": "string"},
                "command_line": {"type": "string"},
                "command": {"type": "string"},
                "label": {"type": "string"},
                "env": {"type": "array", "items": {"type": "string"}},
                "artifacts": {"type": "array", "items": {"type": "string"}},
                "category": {"type": "string"},
                "note": {"type": "string"},
                "timeout": {"type": "integer", "minimum": 1},
                "strict": {"type": "boolean", "default": False},
                "no_copy": {"type": "boolean", "default": False},
                "force": {"type": "boolean", "default": False},
                "mcp_timeout_seconds": {"type": "integer", "minimum": 1},
            },
            ["action"],
        ),
        "handler": tool_debug_evidence,
    },
    "fuzz_campaign": {
        "description": "Run the fuzz campaign evidence helper actions: init, add-run, lint, or summary.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "action": {"type": "string", "enum": ["init", "add-run", "lint", "summary"]},
                "campaign": {"type": "string"},
                "campaign_id": {"type": "string"},
                "target": {"type": "string"},
                "target_version": {"type": "string"},
                "target_file": {"type": "string"},
                "tool": {"type": "string"},
                "tool_version": {"type": "string"},
                "version_command": {"type": "string"},
                "scope": {"type": "string"},
                "environment": {"type": "string"},
                "rate_limits": {"type": "string"},
                "instrumentation": {"type": "string"},
                "commands": {"type": "array", "items": {"type": "string"}},
                "command": {"type": "string"},
                "env": {"type": "array", "items": {"type": "string"}},
                "build_flags": {"type": "array", "items": {"type": "string"}},
                "sanitizer_flags": {"type": "array", "items": {"type": "string"}},
                "harnesses": {"type": "array", "items": {"type": "string"}},
                "grammars": {"type": "array", "items": {"type": "string"}},
                "schemas": {"type": "array", "items": {"type": "string"}},
                "models": {"type": "array", "items": {"type": "string"}},
                "request_templates": {"type": "array", "items": {"type": "string"}},
                "ui_scripts": {"type": "array", "items": {"type": "string"}},
                "seed_corpora": {"type": "array", "items": {"type": "string"}},
                "dictionaries": {"type": "array", "items": {"type": "string"}},
                "artifacts": {"type": "array", "items": {"type": "string"}},
                "kind": {"type": "string", "enum": ["campaign", "crash", "api", "logic"]},
                "exit_code": {"type": "integer"},
                "replay_command": {"type": "string"},
                "logs": {"type": "array", "items": {"type": "string"}},
                "crash_inputs": {"type": "array", "items": {"type": "string"}},
                "minimized_reproducers": {"type": "array", "items": {"type": "string"}},
                "debugger_outputs": {"type": "array", "items": {"type": "string"}},
                "sanitizer_reports": {"type": "array", "items": {"type": "string"}},
                "stack_traces": {"type": "array", "items": {"type": "string"}},
                "core_dumps": {"type": "array", "items": {"type": "string"}},
                "screenshots": {"type": "array", "items": {"type": "string"}},
                "api_request_sequences": {"type": "array", "items": {"type": "string"}},
                "auth_context": {"type": "string"},
                "resource_ids": {"type": "array", "items": {"type": "string"}},
                "cleanup_actions": {"type": "array", "items": {"type": "string"}},
                "invariant": {"type": "string"},
                "expected": {"type": "string"},
                "observed": {"type": "string"},
                "replay_stability": {"type": "string"},
                "note": {"type": "string"},
                "strict": {"type": "boolean", "default": False},
                "no_copy": {"type": "boolean", "default": False},
                "force": {"type": "boolean", "default": False},
                "mcp_timeout_seconds": {"type": "integer", "minimum": 1},
            },
            ["action"],
        ),
        "handler": tool_fuzz_campaign,
    },
    "lpac_proof": {
        "description": "Run the MSRC LPAC proof evidence helper actions: init, capture, add-artifact, lint, or summary.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "action": {"type": "string", "enum": ["init", "capture", "add-artifact", "lint", "summary"]},
                "case": {"type": "string"},
                "case_id": {"type": "string"},
                "attack_scenario": {"type": "string", "enum": ["sandbox-escape", "private-data-access"]},
                "eligible_sandbox": {"type": "string"},
                "sandbox_notes": {"type": "string"},
                "canary_build": {"type": "string"},
                "build_lab_ex": {"type": "string"},
                "capture_windows_build": {"type": "boolean", "default": False},
                "date_tested": {"type": "string"},
                "sandbox_tools_repo": {"type": "string"},
                "sandbox_tools_commit": {"type": "string"},
                "tool_used": {"type": "string"},
                "launch_command": {"type": "string"},
                "debugger_used": {"type": "boolean"},
                "debugger_dependency": {"type": "string", "enum": ["none", "optional", "required"]},
                "optional_debugger_steps": {"type": "string"},
                "pov_source": {"type": "array", "items": {"type": "string"}},
                "pov_binary": {"type": "array", "items": {"type": "string"}},
                "build_instructions": {"type": "string"},
                "baseline_denied_operation": {"type": "string"},
                "exploit_success_operation": {"type": "string"},
                "finishing_privilege_or_data": {"type": "string"},
                "shipped_component": {"type": "string"},
                "vulnerability_path": {"type": "string"},
                "artifacts": {"type": "array", "items": {"type": "string"}},
                "category": {"type": "string"},
                "command": {"type": "string"},
                "label": {"type": "string"},
                "timeout": {"type": "integer", "minimum": 1},
                "note": {"type": "string"},
                "strict": {"type": "boolean", "default": False},
                "no_copy": {"type": "boolean", "default": False},
                "force": {"type": "boolean", "default": False},
                "mcp_timeout_seconds": {"type": "integer", "minimum": 1},
            },
            ["action"],
        ),
        "handler": tool_lpac_proof,
    },
    "ipsw_provenance": {
        "description": "Run the ASB IPSW provenance helper actions: init, record-command, add-artifact, lint, or summary.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "action": {"type": "string", "enum": ["init", "record-command", "add-artifact", "lint", "summary"]},
                "case": {"type": "string"},
                "case_id": {"type": "string"},
                "device": {"type": "string"},
                "model": {"type": "string"},
                "board": {"type": "string"},
                "product_version": {"type": "string"},
                "build": {"type": "string"},
                "firmware_source": {"type": "string"},
                "firmware_sha256": {"type": "string"},
                "restore_identity": {"type": "string"},
                "architecture": {"type": "string"},
                "artifact_type": {"type": "string"},
                "ipsw": {"type": "string"},
                "ipsw_version": {"type": "string"},
                "commands": {"type": "array", "items": {"type": "string"}},
                "command": {"type": "string"},
                "fact_source": {"type": "string", "enum": ["archive-metadata", "extracted-file", "reconstructed-macho", "later-re-tooling", "diff-output", "runtime-device", "other"]},
                "artifacts": {"type": "array", "items": {"type": "string"}},
                "category": {"type": "string"},
                "capture": {"type": "boolean", "default": False},
                "label": {"type": "string"},
                "timeout": {"type": "integer", "minimum": 1},
                "note": {"type": "string"},
                "strict": {"type": "boolean", "default": False},
                "no_copy": {"type": "boolean", "default": False},
                "force": {"type": "boolean", "default": False},
                "mcp_timeout_seconds": {"type": "integer", "minimum": 1},
            },
            ["action"],
        ),
        "handler": tool_ipsw_provenance,
    },
    "re_readiness_check": {
        "description": "Run the generic reverse-engineering readiness helper for Ghidra, radare2, and/or JADX.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "tools": {"type": "array", "items": {"type": "string", "enum": ["all", "ghidra", "radare2", "jadx"]}},
                "targets": {"type": "array", "items": {"type": "string"}},
                "output": {"type": "string"},
                "ghidra_home": {"type": "string"},
                "java": {"type": "string"},
                "r2": {"type": "string"},
                "rabin2": {"type": "string"},
                "rahash2": {"type": "string"},
                "rafind2": {"type": "string"},
                "radiff2": {"type": "string"},
                "jadx": {"type": "string"},
                "jadx_gui": {"type": "string"},
                "mcp_timeout_seconds": {"type": "integer", "minimum": 1},
            }
        ),
        "handler": tool_re_readiness_check,
    },
    "ghidra_export": {
        "description": "Plan or run a Ghidra analyzeHeadless export and return the generated evidence manifest.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "input": {"type": "string"},
                "output_dir": {"type": "string"},
                "project_dir": {"type": "string"},
                "project_name": {"type": "string"},
                "ghidra_home": {"type": "string"},
                "analyze_headless": {"type": "string"},
                "processor": {"type": "string"},
                "compiler": {"type": "string"},
                "loader": {"type": "string"},
                "loader_args": {"type": "array", "items": {"type": "string"}},
                "analysis_timeout": {"type": "integer", "minimum": 1},
                "script_paths": {"type": "array", "items": {"type": "string"}},
                "pre_scripts": {"type": "array", "items": {"type": "string"}},
                "post_scripts": {"type": "array", "items": {"type": "string"}},
                "extra_args": {"type": "array", "items": {"type": "string"}},
                "no_analysis": {"type": "boolean", "default": False},
                "overwrite": {"type": "boolean", "default": False},
                "read_only": {"type": "boolean", "default": False},
                "log": {"type": "string"},
                "script_log": {"type": "string"},
                "run": {"type": "boolean", "default": False},
                "timeout": {"type": "integer", "minimum": 1, "default": 3600},
                "mcp_timeout_seconds": {"type": "integer", "minimum": 1},
            },
            ["input", "output_dir", "project_dir"],
        ),
        "handler": tool_ghidra_export,
    },
    "jadx_export": {
        "description": "Plan or run a JADX export and return the generated evidence manifest.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "input": {"type": "string"},
                "output_dir": {"type": "string"},
                "jadx": {"type": "string"},
                "mode": {"type": "string", "enum": ["all", "sources", "resources"], "default": "all"},
                "deobf": {"type": "boolean", "default": False},
                "show_bad_code": {"type": "boolean", "default": False},
                "cfg": {"type": "boolean", "default": False},
                "export_gradle": {"type": "boolean", "default": False},
                "export_gradle_type": {"type": "string", "enum": ["auto", "android-app", "android-library", "simple-java"]},
                "plugin_options": {"type": "array", "items": {"type": "string"}},
                "extra_args": {"type": "array", "items": {"type": "string"}},
                "run": {"type": "boolean", "default": False},
                "timeout": {"type": "integer", "minimum": 1, "default": 3600},
                "hash_limit": {"type": "integer", "minimum": 1, "default": 500},
                "mcp_timeout_seconds": {"type": "integer", "minimum": 1},
            },
            ["input", "output_dir"],
        ),
        "handler": tool_jadx_export,
    },
    "r2_triage": {
        "description": "Collect repeatable radare2/rabin2/rahash2 binary triage evidence and return the manifest.",
        "inputSchema": schema(
            {
                "workspace_root": {"type": "string"},
                "target": {"type": "string"},
                "output_dir": {"type": "string"},
                "r2": {"type": "string"},
                "rabin2": {"type": "string"},
                "rahash2": {"type": "string"},
                "skip_r2": {"type": "boolean", "default": False},
                "deep": {"type": "boolean", "default": False},
                "timeout": {"type": "integer", "minimum": 1, "default": 120},
                "mcp_timeout_seconds": {"type": "integer", "minimum": 1},
            },
            ["target", "output_dir"],
        ),
        "handler": tool_r2_triage,
    },
}


def tool_descriptions() -> list[dict[str, Any]]:
    result = []
    for name, spec in TOOLS.items():
        result.append({"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]})
    return result


def response(message_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def error_response(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def tool_response(payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    return {"isError": is_error, "content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    message_id = message.get("id")
    params = message.get("params") or {}
    if method == "initialize":
        return response(
            message_id,
            {
                "protocolVersion": params.get("protocolVersion") or "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "maxtac", "version": "0.1.0"},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return response(message_id, {})
    if method == "tools/list":
        return response(message_id, {"tools": tool_descriptions()})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name not in TOOLS:
            return response(message_id, tool_response({"error": f"Unknown tool: {name}"}, is_error=True))
        if not isinstance(arguments, dict):
            return response(message_id, tool_response({"error": "Tool arguments must be an object"}, is_error=True))
        try:
            payload = TOOLS[name]["handler"](arguments)
            return response(message_id, tool_response(payload))
        except ToolFailure as exc:
            error_payload = exc.payload or {"error": str(exc)}
            if "error" not in error_payload:
                error_payload = {"error": str(exc), **error_payload}
            return response(message_id, tool_response(error_payload, is_error=True))
        except SystemExit as exc:
            return response(message_id, tool_response({"error": str(exc)}, is_error=True))
        except Exception as exc:  # noqa: BLE001 - MCP server must return tool errors, not crash.
            return response(message_id, tool_response({"error": f"{type(exc).__name__}: {exc}"}, is_error=True))
    if message_id is None:
        return None
    return error_response(message_id, -32601, f"Method not found: {method}")


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            outgoing = error_response(None, -32700, f"Parse error: {exc}")
        else:
            if not isinstance(message, dict):
                outgoing = error_response(None, -32600, "Invalid request")
            else:
                outgoing = handle_request(message)
        if outgoing is not None:
            sys.stdout.write(json.dumps(outgoing, separators=(",", ":")) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
