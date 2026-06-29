---
name: maxtac-asb-ipsw
description: "Use this skill when Apple vulnerability research needs advanced IPSW or OTA provenance, patch diffing, kernelcache or dyld analysis, and firmware-derived ASB evidence."
---

# MaxTAC ASB IPSW Research

Use `ipsw` when firmware artifacts answer a vulnerability-research question. This skill is not a general IPSW usage manual. Start from the security question, preserve provenance, extract only the artifacts needed to answer it, and turn the result into root-cause, reachability, exploitability, or mitigation-bypass evidence.

Treat every fact as build-specific. Preserve the device product type, hardware model or board when relevant, product version, build number, firmware URL or local source path, original file hash, selected restore identity, architecture, `ipsw` version, command line, and whether the fact came from archive metadata, extracted files, reconstructed Mach-O output, diff output, or later RE tooling.

## Research Packet

Create or update `research/apple-firmware/<case-id>/ipsw-research-packet.md` with:

- Question: patch archaeology, vulnerable/fixed diff, kernelcache triage, dyld shared cache triage, entitlement or sandbox delta, trust-cache scope, firmware payload RE, or mitigation-bypass support.
- Vulnerable and fixed builds, including exact device identifiers and restore identity where applicable.
- Artifact provenance bundle path and hashes.
- Component and attack surface: daemon, framework, app extension, kernel subsystem, KEXT, DriverKit extension, iBoot, SEP, coprocessor payload, trust cache, sandbox profile, entitlement, or launchd path.
- Diff anchors: changed file paths, UUIDs, symbols, function starts, selectors, strings, entitlements, sandbox rules, launchd jobs, MIG routines, IOKit user-client methods, syscalls, or Mach traps.
- Root-cause candidate and fix hypothesis.
- Reachability evidence, not just changed-code evidence.
- Exploitability or mitigation-bypass implication.
- Artifacts needed by Source or Binary pack follow-up.

## Provenance Helper

Use `python3 <skill-dir>/scripts/ipsw-provenance.py` as the canonical helper. Actions are `init`, `record-command`, `add-artifact`, `lint`, and `summary`; the helper writes under `<workspace-root>/research/apple-firmware/<case-id>/`.

Initialize before extraction or diffing:

```bash
python3 <skill-dir>/scripts/ipsw-provenance.py init \
  --device iPhone16,1 \
  --model D84AP \
  --product-version 18.2 \
  --build 22C150 \
  --firmware-source ./firmware.ipsw \
  --restore-identity "BuildIdentity-0" \
  --architecture arm64e \
  --command "ipsw info firmware.ipsw --json"
```

Record commands and attach outputs as evidence:

```bash
python3 <skill-dir>/scripts/ipsw-provenance.py record-command <case-id> \
  --command "ipsw extract --kernel --json -o evidence/extract firmware.ipsw" \
  --fact-source extracted-file \
  --capture

python3 <skill-dir>/scripts/ipsw-provenance.py add-artifact <case-id> \
  --category kernelcache \
  --fact-source extracted-file \
  --command "ipsw extract --kernel --json -o evidence/extract firmware.ipsw" \
  --artifact ./evidence/extract/kernelcache.release.iphone
```

Before using firmware evidence in a report or handoff:

```bash
python3 <skill-dir>/scripts/ipsw-provenance.py lint <case-id> --strict
python3 <skill-dir>/scripts/ipsw-provenance.py summary <case-id>
```

## Advanced Workflow

1. Define the research question before downloading or extracting anything. Examples: "Which check was added for this CVE?", "Did the sandbox rule change make this broker path reachable?", "Which kernel user-client method gained validation?", or "Does the fixed build reveal a mitigation bypass constraint?"
2. Acquire the smallest comparable artifact set: vulnerable build, fixed build, matching device class, matching OTA/IPSW type where possible, and any RSR or beta caveats.
3. Extract narrow targets first: kernelcache, specific KEXTs, dyld shared cache members, entitlements, sandbox profiles, launchd plists, trust caches, DeviceTree, SEP or coprocessor payloads, or filesystem paths named by the question.
4. Diff semantically. Prefer symbol, selector, string, function-start, entitlement, sandbox, launchd, trust-cache, and import deltas over broad file lists.
5. Reconstruct root cause. A patch diff is a lead until reachability, attacker-controlled input, missing validation, state transition, or authorization drift is proven.
6. Hand off to Binary or Source pack when the next step needs decompiler output, control-flow evidence, taint, crash replay, or instrumentation.
7. Feed mitigation blockers into `maxtac-asb-mitigations` with build-specific symbols, UUIDs, and changed checks.

## Reference Routing

Read only the reference tied to the active question:

- `<skill-dir>/references/ipsw-acquisition-and-metadata.md`: device/build selection, URLs, archive metadata, signing status, and hash fields.
- `<skill-dir>/references/ipsw-extraction-and-mounting.md`: targeted extraction, mounting, filesystem paths, entitlements, and databases.
- `<skill-dir>/references/ipsw-kernelcache-and-kexts.md`: kernelcache decompression, KEXT extraction, kernel C++ classes, MIG, traps, syscalls, and RE handoff.
- `<skill-dir>/references/ipsw-dyld-shared-cache.md`: dyld shared cache extraction, ObjC/Swift metadata, selectors, symbols, addresses, and imports.
- `<skill-dir>/references/ipsw-img4-aea-and-firmware.md`: IMG4, AEA, iBoot, SEP, coprocessor payloads, trust caches, and wrapped ramdisks.
- `<skill-dir>/references/ipsw-diffing-and-asb-triage.md`: vulnerable/fixed diffing, patch archaeology, cache discipline, and ASB triage.
- `<skill-dir>/references/ipsw-install-build.md`: only when `ipsw` is missing or the installed command surface is incompatible.

## Hard Rules

- Do not present "file changed" as a finding without reachability and security-boundary reasoning.
- Do not compare mismatched device classes, restore identities, beta trains, simulator artifacts, RSR payloads, or OTA/IPSW shapes without noting the caveat.
- Do not flatten filesystem paths when path context is evidence.
- Do not overwrite original firmware artifacts or extracted evidence. Work in explicit output directories.
- Do not let build IDs and case IDs become the stable research-library hierarchy. Move reusable platform knowledge into stable `research/<platform>/...` notes after analysis.
