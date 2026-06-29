## MaxTAC

<p align="center">
  <img src="assets/icon.png" alt="MaxTAC logo" width="150">
</p>

MaxTAC is split into focused Codex plugins for authorized vulnerability research. Install **MaxTAC Core** plus only the domain packs that match the current target.

Warning: Using MaxTAC workflows with non-TAC accounts may trigger OpenAI cyber policy limitations. Use these plugins only for authorized research inside applicable program scope.

## Plugin Packs

| Pack | Path | Use when |
| --- | --- | --- |
| MaxTAC Core | `plugins/maxtac-core` | You need the shared research workspace, ledgers, canonical result contracts, reporting flow, and goal-bounded auditor/debater orchestration. |
| MaxTAC for Source | `plugins/maxtac-source` | You need static triage, source diff/repo scan closure, external finding intake, control-flow evidence, or OpenGrep searches over source code or existing decompiler output. |
| MaxTAC for Binary | `plugins/maxtac-binary` | You need native binary RE, Ghidra, radare2, debugger evidence, crash replay, instrumentation, or systems fuzzing. |
| MaxTAC for Web | `plugins/maxtac-web` | You need web/API/session/tenant triage, browser debugging, or stateful API fuzzing. |
| MaxTAC for Supply Chains | `plugins/maxtac-supply-chains` | You need package compromise hunting, source-to-artifact diffing, CI/CD release takeover analysis, OSS proof gating, dependency, provenance, registry, container, or release-pipeline triage. |
| MaxTAC for Android | `plugins/maxtac-android` | You need APK/DEX/resource RE, Android component triage, ADB/logcat/JDWP/Frida runtime evidence, or Android-specific auditors. |
| MaxTAC for Apple Systems | `plugins/maxtac-apple-systems` | You need ASB Commpage/TCC proof packets, advanced IPSW patch-diff research, Apple mitigation-bypass workflows, or Apple-specific auditors. |
| MaxTAC for Microsoft Systems | `plugins/maxtac-microsoft-systems` | You need MSRC LPAC proofing, Windows mitigation reasoning, or Microsoft/Windows-specific auditors. |

Virtualization and general environment-management guidance is intentionally excluded from active packs.

## Recommended Combinations

- Source repository: Core + Source + the relevant domain pack.
- Web or SaaS target: Core + Web, optionally Source when code is available.
- Native/binary target: Core + Binary, optionally Source after decompiler output exists and needs static packet work.
- Supply-chain target: Core + Supply Chains, optionally Source or Web depending on the affected path.
- Android target: Core + Android, optionally Source when code is available or Binary when native libraries dominate the evidence path.
- Apple systems target: Core + Apple Systems, plus Binary or Source when the evidence path needs RE or code analysis.
- Microsoft systems target: Core + Microsoft Systems, plus Binary or Source when the evidence path needs RE or code analysis.

## Core Workspace

Core creates and manages the shared workspace contract:

```text
program-info.md    # authorized scope and exclusions
primitives.json    # individual findings
chains.json        # combined findings
reporting/         # submission-ready reports and evidence indexes
research/          # durable research library
debates/           # verifier debate results
audits/            # auditor results
proof/             # proof-of-vulnerability development
fuzz/              # fuzzing inputs, scripts, and artifacts
contracts/         # canonical result bundles and generated reports
tmp/               # temporary files
```

## Auditor Catalogs

Core keeps only a tiny fallback auditor catalog. Domain packs expose their own auditor catalogs through MCP tools:

- Web: `web_auditor_list`, `web_auditor_filter`, `web_auditor_show`
- Binary: `binary_auditor_list`, `binary_auditor_filter`, `binary_auditor_show`
- Supply Chains: `supply_chain_auditor_list`, `supply_chain_auditor_filter`, `supply_chain_auditor_show`
- Android: `android_auditor_list`, `android_auditor_filter`, `android_auditor_show`
- Apple: `apple_auditor_list`, `apple_auditor_filter`, `apple_auditor_show`
- Microsoft: `microsoft_auditor_list`, `microsoft_auditor_filter`, `microsoft_auditor_show`

Use the matching domain auditor tools before falling back to Core's generic auditor helper.

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
