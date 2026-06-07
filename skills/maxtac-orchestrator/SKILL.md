---
name: maxtac-orchestrator
description: Run MaxTAC authorized multi-agent vulnerability research campaigns for XNU, Windows kernel-adjacent artifacts, native binaries, and open-source systems code. Use when the user asks to use MaxTAC, run a campaign, coordinate Auditor/Debater/Prover subagents, or move through prepare, discovery, triage, proof, and report phases.
---

# MaxTAC Orchestrator

Use this skill as the campaign controller. MaxTAC is for authorized systems vulnerability research, not opportunistic live testing. Rely on researcher-supplied program details in the user prompt and target workspace `AGENTS.md`; do not perform broad program lookups unless the user asks. Keep the work local, offline, or inside an explicitly approved lab unless those supplied instructions allow otherwise.

## Operating Model

Run four phases:

1. Prepare: summarize supplied constraints and build `data/maxtac/target-profile.json`.
2. Discovery: select focused Auditor packets from the catalog, initialize Apple domain notes when relevant, add focused Apple mechanism analysis when exploitability is blocked, and delegate bounded investigations when subagents are authorized and available.
3. Triage: deduplicate candidates, then debate reachability, boundary crossing, and primitive quality before promoting a finding.
4. Proof: reproduce in a clean lab, add negative controls, suggest a fix, and package evidence.

Use the parent agent as the state owner. Subagents return packets; the parent deduplicates and updates the ledger.

## Skill Order

1. Use `maxtac-prepare` to build or refresh the target profile from supplied artifacts, the user prompt, and target workspace `AGENTS.md`.
2. Use `maxtac-apple-workspace` for Apple campaigns to create `data/maxtac/research/<domain>/<target>/` notes and keep the ledger compact.
3. Use focused Apple skills as needed: `maxtac-apple-target-flags`, `maxtac-apple-sptm-bypass`, `maxtac-apple-aslr-bypass`, `maxtac-apple-pac-bypass`, `maxtac-apple-jop-chaining`, `maxtac-apple-gadget-chaining`, `maxtac-apple-stack-pivoting`, and `maxtac-apple-heap-grooming`.
4. Use `maxtac-auditor-router` to select Auditor entries and create sealed packets.
5. Use `maxtac-finding-ledger` before adding or changing findings. Include `--domain` for Apple findings when known.
6. Use `maxtac-triage-debate` once a candidate has enough evidence to evaluate.
7. Use `maxtac-proof-lab` only after a finding is `confident`.
8. Use `maxtac-chain-analysis` when multiple findings may compose into stronger impact.
9. Use `maxtac-report-writer` for proofed findings or campaign summaries.

When an Apple path blocks, route to an alternative missing primitive or domain note before de-escalating: leak, PAC-compatible reuse, SPTM transition bug, Target Flag proof, JOP dispatcher, gadget inventory, stack/context pivot, or heap placement.

## Delegation Rules

Only spawn subagents when the user has asked for MaxTAC, multi-agent work, subagents, delegation, or a campaign. If subagent tools are unavailable, run the same packets sequentially in the parent thread.

When spawning Auditors:

- Give each Auditor one catalog entry and one sealed packet.
- Include target profile facts, exact files or binaries, relevant Apple domain notes, focused mechanism notes, allowed operations, and output schema.
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
  research/
  reports/
```

Do not store raw secrets, private keys, unredacted tokens, customer data, or destructive payloads.

## Completion Standard

Stop a campaign phase only when the next action is clear:

- Discovery found no credible candidates in the selected packets.
- A candidate was added, duplicated, or de-escalated in the ledger.
- Triage promoted a finding to `confident`, returned it for more work, routed it to an alternative primitive, or de-escalated it with decisive evidence.
- Proof produced a proof packet, failed with a recorded reason, or found a required scope change.
- A report was written from proofed evidence.
