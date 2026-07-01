#!/usr/bin/env python3
"""List MaxTAC auditors and enrich auditor subagent prompts."""

from __future__ import annotations

import argparse
import json
import secrets
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CORE_SKILLS_DIR = SKILL_DIR.parent
CORPUS_SCRIPT = CORE_SKILLS_DIR / "maxtac-core-corpus" / "scripts" / "corpus.py"
MODEL_SCRIPT = CORE_SKILLS_DIR / "maxtac-core-modeling" / "scripts" / "model.py"
LEDGER_SCRIPTS_DIR = SKILL_DIR.parent / "maxtac-core-ledger" / "scripts"
sys.path.insert(0, str(LEDGER_SCRIPTS_DIR))

import workspace_db  # noqa: E402
import auditor_registry  # noqa: E402


def generated_id(prefix: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{timestamp}-{secrets.token_hex(3)}"


def read_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def root_path(value: str | None) -> Path:
    root = Path(value or ".").expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Workspace root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Workspace root is not a directory: {root}")
    return root


def workspace_path(root: Path, value: Path, label: str) -> Path:
    path = value.expanduser()
    if not path.is_absolute():
        path = root / path
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise SystemExit(f"{label} escapes workspace root: {resolved_path}") from exc
    return resolved_path


def text_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(text_values(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(text_values(item))
        return result
    return [str(value)]


def auditor_search_text(auditor: dict[str, Any]) -> str:
    return " ".join(text_values(auditor)).lower()


def condensed_auditor(auditor: dict[str, Any]) -> str:
    auditor_id = str(auditor.get("id", "")).strip()
    name = str(auditor.get("name") or auditor.get("title") or auditor_id).strip()
    specialty = auditor.get("specialty") or auditor.get("category") or auditor.get("focus")
    summary = auditor.get("summary") or auditor.get("description") or auditor.get("usage")
    tags = auditor.get("tags") or auditor.get("keywords") or auditor.get("cwe")

    parts = [f"- {auditor_id}: {name}"]
    if specialty:
        parts.append(f"specialty={specialty}")
    if tags:
        if isinstance(tags, list):
            tags = ", ".join(str(tag) for tag in tags)
        parts.append(f"tags={tags}")
    if summary:
        parts.append(str(summary))
    return " | ".join(parts)


def markdown_for_auditor(auditor: dict[str, Any]) -> str:
    for key in ("markdown", "instructions", "prompt", "content"):
        value = auditor.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip() + "\n"
        if isinstance(value, list) and value:
            return "\n".join(str(line) for line in value).strip() + "\n"

    auditor_id = str(auditor.get("id", "")).strip()
    name = str(auditor.get("name") or auditor.get("title") or auditor_id).strip()
    lines = [f"# {name}", "", f"- Auditor: {auditor_id}"]
    for key in ("specialty", "category", "focus", "summary", "description", "usage"):
        value = auditor.get(key)
        if value:
            label = key.replace("_", " ").title()
            lines.append(f"- {label}: {value}")
    tags = auditor.get("tags") or auditor.get("keywords")
    if tags:
        if isinstance(tags, list):
            tags = ", ".join(str(tag) for tag in tags)
        lines.append(f"- Tags: {tags}")
    return "\n".join(lines).rstrip() + "\n"


def list_auditors(auditors: list[dict[str, Any]]) -> None:
    for auditor in auditors:
        print(condensed_auditor(auditor))


def filter_auditors(auditors: list[dict[str, Any]], query: str) -> None:
    needle = query.lower()
    matches = [auditor for auditor in auditors if needle in auditor_search_text(auditor)]
    if not matches:
        print("No matching auditors.")
        return
    list_auditors(matches)


def show_auditor(auditors: list[dict[str, Any]], auditor_id: str) -> None:
    needle = auditor_id.lower()
    for auditor in auditors:
        if str(auditor.get("id", "")).lower() == needle:
            print(markdown_for_auditor(auditor), end="")
            return
    raise SystemExit(f"Auditor not found: {auditor_id}")


def python_command() -> str:
    return sys.executable or "python3"


def shell_quote(value: str | Path) -> str:
    return shlex.quote(str(value))


def run_context_command(label: str, command: list[str], *, timeout: int = 45) -> str:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"## {label}\n\nUnavailable: {exc}\n"
    output = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        details = stderr or output or f"exit status {completed.returncode}"
        return f"## {label}\n\nUnavailable: {details}\n"
    return f"## {label}\n\n{output or '(no matching records)'}\n"


def pre_audit_context(root: Path, query: str | None) -> str:
    if not query:
        return (
            "## Pre-Audit Context\n\n"
            "No `--context-query` was supplied. The parent prompt must include corpus orientation, model context, "
            "or a clear reason that neither applies.\n"
        )
    sections = [
        f"## Pre-Audit Context\n\nContext query: `{query}`\n",
    ]
    if CORPUS_SCRIPT.exists():
        sections.append(
            run_context_command(
                "Corpus Orientation",
                [
                    python_command(),
                    str(CORPUS_SCRIPT),
                    "orient",
                    "--root",
                    str(root),
                    "--query",
                    query,
                    "--limit",
                    "8",
                ],
            )
        )
    else:
        sections.append(f"## Corpus Orientation\n\nUnavailable: helper not found at {CORPUS_SCRIPT}\n")
    if MODEL_SCRIPT.exists():
        sections.append(
            run_context_command(
                "Model Search",
                [
                    python_command(),
                    str(MODEL_SCRIPT),
                    "search",
                    "--root",
                    str(root),
                    "--query",
                    query,
                    "--limit",
                    "8",
                ],
            )
        )
    else:
        sections.append(f"## Model Search\n\nUnavailable: helper not found at {MODEL_SCRIPT}\n")
    return "\n".join(section.rstrip() for section in sections) + "\n"


def enrich_prompt(prompt_file: Path, root: Path, *, context_query: str | None = None, prompt_kind: str = "audit") -> None:
    prompt_path_input = workspace_path(root, prompt_file, "Prompt file")
    raw_prompt = read_text(prompt_path_input).rstrip()
    audit_id = generated_id("audit")
    helper_path = Path(__file__).resolve()
    assessment_path = f"tmp/assessment-{audit_id}.md"
    kind_label = prompt_kind.replace("-", " ")
    goal_objective = (
        f"Produce a focused MaxTAC {kind_label} assessment for the supplied hypothesis, proposition, or evidence, "
        f"then persist it to {workspace_db.DB_FILE}. Negative end outcome: if the supplied context, directly "
        "referenced files, or available tools are insufficient to decide the question within a bounded pass, stop "
        "broadening scope and persist an assessment with blockers, missing evidence, and the safest recommended next step."
    )
    goal_call = json.dumps({"objective": goal_objective})
    enriched = f"""FIRST ACTION REQUIRED: activate a Codex goal before doing any audit work.

If the `create_goal` tool is available, your first tool call must be:

```json
{goal_call}
```

If `create_goal` is unavailable but slash commands are available, send this before any other work:

```text
/goal {goal_objective}
```

Do not inspect files, run commands, reason through the hypothesis, or draft the assessment until goal activation has been attempted. Work inside that active goal. If goal activation is unavailable, continue only within the bounds below and record `Goal activation: unavailable` in the assessment.

Bounds: inspect the supplied packet/evidence, directly referenced files/functions, and immediately necessary callers/callees only. Do not start broad repo discovery, fuzzing, PoV construction, or unrelated refactors unless this prompt explicitly grants that scope. Do not complete the subagent run until the goal is either achieved or ended with the negative outcome above.

## {kind_label.title()} Task

{raw_prompt}

---

{pre_audit_context(root, context_query)}

---

## MaxTAC Audit Persistence Instructions

Audit ID: `{audit_id}`
Assessment kind: `{prompt_kind}`

Persist the final audit assessment to `{workspace_db.DB_FILE}` before completing the subagent run. Draft the Markdown assessment at `{assessment_path}`, then record it with:

```text
{shell_quote(python_command())} "{helper_path}" --root "{root}" --audit {audit_id} --record-assessment {assessment_path}
```

Include a `Goal Activation` section naming `create_goal`, `/goal`, or `unavailable`; then include the assessment kind, vulnerability hypothesis or verification focus, method, reviewed files or components, findings, evidence, exploitability notes when relevant, blockers, and a clear conclusion. Summarize supporting evidence in the assessment and cite durable artifact paths from `research/`, `proof/`, `fuzz/`, `contracts/`, or `tmp/` when needed.
"""
    workspace_db.create_audit(root, audit_id, enriched)
    print(enriched, end="")


def one_line(value: Any, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def render_audit_row(payload: dict[str, Any]) -> str:
    status = "assessed" if payload.get("assessment_text") else "prompt-only"
    artifacts = payload.get("artifacts") or []
    conclusion = one_line(payload.get("conclusion") or payload.get("prompt_text"))
    return (
        f"{payload.get('audit_id')} "
        f"status={status} "
        f"artifacts={len(artifacts)} "
        f"updated={payload.get('updated_at', '')} "
        f"{conclusion}"
    ).rstrip()


def print_audit_detail(payload: dict[str, Any]) -> None:
    print(f"Audit: {payload.get('audit_id')}")
    print(f"- storage: {workspace_db.DB_FILE}")
    print(f"- goal_activation: {payload.get('goal_activation', '') or 'unknown'}")
    print(f"- updated: {payload.get('updated_at', '')}")
    print()
    artifacts = payload.get("artifacts") or []
    if artifacts:
        print("Artifacts:")
        for artifact in artifacts:
            print(
                f"- {artifact.get('path', '')} "
                f"kind={artifact.get('kind', '')} "
                f"size={artifact.get('size', 0)} "
                f"mtime={artifact.get('mtime_utc', '')}"
            )
        print()
    print("## Conclusion")
    print(str(payload.get("conclusion", "")).rstrip() or "(missing)")
    print()
    if payload.get("assessment_text"):
        print("## Assessment")
        print(str(payload.get("assessment_text", "")).rstrip())


def record_assessment(audit_id: str, assessment_file: Path, root: Path) -> None:
    assessment_path = workspace_path(root, assessment_file, "Assessment file")
    assessment_text = read_text(assessment_path)
    payload = workspace_db.record_audit_assessment(root, audit_id, assessment_text)
    print(render_audit_row(payload))


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC auditor helper")
    parser.add_argument("--root", default=".", help="Workspace root; prompt files should be staged under tmp/")
    parser.add_argument("--catalog", default="core", help="Auditor catalog for --list/--filter/--show; use --catalogs to list choices")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--catalogs", action="store_true", help="List available local auditor catalogs")
    group.add_argument("--auditor-rebuild", action="store_true", help="Rebuild the SQLite auditor registry from active plugins")
    group.add_argument("--list", action="store_true", help="List condensed auditor information")
    group.add_argument("--filter", metavar="TEXT", help="Filter auditors by text")
    group.add_argument("--show", metavar="AUDITOR_ID", help="Show full auditor markdown")
    group.add_argument("--prompt-file", type=Path, help="Enrich a persisted audit prompt")
    group.add_argument("--audit", metavar="AUDIT_ID", help="Audit ID to update")
    group.add_argument("--audit-sync", action="store_true", help="Refresh audit search records in workspace.sqlite")
    group.add_argument("--audit-list", action="store_true", help="List synced audit assessments")
    group.add_argument("--audit-show", metavar="AUDIT_ID", help="Show synced audit details")
    group.add_argument("--audit-search", metavar="TEXT", help="Semantic search audit prompts, assessments, and artifacts")
    parser.add_argument("--record-assessment", type=Path, help="Record an assessment Markdown file into workspace.sqlite")
    parser.add_argument("--context-query", help="Embed corpus orientation and model search output into an enriched prompt")
    parser.add_argument(
        "--prompt-kind",
        choices=("audit", "verifier", "attention-review", "mitigation-review"),
        default="audit",
        help="Assessment kind to embed when enriching --prompt-file",
    )
    parser.add_argument("--limit", type=int, default=10, help="Maximum rows for audit list or search output")
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()

    if args.catalogs:
        if args.context_query:
            raise SystemExit("--context-query can only be used with --prompt-file")
        auditor_registry.print_catalogs()
        return

    if args.auditor_rebuild:
        if args.context_query:
            raise SystemExit("--context-query can only be used with --prompt-file")
        summary = auditor_registry.rebuild_registry(active_only=True)
        print(f"Rebuilt {summary['count']} auditor(s) into {summary['db']}")
        for catalog, count in sorted(summary["catalogs"].items()):
            print(f"- {catalog}: {count}")
        return

    if args.prompt_file:
        if args.record_assessment:
            raise SystemExit("--record-assessment can only be used with --audit")
        enrich_prompt(args.prompt_file, root_path(args.root), context_query=args.context_query, prompt_kind=args.prompt_kind)
        return

    root = root_path(args.root)
    if args.context_query:
        raise SystemExit("--context-query can only be used with --prompt-file")
    if args.audit:
        if not args.record_assessment:
            raise SystemExit("--audit requires --record-assessment")
        record_assessment(args.audit, args.record_assessment, root)
        return
    if args.record_assessment:
        raise SystemExit("--record-assessment can only be used with --audit")
    if args.audit_sync:
        payloads = workspace_db.sync_audits(root)
        print(f"Refreshed {len(payloads)} audit record(s) in {workspace_db.DB_FILE}")
        return
    if args.audit_list:
        for payload in workspace_db.list_audits(root)[: max(1, args.limit)]:
            print(render_audit_row(payload))
        return
    if args.audit_show:
        payload = workspace_db.get_audit(root, args.audit_show)
        if not payload:
            raise SystemExit(f"Audit not found: {args.audit_show}")
        print_audit_detail(payload)
        return
    if args.audit_search:
        rows = workspace_db.semantic_search_audits(root, args.audit_search, args.limit)
        if not rows:
            print("No matching audits.")
            return
        for score, payload in rows:
            print(f"{score:.6f} {render_audit_row(payload)}")
        return

    if args.list:
        list_auditors(auditor_registry.list_auditors(catalog=args.catalog))
    elif args.filter:
        matches = auditor_registry.filter_auditors(None, args.filter, catalog=args.catalog, limit=args.limit)
        if not matches:
            print("No matching auditors.")
            return
        list_auditors(matches)
    elif args.show:
        auditor = auditor_registry.show_auditor(None, args.show, catalog=args.catalog)
        if auditor is None:
            raise SystemExit(f"Auditor not found: {args.show}")
        print(auditor_registry.markdown_for_output(auditor), end="")


if __name__ == "__main__":
    main()
