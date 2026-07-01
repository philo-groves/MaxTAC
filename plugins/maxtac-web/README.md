# MaxTAC for Web

MaxTAC for Web adds web application, API, browser-state, session, tenant, SaaS research workflows, and scoped web input loops.

Use this pack with MaxTAC Core when the target is a web app, API, browser-mediated workflow, SaaS control plane, tenant boundary, or stateful HTTP surface.

## When To Use

- Web and API surface triage.
- Stateful API fuzzing, schema-backed fuzzing, captured HTTP replay, and logic-oracle evidence.
- Browser debugging, DOM/storage evidence, request timing, frame/process state, CDP, WebDriver BiDi, or WebKit inspection.
- Session, tenant, authorization, request-flow, and business-logic mapping.
- Scoped input loops that model a sitemap, route inventory, actors, sessions, and input worklist before deep input auditing.
- Webhook, OAuth app, package registry API, or SaaS workflow investigation.

## Skills

- `maxtac-web-surface-triage`: route, session, tenant, authorization, browser-state, and business-logic surface triage.
- `maxtac-web-api-fuzzing`: stateful request fuzzing, schema-backed fuzzing, parameter fuzzing, and replay.
- `maxtac-web-browser-debugging`: browser debugging, protocol instrumentation, DOM/storage evidence, timing, and process/frame state.
- `maxtac-web-input-loop`: scoped sitemap and input worklist loop for systematic web input auditing under program scope and rate limits.

## Typical Pairings

- Web + Source when implementation code, route handlers, or API services are available.
- Web + Cloud when SSRF, cloud-hosted APIs, control-plane consoles, OAuth/OIDC federation, signed URLs, or cloud metadata paths matter.
- Web + Supply Chains when the path depends on package registries, webhooks, OAuth apps, SaaS CI/CD, or release consoles.
- Web + Android or Apple Systems when mobile apps rely on webviews, APIs, account flows, or browser-mediated proof.

## Output Artifacts

Web workflows commonly produce:

- Route and request-flow maps.
- `contracts/loops/<loop-id>/` Web input loop worklists, gates, events, and next-action prompts.
- Captured HTTP transcripts and replay plans.
- Fuzzing cases, state machines, and logic-oracle evidence.
- Browser storage, DOM, frame, and protocol evidence.
- Tenant/session boundary notes.

## Boundary

This pack does not own source-code static analysis, binary reverse engineering, cloud IAM/runtime proof, package compromise hunting, or program-specific platform proof. Pair with the relevant pack for those paths.
