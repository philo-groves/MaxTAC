---
name: maxtac-core-modeling
description: "Use this skill when MaxTAC research needs a durable security model, invariant dictionary, architecture understanding, first-order-logic-style assertions, unknown tracking, contradiction tracking, or model-backed auditor handoffs across source, web, cloud, binary, supply-chain, Android, Apple, or Microsoft targets."
---

# MaxTAC Core Modeling

Use this skill to turn scattered architecture and security observations into a durable model that future MaxTAC sessions can query and reuse. The model captures entities, trust relationships, invariants, bounded first-order-logic-style formulas, assumptions, unknowns, contradictions, and evidence links. It complements the `research/` library: prose explains the system, while `models/` keeps a machine-readable dictionary of what is believed, why, and how confident that belief is.

## Storage Contract

Store model bundles under the workspace root:

```text
models/<model-id>/
  model.json       # canonical machine-readable security model
  invariants.md   # projected invariant dictionary
  obligations.md  # projected unknowns, assumptions, and open proof obligations
  graph.mmd        # projected Mermaid relationship graph
```

Use `scripts/model.py` instead of hand-editing `model.json` when creating, validating, projecting, searching, or exporting auditor prompts.

## Workflow

1. Create or select a model for the target system, product area, subsystem, protocol, policy engine, or chain boundary.
2. Add entities before relations. Entities should represent actors, principals, services, components, resources, entrypoints, guards, sinks, states, assets, trust boundaries, policies, roles, tenants, or build artifacts.
3. Add relations for meaningful security edges: who can call whom, what owns or controls what, where identity comes from, which guard authorizes an operation, which state transition protects an asset, and which trust boundary is crossed.
4. Add invariants in one-sentence form: "Only X may do Y to Z when C." Add a formula when the rule can be expressed compactly.
5. Add assumptions and unknowns explicitly instead of letting them disappear into prose.
6. Mark contradictions when two assertions cannot both be true. Do not silently delete stale beliefs; mark them `stale` or `refuted` and preserve evidence.
7. Run `validate` and `project` after meaningful model edits.
8. Use `export-prompt` before auditor or debater handoff so the subagent sees confirmed facts, candidate assertions, formulas, unknowns, and warnings in a compact format.

## Commands

Create a model:

```text
python3 <skill-dir>/scripts/model.py init --root <workspace-root> --model-id <id> --target "<target>" --kind subsystem --summary "..."
```

Add an entity:

```text
python3 <skill-dir>/scripts/model.py add-entity models/<id>/model.json --kind service --name "Export API" --description "Handles tenant data exports." --status observed --confidence medium --evidence research/export/api.md
```

Add a relation:

```text
python3 <skill-dir>/scripts/model.py add-relation models/<id>/model.json --subject ENT-0001 --predicate authorizes --object ENT-0003 --description "Export API checks the tenant policy guard before object reads." --status observed --confidence medium --evidence research/export/api.md
```

Add an invariant:

```text
python3 <skill-dir>/scripts/model.py add-invariant models/<id>/model.json --statement "Only a user in the object's tenant may export that object unless they hold the global support role." --scope "Tenant export workflow" --formula 'forall user, object. can_export(user, object) -> same_tenant(user, object) or has_role(user, "support")' --status candidate --confidence medium
```

Track a missing fact:

```text
python3 <skill-dir>/scripts/model.py add-unknown models/<id>/model.json --question "Does webhook replay reuse the original tenant authorization decision?" --scope "Webhook retry state machine"
```

Validate and project:

```text
python3 <skill-dir>/scripts/model.py validate models/<id>/model.json --strict
python3 <skill-dir>/scripts/model.py project models/<id>/model.json
```

Search indexed models:

```text
python3 <skill-dir>/scripts/model.py search --root <workspace-root> --query "tenant export same_tenant"
```

Export a model-backed auditor prompt:

```text
python3 <skill-dir>/scripts/model.py export-prompt models/<id>/model.json --focus "Check whether the export guard dominates all object reads." --output tmp/export-model-auditor-prompt.md
```

## Assertion Status

- `candidate`: plausible but not proven by direct evidence.
- `observed`: seen in code, runtime behavior, documentation, or artifacts, but not yet treated as a stable security conclusion.
- `confirmed`: supported by evidence strong enough for future sessions to rely on.
- `refuted`: previously proposed but disproven.
- `stale`: once useful but superseded by a version, architecture, or evidence change.

Any `observed`, `confirmed`, `refuted`, or `stale` assertion must include at least one evidence reference. Keep vulnerability claims out of the model until they are validated through the ledger/debate flow; model invariant violations can seed hypotheses, but they are not findings by themselves.

## Formula Guidance

Use formulas as compact, bounded assertions, not as unconstrained theorem-prover input. Prefer readable first-order-logic-style clauses:

```text
forall actor, object. can_read(actor, object) -> same_tenant(actor, object) or has_role(actor, "admin")
exists request. crosses_boundary(request, "browser", "api") and lacks_csrf_token(request)
```

Use the same predicate names consistently within a model. If a predicate is only a guess, keep the related formula `candidate` and add an unknown for the missing evidence. Read `references/modeling-assertions.md` when exact assertion conventions matter.

## Handoff Rules

- Query the model before spawning auditors for a modeled subsystem.
- Pass model exports to auditors as context, not as proof.
- Ask auditors to confirm, refute, or narrow specific assertions and unknowns.
- After an audit, update both the model and the relevant research note when durable system knowledge changed.
- Link ledger findings to violated invariant IDs when a finding depends on an invariant break.

## Resources

- `scripts/model.py`: canonical security model helper.
- `schemas/security-model.schema.json`: JSON schema for `model.json`.
- `references/modeling-assertions.md`: conventions for entities, relations, invariants, formulas, assumptions, unknowns, and contradictions.
