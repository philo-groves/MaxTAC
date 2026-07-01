---
name: maxtac-source-invariant-loop
description: "Use this skill when MaxTAC Source needs a loop that models security invariants for a code subsystem, maps guards, sinks, entrypoints, callers, and proof obligations in source or decompiler output, then performs targeted audits for invariant violations."
---

# MaxTAC Source Invariant Loop

Use this loop when source review depends on what must always be true: authorization, ownership, privilege, parser bounds, state transitions, sandbox policy, file/path trust, tenant separation, or lifecycle rules. The loop turns invariants into audit targets without forcing a full deep scan.

## Setup

1. Bound the subsystem and actor model. Name protected assets, entrypoints, callers, guards, sinks, state transitions, and trust boundaries.
2. Run `maxtac-core-corpus orient` and search existing models before writing new assertions.
3. Create or update a Core model with `maxtac-core-modeling`. Observed or confirmed invariants need receipt fields: guard, sink, authority boundary, trusted callers, proof obligations, bypass assumptions, binary gaps, and refutation conditions.
4. Create Core loop state:

```text
python3 <core-workflow-skill-dir>/scripts/loop.py init \
  --root <workspace-root> \
  --loop-id <id> \
  --kind source-invariant \
  --owner-plugin maxtac-source \
  --target "<subsystem>" \
  --scope "<paths, entrypoints, and invariant family>" \
  --summary "Map source invariants to code and audit for violations." \
  --positive-gate "Invariant is confirmed, refuted, or narrowed with guard/sink/caller evidence and targeted audit disposition." \
  --negative-gate "Invariant lacks exact guard, sink, trusted caller set, proof obligation, refutation condition, or source reachability evidence." \
  --output "models/<model-id>/" \
  --output "tmp or research/artifacts invariant packets" \
  --output "ledger/contract/corpus updates"
```

5. Add one loop item per invariant or proof obligation. Good item kinds include `guard-dominance`, `caller-set`, `sink-reachability`, `state-transition`, `path-trust`, `parser-bound`, and `authority-boundary`.

## Iterate

For each invariant item:

1. Export a model-backed auditor prompt with the invariant focus.
2. Map source entrypoints to the sink using direct source reading, codebase-memory, CFG, call graph evidence, or decompiler output.
3. Verify the guard. Ask whether it is server-side, dominates all sink paths, handles errors, survives callbacks/races, and cannot be bypassed by alternate callers.
4. Verify the trusted caller set. Search direct callers, registration tables, generated bindings, tests, launch/service metadata, and reflection or dispatch mechanisms.
5. Run OpenGrep or CFG only when it will answer a repeatable proof obligation.
6. Spawn a targeted auditor when guard dominance, caller completeness, or state-machine behavior remains judgment-heavy.
7. Update model assertion status and the loop item. Promote plausible violations through the normal ledger/debate path.

## Gates

Positive closure requires:

- invariant statement and model ID;
- guard, sink, authority boundary, and trusted caller evidence;
- proof obligations resolved or converted into explicit unknowns;
- targeted audit disposition: no issue, rejected, limited, de-escalated, primitive candidate, or chain candidate;
- corpus note or model projection updated when durable architecture changed.

Negative closure requires a blocker:

- missing code path, generated code, closed binary caller, unresolved dispatch, ambiguous state transition, or missing runtime proof;
- unresolved blocker is recorded as a model unknown and loop item blocker.

## Output

Use Core model as the durable invariant dictionary. Use Source packets, CFG, OpenGrep, and source-scan receipts as evidence. Use corpus notes for narrative architecture or negative results, and ledger entries only for surviving primitive or chain hypotheses.

## Hard Rules

- Do not claim an invariant is confirmed because one obvious path has a guard.
- Do not close an invariant item without a refutation condition.
- Do not bury invariant proof obligations in prose; put them in the Core model and loop item.
- Do not let this loop become a whole-repository scan. Escalate to `maxtac-source-deep-scan-loop` when every function or field needs coverage.
