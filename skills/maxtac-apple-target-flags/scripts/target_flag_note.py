#!/usr/bin/env python3
"""Create an Apple Target Flag proof note template."""

from __future__ import annotations

import argparse
from pathlib import Path


DOMAINS = [
    "apple-intelligence",
    "boot-chain",
    "comms",
    "icloud",
    "kernel",
    "private-cloud-compute",
    "radios",
    "sandbox",
    "webkit",
]


PRIMITIVE_HINTS = {
    "register": "Crash shows a general-purpose register containing the matching Target Flag value.",
    "read-write": "Crash or trace shows the vulnerable context read from or wrote to the matching Target Flag address.",
    "pc-control": "Crash shows PC control by branching to the matching Target Flag address.",
    "tcc-write": "tccutil flag check reports a modified user or system TCC database integrity_flag.",
}


def build_note(args: argparse.Namespace) -> str:
    hint = PRIMITIVE_HINTS[args.primitive]
    return f"""# Apple Target Flag Note: {args.target}

Domain: {args.domain}
Tier: {args.tier}
Primitive: {args.primitive}

## Expected Evidence

- OS build:
- Device or Mac class:
- SoC:
- Boot identifier or boot time:
- Vulnerable process:
- Crash log path:
- Target Flag source: commpage / TCC
- Expected proof: {hint}

## Observed Evidence

- Register or PC evidence:
- FAR or memory access evidence:
- TCC flag output:
- Vulnerability path that reached the flag:
- Negative control:

## Review

- Correct process:
- Correct privilege tier:
- Same boot as Target Flag read:
- Partial-control limits:
- Alternative proof path if this one blocks:
- Ledger finding or milestone:
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an Apple Target Flag note")
    parser.add_argument("--domain", required=True, choices=DOMAINS)
    parser.add_argument("--target", required=True)
    parser.add_argument("--primitive", required=True, choices=sorted(PRIMITIVE_HINTS))
    parser.add_argument("--tier", required=True, choices=["user", "kernel", "tcc"])
    parser.add_argument("--output")
    args = parser.parse_args()

    note = build_note(args)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(note, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(note)


if __name__ == "__main__":
    main()
