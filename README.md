## MaxTAC
Maximize your verified OpenAI Trusted Access for Cyber (TAC) membership with a plugin that identifies and proves vulnerabilities in source code, binaries, and web services. Optional skills for Apple and Microsoft vulnerability research are also included.

This plugin is heavily inspired by [MDASH](https://www.microsoft.com/en-us/security/blog/2026/05/12/defense-at-ai-speed-microsofts-new-multi-model-agentic-security-system-tops-leading-industry-benchmark/).

## Skills
The `maxtac-core-*` skills should always be enabled for the plugin to work correctly.

- `maxtac-core-workflow`: Acts as an orchestrator for all research. Manages a set of research phases to work through, tracks those phases, and aides with continued research planning.
- `maxtac-core-preparation`: Prepares sessions and targets to perform recon and threat modeling, with a different approach depending on the type of target (source code, binary).
- `maxtac-core-finding-ledger`: Centralized finding management to help with research history tracking and deduplication. Each finding has a state and a link to its research notes.
- `maxtac-core-subagent-audit`: Auditor subagents, each specializing in a type of vulnerability recon and analysis, that may be spawned by the core workflow.
- `maxtac-core-subagent-debate`: Debator subagents, each assessing bug reachability and exploitability with the the same information, that may be spawned by the core workflow.

The `maxtac-asb-*` skills should only be enabled for macOS, iOS, and other Apple-related research.

- `maxtac-asb-program-info`: Information for the Apple Security Bounty (ASB) program, including eligible bounty categories, priorities, and general proof requirements.
- `maxtac-asb-target-flags`: Details for Apple target flags, which are vulnerability proof mechanisms built into every Apple OS.
- `maxtac-asb-sandboxing`: Security hardening features and common bypasses for eligible Apple sandboxes, including differences between macOS and iOS instances.

The `maxtac-msrc-*` skills should only be enabled for Windows, .NET, and other Microsoft-related research.

- `maxtac-msrc-program-info`: Information for the Microsoft Security Research Center (MSRC) program, including eligible bounty categories, priorities, and general proof requirements.
- `maxtac-msrc-sandboxing`: Requirements for eligible MSRC sandboxes, including how to use the LPAC tool.

## How to Install
Just ask Codex to install the plugin for you. With how fast Codex plugins are moving, any list of installation steps given may be invalid next week.
