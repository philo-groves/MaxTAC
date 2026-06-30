## MaxTAC

<p align="center">
  <img src="assets/icon.png" alt="MaxTAC logo" width="150">
</p>

MaxTAC is split into focused Codex plugins for authorized vulnerability research. Install **MaxTAC Core** plus only the domain packs that match the current target.

Warning: Using MaxTAC workflows with non-TAC accounts may trigger OpenAI cyber policy limitations. Use these plugins only for authorized research inside applicable program scope.

## Plugin Packs

| Pack | Path | Use when |
| --- | --- | --- |
| MaxTAC Core | `plugins/maxtac-core` | You need the shared research workspace, faceted research corpus, security models, invariant receipts, false-negative review, ledgers, canonical result contracts, thin/full closure profiles, reporting flow, and goal-bounded auditor/debater orchestration. |
| MaxTAC for Source | `plugins/maxtac-source` | You need static triage, optional codebase-memory graph orientation, source diff/repo scan closure, thin exact-path closure, negative-evidence inputs, external finding intake, control-flow evidence, or OpenGrep searches over source code or existing decompiler output. |
| MaxTAC for Binary | `plugins/maxtac-binary` | You need native binary RE, Ghidra, radare2, debugger evidence, crash replay, instrumentation, or systems fuzzing. |
| MaxTAC for Web | `plugins/maxtac-web` | You need web/API/session/tenant triage, browser debugging, or stateful API fuzzing. |
| MaxTAC for Cloud | `plugins/maxtac-cloud` | You need AWS, Azure, or GCP IAM, storage, data-plane, runtime metadata, workload identity, managed Kubernetes, or cloud network boundary research. |
| MaxTAC for Supply Chains | `plugins/maxtac-supply-chains` | You need package compromise hunting, source-to-artifact diffing, CI/CD release takeover analysis, OSS proof gating, dependency, provenance, registry, container, or release-pipeline triage. |
| MaxTAC for Android | `plugins/maxtac-android` | You need APK/DEX/resource RE, Android component triage, ADB/logcat/JDWP/Frida runtime evidence, or Android-specific auditors. |
| MaxTAC for Apple Systems | `plugins/maxtac-apple-systems` | You need ASB Commpage/TCC proof packets, advanced IPSW patch-diff research, Apple mitigation-bypass workflows, or Apple-specific auditors. |
| MaxTAC for Microsoft Systems | `plugins/maxtac-microsoft-systems` | You need MSRC LPAC proofing, Windows mitigation reasoning, or Microsoft/Windows-specific auditors. |

Virtualization and general environment-management guidance is intentionally excluded from active packs.

## Recommended Combinations

- Source repository: Core + Source + the relevant domain pack.
- Web or SaaS target: Core + Web, optionally Source when code is available.
- Cloud target: Core + Cloud, optionally Web, Source, or Supply Chains depending on the entrypoint.
- Native/binary target: Core + Binary, optionally Source after decompiler output exists and needs static packet work.
- Supply-chain target: Core + Supply Chains, optionally Source, Web, or Cloud depending on the affected path.
- Android target: Core + Android, optionally Source when code is available or Binary when native libraries dominate the evidence path.
- Apple systems target: Core + Apple Systems, plus Binary or Source when the evidence path needs RE or code analysis.
- Microsoft systems target: Core + Microsoft Systems, plus Binary or Source when the evidence path needs RE or code analysis.

## Core Workspace

Core creates and manages the shared workspace contract:

```text
program-info.md    # authorized scope and exclusions
workspace.sqlite   # findings, corpus notes, model assertions, debate tallies, audit index, and workspace search memory
reporting/         # submission-ready reports and evidence indexes
research/          # faceted research corpus
  notes/           # canonical compact research notes
  views/           # generated corpus indexes and graph views
  artifacts/       # raw corpus artifacts and imported legacy markdown
models/            # machine-readable security models and invariant dictionaries
proof/             # proof-of-vulnerability development
fuzz/              # fuzzing inputs, scripts, and artifacts
contracts/         # canonical result bundles, false-negative reviews, and generated reports
tmp/               # temporary files
```

## Auditor Registry

Core owns a global SQLite auditor registry at `$CODEX_HOME/maxtac/auditors.sqlite`. Domain packs publish `references/auditors.json`; Core's `SessionStart` hook rebuilds the registry from the active plugin set so agents have one source of truth with duplicate prevention and FTS search.

Use Core's helper for every auditor lookup:

```text
python3 plugins/maxtac-core/skills/maxtac-core-subagents/scripts/audit-helper.py --catalogs
python3 plugins/maxtac-core/skills/maxtac-core-subagents/scripts/audit-helper.py --catalog apple --filter tcc
python3 plugins/maxtac-core/skills/maxtac-core-subagents/scripts/audit-helper.py --catalog apple --show apple-tcc-bypass
```

If plugins changed during a running session, refresh the registry manually:

```text
python3 plugins/maxtac-core/skills/maxtac-core-subagents/scripts/auditor_registry.py rebuild
```

## Install

Install the plugin roots you need from `plugins/`. For example, for web research install:

```text
plugins/maxtac-core
plugins/maxtac-source
plugins/maxtac-web
```

See [TOOLING.md](TOOLING.md) for the external tools each pack may route to.

## License

MIT
