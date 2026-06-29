# MaxTAC for Microsoft Systems

MaxTAC for Microsoft Systems adds Windows surface triage, MSRC LPAC proof guidance, Windows mitigation reasoning, and Microsoft/Windows-specific auditor routing.

Use this pack with MaxTAC Core when the target involves Windows platform behavior, Microsoft service boundaries, MSRC proof expectations, LPAC sandbox escape or data access scenarios, Windows mitigations, or Microsoft-specific evidence.

## When To Use

- Windows surface triage across build, token, integrity, COM/RPC/ALPC, object namespace, services, tasks, drivers, sandboxes, and mitigation boundaries.
- MSRC bounty proof workflows for Windows Insider Preview local sandbox attack scenarios.
- LPAC sandbox escape or private data access proof using Microsoft SandboxSecurityTools.
- Windows mitigation reasoning, constraints, or workaround paths.
- Windows-specific auditor routing.

## Skills

- `maxtac-windows-surface-triage`: Windows identity, IPC, service, driver, sandbox, object namespace, and mitigation-boundary triage.
- `maxtac-msrc-lpac-proof`: MSRC LPAC proof guidance using `LaunchAppContainer` or `EdgeSandboxTestTool`.
- `maxtac-msrc-mitigations`: Windows mitigation reasoning when runtime behavior suggests mitigation constraints or bypass paths.

## Typical Pairings

- Microsoft Systems + Binary for Windows binaries, native debugging, crash replay, and mitigation-aware RE.
- Microsoft Systems + Source when source or decompiler output needs static closure.
- Microsoft Systems + Cloud when Microsoft proof depends on Azure, Entra, cloud storage, device management, or cloud-delivered runtime state.
- Microsoft Systems + Supply Chains when Windows release artifacts, installers, signing, CI/CD, or update channels matter.
- Microsoft Systems + Web when proof depends on account, browser, service, or SaaS flows.

## Output Artifacts

Microsoft workflows commonly produce:

- LPAC proof setup notes and transcripts.
- `research/windows/<case-id>/surface-triage.md` for Windows surface maps and proof-direction handoffs.
- Windows build, token, process, ACL, registry, sandbox, and mitigation evidence.
- Crash/debugger logs when paired with Binary.
- MSRC-oriented proof packets and auditor assessments.

## Boundary

This pack focuses on Microsoft program and Windows platform proof. Use Binary for broad native analysis, Source for static review, Cloud for Azure or cloud identity proof, and Supply Chains for signing or release-path provenance.
