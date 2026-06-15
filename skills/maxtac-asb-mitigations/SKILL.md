---
name: maxtac-asb-mitigations
description: Use this skill when Apple research results in unexpected runtime behavior, possibly due to attacker mitigations in Apple software architectures. Encountering a mitigation is not a direct blocker; there may be a bypass or workaround available.
---

## Kernel Integrity Protection (KIP)
After the operating system kernel completes initialization, Kernel Integrity Protection (KIP) is enabled to help prevent modifications of kernel and driver code. The memory controller provides a protected physical memory region that iBoot uses to load the kernel and kernel extensions. After startup is complete, the memory controller denies writes to the protected physical memory region. The Application Processor’s Memory Management Unit (MMU) is configured to help prevent mapping privileged code from physical memory outside the protected memory region and to help prevent writeable mappings of physical memory within the kernel memory region.

To prevent reconfiguration, the hardware used to enable KIP is locked after the boot process is complete.

### Bypassing KIP
There are no known exploitation primitives or bypass techniques for KIP on a fully up-to-date system.

## Fast Permission Restrictions (APRR)
Starting with the Apple A11 Bionic and S3 SoCs, a new hardware primitive was introduced. This primitive, Fast Permission Restrictions, includes a CPU register that quickly restricts permissions per thread. With Fast Permission Restrictions (also known as APRR registers), supported operating systems can remove execute permissions from memory without the overhead of a system call and a page table walk or flush. These registers provide one more level of mitigation for attacks from the web, particularly for code compiled at runtime (just-in-time compiled)—because memory can’t be effectively executed at the same time it’s being read from and written to.

### Bypassing APRR
- **Control Flow Hijacking**: Redirecting execution to JIT unlocking functions (like `performJITMemcpy`) or using ROP/JOP chains to temporarily modify APRR register indices, allowing writes to the JIT region. 
- **Memory Corruption**: Corrupting heap buffers containing JIT machine code before they are copied into the JIT region, often exploiting race conditions or use-after-free vulnerabilities. 
- **PAC Bypasses**: Since Pointer Authentication Codes (PAC) protect JIT code integrity, attackers often require a separate PAC bypass (such as forging signatures or exploiting PAC key leakage) to execute arbitrary code in the JIT region after APRR restrictions are lifted. 
- **Signal Handling Exploits**: Crashing threads during JIT code copying to gain control over register context, which can be used to bypass both APRR and PAC checks by manipulating the execution state.

These vulnerabilities were notably exploited in CVE-2020-9870 and CVE-2020-9910.

## System Coprocessor Integrity Protection (SCIP)
Coprocessor firmware handles many critical system tasks — for example, the Secure Enclave, the image sensor processor, and the motion coprocessor. Therefore its security is a key part of the security of the overall system. To prevent modification of coprocessor firmware, Apple uses a mechanism called *System Coprocessor Integrity Protection (SCIP)*.

SCIP works much like KIP: At boot time, iBoot loads each coprocessor’s firmware into a protected memory region, one that’s reserved and separate from the KIP region. iBoot configures each coprocessor’s memory unit to help prevent:

- Executable mappings outside its part of the protected memory region
- Writeable mappings inside its part of the protected memory region

Also at boot time, to configure SCIP for the Secure Enclave, the Secure Enclave operating system is used. After the boot process is complete, the hardware used to enable SCIP is locked. This is designed to prevent reconfiguration.

### Bypassing SCIP
There are no known exploitation primitives or bypass techniques for SCIP on a fully up-to-date system.

## Pointer Authentication Codes (PAC)
Pointer Authentication Codes (PACs) are used to protect against exploitation of memory corruption bugs. System software and built-in apps use PAC to help prevent modification of function pointers and return addresses (code pointers). PAC uses five secret 128-bit values to sign kernel instructions and data, and each user space process has its own B keys. Items are salted and signed as indicated below.

| Item | Key | Salt |
| --- | --- | --- |
| Function Return Address | IB | Storage address |
| Function Pointer | IA | 0 |
| Block Invocation Function | IA | Storage address |
| Block Descriptor Pointer | DA | Storage address + 0xC0BB |
| Objective-C Method Cache | IB | Storage address + Class + Selector |
| Objective-C Isa Pointer | DA | Storage address + 0x6AE1 |
| Objective-C Super Pointer | DA | Storage address + 0xB5AB |
| Selector Typed Objective-C ivars | DB | Storage address + 0x57C2 |
| Objective-C Read-only Class Data Pointer | DA | Storage address + 0x61F8 |
| C++ V-Table Entries | IA | Storage address + Hash (mangled method name) |
| C++ V-Table Pointers | DA | Storage address + Hash (mangled base V-Table name) |
| Computed Goto Label | IA | Hash (function name) |
| Kernel Thread State | GA | • |
| User Thread State Registers | IA | Storage address |

The signature value is stored in the unused padding bits at the top of the 64-bit pointer. The signature is verified before use, and the padding is restored to help ensure a functioning pointer address. Failure to verify results in an abort. This verification increases the difficulty of many attacks, such as a return-oriented programming (ROP) attack, which attempts to trick the device into executing existing code maliciously by manipulating function return addresses stored on the stack.

### Bypassing PAC
PAC is one of the most often confronted mitigations in Apple research, and there are a variety of techniques that have been used to bypass it.

Implementation Flaws:
- **Unprotected Imports**: Attackers exploit code that loads function pointers from writable memory and signs them using instructions like PACIZA without prior validation. This allows attackers with arbitrary read/write primitives to overwrite the raw pointer, causing the system to sign and execute malicious addresses.
- **Signing Gadgets**: Vulnerabilities that allow coercion of the system to execute specific instruction sequences (signing oracles) enable attackers to forge valid PAC signatures for arbitrary pointers.

Hardware and Side-Channel Attacks:
- **PACMAN Attack**: Discovered on Apple M1 chips, this hardware vulnerability uses speculative execution to measure timing variations during pointer authentication. This allows attackers to leak the PAC key from the processor, effectively bypassing protection entirely.
- **Timing Side-Channels**: Advanced assessments have demonstrated that timing variations in signature verification operations can be exploited to deduce keys or bypass authentication.

Exploitation Primitives:
- **Memory Disclosure**: Leaking valid PAC-protected pointers along with their context values allows attackers to reuse or "counterfeit" pointers.
- **JIT Exploitation**: Compromising Just-In-Time (JIT) compilers can allow attackers to inject malicious instructions into writable JIT regions, bypassing control flow integrity checks.

These bypasses often require an existing vulnerability (such as arbitrary read/write) to serve as a foothold for the PAC attack.

## Page Protection Layer (PPL)
Page Protection Layer (PPL) in iOS, iPadOS, visionOS, and watchOS is designed to prevent user space code from being modified after code signature verification is complete. Building on KIP and Fast Permission Restrictions, PPL manages the page table permission overrides to make sure only the PPL can alter protected pages containing user code and page tables. The system provides a massive reduction in attack surface by supporting systemwide code integrity enforcement, even in the face of a compromised kernel. This protection isn’t offered in macOS because PPL is only applicable on systems where all executed code must be signed.

### Bypassing PPL
- **Operation Triangulation (CVE-2023-38606)**: This sophisticated exploit, discovered by Kaspersky, bypassed PPL using hardware memory-mapped I/O (MMIO) registers (specifically GPU L2 cache debug registers) to patch page table entries directly. It also leveraged CVE-2023-32434, an integer overflow in XNU’s memory mapping syscalls, to gain read/write access to physical memory.
- **Project Zero Bypass (iOS 13.6)**: A 2020 bypass exploited improper Translation Lookaside Buffer (TLB) invalidation in the `pmap_remove_options_internal()` function.  Attackers used a stale TLB entry to map PPL-protected pages as writable before the page table entries were fully removed.
- **Fugu15 Jailbreak**: This jailbreak for iOS 15 required a PPL bypass alongside Pointer Authentication Code (PAC) bypasses to execute unsigned code, demonstrating the increasing difficulty of bypassing Apple’s kernel protections.

## Secure Page Table Monitor (SPTM) and Trusted Execution Monitor (TEM)
Secure Page Table Monitor (SPTM) and Trusted Execution Monitor (TXM) in iOS, iPadOS, macOS, and visionOS are designed to work together to help protect page tables for both user and kernel processes against modification. This includes when attackers have kernel write capabilities and can bypass control flow protections. SPTM does this by utilizing a higher privilege level than the kernel, and utilizing the lower privileged TXM to actually enforce the policies that govern code execution. This system is designed so that a TXM compromise doesn’t automatically translate to an SPTM bypass due to this privilege separation and the governing of trust between them. In the A15 or later and M2 or later SOCs, SPTM (in combination with TXM) replaces the PPL, providing a smaller attack surface that doesn’t rely on trust of the kernel, even during early boot. SPTM relies on new silicon primitives that are an evolution of the Fast Permission Restrictions that PPL utilizes, and are available only on the processors listed in the table above.

### Bypassing SPTM and TXM
There are no known exploitation primitives or bypass techniques for SPTM and TXM on a fully up-to-date system.

## Memory Integrity Enforcement (MIE)
Memory Integrity Enforcement (MIE), is a comprehensive memory safety defense for Apple platforms available on A19 and M5 processors or later. MIE is built on the robust foundation provided by Apple’s secure memory allocators, coupled with Enhanced Memory Tagging Extension (EMTE) in synchronous mode, and supported by extensive Tag Confidentiality Enforcement policies. MIE is built in to Apple silicon and offers unparalleled, always-on memory safety protection for key attack surfaces including the kernel, while maintaining the power and performance that users expect. For more information, see [Memory Integrity Enforcement: A complete vision for memory safety in Apple devices](https://security.apple.com/blog/memory-integrity-enforcement/) on Apple Security Research blog.

### Memory Tagging Extension (MTE)
Arm published the Memory Tagging Extension (MTE) specification in 2019 as a tool for hardware to help find memory corruption bugs. MTE is a memory tagging and tag-checking system, where every memory allocation is tagged with a secret. The hardware guarantees that later requests to access memory are granted only if the request contains the correct secret. If the secrets don’t match, the app crashes, and the event is logged. This allows developers to identify memory corruption bugs immediately as they occur.

### Enhanced Memory Tagging Extension (EMTE)
EMTE closes the holes that prevent MTE from being an active defense, including only supporting the more secure synchronous mode. In addition, accessing nontagged memory from a tagged memory region requires knowing that region’s tag, making it significantly harder for attackers to turn out-of-bounds bugs in dynamic tagged memory into a way to sidestep EMTE by directly modifying nontagged allocations.

### Tag Confidentiality Enforcement (TCE)
Tag Confidentiality Enforcement protects the implementation of the secure allocators from technical threats and guards the confidentiality of EMTE tags—including against side-channel and speculative-execution attacks. The Secure Page Table Monitor protects the kernel allocator backing store and tag storage. The system also ensures that when the kernel accesses memory on behalf of an application, it’s subject to the same tag-checking rules as userspace. Tag Confidentiality Enforcement also is designed to mitigate against tag leakage due to timing or speculative attacks, and even includes a protection against Spectre V1.

### Bypassing MIE
There is only one known MIE bypass in history, developed in May 2026. The bypass leveraged two critical data-only vulnerabilities in the kernel memory allocator, specifically targeting the `_zalloc_ro_mut` function.  Key techniques included:

- **Integer Overflow**: Exploiting an unchecked addition in a bounds check that allowed writes to bypass validation when the length parameter caused a wrap-around.
- **Timing Manipulation**: Using race conditions between memory allocation and tag validation to create mismatches in MIE’s memory tags.
- **Privilege Escalation**: The chain achieved local root access by corrupting kernel credential structures without injecting malicious code.