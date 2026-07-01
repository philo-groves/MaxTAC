# MaxTAC for Source

MaxTAC for Source adds static-analysis workflows for source code and existing decompiler output, including bundled codebase-memory-mcp graph integration, patch-history correlation loops, invariant-driven source loops, and deep source scan loops. It is for evidence-driven source review, not reverse engineering itself.

Use this pack with MaxTAC Core when the target includes source code, generated code, decompiled code, code-scanning findings, exact-path thin closures, negative-evidence source inputs, source diffs, invariant worklists, or function/field inventories that need auditable closure.

## When To Use

- Static surface triage over source code or existing decompiler output.
- codebase-memory-mcp architecture, graph, symbol, route, call-path, ADR, and diff-impact queries before source triage, launched through this plugin's MCP registration.
- Git-backed diff scans, repository scans, or scoped-path source reviews.
- CVE, advisory, release-note, and patch-history correlation that should enrich a threat model without overclaiming reachability.
- Invariant-driven audits that model guards, sinks, authority boundaries, proof obligations, and refutation conditions before targeted review.
- Deep source scans that maintain item-level ledgers for functions, fields, routes, handlers, generated code, and security-sensitive data flows.
- Thin exact-path source closure for tiny non-reportable helpers or file families, with Core false-negative review when many negative receipts become a broader conclusion.
- External finding intake from SARIF, GitHub code scanning, Dependabot, advisories, scanner JSON, tickets, or freeform reports.
- Control-flow, call-graph, guard dominance, callback, cleanup, and source-to-sink evidence.
- OpenGrep rule authoring and static result interpretation.

## Skills

- `maxtac-sast-surface-triage`: maps trust boundaries, entrypoints, sinks, invariants, and route hypotheses.
- `maxtac-source-codebase-memory`: plugin-bundled codebase-memory-mcp indexing, architecture queries, graph search, call-path tracing, diff-impact mapping, and ADR lookup.
- `maxtac-sast-opengrep`: OpenGrep rules, static vulnerability searches, taint/pattern matching, and evidence packaging.
- `maxtac-sast-control-flow-graph`: static CFG/call-graph evidence for reachability and path reasoning.
- `maxtac-source-scan`: deterministic source worklists, thin exact-path closure, coverage receipts, negative-evidence inputs, closure validation, and result-contract output.
- `maxtac-source-finding-intake`: normalize and triage external security findings against a repository.
- `maxtac-source-patch-history-loop`: correlate source commits, tags, advisories, CVEs, release notes, and quiet hardening into threat-model evidence and follow-up work.
- `maxtac-source-invariant-loop`: model source invariants and audit the exact code responsible for preserving or violating them.
- `maxtac-source-deep-scan-loop`: build and execute a prioritized item ledger for exhaustive function, field, route, handler, and source-object review.

## Typical Pairings

- Core + Source for source-only reviews.
- Source + Binary when decompiler output becomes the static evidence layer.
- Source + Android when JADX output or Android source needs static triage.
- Source + Web when backend routes, handlers, or API implementation code are available.
- Source + Cloud when infrastructure-as-code, policy code, cloud service handlers, or deployment scripts determine the boundary.
- Source + Supply Chains when package or CI/CD questions depend on source-level reachability.

## Output Artifacts

Source workflows commonly write:

- `contracts/source-scans/<scan-id>/` worklists, coverage rows, and receipts.
- `contracts/loops/<loop-id>/` Source loop worklists, gates, events, and next-action prompts.
- `contracts/intake/<intake-id>/` normalized external findings.
- CFG, call graph, and OpenGrep evidence under `tmp/` or the relevant research artifact directory.
- Codebase Memory packets from graph, architecture, ADR, and diff-impact queries.
- Core result contracts under `contracts/<result-id>/`.

## Boundary

This pack does not own binary lifting, debugger work, firmware extraction, browser instrumentation, cloud control-plane proof, or package registry investigation. Pair it with the relevant domain pack when those surfaces are needed.
