#!/usr/bin/env python3
"""Create and lint ASB target-flag proof packets."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
from pathlib import Path
import re
import sys


REQUIRED_HEADINGS = [
    "# ASB Proof Packet",
    "## Target Flag Claim",
    "## Target Identity",
    "## Environment",
    "## Primitive Chain",
    "## Commpage Or TCC Workflow",
    "## Positive Proof",
    "## Negative Control",
    "## Artifact Index",
    "## Submission Notes",
]

PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|UNKNOWN)\b|<[^>\n]+>", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_packet(args: argparse.Namespace) -> str:
    today = _dt.date.today().isoformat()
    case_id = args.case_id or "TBD"
    flag_type = args.flag_type or "TBD"
    target = args.target or "TBD"
    build = args.build or "TBD"
    primitive = args.primitive or "TBD"
    workflow = args.workflow or "TBD"

    artifact_lines = []
    for artifact in args.artifact or []:
        path = Path(artifact)
        if path.exists() and path.is_file():
            artifact_lines.append(f"- `{path}`: sha256 `{sha256_file(path)}`")
        else:
            artifact_lines.append(f"- `{path}`: missing at packet creation time")
    if not artifact_lines:
        artifact_lines.append("- TBD")

    return f"""# ASB Proof Packet: {case_id}

Created: {today}

## Target Flag Claim

- Flag type: {flag_type}
- Claimed capability: {primitive}
- Eligibility rationale: TBD

## Target Identity

- Target: {target}
- Process, service, or kernel path: TBD
- Bundle ID or binary path: TBD
- Code-signing identity and entitlements: TBD
- Sandbox, TCC, broker, or kernel context: TBD

## Environment

- Build: {build}
- Hardware model or board: TBD
- Architecture: TBD
- Security state caveats: TBD
- PoV invocation: TBD

## Primitive Chain

- Vulnerability path: TBD
- Attacker-controlled input: TBD
- Sink reached by the target: TBD
- Why the proof is attributable to the vulnerable target: TBD

## Commpage Or TCC Workflow

- Workflow: {workflow}
- Commpage values and addresses or TCC baseline: TBD
- Capture method: TBD
- Reset or cleanup method: TBD

## Positive Proof

- Observation: TBD
- Crash, panic, log, transcript, or screenshot: TBD
- Registers, fault address, memory result, or TCC output: TBD

## Negative Control

- Control used: TBD
- Expected result: TBD
- Observed result: TBD

## Artifact Index

{chr(10).join(artifact_lines)}

## Submission Notes

- Reproduction notes: TBD
- Limitations and caveats: TBD
- Reviewer should verify: TBD
"""


def create_packet(args: argparse.Namespace) -> int:
    output = Path(args.output)
    if output.exists() and not args.force:
        print(f"refusing to overwrite existing packet: {output}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_packet(args), encoding="utf-8", newline="\n")
    print(f"created ASB proof packet: {output}")
    return 0


def lint_packet(args: argparse.Namespace) -> int:
    packet = Path(args.packet)
    if not packet.exists():
        print(f"packet not found: {packet}", file=sys.stderr)
        return 2
    text = packet.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing heading: {heading}")

    if args.strict:
        placeholders = sorted(set(match.group(0) for match in PLACEHOLDER_RE.finditer(text)))
        if placeholders:
            errors.append("strict packet still has placeholders: " + ", ".join(placeholders[:10]))

    if "## Positive Proof" in text and "## Negative Control" in text:
        positive = text.split("## Positive Proof", 1)[1].split("## Negative Control", 1)[0]
        negative = text.split("## Negative Control", 1)[1].split("## Artifact Index", 1)[0]
        if PLACEHOLDER_RE.search(positive):
            warnings.append("positive proof section still appears incomplete")
        if PLACEHOLDER_RE.search(negative):
            warnings.append("negative control section still appears incomplete")

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)

    if errors:
        return 1
    print(f"packet lint passed: {packet}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC ASB proof packet helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create an ASB proof packet template")
    create.add_argument("--output", required=True, help="Markdown packet path to write")
    create.add_argument("--case-id", default="")
    create.add_argument("--flag-type", choices=["commpage", "tcc", "commpage-kernel", "mixed"], default="")
    create.add_argument("--target", default="")
    create.add_argument("--build", default="")
    create.add_argument("--primitive", default="")
    create.add_argument("--workflow", default="")
    create.add_argument("--artifact", action="append", default=[])
    create.add_argument("--force", action="store_true")
    create.set_defaults(func=create_packet)

    lint = subparsers.add_parser("lint", help="Check an ASB proof packet")
    lint.add_argument("packet", help="Markdown packet path to lint")
    lint.add_argument("--strict", action="store_true", help="Fail if placeholders remain")
    lint.set_defaults(func=lint_packet)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
