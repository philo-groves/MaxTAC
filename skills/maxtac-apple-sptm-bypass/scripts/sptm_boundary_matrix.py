#!/usr/bin/env python3
"""Create a page-permission boundary matrix for Apple kernel research."""

from __future__ import annotations

import argparse
from pathlib import Path


MEMORY_CLASSES = [
    "ordinary-kernel-data",
    "page-table",
    "trust-cache",
    "code-page",
    "user-mapping",
    "dma-iommu",
    "copyin-copyout",
    "device-memory",
    "protected-metadata",
]


def mechanism_for_soc(soc: str) -> str:
    normalized = soc.upper().replace(" ", "")
    if normalized.startswith("A"):
        try:
            number = int(normalized[1:].split("-")[0])
        except ValueError:
            return "record exact SoC; mechanism unknown"
        return "SPTM/TXM likely supported" if number >= 15 else "PPL/APRR era, not SPTM"
    if normalized.startswith("M"):
        try:
            number = int(normalized[1:].split("-")[0])
        except ValueError:
            return "record exact SoC; mechanism unknown"
        return "SPTM/TXM likely supported" if number >= 2 else "PPL not applicable on macOS; record platform split"
    return "record exact SoC; mechanism unknown"


def build_matrix(args: argparse.Namespace) -> str:
    mechanism = mechanism_for_soc(args.soc)
    return f"""# Apple SPTM Boundary Matrix

OS build: {args.os_build}
SoC: {args.soc}
Mechanism estimate: {mechanism}
Memory class: {args.memory_class}
Primitive: {args.primitive}

| Question | Current answer |
| --- | --- |
| Is the primitive ordinary kernel data, protected metadata, or page-table state? | {args.memory_class} |
| Which component validates the transition? | |
| Which component commits the transition? | |
| Can attacker input survive validation until commit? | |
| Is there a race, stale owner, or lifetime mismatch? | |
| Is there a data-only impact if page-table control is blocked? | |
| What negative control proves the boundary? | |

## Alternative Paths

- Data-only policy or entitlement state:
- Mapping lifetime confusion:
- DMA/IOMMU or device-memory mismatch:
- copyin/copyout edge:
- Target Flag proof:
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an Apple SPTM boundary matrix")
    parser.add_argument("--soc", required=True)
    parser.add_argument("--os-build", required=True)
    parser.add_argument("--memory-class", required=True, choices=MEMORY_CLASSES)
    parser.add_argument("--primitive", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    matrix = build_matrix(args)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(matrix, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(matrix)


if __name__ == "__main__":
    main()
