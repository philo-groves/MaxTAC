#!/usr/bin/env python3
"""Maintain a compact MaxTAC finding ledger."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback.
    fcntl = None


DEFAULT_LEDGER = Path("data/maxtac/findings.json")
STATES = {"discovered", "triage-ready", "confident", "proofed", "duplicate", "de-escalated"}
DOMAINS = {
    "apple-intelligence",
    "boot-chain",
    "comms",
    "icloud",
    "kernel",
    "private-cloud-compute",
    "radios",
    "sandbox",
    "webkit",
}
LOCK_TIMEOUT_SECONDS = 120.0


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokens(*values: Any) -> set[str]:
    text = " ".join(str(value or "") for value in values)
    return {part for part in re.split(r"[^a-zA-Z0-9_+-]+", text.lower()) if len(part) > 2}


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "findings": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("findings"), list):
        raise SystemExit(f"{path} is not a MaxTAC findings ledger")
    return payload


def save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(ledger, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@contextmanager
def ledger_lock(path: Path, exclusive: bool) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    if fcntl is not None:
        with lock_path.open("a+", encoding="utf-8") as handle:
            mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(handle.fileno(), mode)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return

    lock_dir = Path(f"{lock_path}.d")
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    while True:
        try:
            lock_dir.mkdir()
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise SystemExit(f"Timed out waiting for ledger lock: {lock_dir}")
            time.sleep(0.1)
    try:
        yield
    finally:
        lock_dir.rmdir()


@contextmanager
def open_ledger(path: Path, write: bool = False) -> Iterator[dict[str, Any]]:
    with ledger_lock(path, exclusive=write):
        ledger = load_ledger(path)
        yield ledger
        if write:
            save_ledger(path, ledger)


def next_id(findings: list[dict[str, Any]]) -> str:
    highest = 0
    for finding in findings:
        match = re.fullmatch(r"M-(\d{4})", str(finding.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"M-{highest + 1:04d}"


def parse_multi(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        for item in value.split(","):
            item = item.strip()
            if item and item not in result:
                result.append(item)
    return result


def finding_text(finding: dict[str, Any]) -> set[str]:
    return tokens(
        finding.get("title"),
        finding.get("domain"),
        finding.get("target"),
        finding.get("category"),
        " ".join(finding.get("locations", [])),
        finding.get("summary"),
        " ".join(finding.get("evidence", [])),
    )


def search_findings(ledger: dict[str, Any], query: argparse.Namespace) -> list[tuple[int, dict[str, Any]]]:
    query_tokens = tokens(query.title, query.target, query.category, " ".join(parse_multi(query.location)), query.evidence)
    query_domain = getattr(query, "domain", None)
    if not query_tokens and not query_domain:
        return []
    results: list[tuple[int, dict[str, Any]]] = []
    for finding in ledger["findings"]:
        if query_domain and finding.get("domain") != query_domain:
            continue
        overlap = query_tokens & finding_text(finding)
        if overlap or not query_tokens:
            results.append((len(overlap), finding))
    results.sort(key=lambda item: (item[0], item[1].get("id", "")), reverse=True)
    return results


def duplicate_query(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        title=args.title,
        target=args.target,
        category=args.category,
        location=args.location,
        evidence=",".join(parse_multi(args.evidence)),
        domain=None,
    )


def cmd_init(args: argparse.Namespace) -> None:
    path = Path(args.file)
    with ledger_lock(path, exclusive=True):
        if path.exists() and not args.force:
            print(f"Ledger already exists: {path}")
            return
        save_ledger(path, {"version": 1, "findings": []})
    print(f"Initialized {path}")


def cmd_summary(args: argparse.Namespace) -> None:
    with open_ledger(Path(args.file)) as ledger:
        findings = [
            finding
            for finding in ledger["findings"]
            if not args.domain or finding.get("domain") == args.domain
        ]
    counts = {state: 0 for state in sorted(STATES)}
    for finding in findings:
        counts[finding.get("state", "unknown")] = counts.get(finding.get("state", "unknown"), 0) + 1
    print("MaxTAC finding ledger summary")
    if args.domain:
        print(f"Domain: {args.domain}")
    for state, count in counts.items():
        if count:
            print(f"- {state}: {count}")
    active = [f for f in findings if f.get("state") not in {"duplicate", "de-escalated"}]
    for finding in active:
        domain = f" domain={finding.get('domain')}" if finding.get("domain") else ""
        print(f"- {finding['id']} {finding.get('state')}{domain}: {finding.get('title')}")


def cmd_search(args: argparse.Namespace) -> None:
    with open_ledger(Path(args.file)) as ledger:
        results = search_findings(ledger, args)
    if not results:
        print("No likely matches.")
        return
    for score, finding in results[: args.limit]:
        domain = finding.get("domain") or "-"
        print(
            f"{finding['id']} score={score} state={finding.get('state')} "
            f"domain={domain} title={finding.get('title')}"
        )


def cmd_add(args: argparse.Namespace) -> None:
    path = Path(args.file)
    with open_ledger(path, write=True) as ledger:
        duplicates = search_findings(ledger, duplicate_query(args))
        if duplicates and not args.allow_duplicate:
            score, finding = duplicates[0]
            domain = finding.get("domain") or "-"
            raise SystemExit(
                f"Likely duplicate: {finding['id']} score={score} domain={domain} "
                f"title={finding.get('title')}. Use --allow-duplicate if materially different."
            )

        timestamp = now()
        finding = {
            "id": next_id(ledger["findings"]),
            "title": args.title,
            "domain": args.domain,
            "target": args.target,
            "category": args.category,
            "locations": parse_multi(args.location),
            "summary": args.summary,
            "evidence": parse_multi(args.evidence),
            "state": args.state,
            "related": parse_multi(args.related),
            "milestones": [
                {
                    "time": timestamp,
                    "note": args.note or "Finding added.",
                }
            ],
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        ledger["findings"].append(finding)
    print(f"Added {finding['id']} {finding['state']}: {finding['title']}")


def find_by_id(ledger: dict[str, Any], finding_id: str) -> dict[str, Any]:
    for finding in ledger["findings"]:
        if finding.get("id") == finding_id:
            return finding
    raise SystemExit(f"Finding not found: {finding_id}")


def cmd_update(args: argparse.Namespace) -> None:
    path = Path(args.file)
    with open_ledger(path, write=True) as ledger:
        finding = find_by_id(ledger, args.finding_id)
        if args.state:
            finding["state"] = args.state
        if args.domain:
            finding["domain"] = args.domain
        if args.clear_domain:
            finding["domain"] = None
        if args.title:
            finding["title"] = args.title
        if args.target:
            finding["target"] = args.target
        if args.category:
            finding["category"] = args.category
        if args.location:
            finding["locations"] = parse_multi(args.location)
        if args.summary:
            finding["summary"] = args.summary
        if args.evidence:
            finding["evidence"] = parse_multi(args.evidence)
        if args.related:
            finding["related"] = parse_multi(args.related)
        if args.note:
            finding.setdefault("milestones", []).append({"time": now(), "note": args.note})
        finding["updated_at"] = now()
    print(f"Updated {finding['id']} {finding.get('state')}: {finding.get('title')}")


def cmd_milestone(args: argparse.Namespace) -> None:
    path = Path(args.file)
    with open_ledger(path, write=True) as ledger:
        finding = find_by_id(ledger, args.finding_id)
        finding.setdefault("milestones", []).append({"time": now(), "note": args.note})
        finding["updated_at"] = now()
    print(f"Added milestone to {finding['id']}: {args.note}")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC finding ledger")
    parser.add_argument("--file", default=str(DEFAULT_LEDGER))
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    summary = subparsers.add_parser("summary")
    summary.add_argument("--domain", choices=sorted(DOMAINS))
    summary.set_defaults(func=cmd_summary)

    search = subparsers.add_parser("search")
    add_query_args(search)
    search.add_argument("--limit", type=int, default=10)
    search.set_defaults(func=cmd_search)

    add = subparsers.add_parser("add")
    add_required_finding_args(add)
    add.add_argument("--state", choices=sorted(STATES), default="discovered")
    add.add_argument("--allow-duplicate", action="store_true")
    add.add_argument("--note")
    add.set_defaults(func=cmd_add)

    update = subparsers.add_parser("update")
    update.add_argument("finding_id")
    update.add_argument("--state", choices=sorted(STATES))
    update.add_argument("--domain", choices=sorted(DOMAINS))
    update.add_argument("--clear-domain", action="store_true")
    update.add_argument("--title")
    update.add_argument("--target")
    update.add_argument("--category")
    update.add_argument("--location", action="append")
    update.add_argument("--summary")
    update.add_argument("--evidence", action="append")
    update.add_argument("--related", action="append")
    update.add_argument("--note")
    update.set_defaults(func=cmd_update)

    milestone = subparsers.add_parser("milestone")
    milestone.add_argument("finding_id")
    milestone.add_argument("--note", required=True)
    milestone.set_defaults(func=cmd_milestone)
    return parser


def add_query_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title")
    parser.add_argument("--domain", choices=sorted(DOMAINS))
    parser.add_argument("--target")
    parser.add_argument("--category")
    parser.add_argument("--location", action="append")
    parser.add_argument("--evidence")


def add_required_finding_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", required=True)
    parser.add_argument("--domain", choices=sorted(DOMAINS))
    parser.add_argument("--target", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--location", action="append")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--evidence", action="append", required=True)
    parser.add_argument("--related", action="append")


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
