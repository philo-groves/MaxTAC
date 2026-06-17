---
name: maxtac-msrc-mitigations
description: "Use this skill when Windows vulnerability research shows unexpected runtime behavior that may be caused by Microsoft platform mitigations, and the task is to reason about bypasses, constraints, or workaround paths."
---

# MaxTAC MSRC Mitigations

Use this skill to decide whether a Windows mitigation is shaping exploit behavior, what evidence to capture, and when to load the deeper mitigation reference. Do not stop at "the mitigation blocked it" or "the mitigation was bypassed"; capture the exact policy state and the security boundary affected.

## Mitigation Triage

Treat a mitigation as relevant when a primitive is reachable but the expected follow-on action fails, downgrades, audits, or succeeds only on a different Windows build, SKU, hardware class, VM, policy configuration, or process token.

Before reasoning about bypasses or report impact, record:

- Exact Windows build, SKU, architecture, Insider channel when relevant, VM/cloud/physical environment, and hardware security capabilities.
- Secure Boot, TPM, measured boot, BitLocker, VBS/VSM, HVCI, Credential Guard, KCET, Kernel DMA Protection, WDAC/SAC, vulnerable driver blocklist, and Administrator Protection state when relevant.
- Process mitigation policy, loaded module policy, AppContainer/LPAC/integrity level, token capabilities, PPL signer/protection level, and broker relationship for the target process.
- Whether the primitive needs admin, kernel, physical, sandboxed, same-user, or remote code execution before the mitigation interaction matters.
- Event logs, Code Integrity messages, bugchecks, access-denied results, process mitigation output, token dumps, debugger traces, and before/after baselines.

Useful evidence sources include `Get-ComputerInfo`, `Get-CimInstance -Namespace root\Microsoft\Windows\DeviceGuard -ClassName Win32_DeviceGuard`, `Get-ProcessMitigation`, `whoami /all`, process token inspection, Code Integrity event logs, `msinfo32`, WDAC policy exports, and target-specific debugger output.

## When A Mitigation May Be Active

| Mitigation | Signals worth checking | Read more |
| --- | --- | --- |
| VBS/VSM | Device Guard reports virtualization-based security, VTL1-backed services are running, or kernel compromise cannot directly alter isolated policy or credentials. | `<skill-dir>/references/windows-platform-mitigations.md#virtualization-based-security-vbs-and-virtual-secure-mode-vsm` |
| HVCI / Memory Integrity | Unsigned or modified kernel code cannot execute, writable/executable kernel mappings fail, or signed vulnerable driver paths become the viable route. | `<skill-dir>/references/windows-platform-mitigations.md#hypervisor-protected-code-integrity-hvci--memory-integrity` |
| KDP | Specific kernel or driver data resists VTL0 writes while adjacent mutable state remains writable; target code uses protected data sections or KDP APIs. | `<skill-dir>/references/windows-platform-mitigations.md#kernel-data-protection-kdp` |
| KCET / shadow stacks | Return-address hijack attempts bugcheck or fail on supported hardware with kernel shadow stacks and HVCI enabled. | `<skill-dir>/references/windows-platform-mitigations.md#kernel-mode-hardware-enforced-stack-protection-kcet` |
| CFG/KCFG/XFG | Load config or runtime policy constrains indirect calls, but valid targets, callbacks, or data-only paths remain possible. | `<skill-dir>/references/windows-platform-mitigations.md#control-flow-guard-cfg-kernel-cfg-and-extended-flow-guard-xfg` |
| User-mode Exploit Protection | `Get-ProcessMitigation` or process policy shows DEP, ASLR, ACG, CIG, win32k lockdown, child-process blocking, or related settings. | `<skill-dir>/references/windows-platform-mitigations.md#user-mode-exploit-protection` |
| PPL / LSA / Credential Guard | Protected processes reject handles, injection, or memory reads; secrets are isolated even after ordinary kernel or LSASS compromise. | `<skill-dir>/references/windows-platform-mitigations.md#protected-process-light-ppl-lsa-protection-and-credential-guard` |
| AppContainer / LPAC | Token inspection shows AppContainer, LPAC, Low IL, capabilities, package identity, or restricted broker-mediated access. | `<skill-dir>/references/windows-platform-mitigations.md#appcontainer-less-privileged-appcontainer-lpac-and-integrity-levels` |
| WDAC / SAC / driver blocklists | Code Integrity policy, Smart App Control, HVCI, S Mode, or blocklist state controls which apps, scripts, or drivers can load. | `<skill-dir>/references/windows-platform-mitigations.md#windows-app-control-smart-app-control-and-vulnerable-driver-blocklists` |
| Administrator Protection | Admin users run deprivileged until Windows Hello approval produces a separate just-in-time admin token. | `<skill-dir>/references/windows-platform-mitigations.md#administrator-protection` |
| Kernel DMA Protection | `msinfo32` or device policy reports DMA protection, especially for Thunderbolt, USB4, CFexpress, lock-screen, or external PCIe paths. | `<skill-dir>/references/windows-platform-mitigations.md#kernel-dma-protection` |
| Kernel memory mitigations | Kernel memory corruption behaves as data-only, type-valid, or info-leak-dependent because classic shellcode or ROP paths are blocked. | `<skill-dir>/references/windows-platform-mitigations.md#kernel-memory-pool-and-address-space-mitigations` |
| Secure Boot / TPM / BitLocker | Boot trust, PCR measurements, recovery state, firmware policy, or disk unlock behavior changes exploitability or persistence. | `<skill-dir>/references/windows-platform-mitigations.md#secure-boot-tpm-measured-boot-and-bitlocker` |

## When To Read The Reference

Read `<skill-dir>/references/windows-platform-mitigations.md` when:

- A Windows primitive behaves differently across build, SKU, hardware, policy, token, sandbox, or process mitigation state.
- A proof needs to explain why code execution, credential access, sandbox escape, driver loading, DMA, or persistence is blocked or still viable.
- A chain depends on data-only exploitation, broker abuse, valid code reuse, signed vulnerable code, policy gaps, or another mitigation-aware path.
- An MSRC report needs precise mitigation interaction evidence rather than generic "blocked" or "bypassed" wording.

Pair this skill with `maxtac-msrc-lpac-proof` for Windows Insider Preview local sandbox attack scenarios and with `maxtac-dast-debugger` when runtime policy or token evidence must be captured.
