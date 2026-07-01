---
name: maxtac-web-input-loop
description: "Use this skill when MaxTAC Web needs a scoped loop that models a sitemap, route or API input inventory, then systematically walks user-controllable web inputs for deep security auditing while respecting authorization, program scope, rate limits, and safety constraints."
---

# MaxTAC Web Input Loop

Use this loop to audit all user-controllable inputs in a bounded web target. It is broader than web surface triage and more structured than one-off fuzzing. It should respect program scope and rate limits at every step.

## Setup

1. Record authorized hosts, accounts, roles, tenants, rate limits, excluded paths, destructive-action rules, and data handling limits.
2. Build a sitemap or API map from allowed crawling, route docs, OpenAPI/GraphQL schemas, HAR captures, browser navigation, or source routes.
3. Model session, tenant, ownership, CSRF, idempotency, object lifecycle, and browser state with Core modeling when they influence input meaning.
4. Create Core loop state:

```text
python3 <core-workflow-skill-dir>/scripts/loop.py init \
  --root <workspace-root> \
  --loop-id <id> \
  --kind web-input \
  --owner-plugin maxtac-web \
  --target "<host, API group, or workflow>" \
  --scope "<routes, roles, tenants, and input classes>" \
  --summary "Systematically audit scoped web inputs with safety and rate-limit gates." \
  --positive-gate "Input is tested or reviewed for actor, validation, authorization, state, replay, and sink behavior with evidence and disposition." \
  --negative-gate "Input lacks safe test plan, actor model, rate-limit compliance, authorization context, or non-destructive evidence path." \
  --safety "Respect program rate limits and scope." \
  --safety "Do not perform destructive actions without explicit approval." \
  --output "research/artifacts/web-input/<id>/" \
  --output "contracts/loops/<id>/"
```

5. Add loop items for routes, parameters, forms, file uploads, GraphQL fields, RPC methods, webhooks, websocket messages, storage-controlled values, postMessage handlers, and browser-only inputs.

## Iterate

For each input:

1. Record actor, auth state, tenant/object relationship, request method, content type, source of control, expected validation, and protected sink or state transition.
2. Choose a safe audit method: manual review, replay, schema fuzzing, parameter mutation, role/tenant comparison, browser debugging, source review, or targeted auditor.
3. Test for server-side validation, authz, IDOR, tenant confusion, CSRF, replay, desync, injection, SSRF, upload handling, browser/client injection, and state-machine bypass as applicable.
4. Capture evidence: request/response, HAR, curl, browser state, source route, schema, fuzz case, or negative control.
5. Update the Core model when the input proves or refutes an invariant.
6. Update loop item, corpus, ledger, and result contract when warranted.

## Gates

Positive closure requires:

- actor and state context;
- input source and sink or state transition;
- safe method and rate-limit compliance;
- validation/authz/security disposition;
- evidence or explicit reason evidence cannot be collected safely.

Negative closure requires:

- unavailable credentials, rate-limit/scope uncertainty, destructive side effect, missing object ownership model, or unresolved browser/session state.

## Output

Keep HTTP transcripts, HARs, schemas, screenshots, and browser evidence as artifacts. Use corpus notes for durable route or workflow knowledge. Use findings ledger only for surviving primitives or chains. Use false-negative review before converting many negative input items into a broad "no issue" conclusion.

## Hard Rules

- Do not crawl or fuzz outside authorized scope.
- Do not exceed rate limits or mutate production data destructively without approval.
- Do not treat client-side validation as a server-side security control.
- Do not close an input without actor, object, and state context.
