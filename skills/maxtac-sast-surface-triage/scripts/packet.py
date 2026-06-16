#!/usr/bin/env python3
"""Create, lint, and convert MaxTAC SAST packets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PacketSpec:
    packet_type: str
    heading: str
    fields: tuple[str, ...]
    enums: dict[str, tuple[str, ...]] | None = None


SPECS = {
    "surface": PacketSpec(
        packet_type="surface",
        heading="Surface Triage Packet",
        fields=(
            "Target slice",
            "Actor and starting privileges",
            "Protected asset or trust boundary",
            "Entry points",
            "Controlled inputs",
            "Security invariant",
            "Suspect guard, sink, or state transition",
            "Key files/functions",
            "Evidence collected",
            "Evidence still needed",
            "Suggested tools",
            "Suggested auditor filters",
            "Candidate hypothesis",
            "Confidence",
        ),
        enums={"Confidence": ("low", "medium", "high")},
    ),
    "cfg": PacketSpec(
        packet_type="cfg",
        heading="Control-Flow Evidence",
        fields=(
            "Question",
            "Actor and entrypoint",
            "Sink or protected transition",
            "Required guard",
            "Graph type",
            "Tools or commands",
            "Confirmed path",
            "Blocking guard or missing guard",
            "State, lock, or lifetime assumptions",
            "Uncertain edges",
            "Security conclusion",
        ),
    ),
    "opengrep": PacketSpec(
        packet_type="opengrep",
        heading="OpenGrep Result Packet",
        fields=(
            "Rule or search",
            "Target slice",
            "Matched files/functions",
            "Source or controlled input",
            "Sink or protected transition",
            "Expected guard or invariant",
            "Confirmed path",
            "False-positive reasons removed",
            "Remaining uncertainty",
            "Suggested auditor filters",
        ),
    ),
}

TYPE_CHOICES = tuple(SPECS)
HEADING_RE = re.compile(r"^\s*##\s+(.+?)\s*$")
FIELD_RE = re.compile(r"^\s*-\s+([^:\n]+):\s*(.*)$")
PLACEHOLDER_RE = re.compile(r"^\s*(?:\[.*\]|<.*>|TODO|TBD|FIXME)\s*$", re.IGNORECASE)
PROMOTION_CLAIM_RE = re.compile(
    r"\b(?:proofed|validated|reportable|submission-ready|promote(?:d)?\s+to|confirmed\s+vulnerability)\b",
    re.IGNORECASE,
)
NEGATIVE_PATH_RE = re.compile(r"\b(?:not\s+confirmed|unconfirmed|unknown|needs\s+cfg|needs\s+validation)\b", re.IGNORECASE)


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    packet_path = Path(path)
    if not packet_path.exists():
        raise SystemExit(f"Packet file not found: {packet_path}")
    return packet_path.read_text(encoding="utf-8", errors="replace")


def output_text(path: str | None, text: str) -> None:
    if not path or path == "-":
        print(text, end="")
        return
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def spec_for(packet_type: str) -> PacketSpec:
    try:
        return SPECS[packet_type]
    except KeyError as exc:
        choices = ", ".join(TYPE_CHOICES)
        raise SystemExit(f"Unknown packet type: {packet_type}. Expected one of: {choices}") from exc


def field_map(spec: PacketSpec) -> dict[str, str]:
    return {normalize(field): field for field in spec.fields}


def detect_packet_type(text: str) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    heading_map = {normalize(spec.heading): spec.packet_type for spec in SPECS.values()}
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        packet_type = heading_map.get(normalize(match.group(1)))
        if packet_type:
            return packet_type, warnings

    discovered_labels = {
        normalize(match.group(1))
        for line in text.splitlines()
        if (match := FIELD_RE.match(line))
    }
    scores = []
    for spec in SPECS.values():
        labels = set(field_map(spec))
        scores.append((len(discovered_labels & labels), spec.packet_type))
    scores.sort(reverse=True)
    if scores and scores[0][0] >= 3:
        if len(scores) > 1 and scores[0][0] == scores[1][0]:
            warnings.append("packet type inferred ambiguously from fields")
        warnings.append("packet heading is missing; inferred packet type from fields")
        return scores[0][1], warnings
    return None, ["packet heading is missing or not a known MaxTAC SAST packet"]


def parse_fields(text: str, spec: PacketSpec) -> tuple[dict[str, str], list[str]]:
    labels = field_map(spec)
    fields: dict[str, str] = {}
    warnings: list[str] = []
    current_field: str | None = None

    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading and normalize(heading.group(1)) != normalize(spec.heading):
            current_field = None
            continue

        match = FIELD_RE.match(line)
        if match:
            canonical = labels.get(normalize(match.group(1)))
            if canonical:
                current_field = canonical
                fields[canonical] = match.group(2).strip()
                continue
            if current_field is None:
                warnings.append(f"unexpected packet field ignored: {match.group(1).strip()}")
                continue

        if current_field is not None:
            continuation = line.rstrip()
            if continuation:
                fields[current_field] = (fields[current_field] + "\n" + continuation).strip()

    return fields, warnings


def is_blank(value: str | None) -> bool:
    if value is None:
        return True
    stripped = value.strip()
    if not stripped:
        return True
    return bool(PLACEHOLDER_RE.fullmatch(stripped))


def render_packet(spec: PacketSpec, values: dict[str, str] | None = None) -> str:
    values = values or {}
    lines = [f"## {spec.heading}", ""]
    for field in spec.fields:
        value = values.get(field, "")
        if "\n" in value:
            first, *rest = value.splitlines()
            lines.append(f"- {field}: {first}")
            lines.extend(rest)
        else:
            lines.append(f"- {field}: {value}")
    return "\n".join(lines).rstrip() + "\n"


def lint_packet(text: str, packet_type: str = "auto", source: str = "<stdin>") -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    detected_type = packet_type
    if packet_type == "auto":
        detected_type, detect_warnings = detect_packet_type(text)
        warnings.extend(detect_warnings)
        if not detected_type:
            return {
                "source": source,
                "type": None,
                "ok": False,
                "errors": ["could not identify packet type"],
                "warnings": warnings,
                "fields": {},
            }

    spec = spec_for(str(detected_type))
    fields, parse_warnings = parse_fields(text, spec)
    warnings.extend(parse_warnings)

    for field in spec.fields:
        if field not in fields:
            errors.append(f"missing field: {field}")
        elif is_blank(fields[field]):
            errors.append(f"empty field: {field}")

    for field, allowed_values in (spec.enums or {}).items():
        value = fields.get(field, "").strip().lower()
        if value and value not in allowed_values:
            allowed = ", ".join(allowed_values)
            errors.append(f"{field} must be one of: {allowed}")

    packet_body = "\n".join(fields.values())
    if PROMOTION_CLAIM_RE.search(packet_body):
        warnings.append("packet appears to claim final finding status; keep SAST packets as hypotheses or evidence")

    if spec.packet_type == "surface":
        tools = fields.get("Suggested tools", "")
        if tools and not re.search(r"\b(?:opengrep|cfg|re|dast|auditor)\b", tools, re.IGNORECASE):
            warnings.append("Suggested tools should route to OpenGrep, CFG, RE, DAST, or auditors")
        confidence = fields.get("Confidence", "").strip().lower()
        evidence_needed = fields.get("Evidence still needed", "").strip().lower()
        if confidence == "high" and evidence_needed and evidence_needed not in {"none", "n/a", "na"}:
            warnings.append("high-confidence triage still lists evidence gaps")

    if spec.packet_type == "opengrep" and NEGATIVE_PATH_RE.search(fields.get("Confirmed path", "")):
        warnings.append("OpenGrep path is not confirmed; auditor prompt should preserve reachability uncertainty")

    return {
        "source": source,
        "type": spec.packet_type,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "fields": fields,
    }


def parse_set_values(spec: PacketSpec, values: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    labels = field_map(spec)
    for item in values or []:
        if "=" in item:
            raw_label, raw_value = item.split("=", 1)
        elif ":" in item:
            raw_label, raw_value = item.split(":", 1)
        else:
            raise SystemExit(f"--set requires FIELD=VALUE: {item}")
        canonical = labels.get(normalize(raw_label))
        if not canonical:
            choices = ", ".join(spec.fields)
            raise SystemExit(f"Unknown {spec.packet_type} field: {raw_label}. Expected one of: {choices}")
        result[canonical] = raw_value.strip()
    return result


def split_filters(value: str) -> list[str]:
    filters: list[str] = []
    for part in re.split(r"[,;\n]+", value):
        cleaned = part.strip().strip("-` ")
        if cleaned and cleaned not in filters:
            filters.append(cleaned)
    return filters


def packet_summary(result: dict[str, Any]) -> str:
    spec = spec_for(result["type"])
    fields = result["fields"]
    if spec.packet_type == "surface":
        return str(fields.get("Candidate hypothesis") or fields.get("Target slice") or spec.heading)
    if spec.packet_type == "cfg":
        return str(fields.get("Question") or fields.get("Security conclusion") or spec.heading)
    return str(fields.get("Rule or search") or fields.get("Target slice") or spec.heading)


def load_results(paths: list[str], packet_type: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in paths:
        text = read_text(path)
        result = lint_packet(text, packet_type=packet_type, source=path)
        result["canonical_markdown"] = render_packet(spec_for(result["type"]), result["fields"]) if result["type"] else text
        results.append(result)
    return results


def render_auditor_prompt(results: list[dict[str, Any]], args: argparse.Namespace) -> str:
    filters: list[str] = []
    for value in args.auditor_filter or []:
        for item in split_filters(value):
            if item not in filters:
                filters.append(item)
    for result in results:
        fields = result.get("fields", {})
        for field in ("Suggested auditor filters",):
            for item in split_filters(str(fields.get(field, ""))):
                if item not in filters:
                    filters.append(item)

    lines = ["# MaxTAC Targeted SAST Auditor Prompt", ""]
    if args.auditor:
        lines.append(f"- Auditor: `{args.auditor}`")
    if args.focus:
        lines.append(f"- Focus: {args.focus}")
    if filters:
        lines.append(f"- Suggested auditor filters: {', '.join(filters)}")
    lines.append("")

    lines.extend(
        [
            "## Ground Rules",
            "",
            "- Treat these packets as structured triage and evidence, not as finding promotion.",
            "- Do not mark a primitive or chain as validated, proofed, or reportable from packet prose alone.",
            "- Verify actor control, reachability, guard behavior, and security impact directly against code or tool evidence.",
            "- Separate confirmed facts from assumptions, uncertain edges, and recommended follow-up.",
            "",
            "## Packet Index",
            "",
        ]
    )
    for result in results:
        status = "ok" if result["ok"] else "invalid"
        lines.append(f"- {result['source']} ({result['type']}, {status}): {packet_summary(result)}")
    lines.append("")

    lines.extend(["## Canonical Packets", ""])
    for result in results:
        spec = spec_for(result["type"])
        lines.append(f"### {spec.heading} ({result['source']})")
        lines.append("")
        lines.append(result["canonical_markdown"].rstrip())
        lines.append("")
        warnings = result.get("warnings") or []
        if warnings:
            lines.append("Lint warnings:")
            for warning in warnings:
                lines.append(f"- {warning}")
            lines.append("")

    lines.extend(
        [
            "## Auditor Task",
            "",
            "1. Decide whether the hypothesis is valid, invalid, duplicate-like, or still under-evidenced.",
            "2. Identify the narrowest reachable path from actor-controlled input to sink or protected transition.",
            "3. State whether the expected guard dominates the sink, is missing, is reordered, or is bypassable.",
            "4. Note false positives, blockers, negative evidence, and any additional CFG, OpenGrep, RE, or DAST work needed.",
            "5. Return a concise assessment with file/function references and enough reasoning for ledger triage.",
            "",
            "## Required Assessment Shape",
            "",
            "- Hypothesis reviewed:",
            "- Verdict: valid / invalid / duplicate-like / needs-more-evidence",
            "- Confidence: low / medium / high",
            "- Reviewed files/functions:",
            "- Confirmed evidence:",
            "- Missing or blocking evidence:",
            "- Security impact if valid:",
            "- Recommended ledger action:",
            "",
        ]
    )
    return "\n".join(lines)


def cmd_create(args: argparse.Namespace) -> None:
    spec = spec_for(args.type)
    values = parse_set_values(spec, args.set)
    output_text(args.output, render_packet(spec, values))


def print_lint_result(result: dict[str, Any]) -> None:
    status = "ok" if result["ok"] else "invalid"
    packet_type = result["type"] or "unknown"
    print(f"{status}: {result['source']} ({packet_type})")
    for error in result["errors"]:
        print(f"- error: {error}")
    for warning in result["warnings"]:
        print(f"- warning: {warning}")


def cmd_lint(args: argparse.Namespace) -> None:
    results = load_results(args.packet, args.type)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print_lint_result(result)

    has_errors = any(result["errors"] for result in results)
    has_warnings = any(result["warnings"] for result in results)
    if has_errors or (args.strict and has_warnings):
        raise SystemExit(1)


def cmd_prompt(args: argparse.Namespace) -> None:
    results = load_results(args.packet, args.type)
    invalid = [result for result in results if result["errors"]]
    if invalid and not args.allow_invalid:
        for result in invalid:
            print_lint_result(result)
        raise SystemExit("Refusing to convert invalid packets. Use --allow-invalid to override.")
    prompt = render_auditor_prompt(results, args)
    output_text(args.output, prompt)


def add_type_arg(parser: argparse.ArgumentParser, *, default: str = "auto") -> None:
    choices = ("auto", *TYPE_CHOICES)
    parser.add_argument("--type", choices=choices, default=default)


def add_prompt_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser], name: str) -> None:
    prompt = subparsers.add_parser(name, help="Convert packets into an auditor prompt")
    prompt.add_argument("packet", nargs="+", help="Packet markdown file; use - for stdin")
    add_type_arg(prompt)
    prompt.add_argument("--auditor", help="Target auditor id, if already selected")
    prompt.add_argument("--auditor-filter", action="append", help="Extra auditor routing filter")
    prompt.add_argument("--focus", help="One-sentence audit focus")
    prompt.add_argument("--output", help="Prompt output path; defaults to stdout")
    prompt.add_argument("--allow-invalid", action="store_true", help="Convert even when lint errors are present")
    prompt.set_defaults(func=cmd_prompt)


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC SAST packet helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a canonical packet template")
    create.add_argument("type", choices=TYPE_CHOICES)
    create.add_argument("--set", action="append", metavar="FIELD=VALUE", help="Populate a packet field")
    create.add_argument("--output", help="Packet output path; defaults to stdout")
    create.set_defaults(func=cmd_create)

    lint = subparsers.add_parser("lint", help="Validate packet structure and handoff quality")
    lint.add_argument("packet", nargs="+", help="Packet markdown file; use - for stdin")
    add_type_arg(lint)
    lint.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    lint.add_argument("--json", action="store_true")
    lint.set_defaults(func=cmd_lint)

    add_prompt_parser(subparsers, "prompt")
    add_prompt_parser(subparsers, "convert")
    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
