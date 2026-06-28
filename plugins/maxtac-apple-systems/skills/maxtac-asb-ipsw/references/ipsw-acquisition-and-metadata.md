# IPSW Acquisition and Metadata

Use this reference when choosing firmware builds, downloading IPSWs or OTAs,
recording build identity, or deciding whether a partial remote extraction is
enough for the current reverse engineering question.

## Contents

- [Quick Commands](#quick-commands)
- [Build Identity](#build-identity)
- [IPSW, OTA, RSR, and Simulator Inputs](#ipsw-ota-rsr-and-simulator-inputs)
- [Remote Extraction Versus Full Downloads](#remote-extraction-versus-full-downloads)
- [Keys, SHSH, and Provenance](#keys-shsh-and-provenance)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

List and resolve devices:

```bash
ipsw device-list --plain
ipsw device-list --json > device-list.json
ipsw device-info --prod iPhone16,1 --json > iPhone16,1.json
ipsw device-info --name "iPhone 15 Pro" --json
```

Discover or download IPSWs:

```bash
ipsw download ipsw --device iPhone16,1 --latest --urls
ipsw download ipsw --device iPhone16,1 --version 18.2 --urls
ipsw download ipsw --device iPhone16,1 --build 22C150 -o firmware/
ipsw download ipsw --device iPhone16,1 --latest --kernel --dyld --dyld-arch arm64e -o extracted/
```

Discover or download OTAs:

```bash
ipsw download ota --platform ios --latest --device iPhone16,1 --urls --json
ipsw download ota --platform ios --version 18.2 --device iPhone16,1 -o ota/
ipsw download ota --platform ios --latest --kernel --dyld --dyld-arch arm64e -o extracted/
ipsw download ota --platform ios --latest --fcs-keys -o keys/
```

Record archive metadata before extraction:

```bash
ipsw info iPhone16,1_18.2_22C150_Restore.ipsw --json > ipsw-info.json
ipsw info iPhone16,1_18.2_22C150_Restore.ipsw --list > ipsw-file-list.txt
ipsw extract --sys-ver iPhone16,1_18.2_22C150_Restore.ipsw > system-version.txt
```

## Build Identity

Use build numbers, not marketing versions alone. The same visible OS version can
have different build trains, beta/release channel state, device support, and
payload layout.

Record these fields before analysis:

- `ProductType` such as `iPhone16,1`.
- Board/model identifiers when the target path is SoC- or board-specific.
- `ProductVersion`, `BuildVersion`, and release channel.
- Archive URL or local source path.
- SHA-256 of the IPSW/OTA and hashes of extracted targets.
- `BuildManifest.plist`, `Restore.plist`, and `SystemVersion.plist` outputs.
- Selected restore identity when `--ident` is used.
- Architecture such as `arm64e`, `arm64`, `x86_64`, or DriverKit.

`ipsw device-list` is useful for discovery, but its embedded database is sourced
from Xcode device traits and can include simulator variants. Confirm the actual
firmware supports the device with `ipsw info` and the archive's build manifest.

## IPSW, OTA, RSR, and Simulator Inputs

Prefer a full IPSW when:

- You need a reproducible filesystem baseline.
- Absence of a file or entitlement matters.
- You will run broad `ipsw diff` modes.
- You need restore ramdisks, iBoot, SEP, or full BuildManifest evidence.

Use OTA inputs when:

- The relevant fix shipped as an OTA or Rapid Security Response.
- Remote extraction can obtain a kernelcache or dyld cache without downloading a
  multi-GB archive.
- You have the AEA key material needed for encrypted OTA payloads.

Be explicit about OTA type:

- `--delta` for delta OTAs.
- `--rsr` for Rapid Security Response OTAs.
- `--sim` for simulator runtime OTAs.
- `--beta` for beta channels.
- `--platform ios|watchos|tvos|audioos|accessory|macos|recovery`.

For RSR OTAs, provide the target `--build`; the OTA guide calls out that the
build value is required. For iOS 16.x/macOS 13.x and newer OTA patch workflows,
check host support before planning bulk extraction because the official guide
notes private host APIs for applying some OTA patches.

Simulator runtime OTAs are not physical-device firmware. Do not use them to
prove device exploitability without a matching physical firmware artifact.

## Remote Extraction Versus Full Downloads

Remote extraction is excellent for first-pass RE:

```bash
ipsw extract --kernel --remote https://updates.cdn-apple.com/.../Restore.ipsw -o extracted/
ipsw extract --dyld --dyld-arch arm64e --remote https://updates.cdn-apple.com/.../Restore.ipsw -o extracted/
```

Use remote extraction when the question is "inspect this kernelcache/dyld cache
quickly." Use a full archive when the question is "compare whole firmware,"
"prove no other file changed," or "package complete evidence for handoff."

For repeatable research directories, store:

```text
firmware/
  original/
  extracted/
  metadata/
  hashes/
  notes/
```

Do not flatten download or extraction output unless paths are irrelevant.
Directory paths are evidence in filesystem, launchd, entitlement, sandbox, and
framework import investigations.

## Keys, SHSH, and Provenance

`ipsw download keys` downloads firmware keys from The iPhone Wiki. Treat those
keys as community-derived metadata, not Apple-published facts:

```bash
ipsw download keys --device iPhone14,2 --build 21A329 --json > keys.json
```

Record key source, retrieval date, and command line. Do not mix key-derived
facts into report text without naming the provenance.

Use TSS/SHSH only when restore/signing status matters:

```bash
ipsw download tss --device iPhone14,2 --version 17.0 --signed
ipsw download tss --device iPhone14,2 --version 17.0 --ecid 1234567890 --output blobs.shsh
```

SHSH signing status is operational reproduction context. It is not static proof
that a binary is vulnerable or fixed.

## Evidence Checklist

Capture:

- `ipsw version` and complete command lines.
- Firmware URL, local filename, and SHA-256.
- Device/product/board/model identity.
- Product version and build number.
- IPSW/OTA type: full restore, beta, delta OTA, RSR, simulator, recovery.
- `ipsw info --json`, `ipsw info --list`, and extracted `SystemVersion`.
- BuildManifest and restore identity if variant-specific components differ.
- Whether extraction was full local, full remote, or partial remote.
- Key, SHSH, and AEA sources when used.

## Official Source Paths

- https://blacktop.github.io/ipsw/docs/getting-started/installation/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/download/ipsw/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/download/ota/
- https://blacktop.github.io/ipsw/docs/guides/ota/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/device-info/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/device-list/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/info/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/download/keys/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/download/tss/
