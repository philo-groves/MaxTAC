---
name: maxtac-proof-lab
description: Proof MaxTAC confident systems vulnerabilities in clean authorized lab environments. Use after triage marks a kernel, driver, binary, crash, fuzzing, patch-diff, or open-source systems finding confident and a deterministic reproduction, negative controls, fix suggestion, or proof packet is needed.
---

# MaxTAC Proof Lab

Use this skill only for `confident` findings. Proofing should make the issue undeniable to a skeptical triager while staying within the authorized lab and impact tolerance.

## Lab Defaults

- Prefer VM, container, emulator, or disposable local lab execution.
- Keep unknown binaries static-only unless execution is explicitly allowed.
- Use minimal inputs, scoped accounts, local test data, and deterministic commands.
- Avoid persistence, stealth, production targets, destructive payloads, secret collection, and broad scanning.
- Redact tokens, keys, usernames, machine IDs, customer data, and crash dumps that contain sensitive memory.

## Proof Workflow

1. Load the finding from `data/maxtac/findings.json` and confirm state is `confident`.
2. Rebuild the claim from evidence: actor, entry point, controlled input, missing guard, boundary, primitive, and impact.
3. Reproduce in a clean lab or produce undeniable static evidence when runtime proof is not allowed.
4. Add negative controls: safe input, unauthorized actor failure, patched path, different IOCTL, owner/non-owner, entitlement absent/present, or harmless format variant.
5. Suggest the smallest robust fix and regression test.
6. Spawn or run a fresh Auditor check against reproduction and fix correctness when subagents are authorized.
7. Create a proof packet under `data/maxtac/proof/`.
8. Update the ledger to `proofed`, `triage-ready`, or `de-escalated`.

## Helper Script

Use `scripts/proof_packet.py` to create a consistent proof artifact:

```bash
python <skill-dir>/scripts/proof_packet.py --finding-id M-0001 --title "Unchecked IOCTL output length" --target "example.sys" --claim "..." --reproduction "..." --expected "..." --actual "..." --impact "..." --evidence "..." --negative-control "..." --constraints "..." --fix "..."
```

## Proof Standard

A proof packet must include:

- target identity: artifact path, version/build/commit, hashes when relevant
- exact vulnerability claim
- reproduction or static proof
- expected and actual behavior
- impact and limits
- negative controls
- preconditions and constraints
- cleanup
- fix suggestion and regression test idea

If proof fails, record why. Do not force a proofed state from a weak crash, ambiguous decompiler view, scanner output, or unvalidated exploitability claim.
