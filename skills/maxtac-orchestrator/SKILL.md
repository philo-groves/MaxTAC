---
name: maxtac-orchestrator
description: Run MaxTAC authorized multi-agent vulnerability research campaigns for XNU, Windows kernel-adjacent artifacts, native binaries, and open-source systems code. Use when the user asks to use MaxTAC, run a campaign, coordinate Auditor/Debater/Prover subagents, or move through prepare, discovery, triage, proof, and report phases.
---

# MaxTAC Orchestrator

Use this skill as the campaign controller. MaxTAC is for authorized systems vulnerability research, not opportunistic live testing. Keep the work local, offline, or inside an explicitly approved lab unless scope says otherwise.

## Operating Model

Run four phases:

1. Prepare: establish scope and build `data/maxtac/target-profile.json`.
2. Discovery: select focused Auditor packets from the catalog and delegate bounded investigations when subagents are authorized and available.
3. Triage: deduplicate candidates, then debate reachability, boundary crossing, and primitive quality before promoting a finding.
4. Proof: reproduce in a clean lab, add negative controls, suggest a fix, and package evidence.

Use the parent agent as the state owner. Subagents return packets; the parent deduplicates and updates the ledger.

## Skill Order

1. Use `maxtac-engagement-scope` first when authorization, allowed execution, lab boundaries, or artifact handling are unclear.
2. Use `maxtac-prepare` to build or refresh the target profile.
3. Use `maxtac-auditor-router` to select Auditor entries and create sealed packets.
4. Use `maxtac-finding-ledger` before adding or changing findings.
5. Use `maxtac-triage-debate` once a candidate has enough evidence to evaluate.
6. Use `maxtac-proof-lab` only after a finding is `confident`.
7. Use `maxtac-chain-analysis` when multiple findings may compose into stronger impact.
8. Use `maxtac-report-writer` for proofed findings or campaign summaries.

## Delegation Rules

Only spawn subagents when the user has asked for MaxTAC, multi-agent work, subagents, delegation, or a campaign. If subagent tools are unavailable, run the same packets sequentially in the parent thread.

When spawning Auditors:

- Give each Auditor one catalog entry and one sealed packet.
- Include target profile facts, exact files or binaries, allowed operations, and output schema.
- Do not ask Auditors to update shared files.
- Prefer independent packets with disjoint file or artifact focus.
- Keep Windows kernel work focused on supplied drivers, driver source, driver binaries, public symbols, patch diffs, and lab artifacts.
- Treat Linux kernel targets and browser/API application testing as out of v0 scope unless the user explicitly overrides the campaign family.

When spawning Debaters:

- Use independent agents with the same candidate packet.
- Ask each Debater for `valid`, `invalid`, or `needs-more-work`.
- Require reasoning about reachability, boundary crossing, primitive quality, scope, and missing proof.
- Let one decisive hard blocker stop promotion even if a simple majority says valid.

When spawning Provers:

- Use a fresh context with only the finding packet, target profile, scope limits, and lab instructions.
- Require deterministic reproduction, negative controls, cleanup, and a proof packet.
- Avoid letting the Prover inherit the discovery narrative unless the evidence itself needs it.

## Campaign State

Keep durable artifacts under `data/maxtac/`:

```text
data/maxtac/
  target-profile.json
  findings.json
  auditor-packets/
  debates/
  proof/
  reports/
```

Do not store raw secrets, private keys, unredacted tokens, customer data, or destructive payloads.

## Completion Standard

Stop a campaign phase only when the next action is clear:

- Discovery found no credible candidates in the selected packets.
- A candidate was added, duplicated, or de-escalated in the ledger.
- Triage promoted a finding to `confident`, returned it for more work, or de-escalated it.
- Proof produced a proof packet, failed with a recorded reason, or found a required scope change.
- A report was written from proofed evidence.
