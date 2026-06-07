#!/usr/bin/env python3
"""Create a non-payload heap grooming experiment plan."""

from __future__ import annotations

import argparse
from pathlib import Path


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def build_plan(args: argparse.Namespace) -> str:
    sizes = split_csv(args.sizes)
    counts = split_csv(args.counts)
    lines = [
        f"# Apple Heap Grooming Plan: {args.target}",
        "",
        f"Allocator or heap: {args.allocator}",
        f"Primitive: {args.primitive}",
        "",
        "| Run | Size | Count | Timing | Expected observation | Actual observation |",
        "| ---: | --- | ---: | --- | --- | --- |",
    ]
    run = 1
    for size in sizes:
        for count in counts:
            lines.append(f"| {run} | {size} | {count} | baseline | placement signal | |")
            run += 1
            lines.append(f"| {run} | {size} | {count} | delayed free/use | stale-object signal | |")
            run += 1
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "- Same sequence without vulnerable trigger:",
            "- Same trigger without fill allocations:",
            "- Reboot or relaunch variance:",
            "- Entitlement or sandbox variance:",
            "",
            "## Outcomes",
            "",
            "- No reuse:",
            "- Wrong replacement object:",
            "- Controlled data observed:",
            "- PAC or ASLR blocker:",
            "- Target Flag partial proof:",
            "- Stable security impact:",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an Apple heap grooming experiment plan")
    parser.add_argument("--target", required=True)
    parser.add_argument("--allocator", required=True)
    parser.add_argument("--primitive", required=True)
    parser.add_argument("--sizes", required=True)
    parser.add_argument("--counts", default="16,64,256")
    parser.add_argument("--output")
    args = parser.parse_args()

    plan = build_plan(args)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plan, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(plan)


if __name__ == "__main__":
    main()
