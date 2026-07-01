---
name: maxtac-source-patch-history-loop
description: "Use this skill when MaxTAC Source needs a loop over source commit history, public CVEs or advisories, vendor releases, and quiet hardening diffs to enrich a code subsystem threat model, identify bug precedent, prioritize risky files or functions, or seed targeted audits."
---

# MaxTAC Source Patch History Loop

Use this loop to turn code history and public vulnerability history into targeted security context. The loop is evidence-gathering and prioritization; a commit diff or CVE correlation is not a finding until reachability, actor control, and impact are validated through normal MaxTAC flow.

## Setup

1. Bound the target: repository path, subsystem paths, relevant versions/tags/branches, and date range.
2. Run Core corpus orientation for the subsystem and note prior negative results or open questions.
3. Create Core loop state:

```text
python3 <core-workflow-skill-dir>/scripts/loop.py init \
  --root <workspace-root> \
  --loop-id <id> \
  --kind source-patch-history \
  --owner-plugin maxtac-source \
  --target "<repo or subsystem>" \
  --scope "<tags, commits, paths, and advisory range>" \
  --summary "Correlate source patch history with CVE/advisory precedent and quiet hardening." \
  --positive-gate "Patch or advisory item is correlated to files/functions, bug class, security invariant, and next audit action or documented non-security rationale." \
  --negative-gate "Patch/advisory item lacks provenance, comparable diff, affected path mapping, or reachability/security-boundary interpretation." \
  --output "research/artifacts/source-patch-history/<id>/" \
  --output "research/notes/ closure or threat-model notes" \
  --output "models/<model-id>/ invariant or unknown updates"
```

4. Add loop items for CVEs, advisories, release notes, suspicious commits, and quiet hardening diffs. Prefer stable item IDs like `cve-2026-0001`, `commit-<shortsha>`, or `tag-diff-<old>-<new>`.

## Iterate

For each item:

1. Preserve provenance: advisory URL or local export, commit SHA, tags, release, author date, touched paths, and diff command.
2. Diff narrowly with `git show`, `git diff`, or `git log -p -- <paths>`. Store raw command output under `research/artifacts/source-patch-history/<id>/`.
3. Map changed code to functions, fields, entrypoints, guards, sinks, and tests.
4. Classify bug precedent: memory safety, parser, authz, sandbox, command execution, TOCTOU, injection, disclosure, denial of service, supply-chain, or hardening only.
5. Update Core model when the diff reveals a security invariant, proof obligation, assumption, unknown, contradiction, or refutation condition.
6. Route promising items into `maxtac-sast-surface-triage`, `maxtac-source-scan`, CFG, OpenGrep, or targeted auditors.
7. Update the loop item with evidence and status.

## Gates

Positive closure for an item requires:

- public source or local provenance;
- exact commits/tags or a documented reason exact mapping is impossible;
- affected files/functions and bug-class interpretation;
- threat-model consequence, such as "seed invariant", "audit sink", "historical false positive", or "non-security cleanup";
- corpus/model/ledger/contract references when durable knowledge changed.

Negative closure requires a blocker such as:

- advisory lacks enough detail to map to source;
- comparable tags are unavailable;
- patch touches generated/vendor code outside scope;
- diff is non-security after evidence review;
- reachable impact requires Binary, Apple, Android, Web, Cloud, or Supply Chain follow-up.

## Output

Write durable conclusions as compact corpus notes tagged by subsystem, bug class, CVE/advisory, and knowledge kind. Keep raw diffs and advisory exports as artifacts. Use findings ledger only when a new primitive or chain hypothesis survives source review beyond historical precedent.

## Hard Rules

- Do not treat CVE similarity as proof of current vulnerability.
- Do not overfit to public CVEs; quiet hardening commits can be better leads.
- Do not close a suspicious security diff until it has a code owner path, invariant implication, or explicit non-security rationale.
- Do not let this loop replace Source Scan coverage when a target path needs auditable review receipts.
