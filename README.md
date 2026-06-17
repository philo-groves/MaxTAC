## MaxTAC
<p align="center">
  <img src="assets/icon.png" alt="MaxTAC logo" width="150">
</p>

<p align="center">
  <a href=".codex-plugin/plugin.json">Manifest</a> ·
  <a href="#skills">Skills</a> ·
  <a href="TOOLING.md">Tooling</a>
</p>

Maximize your verified OpenAI Trusted Access for Cyber (TAC) membership with a plugin that identifies and proves vulnerabilities in source code, binaries, and web services. Optional skills for Apple and Microsoft vulnerability research are also included.

Warning: Using this plugin with non-TAC accounts will likely trigger OpenAI cyber policy violations. Violations may sometimes occur for TAC-verified users, but none were experienced during plugin testing. Not a TAC member? Sign up here: https://chatgpt.com/cyber

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
This plugin was created to resolve several issues that exist for general AI-based security research, ordered roughly by impact on long-running vulnerability discovery and proof.

- **Behavioral Lock**: By default, long contexts amplify the current pattern, whether that is spinning inside one branch or jumping across surfaces without depth. The solution is an attention cadence based on phase history, ledger timestamps, and recent workspace file mtimes; `workspace_status` warns when the agent must explicitly deepen, pivot, consolidate, phase-shift, or delegate-review.
- **Finding Overhype**: By default, models will consider bug candidates to be confirmed before verification. The solution is a debate mechanism with several isolated voters to prevent self-bias.
- **Incomplete Subagents**: By default, spawned subagents are not guaranteed to complete a specific task. The solution is to use Codex-native goals with positive and negative gates for each subagent.
- **Heavy Subagents**: By default, each subagent consumes several GB of RAM, which can quickly cause resource collapse. The solution is a script that budgets 4 GiB per subagent, measures available resources, and forces auditor subagents to run sequentially on systems below 17 GiB total RAM.
- **Primitive Loss**: By default, models often de-escalate findings if not relevant to the chain-at-hand, invalidating future work with the primitive. The solution is separate tracking for primitives and chains.
- **Finding Confusion**: Even with a perfect research library, findings may become sparse, duplicated, and hard to find. The solution is a core ledger skill with a file-based findings tracker.
- **Unstructured Phases**: By default, models have trouble managing and remembering their own research state. The solution is a set of tools for managing this state with a file-based workflow tracker.
- **Tunnel-Vision Submodules**: By default, models keep extending the first active folder until it becomes a second messy workspace root. The solution is stable subsystem hierarchy: create or reuse focused submodules as the research target moves across components, and keep session, date, build, tool, and hypothesis names in artifact case directories.
- **No Directory Structure**: By default, models will persist all files to the base directory of the workspace, turning a knowledge base into a scrambled mess. The solution is a directory hierarchy that transforms and grows with the research program.
- **Artifact Creep**: By default, models will hide synthesized markdown inside artifact folders because it was created during a tool run. The solution is a strict split: `research/` markdown is a durable, book-like system model; `artifacts/` contains raw evidence, generated outputs, manifests, transcripts, hashes, binaries, and proof material.
- **Few Bug Classes**: By default, models prefer a set of popular bug classes and not less frequent bug classes when necessary. The solution is a collection of 80+ prompt templates for specialist auditor subagents.
- **Debugger Neglect**: By default, models will prefer static analysis and fuzzing for vulnerability research. These are strong, but debuggers are often ignored. The solution is guidance for debuggers on every major platform, plus web.
- **Minimal Tool Knowledge**: By default, models will only have knowledge of tools within their training data. Advanced, uncommon, and newer features are limited. The solution is guidance for advanced tools (e.g. radare2, opengrep, AFL++).

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
MaxTAC includes a small Python MCP server declared in `.mcp.json`. When enabled in Codex, it exposes deterministic tools grouped around the same workflow used by the skills:

- **Workspace flow**: `workspace_init`, `workspace_status`, `workspace_phase`, `workspace_new_submodule`, `workspace_split_large_markdown`, and `workspace_report_ready` create the canonical workspace, inspect health, manage phase history, maintain research submodules, split oversized book-like notes, and check report readiness. `workspace_status` also reports research hygiene and attention-lock warnings.
- **Finding ledgers**: `ledger_init`, `ledger_search`, `ledger_add`, `ledger_update`, `ledger_summary`, `ledger_list`, and `ledger_milestone` manage primitive and chain ledgers, including duplicate checks, state transitions, active finding summaries, and timestamped branch decisions.
- **Subagent orchestration**: `subagent_readiness`, `audit_prompt_create`, `debate_prompt_create`, and `debate_tally` decide parallel vs sequential spawning, persist goal-bounded auditor/debater prompts, validate debate ballots, and write debate summaries.
- **SAST and evidence packets**: `packet_validate` validates MaxTAC surface, CFG, and OpenGrep packets. `evidence_pack` creates proof bundles with copied artifacts, SHA-256 hashes, command lines, tool versions, export settings, and related finding links.
- **Dynamic testing wrappers**: `debug_evidence` records debugger/runtime captures, while `fuzz_campaign` records fuzz campaign setup, runs, crashes, reproducers, and campaign summaries.
- **Platform proof helpers**: `ipsw_provenance` records ASB firmware provenance, extraction commands, and related artifacts. `lpac_proof` records MSRC LPAC sandbox proof evidence.
- **Reverse engineering exports**: `re_readiness_check`, `ghidra_export`, `jadx_export`, and `r2_triage` check RE tool readiness and produce repeatable Ghidra, JADX, and radare2 evidence manifests.

## How to Install
Just ask Codex to install the plugin for you.

> Please clone https://github.com/philo-groves/MaxTAC and integrate it as a Codex plugin.

## License

MIT
