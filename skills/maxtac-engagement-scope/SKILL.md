---
name: maxtac-engagement-scope
description: Establish authorized MaxTAC engagement scope for systems vulnerability research. Use before kernel, driver, binary, crash, fuzzing, patch-diff, or open-source systems work when target permission, artifact handling, lab execution, impact tolerance, or deliverable boundaries are unclear.
---

# MaxTAC Engagement Scope

Use this skill before any MaxTAC campaign step that could execute code, touch a live system, alter state, or depend on public program rules. Proceed when the target is supplied source, binaries, crash logs, symbols, configs, or a lab owned or authorized by the user.

## Scope Brief

Write a compact brief:

```text
Authorized context: <workspace, supplied artifacts, bounty/program, internal test, lab, or unknown>
Target assets: <repos, binaries, drivers, symbols, kernels, versions, crash inputs>
Target family: <xnu / windows-kernel-adjacent / binary / open-source-systems>
Allowed operations: <read-only, static reversing, build, fuzz, debug, VM execution, patch diff>
Out of scope: <live systems, persistence, destructive payloads, unavailable platforms, Linux kernel for v0>
Impact tolerance: <local-only, lab-only, controlled crash, low-rate live, no external effects>
Artifact handling: <where to store binaries, secrets policy, redistribution limits>
Deliverable: <auditor packets, findings, harness, crash root cause, proof packet, report>
Next skill: <maxtac-prepare or specific follow-up>
```

Ask only for missing facts that change safety or execution. If the workspace contains the target source or artifacts and the user asks for local/static review, proceed with local-only assumptions.

## Systems Defaults

- Prefer `~/maxtac-resources/` for large binaries, symbols, kernels, crash dumps, and corpora.
- Keep generated campaign state in the active workspace under `data/maxtac/`.
- Default unknown binaries to static analysis until lab execution is explicitly allowed.
- Default fuzzing and debugging to local VM/container/lab only.
- Treat public program scope as exact: use the official asset identifiers and rules, not broad company ownership.
- Treat closed-source Windows kernel internals as context, not an audit target, unless the user provides artifacts or an authorized lab target.

## Scope Recheck

Re-check scope before:

- Running unknown binaries or drivers.
- Loading kernel extensions, drivers, or privileged helpers.
- Fuzzing kernels, drivers, system services, or parsers for long runs.
- Touching live external systems or third-party accounts.
- Producing a PoC that changes state, persists, escalates privilege, or collects sensitive data.

If a requested step exceeds scope, record the blocker and propose a local, static, or lab-safe alternative.
