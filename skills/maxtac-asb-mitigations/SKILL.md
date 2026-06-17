---
name: maxtac-asb-mitigations
description: "Use this skill when Apple research shows unexpected runtime behavior that may be caused by Apple software or hardware mitigations, and the task is to reason about bypasses, constraints, or workaround paths."
---

# MaxTAC ASB Mitigations

Use this skill to decide whether an Apple mitigation is shaping exploit behavior, what evidence to preserve, and when to load the deeper reference. Do not use mitigation notes to dismiss a primitive automatically; record the blocked step, affected build, and remaining chain options.

## Mitigation Triage

Treat a mitigation as relevant when the primitive is reachable but the next exploitation step fails at a protected boundary: pointer authentication fault, tag-check crash, execute/write permission mismatch, JIT permission transition, protected page-table or code-signing state, protected kernel or coprocessor memory, or build/silicon-specific behavior.

Before reasoning about a bypass, record:

- Device product type, board/model when known, OS version, build number, and architecture.
- Whether the target is userspace, kernel, coprocessor firmware, browser/JIT, DriverKit, or platform policy code.
- Crash, panic, exception, or log text that names PAC, tag checks, code signing, page protection, protected mappings, or permission failures.
- Whether behavior differs across device class, SoC generation, OS build, boot args, SIP/security policy state, entitlements, sandbox profile, or arm64e versus non-arm64e code.
- The exact primitive already proven: controlled read, controlled write, pointer corruption, control-flow edge, allocator corruption, code signing bypass, or data-only state change.

## When A Mitigation May Be Active

| Mitigation | Signals worth checking | Read more |
| --- | --- | --- |
| KIP | Kernel or KEXT text/data in protected physical regions cannot be modified after boot, even with a write primitive. | `<skill-dir>/references/apple-platform-mitigations.md#kernel-integrity-protection-kip` |
| SCIP | Coprocessor firmware regions reject executable or writable mappings after boot lock, especially SEP, ISP, or motion coprocessor paths. | `<skill-dir>/references/apple-platform-mitigations.md#system-coprocessor-integrity-protection-scip` |
| APRR | JIT or runtime-generated code cannot be writable and executable in the expected thread context; JIT copy/unlock functions become important edges. | `<skill-dir>/references/apple-platform-mitigations.md#fast-permission-restrictions-aprr` |
| PAC | Corrupted code or data pointers fail authentication, arm64e disassembly shows PAC/AUT instructions, or a crash points to pointer auth failure. | `<skill-dir>/references/apple-platform-mitigations.md#pointer-authentication-codes-pac` |
| PPL | Kernel write does not let the chain patch user code pages, page tables, or code-signing protected pages on iOS-family platforms. | `<skill-dir>/references/apple-platform-mitigations.md#page-protection-layer-ppl` |
| SPTM/TXM | Page-table or code-execution policy changes fail on A15/M2-class or newer devices even after kernel compromise. | `<skill-dir>/references/apple-platform-mitigations.md#secure-page-table-monitor-sptm-and-trusted-execution-monitor-txm` |
| MTE/EMTE/TCE/MIE | Memory corruption becomes a synchronous tag-check crash, tag leakage is blocked, or allocator metadata corruption behaves differently on A19/M5-class or newer devices. | `<skill-dir>/references/apple-platform-mitigations.md#memory-integrity-enforcement-mie-mte-emte-and-tce` |

## When To Read The Reference

Read `<skill-dir>/references/apple-platform-mitigations.md` when:

- A proven primitive no longer yields the expected control, write, code execution, or persistence outcome.
- A chain requires a mitigation bypass, mitigation-aware data-only impact, or device/build-specific exploitability claim.
- The report needs to explain why the result is still exploitable despite PAC, PPL, SPTM/TXM, MIE, KIP, SCIP, or APRR.
- Cross-version or cross-device behavior suggests the mitigation surface changed.

Pair this skill with `maxtac-asb-ipsw` when the mitigation question depends on firmware, kernelcache, dyld shared cache, or build-specific symbols.
