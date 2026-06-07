---
name: maxtac-apple-jop-chaining
description: Analyze Apple jump-oriented programming and call-oriented chain feasibility for authorized MaxTAC research. Use when JOP dispatch, indirect branches, call targets, BTI, PAC-compatible pointers, dyld shared cache gadgets, kernel code reuse, or non-return control-flow chaining affects exploitability.
---

# MaxTAC Apple JOP Chaining

Use this skill when a bug has or may obtain PC control but return-address chaining is not a credible modern iOS path. Model JOP and call-oriented chaining as a requirements table and keep the output non-weaponized: evidence, blockers, alternative primitives, and lab checks.

## Source Anchors

- Apple Platform Security, PAC and OS integrity: `https://support.apple.com/guide/security/operating-system-integrity-sec8b776536b/web`
- Apple Security Bounty Target Flags: `https://security.apple.com/bounty/target-flags/`
- Apple security updates index: `https://support.apple.com/en-us/100100`

## Apple-Specific Mitigations

- PAC raises the cost of return-address and indirect-pointer substitution; JOP still needs PAC-compatible branch targets or legitimate signed callbacks.
- BTI and branch landing constraints can reject otherwise useful indirect-branch targets.
- ASLR/KASLR, dyld shared cache UUID, kernelcache identity, architecture slice, and arm64e status must match the lab artifact.
- Code signing, sandboxing, SPTM/PPL, and executable-memory policy can make code reuse more plausible than injected code.
- Target Flag PC control proves a primitive, not a complete chain.

## Common Bypass Directions

- Use legitimate dispatchers, callback tables, block invokes, Objective-C message send, C++ virtual calls, Swift witness-table calls, or kernel function-pointer paths.
- Prefer signed callback reuse and call-oriented side effects over arbitrary branch forgery.
- Keep dispatcher, state register, memory read/write, cleanup, and side-effect constraints separate.
- If PC control is present but no dispatcher exists, redirect to stack pivoting, heap grooming, ASLR leak, or PAC reuse rather than closing the finding.

## CVE Precedents

These are memory-corruption precedents where JOP/call-oriented analysis may be relevant on hardened Apple platforms:

- CVE-2020-27930: FontParser memory corruption with arbitrary-code-execution impact.
- CVE-2023-41064: ImageIO buffer overflow with reported active exploitation.
- CVE-2023-32439: WebKit type confusion with reported active exploitation.
- CVE-2023-28206: IOSurfaceAccelerator kernel memory corruption, useful for kernel-side post-primitive modeling.

## Workflow Example

Hypothetical WebKit type confusion:

1. Record exact OS build, dyld shared cache UUID, process, architecture slice, and arm64e status.
2. Build a requirements table with `scripts/jop_chain_table.py`.
3. Inventory candidate dispatch surfaces without constructing a chain: message send, callbacks, block invokes, vtables, or indirect branches.
4. Fill each row with evidence, missing evidence, mitigation interaction, and next lab check.
5. If one row blocks, route to the mechanism skill that can supply it instead of de-escalating the whole candidate.

## Helper Script

```bash
python <skill-dir>/scripts/jop_chain_table.py --target WebKitCandidate --pc-control partial --dispatcher missing --pac "signed callback needed" --output data/maxtac/research/webkit/candidate/jop-table.md
```

## Handoff

Return:

```text
JOP note:
Domain:
Control-flow primitive:
Dispatcher or call surface:
PAC/BTI interaction:
ASLR dependency:
State and cleanup constraints:
Alternative primitive needed:
Ledger action:
```
