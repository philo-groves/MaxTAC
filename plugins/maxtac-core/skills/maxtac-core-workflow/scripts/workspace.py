#!/usr/bin/env python3
"""Initialize and inspect MaxTAC research workspaces."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REFERENCES_DIR = SKILL_DIR / "references"
PROGRAM_INFO_TEMPLATE = REFERENCES_DIR / "program-info.template.md"
SUBSYSTEM_TEMPLATE = REFERENCES_DIR / "subsystem.template.md"
LEDGER_SCRIPTS_DIR = SKILL_DIR.parent / "maxtac-core-ledger" / "scripts"
sys.path.insert(0, str(LEDGER_SCRIPTS_DIR))

import workspace_db  # noqa: E402

STATE_FILE = ".maxtac-workspace.json"
WORKSPACE_FILES = {
    "program-info.md": "authorized scope and exclusions",
    workspace_db.DB_FILE: "SQLite findings, corpus notes, model assertions, debate tallies, audit index, and search memory",
}
WORKSPACE_DIRS = {
    "research": "scalable markdown research library",
    "research/notes": "canonical faceted corpus notes",
    "research/views": "generated corpus indexes and graph views",
    "research/artifacts": "raw corpus artifacts and imported legacy markdown",
    "models": "machine-readable security models and invariant dictionaries",
    "proof": "proof-of-vulnerability development",
    "fuzz": "fuzzing inputs, scripts, and artifacts",
    "tmp": "temporary files that can be deleted between sessions",
    "contracts": "canonical result contracts and coverage bundles",
    "reporting": "submission-ready reports and evidence indexes",
}
LEDGER_TYPES = workspace_db.TYPE_CHOICES
LEGACY_LEDGER_FILES = workspace_db.LEGACY_LEDGER_FILES
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
PHASE_TRANSITIONS = {
    "prepare": {"scan"},
    "scan": {"prepare", "validation"},
    "validation": {"scan", "primitive-proof"},
    "primitive-proof": {"scan", "validation", "chain-proof"},
    "chain-proof": {"scan", "primitive-proof", "reporting"},
    "reporting": {"scan", "chain-proof"},
}
TERMINAL_STATES = {"duplicate", "de-escalated"}
LARGE_MARKDOWN_LINES = 300
SPLIT_TARGET_LINES = 220
PLACEHOLDER_RE = re.compile(r"\[[^\]\n]+\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
TOOL_DIRECTORY_NAMES = {
    "adb",
    "frida",
    "ghidra",
    "ipsw",
    "jadx",
    "lldb",
    "opengrep",
    "r2",
    "radare2",
}
ATTENTION_WINDOW_MINUTES = 90
ATTENTION_FILE_COUNT = 40
ATTENTION_PHASE_REVIEW_MINUTES = 120
ATTENTION_LEDGER_REVIEW_MINUTES = 90
ATTENTION_DOMINANCE_RATIO = 0.7
ATTENTION_MIN_RESEARCH_FILES = 8
ATTENTION_TOP_LEVEL_DIRS = (
    "research",
    "models",
    "proof",
    "fuzz",
    "tmp",
    "reporting",
)
ATTENTION_EVIDENCE_TOP_LEVEL_DIRS = {
    "proof",
    "fuzz",
    "tmp",
}
ATTENTION_TRACKED_SUFFIXES = {
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".json",
    ".log",
    ".m",
    ".md",
    ".mmd",
    ".mm",
    ".opengrep",
    ".plist",
    ".py",
    ".rule",
    ".rules",
    ".semgrep",
    ".sh",
    ".swift",
    ".txt",
    ".yaml",
    ".yml",
}
ATTENTION_PRUNE_DIRS = {
    ".build",
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "deriveddata",
    "node_modules",
    "products",
    "venv",
}
ATTENTION_ARTIFACT_DIR_NAMES = {
    "artifact",
    "artifacts",
    "captures",
    "extract",
    "extracted",
    "generated",
    "log",
    "logs",
    "output",
    "outputs",
    "packets",
    "raw",
    "screenshots",
    "traces",
}
ATTENTION_DECISION_OPTIONS = (
    "deepen",
    "pivot",
    "consolidate",
    "phase-shift",
    "delegate-review",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def root_path(value: str | None) -> Path:
    root = Path(value or ".").expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Workspace root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Workspace root is not a directory: {root}")
    return root


def relative_to(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def ensure_within(root: Path, path: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise SystemExit(f"{label} escapes workspace root: {resolved_path}") from exc
    return resolved_path


def workspace_path(root: Path, value: str | Path, label: str = "path") -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return ensure_within(root, path, label)


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_template(path: Path, fallback: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return fallback


def slugify(value: str, default: str = "submodule") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or default


def markdown_name(value: str) -> str:
    path = Path(value)
    name = slugify(path.stem, "subsystem") + ".md"
    return name


def normalize_phase(value: str) -> str:
    key = value.strip().lower().replace("_", "-").replace(" ", "-")
    key = PHASE_ALIASES.get(key, key)
    if key not in PHASES:
        choices = ", ".join(PHASES)
        raise SystemExit(f"Unknown phase: {value}. Expected one of: {choices}")
    return key


def load_state(root: Path) -> dict[str, Any] | None:
    path = root / STATE_FILE
    if not path.exists():
        return None
    state = read_json(path)
    phase = state.get("current_phase", "prepare")
    state["current_phase"] = normalize_phase(str(phase))
    history = state.setdefault("phase_history", [])
    if not isinstance(history, list):
        raise SystemExit(f"{path} has invalid phase_history")
    state.setdefault("version", 1)
    return state


def save_state(root: Path, state: dict[str, Any]) -> None:
    write_json(root / STATE_FILE, state)


def initial_state(phase: str = "prepare", note: str = "Workspace initialized.") -> dict[str, Any]:
    timestamp = now()
    return {
        "version": 1,
        "current_phase": phase,
        "phase_history": [
            {
                "time": timestamp,
                "from": None,
                "to": phase,
                "note": note,
            }
        ],
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def create_ledger(root: Path, ledger_type: str, *, force: bool = False) -> str:
    result = workspace_db.initialize_workspace_db(root)
    count = workspace_db.count_findings(root, ledger_type)
    if force:
        workspace_db.save_ledger(root, ledger_type, {"version": 2, "type": ledger_type, "findings": []})
        return "reset"
    imported = result.imported.get(ledger_type, 0)
    if imported:
        return f"migrated {imported} legacy finding(s)"
    if count:
        return "exists"
    return "created" if result.created else "exists"


def load_ledger(root: Path, ledger_type: str) -> tuple[Path, dict[str, Any] | None, str | None]:
    path = root / workspace_db.DB_FILE
    if not path.exists() and not any((root / legacy_path).exists() for legacy_path in LEGACY_LEDGER_FILES.values()):
        return path, None, "missing"
    try:
        payload = workspace_db.load_ledger(root, ledger_type)
    except SystemExit as exc:
        return path, None, str(exc)
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return path, None, "invalid findings list"
    return path, payload, None


def ledger_counts(ledger: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in ledger.get("findings", []):
        state = str(finding.get("state", "unknown"))
        counts[state] = counts.get(state, 0) + 1
    return counts


def workspace_memory_counts(root: Path) -> dict[str, Any] | None:
    if not (root / workspace_db.DB_FILE).exists():
        return None
    try:
        return {
            "corpus_documents": workspace_db.count_corpus_documents(root),
            "corpus_edges": workspace_db.count_corpus_edges(root),
            "models": workspace_db.count_models(root),
            "debates": workspace_db.count_debates(root),
            "audits": workspace_db.count_audits(root),
        }
    except Exception as exc:
        return {"error": str(exc)}


def finding_state_counts(root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for ledger_type in LEDGER_TYPES:
        _, ledger, error = load_ledger(root, ledger_type)
        if error or ledger is None:
            continue
        for finding in ledger.get("findings", []):
            counts[str(finding.get("state", "unknown"))] += 1
    return counts


def phase_rank(phase: str | None) -> int:
    if phase in PHASES:
        return PHASES.index(str(phase))
    return -1


def phase_guidance(root: Path, state: dict[str, Any] | None, memory: dict[str, Any] | None = None) -> dict[str, Any]:
    current = str(state.get("current_phase", "prepare")) if state else None
    memory = memory if memory is not None else workspace_memory_counts(root)
    if not memory or memory.get("error"):
        memory = {}
    finding_counts = finding_state_counts(root)
    reasons: list[str] = []
    suggested = "prepare"

    if int(memory.get("audits", 0) or 0) > 0:
        suggested = "scan"
        reasons.append(f"{memory.get('audits')} audit record(s) exist")
    if any(finding_counts.get(state_name, 0) for state_name in ("discovered", "confident", "limited")):
        suggested = "scan"
        reasons.append("active scan-state findings exist")
    if int(memory.get("debates", 0) or 0) > 0 or finding_counts.get("validated", 0):
        suggested = "validation"
        if int(memory.get("debates", 0) or 0) > 0:
            reasons.append(f"{memory.get('debates')} debate record(s) exist")
        if finding_counts.get("validated", 0):
            reasons.append("validated finding(s) exist")
    if recursive_file_count(root / "proof") > 0 or finding_counts.get("proofed", 0):
        suggested = "primitive-proof"
        reasons.append("proof artifacts or proofed primitive/chain state exists")
    if finding_counts.get("proofed", 0) and load_ledger(root, "chain")[1]:
        _, chain_ledger, chain_error = load_ledger(root, "chain")
        if not chain_error and chain_ledger:
            if any(finding.get("state") == "proofed" for finding in chain_ledger.get("findings", [])):
                suggested = "chain-proof"
                reasons.append("proofed chain finding exists")
    report_files = sorted((root / "reporting").glob("*.md")) if (root / "reporting").is_dir() else []
    if report_files:
        suggested = "reporting"
        reasons.append(f"{len(report_files)} reporting markdown file(s) exist")

    stale = bool(current and phase_rank(suggested) > phase_rank(current))
    return {
        "current": current,
        "suggested": suggested if stale else current,
        "stale": stale,
        "reasons": reasons if stale else [],
    }


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def large_markdown_files(root: Path, limit: int = LARGE_MARKDOWN_LINES) -> list[tuple[Path, int]]:
    research = root / "research"
    if not research.exists():
        return []
    result: list[tuple[Path, int]] = []
    for path in sorted(research.rglob("*.md")):
        if not path.is_file():
            continue
        lines = count_lines(path)
        if lines > limit:
            result.append((path, lines))
    return result


def markdown_under_artifacts(root: Path) -> list[Path]:
    research = root / "research"
    if not research.exists():
        return []
    result: list[Path] = []
    for path in sorted(research.rglob("*.md")):
        if "artifacts" in path.relative_to(research).parts:
            result.append(path)
    return result


def evidence_reference_keys(root: Path, value: Any) -> set[str]:
    text = str(value or "").strip().strip("`")
    if not text:
        return set()
    text = text.split("#", 1)[0]
    normalized = text.replace("\\", "/").lstrip("./")
    keys = {normalized}
    path = Path(text).expanduser()
    if path.is_absolute():
        keys.add(relative_to(path, root))
    else:
        keys.add(relative_to(root / path, root))
    return {key for key in keys if key}


def corpus_evidence_index(root: Path) -> dict[str, set[str]]:
    if not (root / workspace_db.DB_FILE).exists():
        return {}
    index: dict[str, set[str]] = {}
    try:
        with workspace_db.connect(root) as conn:
            workspace_db.ensure_schema(conn)
            rows = conn.execute("SELECT doc_id, raw_json FROM corpus_documents").fetchall()
    except Exception:
        return {}
    for row in rows:
        try:
            payload = json.loads(row["raw_json"])
        except json.JSONDecodeError:
            continue
        doc_id = str(row["doc_id"])
        for evidence in payload.get("evidence") or []:
            for key in evidence_reference_keys(root, evidence):
                index.setdefault(key, set()).add(doc_id)
    return index


def artifact_markdown_records(root: Path) -> list[dict[str, Any]]:
    evidence_index = corpus_evidence_index(root)
    records: list[dict[str, Any]] = []
    for path in markdown_under_artifacts(root):
        rel = relative_to(path, root)
        referenced_by = sorted(evidence_index.get(rel, set()))
        records.append({"path": path, "relative": rel, "referenced_by": referenced_by})
    return records


def markdown_outside_corpus(root: Path) -> list[Path]:
    research = root / "research"
    if not research.exists():
        return []
    allowed_roots = {"notes", "views", "artifacts"}
    result: list[Path] = []
    for path in sorted(research.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            parts = path.relative_to(research).parts
        except ValueError:
            continue
        if parts and parts[0] not in allowed_roots:
            result.append(path)
    return result


def tool_named_research_dirs(root: Path) -> list[Path]:
    research = root / "research"
    if not research.exists():
        return []
    result: list[Path] = []
    for path in sorted(research.rglob("*")):
        if not path.is_dir():
            continue
        relative_parts = path.relative_to(research).parts
        if "artifacts" in relative_parts:
            continue
        if path.name.lower() in TOOL_DIRECTORY_NAMES:
            result.append(path)
    return result


def parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        timestamp = datetime.fromisoformat(text)
    except ValueError:
        return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def latest_phase_timestamp(state: dict[str, Any] | None) -> datetime | None:
    if not state:
        return None
    history = state.get("phase_history")
    if isinstance(history, list):
        for item in reversed(history):
            if isinstance(item, dict):
                timestamp = parse_timestamp(item.get("time"))
                if timestamp:
                    return timestamp
    return parse_timestamp(state.get("updated_at")) or parse_timestamp(state.get("created_at"))


def file_timestamp(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    except OSError:
        return None


def latest_ledger_timestamp(root: Path) -> datetime | None:
    timestamps = []
    db_timestamp = file_timestamp(root / workspace_db.DB_FILE)
    if db_timestamp:
        timestamps.append(db_timestamp)
    for relative_path in LEGACY_LEDGER_FILES.values():
        timestamp = file_timestamp(root / relative_path)
        if timestamp:
            timestamps.append(timestamp)
    return max(timestamps) if timestamps else None


def minutes_since(timestamp: datetime | None, now_dt: datetime) -> int | None:
    if timestamp is None:
        return None
    return max(0, int((now_dt - timestamp).total_seconds() // 60))


def format_minutes(value: int | None) -> str:
    if value is None:
        return "unknown"
    if value < 60:
        return f"{value}m"
    hours, minutes = divmod(value, 60)
    if minutes == 0:
        return f"{hours}h"
    return f"{hours}h {minutes}m"


def top_level_area(path: Path, root: Path) -> str | None:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return None
    return parts[0] if parts else None


def has_artifactish_dir(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return False
    return any(part.lower() in ATTENTION_ARTIFACT_DIR_NAMES for part in parts)


def research_module_key(path: Path, root: Path) -> str | None:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return None
    if not parts or parts[0] != "research":
        return None

    module_parts = ["research"]
    for part in parts[1:-1]:
        if part.lower() in ATTENTION_ARTIFACT_DIR_NAMES:
            break
        module_parts.append(part)
        if len(module_parts) >= 4:
            break
    if len(module_parts) == 1 and len(parts) > 1:
        module_parts.append(parts[1])
    return "/".join(module_parts)


def recent_attention_files(root: Path, window_minutes: int, limit: int) -> list[tuple[Path, datetime]]:
    window_minutes = max(1, int(window_minutes))
    limit = max(1, int(limit))
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    result: list[tuple[Path, datetime]] = []

    for dirname in ATTENTION_TOP_LEVEL_DIRS:
        base = root / dirname
        if not base.exists() or not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [
                item
                for item in dirnames
                if item.lower() not in ATTENTION_PRUNE_DIRS
            ]
            for filename in filenames:
                path = Path(dirpath) / filename
                if path.suffix.lower() not in ATTENTION_TRACKED_SUFFIXES:
                    continue
                timestamp = file_timestamp(path)
                if timestamp is None or timestamp < cutoff:
                    continue
                result.append((path, timestamp))

    result.sort(key=lambda item: item[1], reverse=True)
    return result[:limit]


def attention_report(root: Path, window_minutes: int = ATTENTION_WINDOW_MINUTES, file_count: int = ATTENTION_FILE_COUNT) -> dict[str, Any]:
    now_dt = datetime.now(timezone.utc)
    state = load_state(root)
    phase_timestamp = latest_phase_timestamp(state)
    ledger_timestamp = latest_ledger_timestamp(root)
    phase_age = minutes_since(phase_timestamp, now_dt)
    ledger_age = minutes_since(ledger_timestamp, now_dt)
    recent_files = recent_attention_files(root, window_minutes, file_count)

    area_counts: Counter[str] = Counter()
    module_counts: Counter[str] = Counter()
    durable_research_markdown = 0
    evidence_files = 0

    for path, _ in recent_files:
        area = top_level_area(path, root) or "unknown"
        area_counts[area] += 1
        if area == "research":
            module = research_module_key(path, root)
            if module:
                module_counts[module] += 1
            if path.suffix.lower() == ".md" and not has_artifactish_dir(path, root):
                durable_research_markdown += 1
        if area in ATTENTION_EVIDENCE_TOP_LEVEL_DIRS or has_artifactish_dir(path, root):
            evidence_files += 1

    research_file_count = sum(module_counts.values())
    dominant_module: dict[str, Any] | None = None
    if module_counts:
        module, count = module_counts.most_common(1)[0]
        ratio = count / research_file_count if research_file_count else 0.0
        dominant_module = {
            "module": module,
            "count": count,
            "ratio": round(ratio, 3),
        }

    warnings: list[dict[str, str]] = []
    current_phase = state.get("current_phase") if state else None
    if phase_age is not None and phase_age >= ATTENTION_PHASE_REVIEW_MINUTES:
        warnings.append(
            {
                "kind": "phase-age",
                "message": (
                    f"Current phase `{current_phase}` has been active for {format_minutes(phase_age)}; "
                    "record a phase note, shift phase, or explicitly renew the current phase with a narrower next checkpoint."
                ),
            }
        )
    if (
        dominant_module
        and research_file_count >= ATTENTION_MIN_RESEARCH_FILES
        and dominant_module["ratio"] >= ATTENTION_DOMINANCE_RATIO
    ):
        warnings.append(
            {
                "kind": "module-dominance",
                "message": (
                    f"{dominant_module['module']} accounts for "
                    f"{dominant_module['count']}/{research_file_count} recent research files; "
                    "close the branch or choose an explicit deepen, pivot, consolidate, or delegate-review action."
                ),
            }
        )
    if module_counts and len(module_counts) >= 4 and max(module_counts.values()) <= 2:
        warnings.append(
            {
                "kind": "shallow-hopping",
                "message": (
                    f"{len(module_counts)} research modules were touched with no module receiving more than two tracked files; "
                    "pick one branch to deepen or consolidate before opening another surface."
                ),
            }
        )
    if evidence_files >= 8 and durable_research_markdown == 0:
        warnings.append(
            {
                "kind": "evidence-without-library-update",
                "message": (
                    f"{evidence_files} recent evidence/artifact files were tracked with no durable research markdown update; "
                    "incorporate reusable knowledge into the research library or mark the branch artifact-only."
                ),
            }
        )
    if ledger_age is not None and ledger_age >= ATTENTION_LEDGER_REVIEW_MINUTES and recent_files:
        warnings.append(
            {
                "kind": "ledger-stale",
                "message": (
                    f"The latest ledger file update is {format_minutes(ledger_age)} old while workspace files changed recently; "
                    "add a finding, milestone, de-escalation, or explicit no-finding closure if the branch produced a decision."
                ),
            }
        )

    return {
        "window_minutes": max(1, int(window_minutes)),
        "file_count_limit": max(1, int(file_count)),
        "phase": current_phase,
        "phase_started_at": phase_timestamp.isoformat() if phase_timestamp else None,
        "phase_age_minutes": phase_age,
        "latest_ledger_update": ledger_timestamp.isoformat() if ledger_timestamp else None,
        "ledger_age_minutes": ledger_age,
        "recent_files_considered": len(recent_files),
        "recent_area_counts": dict(sorted(area_counts.items())),
        "recent_research_modules": [
            {"module": module, "count": count}
            for module, count in module_counts.most_common()
        ],
        "dominant_research_module": dominant_module,
        "durable_research_markdown_recent": durable_research_markdown,
        "evidence_artifact_files_recent": evidence_files,
        "decision_options": list(ATTENTION_DECISION_OPTIONS),
        "decision_required": bool(warnings),
        "warnings": warnings,
    }


def check_program_info(root: Path) -> tuple[bool, str]:
    path = root / "program-info.md"
    if not path.exists():
        return False, "program-info.md is missing"
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return False, "program-info.md is empty"
    if PLACEHOLDER_RE.search(text):
        return False, "program-info.md still contains template placeholders"
    return True, "program-info.md is populated"


def recursive_file_count(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def selected_chains(root: Path, chain_id: str | None) -> tuple[list[dict[str, Any]], list[str]]:
    _, ledger, error = load_ledger(root, "chain")
    if error or ledger is None:
        return [], [f"{workspace_db.DB_FILE} chain ledger is {error}"]
    chains = ledger.get("findings", [])
    if chain_id:
        matches = [finding for finding in chains if str(finding.get("id", "")).lower() == chain_id.lower()]
        if not matches:
            return [], [f"chain not found: {chain_id}"]
        return matches, []
    proofed = [finding for finding in chains if finding.get("state") == "proofed"]
    if not proofed:
        return [], ["no proofed chains found"]
    return proofed, []


def report_readiness(root: Path, chain_id: str | None = None, *, require_report_file: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    ok, detail = check_program_info(root)
    add("program-info", ok, detail)

    chains, chain_errors = selected_chains(root, chain_id)
    if chain_errors:
        add("proofed-chain", False, "; ".join(chain_errors))
    else:
        proofed_count = sum(1 for chain in chains if chain.get("state") == "proofed")
        add("proofed-chain", proofed_count > 0, f"{proofed_count} proofed chain(s) selected")
        for chain in chains:
            chain_label = str(chain.get("id", "unknown"))
            has_summary = bool(str(chain.get("summary", "")).strip())
            has_evidence = bool(chain.get("evidence"))
            has_location = bool(chain.get("locations"))
            add(f"{chain_label}-summary", has_summary, "summary present" if has_summary else "summary missing")
            add(f"{chain_label}-evidence", has_evidence, "evidence present" if has_evidence else "evidence missing")
            add(f"{chain_label}-location", has_location, "location present" if has_location else "location missing")

    proof_count = recursive_file_count(root / "proof")
    add("proof-artifacts", proof_count > 0, f"{proof_count} proof file(s) under proof/")

    reports = root / "reporting"
    if require_report_file:
        report_files = sorted(reports.glob("*.md")) if reports.exists() else []
        if chain_id:
            report_files = [path for path in report_files if chain_id.lower() in path.name.lower()]
        add("report-file", bool(report_files), f"{len(report_files)} matching report file(s)")
    else:
        add("reporting-directory", reports.is_dir(), "reporting/ exists" if reports.is_dir() else "reporting/ is missing")

    state = load_state(root)
    current_phase = state.get("current_phase") if state else None
    phase_ok = current_phase in {"chain-proof", "reporting"}
    add(
        "phase",
        phase_ok,
        f"current phase is {current_phase}" if current_phase else "workspace phase is not initialized",
    )

    ready = all(check["ok"] for check in checks)
    return {"ready": ready, "checks": checks, "chains": chains}


def print_checks(result: dict[str, Any]) -> None:
    print("Report readiness: ready" if result["ready"] else "Report readiness: not ready")
    for check in result["checks"]:
        mark = "ok" if check["ok"] else "missing"
        print(f"- {mark}: {check['name']} - {check['detail']}")


def print_attention(result: dict[str, Any]) -> None:
    print("Attention cadence:")
    print(
        f"- window: latest {result['window_minutes']}m, "
        f"{result['recent_files_considered']} tracked file(s)"
    )
    print(
        f"- phase age: {format_minutes(result['phase_age_minutes'])} "
        f"({result['phase'] or 'not initialized'})"
    )
    print(f"- ledger age: {format_minutes(result['ledger_age_minutes'])}")
    dominant = result.get("dominant_research_module")
    if dominant:
        ratio = int(float(dominant["ratio"]) * 100)
        print(f"- dominant research module: {dominant['module']} ({ratio}% of recent research files)")
    else:
        print("- dominant research module: none")
    if result["warnings"]:
        print("- decision required: choose deepen, pivot, consolidate, phase-shift, or delegate-review")
        for warning in result["warnings"]:
            print(f"- review: {warning['message']}")
    else:
        print("- warnings: none")


def cmd_init(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    phase = normalize_phase(args.phase)
    print(f"MaxTAC workspace root: {root}")

    for dirname, description in WORKSPACE_DIRS.items():
        path = root / dirname
        path.mkdir(parents=True, exist_ok=True)
        print(f"- directory: {dirname}/ ({description})")

    program_info = root / "program-info.md"
    if args.no_program_info:
        print("- file: program-info.md skipped")
    elif program_info.exists() and not args.force_program_info:
        print("- file: program-info.md exists")
    else:
        template = read_template(PROGRAM_INFO_TEMPLATE, "# [program name]\n[description of the program]\n")
        program_info.write_text(template.rstrip() + "\n", encoding="utf-8")
        print("- file: program-info.md created from template")

    for ledger_type in LEDGER_TYPES:
        status = create_ledger(root, ledger_type, force=args.force_ledgers)
        print(f"- ledger: {workspace_db.DB_FILE} {ledger_type} {status}")

    state = load_state(root)
    if state and not args.force_state:
        print(f"- state: {STATE_FILE} exists (phase={state.get('current_phase')})")
    else:
        save_state(root, initial_state(phase, args.note or "Workspace initialized."))
        print(f"- state: {STATE_FILE} initialized (phase={phase})")


def cmd_status(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    state = load_state(root)
    attention = attention_report(root, args.attention_window_minutes, args.attention_file_count)
    memory = workspace_memory_counts(root)
    phase_status = phase_guidance(root, state, memory)
    artifact_records = artifact_markdown_records(root)
    unreferenced_artifacts = [record for record in artifact_records if not record["referenced_by"]]

    if args.json:
        payload: dict[str, Any] = {
            "root": str(root),
            "phase": state.get("current_phase") if state else None,
            "phase_guidance": phase_status,
            "files": {},
            "directories": {},
            "ledgers": {},
            "large_markdown": [],
            "research_hygiene": {
                "markdown_under_artifacts": [],
                "artifact_markdown": [],
                "artifact_markdown_unreferenced": [],
                "tool_named_research_dirs": [],
                "markdown_outside_corpus": [],
            },
            "attention": attention,
            "report_ready": report_readiness(root, args.chain),
        }
        for filename in WORKSPACE_FILES:
            path = root / filename
            payload["files"][filename] = path.exists()
        for dirname in WORKSPACE_DIRS:
            path = root / dirname
            payload["directories"][dirname] = path.is_dir()
        for ledger_type in LEDGER_TYPES:
            path, ledger, error = load_ledger(root, ledger_type)
            payload["ledgers"][ledger_type] = {
                "path": str(path),
                "error": error,
                "counts": ledger_counts(ledger) if ledger else {},
            }
        payload["workspace_memory"] = memory or {
            "error": f"{workspace_db.DB_FILE} missing"
        }
        payload["large_markdown"] = [
            {"path": relative_to(path, root), "lines": lines}
            for path, lines in large_markdown_files(root, args.max_lines)
        ]
        payload["research_hygiene"]["markdown_under_artifacts"] = [record["relative"] for record in artifact_records]
        payload["research_hygiene"]["artifact_markdown"] = [
            {"path": record["relative"], "referenced_by": record["referenced_by"]}
            for record in artifact_records
        ]
        payload["research_hygiene"]["artifact_markdown_unreferenced"] = [
            record["relative"] for record in unreferenced_artifacts
        ]
        payload["research_hygiene"]["tool_named_research_dirs"] = [
            relative_to(path, root) for path in tool_named_research_dirs(root)
        ]
        payload["research_hygiene"]["markdown_outside_corpus"] = [
            relative_to(path, root) for path in markdown_outside_corpus(root)
        ]
        print(json.dumps(payload, indent=2))
        return

    print(f"MaxTAC workspace status: {root}")
    if state:
        print(f"- phase: {state.get('current_phase')}")
    else:
        print(f"- phase: not initialized ({STATE_FILE} missing)")
    if phase_status["stale"]:
        print(
            f"- phase guidance: suggest `{phase_status['suggested']}` because "
            f"{'; '.join(phase_status['reasons'])}"
        )

    print("Workspace files:")
    for filename, description in WORKSPACE_FILES.items():
        status = "ok" if (root / filename).exists() else "missing"
        print(f"- {status}: {filename} - {description}")

    print("Workspace directories:")
    for dirname, description in WORKSPACE_DIRS.items():
        status = "ok" if (root / dirname).is_dir() else "missing"
        print(f"- {status}: {dirname}/ - {description}")

    print("Ledgers:")
    for ledger_type in LEDGER_TYPES:
        path, ledger, error = load_ledger(root, ledger_type)
        if error or ledger is None:
            print(f"- {ledger_type}: {error} ({relative_to(path, root)})")
            continue
        counts = ledger_counts(ledger)
        summary = ", ".join(f"{state_name}={count}" for state_name, count in sorted(counts.items()))
        active = sum(
            1 for finding in ledger.get("findings", []) if finding.get("state") not in TERMINAL_STATES
        )
        print(f"- {ledger_type}: {len(ledger.get('findings', []))} finding(s), active={active}, {summary or 'empty'}")

    if memory is None:
        print(f"Workspace memory: {workspace_db.DB_FILE} missing")
    elif memory.get("error"):
        print(f"Workspace memory: error: {memory['error']}")
    else:
        print(
            "Workspace memory: "
            f"corpus={memory['corpus_documents']} note(s), "
            f"corpus_edges={memory['corpus_edges']}, "
            f"models={memory['models']}, debates={memory['debates']}, audits={memory['audits']}"
        )

    large = large_markdown_files(root, args.max_lines)
    if large:
        print(f"Large markdown files over {args.max_lines} lines:")
        for path, lines in large:
            print(f"- {relative_to(path, root)} ({lines} lines)")
    else:
        print(f"Large markdown files over {args.max_lines} lines: none")

    artifact_markdown = unreferenced_artifacts
    tool_dirs = tool_named_research_dirs(root)
    outside_corpus = markdown_outside_corpus(root)
    if artifact_markdown or tool_dirs or outside_corpus:
        print("Research hygiene warnings:")
        for record in artifact_markdown:
            print(
                f"- review: {record['relative']} is unreferenced markdown under artifacts/; "
                "reference it from a corpus note or rewrite durable conclusions into a corpus note if future sessions should read it"
            )
        for path in outside_corpus[:25]:
            print(
                f"- review: {relative_to(path, root)} is research markdown outside research/notes, research/views, or research/artifacts; "
                "import durable knowledge with maxtac-core-corpus instead of growing a hand-authored hierarchy"
            )
        if len(outside_corpus) > 25:
            print(f"- review: {len(outside_corpus) - 25} additional outside-corpus markdown file(s) omitted")
        for path in tool_dirs:
            print(
                f"- review: {relative_to(path, root)}/ is tool-named research; "
                "move raw tool outputs under artifacts/ unless the tool itself is the modeled system"
            )
    else:
        referenced_count = len(artifact_records)
        if referenced_count:
            print(
                "Research hygiene warnings: none "
                f"({referenced_count} artifact markdown file(s) are referenced by corpus note evidence)"
            )
        else:
            print("Research hygiene warnings: none")

    print_attention(attention)
    print_checks(report_readiness(root, args.chain))


def cmd_phase(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    state = load_state(root)
    if state is None:
        state = initial_state("prepare", "Workspace phase initialized.")

    current = str(state.get("current_phase", "prepare"))
    if args.phase and (args.suggest or args.auto):
        raise SystemExit("pass either a target phase, --suggest, or --auto")
    if args.list:
        print("MaxTAC phases:")
        for phase in PHASES:
            next_phases = ", ".join(sorted(PHASE_TRANSITIONS[phase]))
            print(f"- {phase}: next {next_phases}")
        return

    if args.suggest or args.auto:
        guidance = phase_guidance(root, state)
        if not guidance["stale"]:
            print(f"Phase guidance: current phase `{current}` is consistent with workspace evidence.")
            if args.auto:
                save_state(root, state)
            return
        target = str(guidance["suggested"])
        reason_text = "; ".join(guidance["reasons"])
        if args.suggest:
            print(f"Phase guidance: suggest `{target}` from current `{current}`.")
            print(f"Reason: {reason_text}")
            return
        timestamp = now()
        state["current_phase"] = target
        state["updated_at"] = timestamp
        state.setdefault("phase_history", []).append(
            {
                "time": timestamp,
                "from": current,
                "to": target,
                "note": args.note or f"Auto phase inference from workspace evidence: {reason_text}",
                "auto": True,
            }
        )
        save_state(root, state)
        print(f"Phase changed: {current} -> {target}")
        return

    if not args.phase:
        next_phases = ", ".join(sorted(PHASE_TRANSITIONS[current]))
        print(f"Current phase: {current}")
        print(f"Allowed next phases: {next_phases}")
        return

    target = normalize_phase(args.phase)
    if target == current:
        if args.note:
            timestamp = now()
            state["updated_at"] = timestamp
            state.setdefault("phase_history", []).append(
                {
                    "time": timestamp,
                    "from": current,
                    "to": target,
                    "note": args.note,
                    "renewal": True,
                }
            )
            print(f"Phase renewed: {current}")
        else:
            print(f"Phase unchanged: {current}")
        save_state(root, state)
        return

    allowed = PHASE_TRANSITIONS[current]
    if target not in allowed and not args.force:
        allowed_text = ", ".join(sorted(allowed))
        raise SystemExit(f"Invalid transition {current} -> {target}. Allowed: {allowed_text}. Use --force to override.")

    timestamp = now()
    state["current_phase"] = target
    state["updated_at"] = timestamp
    state.setdefault("phase_history", []).append(
        {
            "time": timestamp,
            "from": current,
            "to": target,
            "note": args.note,
        }
    )
    save_state(root, state)
    print(f"Phase changed: {current} -> {target}")


def research_parent(root: Path, value: str | None) -> Path:
    research = root / "research"
    if value:
        raw = Path(value).expanduser()
        if raw.is_absolute():
            parent = raw
        elif raw.parts and raw.parts[0].lower() == "research":
            parent = root / raw
        else:
            parent = research / raw
    else:
        parent = research
    return ensure_within(research, parent, "research parent")


def write_subsystem_template(path: Path, title: str, overwrite: bool) -> str:
    if path.exists() and not overwrite:
        return "exists"
    existed = path.exists()
    template = read_template(SUBSYSTEM_TEMPLATE, "# [subsystem name]\n[security knowledge base notes]\n")
    text = template.replace("[subsystem name]", title)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return "written" if existed else "created"


def cmd_new_submodule(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    parent = research_parent(root, args.parent)
    parent.mkdir(parents=True, exist_ok=True)

    name = slugify(args.name)
    module_dir = ensure_within(root / "research", parent / name, "submodule")
    if module_dir.exists() and not module_dir.is_dir():
        raise SystemExit(f"Submodule path exists and is not a directory: {module_dir}")
    if module_dir.exists() and not args.force:
        raise SystemExit(f"Submodule already exists: {relative_to(module_dir, root)}. Use --force to reuse it.")
    module_dir.mkdir(parents=True, exist_ok=True)

    print(f"Submodule: {relative_to(module_dir, root)}")
    if not args.no_artifacts:
        artifacts = module_dir / "artifacts"
        artifacts.mkdir(exist_ok=True)
        print(f"- directory: {relative_to(artifacts, root)}")
        print("- note: keep book-like markdown in the submodule; keep raw evidence and transcripts under artifacts/")

    for markdown in args.markdown or []:
        filename = markdown_name(markdown)
        markdown_path = module_dir / filename
        title = args.title or Path(filename).stem.replace("-", " ").title()
        status = write_subsystem_template(markdown_path, title, args.overwrite)
        print(f"- markdown: {relative_to(markdown_path, root)} {status}")


def heading_title(lines: list[str], fallback: str) -> str:
    for line in lines:
        match = HEADING_RE.match(line)
        if match:
            return match.group(2).strip()
    return fallback


def split_at_heading(lines: list[str], level: int) -> list[tuple[str, list[str]]]:
    blocks: list[tuple[str, list[str]]] = []
    intro: list[str] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in lines:
        match = HEADING_RE.match(line)
        if match and len(match.group(1)) == level:
            if current_title is not None:
                blocks.append((current_title, current_lines))
            elif any(item.strip() for item in intro):
                blocks.append(("overview", intro))
            current_title = match.group(2).strip()
            current_lines = [line]
            intro = []
        else:
            if current_title is None:
                intro.append(line)
            else:
                current_lines.append(line)

    if current_title is not None:
        blocks.append((current_title, current_lines))
    elif any(item.strip() for item in intro):
        blocks.append(("overview", intro))
    return blocks


def choose_split_level(lines: list[str]) -> int | None:
    for level in (2, 3, 1, 4):
        count = 0
        for line in lines:
            match = HEADING_RE.match(line)
            if match and len(match.group(1)) == level:
                count += 1
        if count >= 2:
            return level
    return None


def chunk_lines(title: str, lines: list[str], max_lines: int) -> list[tuple[str, list[str]]]:
    chunks: list[tuple[str, list[str]]] = []
    for index in range(0, len(lines), max_lines):
        chunk = lines[index : index + max_lines]
        chunk_title = f"{title} part {len(chunks) + 1}"
        if not chunk or not HEADING_RE.match(chunk[0]):
            chunk = [f"# {chunk_title}\n", "\n", *chunk]
        chunks.append((chunk_title, chunk))
    return chunks


def split_markdown(lines: list[str], max_lines: int) -> list[tuple[str, list[str]]]:
    level = choose_split_level(lines)
    blocks = split_at_heading(lines, level) if level else [("overview", lines)]
    result: list[tuple[str, list[str]]] = []

    for title, block_lines in blocks:
        if len(block_lines) <= max_lines:
            result.append((title, block_lines))
            continue
        split_level = choose_split_level(block_lines)
        if split_level:
            subblocks = split_at_heading(block_lines, split_level)
            if len(subblocks) > 1:
                for subtitle, sublines in subblocks:
                    merged_title = title if subtitle == "overview" else f"{title} {subtitle}"
                    if len(sublines) <= max_lines:
                        result.append((merged_title, sublines))
                    else:
                        result.extend(chunk_lines(merged_title, sublines, max_lines))
                continue
        result.extend(chunk_lines(title, block_lines, max_lines))
    return result


def unique_output_path(directory: Path, title: str, used: set[Path]) -> Path:
    base = slugify(title, "section")
    candidate = directory / f"{base}.md"
    counter = 2
    while candidate in used or candidate.exists():
        candidate = directory / f"{base}-{counter}.md"
        counter += 1
    used.add(candidate)
    return candidate


def default_artifact_candidates(source: Path) -> list[Path]:
    parent = source.parent
    stem = source.stem
    return [
        parent / f"{stem}-artifacts",
        parent / f"{stem}_artifacts",
        parent / f"{stem}.artifacts",
    ]


def copy_artifact(source: Path, destination_dir: Path, *, overwrite: bool) -> Path:
    destination = destination_dir / source.name
    if destination.exists() and not overwrite:
        raise SystemExit(f"Artifact destination exists: {destination}")
    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return destination


def cmd_split_large_markdown(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    source = workspace_path(root, args.markdown_file, "markdown file")
    if not source.exists():
        raise SystemExit(f"Markdown file not found: {source}")
    if source.suffix.lower() != ".md":
        raise SystemExit(f"Expected a markdown file: {source}")

    lines = source.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    if len(lines) <= args.large_threshold and not args.force:
        raise SystemExit(
            f"{relative_to(source, root)} has {len(lines)} lines, below threshold {args.large_threshold}. "
            "Use --force to split anyway."
        )

    target_name = slugify(args.submodule or source.stem)
    target_dir = ensure_within(root / "research", source.parent / target_name, "target submodule")
    if target_dir.exists() and not args.force:
        raise SystemExit(f"Target submodule already exists: {relative_to(target_dir, root)}. Use --force to reuse it.")
    target_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = target_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    blocks = split_markdown(lines, args.max_lines)
    written: list[dict[str, Any]] = []
    used_paths: set[Path] = set()
    for title, block_lines in blocks:
        output_path = unique_output_path(target_dir, title, used_paths)
        output_path.write_text("".join(block_lines).rstrip() + "\n", encoding="utf-8")
        written.append(
            {
                "path": relative_to(output_path, root),
                "title": heading_title(block_lines, title),
                "lines": len(block_lines),
            }
        )

    artifact_sources: list[Path] = []
    for value in args.copy_artifact or []:
        artifact_sources.append(workspace_path(root, value, "artifact"))
    for candidate in default_artifact_candidates(source):
        if candidate.exists():
            artifact_sources.append(ensure_within(root, candidate, "artifact"))

    copied: list[dict[str, str]] = []
    seen_artifacts: set[Path] = set()
    for artifact in artifact_sources:
        resolved = artifact.resolve()
        if resolved in seen_artifacts:
            continue
        seen_artifacts.add(resolved)
        if not artifact.exists():
            raise SystemExit(f"Artifact not found: {artifact}")
        destination = copy_artifact(artifact, artifacts_dir, overwrite=args.force)
        copied.append({"from": relative_to(artifact, root), "to": relative_to(destination, root)})

    manifest = {
        "version": 1,
        "source": relative_to(source, root),
        "source_lines": len(lines),
        "target_submodule": relative_to(target_dir, root),
        "created_at": now(),
        "sections": written,
        "artifacts": copied,
        "source_deleted": False,
    }

    if args.delete_source and not args.verified:
        raise SystemExit("--delete-source requires --verified")
    if args.delete_artifacts and not args.verified:
        raise SystemExit("--delete-artifacts requires --verified")

    if args.delete_source:
        source.unlink()
        manifest["source_deleted"] = True

    deleted_artifacts: list[str] = []
    if args.delete_artifacts:
        for artifact in seen_artifacts:
            if artifact.is_dir():
                shutil.rmtree(artifact)
            elif artifact.exists():
                artifact.unlink()
            deleted_artifacts.append(relative_to(artifact, root))
    manifest["artifacts_deleted"] = deleted_artifacts

    manifest_path = target_dir / "split-manifest.json"
    write_json(manifest_path, manifest)

    print(f"Split markdown: {relative_to(source, root)} -> {relative_to(target_dir, root)}")
    print(f"- source lines: {len(lines)}")
    print(f"- created markdown files: {len(written)}")
    for item in written:
        print(f"  - {item['path']} ({item['lines']} lines)")
    if copied:
        print(f"- copied artifacts: {len(copied)}")
    print(f"- manifest: {relative_to(manifest_path, root)}")
    if not args.delete_source:
        print("- source retained; delete it only after verifying the split")


def cmd_report_ready(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    result = report_readiness(root, args.chain, require_report_file=args.require_report_file)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_checks(result)
    if not result["ready"]:
        raise SystemExit(1)


def add_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="Workspace root; defaults to the current directory")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC workspace workflow helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create canonical workspace files and directories")
    add_root_arg(init)
    init.add_argument("--phase", default="prepare", help="Initial phase")
    init.add_argument("--note")
    init.add_argument("--no-program-info", action="store_true")
    init.add_argument("--force-program-info", action="store_true", help="Rewrite program-info.md from the template")
    init.add_argument("--force-ledgers", action="store_true", help="Overwrite existing ledgers with empty ledgers")
    init.add_argument("--force-state", action="store_true", help=f"Rewrite {STATE_FILE}")
    init.set_defaults(func=cmd_init)

    status = subparsers.add_parser("status", help="Inspect workspace health")
    add_root_arg(status)
    status.add_argument("--chain", help="Specific chain id for report readiness checks")
    status.add_argument("--max-lines", type=int, default=LARGE_MARKDOWN_LINES)
    status.add_argument("--attention-window-minutes", type=int, default=ATTENTION_WINDOW_MINUTES)
    status.add_argument("--attention-file-count", type=int, default=ATTENTION_FILE_COUNT)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    phase = subparsers.add_parser("phase", help="Show or change the workflow phase")
    add_root_arg(phase)
    phase.add_argument("phase", nargs="?", help="Target phase")
    phase.add_argument("--list", action="store_true", help="List phases and allowed transitions")
    phase.add_argument("--force", action="store_true", help="Allow a nonstandard phase transition")
    phase.add_argument("--suggest", action="store_true", help="Suggest a phase from workspace evidence without writing state")
    phase.add_argument("--auto", action="store_true", help="Update to the evidence-suggested phase and record an automatic phase note")
    phase.add_argument("--note")
    phase.set_defaults(func=cmd_phase)

    submodule = subparsers.add_parser("new-submodule", help="Create a legacy research submodule")
    add_root_arg(submodule)
    submodule.add_argument("name", help="Submodule directory name")
    submodule.add_argument("--parent", help="Parent under research/; defaults to research/")
    submodule.add_argument("--markdown", action="append", help="Create a subsystem markdown file")
    submodule.add_argument("--title", help="Title for created subsystem markdown")
    submodule.add_argument("--no-artifacts", action="store_true")
    submodule.add_argument("--force", action="store_true", help="Reuse an existing submodule directory")
    submodule.add_argument("--overwrite", action="store_true", help="Overwrite created markdown files")
    submodule.set_defaults(func=cmd_new_submodule)

    split = subparsers.add_parser("split-large-markdown", help="Split a large research markdown into a submodule")
    add_root_arg(split)
    split.add_argument("markdown_file")
    split.add_argument("--submodule", help="Target submodule name; defaults to the markdown stem")
    split.add_argument("--large-threshold", type=int, default=LARGE_MARKDOWN_LINES)
    split.add_argument("--max-lines", type=int, default=SPLIT_TARGET_LINES)
    split.add_argument("--copy-artifact", action="append", help="File or directory to copy into the new artifacts/")
    split.add_argument("--delete-source", action="store_true", help="Delete the source markdown after a verified split")
    split.add_argument("--delete-artifacts", action="store_true", help="Delete copied source artifacts after verification")
    split.add_argument("--verified", action="store_true", help="Confirm the split has been reviewed")
    split.add_argument("--force", action="store_true", help="Split below threshold or reuse existing outputs")
    split.set_defaults(func=cmd_split_large_markdown)

    report = subparsers.add_parser("report-ready", help="Check whether proofed chains are ready for reporting")
    add_root_arg(report)
    report.add_argument("--chain", help="Specific chain id")
    report.add_argument("--require-report-file", action="store_true")
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=cmd_report_ready)

    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
