---
name: maxtac-apple-workspace
description: Lay out and maintain MaxTAC Apple research workspaces. Use when creating Apple domain directories, target-specific markdown notes, domain-indexed research artifacts, or ledger links for apple-intelligence, boot-chain, comms, icloud, kernel, private-cloud-compute, radios, sandbox, and webkit research.
---

# MaxTAC Apple Workspace

Use this skill before or during Apple campaigns so research does not pile into the finding ledger. The ledger tracks compact finding state; domain target directories persist detailed markdown, crash interpretation, diagrams, tables, and mechanism notes.

## Directory Layout

Default root:

```text
data/maxtac/research/
  apple-intelligence/
  boot-chain/
  comms/
  icloud/
  kernel/
  private-cloud-compute/
  radios/
  sandbox/
  webkit/
```

Under each domain, create any number of target directories:

```text
data/maxtac/research/kernel/ioexample/
  notes.md
  aslr-leaks.md
  pac-matrix.md
  target-flag-note.md
```

Use lowercase kebab-case target directory names unless the target has a stable existing identifier.

## Domain Use

- `apple-intelligence`: on-device model surfaces, local AI services, prompt/data boundaries, and private inference handoff points.
- `boot-chain`: SecureROM, iBoot, boot policy, restore/update paths, trust cache, and early-boot artifacts.
- `comms`: Messages, FaceTime, Push, IDS, APNs, parsers, and communication daemons.
- `icloud`: account, sync, CloudKit, escrow, keychain sync, and server/client trust boundaries.
- `kernel`: XNU, IOKit, kernel extensions, kernelcache, MIG, VFS, and memory-safety primitives.
- `private-cloud-compute`: PCC client/server boundary notes, attestation, privacy guarantees, and request/response surfaces.
- `radios`: baseband-adjacent, Wi-Fi, Bluetooth, NFC, UWB, and radio daemon research notes.
- `sandbox`: sandbox profiles, TCC adjacency, app groups, helpers, extensions, and container boundaries.
- `webkit`: WebKit, JavaScriptCore, media parsers reached by web content, and browser process boundaries.

## Workflow

1. Initialize domain directories with `scripts/init_apple_workspace.py`.
2. For each target, create a target directory and `notes.md`.
3. Keep detailed mechanism notes in markdown files inside that target directory.
4. Add compact ledger findings with `--domain <domain>` and reference markdown paths in `--evidence`, `--related`, or milestone notes.
5. Before starting a new research area, search the ledger by `--domain` and run `rg` in the matching domain directory to avoid duplicated work.

## Helper Script

```bash
python <skill-dir>/scripts/init_apple_workspace.py --root data/maxtac/research
python <skill-dir>/scripts/init_apple_workspace.py --domain kernel --target IOExample --root data/maxtac/research
```

## Handoff

Return:

```text
Apple workspace:
Domain:
Target directory:
Markdown notes created or updated:
Ledger domain filter:
Next research skill:
```
