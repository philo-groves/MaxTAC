---
name: maxtac-source-deep-scan-loop
description: "Use this skill when MaxTAC Source needs a loop to deeply audit every security-relevant function, field, route, handler, or generated code item in a bounded code subsystem, with invariant modeling, sensitivity prioritization, item-level evidence, and auditable closure."
---

# MaxTAC Source Deep Scan Loop

Use this loop for bounded but exhaustive source review. It is heavier than Source Scan because it tracks code items inside files, such as functions, methods, structs, fields, route handlers, callbacks, generated dispatch entries, or parser productions. Use it when shallow file coverage would miss important behavior.

## Setup

1. Bound the subsystem. Name included paths, excluded paths, generated code policy, language/runtime, and target version.
2. Run Core corpus orientation and create or refresh a Core model for important invariants.
3. Initialize `maxtac-source-scan` for file-level coverage receipts when source files are in scope.
4. Create Core loop state:

```text
python3 <core-workflow-skill-dir>/scripts/loop.py init \
  --root <workspace-root> \
  --loop-id <id> \
  --kind source-deep-scan \
  --owner-plugin maxtac-source \
  --target "<subsystem>" \
  --scope "<paths and code item classes>" \
  --summary "Deep audit each function, field, route, or generated item by security sensitivity." \
  --positive-gate "Each code item is audited, closed with evidence, or deferred with a concrete blocker and owner path." \
  --negative-gate "Any security-sensitive item lacks source reachability, invariant mapping, evidence, or disposition." \
  --output "contracts/source-scans/<id>/" \
  --output "contracts/loops/<id>/" \
  --output "contracts/<result-id>/result.json"
```

5. Build the item ledger. Add loop items for functions, fields, route handlers, callbacks, parser productions, dispatch table entries, config-driven sinks, and generated-code stubs. Prioritize by security sensitivity.

## Prioritization

Use priority 5 for:

- external entrypoints, privileged transitions, authz decisions, parser length/offset handling, deserialization, command execution, filesystem mutation, secrets, unsafe memory, callbacks, or policy effects.

Use priority 4 for:

- guard helpers, object ownership, state transitions, error paths, cleanup paths, concurrency, type conversion, and boundary adapters.

Use priority 3 or lower for:

- pure formatting, tests, simple constant tables, or unreachable scaffolding, unless they feed a sensitive item.

## Iterate

For each item:

1. Identify actor, input control, state, invariant, guard, sink, caller/callee edges, and prior bug precedent.
2. Read directly related code, not the whole repository by inertia.
3. Use CFG/call graph when reachability or guard dominance is the central question.
4. Use OpenGrep when a pattern should be repeated across similar items.
5. Use targeted auditors for bug-class-specific judgment.
6. Update the item with evidence, blockers, model refs, ledger refs, and contract refs.
7. Close the matching Source Scan row or add a supporting row when the file-level receipt changes.

## Gates

Positive closure requires:

- every in-scope code item is terminal or explicitly deferred;
- high-sensitivity items have evidence and a modeled invariant or reason no invariant applies;
- surviving primitive hypotheses are in the ledger;
- file-level Source Scan validates;
- result contract validates.

Negative closure requires:

- unreviewed high-sensitivity items;
- missing generated-code owner path;
- unresolved caller/callee ambiguity;
- unmodeled invariant on a security boundary;
- source-scan rows still open.

## Output

Keep the loop worklist under `contracts/loops/<id>/`. Keep file coverage in `contracts/source-scans/<id>/`. Keep raw static outputs under `research/artifacts/` or `tmp/`. Write compact corpus notes for durable subsystem knowledge and use Core false-negative review for broad no-finding conclusions.

## Hard Rules

- Do not use this loop for an entire repository unless the repository is small enough for real item-level coverage.
- Do not mark a function closed because its file has a receipt; item-level behavior still needs a disposition.
- Do not create noisy ledger rows for every smell. Ledger entries are for surviving primitive or chain hypotheses.
- Do not continue scanning new items after repeated attention warnings; consolidate, narrow, or split the loop.
