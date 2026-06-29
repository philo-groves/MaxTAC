#!/usr/bin/env python3
"""Create and lint OSS supply-chain proof gate packets."""

from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path
import re
import sys


REQUIRED_HEADINGS = [
    "# OSS Supply Chain Proof Gate",
    "## Program And Scope Basis",
    "## Target Ownership",
    "## Affected Consumer",
    "## Attacker Control",
    "## Security Impact",
    "## Proof Quality",
    "## Exclusions Checked",
    "## Decision",
    "## Evidence Index",
]

PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|UNKNOWN)\b|<[^>\n]+>", re.IGNORECASE)
VALID_DECISIONS = {
    "reportable",
    "needs_product_impact",
    "third_party_first",
    "needs_review",
    "not_actionable",
}


def render(args: argparse.Namespace) -> str:
    today = _dt.date.today().isoformat()
    return f"""# OSS Supply Chain Proof Gate: {args.case_id or "TBD"}

Created: {today}

## Program And Scope Basis

- Program: TBD
- Rule source or policy path: TBD
- Target: {args.target or "TBD"}
- Ecosystem: {args.ecosystem or "TBD"}
- Scope basis: TBD

## Target Ownership

- Ownership class: first-party / third-party dependency / transitive dependency / vendored / generated / registry / unknown
- Owner or maintainer evidence: TBD
- Upstream notification status: TBD

## Affected Consumer

- Consumer that installs, builds, imports, deploys, signs, or serves the artifact: TBD
- Supported version or release path: TBD
- Evidence that the consumer reaches the artifact: TBD

## Attacker Control

- Claim: {args.claim or "TBD"}
- Attacker-controlled input or authority: TBD
- Trust boundary crossed: TBD
- Negative control: TBD

## Security Impact

- Impact class: code execution / credential theft / artifact poisoning / signing abuse / deployment takeover / data access / integrity loss / other
- Real-world impact on in-scope consumer: TBD
- Blast radius: TBD

## Proof Quality

- Positive proof: TBD
- Static evidence: TBD
- Dynamic or isolated PoV: TBD
- Product-impact reproduction: TBD
- Remaining proof gaps: TBD

## Exclusions Checked

- Dependency presence only: TBD
- Stale CVE or known advisory only: TBD
- Unsupported target or version: TBD
- Test, demo, fixture, or local-only path: TBD
- No realistic attacker path: TBD
- Duplicate or already reported: TBD

## Decision

- Decision: needs_review
- Rationale: TBD
- Next action: TBD

## Evidence Index

- TBD
"""


def create(args: argparse.Namespace) -> int:
    output = Path(args.output)
    if output.exists() and not args.force:
        print(f"refusing to overwrite existing packet: {output}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(args), encoding="utf-8", newline="\n")
    print(f"created OSS proof gate packet: {output}")
    return 0


def lint(args: argparse.Namespace) -> int:
    packet = Path(args.packet)
    if not packet.exists():
        print(f"packet not found: {packet}", file=sys.stderr)
        return 2
    text = packet.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing heading: {heading}")

    decision_match = re.search(r"^- Decision:\s*([a-z_]+)\s*$", text, re.MULTILINE)
    if not decision_match:
        errors.append("missing '- Decision:' field")
    elif decision_match.group(1) not in VALID_DECISIONS:
        errors.append(
            "invalid decision: "
            + decision_match.group(1)
            + " (expected one of "
            + ", ".join(sorted(VALID_DECISIONS))
            + ")"
        )

    if "## Positive Proof" in text:
        warnings.append("packet uses old proof wording; expected '## Proof Quality'")

    placeholders = sorted(set(match.group(0) for match in PLACEHOLDER_RE.finditer(text)))
    if placeholders and args.strict:
        errors.append("strict packet still has placeholders: " + ", ".join(placeholders[:10]))
    elif placeholders:
        warnings.append("packet still has placeholders")

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"packet lint passed: {packet}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC OSS supply-chain proof gate helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create an OSS proof gate packet")
    create_parser.add_argument("--output", required=True)
    create_parser.add_argument("--case-id", default="")
    create_parser.add_argument("--target", default="")
    create_parser.add_argument("--ecosystem", default="")
    create_parser.add_argument("--claim", default="")
    create_parser.add_argument("--force", action="store_true")
    create_parser.set_defaults(func=create)

    lint_parser = subparsers.add_parser("lint", help="Check an OSS proof gate packet")
    lint_parser.add_argument("packet")
    lint_parser.add_argument("--strict", action="store_true")
    lint_parser.set_defaults(func=lint)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
