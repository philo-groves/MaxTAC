---
name: maxtac-windows-surface-triage
description: "Use this skill when Windows or Microsoft systems vulnerability research needs first-pass build, identity, token, service, COM/RPC/ALPC, object namespace, driver, sandbox, or mitigation surface triage."
---

# MaxTAC Windows Surface Triage

Use this skill as the first pass for Windows and Microsoft systems vulnerability research. The goal is to map the build, actor, token, process boundary, service boundary, IPC surface, named object, driver interface, code-integrity state, and likely proof path before choosing LPAC proof, mitigation work, Binary, Source, Web, Cloud, or auditor routing.

## Operating Rules

- Start from exact platform facts: Windows build, SKU, Insider channel when relevant, architecture, device class, installed feature, target component version, and whether the program requires a specific proof environment.
- Record actor identity: user, group, token type, integrity level, privileges, AppContainer/LPAC/package identity, capability SIDs, service SID, logon session, elevation state, and network/domain context.
- Map the boundary before naming a bug class: UAC/integrity, AppContainer/LPAC, token/impersonation, COM/DCOM/RPC/ALPC, object namespace, service/task/updater, driver/IOCTL, code integrity/WDAC, protected process, registry/filesystem ACL, or browser/document sandbox.
- Use `maxtac-msrc-lpac-proof` when the issue may require MSRC LPAC sandbox proof with SandboxSecurityTools.
- Use `maxtac-msrc-mitigations` after a primitive exists and Windows mitigations or policy controls shape exploitation.
- Pair with Binary for native crash replay, WinDbg/x64dbg work, drivers, COM servers, and memory-corruption evidence. Pair with Source when code or decompiler output needs static closure.

## Triage Workflow

1. Define the target slice: component, executable, service, app package, driver, broker, IPC interface, registry/file path, task, update flow, or sandbox boundary.
2. Inventory entrypoints: COM classes, elevation monikers, DCOM/RPC interfaces, ALPC ports, named pipes, services, scheduled tasks, updaters, file and registry watchers, shell extensions, protocol handlers, preview handlers, drivers, IOCTLs, browser brokers, and package activations.
3. Map identity and authority: process tree, primary/impersonation tokens, integrity levels, privileges, SIDs, AppContainer/LPAC capabilities, service identity, DACL/SACL/integrity labels, and broker audit behavior.
4. Identify protected assets and invariants: higher-integrity execution, privileged service action, cross-user data, sandbox escape, kernel boundary, protected process access, policy-restricted code execution, or sensitive registry/file state.
5. Rank hypotheses around impersonation mistakes, missing RevertToSelf, weak security descriptors, per-user versus machine-wide lookup confusion, writable trusted paths, named-object pre-creation, path canonicalization, reparse points, handle passing, DLL search, and IOCTL validation.
6. Route to the narrowest skill or auditor and keep the packet as the handoff artifact for proof work.

## Windows Surface Triage Packet

Store results under `research/windows/<case-id>/surface-triage.md`:

```markdown
## Windows Surface Triage Packet

- Windows build/SKU/architecture:
- Component or target process:
- Actor, token, integrity, and privileges:
- AppContainer/LPAC/package state:
- Boundary or mitigation:
- Protected asset:
- Entrypoints:
- Service/broker/driver involved:
- ACL, DACL, integrity label, or policy source:
- Attacker-controlled inputs:
- Expected security invariant:
- Suspect bypass direction:
- Crash/debug/proof artifacts collected:
- Suggested workflow: LPAC Proof / Mitigations / Binary / Source / Web / Cloud
- Suggested auditor filters:
- Candidate hypothesis:
- Confidence: low / medium / high
```

## Auditor Routing

Use the Microsoft pack's auditor MCP tools when available. Good starting filters include `com`, `dcom`, `rpc`, `alpc`, `broker`, `object-manager`, `named-pipe`, `symlink`, `token`, `impersonation`, `uac`, `integrity-level`, `service`, `scheduled-task`, `driver`, `ioctl`, `kernel`, `appcontainer`, `lpac`, `code-integrity`, and `wdac`.
