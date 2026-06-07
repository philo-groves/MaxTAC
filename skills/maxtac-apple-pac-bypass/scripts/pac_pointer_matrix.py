#!/usr/bin/env python3
"""Create a PAC pointer-class matrix and extract PAC crash hints."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


POINTER_CLASSES = {
    "return": ("IB", "storage address"),
    "function": ("IA", "0"),
    "block-invoke": ("IA", "storage address"),
    "block-descriptor": ("DA", "storage address + 0xC0BB"),
    "objc-cache": ("IB", "storage address + class + selector"),
    "objc-isa": ("DA", "storage address + 0x6AE1"),
    "objc-super": ("DA", "storage address + 0xB5AB"),
    "cpp-vtable-entry": ("IA", "storage address + hash(mangled method name)"),
    "cpp-vtable-pointer": ("DA", "storage address + hash(mangled base vtable name)"),
    "thread-state": ("IA/GA", "storage address or kernel thread-state context"),
    "data-only": ("none or context-specific", "not a direct code pointer"),
}

PAC_HINT_RE = re.compile(r"pointer authentication|ptrauth|pac|authentication failure|possible pointer", re.I)


def crash_hints(path: str | None) -> list[str]:
    if not path:
        return []
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return [line.strip() for line in text.splitlines() if PAC_HINT_RE.search(line)][:20]


def build_report(args: argparse.Namespace) -> str:
    key, salt = POINTER_CLASSES[args.pointer_class]
    hints = crash_hints(args.crash_log)
    lines = [
        f"# Apple PAC Pointer Matrix: {args.pointer_class}",
        "",
        f"Key hypothesis: {key}",
        f"Discriminator or salt: {salt}",
        f"Storage address known: {args.storage_known}",
        "",
        "| Question | Current answer |",
        "| --- | --- |",
        "| Where is the pointer signed? | |",
        "| Where is it stored? | |",
        "| Where is it authenticated? | |",
        "| Is reuse same process and same pointer class? | |",
        "| Does storage address participate in the discriminator? | |",
        "| What is the observed failure mode? | |",
        "| What data-only impact exists if control flow blocks? | |",
        "",
        "## Crash Hints",
        "",
    ]
    lines.extend(f"- {line}" for line in hints) if hints else lines.append("- None supplied.")
    lines.extend(
        [
            "",
            "## Alternative Paths",
            "",
            "- Pre-signing input control:",
            "- Same-slot signed pointer reuse:",
            "- Post-auth data-only state:",
            "- JOP or gadget-chain follow-up:",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a PAC pointer-class matrix")
    parser.add_argument("--pointer-class", required=True, choices=sorted(POINTER_CLASSES))
    parser.add_argument("--storage-known", action="store_true")
    parser.add_argument("--crash-log")
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report(args)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(report)


if __name__ == "__main__":
    main()
