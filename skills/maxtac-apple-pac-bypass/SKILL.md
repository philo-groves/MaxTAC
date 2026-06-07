---
name: maxtac-apple-pac-bypass
description: Analyze Apple pointer authentication bypass hypotheses for authorized MaxTAC Apple research. Use when arm64e PAC, signed pointer reuse, pointer substitution, Objective-C metadata, C++ vtables, block pointers, return addresses, thread state, or PAC crash evidence affects exploitability.
---

# MaxTAC Apple PAC Bypass

Use this skill when arm64e pointer authentication is the blocker or when a crash suggests pointer authentication failure. Prefer signed-pointer reuse, substitution within a credible equivalence class, bugs before signing, and data-only impacts over speculative PAC forgery.

## Source Anchors

- Apple Platform Security, Pointer Authentication Codes: `https://support.apple.com/guide/security/operating-system-integrity-sec8b776536b/web`
- Apple security updates index: `https://support.apple.com/en-us/100100`

## Apple-Specific Mitigations

- PAC signs pointer bits with key and discriminator context; Apple documents different treatment for return addresses, function pointers, block pointers, Objective-C method caches, Objective-C isa/super pointers, C++ vtables, computed goto labels, and thread state.
- Some classes include storage address, class, selector, or mangled method/base names in the discriminator.
- User-space processes have their own B keys; kernel and user contexts differ.
- Authentication failure aborts before use; a "possible pointer authentication failure" crash is evidence to classify, not PC control by itself.
- BTI, ASLR, sandbox, code signing, and library validation may still block a path after a PAC-compatible pointer exists.

## Common Bypass Directions

- Reuse an already-signed pointer in the same process, same pointer class, same key class, and same discriminator assumptions.
- Move within equivalent storage only when the discriminator allows it; storage-address discriminators usually make blind relocation fail.
- Look before signing or after authentication: parser bugs that choose a legitimate callback, stale object reuse, data-only authorization fields, length/state fields, port rights, or policy decisions.
- For Objective-C and Swift, separate isa, method cache, block invocation, C++ vtable, witness table, and callback slots.
- When the primary control-flow route fails, test non-control-data impact before de-escalating.

## CVE Precedents

Use these as Apple memory-corruption precedents where PAC analysis may be needed on current arm64e devices:

- CVE-2019-8605: kernel use-after-free with kernel-privilege impact.
- CVE-2020-27932: kernel type confusion with active-exploitation reporting.
- CVE-2021-30807: IOMobileFrameBuffer memory corruption.
- CVE-2023-32434: kernel integer overflow with kernel-privilege impact.

## Workflow Example

Hypothetical callback-slot substitution:

1. Classify the pointer class and storage context with `scripts/pac_pointer_matrix.py`.
2. Identify where the target signs, stores, strips, authenticates, and uses the pointer.
3. Collect same-process signed-pointer candidates from equivalent callback slots.
4. Test substitution only in a lab and record authentication failure versus legitimate call versus ordinary UAF crash.
5. If substitution fails, redirect to pre-signing input control, post-auth data-only impact, or a JOP/gadget skill.

## Helper Script

```bash
python <skill-dir>/scripts/pac_pointer_matrix.py --pointer-class objc-cache --crash-log crash.txt --output data/maxtac/research/webkit/candidate/pac-matrix.md
```

## Handoff

Return:

```text
PAC note:
Domain:
Pointer class:
Signing/authentication sites:
Key/discriminator hypothesis:
Reuse/substitution condition:
Observed failure mode:
Alternative path:
Ledger action:
```
