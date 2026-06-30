---
name: maxtac-web-surface-triage
description: "Use this skill when web application or API vulnerability research needs route, session, tenant, authorization, request-flow, browser-state, or business-logic surface triage."
---

# MaxTAC Web Surface Triage

Use this skill as the first pass for web applications, APIs, browser-facing services, and SaaS workflows. The goal is a compact map of actors, sessions, routes, trust boundaries, state transitions, and security invariants that can be handed to Web auditors, Source/SAST tools, API fuzzing, or browser debugging.

## Operating Rules

- Start from externally reachable routes, API methods, webhooks, jobs, callbacks, browser entrypoints, and tenant boundaries.
- Capture the actor, authentication state, authorization source, object ownership rule, state transition, and protected asset before guessing bug classes.
- Prefer a few strong hypotheses over a long checklist.
- Keep generated packets, HAR files, curl reproducers, proxy exports, and screenshots as artifacts. Rewrite durable architecture, route, tenant, and workflow knowledge into `research/`.
- Use `maxtac-source` when code-level reachability, guard dominance, or OpenGrep rules are needed.
- Use `maxtac-web-api-fuzzing` for stateful API, schema, parameter, or request-sequence fuzzing.
- Use `maxtac-web-browser-debugging` when browser state, DOM, storage, service workers, frame/process boundaries, or network timing are part of the evidence.

## Triage Workflow

1. Define the target slice: product area, host, API group, route family, tenant or organization scope, browser/client surface, and deployment or version when known.
2. Inventory entrypoints: routes, GraphQL operations, RPC methods, webhooks, file upload paths, OAuth/OIDC/SAML callbacks, admin actions, background jobs, real-time channels, and browser-controlled storage or postMessage handlers.
3. Map identity and state: credentials, session cookies, bearer tokens, CSRF state, OAuth grants, tenant IDs, object IDs, roles, entitlements, approval state, idempotency keys, and resource lifecycle state.
4. Identify protected assets and invariants: "Only actor X may do Y to object Z after condition C" is the preferred shape.
5. Rank hypotheses around missing server-side checks, state-machine bypass, IDOR, cross-tenant confusion, replay, authorization drift, unsafe interpretation, SSRF, desync, and browser/client injection.

## Web Triage Packet

```markdown
## Web Surface Triage Packet

- Target slice:
- Actor and starting state:
- Protected asset or trust boundary:
- Entrypoints:
- Session and identity material:
- Tenant or ownership model:
- Controlled inputs:
- Security invariant:
- Suspect guard, sink, or state transition:
- Browser/client state involved:
- Key files/routes/handlers:
- Evidence collected:
- Evidence still needed:
- Suggested tools: Source/SAST / Web API fuzzing / Browser debugging / Auditors
- Suggested auditor filters:
- Candidate hypothesis:
- Confidence: low / medium / high
```

## Auditor Routing

Use the Web pack's auditor MCP tools when available. If those tools are not exposed in the current context, use Core's local fallback: `python3 <maxtac-core-subagents-skill-dir>/scripts/audit-helper.py --catalog web --filter <term>`. Good starting filters include `authz`, `tenant`, `idor`, `oauth`, `saml`, `session`, `replay`, `approval`, `payment`, `ssrf`, `sql-injection`, `xss`, `websocket`, `http`, and `business-logic`.
