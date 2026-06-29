# MaxTAC Core

MaxTAC Core is the required base pack for MaxTAC research. It owns the research workflow, workspace structure, finding ledgers, result contracts, report projection, and goal-bounded auditor or verifier orchestration.

Install this pack for every MaxTAC engagement, then add only the domain packs needed by the target.

## When To Use

- Starting or continuing an authorized MaxTAC vulnerability research session.
- Tracking primitives, chains, validation state, proof state, duplicates, and de-escalations.
- Creating canonical result bundles with coverage, findings, evidence, limitations, and deterministic report output.
- Routing focused auditor and verifier-debate subagents.
- Keeping durable research notes separate from transient audit artifacts.

## Skills

- `maxtac-core-workflow`: standard MaxTAC phases, workspace layout, validation, proof, and reporting flow.
- `maxtac-core-ledger`: finding state tracking, deduplication, promotion, de-escalation, and report linkage.
- `maxtac-core-subagents`: goal-bounded auditor and verifier-debate subagent guidance.
- `maxtac-core-contracts`: machine-readable result contracts, coverage closure, schemas, and report projection.

## Typical Pairings

- Core + Source for source-code review, diff scans, intake, CFG, and OpenGrep evidence.
- Core + Binary for reverse engineering, native debugging, crash replay, and systems fuzzing.
- Core + Web for web, API, session, tenant, and browser-state research.
- Core + Supply Chains for packages, CI/CD, provenance, signing, containers, and release paths.
- Core + program packs such as Android, Apple Systems, or Microsoft Systems when the program requires specialized proof workflows.

## Output Artifacts

Core expects research artifacts such as:

- `research/` durable notes.
- `findings/` primitive and chain ledgers.
- `audits/` auditor packets and receipts.
- `proof/` proof-of-vulnerability artifacts.
- `contracts/` canonical result bundles.
- `reporting/` submission-ready report projections.

## Boundary

Core does not contain source, binary, web, supply-chain, Android, Apple, or Microsoft-specific exploitation guidance. Use domain packs for target-specific research direction.
