---
name: maxtac-source-finding-intake
description: "Use this skill when MaxTAC needs to import, normalize, and statically triage external security findings such as SARIF, GitHub code scanning or Dependabot exports, CVE/GHSA advisories, scanner JSON, bug bounty reports, Jira or Linear ticket text, or freeform vulnerability claims against a repository."
---

# MaxTAC Source Finding Intake

Use this skill for backlog burn-down and external finding triage. It starts from claims that already exist, normalizes them into a stable intake file, then uses static repository evidence to classify each item as `confirmed`, `not_actionable`, or `needs_review`.

This is not a source scan. Do not claim exhaustive coverage, run PoCs, or edit code while using this skill.

## Intake Artifacts

Store intake bundles under:

```text
contracts/intake/<intake-id>/
  raw/
  intake.json
```

`intake.json` uses `schema_version: maxtac.intake/v1`. Read `references/intake-contract.md` only when exact field shape matters.

## Normalize

Normalize local SARIF, scanner JSON, GitHub alert JSON, advisory text, ticket text, or freeform claims:

```text
python <skill-dir>/scripts/finding_intake.py normalize --root <workspace-root> --repo <repo-path> --input findings.sarif --source-type sarif --intake-id <id>
```

If `--source-type auto` is used, the helper detects SARIF-like JSON, GitHub code-scanning alerts, Dependabot alerts, generic JSON, or freeform text.

For GitHub, Jira, or Linear, first retrieve the exact content through the available connector, CLI, or API authorized by the user, save it under `contracts/intake/<id>/raw/`, then normalize that saved file. Preserve source URLs and issue IDs in the normalized item references.

## Static Triage

For each normalized item:

1. Read repository policy such as `SECURITY.md`, supported-version docs, program rules, or `program-info.md` when available.
2. Inspect the smallest relevant code/config/dependency evidence set.
3. Identify source, control, sink, reachable path, boundary, counterevidence, and proof gaps.
4. Assign:
   - `confirmed`: static evidence connects the claim to reachable code and a supported security boundary.
   - `not_actionable`: static evidence defeats the claim.
   - `needs_review`: evidence is ambiguous, runtime-only, policy-dependent, or blocked.
5. Rank `confirmed` and `needs_review` queues separately by exploitability.
6. For confirmed items, add a prompt-ready handoff to `maxtac-core-contracts`, `maxtac-source-scan`, or `maxtac-core-ledger`.

Use the helper to validate and summarize the normalized file:

```text
python <skill-dir>/scripts/finding_intake.py validate contracts/intake/<id>/intake.json
python <skill-dir>/scripts/finding_intake.py summarize contracts/intake/<id>/intake.json
```

## Boundary Gate

Before marking an item `confirmed`, identify:

- product surface: hosted service, library API, CLI, local developer UI, plugin hook, example/demo, test/fixture, docs, generated code, vendored code, or unknown
- source trust: untrusted user input, tenant/user-controlled data, remote attacker input, trusted operator input, trusted developer configuration, local-only input, intentionally code-executing extension point, or unknown
- policy basis: `SECURITY.md`, program scope, product docs, package/deploy metadata, code comments, threat model, or unknown

A dangerous sink alone is not enough for `confirmed`.

## Hard Rules

- Do not invent scanner severity, generated finding IDs, remediation, or source locations that the input did not provide.
- Do not deduplicate inputs during intake. Keep one normalized item per supplied finding; record duplicate suspicion as evidence or counterevidence.
- Do not mark `confirmed` without a reachable path and supported security boundary.
- Do not mark `not_actionable` just because runtime proof is missing. Use `needs_review` for unresolved proof gaps.
- Do not mutate Jira, Linear, GitHub, or scanner systems from this skill. Tracking belongs in a future optional workflow.
