---
name: maxtac-core-contracts
description: "Use this skill when MaxTAC research needs canonical machine-readable result contracts, finding schemas, coverage closure records, deterministic report projection, or conversion from primitive/chain ledgers into a sealed review bundle."
---

# MaxTAC Core Contracts

Use this skill to turn MaxTAC research state into a machine-readable result bundle before final reporting, handoff, tracking, or source-scan closure. The contract complements `maxtac-core-ledger`: ledgers track long-running primitive and chain state, while result contracts capture one bounded review result with findings, coverage, evidence references, limitations, and a deterministic report projection.

## Contract Paths

Store canonical result bundles under the workspace root:

```text
contracts/<result-id>/
  result.json
  report.md
```

Use `scripts/contract.py` instead of hand-editing `result.json` when creating, validating, or projecting a bundle.

## Workflow

1. Create or import a result bundle.
   - For a fresh source scan or bounded review, run `init`.
   - For an existing MaxTAC workspace with useful primitive or chain ledgers, run `from-ledger`.
2. Add findings and coverage surfaces as work closes.
3. Keep affected locations concrete. Include root-control, entrypoint, sink, or proof-artifact labels when they matter.
4. Mark every reviewed surface with one disposition: `reported`, `no_issue_found`, `rejected`, `not_applicable`, `needs_follow_up`, or `deferred`.
5. Run `validate` before using a contract for reporting or handoff.
6. Run `finalize` to write the deterministic `report.md` projection.

## Commands

Create a new bundle:

```text
python <skill-dir>/scripts/contract.py init --root <workspace-root> --result-id <id> --target "<target>" --kind source_scan --include .
```

Convert current ledgers into a bundle:

```text
python <skill-dir>/scripts/contract.py from-ledger --root <workspace-root> --result-id <id> --target "<target>"
```

Add a finding:

```text
python <skill-dir>/scripts/contract.py add-finding <result.json> --title "Missing authorization on export" --type chain --state proofed --severity high --confidence medium --category "Authorization bypass" --location "root_control:src/export.py:88" --evidence "proof/export-pov.md" --summary "..."
```

Attach a model or invariant reference to a result or finding:

```text
python <skill-dir>/scripts/contract.py add-model-ref <result.json> --kind invariant --model-id export-api --assertion-id INV-0001 --note "Finding violates the tenant export invariant."
python <skill-dir>/scripts/contract.py add-model-ref <result.json> --finding-id M-0004 --kind invariant --model-id export-api --assertion-id INV-0001
```

Add or close a coverage surface:

```text
python <skill-dir>/scripts/contract.py add-surface <result.json> --surface "Export API routes" --risk-area authz --disposition reported --receipt "contracts/source-scans/export-api/work_ledger.jsonl" --notes "Covered route handlers and shared export helper."
```

Validate and project:

```text
python <skill-dir>/scripts/contract.py validate <result.json>
python <skill-dir>/scripts/contract.py finalize <result.json>
```

## Field Guidance

- `severity`: use `critical`, `high`, `medium`, `low`, or `informational`.
- `confidence`: use `high`, `medium`, or `low`, calibrated from proof quality.
- `state`: preserve MaxTAC states such as `discovered`, `confident`, `validated`, `proofed`, `duplicate`, `limited`, and `de-escalated`.
- `affected_locations`: use `label:path:lines` for command input, for example `sink:src/archive.py:142-151`.
- `evidence`: point at workspace-relative audit, proof, fuzzing, source-scan, or artifact paths.
- `model_refs`: point at `maxtac-core-modeling` model IDs and assertion IDs when a finding, coverage decision, or bounded result depends on a modeled entity, relation, invariant, formula, assumption, unknown, or contradiction.
- `coverage.receipt_refs`: point at artifacts that prove the reviewed surface was covered or explicitly deferred.

Read `schemas/result-bundle.schema.json` only when exact schema shape matters.

## Hard Rules

- Do not treat a ledger entry as report-ready just because it exists. The contract must preserve severity, confidence, locations, evidence, validation, attack path or proof gap, and coverage disposition.
- Do not silently drop reviewed-but-rejected surfaces. Record them as coverage.
- Do not put raw tool logs in `result.json`; store logs as artifacts and reference them.
- Do not author `report.md` by hand when a canonical `result.json` exists. Update the contract and regenerate the report.
- Do not use model references as evidence by themselves. They preserve context and invariant IDs; proof still needs audit, validation, proof, or coverage artifacts.
