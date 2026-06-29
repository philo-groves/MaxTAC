# MaxTAC for Apple Systems

MaxTAC for Apple Systems adds Apple Security Bounty Commpage/TCC proof packets, advanced IPSW provenance and patch-diff research, Apple mitigation-bypass workflows, and Apple-specific auditor routing.

Use this pack with MaxTAC Core when the target involves Apple platform research, ASB proof requirements, IPSW/OTA artifacts, Apple firmware, dyld shared cache, kernelcache, or mitigation-bypass evidence.

## When To Use

- ASB Commpage or TCC target-flag proof packets.
- Advanced IPSW/OTA provenance, patch archaeology, kernelcache, dyld shared cache, and firmware-derived evidence.
- Apple mitigation-bypass reasoning after a primitive is proven.
- Build-specific Apple platform evidence and Apple-specific auditor routing.

## Skills

- `maxtac-asb-flag-proof`: Commpage or TCC proof workflows and verifiable ASB target-flag packets.
- `maxtac-asb-ipsw`: advanced IPSW/OTA provenance, patch diffing, kernelcache or dyld analysis, and firmware-derived ASB evidence.
- `maxtac-asb-mitigations`: Apple mitigation-bypass direction, controls, and proof artifacts after a primitive is proven.

## Typical Pairings

- Apple Systems + Binary for kernelcache, dyld, firmware, and native RE.
- Apple Systems + Source when source or decompiler output needs static packet work.
- Apple Systems + Supply Chains when release artifacts, provenance, signing, or package integrity matter.
- Apple Systems + Web when Apple proof depends on browser, WebKit, account, or SaaS workflows.

## Output Artifacts

Apple workflows commonly produce:

- `research/apple/<case-id>/asb-proof-packet.md` for Commpage or TCC proof.
- `research/apple/<case-id>/mitigation-bypass-packet.md` for mitigation-bypass evidence.
- `research/apple-firmware/<case-id>/` IPSW provenance bundles and research packets.
- Crash logs, panic logs, unified logs, entitlements, sandbox profiles, dyld/kernelcache UUIDs, and proof artifact indexes.

## Boundary

This pack does not teach general Apple mitigation background by default. It focuses on bypass direction, build-specific evidence, and proof packets. Use Binary or Source when detailed RE or static analysis is needed.
