#!/usr/bin/env python3
"""Extract and summarize candidate Apple ASLR leak values from text artifacts."""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path


ADDRESS_RE = re.compile(r"\b0x[0-9a-fA-F]{6,16}\b")


def read_addresses(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise SystemExit(f"Could not read {path}: {exc}") from exc
    return [match.group(0).lower() for match in ADDRESS_RE.finditer(text)]


def build_report(paths: list[Path], limit: int) -> str:
    by_file: dict[str, Counter[str]] = {}
    seen_in: dict[str, set[str]] = defaultdict(set)
    for path in paths:
        counts = Counter(read_addresses(path))
        by_file[str(path)] = counts
        for address in counts:
            seen_in[address].add(str(path))

    lines = ["# Apple ASLR Leak Matrix", ""]
    lines.append("| Artifact | Unique addresses | Top candidates |")
    lines.append("| --- | ---: | --- |")
    for artifact, counts in by_file.items():
        top = ", ".join(f"{addr}({count})" for addr, count in counts.most_common(limit))
        lines.append(f"| {artifact} | {len(counts)} | {top or '-'} |")

    repeated = sorted(
        ((addr, files) for addr, files in seen_in.items() if len(files) > 1),
        key=lambda item: (len(item[1]), item[0]),
        reverse=True,
    )
    lines.extend(["", "## Repeated Across Artifacts", ""])
    if not repeated:
        lines.append("- None found.")
    for address, files in repeated[:limit]:
        lines.append(f"- {address}: {len(files)} artifacts")

    lines.extend(
        [
            "",
            "## Classify Manually",
            "",
            "- Image slide:",
            "- Dyld shared cache:",
            "- Heap/object layout:",
            "- Stack:",
            "- Kernel slide:",
            "- JIT/shared mapping:",
            "- Same-actor reachability:",
            "- Post-leak primitive:",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize candidate ASLR leaks")
    parser.add_argument("artifacts", nargs="+")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report([Path(item) for item in args.artifacts], args.limit)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(report)


if __name__ == "__main__":
    main()
