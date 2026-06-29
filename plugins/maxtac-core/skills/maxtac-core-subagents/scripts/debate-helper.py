#!/usr/bin/env python3
"""Enrich MaxTAC debate prompts and write debate tally outputs."""

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


def enrich_prompt(prompt_file: Path, root: Path) -> None:
    prompt_path_input = workspace_path(root, prompt_file, "Prompt file")
    raw_prompt = read_text(prompt_path_input).rstrip()
    debate_id = generated_id("debate")
    debate_dir = root / "debates" / debate_id
    debate_dir.mkdir(parents=True, exist_ok=False)

    prompt_path = debate_dir / "prompt.md"
    goal_objective = (
        "Evaluate the single binary debate proposition from the supplied evidence and persist one well-supported "
        f"ballot to {debate_dir}. Negative end outcome: if the proposition cannot be judged from the supplied or "
        "directly referenced evidence within a bounded pass, stop broadening scope and persist a ballot with low "
        "confidence, explicit blockers, and the side defined by the proposition as not-proven; when unclear, choose no."
    )
    goal_call = json.dumps({"objective": goal_objective})
    enriched = f"""FIRST ACTION REQUIRED: activate a Codex goal before doing any debate work.

If the `create_goal` tool is available, your first tool call must be:

```json
{goal_call}
```

If `create_goal` is unavailable but slash commands are available, send this before any other work:

```text
/goal {goal_objective}
```

Do not inspect files, run commands, reason through the proposition, or draft the ballot until goal activation has been attempted. Work inside that active goal. If goal activation is unavailable, continue only within the bounds below and record `"goal_activation": "unavailable"` in the ballot.

Bounds: review only the debate prompt, supplied evidence, directly referenced files/artifacts, and immediately necessary context needed to cast the ballot. Do not launch new audits, fuzzing, PoV construction, or broad discovery. Do not complete the subagent run until the goal is either achieved or ended with the negative outcome above.

## Debate Task

{raw_prompt}

---

## MaxTAC Debate Persistence Instructions

Debate ID: `{debate_id}`
Debate directory: `{debate_dir}`

Persist your ballot before completing the subagent run. Choose a stable subagent name for yourself, then write your ballot to `ballot-<subagent-name>.json` in the debate directory. Use this exact JSON structure:

```json
{{
  "debate": "{debate_id}",
  "subagent": "<subagent-name>",
  "goal_activation": "create_goal",
  "choice": "yes",
  "confidence": 85,
  "reasoning": "detailed reasoning for the choice",
  "evidence": "detailed evidence supporting the reasoning",
  "blockers": null
}}
```

The `goal_activation` value must be `create_goal`, `/goal`, or `unavailable`. The `choice` value must be either `yes` or `no`. The `confidence` value must be an integer from 0 to 100. Use `blockers` for blockers or concerns about the debate topic, otherwise use null.
"""
    prompt_path.write_text(enriched, encoding="utf-8")
    workspace_db.sync_debates(root, debate_id)
    print(enriched, end="")


def load_ballot(path: Path, expected_debate: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    choice = ballot_value(payload, "choice").lower()
    if choice not in {"yes", "no"}:
        raise SystemExit(f"{path} ballot choice must be yes or no")
    confidence = payload.get("confidence")
    if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
        raise SystemExit(f"{path} ballot confidence must be an integer from 0 to 100")
    debate = ballot_value(payload, "debate")
    if debate != expected_debate:
        raise SystemExit(f"{path} ballot debate must be {expected_debate}")
    return payload


def ballot_value(ballot: dict[str, Any], key: str, default: str = "") -> str:
    value = ballot.get(key, default)
    if value is None:
        return ""
    return str(value)


def compute_tally(debate_id: str, debate_dir: Path, ballots: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    counts: dict[str, int] = {"yes": 0, "no": 0}
    confidence_totals: dict[str, int] = {"yes": 0, "no": 0}
    normalized_ballots: list[dict[str, Any]] = []
    for path, ballot in ballots:
        choice = ballot_value(ballot, "choice").lower()
        confidence = int(ballot["confidence"])
        counts[choice] += 1
        confidence_totals[choice] += confidence
        normalized_ballots.append(
            {
                "file": str(path),
                "subagent": ballot_value(ballot, "subagent", path.stem.removeprefix("ballot-")),
                "goal_activation": ballot_value(ballot, "goal_activation", "unknown"),
                "choice": choice,
                "confidence": confidence,
                "reasoning": ballot_value(ballot, "reasoning"),
                "evidence": ballot_value(ballot, "evidence"),
                "blockers": ballot.get("blockers"),
            }
        )

    if counts["yes"] > counts["no"]:
        winner = "yes"
    elif counts["no"] > counts["yes"]:
        winner = "no"
    else:
        winner = "tie"

    return {
        "debate_id": debate_id,
        "debate_dir": str(debate_dir),
        "ballots": len(ballots),
        "counts": counts,
        "average_confidence": {
            choice: (confidence_totals[choice] / counts[choice] if counts[choice] else 0)
            for choice in ("yes", "no")
        },
        "winner": winner,
        "ballot_files": [str(path) for path, _ in ballots],
        "ballot_details": normalized_ballots,
    }


def render_tally_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# Debate Tally: {result['debate_id']}",
        "",
        f"- Debate directory: `{result['debate_dir']}`",
        f"- Ballots: {result['ballots']}",
        f"- Winner: {result['winner']}",
        f"- Yes: {result['counts'].get('yes', 0)}",
        f"- No: {result['counts'].get('no', 0)}",
        f"- Average yes confidence: {result['average_confidence'].get('yes', 0):.1f}",
        f"- Average no confidence: {result['average_confidence'].get('no', 0):.1f}",
        "",
    ]
    for ballot in result["ballot_details"]:
        lines.extend(
            [
                f"## {ballot['subagent']}",
                "",
                f"- Ballot file: `{ballot['file']}`",
                f"- Goal activation: {ballot['goal_activation']}",
                f"- Choice: {ballot['choice']}",
                f"- Confidence: {ballot['confidence']}",
                "",
                "### Reasoning",
                "",
                ballot["reasoning"],
                "",
                "### Evidence",
                "",
                ballot["evidence"],
                "",
            ]
        )
        if ballot.get("blockers"):
            lines.extend(["### Blockers", "", str(ballot["blockers"]), ""])
    return "\n".join(lines).rstrip() + "\n"


def render_summary_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# Debate Summary: {result['debate_id']}",
        "",
        f"- Winner: {result['winner']}",
        f"- Ballots: {result['ballots']}",
        f"- Yes votes: {result['counts'].get('yes', 0)}",
        f"- No votes: {result['counts'].get('no', 0)}",
        f"- Average yes confidence: {result['average_confidence'].get('yes', 0):.1f}",
        f"- Average no confidence: {result['average_confidence'].get('no', 0):.1f}",
        "",
        "## Ballot Basis",
        "",
    ]
    for ballot in result["ballot_details"]:
        blockers = f" Blockers: {ballot['blockers']}" if ballot.get("blockers") else ""
        lines.extend(
            [
                f"- {ballot['subagent']}: {ballot['choice']} ({ballot['confidence']}%). Goal activation: {ballot['goal_activation']}.{blockers}",
                f"  Evidence: {ballot['evidence']}",
                f"  Reasoning: {ballot['reasoning']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Parent Review",
            "",
            "Review this generated summary against the ballot details in `tally.md` before using the result for a ledger state transition.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def tally(debate_id: str, root: Path) -> None:
    debate_dir = root / "debates" / debate_id
    if not debate_dir.exists():
        raise SystemExit(f"Debate not found: {debate_id}")

    ballot_paths = sorted(debate_dir.glob("ballot-*.json"))
    if not ballot_paths:
        raise SystemExit(f"No ballots found for debate: {debate_id}")

    ballots = [(path, load_ballot(path, debate_id)) for path in ballot_paths]
    result = compute_tally(debate_id, debate_dir, ballots)
    tally_json_path = debate_dir / "tally.json"
    tally_path = debate_dir / "tally.md"
    summary_path = debate_dir / "summary.md"
    tally_json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    tally_path.write_text(render_tally_markdown(result), encoding="utf-8")
    summary_path.write_text(render_summary_markdown(result), encoding="utf-8")
    workspace_db.sync_debates(root, debate_id)

    print(render_summary_markdown(result), end="")
    print()
    print(f"Wrote tally JSON: {tally_json_path}")
    print(f"Wrote tally review: {tally_path}")
    print(f"Wrote debate summary: {summary_path}")


def one_line(value: Any, limit: int = 140) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def render_debate_row(payload: dict[str, Any]) -> str:
    counts = payload.get("counts") or {}
    average = payload.get("average_confidence") or {}
    return (
        f"{payload.get('debate_id')} "
        f"winner={payload.get('winner', 'none')} "
        f"ballots={payload.get('ballots', 0)} "
        f"yes={counts.get('yes', 0)} "
        f"no={counts.get('no', 0)} "
        f"avg_yes={float(average.get('yes', 0)):.1f} "
        f"avg_no={float(average.get('no', 0)):.1f} "
        f"updated={payload.get('updated_at', '')}"
    )


def print_debate_detail(payload: dict[str, Any]) -> None:
    counts = payload.get("counts") or {}
    average = payload.get("average_confidence") or {}
    print(f"Debate: {payload.get('debate_id')}")
    print(f"- directory: {payload.get('debate_dir', '')}")
    print(f"- prompt: {payload.get('prompt_path', '')}")
    print(f"- tally: {payload.get('tally_path', '') or 'missing'}")
    print(f"- summary: {payload.get('summary_path', '') or 'missing'}")
    print(f"- winner: {payload.get('winner', 'none')}")
    print(f"- ballots: {payload.get('ballots', 0)}")
    print(f"- yes: {counts.get('yes', 0)} (avg confidence {float(average.get('yes', 0)):.1f})")
    print(f"- no: {counts.get('no', 0)} (avg confidence {float(average.get('no', 0)):.1f})")
    print(f"- updated: {payload.get('updated_at', '')}")
    print()
    for ballot in payload.get("ballot_details", []):
        print(f"## {ballot.get('subagent', '')}")
        print(f"- file: {ballot.get('file', '')}")
        print(f"- goal_activation: {ballot.get('goal_activation', '')}")
        print(f"- choice: {ballot.get('choice', '')}")
        print(f"- confidence: {ballot.get('confidence', '')}")
        if ballot.get("blockers"):
            print(f"- blockers: {ballot.get('blockers')}")
        print()
        print("### Evidence")
        print(str(ballot.get("evidence", "")).rstrip())
        print()
        print("### Reasoning")
        print(str(ballot.get("reasoning", "")).rstrip())
        print()


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC debate helper")
    parser.add_argument("--root", default=".", help="Workspace root; prompt files should be staged under tmp/")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt-file", type=Path, help="Enrich a persisted debate prompt")
    group.add_argument("--debate", help="Debate ID to review")
    group.add_argument("--sync", action="store_true", help="Sync all debate artifacts into workspace.sqlite")
    group.add_argument("--list", action="store_true", help="List synced debate tallies")
    group.add_argument("--show", metavar="DEBATE_ID", help="Show synced debate details and ballot reasoning")
    group.add_argument("--search", metavar="TEXT", help="Semantic search debate prompts, tallies, and ballots")
    parser.add_argument("--tally", action="store_true", help="Validate ballots and write tally.json, tally.md, and summary.md")
    parser.add_argument("--limit", type=int, default=10, help="Maximum rows for list or search output")
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()

    if args.prompt_file:
        if args.tally:
            raise SystemExit("--tally can only be used with --debate")
        enrich_prompt(args.prompt_file, root_path(args.root))
        return

    if args.debate:
        if not args.tally:
            raise SystemExit("--debate requires --tally")
        tally(args.debate, root_path(args.root))
        return

    if args.tally:
        raise SystemExit("--tally can only be used with --debate")

    root = root_path(args.root)
    if args.sync:
        payloads = workspace_db.sync_debates(root)
        print(f"Synced {len(payloads)} debate(s) into {workspace_db.DB_FILE}")
    elif args.list:
        for payload in workspace_db.list_debates(root)[: max(1, args.limit)]:
            print(render_debate_row(payload))
    elif args.show:
        payload = workspace_db.get_debate(root, args.show)
        if not payload:
            raise SystemExit(f"Debate not found: {args.show}")
        print_debate_detail(payload)
    elif args.search:
        rows = workspace_db.semantic_search_debates(root, args.search, args.limit)
        if not rows:
            print("No matching debates.")
            return
        for score, payload in rows:
            print(f"{score:.6f} {render_debate_row(payload)}")
            if payload.get("summary_path"):
                print(f"  summary={payload.get('summary_path')}")
            else:
                print(f"  prompt={payload.get('prompt_path', '')}")


if __name__ == "__main__":
    main()
