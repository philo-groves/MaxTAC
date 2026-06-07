---
name: maxtac-triage-debate
description: Run MaxTAC Debater evaluation for candidate systems vulnerabilities. Use when a kernel, driver, binary, crash, fuzzing, patch-diff, or open-source systems finding is triage-ready and needs independent judgment on reachability, exploitability, primitive quality, scope, alternative paths, or de-escalation.
---

# MaxTAC Triage Debate

Use this skill after `maxtac-finding-ledger` marks a finding `triage-ready`. The goal is not consensus theater; it is to find blockers before proof work gets expensive.

## Debate Questions

Each Debater must answer:

- Reachability: Can the scoped attacker realistically reach the entry point?
- Control: What bytes, pointers, object IDs, paths, messages, sizes, states, or timing does the attacker control?
- Boundary crossing: Which user/kernel, sandbox, entitlement, privilege, object, process, file, parser, or trust boundary fails?
- Primitive quality: Is this a crash, info leak, UAF, type confusion, controlled write, confused deputy, permission bypass, path escape, or other useful primitive?
- Mitigations: Which checks, locks, refcounts, ACLs, entitlements, probes, code-signing, or hardening may block it?
- Scope: Does validation fit the authorized lab and impact tolerance?
- Proof gap: What exact evidence is still needed?
- Alternative paths: If the primary path blocks, what adjacent primitive, target surface, domain note, or proof route should be tried before de-escalation?

## Subagent Pattern

If subagents are authorized and available, spawn three Debaters with the same finding packet and no extra narrative. A cost-conscious model is acceptable for Debaters when the user has not requested maximum depth.

Ask for this output:

```text
Verdict: valid | invalid | needs-more-work
Hard blockers: <none or list>
Reachability: <accepted/rejected/unknown with reason>
Boundary crossing: <accepted/rejected/unknown with reason>
Primitive quality: <accepted/rejected/unknown with reason>
Missing evidence: <specific tests, traces, lines, symbols, crashes>
Alternative paths: <specific next routes or none with reason>
Recommended ledger state: <confident / de-escalated / triage-ready>
```

## Decision Rule

Promote to `confident` when a majority says `valid` and no Debater identifies a decisive hard blocker.

Keep as `triage-ready` when the issue is plausible but the missing evidence is specific and obtainable.

Before de-escalating, require the debate packet to name alternative paths that were checked or explain why none are plausible within scope. De-escalate only when:

- entry point is not reachable by the scoped actor
- the guard exists and applies before the dangerous operation
- the target or technique is out of scope
- the crash is expected, local-only without security impact, or caused by the harness
- the primitive and its alternative paths depend on unrealistic memory layout, unavailable privileges, prohibited impact, or evidence contradicted by the artifacts

Update the ledger with the debate result and store debate notes under `data/maxtac/debates/` when useful.
