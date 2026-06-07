---
name: maxtac-apple-target-flags
description: Prepare and evaluate Apple Security Bounty Target Flag evidence for authorized MaxTAC Apple research. Use when commpage Target Flags, TCC Target Flags, crash-log proof, register control, arbitrary read/write proof, PC-control proof, or bounty proof standards affect an Apple finding.
---

# MaxTAC Apple Target Flags

Use this skill when an Apple finding needs objective proof of attacker control. Keep the work local, authorized, and evidence-first. Target Flags are proof artifacts, not a substitute for the vulnerability path.

## Source Anchors

- Apple Security Bounty Target Flags: `https://security.apple.com/bounty/target-flags/`
- Apple Security Bounty Guidelines: `https://security.apple.com/bounty/guidelines/`
- Apple security updates index: `https://support.apple.com/en-us/100100`

## Apple-Specific Mitigations

- Commpage values are boot-selected. Do not reuse addresses or values from another boot, device, VM, crash, or copied report.
- User and kernel proofs use different target values and addresses.
- TCC Target Flags prove per-user or system TCC database modification through `tccutil flag check`; they do not automatically prove sandbox escape, FDA bypass, or privilege escalation.
- Crash logs must belong to the vulnerable process or victim context, not only a helper harness that read the commpage.
- Target Flag evidence must be paired with the separate bug path that caused the read, write, register control, PC control, or TCC modification.

## Common Bypass Directions

- If the primary proof crashes in the harness, redirect toward the victim process and collect the precise process, thread, register, PC, FAR, and exception fields.
- If a primitive is partial, preserve the narrower result and look for adjacent controlled fields, repeatability, or a second primitive rather than closing the finding.
- If TCC evidence is ambiguous, split the claim into user DB, system DB, responsible process, attribution, prompt state, and sandbox state.
- If a Target Flag category does not apply, write a detailed exploitability note and route to the mechanism skill that owns the missing primitive.

## CVE Precedents

Use these as precedent seeds, not proof that current Target Flags existed for the original reports:

- CVE-2016-4655: kernel memory disclosure, useful precedent for separating an information leak from a later kernel primitive.
- CVE-2016-4656: kernel memory corruption with kernel-privilege impact.
- CVE-2021-30807: IOMobileFrameBuffer memory corruption with reported active exploitation.
- CVE-2023-28206: IOSurfaceAccelerator out-of-bounds write with kernel-privilege impact.

## Workflow Example

Hypothetical kernel UAF proof:

1. Record OS build, SoC, device class, boot time, vulnerable process, domain, and target directory path.
2. Classify the strongest controlled primitive: register control, read/write, PC control, or TCC modification.
3. Generate a Target Flag note with `scripts/target_flag_note.py`.
4. Re-run the PoC in the lab and capture the crash log for the vulnerable process.
5. Confirm user versus kernel target selection, register/PC/FAR evidence, and the vulnerable path that caused access to the flag.
6. Add a ledger milestone with the note path, keeping detailed crash interpretation in `data/maxtac/research/<domain>/<target>/`.

## Helper Script

```bash
python <skill-dir>/scripts/target_flag_note.py --domain kernel --target IOExample --primitive pc-control --tier kernel --output data/maxtac/research/kernel/ioexample/target-flag-note.md
```

## Handoff

Return:

```text
Target Flag note:
Domain:
Primitive claimed:
Tier: user / kernel / TCC
Crash-log evidence:
Bug path linking vulnerability to flag:
Alternative proof path if blocked:
Ledger action:
```
