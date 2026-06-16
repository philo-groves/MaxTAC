# IPSW Extraction and Mounting

Use this reference when extracting firmware components, filesystem artifacts,
DMGs, dyld caches, kernelcaches, entitlements, or when mounting an IPSW image for
manual inspection.

## Contents

- [Quick Commands](#quick-commands)
- [Extraction Targets](#extraction-targets)
- [Filesystem and Entitlement Workflows](#filesystem-and-entitlement-workflows)
- [Mounting Restore Images](#mounting-restore-images)
- [Output Discipline](#output-discipline)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

Extract common RE targets:

```bash
ipsw extract --kernel --device iPhone16,1 -o extracted/ firmware.ipsw
ipsw extract --dyld --dyld-arch arm64e -o extracted/ firmware.ipsw
ipsw extract --dtree -o extracted/ firmware.ipsw
ipsw extract --kernel --sep --dyld --dyld-arch arm64e --json -o extracted/ firmware.ipsw
```

Extract firmware and newer protection payloads:

```bash
ipsw extract --iboot -o extracted/ firmware.ipsw
ipsw extract --sep -o extracted/ firmware.ipsw
ipsw extract --sptm -o extracted/ firmware.ipsw
ipsw extract --exclave -o extracted/ firmware.ipsw
```

Extract archive or filesystem matches:

```bash
ipsw extract --pattern '.*\.ttf$' -o extracted/fonts firmware.ipsw
ipsw extract --files --pattern '.*LaunchDaemons.*\.plist$' -o extracted/launchd firmware.ipsw
ipsw extract --files --pattern '.*/MobileSafari$' -o extracted/bin firmware.ipsw
ipsw extract --sys-ver firmware.ipsw
```

Extract specific DMG families:

```bash
ipsw extract --dmg fs -o extracted/dmgs firmware.ipsw
ipsw extract --dmg sys -o extracted/dmgs firmware.ipsw
ipsw extract --dmg exc -o extracted/dmgs firmware.ipsw
ipsw extract --dmg rdisk --ident Erase -o extracted/dmgs firmware.ipsw
```

## Extraction Targets

Use `ipsw info --json` first to identify the actual filenames and restore
identities present in the archive. The high-level extraction flags hide useful
variant choices.

Common target meanings:

- `--kernel`: kernelcache for the selected device or compatible identity.
- `--dyld`: dyld shared cache; pair with `--dyld-arch arm64e` for modern iOS.
- `--driverkit`: DriverKit dyld shared cache.
- `--dtree`: DeviceTree payload.
- `--iboot`: iBoot files.
- `--sep`: Secure Enclave firmware.
- `--sptm`: SPTM and TXM firmwares.
- `--exclave`: Exclave bundle.
- `--dmg app|sys|fs|exc|rdisk|rosetta`: restore image family.
- `--fcs-key` and `--pem-db`: AEA key handling for encrypted DMGs.

If extraction returns multiple plausible outputs, keep all of them until the
build identity, restore identity, device, and architecture selection is clear.

## Filesystem and Entitlement Workflows

Use filesystem regex extraction for targeted triage without mounting:

```bash
ipsw extract --files --pattern '.*/System/Library/LaunchDaemons/.*\.plist$' firmware.ipsw -o fs-launchd/
ipsw extract --files --pattern '.*/usr/libexec/.*' firmware.ipsw -o fs-libexec/
```

Avoid `--flat` for security evidence. Flattening can destroy the path context
that distinguishes a launch daemon, plugin, framework, private framework,
executable, or resource.

Build an entitlement database when entitlement deltas or attack surface matter:

```bash
ipsw ent --sqlite entitlements.db --ipsw firmware.ipsw
ipsw ent --sqlite entitlements.db --key platform-application
ipsw ent --sqlite entitlements.db --value LockdownMode
ipsw ent firmware.ipsw --fs --has com.apple.developer.hardened-process --file-only
```

Use direct `--fs` entitlement search for one-off questions. Use SQLite or
PostgreSQL when comparing many builds or tracking entitlement drift across
devices and versions.

## Mounting Restore Images

Use mounting for manual browsing, but prefer extraction commands for repeatable
automation.

```bash
ipsw mount fs firmware.ipsw
ipsw mount fs firmware.ipsw --mount-point /tmp/ios-fs
ipsw mount fs firmware.ipsw --detach
ipsw mount sys firmware.ipsw --key "<DMG_KEY>"
ipsw mount fs firmware.ipsw --lookup
ipsw mount exc firmware.ipsw --pem-db aea-pems.json
ipsw mount rdisk firmware.ipsw --ident Erase
```

Host support matters. DMG/APFS mounting is most reliable on macOS. On other
hosts, prefer `ipsw extract --files`, `--dmg`, or dedicated filesystem tooling
unless the installed `ipsw` build and OS can mount the image.

Restore ramdisks may appear as `.dmg` entries while actually being IMG4/IM4P
wrapped payloads. If mounting fails, inspect the file with `ipsw img4 info` and
extract the IM4P payload before treating it as a DMG.

## Output Discipline

Always route output:

```bash
mkdir -p evidence/{metadata,extract,logs,hashes}
ipsw extract --kernel --dyld --dyld-arch arm64e --json -o evidence/extract firmware.ipsw \
  | tee evidence/metadata/extract-paths.json
```

Hash extracted high-value files:

```bash
shasum -a 256 evidence/extract/* > evidence/hashes/extracted.sha256
```

If a command supports `--json`, use it for machine evidence and keep a human
text copy only as secondary notes.

## Evidence Checklist

Capture:

- `ipsw info --json` and archive file list.
- Exact extraction flags, output directory, and JSON path output.
- Restore identity, device, and architecture selection.
- Whether extraction came from local archive or `--remote`.
- DMG type, mount point, key/PEM provenance, and mounted path.
- Hashes for extracted kernelcache, dyld cache, DMGs, KEXTs, dylibs, and plists.
- Original paths for filesystem files and entitlements.
- Whether paths were preserved or flattened.

## Official Source Paths

- https://blacktop.github.io/ipsw/docs/cli/ipsw/extract/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/mount/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/info/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/ent/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/img4/info/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/img4/extract/
