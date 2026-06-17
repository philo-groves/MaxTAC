# Windows Platform Mitigations Reference

This reference keeps mitigation background and bypass-oriented reasoning out of `SKILL.md`. Read only the section tied to the observed behavior.

## Contents

- [Virtualization-Based Security (VBS) and Virtual Secure Mode (VSM)](#virtualization-based-security-vbs-and-virtual-secure-mode-vsm)
- [Hypervisor-Protected Code Integrity (HVCI) / Memory Integrity](#hypervisor-protected-code-integrity-hvci--memory-integrity)
- [Kernel Data Protection (KDP)](#kernel-data-protection-kdp)
- [Kernel-Mode Hardware-Enforced Stack Protection (KCET)](#kernel-mode-hardware-enforced-stack-protection-kcet)
- [Control Flow Guard (CFG), Kernel CFG, and eXtended Flow Guard (XFG)](#control-flow-guard-cfg-kernel-cfg-and-extended-flow-guard-xfg)
- [User-Mode Exploit Protection](#user-mode-exploit-protection)
- [Protected Process Light (PPL), LSA Protection, and Credential Guard](#protected-process-light-ppl-lsa-protection-and-credential-guard)
- [AppContainer, Less Privileged AppContainer (LPAC), and Integrity Levels](#appcontainer-less-privileged-appcontainer-lpac-and-integrity-levels)
- [Windows App Control, Smart App Control, and Vulnerable Driver Blocklists](#windows-app-control-smart-app-control-and-vulnerable-driver-blocklists)
- [Administrator Protection](#administrator-protection)
- [Kernel DMA Protection](#kernel-dma-protection)
- [Kernel Memory, Pool, and Address-Space Mitigations](#kernel-memory-pool-and-address-space-mitigations)
- [Secure Boot, TPM, Measured Boot, and BitLocker](#secure-boot-tpm-measured-boot-and-bitlocker)
- [Reporting Mitigation Interactions](#reporting-mitigation-interactions)

## Virtualization-Based Security (VBS) and Virtual Secure Mode (VSM)

Virtualization-Based Security uses the Windows hypervisor to isolate security-sensitive code and data from the normal NT kernel. The normal kernel and most drivers run in VTL0. The secure kernel and VBS-backed trustlets run in VTL1. Windows builds multiple mitigations on this split, including HVCI, Credential Guard, Kernel Data Protection, kernel shadow stacks, and some secure policy enforcement.

For vulnerability research, separate "kernel compromise" from "VTL1 compromise." A bug that gives arbitrary read/write in VTL0 is still serious, but VBS can prevent the classic next step of loading unsigned kernel code, patching protected policy data, or directly extracting isolated credentials.

Treat VBS/VSM as relevant when Device Guard reports VBS running, VTL1-backed services are active, or a kernel primitive cannot directly modify isolated credentials or protected policy. Record whether Secure Boot is enabled, whether HVCI is enabled, whether the machine is Secured-core, and whether the target is Windows Server, a cloud VM, a consumer Windows 11 build, or an Insider build.

Common VBS-aware routes include data-only VTL0 impact, corrupting unprotected policy state, abusing signed vulnerable drivers, attacking secure interfaces such as hypercalls or trustlet communication, and downgrading the boot or device policy chain when that is in scope.

## Hypervisor-Protected Code Integrity (HVCI) / Memory Integrity

HVCI, exposed in Windows Security as Memory Integrity, runs kernel-mode code integrity decisions in the VBS environment. It helps ensure kernel executable pages are validated before execution and are not writable while executable. It also constrains kernel memory allocations that historically enabled shellcode, unsigned driver loading, or code patching after a kernel bug.

HVCI changes exploit planning: arbitrary kernel write is not automatically arbitrary kernel code execution. A report should call out whether the proof requires code execution, data-only privilege escalation, tampering with an already-signed driver, or a policy bypass.

Treat HVCI as relevant when unsigned driver loading fails, kernel executable memory cannot be patched, code pages cannot become writable and executable, or a signed vulnerable driver becomes the only practical kernel execution path.

HVCI-aware routes include signed vulnerable drivers that are not blocked, data-only kernel exploitation such as token or object corruption, code reuse within trusted kernel images, and compatibility gaps where HVCI is off because of hardware, policy, driver, or virtualization constraints.

## Kernel Data Protection (KDP)

Kernel Data Protection protects selected kernel and driver data from VTL0 tampering by using VBS. Static KDP can protect a section of a loaded driver image, and dynamic KDP can allocate secure read-only memory from a protected pool. Driver developers can request static protection with `MmProtectDriverSection`; that call fails if VSM is disabled.

Current Windows Internals research describes build-dependent changes in the KDP implementation. Record the exact Windows build before assuming secure pool or KDP Pool behavior.

KDP is not a blanket "kernel memory is read-only" feature. It protects opted-in data regions. When reviewing a kernel exploit, identify whether the target data structure is KDP-protected, merely `const`, read-only through normal page table state, or fully mutable in VTL0.

KDP-aware routes include choosing mutable adjacent state, using legitimate APIs that update policy, corrupting inputs before protection is applied, targeting drivers that do not opt in, or exploiting VSM availability assumptions.

## Kernel-Mode Hardware-Enforced Stack Protection (KCET)

Kernel-mode Hardware-enforced Stack Protection extends shadow stack enforcement to kernel mode on supported Windows 11 systems. It depends on hardware support for Intel CET or AMD shadow stacks, and Microsoft documents VBS and HVCI as prerequisites. A protected kernel stack has a corresponding hardware-protected shadow stack; when a return address mismatch is detected, Windows stops the system rather than continuing an unintended control-flow path.

Treat KCET as relevant when return-address corruption fails or bugchecks on hardware and policy combinations that support kernel shadow stacks.

KCET primarily attacks kernel ROP. It does not stop forward-edge calls, callbacks, function pointers, dispatch tables, object methods, or data-only exploitation by itself. Routes around it usually use forward-edge control flow, type-valid object corruption, legitimate call paths, or environments where required hardware, HVCI, VBS, or driver compatibility is missing.

## Control Flow Guard (CFG), Kernel CFG, and eXtended Flow Guard (XFG)

Control Flow Guard protects indirect calls by checking that the destination is a valid call target recorded in load-time metadata. Kernel CFG applies the idea in kernel mode. eXtended Flow Guard narrows some forward-edge calls further by using type-signature metadata rather than accepting every valid CFG target.

When triaging binaries, record whether the module was built with CFG, whether strict CFG is enforced for loaded modules, whether XFG metadata appears in load configuration or related sections, and whether the suspicious indirect edge is actually instrumented.

CFG/XFG-aware routes include calling a valid target with attacker-controlled arguments, counterfeit object-oriented programming through compatible virtual methods, uninstrumented edges or modules, JIT target-marking bugs, and data-only corruption.

## User-Mode Exploit Protection

Windows Exploit Protection exposes per-process mitigations such as DEP, ASLR, mandatory ASLR, bottom-up ASLR, high-entropy ASLR, CFG, ACG, CIG, block remote images, block low-integrity images, untrusted font blocking, win32k system-call disable, child-process creation blocking, extension point disablement, SEHOP, heap integrity, and ROP-oriented checks such as IAF, EAF, CallerCheck, and SimExec.

These settings are often process-specific. Before deciding that an exploit "bypassed Windows," export or inspect the actual process mitigation policy, image load state, token integrity level, loaded modules, child-process policy, and whether audit-only mode was used.

Routes around process mitigations often involve weakly protected helper processes, broker confused deputy paths, trusted code loaded for untrusted purposes, data-only impact, or compatibility opt-outs for JITs, runtimes, plug-ins, input methods, and security products.

## Protected Process Light (PPL), LSA Protection, and Credential Guard

Protected Process Light restricts which processes can open, read, write, debug, or inject into protected processes. Anti-malware services and LSASS commonly use PPL. LSA protection prevents nonprotected processes from reading LSASS memory or injecting code; LSA plug-ins loaded into protected LSA must satisfy Microsoft signature requirements. Credential Guard uses VBS to isolate NTLM hashes, Kerberos TGTs, and domain credentials so ordinary compromise of the Windows kernel or LSASS process is not automatically enough to read those secrets.

For vulnerability reports, distinguish PPL bypass, LSASS memory disclosure, Credential Guard secret extraction, token theft, authentication relay, and local administrator compromise. They are different impact levels.

PPL and Credential Guard routes include kernel arbitrary write or signed vulnerable driver paths, abusing trusted signer levels, stealing tokens or session material instead of isolated secrets, exploiting allowed plug-ins or drivers, and attacking authentication flows that do not require LSASS dumping.

## AppContainer, Less Privileged AppContainer (LPAC), and Integrity Levels

AppContainer isolates applications with low-privilege tokens, capability SIDs, private storage, and restricted access to files, registry, COM, devices, and network resources. LPAC is stricter: it does not automatically receive access to many resources that regular AppContainers can reach through broad `ALL_APPLICATION_PACKAGES` permissions. Windows uses LPAC for especially risky content, parser, and browser surfaces.

For sandbox research, map the token first: integrity level, AppContainer SID, LPAC state, capabilities, package identity, broker processes, named objects, network capabilities, and filesystem or registry ACLs.

Common sandbox routes include broker confused deputy bugs, overbroad capabilities, bad ACLs on named objects, code that assumes regular AppContainer resources are present under LPAC, loopback/network exceptions, and privileged fallback paths.

## Windows App Control, Smart App Control, and Vulnerable Driver Blocklists

Windows App Control for Business, formerly WDAC, changes the model from "run unless known bad" to "run only when policy says yes." It covers applications, scripts, MSIs, batch files, PowerShell constrained language behavior, and kernel drivers. Smart App Control uses signing and cloud reputation signals for consumer and simpler environments. The Microsoft vulnerable driver blocklist blocks known vulnerable or malicious drivers and is enabled with HVCI or S Mode and by default on many modern Windows 11 systems.

Application control is a strong mitigation, not an antivirus replacement. A research note should include policy mode, audit/enforce state, supplemental policies, ISG or managed-installer trust, script enforcement, driver blocklist state, and whether a failure was caused by compatibility holdback.

Routes around application control include policy gaps, signed vulnerable code, blocklist lag, trusted interpreters and LOLBins, MSI custom actions, developer tools, reputation abuse, and supplemental-policy mistakes.

## Administrator Protection

Administrator Protection is a Windows 11 platform security feature in preview that keeps administrator users deprivileged by default and grants just-in-time administrator rights only after explicit Windows Hello verification. Microsoft describes it as a least-privilege elevation model using a hidden, system-managed, profile-separated local administrator account for isolated admin tokens.

This defense matters for local privilege escalation and post-exploitation research because code running in the user's normal context should not silently inherit a reusable linked admin token.

Administrator Protection routes include exploiting the elevated target after consent, abusing installers, services, brokers, scheduled tasks, update flows, shell elevation handlers, and COM elevation monikers, confusing prompt context, or targeting unsupported and disabled deployments. Keep standard-user impact separate; a bug that works without elevation is usually stronger.

## Kernel DMA Protection

Kernel DMA Protection uses the IOMMU to block unauthorized external PCIe-class DMA access, especially Thunderbolt, USB4, and CFexpress scenarios. It can block DMA-capable devices with incompatible drivers while the device is locked or before an authorized user signs in. It does not require VBS, and Microsoft documents `msinfo32.exe` and Windows Security Core Isolation details as ways to check whether it is enabled.

This mitigation matters when a proof assumes physical access, a malicious peripheral, lock-screen memory access, external GPU paths, or driver DMA-remapping compatibility.

DMA-relevant routes include pre-OS attacks, unsupported buses such as FireWire/PCMCIA/CardBus/ExpressCard, DMA-remapping gaps, driver compatibility gaps, and vulnerable trusted firmware or driver paths.

## Kernel Memory, Pool, and Address-Space Mitigations

Windows uses layered kernel memory mitigations: kernel ASLR, DEP/NX, SMEP, nonpaged pool NX defaults, pool cookies and headers, safe unlinking patterns, object reference validation, handle protections, Kernel CFG, HVCI, KDP, and shadow stacks where available. These mitigations make old "write shellcode, jump to it" kernel exploits unrealistic on modern systems.

When reviewing kernel memory corruption, classify the primitive precisely: null dereference, controlled read, controlled write, write-what-where, UAF, type confusion, pool overflow, object lifetime confusion, information leak, or race. Different mitigations matter for each primitive.

Kernel memory routes often pair with an information leak, exploit type-valid corruption, avoid new executable memory, use races and lifetime bugs, or account for mitigation state differences across hardware, build, policy, and compatibility.

## Secure Boot, TPM, Measured Boot, and BitLocker

Secure Boot verifies boot components before Windows runs. TPM-backed measured boot records what loaded. BitLocker can bind disk unlock to PCR measurements so boot-chain tampering changes the key-release conditions. Pluton-equipped devices integrate TPM-like security into the processor package on supported hardware.

These are not memory corruption mitigations, but they shape research around persistence, bootkits, offline tampering, credential theft, and security-feature downgrade.

Routes around boot and device root-of-trust defenses include firmware or boot-component vulnerabilities, recovery and update path abuse, external boot policy mistakes, rollback logic, unsealed secrets after unlock, disabled Secure Boot, weak PCR binding, suspended BitLocker, local recovery-key access, and test-signing modes.

## Reporting Mitigation Interactions

For MSRC-quality reporting, capture the exact Windows build, SKU, hardware, VBS state, HVCI state, Secure Boot state, process mitigation policy, WDAC/SAC state, driver blocklist state, PPL signer level, token attributes, and whether the primitive requires admin, kernel, physical, sandboxed, same-user, or remote code execution.

Unexpected mitigation behavior can be a useful finding:

- A protected process accepts an untrusted plug-in.
- A broker performs privileged work for a sandboxed caller.
- A signed driver exposes arbitrary kernel read/write and is not blocked.
- A process expected to enforce ACG, CIG, or win32k lockdown runs with weaker policy.
- A VBS-backed feature silently falls back because firmware, Secure Boot, hypervisor, or incompatible drivers disable the dependency.
- A data-only exploit remains viable even when HVCI and kernel shadow stacks block classic code execution.
