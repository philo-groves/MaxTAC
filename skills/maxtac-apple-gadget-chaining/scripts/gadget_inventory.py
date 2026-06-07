#!/usr/bin/env python3
"""Summarize gadget-like instructions from Apple disassembly text."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


PATTERNS = {
    "indirect_branch": re.compile(r"\bbr\s+x\d+\b", re.I),
    "indirect_call": re.compile(r"\bblr\s+x\d+\b", re.I),
    "return": re.compile(r"\bret\b", re.I),
    "pac": re.compile(r"\b(pac|aut)[a-z0-9]*\b", re.I),
    "bti": re.compile(r"\bbti\b", re.I),
    "stack_write": re.compile(r"\bstr\b.*\bsp\b|\bstp\b.*\bsp\b", re.I),
    "memory_load": re.compile(r"\bldr\b.*\[", re.I),
}


def scan(path: Path, limit: int) -> tuple[Counter[str], dict[str, list[str]]]:
    counts: Counter[str] = Counter()
    examples: dict[str, list[str]] = {name: [] for name in PATTERNS}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                counts[name] += 1
                if len(examples[name]) < limit:
                    examples[name].append(line.strip())
    return counts, examples


def build_report(paths: list[Path], limit: int) -> str:
    lines = ["# Apple Gadget Inventory", ""]
    for path in paths:
        counts, examples = scan(path, limit)
        lines.extend([f"## {path}", "", "| Class | Count |", "| --- | ---: |"])
        for name in sorted(PATTERNS):
            lines.append(f"| {name} | {counts[name]} |")
        lines.append("")
        for name in sorted(PATTERNS):
            if examples[name]:
                lines.append(f"### {name}")
                lines.extend(f"- `{line}`" for line in examples[name])
                lines.append("")
    lines.extend(
        [
            "## Manual Classification",
            "",
            "- Artifact UUID and architecture:",
            "- PAC-compatible candidates:",
            "- BTI-compatible candidates:",
            "- Useful side effects:",
            "- Clobbers and cleanup constraints:",
            "- Missing primitive:",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Apple gadget-like instructions")
    parser.add_argument("disassembly", nargs="+")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report([Path(item) for item in args.disassembly], args.limit)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(report)


if __name__ == "__main__":
    main()
