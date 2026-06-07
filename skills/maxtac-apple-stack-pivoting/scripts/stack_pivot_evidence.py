#!/usr/bin/env python3
"""Extract register evidence relevant to Apple stack or context pivots."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REGISTER_RE = re.compile(r"\b(?P<reg>x(?:[0-2]?\d|3[01])|sp|fp|lr|pc)\b\s*[:=]?\s*(?P<value>0x[0-9a-fA-F]+)")
PAC_RE = re.compile(r"pointer authentication|ptrauth|pac|possible pointer", re.I)


def parse_registers(text: str) -> dict[str, list[str]]:
    registers: dict[str, list[str]] = {}
    for match in REGISTER_RE.finditer(text):
        reg = match.group("reg").lower()
        registers.setdefault(reg, [])
        value = match.group("value").lower()
        if value not in registers[reg]:
            registers[reg].append(value)
    return registers


def build_report(path: Path, controlled_values: list[str]) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    registers = parse_registers(text)
    controlled = {value.lower() for value in controlled_values}
    pac_hints = [line.strip() for line in text.splitlines() if PAC_RE.search(line)][:20]

    lines = [f"# Apple Pivot Evidence: {path}", ""]
    lines.append("| Register | Values observed | Controlled marker? |")
    lines.append("| --- | --- | --- |")
    for reg in ["sp", "fp", "lr", "pc"] + [f"x{i}" for i in range(32)]:
        values = registers.get(reg, [])
        if not values:
            continue
        marker = "yes" if any(value in controlled for value in values) else ""
        lines.append(f"| {reg} | {', '.join(values)} | {marker} |")

    lines.extend(["", "## PAC Hints", ""])
    lines.extend(f"- {line}" for line in pac_hints) if pac_hints else lines.append("- None found.")
    lines.extend(
        [
            "",
            "## Manual Review",
            "",
            "- SP control:",
            "- FP/LR/PC control:",
            "- Callee-saved register state:",
            "- Fake-state placement:",
            "- PAC failure versus normal bad access:",
            "- Alternative pivot path:",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Apple pivot evidence from a crash log")
    parser.add_argument("crash_log")
    parser.add_argument("--controlled-value", action="append", default=[])
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report(Path(args.crash_log), args.controlled_value)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(report)


if __name__ == "__main__":
    main()
