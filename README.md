# MaxTAC

Maximize your Trusted Access for Cyber status with a multi-agent cyber plugin purpose-built for authorized vulnerability research and proofing. The initial implementation focuses on XNU, Windows kernel-adjacent artifacts, native binaries, and open-source systems code.

## What Is Included

- `maxtac-orchestrator`: Coordinates the Prepare, Discovery, Triage, Proof, and Report phases.
- `maxtac-engagement-scope`: Establishes authorization, lab boundaries, impact tolerance, and artifact handling.
- `maxtac-prepare`: Builds `data/maxtac/target-profile.json`.
- `maxtac-auditor-router`: Selects systems Auditor packets from `references/auditor-catalog.yaml`.
- `maxtac-finding-ledger`: Tracks discovered, triage-ready, confident, proofed, duplicate, and de-escalated findings.
- `maxtac-triage-debate`: Runs independent Debater evaluation for reachability and exploitability.
- `maxtac-proof-lab`: Creates lab proof packets for confident findings.
- `maxtac-chain-analysis`: Composes findings through explicit preconditions and postconditions.
- `maxtac-report-writer`: Writes reports from proofed evidence.

## Quick Start

Ask Codex to use MaxTAC against an authorized local target:

```text
Use MaxTAC to prepare this XNU target and select the first Auditor wave.
```

The expected campaign state lives under:

```text
data/maxtac/
  target-profile.json
  findings.json
  auditor-packets/
  debates/
  proof/
  reports/
```

## Subagents

- Auditor: Specializes in a specific type of kernel, binary, or open-source systems audit.
- Debater: Works together to determine the reachability and exploitability and each finding.
- Prover: Acts as its own subagent to prevent context pollution and self-bias.

## Phases

Codex continues through the following phases.

### Prepare

In the Prepare phase, Codex lays a foundation to build a knowledge base of the target attack surface and threat models. The approach of recon conducted depends on the type of target.

#### Source Code Recon

Ingest the source target to ~/maxtac-resources/. Build language-aware indices. Analyze past commits and CVE history. Identify code comments, environment assumptions, and undefined behavior. Build a repository map and primary call graphs. Scout existing threat mitigations in the source code.

#### Binary Recon

Add or install the binary locally. Avoid placing binaries in the working directory, prefer ~/maxtac-resources/ in those cases. Decompile the binary (all or partial) to identify strings and other static data. Build a mapping of the most called and most important function. Scout existing threat mitigations in the decompiled code.

#### Kernel And Systems Recon

For XNU and open-source systems targets, map user-kernel entry points, IPC, entitlement or sandbox checks, file and parser surfaces, lifetime rules, locking, and mitigation assumptions. For Windows targets, bias toward supplied driver source, driver binaries, public symbols, patch diffs, and kernel-adjacent artifacts rather than closed-source operating-system internals.

### Discovery

In the Discovery phase, Codex launches a series of specialized Auditor subagents to check for relevant bugs and document findings as discovered. The subagents used for scanning depend on the type of target.

The initial Auditor set is systems-focused: XNU IOKit/MIG, XNU VFS/sandbox, XNU lifetime and parser surfaces, Windows driver IOCTLs, Windows object/token handling, Windows memory and filesystem filters, binary patch diffing, native parser fuzzability, crash root cause, and open-source systems code.

### Triage

In the Triage phase, Codex validates a finding has not already been documented, reachable by an attacker, and exploitable. All three of these qualifications must pass for a finding to escalate to confident.

- De-duplication: A new finding must not already be documented.
- Reachability: A finding must have a full attacker-to-victim pipeline.
- Exploitability: A finding must be exploitable by an attacker.

Codex first performs the de-duplication as the main agent; if successful, several (3) Debater subagents are spawned to debate the reachability and exploitability of the finding. If a majority vote the finding as Valid, it is escalated to Validated. If the finding is Invalid, it may be de-escalated or closed.

To save on cost, the Debater subagents for triage use gpt-5.4-mini.

### Proof

In the Proofing phase, a realistic reproduction of the bug is created and tested. For cleanliness, all testing is conducted on a configured VM or docker container. Codex spawns a new Prover agent at the beginning of this phase with its own self-contained prompt. This prevents pollution and self-bias by having the subagent act in its own isolated session. 

Proof is conducted in three steps (may go back-and-forth):

1. Reproduce the bug from a human attacker-victim perspective. Verify the correct configurations, with the same reachability and exploitability stories as the Triage phase. If the bug cannot be reproduced, it is de-escalated or closed.
2. Suggest a fix for the bug.
3. In a newly spawned Auditor subagent, check for reproduction and fix correctness. If not valid, go back to any previous step.
