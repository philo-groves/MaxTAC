---
name: maxtac-finding-ledger
description: Maintain MaxTAC finding state for authorized systems vulnerability research. Use before adding, deduplicating, promoting, de-escalating, proofing, or reporting kernel, driver, binary, crash, fuzzing, patch-diff, or open-source systems findings.
---

# MaxTAC Finding Ledger

Use this skill as the single source of truth for findings. The parent agent owns ledger writes; Auditor, Debater, and Prover subagents return packets for the parent to merge.

Default path: `data/maxtac/findings.json`.

## States

Use exactly one state:

- `discovered`: plausible candidate from Auditor output.
- `triage-ready`: enough evidence exists for Debaters to evaluate.
- `confident`: triage accepted reachability, boundary crossing, and primitive quality.
- `proofed`: proof lab produced accepted evidence and a proof packet.
- `duplicate`: same root cause or security boundary as another finding.
- `de-escalated`: debunked, out of scope, unreachable, mitigated, or insufficient impact.

## Required Discipline

Before adding a finding:

1. Search by title, target, category, affected surface, entry point, and evidence keywords.
2. Update the existing finding if the root cause is the same.
3. Add a separate finding only when the root cause, boundary, primitive, affected target, or fix path materially differs.

Record milestones for meaningful events: Auditor discovery, duplicate decision, triage vote, blocker, reproduction, negative control, proof packet, patch check, or report.

## Helper Script

Use `scripts/ledger.py`:

```bash
python <skill-dir>/scripts/ledger.py init
python <skill-dir>/scripts/ledger.py summary
python <skill-dir>/scripts/ledger.py search --title "Unchecked IOCTL output length" --target "example.sys" --category memory-safety
python <skill-dir>/scripts/ledger.py add --title "Unchecked IOCTL output length" --target "example.sys" --category memory-safety --location "DeviceControl 0x222004" --summary "..." --evidence "..."
python <skill-dir>/scripts/ledger.py update M-0001 --state confident --note "Debaters accepted low-privileged IOCTL reachability and kernel write primitive."
python <skill-dir>/scripts/ledger.py milestone M-0001 --note "Negative control shows METHOD_BUFFERED path is safe."
```

## Promotion Rules

Promote to `triage-ready` only when a candidate has:

- affected target and entry point
- attacker-controlled input or trigger
- suspected missing guard
- impact hypothesis
- evidence references
- validation steps

Promote to `confident` only after triage accepts:

- realistic reachability from the scoped actor
- boundary crossing or security-property failure
- plausible exploitable primitive or meaningful security impact
- no decisive scope or mitigation blocker

Promote to `proofed` only after `maxtac-proof-lab` creates a proof packet with reproduction, expected/actual behavior, impact, negative controls, constraints, and cleanup.

## Output

Report ledger changes briefly:

```text
Finding ledger:
- Added M-0001 discovered: <title>
- Promoted M-0001 confident: <reason>
- De-escalated M-0002: <reason>
```
