---
name: maxtac-asb-ipsw
description: "Use this skill when Apple firmware reverse engineering requires ipsw for IPSW/OTA download, extraction, kernelcache, dyld_shared_cache, DeviceTree, DMG, IMG4, iBoot, SEP, coprocessor, trust cache, filesystem, mount, diff, or Apple Security Bounty evidence workflows."
---

# MaxTAC ASB IPSW

Use `ipsw` when an Apple firmware artifact is the source of truth: IPSW and OTA acquisition, partial remote extraction, dyld shared cache triage, kernelcache and KEXT preparation, IMG4 payload work, restore image mounting, entitlement/database searches, and patched-vs-vulnerable firmware diffing.

Treat every output as build-specific. Preserve the device product type, model or board when relevant, product version, build number, firmware URL or local source path, original file hash, selected restore identity, architecture, `ipsw` version, command line, and whether facts came from archive metadata, extracted files, reconstructed Mach-O output, or later RE tooling.

Keep build-specific firmware bundles, extracted binaries, hashes, command logs, and generated metadata as artifacts. When firmware work reveals reusable platform knowledge, rewrite it into the stable system research library, such as `research/<platform>/firmware/provenance.md`, `research/<platform>/kernel/<subsystem>.md`, or `research/<platform>/<component>/<subsystem>.md`. Do not let build IDs, dates, or `ipsw` case IDs become the main library hierarchy.

## Provenance Helper

Use `python3 <skill-dir>/scripts/ipsw-provenance.py` to keep firmware-derived facts tied to one build, source hash, restore identity, architecture, tool version, command line, and fact source. The helper creates a bundle under `<workspace-root>/research/apple-firmware/<case-id>/` and lints whether the minimum provenance fields are present.

MaxTAC MCP convention: use `ipsw_provenance` before `scripts/ipsw-provenance.py` when available; actions mirror the script (`init`, `record-command`, `add-artifact`, `lint`, `summary`).

Initialize a provenance bundle:

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

Record commands and classify where facts came from:

```bash
python3 <skill-dir>/scripts/ipsw-provenance.py record-command <case-id> \
  --command "ipsw extract --kernel --json -o evidence/extract firmware.ipsw" \
  --fact-source extracted-file \
  --capture
```

Attach build-specific outputs:

```bash
python3 <skill-dir>/scripts/ipsw-provenance.py add-artifact <case-id> \
  --category kernelcache \
  --fact-source extracted-file \
  --command "ipsw extract --kernel --json -o evidence/extract firmware.ipsw" \
  --artifact ./evidence/extract/kernelcache.release.iphone
```

Before using firmware evidence in a report or handoff, run:

```bash
python3 <skill-dir>/scripts/ipsw-provenance.py lint <case-id> --strict
python3 <skill-dir>/scripts/ipsw-provenance.py summary <case-id>
```

## Readiness Check

Identify the installed `ipsw` entrypoint and current command surface before using examples from this skill:

```bash
ipsw version
ipsw --help
ipsw download ipsw --help
ipsw extract --help
ipsw dyld --help
ipsw kernel --help
ipsw img4 --help
```

On Windows, check the same commands in PowerShell:

```powershell
ipsw.exe version
ipsw.exe extract --help
```

If `ipsw` is missing or a source build is needed, ask first, then read `<skill-dir>/references/ipsw-install-build.md`.

Use explicit output directories. IPSW/OTA artifacts are large, and `ipsw diff` uses persistent caches by default.

## Usage Guidance

### Acquisition and Metadata

Includes device lookup, IPSW and OTA selection, build/version disambiguation, remote URL discovery, archive listing, SystemVersion extraction, SHSH/signing status, firmware key provenance, and evidence fields to record before analysis.

See: `<skill-dir>/references/ipsw-acquisition-and-metadata.md`

### Extraction and Mounting

Includes `ipsw extract` for kernelcache, dyld shared cache, DeviceTree, DMGs, iBoot, SEP, SPTM/TXM, Exclave bundles, filesystem regex extraction, JSON output, remote extraction, `ipsw mount` image types, AEA PEM databases, restore ramdisk identity selection, and entitlement database creation/search.

See: `<skill-dir>/references/ipsw-extraction-and-mounting.md`

### Kernelcache and KEXTs

Includes decompression, KEXT listing/extraction, import resolution, kernel C++ class discovery, MIG subsystem, mach trap and syscall dumping, symbolication with signature folders, IDA handoff, and Ghidra/radare2 preparation boundaries.

See: `<skill-dir>/references/ipsw-kernelcache-and-kexts.md`

### dyld Shared Cache

Includes iOS userspace cache extraction, standalone dylib reconstruction, ObjC/Swift metadata, symbol/address/offset conversion, string and selector search, imports, cross references, class-dump and swift-dump, and cache subfile handling.

See: `<skill-dir>/references/ipsw-dyld-shared-cache.md`

### IMG4, AEA, and Firmware Payloads

Includes IMG4/IM4P/IM4M/IM4R parsing, raw versus decompressed payload extraction, KBAG extraction, keyed decryption, AEA1 DMG handling, wrapped restore ramdisks, iBoot/SEP/coprocessor payload triage, trust cache extraction, and payload handoff to binary RE tools.

See: `<skill-dir>/references/ipsw-img4-aea-and-firmware.md`

### Diffing and ASB Patch Triage

Includes `ipsw diff` modes for files, firmware, launchd, entitlements, sandbox, feature flags, function starts, strings, KDK/signature use, OTA/RSR caveats, cache discipline, and workflows for turning firmware diffs into reportable Apple Security Bounty leads.

See: `<skill-dir>/references/ipsw-diffing-and-asb-triage.md`
