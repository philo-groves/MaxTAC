---
name: maxtac-msrc-mitigations
description: "Use this skill when Windows, Windows Server, Microsoft endpoint, browser, Office, kernel, driver, sandbox, credential, or local privilege escalation research produces unexpected behavior that may be caused by Windows defenses or exploit mitigations. Covers VBS, HVCI, KDP, CET shadow stacks, CFG/XFG/KCFG, exploit protection, PPL, Credential Guard, AppContainer/LPAC, WDAC/App Control, Smart App Control, vulnerable driver blocklists, Administrator Protection, DMA protection, and common mitigation bypass patterns."
---

## Virtualization-Based Security (VBS) and Virtual Secure Mode (VSM)
Virtualization-Based Security uses the Windows hypervisor to create a protected
environment that becomes a root of trust even when the normal NT kernel is
assumed to be compromised. The normal kernel and most drivers run in VTL0. The
secure kernel and VBS-backed trustlets run in VTL1. Windows builds multiple
mitigations on this split, including HVCI, Credential Guard, Kernel Data
Protection, kernel shadow stacks, and some secure policy enforcement.

For vulnerability research, first separate "kernel compromise" from "VTL1
compromise." A bug that gives arbitrary read/write in VTL0 is still serious,
but VBS can prevent the classic next step of loading unsigned kernel code,
patching protected policy data, or directly extracting isolated credentials.
Record whether VBS is running, whether Secure Boot is enabled, whether HVCI is
enabled, and whether the target is a Secured-core PC, Windows Server, cloud VM,
or consumer Windows 11 build.

### Bypassing VBS and VSM
- **Attack VTL0 Data Instead of Code**: VBS raises the bar for kernel code
  execution, so modern exploits often pursue data-only primitives in mutable
  VTL0 structures.
- **Target Unprotected Policy State**: Only specific state is protected by VTL1
  or KDP. Policy pointers, caches, reference counts, and broker decisions may
  remain mutable even when the final policy value is protected.
- **Use Signed Vulnerable Drivers**: Bring Your Own Vulnerable Driver (BYOVD)
  remains one of the most practical VTL0 entry paths when HVCI, WDAC, and the
  vulnerable driver blocklist do not block the driver.
- **Exploit Secure Interfaces**: Bugs in hypercalls, secure kernel interfaces,
  trustlet communication, or VBS device paths are higher-value because they can
  cross the intended VTL boundary.
- **Downgrade the Boot Chain**: If Secure Boot, firmware protections, or device
  guard policy are disabled or misconfigured, attackers may be able to turn off
  or weaken VBS before the OS is trusted.

## Hypervisor-Protected Code Integrity (HVCI) / Memory Integrity
HVCI, exposed in Windows Security as Memory Integrity, runs kernel-mode code
integrity decisions in the VBS environment. It helps ensure kernel executable
pages are validated before execution and are not writable while executable. It
also constrains kernel memory allocations that historically enabled shellcode,
unsigned driver loading, or code patching after a kernel bug.

HVCI changes exploit planning: arbitrary kernel write is no longer equivalent
to arbitrary kernel code execution. A report should call out whether the proof
requires code execution, data-only privilege escalation, tampering with an
already-signed driver, or a policy bypass.

### Bypassing HVCI / Memory Integrity
- **BYOVD With a Nonblocked Driver**: HVCI blocks unsigned or untrusted kernel
  code, but a signed vulnerable driver can still expose powerful IOCTLs unless
  WDAC or the vulnerable driver blocklist catches it.
- **Data-Only Kernel Exploitation**: Token stealing, object pointer swaps,
  callback list edits, handle table manipulation, and security policy flips may
  succeed without introducing new executable pages.
- **Code Reuse Within Trusted Kernel Images**: HVCI does not make signed code
  memory safe. Existing functions, gadgets, or confused driver APIs can still
  be abused if reachable.
- **Compatibility Gaps**: HVCI can be off because of incompatible drivers,
  enterprise policy, unsupported hardware, virtualization conflicts, or user
  choice. Always verify actual state instead of assuming Windows 11 defaults.
- **Firmware or Pre-OS Attacks**: HVCI starts after the boot trust chain. It is
  not a substitute for Secure Boot, firmware integrity, or DMA protection.

## Kernel Data Protection (KDP)
Kernel Data Protection protects selected kernel and driver data from VTL0
tampering by using VBS. Static KDP can protect a section of a loaded driver
image, and dynamic KDP can allocate secure read-only memory from a protected
pool. Driver developers can request static protection with
`MmProtectDriverSection`; that call fails if VSM is disabled.

Current Windows Internals research describes a 26H2-era shift away from the
older dynamic KDP "secure pool" toward an internal KDP Pool design based on
protected kernel data sections. Treat this as build-dependent: record the exact
Windows build before assuming secure pool or KDP Pool behavior.

KDP is not a blanket "kernel memory is read-only" feature. It protects opted-in
data regions. When reviewing a kernel exploit, identify whether the target data
structure is KDP-protected, merely `const`, read-only through normal page table
state, or fully mutable in VTL0.

### Bypassing KDP
- **Choose Mutable Adjacent State**: If a protected policy value cannot be
  modified, nearby pointers, indexes, handles, generation counters, cache
  entries, or authorization decisions may still be writable.
- **Exploit Logic Instead of Writes**: A legitimate code path can make a
  security-relevant change without violating KDP if the policy allows that
  update through an API.
- **Corrupt Inputs Before Protection**: Static and dynamic KDP usually protect
  data after initialization. Bugs that affect construction, parsing, or
  registration can poison protected data before it becomes read-only.
- **Target Drivers That Do Not Opt In**: Third-party kernel drivers often do not
  use KDP for their own sensitive state.
- **Disable the Underlying VSM Requirement**: KDP depends on VBS/VSM. If VSM is
  unavailable, APIs such as `MmProtectDriverSection` cannot enforce protection.

## Kernel-Mode Hardware-Enforced Stack Protection (KCET)
Kernel-mode Hardware-enforced Stack Protection extends shadow stack enforcement
to kernel mode on supported Windows 11 systems. It depends on hardware support
for Intel CET or AMD shadow stacks, and Microsoft documents VBS and HVCI as
prerequisites. A protected kernel stack has a corresponding hardware-protected
shadow stack; when a return address mismatch is detected, Windows stops the
system rather than continuing an unintended control-flow path.

This mitigation specifically attacks kernel ROP. It does not stop all kernel
exploit strategies, and it can block drivers that hijack return addresses or use
shadow-stack-incompatible obfuscation.

### Bypassing Kernel Shadow Stacks
- **Use Forward-Edge Control Flow**: Shadow stacks protect returns. Indirect
  calls, callbacks, function pointers, dispatch tables, and object methods are
  primarily constrained by CFG/KCFG/XFG, not by return shadow stacks.
- **Use Data-Only Exploitation**: Privilege changes, policy changes, and object
  corruption that do not require a fake return chain can avoid shadow-stack
  enforcement.
- **Find Legitimate Call Paths**: If the vulnerable driver exposes an operation
  that already performs the desired action, no ROP chain is needed.
- **Rely on Coverage Gaps**: Kernel shadow stacks require compatible hardware,
  VBS, HVCI, and compatible drivers. Older devices, disabled HVCI, and
  incompatible driver environments may lack enforcement.
- **Attack Context Management Bugs**: Exception dispatch, context switching,
  emulation, or kernel/user transition bugs are higher-value because they can
  disturb the relationship between normal and shadow stack state.

## Control Flow Guard (CFG), Kernel CFG, and eXtended Flow Guard (XFG)
Control Flow Guard protects indirect calls by checking that the destination is a
valid call target recorded in load-time metadata. Kernel CFG applies the idea in
kernel mode. eXtended Flow Guard narrows some forward-edge calls further by
using type-signature metadata rather than accepting every valid CFG target.

When triaging binaries, record whether the module was built with CFG, whether
strict CFG is enforced for loaded modules, whether XFG metadata appears in the
load configuration or related sections, and whether the suspicious indirect
edge is actually instrumented.

### Bypassing CFG, KCFG, and XFG
- **Call a Valid Target**: CFG stops arbitrary targets, not malicious use of a
  valid function with attacker-controlled arguments.
- **Counterfeit Object-Oriented Programming (COOP)**: C++ virtual dispatch can
  be redirected through valid virtual methods when object layout is attacker
  controlled. XFG makes this harder when prototypes differ, but same-signature
  targets can remain useful.
- **Use Uninstrumented Edges or Modules**: CFG depends on compiler and loader
  support. Legacy modules, handwritten assembly, callback edges, and certain
  thunk paths may not be equally protected.
- **Abuse JIT or Dynamic Code Policy**: JIT engines must create valid call
  targets for generated code. Bugs in JIT permission transitions or target
  marking can weaken CFG and ACG together.
- **Pivot to Returns or Data**: CFG is a forward-edge defense. Stack returns
  need CET/shadow stacks; data-only corruption may bypass both.

## User-Mode Exploit Protection
Windows Exploit Protection exposes per-process mitigations such as DEP, ASLR,
mandatory ASLR, bottom-up ASLR, high-entropy ASLR, CFG, ACG, CIG, block remote
images, block low-integrity images, untrusted font blocking, Win32k system-call
disable, child-process creation blocking, extension point disablement, SEHOP,
heap integrity, and ROP-oriented checks such as IAF/EAF/CallerCheck/SimExec.

These settings are often process-specific. Before deciding that an exploit
"bypassed Windows," export or inspect the actual process mitigation policy,
image load state, token integrity level, loaded modules, child process policy,
and whether audit-only mode was used.

### Bypassing Exploit Protection
- **Exploit Missing Per-Process Coverage**: Many mitigations require a process
  policy or compatible binary. The parent, broker, helper, plugin host, or
  update service may run with weaker settings than the renderer or parser.
- **Use the Broker Model Against Itself**: ACG, CIG, Win32k lockdown, and child
  process bans are often paired with a privileged broker. Broker confused
  deputy bugs can turn a mitigation architecture into a reachability path.
- **Load Trusted Code for Untrusted Purposes**: CIG and image load rules allow
  trusted signers. A vulnerable or overly powerful signed module can still be an
  exploit primitive.
- **Target Data-Only Impact**: DEP, ACG, CFG, and ROP checks primarily prevent
  code execution patterns. Credential, policy, file, registry, or IPC
  corruption can still be reportable.
- **Use Compatibility Opt-Outs**: JITs, .NET runtimes, legacy ATL thunking,
  plug-in ecosystems, API hooking, IMEs, and security products frequently need
  mitigation exceptions.

## Protected Process Light (PPL), LSA Protection, and Credential Guard
Protected Process Light restricts which processes can open, read, write, debug,
or inject into protected processes. Anti-malware services and LSASS commonly use
PPL. Added LSA protection prevents nonprotected processes from reading LSASS
memory or injecting code; LSA plug-ins loaded into protected LSA must satisfy
Microsoft signature requirements. Credential Guard goes further by using VBS to
isolate NTLM hashes, Kerberos TGTs, and domain credentials so that ordinary
compromise of the Windows kernel or LSASS process is not automatically enough to
read those secrets.

For vulnerability reports, distinguish PPL bypass, LSASS memory disclosure,
Credential Guard secret extraction, token theft, authentication relay, and local
administrator compromise. They are different impact levels.

### Bypassing PPL, LSA Protection, and Credential Guard
- **Kernel Arbitrary Write or BYOVD**: PPL state is enforced by the kernel. A
  kernel primitive can often downgrade process protection, open forbidden
  handles, or tamper with callbacks unless VBS-backed policy blocks the target.
- **Abuse Trusted Signer Levels**: PPL is a signer hierarchy. A trusted,
  vulnerable, or misconfigured protected component can become a gateway into a
  same-or-lower protected process.
- **Steal Tokens Instead of Secrets**: Credential Guard protects certain stored
  secrets, but access tokens, sessions, cookies, OAuth refresh tokens, DPAPI
  material after unlock, and delegated network access may remain in scope.
- **Exploit Plug-in and Driver Load Rules**: LSA protection rejects unsigned or
  incorrectly signed plug-ins, but vulnerable allowed plug-ins or drivers are
  still code running near the trust boundary.
- **Attack Authentication Flows**: Pass-the-hash and pass-the-ticket are harder
  with Credential Guard, but phishing, relay, Kerberos delegation abuse,
  cloud-token theft, and protocol downgrade bugs may avoid LSASS dumping.

## AppContainer, Less Privileged AppContainer (LPAC), and Integrity Levels
AppContainer isolates applications with low-privilege tokens, capability SIDs,
private storage, and restricted access to files, registry, COM, devices, and
network resources. LPAC is stricter: it does not automatically receive access to
many resources that regular AppContainers can reach through broad
`ALL_APPLICATION_PACKAGES` permissions. Windows uses LPAC for especially risky
content, parser, and browser surfaces.

For sandbox research, map the token first: integrity level, AppContainer SID,
LPAC state, capabilities, package identity, broker processes, named objects,
network capabilities, and filesystem/registry ACLs.

### Bypassing AppContainer and LPAC
- **Broker Confused Deputy**: The normal escape path is not direct file or
  registry access; it is a broker that performs a privileged operation without
  binding the request to the sandboxed caller's authority.
- **Overbroad Capabilities**: Capabilities are security decisions. A capability
  that looks harmless can grant device, network, private API, or enterprise
  resource access.
- **Bad ACLs on Named Objects**: Shared sections, ALPC ports, pipes, COM
  servers, registry keys, directories, and device objects can accidentally grant
  access to AppContainer, `ALL_APPLICATION_PACKAGES`, or a capability SID.
- **Regular AppContainer Assumptions in LPAC**: LPAC lacks resources that normal
  AppContainers receive. Code that silently falls back to broker or privileged
  paths under LPAC deserves attention.
- **Loopback and Network Exceptions**: Network access is capability-mediated,
  and debug or loopback exemptions can alter a sandbox's real attack surface.

## Windows App Control, Smart App Control, and Vulnerable Driver Blocklists
Windows App Control for Business, formerly WDAC, changes the model from "run
unless known bad" to "run only when policy says yes." It covers applications,
scripts, MSIs, batch files, PowerShell constrained language behavior, and kernel
drivers. Smart App Control, introduced for Windows 11 version 22H2, uses the
same family of application control technology with signing and cloud reputation
signals for consumers and simpler environments. The Microsoft vulnerable driver
blocklist blocks known vulnerable or malicious drivers and is enabled with HVCI
or S Mode, and by default on Windows 11 version 22H2 and later.

Application control is a strong mitigation, not an antivirus replacement. A
research note should include policy mode, audit/enforce state, supplemental
policies, ISG or managed-installer trust, script enforcement, driver blocklist
state, and whether a failure was caused by compatibility holdback.

### Bypassing App Control and Driver Blocklists
- **Policy Gaps**: Publisher rules, path rules, broad hash exceptions,
  supplemental policies, and managed installer trust can admit more code than
  intended.
- **Signed Vulnerable Code**: Signed and allowed does not mean safe. BYOVD
  attacks rely on legitimate signed drivers with dangerous primitives.
- **Known-Unknown Driver Lag**: Microsoft notes the downloadable block rules may
  be more complete than the OS-delivered list, and the blocklist is not
  guaranteed to cover every vulnerable driver.
- **Living off Trusted Interpreters**: PowerShell, script hosts, Office macros,
  LOLBins, MSI custom actions, and developer tools can remain useful if policy
  does not constrain scripts and child processes.
- **Reputation Abuse**: Smart App Control and ISG trust cloud predictions.
  Newly signed, repackaged, or reputation-manipulated code is a different
  research surface from a pure signature bypass.

## Administrator Protection
Administrator Protection is a Windows 11 platform security feature in preview
that keeps administrator users deprivileged by default and grants just-in-time
administrator rights only after explicit Windows Hello verification. Microsoft
describes it as a least-privilege elevation model using a hidden,
system-managed, profile-separated local administrator account for isolated
admin tokens. It is not just a cosmetic UAC prompt change.

This defense matters for local privilege escalation and post-exploitation
research because malware running in the user's normal context should not be able
to silently inherit a reusable linked admin token.

### Bypassing Administrator Protection
- **Exploit the Elevated Target After Consent**: Once a user approves elevation,
  the elevated process and its IPC surface become the next trust boundary.
- **Abuse Installers, Services, and Brokers**: MSI repair paths, service control
  flows, scheduled tasks, update brokers, shell elevation handlers, and COM
  elevation monikers are high-value because they mediate privileged actions.
- **Steal or Confuse the Request Context**: Bugs that make the prompt describe
  the wrong binary, wrong publisher, wrong path, or wrong operation can turn
  user consent into a bypass.
- **Target Unsupported or Disabled Deployments**: Administrator Protection is
  preview and policy-dependent. Older Windows builds and many enterprise images
  may still use legacy Admin Approval Mode.
- **Keep Standard-User Impact Separate**: A bug that works without elevation is
  often more valuable than one that needs an Administrator Protection prompt.

## Kernel DMA Protection
Kernel DMA Protection uses the IOMMU to block unauthorized external PCIe-class
DMA access, especially Thunderbolt, USB4, and CFexpress scenarios. It can block
DMA-capable devices with incompatible drivers while the device is locked or
before an authorized user signs in. It does not require VBS, and Microsoft
documents `msinfo32.exe` and Windows Security Core Isolation details as ways to
check whether it is enabled.

This mitigation matters when a proof of vulnerability assumes physical access,
evil peripheral behavior, lock-screen memory access, external GPU paths, or
driver DMA-remapping compatibility.

### Bypassing Kernel DMA Protection
- **Attack Before the OS Loads**: Microsoft documents that Kernel DMA
  Protection does not protect against drive-by DMA during boot; firmware must
  handle that phase.
- **Use Unsupported Buses**: The mitigation does not cover FireWire, PCMCIA,
  CardBus, or ExpressCard.
- **Find DMA-Remapping Gaps**: Not all devices and drivers support DMA
  remapping. Internal/external location, driver properties, and WDDM generation
  can change behavior.
- **Exploit Firmware or Driver Trust**: IOMMU policy can limit memory access,
  but a vulnerable trusted driver or firmware path may still expose the data or
  device operation the attacker wants.

## Kernel Memory, Pool, and Address-Space Mitigations
Windows uses many layered kernel memory mitigations: kernel ASLR, DEP/NX, SMEP,
nonpaged pool NX defaults, pool cookies and headers, safe unlinking patterns,
object reference validation, handle protections, Kernel CFG, HVCI, KDP, and
shadow stacks where available. These mitigations make old "write shellcode,
jump to it" kernel exploits unrealistic on modern systems.

When reviewing kernel memory corruption, classify the primitive precisely:
null dereference, controlled read, controlled write, write-what-where, UAF,
type confusion, pool overflow, object lifetime confusion, information leak, or
race. Different mitigations matter for each primitive.

### Bypassing Kernel Memory Mitigations
- **Pair With an Info Leak**: KASLR and pointer encoding usually fall when a
  reliable kernel pointer or object disclosure exists.
- **Exploit Type-Valid Corruption**: Pool cookies and metadata hardening do not
  stop replacing one valid object, pointer, handle, flag, or reference count
  with another semantically useful value.
- **Avoid New Executable Memory**: Modern kernel exploitation often uses
  data-only outcomes, legitimate kernel APIs, or signed driver functionality.
- **Use Races and Lifetime Bugs**: UAFs, reference count bugs, and double-fetch
  bugs can bypass simple bounds and metadata checks because the object was valid
  at one point in the flow.
- **Account for Mitigation State**: Kernel CFG, HVCI, KCET, KDP, and the driver
  blocklist vary by hardware, build, policy, and compatibility.

## Secure Boot, TPM, Measured Boot, and BitLocker
Secure Boot verifies boot components before Windows runs. TPM-backed measured
boot records what loaded. BitLocker can bind disk unlock to PCR measurements so
boot-chain tampering changes the key-release conditions. Pluton-equipped
devices integrate TPM-like security into the processor package on supported
hardware.

These are not memory corruption mitigations, but they shape vulnerability
research around persistence, bootkits, offline tampering, credential theft, and
security-feature downgrade.

### Bypassing Boot and Device Root-of-Trust Defenses
- **Exploit Firmware or Boot Components**: Secure Boot depends on trusted
  firmware, revocation state, and bootloader validation. Bugs below Windows can
  disable later mitigations.
- **Abuse Recovery and Update Paths**: Recovery environments, rollback logic,
  external boot policy, and update staging can alter measurements or trust.
- **Target Unsealed Secrets Elsewhere**: BitLocker protects data at rest. After
  unlock, secrets can move into memory, tokens, DPAPI state, applications, and
  cloud sessions.
- **Find Policy Misconfiguration**: Disabled Secure Boot, weak PCR binding,
  suspended BitLocker, local admin recovery-key access, and test-signing modes
  change the threat model dramatically.

## Reporting Mitigation Interactions
For MSRC-quality reporting, do not stop at "the mitigation blocked it" or "the
mitigation was bypassed." Capture the exact Windows build, SKU, hardware, VBS
state, HVCI state, Secure Boot state, process mitigation policy, WDAC/SAC state,
driver blocklist state, PPL signer level, token attributes, and whether the
primitive requires admin, kernel, physical, or sandboxed code execution.

Unexpected mitigation behavior is often a useful finding:

- A protected process accepts an untrusted plug-in.
- A broker performs privileged work for a sandboxed caller.
- A signed driver exposes arbitrary kernel read/write and is not blocked.
- A process expected to enforce ACG/CIG/Win32k lockdown runs with weaker
  mitigation policy.
- A VBS-backed feature silently falls back because firmware, Secure Boot,
  hypervisor, or incompatible drivers disable the dependency.
- A data-only exploit remains viable even when HVCI and kernel shadow stacks
  block classic code execution.
