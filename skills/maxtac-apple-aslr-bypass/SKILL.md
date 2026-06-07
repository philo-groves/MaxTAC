---
name: maxtac-apple-aslr-bypass
description: Analyze Apple ASLR and KASLR bypass requirements for authorized MaxTAC research. Use when process image slides, dyld shared cache addresses, heap layout, stack layout, kernel slide, crash-log addresses, pointer leaks, or same-process disclosure affect exploitability.
---

# MaxTAC Apple ASLR Bypass

Use this skill when an Apple finding needs an address-class disclosure or when an apparent leak needs to be proven stable, reachable, and same-boundary. Do not stop at "needs leak"; name the exact address class and propose leak sources to inspect.

## Source Anchors

- Apple Platform Security, runtime process security: `https://support.apple.com/guide/security/security-of-runtime-process-sec15bfe098e/web`
- Apple secure coding guide, ASLR and memory errors: `https://developer.apple.com/library/archive/documentation/Security/Conceptual/SecureCodingGuide/Articles/BufferOverflows.html`
- Apple security updates index: `https://support.apple.com/en-us/100100`

## Apple-Specific Mitigations

- Built-in apps and third-party apps use ASLR; executable code, system libraries, and related structures are randomized at launch.
- Kernel slide, process image slide, dyld shared cache mapping, heap layout, stack layout, JIT regions, and shared memory mappings are separate address classes.
- Dyld shared cache UUID, OS build, architecture slice, Rosetta/native mode, simulator/device mode, and process identity matter.
- PAC, chained fixups, code signing, sandboxing, and library validation remain independent blockers after an address is known.

## Common Bypass Directions

- Same-boundary leaks: structured replies, Mach/XPC dictionaries, object descriptions, crash logs, uninitialized fields, kernel logs, IORegistry data, shared memory, IOSurface metadata, or allocation side effects.
- Stability testing: compare clean launches, same boot, reboot, same process family, device versus simulator, and arm64 versus arm64e.
- Narrowing: if code addresses are blocked, test heap or object-layout leaks; if kernel slide is blocked, test data-only impact that does not require KASLR.
- Split mixed evidence into "leak source", "address class", "same actor reachability", and "post-leak primitive".

## CVE Precedents

- CVE-2016-4655: kernel memory disclosure, a classic KASLR-unblocking precedent.
- CVE-2020-27950: kernel memory disclosure addressed as memory initialization.
- CVE-2022-32894: kernel out-of-bounds write precedent where address knowledge would shape reliability.
- CVE-2023-32434: kernel integer overflow precedent where current-platform exploitability depends on mitigation-specific primitives.

## Workflow Example

Hypothetical service reply leak:

1. Capture three clean-launch replies and three reboot-separated replies from the same authorized lab actor.
2. Run `scripts/aslr_leak_matrix.py` over logs, crash reports, and service replies.
3. Classify each candidate as image, dyld shared cache, heap, stack, kernel, JIT, or unknown.
4. Confirm whether the candidate is reachable by the scoped actor and useful for the next primitive.
5. Store the leak matrix under the domain target directory and update the ledger milestone.

## Helper Script

```bash
python <skill-dir>/scripts/aslr_leak_matrix.py logs/reply-*.txt --output data/maxtac/research/kernel/ioexample/aslr-leaks.md
```

## Handoff

Return:

```text
ASLR note:
Domain:
Address class needed:
Leak source:
Run-to-run behavior:
Build/cache identity:
Post-leak primitive:
Alternative leak paths:
Ledger action:
```
