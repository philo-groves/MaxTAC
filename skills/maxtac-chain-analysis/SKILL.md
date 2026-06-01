---
name: maxtac-chain-analysis
description: Analyze MaxTAC exploit chains across tracked systems findings. Use when kernel, driver, binary, crash, patch-diff, fuzzing, or open-source systems findings may compose into stronger impact through explicit preconditions and postconditions.
---

# MaxTAC Chain Analysis

Use this skill when multiple ledger entries might combine into greater impact. Chain analysis does not proof findings; it organizes how primitives compose and sends confident chains back through triage and proof.

## Chain Model

Represent each step as:

```text
Actor:
Preconditions:
Action or primitive:
Postconditions:
Evidence:
Blockers:
```

Only chain steps when one postcondition satisfies another step's precondition. Do not chain findings merely because they share a component or bug class.

## Useful Systems Chains

- info leak -> KASLR or object layout bypass -> memory corruption reliability
- sandbox escape primitive -> privileged helper or kernel entry reachability
- path confusion -> trusted file write -> dynamic loading or configuration control
- IOCTL confusion -> kernel memory disclosure -> controlled write validation
- parser crash -> root cause -> fuzz harness -> additional reachable variants
- patch-diff guard -> older code path -> proof target selection

## Workflow

1. Load active and de-escalated findings from `maxtac-finding-ledger`.
2. Summarize each candidate as actor, preconditions, primitive, postconditions, evidence, and blockers.
3. Compose only short chains with clear transitions.
4. Check whether the chain creates materially greater impact than individual findings.
5. Record a chain finding in the ledger with related IDs when justified.
6. Send a `triage-ready` chain through `maxtac-triage-debate` before proofing.

## Output

```text
Chain hypothesis:
Related findings:
Step cards:
Escalated impact:
Evidence:
Gaps:
Recommended ledger action:
```
