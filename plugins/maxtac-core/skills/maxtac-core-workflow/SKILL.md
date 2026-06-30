---
name: maxtac-core-workflow
description: "Use this skill when starting, organizing, or continuing an authorized MaxTAC vulnerability research session with standard directories, phases, closure profiles, thin closure decisions, adversarial false-negative review, subsystem notes, validation, proof, and reporting flow."
---

# MaxTAC Core Workflow

Orchestration for vulnerability research workflow. MaxTAC is for authorized vulnerability analysis and proofing. The workflow aggressively utilizes the verified Trusted Access for Cyber (TAC) membership of plugin users and their expanded range of OpenAI cyber capabilities. Do not negatively affect other users or external resources unless given direct permission.

## Directory Structure
The following files and directories are managed under the base directory of the workspace:

```
program-info.md    # authorized scope and exclusions
workspace.sqlite   # findings, model assertions, debate tallies, audit index, and search memory
reporting/         # submission-ready reports and evidence indexes
research/          # faceted research corpus: notes, generated views, and artifacts
  notes/           # canonical compact notes by stable ID
  views/           # generated indexes and graph projections
  artifacts/       # raw corpus artifacts and imported legacy markdown
models/            # machine-readable security models and invariant dictionaries
proof/             # proof-of-vulnerability (PoV) development
fuzz/              # fuzzing inputs, scripts, and artifacts
contracts/         # canonical result bundles and deterministic report projections
tmp/               # temporary files that can be deleted between sessions
```

## Workspace Helper Script

Use `python3 <skill-dir>/scripts/workspace.py` for routine workspace operations instead of hand-creating the standard files and directories:

- `init`: create the canonical workspace directories, seed `program-info.md`, initialize empty finding ledgers, and record the starting phase.
- `status`: summarize workspace health, model counts, ledger counts, false-negative reviews, oversized research markdown, research hygiene, attention-lock warnings, phase state, and report readiness.
- `phase`: show or update the current workflow phase. The canonical forward path is `prepare` -> `scan` -> `validation` -> `primitive-proof` -> `chain-proof` -> `reporting`; the helper also allows documented returns to earlier phases when evidence invalidates a path. Repeating the current phase with `--note` records a timestamped phase renewal. Use `phase --suggest` to inspect evidence-based phase drift and `phase --auto --note ...` to repair stale phase state when the workspace clearly moved ahead.
- `new-submodule`: create a legacy research submodule under `research/`; prefer `maxtac-core-corpus` for new durable knowledge.
- `split-large-markdown`: split a markdown file over the large-file threshold into a submodule. Retain the source by default; delete it only with `--verified --delete-source` after confirming the transcription.
- `report-ready`: check whether a proofed chain has the minimum workspace evidence needed to move into reporting.
- `false-negative-review`: create a structured adversarial reopen review under `contracts/false-negative-reviews/` with a negative-evidence score, explicit gaps, and reopen actions.

The helper stores phase history in `<workspace-root>/.maxtac-workspace.json`. Finding state remains owned by the `maxtac-core-ledger` script and is stored in `<workspace-root>/workspace.sqlite`. The same database also indexes model assertions, debate tallies, and audit assessments so agents can search known invariants, prior votes, conclusions, blockers, and artifacts before repeating work.

Use `scripts/workspace.py` as the canonical Core workspace helper. Domain or program-specific packs may expose MCP wrappers for their own workflows, but Core does not require them.

## Research Workspace
MaxTAC is designed as a modular research workspace meant to scale for scopes of any size, continuously building a knowledge base that provides better context than most security researchers traditionally have access to. Models often persist every research file to the base directory, or fail to persist important knowledge at all; this guidance prevents that behavior.

### Corpus Contract

Treat `research/` as a faceted research corpus, not a hand-authored directory hierarchy. Use `maxtac-core-corpus` to create canonical compact notes under `research/notes/`, index them in `workspace.sqlite`, link them with typed graph edges, and generate browseable views under `research/views/`. A future session should learn the target by querying and orienting through the corpus, not by following whichever folder the previous agent happened to expand.

Treat `models/` as the machine-readable sibling to the corpus. Use `maxtac-core-modeling` to create `models/<model-id>/model.json`, project `invariants.md`, `obligations.md`, and `graph.mmd`, and index model assertions into `workspace.sqlite`. Corpus notes explain system knowledge in prose; models preserve formal entities, relations, invariants, formulas, assumptions, unknowns, contradictions, status, confidence, and evidence references.

Before persisting durable markdown, classify it:

- **Corpus note**: synthesized knowledge future sessions should read. Add it with `maxtac-core-corpus add-note`, using tags such as `domain`, `subsystem`, `boundary`, `asset`, `actor`, `knowledge-kind`, and `phase`.
- **Generated view**: `research/views/*.md` or `graph.mmd` created by `maxtac-core-corpus compile-views`; never edit by hand.
- **Artifact markdown**: raw output, transcripts, copied legacy files, packet dumps, or evidence manifests. Put it under `research/artifacts/`, `proof/`, `fuzz/`, `contracts/`, or `tmp/`.

Markdown under `research/artifacts/` is artifact-only. If it contains durable conclusions, rewrite those facts into compact corpus notes and leave the artifact as evidence. A future reader should be able to orient through `research/notes/` and generated views, then inspect artifacts only for proof and provenance.

Optional code-intelligence systems such as codebase-memory-mcp can accelerate orientation, call-path tracing, ADR lookup, and diff-impact mapping. Treat their output as artifact evidence or a discovery cache. The MaxTAC corpus and `models/` bundles remain the durable security memory; rewrite reusable architecture, trust-boundary, invariant, or negative result into corpus notes, and add structured entities, relations, invariants, formulas, assumptions, unknowns, or contradictions to `models/` when the knowledge should drive future auditor prompts.

### Corpus Writes

Use `maxtac-core-corpus orient` before adding research notes for a target slice. The orientation pack includes primary notes, graph neighbors, negative knowledge, open questions, and underexplored tags. This is the main anti-tunnel mechanism.

Use `maxtac-core-corpus add-note` for new durable knowledge. Notes must stay compact, include a summary, include at least two facet tags, and use evidence for `observed`, `confirmed`, `negative`, `stale`, `superseded`, or `artifact-only` status. If the helper rejects a large note, split the concept or store raw output as an artifact and summarize it.

Use `maxtac-core-corpus link` when one note refines, supersedes, contradicts, supports, depends on, closes, or opens another note. Prefer updating or linking existing notes over adding near-duplicates.

Run `maxtac-core-corpus compile-views` after meaningful writes. Generated views are the replacement for manual hierarchy: if a view is wrong, fix tags or edges and regenerate.

### Legacy Markdown

Older workspaces may contain hand-authored `research/<submodule>/**/*.md` files. Do not continue expanding that hierarchy. Import durable knowledge with `maxtac-core-corpus import-file`, then move raw legacy markdown under `research/artifacts/imported-markdown/` only after the canonical note preserves the important facts.

`new-submodule` remains available for compatibility, but new durable knowledge should go through the corpus helper. `workspace.py status` warns about markdown outside `research/notes/`, `research/views/`, and `research/artifacts/`.

### Branch Closure

Every substantial scan, RE branch, proof branch, or negative result should close with a persistence decision:

- **Incorporated**: reusable knowledge was rewritten into one or more corpus notes, with evidence links and graph edges.
- **Artifact-only**: no reusable system knowledge was produced; keep only raw evidence and state why in a corpus note or ledger milestone.
- **Deferred**: the branch is incomplete; leave a pointer in `tmp/`, `workspace.sqlite`, or a ledger evidence link, not as a misleading corpus note.

This prevents session goals from becoming the knowledge structure and prevents artifacts from becoming a hidden markdown knowledge base.

### Closure Profiles

Use a closure profile before creating narrative artifacts.

Choose **thin closure** when all are true:

- the target is exact and small, usually one to three files, commands, helpers, or a tightly bounded family;
- no reportable primitive or chain survived;
- the essential insight fits in one compact conclusion, such as "helper is simple; caller path shells through it; no privileged caller found";
- the proof requirement is source coverage plus caller/runtime/VM evidence;
- no new formal invariant, architecture model, multi-step chain, or adversarial debate is needed.

Thin closure must still produce:

- one coverage receipt, such as `maxtac-source-scan thin-close` or an equivalent domain receipt;
- caller/runtime/proof evidence when reachability or privilege is the key break;
- one `maxtac-core-contracts thin-closure` result bundle with explicit reopen criteria;
- a ledger update or milestone if a candidate finding already exists;
- one compact corpus `closure` or `negative-result` note that points at the contract and proof evidence.

Thin closure should skip separate surface packets, OpenGrep mini-reports, model entities/invariants, expanded audit prose, and long generated reports unless the target stops being tiny. Do not use thin closure for reportable findings, multi-step chains, privileged reachable behavior, contested conclusions, or reusable architecture that future auditors need as a model.

Choose **full closure** for reportable findings, broad target families, chained behavior, substantial negative results that affect future architecture understanding, or anything requiring formal debate/modeling.

### False-Negative Review

Treat "no reportable chain found" as weaker than "no bugs exist." After a long no-finding session, before closing a broad family, or before trusting many thin closures as a program-level conclusion, run an adversarial false-negative review:

```text
python3 <skill-dir>/scripts/workspace.py false-negative-review \
  --root <workspace-root> \
  --review-id system-cmds-reopen \
  --target "macOS system commands" \
  --scope "all macOS-reachable commands reviewed in this session" \
  --conclusion "No ASB-promotable chain survived the evidence gathered." \
  --evidence source=contracts/source-scans/system-cmds/coverage.jsonl \
  --evidence caller=research/artifacts/system-cmds/caller-search.md \
  --gap patch-diff="Apple OSS tag diffing not completed" \
  --gap chain-composition="No primitive-first chain composer pass yet"
```

The score is a negative-evidence score, not a bug absence score. Use `high` or `medium` false-negative risk as a required decision point: reopen, delegate a resurrection review, or explicitly record why the gap is accepted for this goal.

The default reopen actions intentionally mirror common false-negative hiding places:

- **Primitive graveyard**: review every `de-escalated` or `limited` primitive as if trying to resurrect it.
- **Caller expansion**: search private frameworks, libSystem, launchd jobs, XPC services, scripts, and dyld-cache symbols for API or command consumers.
- **Patch diff**: compare relevant vendor or OSS tags for quiet hardening changes.
- **Chain composer**: start from primitives and chain breaks, not command families.
- **Invariant receipts**: verify exact guard, sink, authority boundary, trusted caller set, bypass assumptions, binary gaps, proof obligations, and refutation conditions.
- **Fuzzing/harnessing**: add targeted harnesses for parser-heavy or input-normalization surfaces before accepting source-only negatives.

When a false-negative review changes confidence, link the review from the corpus closure note, any related contract `closure_evidence`, and ledger milestones for reopened or still-closed candidates.

Read `schemas/false-negative-review.schema.json` only when exact machine-readable review shape matters.

### Attention Cadence

Long-running research has two common failure modes: tunnel vision inside one subsystem or tag cluster, and shallow hopping across many surfaces without enough depth. Do not let the current context decide the next move by inertia.

At the start of a session, after a phase change, every 45-60 minutes of active research, after about 10-15 meaningful workspace writes, and before continuing a branch that has stopped producing new evidence, run `workspace_status` or:

```
python3 <skill-dir>/scripts/workspace.py status --root <workspace-root>
```

The status helper uses phase timestamps, ledger file timestamps, recent corpus/model file mtimes, and recent evidence/artifact mtimes to report attention warnings. Treat these warnings as a required decision point, not an automatic stop. Choose and record one action:

- **Deepen**: continue the same subsystem or tag cluster only with a narrower evidence target, a specific caller/callee, a proof gate, or a short next checkpoint.
- **Pivot**: move to a sibling or child subsystem, a new bug-class route, or a different phase when the current branch is stale.
- **Consolidate**: stop exploratory work and rewrite reusable knowledge into corpus notes and model assertions, update the ledger, or close the branch as artifact-only.
- **Phase-shift**: use `workspace_phase --note ...`, `python3 <skill-dir>/scripts/workspace.py phase <phase> --root <workspace-root> --note ...`, or `python3 <skill-dir>/scripts/workspace.py phase --auto --root <workspace-root> --note ...` when the work has crossed from prepare to scan, scan to validation, validation to proof, or back to a prior phase.
- **Delegate-review**: spawn a goal-bounded auditor/debater to independently judge whether to deepen, pivot, consolidate, or de-escalate.

Intentional deep work is allowed, but the attention budget must be renewed by new evidence, a branch closure, a corpus note or graph edge, a model update, a ledger milestone, or a timestamped phase note. Do not spend more than one attention interval in the same subsystem, tag cluster, or phase without one of those renewals. Likewise, do not open more surfaces after a shallow-hopping warning until one branch has been deepened or consolidated.

## Research Phases

The workflow is optimized for three primary goals:

1. Build a scalable security knowledge base of the program and technology.
2. Identify and verify individual code or system flaws known as primitives.
3. Combine primitives into chains with proven reachabilty and exploitability.

### 1. Prepare

Go to this phase at the start of the workflow or when additional threat modeling is required.

#### First Run Setup
Assume the first run is active if `<workspace-root>/program-info.md` does not exist. Ingest the program information to `<workspace-root>/program-info.md` as a preliminary step. Some programs have streamlined information via skills, others are more generic.

Use `<skill-dir>/references/program-info.template.md` relative to this skill as a template and fill in the missing sections. Key information should come from the user, the installed domain/program pack, or the current official program source.

#### Corpus Setup
Run `maxtac-core-corpus init` during first-run setup. If the workspace already has legacy research markdown outside `research/notes/`, run `maxtac-core-corpus orient` before reading broadly and import durable knowledge opportunistically instead of appending to old directories. Use `maxtac-core-corpus compile-views` after adding or importing notes.

#### Modeling Setup
Use `maxtac-core-modeling` during Prepare when the target has nontrivial architecture, identity, trust, state, or policy behavior. Create or refresh a model under `models/<model-id>/` before spawning broad auditors. At minimum, capture:

- major actors, principals, components, services, resources, assets, entrypoints, guards, sinks, states, and trust boundaries;
- relations that explain identity, authorization, data movement, state transitions, delegation, or trust;
- security invariants and first-order-logic-style formulas where they clarify the rule;
- assumptions, unknowns, and contradictions that could change vulnerability conclusions.

Do not force tiny one-off tasks into a model, but if a session depends on "what must always be true" about a system, create the model before Scan.

#### Target Setup
Run `maxtac-core-corpus orient` for the target slice using a query or tags such as `subsystem`, `boundary`, `asset`, and `knowledge-kind`. Use the orientation pack to identify existing notes, graph neighbors, negative knowledge, open questions, and underexplored tags. Add or update corpus notes only after checking for prior related knowledge.

Next, identify which installed domain pack owns the target method:

- Source/SAST: source repositories, existing decompiler output, optional codebase-memory graph queries, static reachability, guard dominance, and OpenGrep evidence.
- Binary: native binaries, firmware payloads, reverse engineering, crash replay, native instrumentation, and systems fuzzing.
- Web: web applications, APIs, sessions, browser state, tenants, and SaaS workflows.
- Cloud: AWS, Azure, GCP, IAM, storage, data plane, runtime metadata, workload identity, managed Kubernetes, and cloud network boundaries.
- Supply Chains: dependency graphs, package managers, CI/CD, artifact provenance, signing, containers, and release pipelines.
- Android: APK/DEX/resource reverse engineering, Android components, ADB/logcat/JDWP/Frida evidence, IPC, WebView, storage, and permissions.
- Apple Systems or Microsoft Systems: program-specific proof and mitigation rules.

Core creates the workspace and records durable knowledge through corpus notes, model assertions, ledgers, and contracts; the active domain pack chooses the concrete tools, triage packet, and auditor catalog.

### 2. Scan
Go to this phase after the Prepare phase or when additional vulnerability discovery is required.

#### Surface Triage
Use the installed domain pack that matches the target. Produce a compact triage packet or evidence note that names the target slice, actor, trust boundary, controlled inputs, security invariant, suspect guard or sink, evidence already collected, and suggested auditor filters.

When source code or existing decompiler output is available, the Source pack can produce SAST, control-flow, and OpenGrep packets. When the target is web, cloud, supply-chain, binary, Android, Apple, or Microsoft-specific, use that pack's triage guidance before spawning auditors.

Before spawning auditors for a subsystem, search and orient with `maxtac-core-corpus`. If the orientation pack shows matching negative-result or open-question notes, route the audit to close or refine those notes instead of rediscovering them.

Before spawning auditors for a modeled subsystem, search `models/` with `maxtac-core-modeling`. Export a model-backed auditor prompt when known invariants, formulas, assumptions, or unknowns materially affect the audit. If triage discovers reusable architecture or a new invariant, update the model after the packet is stable.

#### Hypothesize
Analyze previously conducted recon, threat modeling, research, models, and surface triage to come up with at least one new primitive or chain hypothesis. Pay close attention to multi-function, multi-file, multi-system security considerations. Magnetize toward code danger zones and security boundaries. Avoid duplicating previous hypotheses on the same software version. Treat candidate invariant violations as hypotheses, not findings.

#### Spawn Auditors
Before spawning a new auditor, search existing corpus notes, model assertions, and audit memory with `maxtac-core-corpus orient`, `maxtac-core-modeling search`, and `audit-helper.py --audit-search "<hypothesis boundary component>"`. If prior knowledge already covers the same boundary, reuse it, write a narrowed delta prompt, or update the ledger/corpus/model instead of repeating the audit. When enriching the final auditor prompt through `maxtac-core-subagents`, pass `--context-query "<hypothesis boundary component>"` so the generated prompt embeds the corpus orientation and model search output.

For each remaining hypothesis, spawn one or more targeted, goal-bounded auditor subagents with `maxtac-core-subagents` skill guidance to scan for unique vulnerabilities. Use the active domain pack's auditor MCP tools or, when those tools are not exposed in the current context, the local catalog fallback in `audit-helper.py --catalog <domain>` to select the narrowest suitable auditor set, usually 1-4 auditors. Avoid a broad "logic analysis" audit when a specific business logic, authorization, parser, race, memory safety, platform, supply-chain, or mitigation auditor fits. Each audit results in a hypothesis-evidence packet containing audit methods and security analysis stored in `workspace.sqlite` for later semantic lookup.

#### Update Findings
Based on audit results, use `maxtac-core-ledger` guidance to create or update findings. In most cases, audits result in findings in a `discovered` or `confident` state. Sometimes, an audit will surface evidence that demotes an existing finding to a `de-escalated` or `limited` state.

During scan, do not write unvalidated vulnerability claims into corpus notes or models as facts. Do update corpus notes and model assertions for stable system knowledge learned during the branch, especially architecture, reachability gates, authorization invariants, state transitions, contradictions, assumptions, unknowns, and negative results that will prevent future duplicate work. Keep speculative packets, broad match sets, and raw branch notes in `workspace.sqlite`, `tmp/`, or `research/artifacts/` until they are rewritten into compact corpus notes and structured model entries.

### 3. Validation
Go to this phase after the Scan phase or when additional pre-proofing validation is required.

#### Spawn Debaters
For each new finding or pre-proofing requirement, spawn three goal-bounded subagents with the `maxtac-core-subagents` skill to judge its validity. If the finding is a chain, also judge its reachability and exploitability. Each debater votes each finding as valid or invalid. Debate tallies are indexed into `workspace.sqlite`; use `debate-helper.py --list`, `--show`, or `--search` to review previous votes before promoting, de-escalating, or reopening the same proposition.

#### Update Findings
If at least two subagents vote invalid, go to the Scan phase where more auditing may be conducted, or the finding may be `de-escalated`. If at least two subagents vote valid, the finding is promoted to `validated` using `maxtac-core-ledger` guidance and update the research (see next section). Before any promotion action, search the finding ledger to determine if the finding already exists, and if it does, use `maxtac-core-ledger` guidance to mark the `duplicate` state. If the finding is original, move to the Proof phase.

#### Update Research
After promoting any finding to `validated`, evidence from its audit(s) is incorporated into the research workspace. Determine whether a related corpus note already exists; if not, create one with `maxtac-core-corpus add-note`. Do not copy audit information directly; instead, rewrite the information into compact durable prose, tag it, and link to exact audit or artifact evidence. If the finding confirms, refutes, or violates a modeled invariant, update the relevant model assertion status and evidence with `maxtac-core-modeling`.

### 4. Primitive Proof
Go to this phase after the Validation phase completes with at least one valid non-duplicate finding.

#### Proof-of-Vulnerability (PoV) Primitive
Construct and execute an isolated proof-of-vulnerability (PoV) primitive that plausibly validates the vulnerable behavior, inputs, and pre-conditions. Primitive proofing is intentionally more lax than chain proofing. This stage is meant to prove a standalone flaw exists, but it does not guarantee a reportable chain. Spawn three goal-bounded debater subagents using `maxtac-core-subagents` guidance to vote whether the PoV reproduces the described primitive: `valid` or `invalid`.

#### Update Findings
If at least two subagents vote invalid, revise the PoV or use `maxtac-core-ledger` guidance to de-escalate the primitive as debunked or out-of-scope. Confirmed primitives are marked as proofed according to `maxtac-core-ledger` guidance, even if they are not reachable or exploitable. If a primitive cannot be proven nor debunked, it is marked as `limited`.

#### Update Research
After executing any primitive PoV, identify related corpus notes for the system. For negative results, update or add negative-result notes so search and orientation prevent duplicate work. For positive results, do not overwrite information that may be important later; append or add concise corpus updates and link to proof artifacts. Update modeled preconditions, invariants, assumptions, and contradictions so later chain planning can search the proven facts.

#### Chain Planning
For each proven primitive, first analyze whether the primitive is exploitable and reachable as a standalone chain. If so, no further scanning is needed; a validated chain may be created based on the single primitive, then go to the Chain Proof phase. If the primitive is not reachable or exploitable on its own, use creative thinking to generate at least two chains and their hypotheses. If all chain primitives are already proven, go to the Chain Proof phase; otherwise, go to the Scan phase to audit the chain gaps.

### 5. Chain Proof
Go to this phase after a Primitive Proof or Scanning phase results in one or more validated chains.

#### Proof-of-Vulnerability (PoV) Chain
For each validated chain, create and execute a realistic end-to-end proof-of-vulnerability (PoV) reproduction of the vulnerability. The PoV must not mock any portion of the chain. The PoV chain must be reachable from a non-self or security sandboxed vector. The PoV chain must demonstrate an exploitable vulnerability that is not documented as an accepted risk or shared responsibility. Spawn three goal-bounded debater subagents using `maxtac-core-subagents` guidance to vote whether the PoV reproduces the described chain: `valid` or `invalid`.

#### Update Findings
If at least two subagents vote invalid, revise the PoV or use `maxtac-core-ledger` guidance to de-escalate the chain. If at least two subagents vote the PoV as valid, promote it to `proofed`. After marking a PoV as `proofed`, write a submission-ready report which includes it.

#### Update Research
After executing any chain PoV, identify corpus notes for every related subsystem, boundary, asset, and invariant. Since chains combine primitives, research may span multiple tags and graph edges. For negative results, update stale or invalid notes to prevent confusing search results. For positive results, append concise corpus updates and link to proof artifacts without burying the chain inside a session-named folder. If a chain proves an invariant violation, keep the invariant ID visible in the ledger evidence, proof notes, corpus note, and any result contract.

### 6. Reporting
Go to this phase after Chain Proof produces at least one proofed chain with accepted evidence.

Run `workspace_report_ready` or `python3 <skill-dir>/scripts/workspace.py report-ready` before drafting or finalizing a submission report. If the helper reports missing proof, scope, ledger, or phase evidence, return to the phase that can produce the missing artifact.

For bounded reviews, source scans, or handoffs, use `maxtac-core-contracts` to create and validate a canonical result bundle under `contracts/` before drafting prose. The contract should preserve findings, evidence references, coverage decisions, limitations, and deterministic report output. For tiny non-reportable targets, prefer `maxtac-core-contracts thin-closure` so the generated projection stays compact and carries reopen criteria instead of a mini-report.

Write submission-ready reports under `<workspace-root>/reporting/`. Reports should be based on proofed chains, not standalone primitives. Include the validated chain summary, attacker reachability, exploitability, affected versions or targets, reproduction steps, observed impact, proof artifacts, limitations, and any program-specific evidence requirements.
