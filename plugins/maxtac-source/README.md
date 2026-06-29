# MaxTAC for Source

MaxTAC for Source adds static-analysis workflows for source code and existing decompiler output. It is for evidence-driven source review, not reverse engineering itself.

Use this pack with MaxTAC Core when the target includes source code, generated code, decompiled code, code-scanning findings, or source diffs that need auditable closure.

## When To Use

- Static surface triage over source code or existing decompiler output.
- Git-backed diff scans, repository scans, or scoped-path source reviews.
- External finding intake from SARIF, GitHub code scanning, Dependabot, advisories, scanner JSON, tickets, or freeform reports.
- Control-flow, call-graph, guard dominance, callback, cleanup, and source-to-sink evidence.
- OpenGrep rule authoring and static result interpretation.

## Skills

- `maxtac-sast-surface-triage`: maps trust boundaries, entrypoints, sinks, invariants, and route hypotheses.
- `maxtac-sast-opengrep`: OpenGrep rules, static vulnerability searches, taint/pattern matching, and evidence packaging.
- `maxtac-sast-control-flow-graph`: static CFG/call-graph evidence for reachability and path reasoning.
- `maxtac-source-scan`: deterministic source worklists, coverage receipts, closure validation, and result-contract output.
- `maxtac-source-finding-intake`: normalize and triage external security findings against a repository.

## Typical Pairings

- Core + Source for source-only reviews.
- Source + Binary when decompiler output becomes the static evidence layer.
- Source + Android when JADX output or Android source needs static triage.
- Source + Web when backend routes, handlers, or API implementation code are available.
- Source + Cloud when infrastructure-as-code, policy code, cloud service handlers, or deployment scripts determine the boundary.
- Source + Supply Chains when package or CI/CD questions depend on source-level reachability.

## Output Artifacts

Source workflows commonly write:

- `audits/source-scans/<scan-id>/` worklists, coverage rows, and receipts.
- `audits/intake/<intake-id>/` normalized external findings.
- CFG, call graph, and OpenGrep evidence under the active audit directory.
- Core result contracts under `contracts/<result-id>/`.

## Boundary

This pack does not own binary lifting, debugger work, firmware extraction, browser instrumentation, cloud control-plane proof, or package registry investigation. Pair it with the relevant domain pack when those surfaces are needed.
