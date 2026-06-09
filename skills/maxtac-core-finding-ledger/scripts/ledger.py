#!/usr/bin/env python3
"""Maintain MaxTAC primitive and chain ledgers."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEDGER_FILES = {
    "primitive": Path("data/maxtac/primitives.json"),
    "chain": Path("data/maxtac/chains.json"),
}
TYPE_CHOICES = tuple(LEDGER_FILES)
TYPE_OR_ALL = (*TYPE_CHOICES, "all")
STATES = {
    "discovered",
    "confident",
    "validated",
    "proofed",
    "duplicate",
    "stalled",
    "de-escalated",
}
TERMINAL_STATES = {"duplicate", "de-escalated"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokens(*values: Any) -> set[str]:
    text = " ".join(str(value or "") for value in values)
    return {part for part in re.split(r"[^a-zA-Z0-9_+-]+", text.lower()) if len(part) > 2}


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def parse_csv(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        for item in value.split(","):
            item = item.strip()
            if item:
                result.append(item)
    return unique(result)


def parse_repeated(values: list[str] | None) -> list[str]:
    return unique([(value or "").strip() for value in values or [] if (value or "").strip()])


def load_ledger(path: Path, ledger_type: str) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "type": ledger_type, "findings": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("findings"), list):
        raise SystemExit(f"{path} is not a MaxTAC findings ledger")
    payload.setdefault("version", 1)
    payload.setdefault("type", ledger_type)
    return payload


def save_ledger(path: Path, ledger: dict[str, Any], ledger_type: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ledger["type"] = ledger_type
    path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")


def selected_types(selection: str) -> list[str]:
    if selection == "all":
        return list(TYPE_CHOICES)
    return [selection]


def selected_ledgers(args: argparse.Namespace, *, allow_all: bool, default_type: str = "primitive") -> list[tuple[str, Path]]:
    raw_selection = getattr(args, "type", None)
    if args.file:
        if raw_selection == "all":
            raise SystemExit("--file requires --type primitive or --type chain")
        return [(raw_selection or default_type, Path(args.file))]
    selection = raw_selection or ("all" if allow_all else default_type)
    if selection == "all" and not allow_all:
        raise SystemExit("--type all is not valid for this command")
    return [(ledger_type, LEDGER_FILES[ledger_type]) for ledger_type in selected_types(selection)]


def next_id(findings: list[dict[str, Any]]) -> str:
    highest = 0
    for finding in findings:
        match = re.fullmatch(r"[A-Z]?-(\d{4})", str(finding.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"M-{highest + 1:04d}"


def finding_text(finding: dict[str, Any]) -> set[str]:
    return tokens(
        finding.get("id"),
        finding.get("type"),
        finding.get("title"),
        finding.get("target"),
        finding.get("category"),
        " ".join(finding.get("locations", [])),
        finding.get("summary"),
        " ".join(finding.get("evidence", [])),
        " ".join(finding.get("related", [])),
        " ".join(finding.get("primitives", [])),
    )


def search_findings(ledger: dict[str, Any], query: argparse.Namespace) -> list[tuple[int, dict[str, Any]]]:
    query_tokens = tokens(
        query.title,
        query.target,
        query.category,
        " ".join(parse_csv(query.location)),
        query.evidence,
        " ".join(parse_csv(getattr(query, "related", None))),
    )
    if not query_tokens:
        return []
    results: list[tuple[int, dict[str, Any]]] = []
    for finding in ledger["findings"]:
        overlap = query_tokens & finding_text(finding)
        if overlap:
            results.append((len(overlap), finding))
    results.sort(key=lambda item: (item[0], item[1].get("id", "")), reverse=True)
    return results


def format_finding(ledger_type: str, finding: dict[str, Any], *, score: int | None = None) -> str:
    score_text = f" score={score}" if score is not None else ""
    return f"{ledger_type}:{finding['id']}{score_text} {finding.get('state')}: {finding.get('title')}"


def cmd_init(args: argparse.Namespace) -> None:
    for ledger_type, path in selected_ledgers(args, allow_all=True):
        if path.exists() and not args.force:
            print(f"Ledger already exists: {path}")
            continue
        save_ledger(path, {"version": 1, "type": ledger_type, "findings": []}, ledger_type)
        print(f"Initialized {ledger_type} ledger: {path}")


def cmd_summary(args: argparse.Namespace) -> None:
    for ledger_type, path in selected_ledgers(args, allow_all=True):
        ledger = load_ledger(path, ledger_type)
        counts = {state: 0 for state in sorted(STATES)}
        for finding in ledger["findings"]:
            state = finding.get("state", "unknown")
            counts[state] = counts.get(state, 0) + 1
        print(f"MaxTAC {ledger_type} ledger summary ({path})")
        for state, count in counts.items():
            if count:
                print(f"- {state}: {count}")
        active = [f for f in ledger["findings"] if f.get("state") not in TERMINAL_STATES]
        for finding in active:
            print(f"- {format_finding(ledger_type, finding)}")


def cmd_list(args: argparse.Namespace) -> None:
    printed = False
    for ledger_type, path in selected_ledgers(args, allow_all=True):
        ledger = load_ledger(path, ledger_type)
        findings = ledger["findings"]
        if args.state:
            findings = [finding for finding in findings if finding.get("state") == args.state]
        for finding in findings[: args.limit or None]:
            print(format_finding(ledger_type, finding))
            printed = True
    if not printed:
        print("No findings.")


def cmd_search(args: argparse.Namespace) -> None:
    printed = False
    for ledger_type, path in selected_ledgers(args, allow_all=True):
        ledger = load_ledger(path, ledger_type)
        results = search_findings(ledger, args)
        for score, finding in results[: args.limit]:
            print(format_finding(ledger_type, finding, score=score))
            printed = True
    if not printed:
        print("No likely matches.")


def cmd_add(args: argparse.Namespace) -> None:
    ledger_type, path = selected_ledgers(args, allow_all=False)[0]
    ledger = load_ledger(path, ledger_type)
    duplicates = search_findings(ledger, args)
    if duplicates and not args.allow_duplicate:
        score, finding = duplicates[0]
        raise SystemExit(
            f"Likely duplicate in {ledger_type} ledger: {finding['id']} score={score} "
            f"title={finding.get('title')}. Use --allow-duplicate if materially different."
        )

    timestamp = now()
    primitive_refs = parse_csv(getattr(args, "primitive", None))
    related = unique(parse_csv(args.related) + primitive_refs)
    finding = {
        "id": next_id(ledger["findings"]),
        "type": ledger_type,
        "title": args.title,
        "target": args.target,
        "category": args.category,
        "locations": parse_csv(args.location),
        "summary": args.summary,
        "evidence": parse_repeated(args.evidence),
        "state": args.state,
        "related": related,
        "milestones": [
            {
                "time": timestamp,
                "note": args.note or "Finding added.",
            }
        ],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    if ledger_type == "chain":
        finding["primitives"] = primitive_refs
    ledger["findings"].append(finding)
    save_ledger(path, ledger, ledger_type)
    print(f"Added {format_finding(ledger_type, finding)}")


def find_matches(args: argparse.Namespace, finding_id: str) -> list[tuple[str, Path, dict[str, Any], dict[str, Any]]]:
    matches: list[tuple[str, Path, dict[str, Any], dict[str, Any]]] = []
    for ledger_type, path in selected_ledgers(args, allow_all=True):
        ledger = load_ledger(path, ledger_type)
        for finding in ledger["findings"]:
            if finding.get("id") == finding_id:
                matches.append((ledger_type, path, ledger, finding))
    return matches


def one_finding_match(args: argparse.Namespace, finding_id: str) -> tuple[str, Path, dict[str, Any], dict[str, Any]]:
    matches = find_matches(args, finding_id)
    if not matches:
        raise SystemExit(f"Finding not found: {finding_id}")
    if len(matches) > 1:
        locations = ", ".join(f"{ledger_type}:{path}" for ledger_type, path, _, _ in matches)
        raise SystemExit(f"Finding id {finding_id} exists in multiple ledgers ({locations}); pass --type.")
    return matches[0]


def cmd_update(args: argparse.Namespace) -> None:
    ledger_type, path, ledger, finding = one_finding_match(args, args.finding_id)
    if args.state:
        finding["state"] = args.state
    if args.title:
        finding["title"] = args.title
    if args.target:
        finding["target"] = args.target
    if args.category:
        finding["category"] = args.category
    if args.location is not None:
        finding["locations"] = parse_csv(args.location)
    if args.summary:
        finding["summary"] = args.summary
    if args.evidence is not None:
        finding["evidence"] = parse_repeated(args.evidence)
    if args.related is not None:
        finding["related"] = parse_csv(args.related)
    if getattr(args, "primitive", None) is not None:
        finding["primitives"] = parse_csv(args.primitive)
        finding["related"] = unique(finding.get("related", []) + finding["primitives"])
    if args.note:
        finding.setdefault("milestones", []).append({"time": now(), "note": args.note})
    finding["type"] = ledger_type
    finding["updated_at"] = now()
    save_ledger(path, ledger, ledger_type)
    print(f"Updated {format_finding(ledger_type, finding)}")


def cmd_milestone(args: argparse.Namespace) -> None:
    ledger_type, path, ledger, finding = one_finding_match(args, args.finding_id)
    finding.setdefault("milestones", []).append({"time": now(), "note": args.note})
    finding["updated_at"] = now()
    save_ledger(path, ledger, ledger_type)
    print(f"Added milestone to {ledger_type}:{finding['id']}: {args.note}")


def add_type_arg(parser: argparse.ArgumentParser, *, allow_all: bool, default: str | None) -> None:
    parser.add_argument("--type", choices=TYPE_OR_ALL if allow_all else TYPE_CHOICES, default=default)


def add_query_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title")
    parser.add_argument("--target")
    parser.add_argument("--category")
    parser.add_argument("--location", action="append")
    parser.add_argument("--evidence")
    parser.add_argument("--related", action="append")


def add_required_finding_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--location", action="append")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--evidence", action="append", required=True)
    parser.add_argument("--related", action="append")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC primitive and chain ledger")
    parser.add_argument("--file", help="Override the default ledger path for the selected --type")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    add_type_arg(init, allow_all=True, default=None)
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    summary = subparsers.add_parser("summary")
    add_type_arg(summary, allow_all=True, default=None)
    summary.set_defaults(func=cmd_summary)

    list_cmd = subparsers.add_parser("list")
    add_type_arg(list_cmd, allow_all=True, default=None)
    list_cmd.add_argument("--state", choices=sorted(STATES))
    list_cmd.add_argument("--limit", type=int, default=0)
    list_cmd.set_defaults(func=cmd_list)

    search = subparsers.add_parser("search")
    add_type_arg(search, allow_all=True, default=None)
    add_query_args(search)
    search.add_argument("--limit", type=int, default=10)
    search.set_defaults(func=cmd_search)

    add = subparsers.add_parser("add")
    add_type_arg(add, allow_all=False, default="primitive")
    add_required_finding_args(add)
    add.add_argument("--primitive", action="append", help="Primitive id used by this chain")
    add.add_argument("--state", choices=sorted(STATES), default="discovered")
    add.add_argument("--allow-duplicate", action="store_true")
    add.add_argument("--note")
    add.set_defaults(func=cmd_add)

    update = subparsers.add_parser("update")
    add_type_arg(update, allow_all=True, default=None)
    update.add_argument("finding_id")
    update.add_argument("--state", choices=sorted(STATES))
    update.add_argument("--title")
    update.add_argument("--target")
    update.add_argument("--category")
    update.add_argument("--location", action="append")
    update.add_argument("--summary")
    update.add_argument("--evidence", action="append")
    update.add_argument("--related", action="append")
    update.add_argument("--primitive", action="append", help="Primitive id used by this chain")
    update.add_argument("--note")
    update.set_defaults(func=cmd_update)

    milestone = subparsers.add_parser("milestone")
    add_type_arg(milestone, allow_all=True, default=None)
    milestone.add_argument("finding_id")
    milestone.add_argument("--note", required=True)
    milestone.set_defaults(func=cmd_milestone)
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
