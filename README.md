# MaxTAC

Maximize your Trusted Access for Cyber status with a multi-agent cyber plugin purpose-built for authorized vulnerability research and proofing. The initial implementation focuses on XNU, Apple platform security research, Windows kernel-adjacent artifacts, native binaries, and open-source systems code.

## What Is Included

- `maxtac-orchestrator`: Coordinates the Prepare, Discovery, Triage, Proof, and Report phases.
- `maxtac-prepare`: Builds `data/maxtac/target-profile.json`.
- `maxtac-apple-workspace`: Creates persistent Apple research directories by domain.
- Focused Apple skills: `maxtac-apple-target-flags`, `maxtac-apple-sptm-bypass`, `maxtac-apple-aslr-bypass`, `maxtac-apple-pac-bypass`, `maxtac-apple-jop-chaining`, `maxtac-apple-gadget-chaining`, `maxtac-apple-stack-pivoting`, and `maxtac-apple-heap-grooming`.
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

Put program details, official scope links, target assets, allowed operations, lab constraints, and exclusions in the target workspace `AGENTS.md` before starting a campaign. MaxTAC assumes that context is already supplied by the researcher and does not run a separate scope preflight skill.

The expected campaign state lives under:

```text
data/maxtac/
  target-profile.json
  findings.json
  auditor-packets/
  debates/
  proof/
  research/
    apple-intelligence/
    boot-chain/
    comms/
    icloud/
    kernel/
    private-cloud-compute/
    radios/
    sandbox/
    webkit/
  reports/
```

Apple findings may include an optional `domain` field matching one of the research directories. Keep detailed markdown in `data/maxtac/research/<domain>/<target>/` and reference those files from the ledger.

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

The initial Auditor set is systems-focused: XNU IOKit/MIG, XNU VFS/sandbox, XNU lifetime and parser surfaces, focused Apple bypass mechanisms, Windows driver IOCTLs, Windows object/token handling, Windows memory and filesystem filters, binary patch diffing, native parser fuzzability, crash root cause, and open-source systems code.

### Triage

In the Triage phase, Codex validates a finding has not already been documented, reachable by an attacker, and exploitable. All three of these qualifications must pass for a finding to escalate to confident.

- De-duplication: A new finding must not already be documented.
- Reachability: A finding must have a full attacker-to-victim pipeline.
- Exploitability: A finding must be exploitable by an attacker.

Codex first performs the de-duplication as the main agent; if successful, several (3) Debater subagents are spawned to debate the reachability and exploitability of the finding. If a majority vote the finding as Valid, it is escalated to Validated. If the finding is Invalid, Debaters must identify alternative routes before recommending de-escalation.

To save on cost, the Debater subagents for triage use gpt-5.4-mini.

### Proof

In the Proofing phase, a realistic reproduction of the bug is created and tested. For cleanliness, all testing is conducted on a configured VM or docker container. Codex spawns a new Prover agent at the beginning of this phase with its own self-contained prompt. This prevents pollution and self-bias by having the subagent act in its own isolated session. 

Proof is conducted in three steps (may go back-and-forth):

1. Reproduce the bug from a human attacker-victim perspective. Verify the correct configurations, with the same reachability and exploitability stories as the Triage phase. If the bug cannot be reproduced, record why and route to a plausible alternate primitive or de-escalate only with decisive evidence.
2. Suggest a fix for the bug.
3. In a newly spawned Auditor subagent, check for reproduction and fix correctness. If not valid, go back to any previous step.
