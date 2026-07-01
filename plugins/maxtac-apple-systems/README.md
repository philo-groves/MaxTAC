# MaxTAC for Apple Systems

MaxTAC for Apple Systems adds Apple platform surface triage, Apple Security Bounty Commpage/TCC proof packets, advanced IPSW provenance and patch-diff research, IPSW CVE-history loops, Apple mitigation-bypass workflows, and Apple-specific auditor routing.

Use this pack with MaxTAC Core when the target involves Apple platform research, ASB proof requirements, Apple service or sandbox boundaries, IPSW/OTA artifacts, Apple firmware, dyld shared cache, kernelcache, or mitigation-bypass evidence.

## When To Use

- Apple surface triage across platform build, process identity, entitlements, sandbox, TCC, IPC, services, drivers, WebKit, and bypass direction.
- ASB Commpage or TCC target-flag proof packets.
- Advanced IPSW/OTA provenance, patch archaeology, CVE-history correlation, kernelcache, dyld shared cache, and firmware-derived evidence.
- IPSW CVE-history loops that correlate Apple advisories, build trains, firmware artifacts, binary diffs, source releases, and public CVE context.
- Apple mitigation-bypass reasoning after a primitive is proven.
- Build-specific Apple platform evidence and Apple-specific auditor routing.

## Skills

- `maxtac-apple-surface-triage`: Apple target, identity, entitlement, sandbox, IPC, service, driver, WebKit, and bypass-direction triage.
- `maxtac-asb-flag-proof`: Commpage or TCC proof workflows and verifiable ASB target-flag packets.
- `maxtac-asb-ipsw`: advanced IPSW/OTA provenance, patch diffing, kernelcache or dyld analysis, and firmware-derived ASB evidence.
- `maxtac-asb-ipsw-cve-history-loop`: Apple IPSW/OTA CVE-history and patch-diff correlation loop for build-specific threat modeling.
- `maxtac-asb-mitigations`: Apple mitigation-bypass direction, controls, and proof artifacts after a primitive is proven.

## Typical Pairings

- Apple Systems + Binary for kernelcache, dyld, firmware, and native RE.
- Apple Systems + Source when source or decompiler output needs static packet work.
- Apple Systems + Cloud when Apple proof depends on cloud storage, account services, device management, or cloud-delivered runtime state.
- Apple Systems + Supply Chains when release artifacts, provenance, signing, or package integrity matter.
- Apple Systems + Web when Apple proof depends on browser, WebKit, account, or SaaS workflows.

## Output Artifacts

Apple workflows commonly produce:

- `research/apple/<case-id>/asb-proof-packet.md` for Commpage or TCC proof.
- `research/apple/<case-id>/surface-triage.md` for Apple surface maps and bypass-direction handoffs.
- `research/apple/<case-id>/mitigation-bypass-packet.md` for mitigation-bypass evidence.
- `research/apple-firmware/<case-id>/` IPSW provenance bundles and research packets.
- `contracts/loops/<loop-id>/` Apple IPSW CVE-history loop worklists, gates, events, and next-action prompts.
- Crash logs, panic logs, unified logs, entitlements, sandbox profiles, dyld/kernelcache UUIDs, and proof artifact indexes.

## Boundary

This pack does not teach general Apple mitigation background by default. It focuses on bypass direction, build-specific evidence, and proof packets. Use Binary or Source when detailed RE or static analysis is needed.
