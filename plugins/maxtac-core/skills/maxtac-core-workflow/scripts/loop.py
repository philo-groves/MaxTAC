#!/usr/bin/env python3
"""Manage MaxTAC loop state and prioritized loop worklists."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any


DOCUMENT_TYPE = "maxtac.loop_state"
SCHEMA_VERSION = "1.0"
ITEM_STATUSES = (
    "open",
    "in_progress",
    "blocked",
    "deferred",
    "needs_follow_up",
    "closed",
    "reported",
    "rejected",
    "not_applicable",
)
LOOP_STATUSES = ("active", "blocked", "complete", "superseded")
TERMINAL_STATUSES = {"closed", "reported", "rejected", "not_applicable"}
ACTIVE_STATUSES = {"open", "in_progress", "needs_follow_up"}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slug(value: str, default: str = "loop") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._").lower()
    return cleaned or default


def parse_repeated(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        for item in str(value).split(","):
            stripped = item.strip()
            if stripped and stripped not in result:
                result.append(stripped)
    return result


def root_path(value: str | None) -> Path:
    root = Path(value or ".").expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"workspace root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"workspace root is not a directory: {root}")
    return root


def loop_dir(root: Path, loop_id: str) -> Path:
    return root / "contracts" / "loops" / slug(loop_id)


def loop_json_path(root: Path, loop_id: str) -> Path:
    return loop_dir(root, loop_id) / "loop.json"


def items_path(loop_path: Path) -> Path:
    return loop_path.parent / "items.jsonl"


def events_path(loop_path: Path) -> Path:
    return loop_path.parent / "events.jsonl"


def prompt_path(loop_path: Path) -> Path:
    return loop_path.parent / "next-prompt.md"


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(row, dict):
            raise SystemExit(f"{path}:{line_number}: expected object row")
        rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def load_loop(root: Path, loop_id: str) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
    path = loop_json_path(root, loop_id)
    payload = read_json(path)
    items = read_jsonl(items_path(path))
    return path, payload, items


def update_timestamp(loop_path: Path, payload: dict[str, Any]) -> None:
    payload["updated_at"] = now()
    write_json(loop_path, payload)


def next_item_id(items: list[dict[str, Any]], prefix: str = "item") -> str:
    highest = 0
    pattern = re.compile(rf"{re.escape(prefix)}-(\d+)$")
    for item in items:
        match = pattern.fullmatch(str(item.get("item_id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:04d}"


def normalize_priority(value: str | int | None) -> int:
    try:
        priority = int(value or 3)
    except ValueError as exc:
        raise SystemExit(f"priority must be an integer 1-5: {value}") from exc
    if priority < 1 or priority > 5:
        raise SystemExit("priority must be between 1 and 5")
    return priority


def merge_unique(existing: list[str], additions: list[str]) -> list[str]:
    result = [str(value) for value in existing if str(value).strip()]
    for value in additions:
        if value and value not in result:
            result.append(value)
    return result


def ensure_item_fields(item: dict[str, Any]) -> dict[str, Any]:
    item.setdefault("item_id", "")
    item.setdefault("title", "")
    item.setdefault("kind", "")
    item.setdefault("status", "open")
    item.setdefault("priority", 3)
    item.setdefault("sensitivity", "medium")
    item.setdefault("target_refs", [])
    item.setdefault("model_refs", [])
    item.setdefault("ledger_refs", [])
    item.setdefault("corpus_refs", [])
    item.setdefault("contract_refs", [])
    item.setdefault("evidence", [])
    item.setdefault("blockers", [])
    item.setdefault("notes", "")
    item.setdefault("created_at", now())
    item.setdefault("updated_at", now())
    return item


def validate_loop_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("document_type") != DOCUMENT_TYPE:
        errors.append(f"document_type must be {DOCUMENT_TYPE}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    for key in ("loop_id", "kind", "owner_plugin", "target", "scope", "summary"):
        if not str(payload.get(key, "")).strip():
            errors.append(f"{key} is required")
    if payload.get("status") not in LOOP_STATUSES:
        errors.append(f"status must be one of {', '.join(LOOP_STATUSES)}")
    for key in ("setup", "positive_gates", "negative_gates", "safety_constraints"):
        if not isinstance(payload.get(key), list):
            errors.append(f"{key} must be an array")
    if not payload.get("positive_gates"):
        errors.append("at least one positive gate is required")
    if not payload.get("negative_gates"):
        errors.append("at least one negative gate is required")
    return errors


def validate_items(items: list[dict[str, Any]], *, require_complete: bool = False) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, raw in enumerate(items):
        item = ensure_item_fields(raw)
        where = f"items[{index}]"
        item_id = str(item.get("item_id", "")).strip()
        if not item_id:
            errors.append(f"{where}.item_id is required")
        elif item_id in seen:
            errors.append(f"{where}.item_id duplicates {item_id}")
        seen.add(item_id)
        if not str(item.get("title", "")).strip():
            errors.append(f"{where}.title is required")
        if item.get("status") not in ITEM_STATUSES:
            errors.append(f"{where}.status must be one of {', '.join(ITEM_STATUSES)}")
        priority = item.get("priority")
        if not isinstance(priority, int) or priority < 1 or priority > 5:
            errors.append(f"{where}.priority must be an integer 1-5")
        for key in ("target_refs", "model_refs", "ledger_refs", "corpus_refs", "contract_refs", "evidence", "blockers"):
            if not isinstance(item.get(key), list):
                errors.append(f"{where}.{key} must be an array")
        if item.get("status") in TERMINAL_STATUSES and not item.get("evidence"):
            errors.append(f"{where}: terminal item requires evidence")
        if item.get("status") in {"blocked", "deferred", "needs_follow_up"} and not item.get("blockers"):
            errors.append(f"{where}: {item.get('status')} item requires blockers")
        if require_complete and item.get("status") in ACTIVE_STATUSES:
            errors.append(f"{where}: item is still active ({item.get('status')})")
    return errors


def cmd_init(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    loop_id = slug(args.loop_id)
    path = loop_json_path(root, loop_id)
    if path.exists() and not args.force:
        raise SystemExit(f"loop already exists: {path}")
    payload = {
        "document_type": DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "loop_id": loop_id,
        "kind": args.kind,
        "owner_plugin": args.owner_plugin,
        "target": args.target,
        "scope": args.scope,
        "summary": args.summary,
        "status": "active",
        "created_at": now(),
        "updated_at": now(),
        "safety_constraints": parse_repeated(args.safety),
        "setup": parse_repeated(args.setup),
        "positive_gates": parse_repeated(args.positive_gate),
        "negative_gates": parse_repeated(args.negative_gate),
        "outputs": parse_repeated(args.output),
    }
    errors = validate_loop_payload(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    write_json(path, payload)
    write_jsonl(items_path(path), [])
    write_jsonl(events_path(path), [])
    print(path)


def cmd_add_item(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    loop_path, payload, items = load_loop(root, args.loop_id)
    item_id = args.item_id or next_item_id(items, args.prefix)
    if any(str(item.get("item_id")) == item_id for item in items):
        raise SystemExit(f"item already exists: {item_id}")
    timestamp = now()
    item = ensure_item_fields(
        {
            "item_id": item_id,
            "title": args.title,
            "kind": args.kind,
            "status": args.status,
            "priority": normalize_priority(args.priority),
            "sensitivity": args.sensitivity,
            "target_refs": parse_repeated(args.target_ref),
            "model_refs": parse_repeated(args.model_ref),
            "ledger_refs": parse_repeated(args.ledger_ref),
            "corpus_refs": parse_repeated(args.corpus_ref),
            "contract_refs": parse_repeated(args.contract_ref),
            "evidence": parse_repeated(args.evidence),
            "blockers": parse_repeated(args.blocker),
            "notes": args.note or "",
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    errors = validate_items([item])
    if errors:
        raise SystemExit("\n".join(errors))
    items.append(item)
    write_jsonl(items_path(loop_path), items)
    update_timestamp(loop_path, payload)
    append_jsonl(events_path(loop_path), {"time": timestamp, "event": "add-item", "item_id": item_id, "note": args.note or ""})
    print(item_id)


def cmd_update_item(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    loop_path, payload, items = load_loop(root, args.loop_id)
    matches = [item for item in items if str(item.get("item_id")) == args.item_id]
    if len(matches) != 1:
        raise SystemExit(f"item not found: {args.item_id}")
    item = ensure_item_fields(matches[0])
    if args.status:
        item["status"] = args.status
    if args.priority:
        item["priority"] = normalize_priority(args.priority)
    if args.sensitivity:
        item["sensitivity"] = args.sensitivity
    if args.title:
        item["title"] = args.title
    if args.kind:
        item["kind"] = args.kind
    for key, values in (
        ("target_refs", args.target_ref),
        ("model_refs", args.model_ref),
        ("ledger_refs", args.ledger_ref),
        ("corpus_refs", args.corpus_ref),
        ("contract_refs", args.contract_ref),
        ("evidence", args.evidence),
        ("blockers", args.blocker),
    ):
        item[key] = merge_unique(item.get(key) or [], parse_repeated(values))
    if args.note:
        existing = str(item.get("notes") or "").strip()
        item["notes"] = f"{existing}\n{args.note}".strip() if existing else args.note
    item["updated_at"] = now()
    errors = validate_items(items)
    if errors:
        raise SystemExit("\n".join(errors))
    write_jsonl(items_path(loop_path), items)
    update_timestamp(loop_path, payload)
    append_jsonl(
        events_path(loop_path),
        {"time": item["updated_at"], "event": "update-item", "item_id": args.item_id, "status": item.get("status"), "note": args.note or ""},
    )
    print(args.item_id)


def choose_next(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [ensure_item_fields(item) for item in items if item.get("status") in ACTIVE_STATUSES]
    if not candidates:
        candidates = [ensure_item_fields(item) for item in items if item.get("status") == "open"]
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-int(item.get("priority") or 3), item.get("updated_at", ""), item.get("item_id", "")))
    return candidates[0]


def item_summary(item: dict[str, Any]) -> str:
    return (
        f"{item.get('item_id')} p{item.get('priority')} {item.get('status')} "
        f"{item.get('kind')}: {item.get('title')}"
    )


def cmd_next(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    _loop_path, _payload, items = load_loop(root, args.loop_id)
    item = choose_next(items)
    if item is None:
        print("No active loop items.")
        return
    print(item_summary(item))
    if args.json:
        print(json.dumps(item, indent=2))


def render_prompt(payload: dict[str, Any], item: dict[str, Any] | None) -> str:
    lines = [
        "# MaxTAC Loop Next Action",
        "",
        f"- Loop: `{payload['loop_id']}`",
        f"- Kind: `{payload['kind']}`",
        f"- Owner plugin: `{payload['owner_plugin']}`",
        f"- Target: {payload['target']}",
        f"- Scope: {payload['scope']}",
        "",
        "## Positive Gates",
        "",
    ]
    for gate in payload.get("positive_gates") or []:
        lines.append(f"- {gate}")
    lines.extend(["", "## Negative Gates", ""])
    for gate in payload.get("negative_gates") or []:
        lines.append(f"- {gate}")
    lines.extend(["", "## Current Item", ""])
    if item is None:
        lines.append("No active item remains. Validate the loop and close or run false-negative review if the conclusion is broad.")
    else:
        lines.extend(
            [
                f"- Item: `{item.get('item_id')}`",
                f"- Title: {item.get('title')}",
                f"- Kind: {item.get('kind')}",
                f"- Priority: {item.get('priority')}",
                f"- Sensitivity: {item.get('sensitivity')}",
                f"- Status: {item.get('status')}",
                f"- Target refs: {', '.join(item.get('target_refs') or []) or 'none'}",
                f"- Model refs: {', '.join(item.get('model_refs') or []) or 'none'}",
                f"- Evidence: {', '.join(item.get('evidence') or []) or 'none'}",
                "",
                "## Task",
                "",
                "Work only the current item unless new evidence proves the loop worklist is wrong. "
                "Update Core corpus/model/ledger/contracts as warranted, then update this loop item with evidence, blockers, or closure.",
                "",
            ]
        )
    return "\n".join(lines)


def cmd_prompt(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    loop_path, payload, items = load_loop(root, args.loop_id)
    item = choose_next(items)
    text = render_prompt(payload, item)
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = root / output
    else:
        output = prompt_path(loop_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(output)


def cmd_event(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    loop_path, payload, _items = load_loop(root, args.loop_id)
    row = {
        "time": now(),
        "event": args.event,
        "item_id": args.item_id or "",
        "note": args.note,
        "evidence": parse_repeated(args.evidence),
    }
    append_jsonl(events_path(loop_path), row)
    update_timestamp(loop_path, payload)
    print(events_path(loop_path))


def cmd_set_status(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    loop_path, payload, _items = load_loop(root, args.loop_id)
    timestamp = now()
    payload["status"] = args.status
    payload["updated_at"] = timestamp
    errors = validate_loop_payload(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    write_json(loop_path, payload)
    append_jsonl(
        events_path(loop_path),
        {
            "time": timestamp,
            "event": "set-status",
            "status": args.status,
            "note": args.note or "",
            "evidence": parse_repeated(args.evidence),
        },
    )
    print(args.status)


def status_payload(payload: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [ensure_item_fields(item) for item in items]
    counts = Counter(str(item.get("status", "open")) for item in normalized)
    next_item = choose_next(normalized)
    return {
        "loop_id": payload.get("loop_id"),
        "kind": payload.get("kind"),
        "target": payload.get("target"),
        "scope": payload.get("scope"),
        "status": payload.get("status"),
        "item_count": len(normalized),
        "counts": dict(sorted(counts.items())),
        "next_item": next_item,
    }


def cmd_status(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    _loop_path, payload, items = load_loop(root, args.loop_id)
    result = status_payload(payload, items)
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"MaxTAC loop: {result['loop_id']} ({result['kind']})")
    print(f"- target: {result['target']}")
    print(f"- scope: {result['scope']}")
    print(f"- status: {result['status']}")
    print(f"- items: {result['item_count']}")
    for status, count in result["counts"].items():
        print(f"- {status}: {count}")
    if result["next_item"]:
        print(f"- next: {item_summary(result['next_item'])}")
    else:
        print("- next: none")


def cmd_validate(args: argparse.Namespace) -> None:
    root = root_path(args.root)
    loop_path, payload, items = load_loop(root, args.loop_id)
    errors = validate_loop_payload(payload)
    errors.extend(validate_items(items, require_complete=args.require_complete))
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"validated {loop_path}")


def add_ref_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target-ref", action="append")
    parser.add_argument("--model-ref", action="append")
    parser.add_argument("--ledger-ref", action="append")
    parser.add_argument("--corpus-ref", action="append")
    parser.add_argument("--contract-ref", action="append")
    parser.add_argument("--evidence", action="append")
    parser.add_argument("--blocker", action="append")


def main() -> None:
    parser = argparse.ArgumentParser(description="MaxTAC loop-state helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a loop state bundle")
    init.add_argument("--root", default=".")
    init.add_argument("--loop-id", required=True)
    init.add_argument("--kind", required=True)
    init.add_argument("--owner-plugin", required=True)
    init.add_argument("--target", required=True)
    init.add_argument("--scope", required=True)
    init.add_argument("--summary", required=True)
    init.add_argument("--safety", action="append")
    init.add_argument("--setup", action="append")
    init.add_argument("--positive-gate", action="append", required=True)
    init.add_argument("--negative-gate", action="append", required=True)
    init.add_argument("--output", action="append")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    add_item = subparsers.add_parser("add-item", help="Add a loop work item")
    add_item.add_argument("--root", default=".")
    add_item.add_argument("--loop-id", required=True)
    add_item.add_argument("--item-id")
    add_item.add_argument("--prefix", default="item")
    add_item.add_argument("--title", required=True)
    add_item.add_argument("--kind", required=True)
    add_item.add_argument("--status", choices=ITEM_STATUSES, default="open")
    add_item.add_argument("--priority", default="3")
    add_item.add_argument("--sensitivity", default="medium")
    add_item.add_argument("--note")
    add_ref_args(add_item)
    add_item.set_defaults(func=cmd_add_item)

    update_item = subparsers.add_parser("update-item", help="Update a loop work item")
    update_item.add_argument("--root", default=".")
    update_item.add_argument("--loop-id", required=True)
    update_item.add_argument("--item-id", required=True)
    update_item.add_argument("--title")
    update_item.add_argument("--kind")
    update_item.add_argument("--status", choices=ITEM_STATUSES)
    update_item.add_argument("--priority")
    update_item.add_argument("--sensitivity")
    update_item.add_argument("--note")
    add_ref_args(update_item)
    update_item.set_defaults(func=cmd_update_item)

    next_cmd = subparsers.add_parser("next", help="Print the highest-priority active item")
    next_cmd.add_argument("--root", default=".")
    next_cmd.add_argument("--loop-id", required=True)
    next_cmd.add_argument("--json", action="store_true")
    next_cmd.set_defaults(func=cmd_next)

    prompt = subparsers.add_parser("prompt", help="Write a compact next-action prompt")
    prompt.add_argument("--root", default=".")
    prompt.add_argument("--loop-id", required=True)
    prompt.add_argument("--output")
    prompt.set_defaults(func=cmd_prompt)

    event = subparsers.add_parser("event", help="Append a loop event")
    event.add_argument("--root", default=".")
    event.add_argument("--loop-id", required=True)
    event.add_argument("--event", required=True)
    event.add_argument("--item-id")
    event.add_argument("--note", required=True)
    event.add_argument("--evidence", action="append")
    event.set_defaults(func=cmd_event)

    set_status = subparsers.add_parser("set-status", help="Update loop lifecycle status")
    set_status.add_argument("--root", default=".")
    set_status.add_argument("--loop-id", required=True)
    set_status.add_argument("--status", choices=LOOP_STATUSES, required=True)
    set_status.add_argument("--note")
    set_status.add_argument("--evidence", action="append")
    set_status.set_defaults(func=cmd_set_status)

    status = subparsers.add_parser("status", help="Summarize loop state")
    status.add_argument("--root", default=".")
    status.add_argument("--loop-id", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    validate = subparsers.add_parser("validate", help="Validate loop state")
    validate.add_argument("--root", default=".")
    validate.add_argument("--loop-id", required=True)
    validate.add_argument("--require-complete", action="store_true")
    validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
