## MaxTAC
Maximize your verified OpenAI Trusted Access for Cyber (TAC) membership with a plugin that identifies and proves vulnerabilities in source code, binaries, and web services. Optional skills for Apple and Microsoft vulnerability research are also included.

This plugin is heavily inspired by [MDASH](https://www.microsoft.com/en-us/security/blog/2026/05/12/defense-at-ai-speed-microsofts-new-multi-model-agentic-security-system-tops-leading-industry-benchmark/).

## Problems & Solutions
This plugin was created to resolve several issues that exist for general AI-based security research.

- **No Directory Structure**: By default, models will persist all files to the base directory of the workspace, turning a knowledge base into a scrambled mess. The solution is a directory hierarchy that transforms and grows with the research program.
- **Minimal Tool Knowledge**: By default, models will only have knowledge of tools within their training data. Advanced, uncommon, and newer features are limited. The solution is guidance for advanced tools (e.g. radare2, opengrep).
- **Unverified Findings**: By default, models will consider bug candidates to be confirmed before verification. The solution is a debate mechanism with several isolated voters to prevent self-bias, plus a stateful finding ledger.

## Skills
The `maxtac-core-*`, `maxtac-sast-*`, `maxtac-dast-*`, and `maxtac-re-*` skills must always be enabled for the plugin to work correctly.

The `maxtac-core-*` skills work together to create healthy research sessions(s) and a scalable knowledge base.

- `maxtac-core-workflow`: Acts as an orchestrator for all research. Manages a set of research phases to work through, tracks those phases, and aides with continued research planning.
- `maxtac-core-subagents`: Subagent flows for security auditing and verifier debate, including how to spawn subagents of each type and prompt templates to use.
- `maxtac-core-ledger`: Centralized finding management to help with research history tracking and deduplication. Each finding has a state and a link to its research notes.

The `maxtac-sast-*` skills are used to perform Static Application Security Testing (SAST).

- `maxtac-sast-control-flow-graph`: 
- `maxtac-sast-logic-analysis`: 
- `maxtac-sast-opengrep`: Provides instructions and references for writing and using OpenGrep rules.

The `maxtac-dast-*` skills are used to perform Dynamic Application Security Testing (DAST).

- `maxtac-dast-debugger`: 
- `maxtac-dast-fuzzer`: 
- `maxtac-dast-virtualization`: 

The `maxtac-re-*` skills are used to perform reverse engineering (RE).

- `maxtac-re-ghidra`: 
- `maxtac-re-jadx`: 
- `maxtac-re-radare2`: 

The `maxtac-asb-*` skills should only be enabled for macOS, iOS, and other Apple-related research.

- `maxtac-asb-flag-proof`: Details for Apple target flags, which are vulnerability proof mechanisms built into every Apple OS.
- `maxtac-asb-mitigations`: 
- `maxtac-asb-workflow`: 

The `maxtac-msrc-*` skills should only be enabled for Windows, .NET, and other Microsoft-related research.

- `maxtac-msrc-lpac-proof`: 
- `maxtac-msrc-mitigations`: 
- `maxtac-msrc-workflow`: 

## How to Install
Just ask Codex to install the plugin for you. With how fast Codex plugins are moving, any list of installation steps given may be invalid next week.
