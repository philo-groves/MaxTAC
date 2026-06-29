---
name: maxtac-asb-flag-proof
description: "Use this skill when an Apple Security Bounty chain needs a Commpage or TCC proof workflow and a verifiable proof packet for a target-flag claim."
---

# MaxTAC ASB Flag Proof

Use this skill to turn an Apple exploit chain into reviewable target-flag evidence. The goal is not to restate Apple's target flag page. The goal is to bind a claimed capability to the vulnerable target, capture the Commpage or TCC observations that prove it, and package the artifacts so another researcher can reproduce or falsify the claim.

Use this only after a real chain or strong exploitability primitive exists. For early primitive triage, use the relevant Source, Binary, Web, Android, or Apple mitigation workflow first.

## Proof Packet Helper

Use `python3 <skill-dir>/scripts/proof-packet.py` to create and lint a packet:

```bash
python3 <skill-dir>/scripts/proof-packet.py create \
  --output research/apple/<case-id>/asb-proof-packet.md \
  --case-id <case-id> \
  --flag-type commpage \
  --target "target process or service" \
  --build "macOS 15.2 24C101 arm64e"

python3 <skill-dir>/scripts/proof-packet.py lint research/apple/<case-id>/asb-proof-packet.md
```

Run `lint --strict` after filling the packet. The helper is intentionally small. It enforces packet shape and placeholder cleanup; it does not decide eligibility.

## Packet Shape

Every proof packet should contain:

- Target flag claim: Commpage register control, Commpage arbitrary read, Commpage arbitrary write, Commpage code execution, kernel variant, or TCC integrity flag modification.
- Target identity: process, service, bundle ID, binary path, code-signing identity, entitlements, sandbox profile, architecture, and whether the proof runs in userland, kernel, DriverKit, browser/JIT, or a brokered service.
- Environment: product, build, hardware model, SIP and security policy state when relevant, development mode or test entitlement caveats, and exact PoV invocation.
- Primitive chain: the vulnerability path that makes the flag observation attributable to the target, not to the harness.
- Positive proof: crash, panic, `tccutil flag check`, log, register state, memory observation, or controlled sink output.
- Negative control: patched build, disabled path, safe input, missing entitlement, reset TCC flag, non-vulnerable target, or same harness without the vulnerable chain.
- Artifact index: PoV source, PoV binary hash, crash or panic logs, unified logs, screenshots or terminal transcripts, commpage values, TCC before/after output, codesign output, entitlements, and packet hashes.

## Commpage Workflow

1. Identify the exact claim: register control, arbitrary read, arbitrary write, program-counter control, or kernel equivalent.
2. Capture the Commpage values and addresses used by the PoV on the target build. Record whether values came from the vulnerable process, a controlled helper, a crash log, or a debugger. Preserve architecture and address width.
3. Bind the observation to the vulnerable target. The packet must show that the target process, kernel path, broker, or service performed the controlled action because of the vulnerability.
4. Make the terminal state reviewable. Prefer crash logs or panic logs that expose register state, fault address, exception type, thread, image UUIDs, and process identity. For non-crash proofs, record the exact sink that consumed or emitted the target value.
5. Add a negative control that breaks the vulnerability path while keeping the harness and Commpage values comparable.

Useful packet questions:

- For register control, which general-purpose register carries the Commpage value, how many bits are controlled, and why is the register relevant at the sink?
- For arbitrary read, which controlled read dereferences the Commpage target address, and where is the value observed?
- For arbitrary write, which controlled write stores the Commpage target value at the Commpage target address, and how is the write verified?
- For code execution or PC control, what path transfers control to the Commpage target address, and what register or fault state proves it?
- For kernel claims, what shows the action occurred in the kernel path rather than a userland helper?

The existing files in `<skill-dir>/assets/` are examples only. Treat them as scaffolding for local PoVs, not as canonical proof requirements.

## TCC Workflow

For TCC target-flag claims, prove modification of the integrity flag through the vulnerable path:

1. Capture baseline output from `tccutil flag check`.
2. Run the PoV without manual database edits outside the vulnerable path.
3. Capture `tccutil flag check` after the PoV and note whether the user or system database changed.
4. Reset with `tccutil flag reset` and capture the reset output.
5. Include a negative control: no Full Disk Access where applicable, patched input, blocked broker path, reset database, or non-vulnerable target.

Use `assets/tcc-verbose-example.sh` and `assets/tcc-minimal-example.sh` only as examples for transcript shape. The report should explain the vulnerable path that changed the flag, not merely show that the flag can be changed from an authorized shell.

## Review Checklist

Before calling the packet ready:

- The proof names the exact target flag and the exact capability demonstrated.
- The observation is attributable to the vulnerable component.
- The packet includes build, hardware, architecture, and target identity.
- Positive and negative controls are both present.
- Crashes are accompanied by enough register, thread, image, and exception detail to show the claimed capability.
- PoV source, binaries, logs, transcripts, and screenshots are hashed or otherwise traceable.
- Any weakened local state is disclosed and not used as the basis for the claim.

## Hard Rules

- Do not claim a flag because a bug category usually leads to that flag.
- Do not claim a Commpage flag from a crash that does not expose the controlled value, target address, register state, or fault path needed by the claim.
- Do not claim TCC impact from manual SQLite edits or an already-authorized maintenance shell. The vulnerable path must cause the modification.
- Do not include secrets, personal data, unrelated TCC database contents, or device identifiers that are not needed for verification.
