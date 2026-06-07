---
name: maxtac-apple-stack-pivoting
description: Analyze Apple stack or context pivot feasibility for authorized MaxTAC research. Use when SP/FP/LR/PC control, fake stack viability, context switching, thread state, PAC-authenticated returns, BTI, crash registers, or pivot evidence affects a JOP or gadget-chain hypothesis.
---

# MaxTAC Apple Stack Pivoting

Use this skill when control exists but state does not. Treat stack pivoting as one way to steer a JOP or call-oriented proof, not as the default path. On modern iOS, PAC often makes return-address routes brittle, so prioritize context pivots, signed callback state, and data-only alternatives.

## Source Anchors

- Apple Platform Security, PAC and OS integrity: `https://support.apple.com/guide/security/operating-system-integrity-sec8b776536b/web`
- Apple Security Bounty Target Flags: `https://security.apple.com/bounty/target-flags/`
- Apple security updates index: `https://support.apple.com/en-us/100100`

## Apple-Specific Mitigations

- PAC protects return addresses and selected thread state; a controlled LR is not enough if authentication fails before use.
- BTI constrains branch landing sites for indirect branches.
- ASLR/KASLR and stack randomization affect fake-stack placement and crash interpretation.
- Guard pages, hardened allocators, stack canaries, non-executable memory, and MIE/EMTE can alter pivot behavior.
- Kernel and user pivots have different Target Flag proof tiers and different cleanup expectations.

## Common Bypass Directions

- Look for context pivots through callback objects, block storage, async completion state, saved register areas, exception/thread state, or message dispatch state.
- If SP control is partial, preserve it and test whether FP, LR, x19-x28, or object-pointer control can supply state.
- If return authentication blocks, route to JOP/call-oriented dispatch or signed callback reuse.
- If no pivot survives, redirect to heap grooming to place controlled objects near legitimate state.

## CVE Precedents

- CVE-2016-4657: WebKit memory corruption, useful as a historical pivot and browser-chain precedent.
- CVE-2020-27930: FontParser memory corruption with code-execution impact.
- CVE-2023-32439: WebKit type confusion with reported active exploitation.
- CVE-2023-41064: ImageIO buffer overflow with reported active exploitation.

## Workflow Example

Hypothetical crash with partial SP influence:

1. Save the crash log, target binary identity, OS build, and domain target path.
2. Run `scripts/stack_pivot_evidence.py` with any controlled marker values.
3. Classify SP, FP, LR, PC, and callee-saved registers as controlled, partially controlled, derived, or unknown.
4. Check PAC failure mode separately from normal bad access.
5. If pivot evidence is weak, route to heap grooming, PAC reuse, JOP, or Target Flag proof rather than de-escalating.

## Helper Script

```bash
python <skill-dir>/scripts/stack_pivot_evidence.py crash.txt --controlled-value 0x4141414141414141 --output data/maxtac/research/webkit/candidate/pivot-evidence.md
```

## Handoff

Return:

```text
Stack/context pivot note:
Domain:
Register control:
Stack or state storage:
PAC/BTI interaction:
Fake-state placement:
Alternative state-control path:
Next skill:
Ledger action:
```
