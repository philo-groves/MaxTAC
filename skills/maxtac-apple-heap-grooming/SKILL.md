---
name: maxtac-apple-heap-grooming
description: Plan Apple heap grooming and allocator-state experiments for authorized MaxTAC research. Use when object placement, zone allocator behavior, kalloc_type, WebKit heaps, IOSurface allocations, UAF reliability, type confusion reliability, spray shape, or allocation/free scheduling affects exploitability.
---

# MaxTAC Apple Heap Grooming

Use this skill when a finding needs reproducible object placement, stale-object reuse, or allocation-shape evidence. Keep the output as an experiment plan and reliability matrix, not a payload.

## Source Anchors

- Apple Platform Security, OS integrity and memory hardening: `https://support.apple.com/guide/security/operating-system-integrity-sec8b776536b/web`
- Apple Security Bounty Target Flags: `https://security.apple.com/bounty/target-flags/`
- Apple security updates index: `https://support.apple.com/en-us/100100`

## Apple-Specific Mitigations

- XNU zones, kalloc_type, zone quarantine, pointer signing, MIE/EMTE, and panic diagnostics can change stale-object reuse.
- WebKit and JavaScriptCore have their own heap behaviors, JIT constraints, Gigacage-style isolation history, and process sandboxing.
- IOSurface, IOKit, XPC, Mach OOL memory, and shared memory can introduce allocator surfaces with different lifetime rules.
- PAC and ASLR can turn a reliable placement primitive into a data-only or signed-pointer-reuse question.

## Common Bypass Directions

- Build a placement experiment: allocate target object, free or stale it, fill with same-size/same-zone candidates, trigger use, and record crash/state.
- Vary count, size, timing, thread, process, entitlement, and reboot state.
- Prefer same-zone or same-type replacements before broad sprays.
- If grooming cannot place control data, redirect to leak gathering, lifetime extension, callback reuse, or Target Flag partial proof.

## CVE Precedents

- CVE-2021-30807: IOMobileFrameBuffer memory corruption, relevant for kernel object reliability work.
- CVE-2022-32894: kernel out-of-bounds write with reported active exploitation.
- CVE-2023-28206: IOSurfaceAccelerator out-of-bounds write, relevant to IOSurface-adjacent placement thinking.
- CVE-2023-32439: WebKit type confusion, relevant to browser heap shaping and object confusion.

## Workflow Example

Hypothetical IOKit UAF reliability pass:

1. Record object type, suspected zone or allocator, size class, entitlement state, and target domain path.
2. Generate an experiment plan with `scripts/heap_groom_plan.py`.
3. Run lab iterations with controlled counts and timing, capturing panics, logs, and negative controls.
4. Mark each run as no reuse, wrong object, controlled data, PAC failure, target flag partial, or stable impact.
5. Store the matrix in the domain target directory and update the ledger with the best-supported primitive.

## Helper Script

```bash
python <skill-dir>/scripts/heap_groom_plan.py --target IOExample --allocator kalloc_type --primitive UAF --sizes 0x80,0x100 --counts 16,64,256 --output data/maxtac/research/kernel/ioexample/heap-groom-plan.md
```

## Handoff

Return:

```text
Heap grooming note:
Domain:
Allocator or heap:
Object and size class:
Placement strategy:
Reliability evidence:
Negative controls:
Alternative reliability path:
Ledger action:
```
