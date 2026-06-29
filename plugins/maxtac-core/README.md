# MaxTAC Core

MaxTAC Core is the required base pack for MaxTAC research. It owns the research workflow, workspace structure, security models, invariant dictionaries, finding ledgers, result contracts, report projection, and goal-bounded auditor or verifier orchestration.

Install this pack for every MaxTAC engagement, then add only the domain packs needed by the target.

## When To Use

- Starting or continuing an authorized MaxTAC vulnerability research session.
- Building and querying durable security models, invariant dictionaries, first-order-logic-style assertions, assumptions, unknowns, and contradictions.
- Tracking primitives, chains, validation state, proof state, duplicates, and de-escalations.
- Creating canonical result bundles with coverage, findings, evidence, limitations, and deterministic report output.
- Routing focused auditor and verifier-debate subagents.
- Keeping durable research notes separate from transient review artifacts.

## Skills

- `maxtac-core-workflow`: standard MaxTAC phases, workspace layout, validation, proof, and reporting flow.
- `maxtac-core-modeling`: security models, invariant dictionaries, architecture relations, first-order-logic-style assertions, assumptions, unknowns, contradictions, and model-backed auditor handoffs.
- `maxtac-core-ledger`: finding state tracking, deduplication, promotion, de-escalation, and report linkage.
- `maxtac-core-subagents`: goal-bounded auditor and verifier-debate subagent guidance.
- `maxtac-core-contracts`: machine-readable result contracts, coverage closure, schemas, and report projection.

## Typical Pairings

- Core + Source for source-code review, diff scans, intake, CFG, and OpenGrep evidence.
- Core + Binary for reverse engineering, native debugging, crash replay, and systems fuzzing.
- Core + Web for web, API, session, tenant, and browser-state research.
- Core + Cloud for AWS, Azure, GCP, IAM, storage, runtime metadata, workload identity, and cloud network boundary research.
- Core + Supply Chains for packages, CI/CD, provenance, signing, containers, and release paths.
- Core + program packs such as Android, Apple Systems, or Microsoft Systems when the program requires specialized proof workflows.

## Output Artifacts

Core expects research artifacts such as:

- `research/` durable notes.
- `models/` security models, invariant dictionaries, model graphs, and proof obligations.
- `workspace.sqlite` primitive and chain findings, model assertions, debate tallies, audit assessments, related evidence, milestones, and search memory.
- `proof/` proof-of-vulnerability artifacts.
- `contracts/` canonical result bundles.
- `reporting/` submission-ready report projections.

## Boundary

Core does not contain source, binary, web, cloud, supply-chain, Android, Apple, or Microsoft-specific exploitation guidance. Use domain packs for target-specific research direction.
