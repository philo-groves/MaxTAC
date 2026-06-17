## MaxTAC
Maximize your verified OpenAI Trusted Access for Cyber (TAC) membership with a plugin that identifies and proves vulnerabilities in source code, binaries, and web services. Optional skills for Apple and Microsoft vulnerability research are also included.

This plugin is heavily inspired by [MDASH](https://www.microsoft.com/en-us/security/blog/2026/05/12/defense-at-ai-speed-microsofts-new-multi-model-agentic-security-system-tops-leading-industry-benchmark/).

## System Requirements

- `python` must be on your path for MaxTAC tools to work correctly.
- External research tools are target-specific, not all mandatory. See [TOOLING.md](TOOLING.md) for the primary tools MaxTAC routes to across SAST, DAST, reverse engineering, Apple firmware, and MSRC proof workflows.

## Architecture
![MaxTAC Architecture Diagram](https://i.imgur.com/6RnsUeO.png)

### Workflow Phases
Codex will work through these phases in any order.

1. **Prepare**: Perform recon and threat modeling on the target.
2. **Scan**: Spawn auditor subagents to search for vulnerabilities.
3. **Validation**: Confirm logical validity and de-duplicate findings.
4. **Primitive Proof**: Prove an individual primitive in isolation.
5. **Chain Proof**: Realistically end-to-end prove a chain of primitives.
6. **Reporting**: Write a report for a proven chain.

### Workspace Structure
Codex will create and manage the following relative files and directories.

```
program-info.md    # authorized scope and exclusions
primitives.json    # individual findings (primitives) of all states
chains.json        # combined findings (chains) of all states
reporting/         # submission-ready reports and evidence indexes
research/          # scalable markdown research library
debates/           # debater subagent results
audits/            # auditor subagent results
proof/             # proof-of-vulnerability (PoV) development
fuzz/              # fuzzing inputs, scripts, and artifacts
tmp/               # temporary files that can be deleted between sessions
```

### Problems & Solutions
This plugin was created to resolve several issues that exist for general AI-based security research.

- **No Directory Structure**: By default, models will persist all files to the base directory of the workspace, turning a knowledge base into a scrambled mess. The solution is a directory hierarchy that transforms and grows with the research program.
- **Artifact Creep**: By default, models will hide synthesized markdown inside artifact folders because it was created during a tool run. The solution is a strict split: `research/` markdown is a durable, book-like system model; `artifacts/` contains raw evidence, generated outputs, manifests, transcripts, hashes, binaries, and proof material.
- **Tunnel-Vision Submodules**: By default, models keep extending the first active folder until it becomes a second messy workspace root. The solution is stable subsystem hierarchy: create or reuse focused submodules as the research target moves across components, and keep session, date, build, tool, and hypothesis names in artifact case directories.
- **Incomplete Subagents**: By default, spawned subagents are not guaranteed to complete a specific task. The solution is to use Codex-native goals with positive and negative gates for each subagent.
- **Heavy Subagents**: By default, each subagent consumes several GB of RAM, which can quickly cause resource collapse. The solution is a script that measures available resources, then helps decide between serial vs parallel spawn behavior.
- **Few Bug Classes**: By default, models prefer a set of popular bug classes and not less frequent bug classes when necessary. The solution is a collection of 80+ prompt templates for specialist auditor subagents.
- **Unstructured Phases**: By default, models have trouble managing and remembering their own research state. The solution is a set of tools for managing this state with a file-based workflow tracker.
- **Finding Overhype**: By default, models will consider bug candidates to be confirmed before verification. The solution is a debate mechanism with several isolated voters to prevent self-bias.
- **Finding Confusion**: Even with a perfect research library, findings may become sparse, duplicated, and hard to find. The solution is a core ledger skill with a file-based findings tracker.
- **Primitive Loss**: By default, models often de-escalate findings if not relevant to the chain-at-hand, invalidating future work with the primitive. The solution is separate tracking for primitives and chains.
- **Minimal Tool Knowledge**: By default, models will only have knowledge of tools within their training data. Advanced, uncommon, and newer features are limited. The solution is guidance for advanced tools (e.g. radare2, opengrep, AFL++).
- **Debugger Neglect**: By default, models will prefer static analysis and fuzzing for vulnerability research. These are strong, but debuggers are often ignored. The solution is guidance for debuggers on every major platform, plus web.

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
