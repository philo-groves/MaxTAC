# Modeling Assertions

Use this reference when a MaxTAC security model needs consistent entity, relation, invariant, formula, assumption, unknown, or contradiction wording.

## Entity Kinds

Prefer the narrowest kind that fits:

- `actor`: a human, attacker role, service account, workload, external system, or caller class.
- `principal`: an identity that can be authenticated or authorized.
- `component`: a subsystem, package, binary, module, library, or logical part.
- `service`: a network, IPC, cloud, platform, broker, worker, or daemon boundary.
- `resource`: an object acted on by the system, such as a record, file, token, package, VM, bucket, or device.
- `asset`: protected data, integrity state, execution authority, secret, account, key, tenant state, privacy data, or privileged capability.
- `entrypoint`: route, RPC, syscall, IOCTL, message handler, parser input, job trigger, webhook, UI action, CLI command, or plugin hook.
- `guard`: authorization, authentication, entitlement, sandbox, policy, signature, validation, quota, rate, state, or type check.
- `sink`: protected state transition, dangerous call, object read/write, code execution, file operation, credential use, release action, or privileged dispatch.
- `state`: protocol state, workflow state, authentication state, lifecycle state, parser state, lock/lifetime state, or release state.
- `boundary`: tenant, process, sandbox, privilege, account, subscription, project, network, origin, package, signing, or trust boundary.
- `policy`: IAM policy, RBAC rule, entitlement, sandbox profile, ACL, security group, admission rule, route guard, approval rule, or business rule.
- `data-store`: database, storage bucket, cache, filesystem area, queue, registry, key store, artifact repository, or telemetry store.
- `message`: request, token, event, packet, Mach/XPC/RPC message, webhook, claim set, package metadata, or signed statement.
- `protocol`: API, IPC, binary format, state machine, exchange flow, build pipeline, or release protocol.
- `role`: admin, owner, member, maintainer, reviewer, support, delegated identity, sandbox profile, or cloud role.
- `tenant`: customer, organization, project, account, workspace, team, subscription, namespace, realm, or app group.
- `build-artifact`: source tree, dependency, lockfile, package, container image, binary, installer, firmware, signature, attestation, or SBOM.
- `unknown`: use only while the entity class is genuinely unclear.

## Relation Predicates

Use lowercase verb phrases. Prefer existing predicates before creating a new one:

- `can_call`, `can_read`, `can_write`, `can_create`, `can_delete`, `can_execute`
- `owns`, `controls`, `contains`, `depends_on`, `trusts`, `delegates_to`
- `authenticates`, `authorizes`, `validates`, `sanitizes`, `checks`, `enforces`
- `derives_identity_from`, `impersonates`, `assumes_role`, `mints`, `signs`
- `crosses_boundary`, `enters_state`, `transitions_to`, `requires_state`
- `emits`, `receives`, `parses`, `serializes`, `stores`, `loads`
- `passes_to`, `copies_to`, `maps_to`, `resolves_to`, `dispatches_to`
- `protects`, `exposes`, `gates`, `bypasses`, `violates`, `mitigates`

If the relation is directional, put the actor/source/producer in `subject` and the target/resource/consumer in `object`.

## Invariants

Write every invariant so that another agent can test it:

```text
Only <actor or principal> may <operation> <asset or resource> when <condition>.
```

Good invariant examples:

- Only a tenant member may export tenant objects unless a global support role is active.
- A package release may be published only from a protected branch after CI provenance and maintainer approval.
- A sandboxed renderer may receive file contents only through a broker action authorized by the browser process.
- A cloud workload may assume a deployment role only when its OIDC subject matches the protected repository and branch.

Weak invariant examples:

- Access control should be correct.
- Parser input should be valid.
- The service should be secure.

## Formula Style

Formulas are compact assertions for finite, evidence-backed reasoning. Use readable first-order-logic-style text:

```text
forall user, object. can_export(user, object) -> same_tenant(user, object) or has_role(user, "support")
forall request. writes_billing_state(request) -> has_idempotency_key(request)
exists package. publishes(package, registry) and not signed_by(package, trusted_builder)
```

Keep formulas near the invariant they express. Avoid formulas that depend on facts not represented by entities, relations, assumptions, or unknowns in the same model.

## Assumptions

Use assumptions for bounded claims that are necessary for current reasoning but not yet confirmed. Include scope and evidence when an assumption is based on partial evidence.

Examples:

- The API gateway injects the tenant ID before requests reach the export service.
- The mobile client cannot directly call the internal transfer endpoint.
- CI runs in GitHub-hosted runners rather than self-hosted runners for protected releases.

## Unknowns

Use unknowns for missing facts that can change the security conclusion. Phrase them as answerable questions.

Examples:

- Does the retry path re-run authorization or reuse a cached decision?
- Which identity source is trusted when both a session tenant and route tenant are present?
- Is the parser state shared across connections after an error?

## Contradictions

Use contradictions when model assertions cannot both be true or when evidence conflicts. Reference assertion IDs when possible and set a resolution once one side is refuted or marked stale.

Examples:

- `REL-0003` says the broker authorizes file access, but `INV-0002` assumes the renderer authorizes access locally.
- Runtime evidence shows support users can export any object, while the source guard appears to require tenant membership.

## Evidence Discipline

Evidence references should be workspace-relative paths where possible. Use:

- `research/...` for synthesized durable knowledge.
- `tmp/...`, `proof/...`, `contracts/...`, or submodule `artifacts/...` for raw outputs, packet files, transcripts, and proof data.
- `workspace.sqlite:<record>` only when referring to indexed audit, debate, or ledger records with no better file artifact.

Do not mark an assertion `observed`, `confirmed`, `refuted`, or `stale` without evidence.
