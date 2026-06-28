# Apple Platform Mitigations Reference

This reference keeps mitigation background and bypass-oriented reasoning out of `SKILL.md`. Read only the section tied to the observed behavior.

## Contents

- [Kernel Integrity Protection (KIP)](#kernel-integrity-protection-kip)
- [Fast Permission Restrictions (APRR)](#fast-permission-restrictions-aprr)
- [System Coprocessor Integrity Protection (SCIP)](#system-coprocessor-integrity-protection-scip)
- [Pointer Authentication Codes (PAC)](#pointer-authentication-codes-pac)
- [Page Protection Layer (PPL)](#page-protection-layer-ppl)
- [Secure Page Table Monitor (SPTM) and Trusted Execution Monitor (TXM)](#secure-page-table-monitor-sptm-and-trusted-execution-monitor-txm)
- [Memory Integrity Enforcement (MIE), MTE, EMTE, and TCE](#memory-integrity-enforcement-mie-mte-emte-and-tce)
- [Reporting Mitigation Interactions](#reporting-mitigation-interactions)

## Kernel Integrity Protection (KIP)

After kernel initialization, Kernel Integrity Protection helps prevent modification of kernel and driver code. The memory controller provides a protected physical memory region that iBoot uses for the kernel and kernel extensions. After startup, the memory controller denies writes to that protected physical region, and the application processor MMU helps prevent privileged code mappings outside the protected region and writable mappings inside the kernel memory region.

KIP becomes difficult to route around because the hardware used to enable it is locked after boot. Treat it as relevant when a kernel primitive can write ordinary kernel data but cannot patch kernel or KEXT code, page tables, or protected mappings in the expected way.

There are no routine exploitation primitives for bypassing KIP on a fully updated system. Chain planning usually needs either a different impact that does not require patching protected code, an earlier boot-chain issue, or a separate policy/path flaw.

## Fast Permission Restrictions (APRR)

Fast Permission Restrictions, also called APRR registers, let supported Apple operating systems quickly restrict permissions per thread. They are especially relevant for JIT code because memory should not be effectively writable and executable at the same time.

Treat APRR as relevant when:

- JIT or runtime-generated code cannot be modified and then executed in the expected thread context.
- The chain depends on a JIT copy, JIT unlock, or runtime code-generation transition.
- The vulnerable path can corrupt pre-JIT buffers, but the final executable JIT region is permission-protected.

Common APRR-aware routes include redirecting execution to JIT copy or unlock functions, corrupting heap buffers before they are copied into JIT memory, using race or lifetime bugs around JIT machine-code transfer, and pairing with a PAC bypass when code integrity also depends on pointer authentication. Historical exploit chains such as CVE-2020-9870 and CVE-2020-9910 used APRR-relevant ideas, but current build behavior must be verified directly.

## System Coprocessor Integrity Protection (SCIP)

Coprocessor firmware handles critical tasks such as Secure Enclave, image sensor processor, and motion coprocessor work. System Coprocessor Integrity Protection protects coprocessor firmware in a way similar to KIP: iBoot loads each coprocessor firmware image into a protected memory region and configures the relevant coprocessor memory unit to prevent executable mappings outside its protected region and writable mappings inside it.

Treat SCIP as relevant when firmware analysis or dynamic behavior suggests that a coprocessor firmware image is protected after boot, especially when an apparent write primitive cannot alter executable firmware state.

There are no routine exploitation primitives for bypassing SCIP on a fully updated system. Chain planning usually needs a bug before protection is locked, a separate coprocessor-facing logic flaw, or an impact that avoids modifying protected firmware.

## Pointer Authentication Codes (PAC)

Pointer Authentication Codes protect against many code-pointer and data-pointer corruption paths. Apple platforms use pointer signatures to protect function returns, function pointers, block invocation data, Objective-C metadata, C++ vtables, computed gotos, thread state, and other security-sensitive pointers. The signature is stored in unused high bits of the pointer and is verified before use.

The exact key and salt depend on the pointer class. Common examples include:

| Item | Key | Salt |
| --- | --- | --- |
| Function return address | IB | Storage address |
| Function pointer | IA | 0 |
| Block invocation function | IA | Storage address |
| Block descriptor pointer | DA | Storage address + 0xC0BB |
| Objective-C method cache | IB | Storage address + class + selector |
| Objective-C isa pointer | DA | Storage address + 0x6AE1 |
| Objective-C super pointer | DA | Storage address + 0xB5AB |
| Selector-typed Objective-C ivars | DB | Storage address + 0x57C2 |
| Objective-C read-only class data pointer | DA | Storage address + 0x61F8 |
| C++ vtable entries | IA | Storage address + hash of mangled method name |
| C++ vtable pointers | DA | Storage address + hash of mangled base vtable name |
| Computed goto label | IA | Hash of function name |
| Kernel thread state | GA | Kernel-specific context |
| User thread state registers | IA | Storage address |

Treat PAC as relevant when a corrupted pointer reaches a use site but fails authentication, when crash logs mention pointer authentication, when disassembly shows PAC/AUT instructions around the target edge, or when a pointer disclosure seems necessary before a control-flow hijack can progress.

PAC-aware routes include:

- Reusing valid signed pointers in the same context.
- Finding signing gadgets or signing oracles that produce a valid pointer for the needed context.
- Corrupting data-only state instead of code pointers.
- Exploiting unprotected imports or code paths that sign attacker-controlled raw pointers.
- Pairing with memory disclosure to reuse signed pointers.

PAC bypass claims require careful proof. Record the signed pointer, authentication context, pointer use site, architecture, and whether the result is a stable primitive or a one-off crash.

## Page Protection Layer (PPL)

Page Protection Layer protects user code pages and page tables on iOS, iPadOS, visionOS, and watchOS after code signature verification. It builds on KIP and APRR by making protected page changes flow through PPL-controlled policy rather than ordinary kernel writes. macOS does not use PPL in the same way because it does not require all executed code to be signed.

Treat PPL as relevant when a kernel write primitive cannot patch user code pages, code-signing protected pages, or page-table state on iOS-family systems. A kernel write is still serious, but it may not be enough to execute unsigned code or alter protected mappings.

Historical PPL bypass patterns include hardware MMIO paths that alter page table entries, stale TLB or pmap invalidation issues, and chains that combine memory mapping bugs with lower-level hardware or kernel behavior. Verify the specific OS build and hardware before assuming any historical route still applies.

## Secure Page Table Monitor (SPTM) and Trusted Execution Monitor (TXM)

Secure Page Table Monitor and Trusted Execution Monitor protect page tables and code-execution policy for user and kernel processes. They are relevant on newer Apple silicon, including A15 or later and M2 or later systems, where SPTM/TXM replace PPL for many purposes. SPTM operates at a higher privilege level than the kernel, while TXM enforces lower-level policies.

Treat SPTM/TXM as relevant when a kernel primitive cannot change page tables or code-execution state on newer devices, or when behavior differs between PPL-era and SPTM/TXM-era hardware.

There are no routine exploitation primitives for bypassing SPTM/TXM on fully updated systems. Chain planning usually needs a data-only outcome, a policy-confusion path through legitimate monitor interfaces, or a separate bug at the SPTM/TXM boundary.

## Memory Integrity Enforcement (MIE), MTE, EMTE, and TCE

Memory Integrity Enforcement combines Apple secure allocators, Enhanced Memory Tagging Extension in synchronous mode, and Tag Confidentiality Enforcement. It is relevant on supported A19 and M5 class processors and later. The goal is to make memory corruption crash immediately or become much harder to transform into a useful primitive.

MTE is a memory tagging and tag-checking design: allocations carry tags, and accesses must present the correct tag. EMTE narrows practical bypass paths by using synchronous checks and by making untagged memory access from tagged regions harder. TCE protects allocator internals and tag confidentiality, including against some side-channel and speculative paths.

Treat MIE-related mitigations as relevant when:

- A memory corruption PoV becomes a synchronous tag-check crash.
- Out-of-bounds access works on one device class but fails on a newer tagged-memory device.
- Allocator metadata corruption or adjacent object corruption no longer gives the expected data-only primitive.
- The chain relies on tag leakage, tag reuse, or modifying untagged allocator backing state.

MIE-aware reasoning should focus on the exact allocation, tag-bearing pointer, crash mode, allocator path, and whether the bug can still produce a data-only effect before the tag check fires. Verify current research before making novelty claims about MIE bypasses.

## Reporting Mitigation Interactions

When mitigation behavior matters to an Apple Security Bounty report or internal proof packet, include:

- Device, SoC, OS version, build, architecture, and relevant firmware/kernelcache source.
- The primitive and the exact step blocked or constrained by the mitigation.
- Crash logs, panic logs, exception codes, register state, and symbolized frames.
- Whether the behavior is device-specific, build-specific, entitlement-specific, sandbox-specific, or arm64e-specific.
- Why the primitive remains security-relevant if code execution or patching is blocked.
- Any data-only impact, reachable policy transition, or chain composition that remains viable.
