#!/usr/bin/env python3
"""Create a non-weaponized JOP/call-oriented chain requirements table."""

from __future__ import annotations

import argparse
from pathlib import Path


ROWS = [
    "PC or indirect-call control",
    "Dispatcher or call surface",
    "State register or object control",
    "PAC-compatible pointer",
    "BTI-compatible landing",
    "ASLR or KASLR knowledge",
    "Writable state memory",
    "Side-effect target",
    "Cleanup or crash tolerance",
]


def build_table(args: argparse.Namespace) -> str:
    supplied = {
        "PC or indirect-call control": args.pc_control,
        "Dispatcher or call surface": args.dispatcher,
        "PAC-compatible pointer": args.pac,
        "BTI-compatible landing": args.bti,
        "ASLR or KASLR knowledge": args.aslr,
        "Writable state memory": args.state,
        "Cleanup or crash tolerance": args.cleanup,
    }
    lines = [f"# Apple JOP Requirements: {args.target}", ""]
    lines.append("| Requirement | Evidence | Missing evidence | Next lab check |")
    lines.append("| --- | --- | --- | --- |")
    for row in ROWS:
        evidence = supplied.get(row, "")
        lines.append(f"| {row} | {evidence} | | |")
    lines.extend(
        [
            "",
            "## Alternative Routes",
            "",
            "- Signed callback reuse:",
            "- Objective-C/Swift dispatch surface:",
            "- Data-only impact without code reuse:",
            "- Target Flag proof subset:",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an Apple JOP requirements table")
    parser.add_argument("--target", required=True)
    parser.add_argument("--pc-control", default="")
    parser.add_argument("--dispatcher", default="")
    parser.add_argument("--pac", default="")
    parser.add_argument("--bti", default="")
    parser.add_argument("--aslr", default="")
    parser.add_argument("--state", default="")
    parser.add_argument("--cleanup", default="")
    parser.add_argument("--output")
    args = parser.parse_args()

    table = build_table(args)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(table, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(table)


if __name__ == "__main__":
    main()
