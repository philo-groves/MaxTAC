# IPSW Diffing and ASB Triage

Use this reference when comparing patched and vulnerable Apple firmware builds,
Rapid Security Responses, OTAs, dyld caches, kernelcaches, launchd configs,
entitlements, sandbox profiles, feature flags, strings, or firmware payloads.

## Contents

- [Quick Commands](#quick-commands)
- [Build Pair Discipline](#build-pair-discipline)
- [Diff Modes](#diff-modes)
- [Cache and Output Discipline](#cache-and-output-discipline)
- [ASB Patch Archaeology Workflow](#asb-patch-archaeology-workflow)
- [Noise Controls](#noise-controls)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

Broad IPSW diff:

```bash
ipsw diff old.ipsw new.ipsw --fw --launchd --markdown --output diff-fw-launchd/
ipsw diff old.ipsw new.ipsw --files --ent --sandbox --feat --json --output diff-behavior/
ipsw diff old.ipsw new.ipsw --strs --starts --markdown --output diff-macho-leads/
```

OTA and RSR diffing:

```bash
ipsw diff old.ota new.ota --output diff-ota/ --markdown
ipsw diff old.ota new.ota --key-db keys.json --output diff-ota/ --markdown
ipsw diff old_rsr_dir new_rsr_dir --files --output diff-rsr-files/ --markdown
```

Section-scoped Mach-O diffing:

```bash
ipsw diff old.ipsw new.ipsw --allow-list __TEXT.__text --starts --strs -o diff-text/
ipsw diff old.ipsw new.ipsw --block-list __TEXT.__info_plist --json -o diff-no-plist/
```

Cache controls:

```bash
ipsw diff old.ipsw new.ipsw --clean --output diff-clean/
ipsw diff old.ipsw new.ipsw --no-cache --output diff-temp/
ipsw diff old.ipsw new.ipsw --cache-dir .cache/ipsw-diffs --cache-max-size 20GiB -o diff-cached/
```

## Build Pair Discipline

A useful firmware diff starts with a defensible pair:

1. Same product type unless the vulnerability is device-family-specific.
2. Same release channel unless beta-vs-release is the research question.
3. Adjacent builds when possible.
4. Matching OTA/IPSW class when comparing payload shape.
5. RSR base build and RSR payload both recorded.
6. KDKs only when relevant and matched to the correct macOS build.

Before diffing, save:

```bash
ipsw info old.ipsw --json > old-info.json
ipsw info new.ipsw --json > new-info.json
ipsw info old.ipsw --list > old-files.txt
ipsw info new.ipsw --list > new-files.txt
```

If the old and new builds target different restore identities or dyld
architectures, split the diff by identity or architecture before drawing
security conclusions.

## Diff Modes

High-signal modes for ASB work:

- `--files`: changed filesystem artifacts.
- `--fw`: non-main firmware such as iBoot, SEP, coprocessor, trust cache.
- `--ent`: Mach-O entitlement changes.
- `--launchd`: launch daemon and launch agent changes.
- `--sandbox`: compiled sandbox profile changes.
- `--feat`: feature flag changes.
- `--starts`: Mach-O function-start changes.
- `--strs`: cstring changes.
- `--loc`: localized strings.
- `--kdk`: macOS KDK kernel matching, when applicable.

Interpretation:

- Entitlement, launchd, sandbox, and feature flag changes are behavioral leads.
- Function-start and string diffs are triage hints, not patch proof.
- Firmware diffs often need family-specific parsing before RE.
- File diffs include signing, plist, asset, localization, and build metadata
  noise.

Use `--json` when another script or ledger will consume the diff. Use
`--markdown` or `--html` for analyst review artifacts.

## Cache and Output Discipline

`ipsw diff` uses a persistent SQLite cache by default. The official docs expose
cache controls:

- `--cache-dir`: override the default diff cache location.
- `--cache-max-size`: LRU eviction threshold.
- `--clean`: delete the cached DB for this IPSW pair before running.
- `--no-cache`: use a temporary database cleaned on exit.

For reportable work, either:

- use `--clean` and record the cache directory, or
- use `--no-cache` for a fully fresh run.

Store diff output under a build-pair name:

```text
diffs/
  iPhone16,1_18.1_22B83_to_18.2_22C150/
    old-info.json
    new-info.json
    ipsw-diff.json
    ipsw-diff.md
    extracted-old/
    extracted-new/
    re-notes/
```

## ASB Patch Archaeology Workflow

Use this sequence to turn firmware diffs into vulnerability leads:

1. Establish build pair and metadata.
2. Run broad behavior diffs: `--files --ent --launchd --sandbox --feat`.
3. Run binary lead diffs: `--starts --strs`, scoped with `--allow-list` if
   output is too large.
4. Extract changed dyld images, standalone Mach-Os, KEXTs, or firmware payloads
   from both builds.
5. Use `maxtac-re-ghidra` or `maxtac-re-radare2` for function-level patch diff.
6. Map changed functions back to attacker-controlled surfaces: app, XPC,
   launchd, sandbox, entitlement, kernel MIG/syscall/IOKit, WebKit, media,
   parser, or network path.
7. Record negative evidence: unchanged entitlements, unchanged launchd path,
   same sandbox profile, unreachable device family, or missing old/new payload.
8. Open a MaxTAC finding only after a plausible root-cause or exploitability
   hypothesis exists.

Do not report a CVE-root-cause claim from `ipsw diff` alone. It narrows the
patch; RE and reachability evidence prove the issue.

## Noise Controls

Use section allow/block lists for Mach-O heavy diffs:

```bash
ipsw diff old.ipsw new.ipsw --allow-list __TEXT.__text --allow-list __DATA_CONST.__const -o diff-code-data/
ipsw diff old.ipsw new.ipsw --block-list __TEXT.__info_plist --block-list __LINKEDIT -o diff-less-noise/
```

Other noise-reduction tactics:

- Compare adjacent builds before comparing far-apart versions.
- Split dyld, kernelcache, filesystem, and firmware payload work.
- Use entitlement and sandbox diffs to prioritize binaries with changed policy.
- Use cstring diffs to locate parser/protocol changes, then verify code.
- Treat localization, assets, build stamps, and signatures as low-priority
  unless they affect the target security boundary.

## Evidence Checklist

Capture:

- Old/new firmware URLs, filenames, hashes, product types, versions, builds.
- `ipsw info --json` and file lists for both.
- Complete `ipsw diff` command, output mode, output path, cache settings.
- AEA key database or KDK paths when used.
- Diff modes selected and why.
- Section allow/block lists.
- Extracted old/new artifacts used for RE.
- Function, string, entitlement, sandbox, launchd, or firmware changes that
  drove the hypothesis.
- Independent RE evidence validating changed behavior and reachability.

## Official Source Paths

- https://blacktop.github.io/ipsw/docs/cli/ipsw/diff/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/extract/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/ent/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/extract/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/extract/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/download/ota/
