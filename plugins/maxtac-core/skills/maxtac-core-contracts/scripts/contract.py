#!/usr/bin/env python3
"""Create, validate, and project MaxTAC canonical result bundles."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
DOCUMENT_TYPE = "maxtac.result_bundle"
SEVERITIES = ("critical", "high", "medium", "low", "informational")
CONFIDENCES = ("high", "medium", "low")
FINDING_TYPES = ("primitive", "chain", "candidate", "external")
DISPOSITIONS = ("reported", "no_issue_found", "rejected", "not_applicable", "needs_follow_up", "deferred")
STATES = ("discovered", "confident", "validated", "proofed", "duplicate", "limited", "de-escalated")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._").lower()
    return cleaned or "result"


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{path}: expected a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_location(value: str) -> dict[str, str]:
    parts = value.split(":", 2)
    if len(parts) == 3:
        label, path, lines = parts
    elif len(parts) == 2:
        label, path, lines = "location", parts[0], parts[1]
    else:
        label, path, lines = "location", value, ""
    return {"label": label.strip() or "location", "path": path.strip(), "lines": lines.strip()}


def parse_repeated(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        stripped = value.strip()
        if stripped and stripped not in result:
            result.append(stripped)
    return result


def base_result(args: argparse.Namespace) -> dict[str, Any]:
    result_id = slug(args.result_id)
    return {
        "document_type": DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "result_id": result_id,
        "created_at": now(),
        "updated_at": now(),
        "target": {
            "name": args.target,
            "kind": args.kind,
            "revision": args.revision or "",
            "source": args.source or "",
        },
        "scope": {
            "include_paths": parse_repeated(args.include) or ["."],
            "exclude_paths": parse_repeated(args.exclude),
            "summary": args.summary or "",
            "limitations": parse_repeated(args.limitation),
        },
        "findings": [],
        "coverage": [],
    }


def next_id(items: list[dict[str, Any]], prefix: str) -> str:
    highest = 0
    pattern = re.compile(rf"{re.escape(prefix)}-(\d+)$")
    for item in items:
        match = pattern.fullmatch(str(item.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:04d}"


def validate_result(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("document_type") != DOCUMENT_TYPE:
        errors.append(f"document_type must be {DOCUMENT_TYPE}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not str(payload.get("result_id", "")).strip():
        errors.append("result_id is required")
    target = payload.get("target")
    if not isinstance(target, dict) or not str(target.get("name", "")).strip() or not str(target.get("kind", "")).strip():
        errors.append("target.name and target.kind are required")
    scope = payload.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
    elif not isinstance(scope.get("include_paths"), list) or not isinstance(scope.get("exclude_paths"), list):
        errors.append("scope.include_paths and scope.exclude_paths must be arrays")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be an array")
    else:
        seen: set[str] = set()
        for index, finding in enumerate(findings):
            where = f"findings[{index}]"
            if not isinstance(finding, dict):
                errors.append(f"{where} must be an object")
                continue
            finding_id = str(finding.get("id", "")).strip()
            if not finding_id:
                errors.append(f"{where}.id is required")
            if finding_id in seen:
                errors.append(f"{where}.id duplicates {finding_id}")
            seen.add(finding_id)
            if finding.get("type") not in FINDING_TYPES:
                errors.append(f"{where}.type must be one of {', '.join(FINDING_TYPES)}")
            if finding.get("severity") not in SEVERITIES:
                errors.append(f"{where}.severity must be one of {', '.join(SEVERITIES)}")
            if finding.get("confidence") not in CONFIDENCES:
                errors.append(f"{where}.confidence must be one of {', '.join(CONFIDENCES)}")
            for key in ("state", "title", "category", "summary"):
                if not str(finding.get(key, "")).strip():
                    errors.append(f"{where}.{key} is required")
            if not isinstance(finding.get("affected_locations"), list):
                errors.append(f"{where}.affected_locations must be an array")
            if not isinstance(finding.get("evidence"), list):
                errors.append(f"{where}.evidence must be an array")
    coverage = payload.get("coverage")
    if not isinstance(coverage, list):
        errors.append("coverage must be an array")
    else:
        seen_surfaces: set[str] = set()
        for index, surface in enumerate(coverage):
            where = f"coverage[{index}]"
            if not isinstance(surface, dict):
                errors.append(f"{where} must be an object")
                continue
            surface_id = str(surface.get("id", "")).strip()
            if not surface_id:
                errors.append(f"{where}.id is required")
            if surface_id in seen_surfaces:
                errors.append(f"{where}.id duplicates {surface_id}")
            seen_surfaces.add(surface_id)
            if surface.get("disposition") not in DISPOSITIONS:
                errors.append(f"{where}.disposition must be one of {', '.join(DISPOSITIONS)}")
            for key in ("surface", "risk_area", "notes"):
                if not str(surface.get(key, "")).strip():
                    errors.append(f"{where}.{key} is required")
            if not isinstance(surface.get("receipt_refs"), list):
                errors.append(f"{where}.receipt_refs must be an array")
    return errors


def result_path(root: Path, result_id: str) -> Path:
    return root / "contracts" / slug(result_id) / "result.json"


def cmd_init(args: argparse.Namespace) -> None:
    path = result_path(Path(args.root), args.result_id)
    if path.exists() and not args.force:
        raise SystemExit(f"result already exists: {path}")
    payload = base_result(args)
    write_json(path, payload)
    print(path)


def cmd_from_ledger(args: argparse.Namespace) -> None:
    root = Path(args.root)
    path = result_path(root, args.result_id)
    if path.exists() and not args.force:
        raise SystemExit(f"result already exists: {path}")
    payload = base_result(args)
    for ledger_type, ledger_path in (("primitive", root / "primitives.json"), ("chain", root / "chains.json")):
        if not ledger_path.exists():
            continue
        ledger = read_json(ledger_path)
        for item in ledger.get("findings", []):
            if not isinstance(item, dict):
                continue
            payload["findings"].append(
                {
                    "id": str(item.get("id") or next_id(payload["findings"], "finding")),
                    "type": ledger_type,
                    "state": str(item.get("state") or "discovered"),
                    "title": str(item.get("title") or "Untitled finding"),
                    "severity": args.default_severity,
                    "confidence": args.default_confidence,
                    "category": str(item.get("category") or "uncategorized"),
                    "summary": str(item.get("summary") or "No summary recorded."),
                    "affected_locations": [{"label": "ledger", "path": loc, "lines": ""} for loc in item.get("locations", [])],
                    "evidence": list(item.get("evidence", [])),
                    "validation": "",
                    "attack_path": "",
                    "remediation": "",
                    "ledger_state": item,
                }
            )
    payload["updated_at"] = now()
    errors = validate_result(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    write_json(path, payload)
    print(path)


def cmd_add_finding(args: argparse.Namespace) -> None:
    path = Path(args.result_json)
    payload = read_json(path)
    finding = {
        "id": args.finding_id or next_id(payload.setdefault("findings", []), "finding"),
        "type": args.type,
        "state": args.state,
        "title": args.title,
        "severity": args.severity,
        "confidence": args.confidence,
        "category": args.category,
        "summary": args.summary,
        "affected_locations": [parse_location(value) for value in args.location or []],
        "evidence": parse_repeated(args.evidence),
        "validation": args.validation or "",
        "attack_path": args.attack_path or "",
        "remediation": args.remediation or "",
    }
    payload["findings"].append(finding)
    payload["updated_at"] = now()
    errors = validate_result(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    write_json(path, payload)
    print(finding["id"])


def cmd_add_surface(args: argparse.Namespace) -> None:
    path = Path(args.result_json)
    payload = read_json(path)
    surfaces = payload.setdefault("coverage", [])
    surface = {
        "id": args.surface_id or next_id(surfaces, "surface"),
        "surface": args.surface,
        "risk_area": args.risk_area,
        "disposition": args.disposition,
        "receipt_refs": parse_repeated(args.receipt),
        "notes": args.notes,
    }
    replaced = False
    for index, existing in enumerate(surfaces):
        if existing.get("id") == surface["id"]:
            surfaces[index] = surface
            replaced = True
            break
    if not replaced:
        surfaces.append(surface)
    payload["updated_at"] = now()
    errors = validate_result(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    write_json(path, payload)
    print(surface["id"])


def cmd_validate(args: argparse.Namespace) -> None:
    path = Path(args.result_json)
    errors = validate_result(read_json(path))
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"validated {path}")


def render_report(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    target = payload["target"]
    scope = payload["scope"]
    lines.append(f"# MaxTAC Result: {target['name']}")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(f"- Result: `{payload['result_id']}`")
    lines.append(f"- Target kind: `{target['kind']}`")
    if target.get("revision"):
        lines.append(f"- Revision: `{target['revision']}`")
    if target.get("source"):
        lines.append(f"- Source: `{target['source']}`")
    lines.append(f"- Include paths: {', '.join(scope.get('include_paths') or ['.'])}")
    if scope.get("exclude_paths"):
        lines.append(f"- Exclude paths: {', '.join(scope['exclude_paths'])}")
    if scope.get("summary"):
        lines.append(f"- Summary: {scope['summary']}")
    for limitation in scope.get("limitations", []):
        lines.append(f"- Limitation: {limitation}")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    findings = payload.get("findings", [])
    if not findings:
        lines.append("No canonical findings were recorded.")
    for finding in sorted(findings, key=lambda item: SEVERITIES.index(item["severity"])):
        lines.append(f"### {finding['id']}: {finding['title']}")
        lines.append("")
        lines.append(f"- Type: `{finding['type']}`")
        lines.append(f"- State: `{finding['state']}`")
        lines.append(f"- Severity: `{finding['severity']}`")
        lines.append(f"- Confidence: `{finding['confidence']}`")
        lines.append(f"- Category: {finding['category']}")
        if finding.get("affected_locations"):
            lines.append("- Affected locations:")
            for location in finding["affected_locations"]:
                label = location.get("label", "location")
                path = location.get("path", "")
                lines_text = location.get("lines", "")
                suffix = f":{lines_text}" if lines_text else ""
                detail = f" - {location.get('detail')}" if location.get("detail") else ""
                lines.append(f"  - `{label}` `{path}{suffix}`{detail}")
        if finding.get("evidence"):
            lines.append("- Evidence:")
            for evidence in finding["evidence"]:
                lines.append(f"  - `{evidence}`")
        lines.append("")
        lines.append(finding["summary"])
        for key, heading in (("validation", "Validation"), ("attack_path", "Attack Path"), ("remediation", "Remediation")):
            if finding.get(key):
                lines.append("")
                lines.append(f"#### {heading}")
                lines.append("")
                lines.append(finding[key])
        lines.append("")
    lines.append("## Coverage")
    lines.append("")
    coverage = payload.get("coverage", [])
    if not coverage:
        lines.append("No canonical coverage surfaces were recorded.")
    else:
        lines.append("| Surface | Risk Area | Disposition | Notes |")
        lines.append("| --- | --- | --- | --- |")
        for surface in coverage:
            notes = str(surface.get("notes", "")).replace("|", "\\|")
            lines.append(
                f"| {surface['surface']} | {surface['risk_area']} | `{surface['disposition']}` | {notes} |"
            )
    lines.append("")
    return "\n".join(lines)


def cmd_finalize(args: argparse.Namespace) -> None:
    path = Path(args.result_json)
    payload = read_json(path)
    errors = validate_result(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    report_path = Path(args.report) if args.report else path.with_name("report.md")
    report_path.write_text(render_report(payload), encoding="utf-8")
    print(report_path)


def add_result_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".")
    parser.add_argument("--result-id", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--kind", default="research")
    parser.add_argument("--revision")
    parser.add_argument("--source")
    parser.add_argument("--include", action="append")
    parser.add_argument("--exclude", action="append")
    parser.add_argument("--summary")
    parser.add_argument("--limitation", action="append")
    parser.add_argument("--force", action="store_true")


def main() -> None:
    parser = argparse.ArgumentParser(description="MaxTAC canonical result contract helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a canonical result bundle")
    add_result_args(init)
    init.set_defaults(func=cmd_init)

    from_ledger = subparsers.add_parser("from-ledger", help="Create a result bundle from MaxTAC ledgers")
    add_result_args(from_ledger)
    from_ledger.add_argument("--default-severity", choices=SEVERITIES, default="medium")
    from_ledger.add_argument("--default-confidence", choices=CONFIDENCES, default="medium")
    from_ledger.set_defaults(func=cmd_from_ledger)

    add_finding = subparsers.add_parser("add-finding", help="Append a canonical finding")
    add_finding.add_argument("result_json")
    add_finding.add_argument("--finding-id")
    add_finding.add_argument("--type", choices=FINDING_TYPES, default="candidate")
    add_finding.add_argument("--state", choices=STATES, default="discovered")
    add_finding.add_argument("--title", required=True)
    add_finding.add_argument("--severity", choices=SEVERITIES, default="medium")
    add_finding.add_argument("--confidence", choices=CONFIDENCES, default="medium")
    add_finding.add_argument("--category", required=True)
    add_finding.add_argument("--summary", required=True)
    add_finding.add_argument("--location", action="append")
    add_finding.add_argument("--evidence", action="append")
    add_finding.add_argument("--validation")
    add_finding.add_argument("--attack-path")
    add_finding.add_argument("--remediation")
    add_finding.set_defaults(func=cmd_add_finding)

    add_surface = subparsers.add_parser("add-surface", help="Append or replace a coverage surface")
    add_surface.add_argument("result_json")
    add_surface.add_argument("--surface-id")
    add_surface.add_argument("--surface", required=True)
    add_surface.add_argument("--risk-area", required=True)
    add_surface.add_argument("--disposition", choices=DISPOSITIONS, required=True)
    add_surface.add_argument("--receipt", action="append")
    add_surface.add_argument("--notes", required=True)
    add_surface.set_defaults(func=cmd_add_surface)

    validate = subparsers.add_parser("validate", help="Validate a result bundle")
    validate.add_argument("result_json")
    validate.set_defaults(func=cmd_validate)

    finalize = subparsers.add_parser("finalize", help="Project a deterministic markdown report")
    finalize.add_argument("result_json")
    finalize.add_argument("--report")
    finalize.set_defaults(func=cmd_finalize)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
