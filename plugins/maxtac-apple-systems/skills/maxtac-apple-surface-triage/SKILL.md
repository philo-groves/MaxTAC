---
name: maxtac-apple-surface-triage
description: "Use this skill when Apple platform vulnerability research needs first-pass target, build, entitlement, sandbox, TCC, IPC, service, driver, WebKit, or mitigation-bypass surface triage."
---

# MaxTAC Apple Surface Triage

Use this skill as the first pass for Apple platform vulnerability research. The goal is to map the build, component, trust boundary, attacker-controlled input, brokered service, entitlement state, and likely proof path before choosing ASB proof, IPSW research, mitigation-bypass work, Binary, Source, Web, or auditor routing.

## Operating Rules

- Start from the exact platform and build: macOS, iOS, iPadOS, visionOS, tvOS, watchOS, bridgeOS, firmware, simulator, hardware model, SoC family, and IPSW/OTA build when available.
- Record target identity: bundle ID, Team ID, signing authority, entitlements, sandbox profile, app group, extension point, launchd label, service name, Mach service, XPC service, DriverKit extension, kext, daemon, or WebKit process.
- Map the boundary before naming a bug class: TCC, App Sandbox/Seatbelt, AMFI/code signing, Hardened Runtime, Gatekeeper/quarantine, SIP/SSV, Data Vault, WebContent sandbox, Lockdown Mode, IOKit/kernel, or SPTM/TXM/MIE class mitigations.
- Focus on bypass direction and verifiable proof. Use `maxtac-asb-flag-proof` when the path may produce Commpage or TCC Target Flag evidence.
- Use `maxtac-asb-ipsw` when build-specific firmware, dyld shared cache, kernelcache, or patch archaeology is needed.
- Use `maxtac-asb-mitigations` after a primitive exists and the question is whether Apple mitigations block or shape exploitation.
- Pair with Binary for dyld, kernelcache, native crash replay, or debugger evidence. Pair with Source when source or decompiler output needs static closure.

## Triage Workflow

1. Define the target slice: product, platform, build, device class, component, process, entitlement set, sandbox state, and program scope.
2. Inventory entrypoints: file formats, URL schemes, document handlers, pasteboard, drag/drop, previews, Spotlight/importers, extensions, XPC, Mach services, LaunchServices, launchd jobs, IOKit user clients, DriverKit, WebKit IPC, network services, sync/backup/migration paths, and MDM/profile inputs.
3. Map identities and brokers: client audit tokens, code-signing identity, Team ID, bundle ID, entitlements, app groups, security-scoped bookmarks, helper tools, privileged daemons, app extensions, and inherited permissions.
4. Identify protected assets and invariants: user data, TCC resources, app container isolation, privileged helper actions, platform-binary trust, unsigned-code restrictions, protected filesystem locations, kernel attack surface, or target-flag state.
5. Rank hypotheses around broker confusion, missing audit-token checks, entitlement confusion, path canonicalization, symlink/hardlink/race behavior, stale security-scoped state, plugin loading, IPC schema validation, generated previews, and mitigation-specific bypasses.
6. Route to the narrowest skill or auditor. Keep the packet small enough that a proof workflow can continue from it without rediscovering the target.

## Apple Surface Triage Packet

Store results under `research/apple/<case-id>/surface-triage.md`:

```markdown
## Apple Surface Triage Packet

- Platform/build/hardware:
- Component or target process:
- Bundle/team/signing identity:
- Entitlements and sandbox state:
- Boundary or mitigation:
- Protected asset or target flag:
- Entrypoints:
- Broker/service/helper involved:
- Client identity source:
- Attacker-controlled inputs:
- Expected security invariant:
- Suspect bypass direction:
- Build-specific artifacts:
- Crash/log/proof artifacts collected:
- Suggested workflow: Flag Proof / IPSW / Mitigations / Binary / Source / Web
- Suggested auditor filters:
- Candidate hypothesis:
- Confidence: low / medium / high
```

## Auditor Routing

Use the Apple pack's auditor MCP tools when available. Good starting filters include `tcc`, `sandbox`, `entitlements`, `xpc`, `mach`, `gatekeeper`, `quarantine`, `amfi`, `code-signing`, `hardened-runtime`, `sip`, `webkit`, `lockdown-mode`, `kernel`, `iokit`, `driverkit`, `sptm`, `mie`, and `memory-tagging`.
