#!/usr/bin/env python3
"""Rank MaxTAC auditor catalog entries against a target profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "references" / "auditor-catalog.yaml"


def as_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {item.strip().lower() for item in value.split(",") if item.strip()}
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(as_set(item))
        return result
    return set()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Profile not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON profile {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return payload


def load_catalog(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Catalog not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("auditors"), list):
        raise SystemExit(f"{path} must contain an auditors list")
    return payload["auditors"]


def score_auditor(profile: dict[str, Any], auditor: dict[str, Any]) -> tuple[int, list[str], bool]:
    profile_family = as_set(profile.get("target_family"))
    profile_platforms = as_set(profile.get("platforms"))
    profile_kinds = as_set(profile.get("target_kinds"))
    profile_surfaces = as_set(profile.get("surfaces"))
    profile_bug_classes = as_set(profile.get("bug_classes") or profile.get("focus_bug_classes"))
    current_tags = profile_family | profile_platforms | profile_kinds | profile_surfaces

    disabled = as_set(auditor.get("disabled_for"))
    if disabled & current_tags:
        return (0, [f"disabled for {', '.join(sorted(disabled & current_tags))}"], True)

    reasons: list[str] = []
    score = 0
    for label, weight, left, right in (
        ("platform", 3, profile_platforms, as_set(auditor.get("platforms"))),
        ("target kind", 4, profile_kinds, as_set(auditor.get("target_kinds"))),
        ("surface", 5, profile_surfaces, as_set(auditor.get("surfaces"))),
        ("bug class", 2, profile_bug_classes, as_set(auditor.get("bug_classes"))),
    ):
        matches = left & right
        if matches:
            score += weight * len(matches)
            reasons.append(f"{label}: {', '.join(sorted(matches))}")

    return (score, reasons, False)


def render_markdown(rows: list[tuple[int, list[str], dict[str, Any]]]) -> str:
    lines = ["# MaxTAC Auditor Selection", ""]
    if not rows:
        lines.append("No matching auditors. Check target profile tags or scope exclusions.")
        return "\n".join(lines) + "\n"

    for score, reasons, auditor in rows:
        lines.append(f"## {auditor['id']} (score {score})")
        lines.append("")
        lines.append(f"Focus: {auditor.get('focus', '').strip()}")
        lines.append("")
        lines.append(f"Reasons: {'; '.join(reasons) if reasons else 'fallback match'}")
        lines.append(f"Surfaces: {', '.join(auditor.get('surfaces', []))}")
        lines.append(f"Bug classes: {', '.join(auditor.get('bug_classes', []))}")
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank MaxTAC auditors for a profile")
    parser.add_argument("--profile", default="data/maxtac/target-profile.json")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--include-zero", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile = load_json(Path(args.profile))
    catalog = load_catalog(Path(args.catalog))

    rows: list[tuple[int, list[str], dict[str, Any]]] = []
    for auditor in catalog:
        score, reasons, disabled = score_auditor(profile, auditor)
        if disabled:
            continue
        if score > 0 or args.include_zero:
            rows.append((score, reasons, auditor))

    rows.sort(key=lambda row: (row[0], row[2].get("id", "")), reverse=True)
    rows = rows[: args.limit]

    if args.format == "json":
        print(json.dumps([
            {"score": score, "reasons": reasons, "auditor": auditor}
            for score, reasons, auditor in rows
        ], indent=2))
    else:
        print(render_markdown(rows))


if __name__ == "__main__":
    main()
