# MaxTAC Core

MaxTAC Core is the required base pack for MaxTAC research. It owns the research workflow, workspace structure, faceted research corpus, security models, invariant dictionaries and receipts, domain loop state, finding ledgers, thin/full closure profiles, false-negative review, result contracts, report projection, and goal-bounded auditor or verifier orchestration.

Install this pack for every MaxTAC engagement, then add only the domain packs needed by the target.

## When To Use

- Starting or continuing an authorized MaxTAC vulnerability research session.
- Writing, importing, searching, linking, and orienting durable research notes through a faceted corpus instead of hand-grown directory trees.
- Building and querying durable security models, invariant dictionaries, invariant receipts, first-order-logic-style assertions, assumptions, unknowns, and contradictions.
- Keeping bounded domain loops alive across turns, subagents, and validation gates without turning the prompt into the only controller.
- Scoring negative evidence and planning adversarial reopen passes after long no-finding sessions.
- Tracking primitives, chains, validation state, proof state, duplicates, and de-escalations.
- Creating canonical result bundles with coverage, findings, evidence, limitations, and deterministic report output.
- Closing tiny non-reportable targets with thin result bundles, proof evidence, and reopen criteria instead of a full artifact train.
- Routing focused auditor and verifier-debate subagents.
- Keeping durable research notes, generated views, raw artifacts, and transient review artifacts separate.

## Skills

- `maxtac-core-workflow`: standard MaxTAC phases, workspace layout, domain loop state, validation, proof, false-negative review, and reporting flow.
- `maxtac-core-corpus`: faceted research corpus notes, tags, graph edges, generated views, import, search, lint, and anti-tunnel orientation packs.
- `maxtac-core-modeling`: security models, invariant dictionaries, invariant receipts, architecture relations, first-order-logic-style assertions, assumptions, unknowns, contradictions, and model-backed auditor handoffs.
- `maxtac-core-ledger`: finding state tracking, deduplication, promotion, de-escalation, and report linkage.
- `maxtac-core-subagents`: goal-bounded auditor and verifier-debate subagent guidance, SQLite-backed auditor registry lookup, and prompt enrichment with corpus/model context.
- `maxtac-core-contracts`: machine-readable result contracts, thin closure bundles, coverage closure, schemas, and report projection.

## Typical Pairings

- Core + Source for source-code review, diff scans, intake, CFG, and OpenGrep evidence.
- Core + Binary for reverse engineering, native debugging, crash replay, and systems fuzzing.
- Core + Web for web, API, session, tenant, and browser-state research.
- Core + Cloud for AWS, Azure, GCP, IAM, storage, runtime metadata, workload identity, and cloud network boundary research.
- Core + Supply Chains for packages, CI/CD, provenance, signing, containers, and release paths.
- Core + program packs such as Android, Apple Systems, or Microsoft Systems when the program requires specialized proof workflows.

## Output Artifacts

Core expects research artifacts such as:

- `research/notes/` canonical compact research notes.
- `research/views/` generated corpus indexes and graph projections.
- `research/artifacts/` raw corpus artifacts and imported legacy markdown.
- `models/` security models, invariant dictionaries, model graphs, and proof obligations.
- `workspace.sqlite` primitive and chain findings, corpus documents, corpus tags, corpus graph edges, model assertions, debate tallies, audit assessments, related evidence, milestones, and workspace search memory.
- `$CODEX_HOME/maxtac/auditors.sqlite` active-plugin auditor registry with duplicate prevention and FTS search.
- `proof/` proof-of-vulnerability artifacts.
- `contracts/` canonical result bundles, loop state, false-negative reviews, and generated report projections.
- `reporting/` submission-ready report projections.

## Boundary

Core does not contain source, binary, web, cloud, supply-chain, Android, Apple, or Microsoft-specific exploitation guidance. Use domain packs for target-specific research direction.

Core rebuilds the global auditor registry from active plugin catalogs at session start. Use Core's helper for every auditor lookup:

```text
python3 plugins/maxtac-core/skills/maxtac-core-subagents/scripts/audit-helper.py --catalogs
python3 plugins/maxtac-core/skills/maxtac-core-subagents/scripts/audit-helper.py --catalog web --filter auth
```

If plugins changed during a running session, refresh the registry with:

```text
python3 plugins/maxtac-core/skills/maxtac-core-subagents/scripts/auditor_registry.py rebuild
```
