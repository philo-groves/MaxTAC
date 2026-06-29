#!/usr/bin/env python3
"""List MaxTAC auditors and enrich auditor subagent prompts."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
AUDITORS_FILE = SKILL_DIR / "references" / "auditors.json"
LEDGER_SCRIPTS_DIR = SKILL_DIR.parent / "maxtac-core-ledger" / "scripts"
sys.path.insert(0, str(LEDGER_SCRIPTS_DIR))

import workspace_db  # noqa: E402


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


def auditors_payload() -> Any:
    if not AUDITORS_FILE.exists():
        raise SystemExit(f"Auditor data file not found: {AUDITORS_FILE}")
    raw = AUDITORS_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        raise SystemExit(f"No auditors found in {AUDITORS_FILE}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{AUDITORS_FILE} is not valid JSON: {exc}") from exc


def normalize_auditor(auditor_id: str, auditor: Any) -> dict[str, Any]:
    if isinstance(auditor, str):
        return {"id": auditor_id, "name": auditor_id, "markdown": auditor}
    if not isinstance(auditor, dict):
        raise SystemExit(f"Auditor {auditor_id} must be an object or markdown string")
    result = dict(auditor)
    result.setdefault("id", auditor_id)
    result.setdefault("name", result["id"])
    return result


def list_item_id(index: int, item: Any) -> str:
    if isinstance(item, dict) and item.get("id"):
        return str(item["id"])
    return f"auditor-{index + 1}"


def load_auditors() -> list[dict[str, Any]]:
    payload = auditors_payload()
    if isinstance(payload, dict):
        if isinstance(payload.get("auditors"), list):
            auditors = [
                normalize_auditor(list_item_id(index, item), item)
                for index, item in enumerate(payload["auditors"])
            ]
        else:
            auditors = [normalize_auditor(str(key), value) for key, value in payload.items()]
    elif isinstance(payload, list):
        auditors = [
            normalize_auditor(list_item_id(index, item), item)
            for index, item in enumerate(payload)
        ]
    else:
        raise SystemExit(f"{AUDITORS_FILE} must contain a JSON list or object")

    if not auditors:
        raise SystemExit(f"No auditors found in {AUDITORS_FILE}")
    return sorted(auditors, key=lambda auditor: str(auditor.get("id", "")))


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


def enrich_prompt(prompt_file: Path, root: Path) -> None:
    prompt_path_input = workspace_path(root, prompt_file, "Prompt file")
    raw_prompt = read_text(prompt_path_input).rstrip()
    audit_id = generated_id("audit")
    audit_dir = root / "audits" / audit_id
    audit_dir.mkdir(parents=True, exist_ok=False)

    assessment_path = audit_dir / "assessment.md"
    prompt_path = audit_dir / "prompt.md"
    goal_objective = (
        "Produce a focused MaxTAC audit assessment for the supplied hypothesis, auditor specialty, and evidence, "
        f"then persist it to {assessment_path}. Negative end outcome: if the supplied context, directly referenced "
        "files, or available tools are insufficient to decide the hypothesis within a bounded pass, stop broadening "
        "scope and persist an assessment with blockers, missing evidence, and the safest recommended next step."
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

## Audit Task

{raw_prompt}

---

## MaxTAC Audit Persistence Instructions

Audit ID: `{audit_id}`
Audit directory: `{audit_dir}`

Persist the final audit assessment to `{assessment_path}` before completing the subagent run. Use Markdown. Include a `Goal Activation` section naming `create_goal`, `/goal`, or `unavailable`; then include the vulnerability hypothesis or audit focus, method, reviewed files or components, findings, evidence, exploitability notes, blockers, and a clear conclusion. Persist supporting evidence files in the same audit directory when useful.
"""
    prompt_path.write_text(enriched, encoding="utf-8")
    workspace_db.sync_audits(root, audit_id)
    print(enriched, end="")


def one_line(value: Any, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def render_audit_row(payload: dict[str, Any]) -> str:
    status = "assessed" if payload.get("assessment_path") else "prompt-only"
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
    print(f"- directory: {payload.get('audit_dir', '')}")
    print(f"- prompt: {payload.get('prompt_path', '')}")
    print(f"- assessment: {payload.get('assessment_path', '') or 'missing'}")
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


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC auditor helper")
    parser.add_argument("--root", default=".", help="Workspace root; prompt files should be staged under tmp/")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List condensed auditor information")
    group.add_argument("--filter", metavar="TEXT", help="Filter auditors by text")
    group.add_argument("--show", metavar="AUDITOR_ID", help="Show full auditor markdown")
    group.add_argument("--prompt-file", type=Path, help="Enrich a persisted audit prompt")
    group.add_argument("--audit-sync", action="store_true", help="Sync all audit artifacts into workspace.sqlite")
    group.add_argument("--audit-list", action="store_true", help="List synced audit assessments")
    group.add_argument("--audit-show", metavar="AUDIT_ID", help="Show synced audit details")
    group.add_argument("--audit-search", metavar="TEXT", help="Semantic search audit prompts, assessments, and artifacts")
    parser.add_argument("--limit", type=int, default=10, help="Maximum rows for audit list or search output")
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()

    if args.prompt_file:
        enrich_prompt(args.prompt_file, root_path(args.root))
        return

    root = root_path(args.root)
    if args.audit_sync:
        payloads = workspace_db.sync_audits(root)
        print(f"Synced {len(payloads)} audit(s) into {workspace_db.DB_FILE}")
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
            if payload.get("assessment_path"):
                print(f"  assessment={payload.get('assessment_path')}")
            else:
                print(f"  prompt={payload.get('prompt_path', '')}")
        return

    auditors = load_auditors()
    if args.list:
        list_auditors(auditors)
    elif args.filter:
        filter_auditors(auditors, args.filter)
    elif args.show:
        show_auditor(auditors, args.show)


if __name__ == "__main__":
    main()
