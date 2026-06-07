---
name: maxtac-apple-sptm-bypass
description: Analyze Apple Secure Page Table Monitor, Trusted Execution Monitor, PPL, KIP, APRR/FPR, and page-permission hardening for authorized MaxTAC Apple research. Use when a kernel primitive, page-table effect, trust-cache effect, memory-permission transition, or SPTM/TXM bypass hypothesis affects exploitability.
---

# MaxTAC Apple SPTM Bypass

Use this skill when a kernel or low-level Apple finding runs into page table, code-signing, memory-permission, or protected-metadata boundaries. Bias toward finding sanctioned transition bugs and data-only security impact before parking a candidate.

## Source Anchors

- Apple Platform Security, operating system integrity: `https://support.apple.com/guide/security/operating-system-integrity-sec8b776536b/web`
- Apple security updates index: `https://support.apple.com/en-us/100100`

## Apple-Specific Mitigations

- KIP protects kernel and driver code after kernel initialization.
- Fast Permission Restrictions/APRR can remove execute permissions efficiently and are especially relevant to JIT and writable/executable transitions.
- PPL protects user code pages and page tables on older supported iOS, iPadOS, visionOS, and watchOS platforms.
- SPTM and TXM protect user and kernel page tables even when an attacker has kernel write capabilities; on A15 or later and M2 or later SoCs, SPTM/TXM replace PPL on supported platforms.
- MIE/EMTE on newer SoCs can change memory-corruption behavior and should be recorded separately from SPTM.

## Common Bypass Directions

- Sanctioned transition bugs: stale ownership, confused mapping lifetime, permission-change races, missing validation before an SPTM/TXM handoff, or TXM policy confusion.
- Boundary mismatches: ordinary kernel data write versus protected page table state, trust cache state, code page metadata, IOMMU/DMA state, or device memory mapping.
- Data-only paths: security policy bits, entitlement-derived state, sandbox decisions, port rights, or vnode/MAC state that changes impact without page table control.
- Platform splits: compare A14/PPL behavior against A15+/SPTM only to isolate mechanism differences; do not generalize from simulator or Intel Mac behavior.

## CVE Precedents

Use these as memory-class and impact precedents, not as confirmed SPTM bypasses:

- CVE-2020-27932: kernel type confusion with kernel-privilege impact.
- CVE-2021-30807: IOMobileFrameBuffer memory corruption with active-exploitation reporting.
- CVE-2023-28206: IOSurfaceAccelerator out-of-bounds write with kernel-privilege impact.
- CVE-2023-32434: kernel integer overflow with reported active exploitation against older iOS versions.

## Workflow Example

Hypothetical page-permission race:

1. Record OS build, SoC, domain, kernelcache identity, and whether the platform is PPL or SPTM/TXM.
2. Classify the primitive with `scripts/sptm_boundary_matrix.py`.
3. Trace the vulnerable path to the transition boundary: who owns the mapping, who validates it, who commits it, and who can race it.
4. Try alternative impact paths before de-escalation: data-only policy state, mapping lifetime confusion, DMA/IOMMU mismatch, copyin/copyout edge, or target-flag proof.
5. Store the boundary matrix in the domain target directory and add a ledger milestone.

## Helper Script

```bash
python <skill-dir>/scripts/sptm_boundary_matrix.py --soc A15 --os-build 23E224 --memory-class page-table --primitive "stale mapping owner" --output data/maxtac/research/kernel/ioexample/sptm-matrix.md
```

## Handoff

Return:

```text
SPTM/PPL note:
Domain:
Platform generation:
Memory class:
Controlled primitive:
Protected boundary:
Alternative paths checked:
Evidence to collect next:
Ledger action:
```
