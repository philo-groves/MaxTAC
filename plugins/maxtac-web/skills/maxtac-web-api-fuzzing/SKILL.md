---
name: maxtac-web-api-fuzzing
description: "Use this skill when web or API dynamic testing needs stateful request fuzzing, schema-backed fuzzing, parameter fuzzing, captured HTTP replay, or logic-oracle evidence."
---

# MaxTAC Web API Fuzzing

Use this skill for REST, GraphQL, HTTP, webhook, browser-request, and SaaS workflow fuzzing. Web/API fuzzing is mostly an oracle and state-model problem: the request sequence must preserve authentication, object creation, cleanup, tenant context, and the security invariant under test.

## Evidence Helper

Use `python3 <skill-dir>/scripts/fuzz-campaign.py` to create and lint web fuzzing evidence bundles under `<workspace-root>/fuzz/<campaign-id>/`.

Initialize a campaign:

```bash
python3 <skill-dir>/scripts/fuzz-campaign.py init \
  --target "billing GraphQL mutation" \
  --target-version "2026-06-28 deploy" \
  --tool Schemathesis \
  --version-command "schemathesis --version" \
  --scope "authorized staging tenant" \
  --environment "local or approved test deployment" \
  --rate-limits "10 rps, test account only" \
  --instrumentation "schema + invariant oracle" \
  --command "schemathesis run openapi.yaml --checks all" \
  --schema ./openapi.yaml
```

Attach an API or logic result:

```bash
python3 <skill-dir>/scripts/fuzz-campaign.py add-run <campaign-id> \
  --kind api \
  --api-request-sequence ./replay.har \
  --auth-context "test user in tenant A" \
  --resource-id "invoice_123" \
  --cleanup-action "delete invoice_123"
```

Before handoff, run:

```bash
python3 <skill-dir>/scripts/fuzz-campaign.py lint <campaign-id> --kind api --strict
python3 <skill-dir>/scripts/fuzz-campaign.py summary <campaign-id>
```

## Tool Selection

Read `<skill-dir>/references/web-api-fuzzing.md` for RESTler, Schemathesis, Nuclei, Burp Intruder, ZAP Fuzzer, ffuf, and replay guidance.

Prefer stateful schema or model-based fuzzing when request order matters. Use captured-traffic or parameter fuzzing only when a lower-level model is unavailable or the target workflow is mostly request-shape variation.

## Evidence Rules

Preserve the API spec, GraphQL schema, HAR/curl replay, auth context, tenant and resource IDs, cleanup actions, response bodies, relevant server logs, and the invariant being tested. Do not treat response-code differences as vulnerabilities unless they demonstrate authorization, isolation, disclosure, state corruption, or another security boundary crossing.
