# IPSW IMG4, AEA, and Firmware Payloads

Use this reference when working with Image4 containers, encrypted payloads,
restore ramdisks, iBoot, SEP, SPTM/TXM, Exclave, coprocessor firmware, AEA DMGs,
or trust caches from an IPSW/OTA.

## Contents

- [Quick Commands](#quick-commands)
- [IMG4 Component Model](#img4-component-model)
- [Wrapped Ramdisks and DMGs](#wrapped-ramdisks-and-dmgs)
- [Keys, KBAGs, and AEA](#keys-kbags-and-aea)
- [Firmware Families](#firmware-families)
- [Trust Caches](#trust-caches)
- [Handoff to RE Tools](#handoff-to-re-tools)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

Inspect and split IMG4:

```bash
ipsw img4 info kernel.img4
ipsw img4 info kernel.img4 --json > kernel-img4.json
ipsw img4 extract --im4p --im4m --im4r --output img4-parts/ kernel.img4
ipsw img4 extract --im4p --raw --output img4-raw/ kernel.img4
ipsw img4 kbag kernel.img4 --json > kernel-kbag.json
```

Decrypt when IV/key material is available:

```bash
ipsw img4 dec payload.img4 --iv "<IV>" --key "<KEY>" --output dec/
ipsw img4 dec payload.img4 --iv-key "<IV><KEY>" --output dec/
```

Extract firmware payloads from an IPSW:

```bash
ipsw extract --iboot --sep --sptm --exclave -o firmware-payloads/ firmware.ipsw
ipsw extract --dmg rdisk --ident Erase -o ramdisks/ firmware.ipsw
ipsw extract --kbag -o kbags/ firmware.ipsw
```

Handle AEA1 DMGs:

```bash
ipsw fw aea --info encrypted.dmg.aea
ipsw fw aea --fcs-key encrypted.dmg.aea > fcs-key.json
ipsw fw aea --key --pem private_key.pem encrypted.dmg.aea
ipsw fw aea --pem-db aea-pems.json --output extracted-aea/ encrypted.dmg.aea
```

## IMG4 Component Model

Use `ipsw img4` when file extensions lie. Many Apple firmware entries use a
familiar extension such as `.dmg` while actually wrapping an Image4 payload.

Core pieces:

- `IMG4`: container.
- `IM4P`: payload. It may be compressed, raw, encrypted, or both.
- `IM4M`: manifest.
- `IM4R`: restore info.
- `KBAG`: keybag metadata for encrypted IM4P payloads.

`ipsw img4 extract --raw` keeps the raw compressed IM4P data. Omit `--raw` when
you want the normal extracted payload. Preserve both when decompression or
payload identity is disputed.

Use `ipsw img4 info --json` before trying decryption. Record payload type,
compression, manifest presence, KBAG state, and component hashes.

## Wrapped Ramdisks and DMGs

Restore ramdisk entries can look like DMGs in `ipsw info`, but fail to mount
because they are IMG4/IM4P wrappers. Workflow:

```bash
unzip -p firmware.ipsw 098-25526-064.dmg > ramdisk.img4
ipsw img4 info ramdisk.img4 --json > ramdisk-img4.json
ipsw img4 extract --im4p --output ramdisk-parts/ ramdisk.img4
```

If the extracted IM4P payload is a DMG, mount or inspect the payload after
hashing it and preserving the IMG4 metadata. Keep the original archive entry,
the IMG4 metadata JSON, and the extracted payload together.

Use `ipsw mount rdisk firmware.ipsw --ident Erase|Upgrade|Recovery` when the
host and installed `ipsw` build can handle the wrapping and mount path directly.

## Keys, KBAGs, and AEA

Key material can come from:

- `ipsw img4 kbag` or `ipsw extract --kbag` for keybag metadata.
- `ipsw download keys` for community firmware keys from The iPhone Wiki.
- `ipsw download ota --fcs-keys` for AEA key databases from OTA metadata.
- Private PEM databases supplied by the research environment.

Rules:

- Keep key provenance with the decrypted artifact.
- Do not treat The iPhone Wiki keys as Apple-published source of truth.
- Do not upload private PEM material into unrelated services.
- Store decrypted payload hashes separately from encrypted original hashes.

AEA1 DMGs appear in newer firmware workflows. Commands that consume AEA material
usually accept `--pem-db`, `--pem`, `--key-val`, `--fcs-key`, or related flags.
Record which path was used because it affects reproducibility.

The official AEA guide describes the lookup order for PEM material as embedded
keys, then a provided `--pem-db`, then Apple's public key service. For offline or
air-gapped work, build and preserve the JSON PEM database up front.

## Firmware Families

`ipsw fw` exposes firmware-family helpers. The available subcommands change over
time; run `ipsw fw --help` and the subcommand's `--help` before relying on a
saved command.

Families currently exposed by the CLI docs include:

- `aea`: AEA1 DMGs.
- `aop`, `cam`, `dcp`, `gpu`, `exclave`: coprocessor or subsystem Mach-O dumps.
- `iboot`: iBoot files.
- `ibootim`: iBoot images.
- `sepfw`: SEP firmware when available in the installed command surface.
- `tc`: trust cache.
- `c1`: C1 baseband firmware.

Use high-level `ipsw extract` first when available (`--iboot`, `--sep`,
`--sptm`, `--exclave`). Use `ipsw fw` when a family-specific parser provides
better structure than raw extraction.

## Trust Caches

Trust cache output is code-signing scope evidence. Use it to answer "which code
hashes are trusted by this build or payload," not "which path is reachable."

Keep:

- Trust cache source file and hash.
- Firmware build identity.
- Any parser output from `ipsw fw tc`.
- Mapping from cdhashes to extracted Mach-O files, if you build one.

Do not infer vulnerability reachability from trust-cache presence. Pair trust
cache data with filesystem paths, launchd/sandbox/entitlement evidence, and
runtime or static call paths.

## Handoff to RE Tools

For extracted firmware:

- Use `file`, `otool`, `ipsw macho info`, or `rabin2 -I` to confirm format.
- Use `maxtac-re-ghidra` for Mach-O, raw ARM firmware, or structured program
  databases.
- Use `maxtac-re-radare2` for quick strings, sections, disassembly, and
  scripted triage.
- For non-Mach-O coprocessor blobs, document architecture, base address, load
  assumptions, and whether code/data split is known.

Never discard container metadata after extracting a payload. IMG4 manifest,
payload type, compression, and key provenance often explain why two visually
similar outputs differ.

## Evidence Checklist

Capture:

- Original IPSW/OTA path and archive entry path.
- IMG4/IM4P/IM4M/IM4R metadata JSON.
- Raw and decompressed/decrypted payload hashes.
- KBAG output and key provenance.
- AEA PEM/key database path, command, and retrieval source.
- Firmware family parser used and `ipsw fw --help`-validated subcommand.
- Restore identity for ramdisks.
- RE import assumptions for raw or non-Mach-O payloads.

## Official Source Paths

- https://blacktop.github.io/ipsw/docs/guides/img4/
- https://blacktop.github.io/ipsw/docs/guides/aea/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/img4/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/img4/info/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/img4/extract/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/img4/dec/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/img4/kbag/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/fw/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/fw/aea/
- https://github.com/tihmstar/img4tool
