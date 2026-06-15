#!/usr/bin/env python3
"""Enrich MaxTAC debate prompts and combine debate ballots."""

from __future__ import annotations

import argparse
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def generated_id(prefix: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{timestamp}-{secrets.token_hex(3)}"


def read_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def enrich_prompt(prompt_file: Path) -> None:
    raw_prompt = read_text(prompt_file).rstrip()
    debate_id = generated_id("debate")
    debate_dir = Path.cwd() / "debates" / debate_id
    debate_dir.mkdir(parents=True, exist_ok=False)

    prompt_path = debate_dir / "prompt.md"
    enriched = f"""{raw_prompt}

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
    print(enriched, end="")


def load_ballot(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return payload


def ballot_value(ballot: dict[str, Any], key: str, default: str = "") -> str:
    value = ballot.get(key, default)
    if value is None:
        return ""
    return str(value)


def tally(debate_id: str) -> None:
    debate_dir = Path.cwd() / "debates" / debate_id
    if not debate_dir.exists():
        raise SystemExit(f"Debate not found: {debate_id}")

    ballots = sorted(debate_dir.glob("ballot-*.json"))
    if not ballots:
        raise SystemExit(f"No ballots found for debate: {debate_id}")

    print(f"# Debate Tally Review: {debate_id}")
    print()
    print(f"- Debate directory: `{debate_dir}`")
    print(f"- Ballots: {len(ballots)}")

    counts: dict[str, int] = {}
    loaded: list[tuple[Path, dict[str, Any]]] = []
    for path in ballots:
        ballot = load_ballot(path)
        choice = ballot_value(ballot, "choice", "unknown").lower()
        counts[choice] = counts.get(choice, 0) + 1
        loaded.append((path, ballot))

    for choice in sorted(counts):
        print(f"- {choice}: {counts[choice]}")
    print()

    for path, ballot in loaded:
        subagent = ballot_value(ballot, "subagent", path.stem.removeprefix("ballot-"))
        choice = ballot_value(ballot, "choice", "unknown")
        confidence = ballot_value(ballot, "confidence", "unknown")
        print(f"## {subagent}")
        print()
        print(f"- Ballot file: `{path}`")
        print(f"- Choice: {choice}")
        print(f"- Confidence: {confidence}")
        print()
        print("### Reasoning")
        print()
        print(ballot_value(ballot, "reasoning", ""))
        print()
        print("### Evidence")
        print()
        print(ballot_value(ballot, "evidence", ""))
        blockers = ballot.get("blockers")
        if blockers:
            print()
            print("### Blockers")
            print()
            print(str(blockers))
        print()


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC debate helper")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt-file", type=Path, help="Enrich a persisted debate prompt")
    group.add_argument("--debate", help="Debate ID to review")
    parser.add_argument("--tally", action="store_true", help="Combine ballots for review")
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()

    if args.prompt_file:
        if args.tally:
            raise SystemExit("--tally can only be used with --debate")
        enrich_prompt(args.prompt_file)
        return

    if args.debate:
        if not args.tally:
            raise SystemExit("--debate requires --tally")
        tally(args.debate)


if __name__ == "__main__":
    main()
