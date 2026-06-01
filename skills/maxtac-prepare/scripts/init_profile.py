#!/usr/bin/env python3
"""Create a starter MaxTAC target profile."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_OUTPUT = Path("data/maxtac/target-profile.json")


def split_values(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        for item in value.split(","):
            item = item.strip()
            if item and item not in result:
                result.append(item)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create data/maxtac/target-profile.json")
    parser.add_argument("--target-name", required=True)
    parser.add_argument(
        "--family",
        required=True,
        choices=["xnu", "windows-kernel-adjacent", "binary", "open-source-systems", "mixed"],
    )
    parser.add_argument("--root", action="append", help="Target source or artifact root")
    parser.add_argument("--platform", action="append", help="Platform tag, may be comma-separated")
    parser.add_argument("--target-kind", action="append", help="Target kind tag, may be comma-separated")
    parser.add_argument("--surface", action="append", help="Surface tag, may be comma-separated")
    parser.add_argument("--allowed-operation", action="append", help="Allowed operation tag")
    parser.add_argument("--scope-summary", default="Authorized local MaxTAC analysis.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    if output.exists() and not args.force:
        raise SystemExit(f"{output} already exists. Use --force to overwrite.")

    profile = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target_name": args.target_name,
        "target_family": args.family,
        "scope_summary": args.scope_summary,
        "artifact_roots": split_values(args.root),
        "platforms": split_values(args.platform),
        "target_kinds": split_values(args.target_kind),
        "surfaces": split_values(args.surface),
        "trust_boundaries": [],
        "entrypoints": [],
        "sensitive_sinks": [],
        "mitigations": [],
        "allowed_operations": split_values(args.allowed_operation) or ["read-only", "static-analysis"],
        "excluded_families": ["linux-kernel", "web-app"],
        "notes": [],
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
