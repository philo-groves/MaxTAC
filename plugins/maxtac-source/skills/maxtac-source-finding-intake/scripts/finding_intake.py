#!/usr/bin/env python3
"""Normalize external security findings into MaxTAC intake contracts."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_TYPES = {
    "sarif", "github_code_scanning", "dependabot", "cve", "ghsa", "advisory",
    "scanner_ticket", "bug_bounty", "jira", "linear", "freeform", "json", "unknown",
}
VERDICTS = {"confirmed", "not_actionable", "needs_review"}
CONFIDENCES = {"high", "medium", "low"}


def now_id() -> str:
    return datetime.now(timezone.utc).strftime("intake-%Y%m%d%H%M%S")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def try_json(path: Path) -> Any | None:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError:
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def git_revision(repo: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()


def location(path: str, start_line: int | None = None, end_line: int | None = None, label: str = "location") -> dict[str, Any]:
    result: dict[str, Any] = {"label": label, "path": path.replace("\\", "/"), "lines": ""}
    if start_line:
        result["lines"] = str(start_line) if not end_line or end_line == start_line else f"{start_line}-{end_line}"
    return result


def blank_triage() -> dict[str, Any]:
    return {
        "verdict": "needs_review",
        "confidence": "low",
        "affected_locations": [],
        "reachable_path": [],
        "boundary_assessment": {
            "product_surface": "unknown",
            "source_trust": "unknown",
            "boundary_crossed": None,
            "policy_basis": "unknown",
        },
        "exploitability_rank": {
            "rank_queue": None,
            "rank": None,
            "rationale": "",
            "drivers": [],
        },
        "evidence": [],
        "counterevidence": [],
        "proof_gaps": ["static triage not completed"],
        "recommended_next_step": "inspect repository evidence",
        "handoff": "",
    }


def item(item_id: str, source_type: str, title: str, input_id: str = "", **fields: Any) -> dict[str, Any]:
    normalized = {
        "vulnerable_component": fields.get("vulnerable_component") or "unknown",
        "claimed_source": fields.get("claimed_source") or "unknown",
        "claimed_sink": fields.get("claimed_sink") or "unknown",
        "claimed_control": fields.get("claimed_control") or "unknown",
        "affected_version_or_path": fields.get("affected_version_or_path") or "unknown",
        "preconditions": fields.get("preconditions") or [],
        "impact": fields.get("impact") or "unknown",
        "references": fields.get("references") or [],
    }
    triage = blank_triage()
    triage["affected_locations"] = fields.get("affected_locations") or []
    return {
        "intake_item_id": item_id,
        "input_id": input_id,
        "source_type": source_type,
        "title": title or "Untitled external finding",
        "normalized_input": normalized,
        "triage": triage,
    }


def detect_type(payload: Any, requested: str, input_path: Path) -> str:
    if requested != "auto":
        return requested
    if isinstance(payload, dict) and payload.get("version") and isinstance(payload.get("runs"), list):
        return "sarif"
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        first = payload[0]
        if "rule" in first and ("most_recent_instance" in first or "instances" in first):
            return "github_code_scanning"
        if "security_vulnerability" in first or "security_advisory" in first:
            return "dependabot"
        return "json"
    if payload is not None:
        return "json"
    suffix = input_path.suffix.lower()
    if suffix in {".sarif"}:
        return "sarif"
    return "freeform"


def sarif_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rules: dict[str, dict[str, Any]] = {}
    for run in payload.get("runs", []):
        tool = run.get("tool", {}).get("driver", {})
        for rule in tool.get("rules", []) or []:
            if isinstance(rule, dict) and rule.get("id"):
                rules[str(rule["id"])] = rule
        for result in run.get("results", []) or []:
            if not isinstance(result, dict):
                continue
            rule_id = str(result.get("ruleId") or result.get("rule", {}).get("id") or "sarif-rule")
            rule = rules.get(rule_id, {})
            message = result.get("message", {})
            title = message.get("text") or message.get("markdown") or rule.get("name") or rule_id
            locations = []
            for sarif_location in result.get("locations", []) or []:
                physical = sarif_location.get("physicalLocation", {})
                artifact = physical.get("artifactLocation", {})
                region = physical.get("region", {})
                path = artifact.get("uri") or artifact.get("uriBaseId") or ""
                if path:
                    locations.append(location(path, region.get("startLine"), region.get("endLine")))
            rows.append(
                {
                    "title": title,
                    "input_id": f"sarif:{rule_id}:{len(rows) + 1}",
                    "vulnerable_component": locations[0]["path"] if locations else "unknown",
                    "claimed_sink": rule_id,
                    "affected_version_or_path": locations[0]["path"] if locations else "unknown",
                    "impact": result.get("level") or rule.get("shortDescription", {}).get("text") or "unknown",
                    "references": [rule_id],
                    "affected_locations": locations,
                }
            )
    return rows


def github_code_scanning_items(payload: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for alert in payload:
        if not isinstance(alert, dict):
            continue
        rule = alert.get("rule") or {}
        instance = alert.get("most_recent_instance") or {}
        location_obj = instance.get("location") or {}
        path = location_obj.get("path") or alert.get("most_recent_instance", {}).get("ref") or "unknown"
        rows.append(
            {
                "title": rule.get("description") or rule.get("name") or rule.get("id") or "GitHub code scanning alert",
                "input_id": str(alert.get("number") or alert.get("html_url") or ""),
                "vulnerable_component": path,
                "claimed_sink": rule.get("id") or "unknown",
                "affected_version_or_path": path,
                "impact": rule.get("security_severity_level") or alert.get("state") or "unknown",
                "references": [value for value in [alert.get("html_url"), rule.get("id")] if value],
                "affected_locations": [location(path, location_obj.get("start_line"), location_obj.get("end_line"))] if path != "unknown" else [],
            }
        )
    return rows


def dependabot_items(payload: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for alert in payload:
        if not isinstance(alert, dict):
            continue
        vuln = alert.get("security_vulnerability") or {}
        advisory = alert.get("security_advisory") or {}
        package = vuln.get("package") or {}
        package_name = package.get("name") or alert.get("dependency", {}).get("package", {}).get("name") or "unknown package"
        manifest = alert.get("dependency", {}).get("manifest_path") or "unknown"
        rows.append(
            {
                "title": advisory.get("summary") or f"Dependabot alert for {package_name}",
                "input_id": str(alert.get("number") or alert.get("html_url") or advisory.get("ghsa_id") or ""),
                "vulnerable_component": package_name,
                "claimed_sink": package_name,
                "affected_version_or_path": f"{package_name} in {manifest}",
                "impact": advisory.get("description") or vuln.get("severity") or "unknown",
                "references": [value for value in [alert.get("html_url"), advisory.get("ghsa_id"), advisory.get("cve_id")] if value],
                "affected_locations": [location(manifest)] if manifest != "unknown" else [],
            }
        )
    return rows


def generic_json_items(payload: Any) -> list[dict[str, Any]]:
    values = payload if isinstance(payload, list) else [payload]
    rows: list[dict[str, Any]] = []
    for value in values:
        if isinstance(value, dict):
            title = str(value.get("title") or value.get("message") or value.get("summary") or value.get("ruleId") or "JSON finding")
            input_id = str(value.get("id") or value.get("ruleId") or value.get("key") or "")
            path = str(value.get("path") or value.get("file") or value.get("location") or "unknown")
            rows.append(
                {
                    "title": title,
                    "input_id": input_id,
                    "vulnerable_component": path,
                    "claimed_sink": str(value.get("sink") or value.get("ruleId") or "unknown"),
                    "claimed_control": str(value.get("control") or "unknown"),
                    "affected_version_or_path": path,
                    "impact": str(value.get("impact") or value.get("severity") or "unknown"),
                    "references": [input_id] if input_id else [],
                    "affected_locations": [location(path)] if path != "unknown" else [],
                }
            )
        else:
            rows.append({"title": str(value), "input_id": "", "impact": "unknown"})
    return rows


def freeform_items(text: str, title: str | None) -> list[dict[str, Any]]:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return [
        {
            "title": title or first_line[:120] or "Freeform vulnerability claim",
            "input_id": "",
            "impact": text.strip() or "unknown",
            "references": [],
        }
    ]


def normalized_rows(source_type: str, payload: Any, text: str, title: str | None) -> list[dict[str, Any]]:
    if source_type == "sarif":
        if not isinstance(payload, dict):
            raise SystemExit("SARIF input must be a JSON object")
        return sarif_items(payload)
    if source_type == "github_code_scanning":
        if not isinstance(payload, list):
            raise SystemExit("GitHub code scanning input must be a JSON array")
        return github_code_scanning_items(payload)
    if source_type == "dependabot":
        if not isinstance(payload, list):
            raise SystemExit("Dependabot input must be a JSON array")
        return dependabot_items(payload)
    if source_type == "json":
        return generic_json_items(payload)
    return freeform_items(text, title)


def cmd_normalize(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    repo = Path(args.repo).resolve()
    input_path = Path(args.input).resolve()
    text = read_text(input_path)
    payload = try_json(input_path)
    source_type = detect_type(payload, args.source_type, input_path)
    if source_type not in SOURCE_TYPES:
        raise SystemExit(f"unsupported source type: {source_type}")
    intake_id = args.intake_id or now_id()
    output = Path(args.output).resolve() if args.output else root / "audits" / "intake" / intake_id / "intake.json"
    raw_dir = output.parent / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_copy = raw_dir / input_path.name
    if input_path != raw_copy:
        raw_copy.write_text(text, encoding="utf-8")
    rows = normalized_rows(source_type, payload, text, args.title)
    items = [item(f"intake-{index + 1:04d}", source_type, row.pop("title", ""), row.pop("input_id", ""), **row) for index, row in enumerate(rows)]
    document = {
        "document_type": "maxtac.intake",
        "schema_version": "maxtac.intake/v1",
        "intake_id": intake_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "path": str(repo),
            "revision": git_revision(repo),
        },
        "source": {
            "type": source_type,
            "raw_path": str(raw_copy),
        },
        "items": items,
    }
    errors = validate_document(document)
    if errors:
        raise SystemExit("\n".join(errors))
    write_json(output, document)
    print(output)


def validate_document(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("document_type") != "maxtac.intake":
        errors.append("document_type must be maxtac.intake")
    if document.get("schema_version") != "maxtac.intake/v1":
        errors.append("schema_version must be maxtac.intake/v1")
    if not isinstance(document.get("items"), list):
        errors.append("items must be an array")
        return errors
    seen: set[str] = set()
    for index, entry in enumerate(document["items"]):
        where = f"items[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{where} must be an object")
            continue
        item_id = str(entry.get("intake_item_id") or "")
        if not item_id:
            errors.append(f"{where}.intake_item_id is required")
        if item_id in seen:
            errors.append(f"{where}.intake_item_id duplicates {item_id}")
        seen.add(item_id)
        if entry.get("source_type") not in SOURCE_TYPES:
            errors.append(f"{where}.source_type is invalid")
        if not str(entry.get("title") or "").strip():
            errors.append(f"{where}.title is required")
        triage = entry.get("triage")
        if not isinstance(triage, dict):
            errors.append(f"{where}.triage is required")
            continue
        if triage.get("verdict") not in VERDICTS:
            errors.append(f"{where}.triage.verdict is invalid")
        if triage.get("confidence") not in CONFIDENCES:
            errors.append(f"{where}.triage.confidence is invalid")
        boundary = triage.get("boundary_assessment")
        if not isinstance(boundary, dict):
            errors.append(f"{where}.triage.boundary_assessment is required")
    return errors


def cmd_validate(args: argparse.Namespace) -> None:
    document = json.loads(Path(args.intake_json).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise SystemExit("intake JSON must be an object")
    errors = validate_document(document)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"validated {args.intake_json}")


def cmd_summarize(args: argparse.Namespace) -> None:
    document = json.loads(Path(args.intake_json).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise SystemExit("intake JSON must be an object")
    errors = validate_document(document)
    if errors:
        raise SystemExit("\n".join(errors))
    counts: dict[str, int] = {}
    for entry in document["items"]:
        verdict = entry["triage"]["verdict"]
        counts[verdict] = counts.get(verdict, 0) + 1
    print(f"MaxTAC intake: {document.get('intake_id')}")
    print(f"- repository: {document.get('repository', {}).get('path', '')}")
    print(f"- items: {len(document['items'])}")
    for verdict in sorted(counts):
        print(f"- {verdict}: {counts[verdict]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MaxTAC external finding intake helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    normalize = subparsers.add_parser("normalize")
    normalize.add_argument("--root", default=".")
    normalize.add_argument("--repo", default=".")
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--output")
    normalize.add_argument("--intake-id")
    normalize.add_argument("--source-type", default="auto", choices=sorted(SOURCE_TYPES | {"auto"}))
    normalize.add_argument("--title")
    normalize.set_defaults(func=cmd_normalize)

    validate = subparsers.add_parser("validate")
    validate.add_argument("intake_json")
    validate.set_defaults(func=cmd_validate)

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("intake_json")
    summarize.set_defaults(func=cmd_summarize)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
