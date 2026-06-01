#!/usr/bin/env python3
"""Create a MaxTAC proof packet markdown file."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_OUTPUT_DIR = Path("data/maxtac/proof")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "proof"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a MaxTAC proof packet")
    parser.add_argument("--finding-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--claim", required=True)
    parser.add_argument("--reproduction", required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--actual", required=True)
    parser.add_argument("--impact", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--negative-control", required=True)
    parser.add_argument("--constraints", required=True)
    parser.add_argument("--fix", required=True)
    parser.add_argument("--cleanup", default="No persistent state created, or cleanup documented in reproduction.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def section(title: str, body: str) -> str:
    return f"## {title}\n\n{body.strip()}\n"


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{args.finding_id}-{slugify(args.title)}.md"
    created = datetime.now(timezone.utc).isoformat()

    content = "\n".join(
        [
            f"# MaxTAC Proof Packet: {args.finding_id}",
            "",
            f"Created: {created}",
            f"Title: {args.title}",
            f"Target: {args.target}",
            "",
            section("Claim", args.claim),
            section("Reproduction", args.reproduction),
            section("Expected Behavior", args.expected),
            section("Actual Behavior", args.actual),
            section("Impact", args.impact),
            section("Evidence", args.evidence),
            section("Negative Controls", args.negative_control),
            section("Constraints", args.constraints),
            section("Fix Recommendation", args.fix),
            section("Cleanup", args.cleanup),
        ]
    )

    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
