## MaxTAC
Maximize your verified OpenAI Trusted Access for Cyber (TAC) membership with a plugin that identifies and proves vulnerabilities in source code, binaries, and web services. Optional skills for Apple and Microsoft vulnerability research are also included.

This plugin is heavily inspired by [MDASH](https://www.microsoft.com/en-us/security/blog/2026/05/12/defense-at-ai-speed-microsofts-new-multi-model-agentic-security-system-tops-leading-industry-benchmark/).

## Architecture
![MaxTAC Architecture Diagram](https://i.imgur.com/6RnsUeO.png)

### Core Workflow

See the `maxtac-core-workflow` skill for related documentation.

### Problems & Solutions
This plugin was created to resolve several issues that exist for general AI-based security research.

- **No Directory Structure**: By default, models will persist all files to the base directory of the workspace, turning a knowledge base into a scrambled mess. The solution is a directory hierarchy that transforms and grows with the research program.
- **Unverified Findings**: By default, models will consider bug candidates to be confirmed before verification. The solution is a debate mechanism with several isolated voters to prevent self-bias.
- **Finding Confusion**: Even with a perfect research library, findings may become sparse, duplicated, and hard to find. The solution is a core ledger skill with a file-based tracker.
- **Primitive Loss**: By default, models often de-escalate findings if not relevant to the chain-at-hand, invalidating future work with the primitive. The solution is separate tracking for primitives and chains.
- **Minimal Tool Knowledge**: By default, models will only have knowledge of tools within their training data. Advanced, uncommon, and newer features are limited. The solution is guidance for advanced tools (e.g. radare2, opengrep).

## Skills
The `maxtac-core-*`, `maxtac-sast-*`, `maxtac-dast-*`, and `maxtac-re-*` skills should be enabled for general MaxTAC research. The Apple `maxtac-asb-*` and Microsoft `maxtac-msrc-*` skills are optional domain packs for platform-specific programs.

### Core Workflow

- `maxtac-core-workflow`: Starts, organizes, and continues authorized vulnerability research sessions with standard directories, phases, subsystem notes, validation, proof, and reporting flow.
- `maxtac-core-subagents`: Runs goal-bounded auditor and verifier-debate subagents for specialist review, mitigation review, and independent votes on vulnerability hypotheses.
- `maxtac-core-ledger`: Tracks findings, deduplicates candidates, records state transitions, links evidence, and manages promotion, de-escalation, proof, and report status.

### Static Analysis

- `maxtac-sast-surface-triage`: Maps source-code and decompiled-code trust boundaries, danger areas, invariants, and auditor routing hints before targeted scans.
- `maxtac-sast-control-flow-graph`: Builds focused static control-flow and call-graph evidence for reachability, guard dominance, path feasibility, callbacks, cleanup paths, lock order, state transitions, and source-to-sink paths.
- `maxtac-sast-opengrep`: Guides OpenGrep rule authoring, taint and pattern matching, result interpretation, and packaging evidence for MaxTAC analysis.

### Dynamic Analysis

- `maxtac-dast-debugger`: Supports debugger, instrumentation, device, browser, and runtime tooling, including LLDB, GDB, x64dbg, WinDbg, Frida, ADB, xcrun, CDP, WebDriver BiDi, and WebKit debugging.
- `maxtac-dast-fuzzer`: Plans fuzzing for parsers, binaries, kernels, protocols, APIs, web apps, browsers, mobile apps, managed runtimes, coverage-guided engines, grammar fuzzers, and harness selection.
- `maxtac-dast-virtualization`: Sets up controlled dynamic testing and exploit-validation environments with snapshots, isolation, guest networking, hypervisors, containers, and repeatable lab workflows.

### Reverse Engineering

- `maxtac-re-ghidra`: Uses Ghidra for headless analysis, decompilation, p-code inspection, scripting, binary search, data type recovery, version tracking, BSim similarity, debugging, and emulation.
- `maxtac-re-jadx`: Uses JADX for Android APK, DEX, JAR, AAR, AAB, smali, resource decoding, deobfuscation, mappings, GUI search, smali debugging, API automation, and plugin workflows.
- `maxtac-re-radare2`: Uses radare2 for binary triage, analysis, expression and string search, binary diffing, debugging, ESIL emulation, hex utilities, and automation.

### Apple Security Bounty (ASB)

- `maxtac-asb-flag-proof`: Proves Apple Security Bounty target flags for register control, arbitrary read/write, arbitrary code execution, and TCC modification across Apple platforms.
- `maxtac-asb-ipsw`: Handles Apple firmware reverse engineering with `ipsw`, including IPSW/OTA download, extraction, kernelcache, dyld shared cache, DeviceTree, DMG, IMG4, iBoot, SEP, coprocessor, trust cache, filesystem, mount, diff, and ASB evidence workflows.
- `maxtac-asb-mitigations`: Reasons about Apple software and hardware mitigations, bypass constraints, unexpected runtime behavior, and workaround paths.

### Microsoft Security Response Center (MSRC)

- `maxtac-msrc-lpac-proof`: Proves Windows Insider Preview local sandbox attack scenarios for MSRC submissions, especially LPAC sandbox escapes and private data access using Microsoft SandboxSecurityTools.
- `maxtac-msrc-mitigations`: Reasons about Microsoft platform mitigations, bypass constraints, unexpected runtime behavior, and workaround paths.

## MCP Tools
MaxTAC includes a small Python MCP server declared in `.mcp.json`. When enabled in Codex, it exposes deterministic tools for workspace setup and status, phase management, research submodules, ledger operations, auditor/debater prompt persistence, debate tallying, SAST packet validation, and evidence packing. It also wraps the existing debugger, fuzzing, LPAC, IPSW, Ghidra, JADX, radare2, and RE-readiness helper scripts so agents can call the same evidence collectors through MCP while preserving their JSON and markdown artifacts.

## How to Install
Just ask Codex to install the plugin for you. With how fast Codex plugins are moving, any list of installation steps given may be invalid next week.

## License

MIT
