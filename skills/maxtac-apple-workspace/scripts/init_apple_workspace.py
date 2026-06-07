#!/usr/bin/env python3
"""Initialize MaxTAC Apple research domain directories and target notes."""

from __future__ import annotations

import argparse
import re
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


def slug(value: str) -> str:
    result = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return result or "target"


def target_note(domain: str, target: str) -> str:
    return f"""# {target}

Domain: {domain}

## Scope

- Target:
- Artifacts:
- Allowed operations:
- Exclusions:

## Research Threads

- New areas to explore:
- Prior work checked:
- Open primitives:
- Mechanism notes:

## Ledger Links

- Findings:
- Milestones:
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize MaxTAC Apple research workspace")
    parser.add_argument("--root", default="data/maxtac/research")
    parser.add_argument("--domain", action="append", choices=DOMAINS)
    parser.add_argument("--target")
    args = parser.parse_args()

    root = Path(args.root)
    domains = args.domain or DOMAINS
    created: list[Path] = []
    for domain in domains:
        domain_dir = root / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        created.append(domain_dir)
        if args.target:
            target_dir = domain_dir / slug(args.target)
            target_dir.mkdir(parents=True, exist_ok=True)
            note = target_dir / "notes.md"
            if not note.exists():
                note.write_text(target_note(domain, args.target), encoding="utf-8")
            created.append(note)

    for path in created:
        print(path)


if __name__ == "__main__":
    main()
