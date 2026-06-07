---
name: maxtac-prepare
description: Prepare a MaxTAC target profile for authorized XNU, Windows kernel-adjacent, native binary, crash, fuzzing, patch-diff, or open-source systems research. Use to inventory artifacts, map entry points and trust boundaries, and create data/maxtac/target-profile.json before Auditor selection.
---

# MaxTAC Prepare

Use this skill to build the shared target profile that all Auditors receive. The profile should be specific enough to route work without bloating every subagent prompt.

## Workflow

1. Read researcher-supplied program details, official scope links, allowed operations, lab constraints, and exclusions from the user prompt and target workspace `AGENTS.md` when present. Do not perform broad program lookups unless the user asks.
2. Inventory the target with fast local commands: `rg --files`, manifest reads, symbol listings, binary metadata, crash logs, and build files.
3. Classify the target family: `xnu`, `windows-kernel-adjacent`, `binary`, `open-source-systems`, or mixed.
4. Map entry points and trust boundaries:
   - XNU/Apple: IOKit userclients, MIG interfaces, sysctls, VFS, sandbox/MAC hooks, Mach ports, XPC services, dyld integrations, Apple Security Bounty Target Flags, PAC/ASLR/SPTM assumptions, JOP/gadget/stack/heap reliability needs, network/file parsers, entitlements, and Apple research domain.
   - Windows: driver dispatch tables, IOCTLs, IRPs, object handles, tokens, minifilters, reparse points, ETW/WMI/RPC or service boundaries, public symbols.
   - Binaries: exported APIs, commands, file formats, IPC, update/install paths, parsers, plugins, dynamic loading.
   - Open-source systems: privileged helpers, parsers, IPC, installers, CI/build scripts, unsafe/native boundaries.
5. Record mitigations and assumptions: code signing, entitlements, sandbox checks, ACLs, ProbeForRead/Write, refcounts, locks, sanitizers, CFG/CET/PAC/KASLR, hardening flags.
6. Write or update `data/maxtac/target-profile.json`.

## Helper Script

Use `scripts/init_profile.py` to create a starter profile when no profile exists:

```bash
python <skill-dir>/scripts/init_profile.py --target-name "<name>" --family xnu --root <target-root>
```

Then edit the JSON based on actual recon. Do not leave broad placeholders in fields that drive Auditor selection.

## Profile Fields

Keep these fields useful:

- `target_name`, `target_family`, `scope_summary`, `artifact_roots`
- `platforms`: `xnu`, `windows`, `mach-o`, `pe`, `native`, `oss`
- `target_kinds`: `kernel-source`, `driver-source`, `driver-binary`, `macho`, `pe`, `crash`, `patch-diff`, `native-source`
- `apple_domains`: `apple-intelligence`, `boot-chain`, `comms`, `icloud`, `kernel`, `private-cloud-compute`, `radios`, `sandbox`, `webkit`
- `surfaces`: `iokit`, `mig`, `vfs`, `sandbox`, `mach-port`, `xpc`, `dyld`, `target-flags`, `commpage`, `pac`, `aslr`, `sptm`, `jop`, `gadget-chain`, `stack-pivot`, `heap-grooming`, `tcc`, `ioctl`, `irp`, `object-manager`, `token`, `minifilter`, `parser`, `ipc`, `plugin-loading`, `patch-diff`, `crash`
- `trust_boundaries`, `entrypoints`, `sensitive_sinks`, `mitigations`
- `allowed_operations`, `excluded_families`, `notes`

## Output

End with:

```text
Target profile: data/maxtac/target-profile.json
Target family: <family>
Top surfaces: <list>
Recommended next skill: maxtac-auditor-router
Open questions: <only blockers>
```
