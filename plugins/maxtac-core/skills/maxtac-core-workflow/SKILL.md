---
name: maxtac-core-workflow
description: "Use this skill when starting, organizing, or continuing an authorized MaxTAC vulnerability research session with standard directories, phases, subsystem notes, validation, proof, and reporting flow."
---

# MaxTAC Core Workflow

Orchestration for vulnerability research workflow. MaxTAC is for authorized vulnerability analysis and proofing. The workflow aggressively utilizes the verified Trusted Access for Cyber (TAC) membership of plugin users and their expanded range of OpenAI cyber capabilities. Do not negatively affect other users or external resources unless given direct permission.

## Directory Structure
The following files and directories are managed under the base directory of the workspace:

```
program-info.md    # authorized scope and exclusions
workspace.sqlite   # findings, debate tallies, audit index, and search memory
reporting/         # submission-ready reports and evidence indexes
research/          # scalable markdown research library
proof/             # proof-of-vulnerability (PoV) development
fuzz/              # fuzzing inputs, scripts, and artifacts
contracts/         # canonical result bundles and deterministic report projections
tmp/               # temporary files that can be deleted between sessions
```

## Workspace Helper Script

Use `python3 <skill-dir>/scripts/workspace.py` for routine workspace operations instead of hand-creating the standard files and directories:

- `init`: create the canonical workspace directories, seed `program-info.md`, initialize empty finding ledgers, and record the starting phase.
- `status`: summarize workspace health, ledger counts, oversized research markdown, research hygiene, attention-lock warnings, phase state, and report readiness.
- `phase`: show or update the current workflow phase. The canonical forward path is `prepare` -> `scan` -> `validation` -> `primitive-proof` -> `chain-proof` -> `reporting`; the helper also allows documented returns to earlier phases when evidence invalidates a path. Repeating the current phase with `--note` records a timestamped phase renewal.
- `new-submodule`: create a durable research submodule under `research/`, with an `artifacts/` directory for raw evidence and optional subsystem markdown from `references/subsystem.template.md`.
- `split-large-markdown`: split a markdown file over the large-file threshold into a submodule. Retain the source by default; delete it only with `--verified --delete-source` after confirming the transcription.
- `report-ready`: check whether a proofed chain has the minimum workspace evidence needed to move into reporting.

The helper stores phase history in `<workspace-root>/.maxtac-workspace.json`. Finding state remains owned by the `maxtac-core-ledger` script and is stored in `<workspace-root>/workspace.sqlite`. The same database also indexes debate tallies and audit assessments so agents can search prior votes, conclusions, blockers, and artifacts before repeating work.

Use `scripts/workspace.py` as the canonical Core workspace helper. Domain or program-specific packs may expose MCP wrappers for their own workflows, but Core does not require them.

## Research Workspace
MaxTAC is designed as a modular research workspace meant to scale for scopes of any size, continuously building a knowledge base that provides better context than most security researchers traditionally have access to. Models often persist every research file to the base directory, or fail to persist important knowledge at all; this guidance prevents that behavior.

### Research Library Contract

Treat `research/` as a permanent, cross-session security book about the target program or system. Its markdown should read like durable chapters: architecture, entrypoints, trust boundaries, invariants, subsystem behavior, confirmed negative knowledge, and links to supporting evidence. It is not a session transcript, scratchpad, tool-output dump, or per-hypothesis storage bin.

Before persisting any markdown, classify it:

- **Research library markdown**: synthesized knowledge a future session should read to understand the system. Put it in the narrowest stable subsystem submodule under `research/`.
- **Artifact markdown**: evidence manifests, command transcripts, reproduction logs, generated packets, or exact tool output. Put it under the relevant submodule's `artifacts/`, `proof/`, `fuzz/`, `contracts/`, or `tmp/`.

Markdown under `artifacts/` is the exception. If a markdown file contains conclusions, triage reasoning, reusable negative evidence, or a subsystem model, rewrite those facts into a sibling research-library note and leave the artifact as a source link. A future reader should be able to learn the system by reading `research/**/*.md` outside `artifacts/`, then inspect artifacts only for proof and provenance.

Optional code-intelligence systems such as codebase-memory-mcp can accelerate orientation, call-path tracing, ADR lookup, and diff-impact mapping. Treat their output as artifact evidence or a discovery cache. The MaxTAC `research/` library remains the durable security memory; rewrite any reusable architecture, trust-boundary, invariant, or negative result into `research/` instead of relying on an external graph or ADR store.

### Submodule Structure

The base module exists at `research/`, containing a hierarchy of system-focused submodules. Submodules should follow durable ownership boundaries such as product area, subsystem, component family, protocol, policy engine, kernel area, or parser family. They should not be named after a single session, date, build number, tool, or hypothesis unless the subject itself is inherently version-specific.

Each submodule contains one or more book-like markdown files for localized system knowledge. Put raw logs, generated JSON, binaries, extracted firmware, screenshots, packet outputs, command transcripts, hashes, and reproduction evidence in a submodule-relative `artifacts/` directory. Submodules may have their own child submodules. There is no child submodule limit.

When research shifts to another component, create or reuse the matching stable submodule instead of continuing to append into the current one. Do not let a single broad module become a second workspace root.

#### Example:
```
research/
  ios-platform/
    security/
      keychain.md
      cryptotokenkit.md
      trustd.md
      artifacts/
    kernel/
      vfs-apfs.md
      artifacts/
    network-identity/
      eap8021x.md
      networkextension.md
      artifacts/
    mail/
      smime-identities.md
      artifacts/
    firmware/
      provenance.md
      artifacts/
```

### Naming Conventions
Due to search noise and loss in large research workspaces, naming is more important than it may seem. Submodule directory names should label the localized system that is being researched. Markdown file names should label the subsystem being documented. Avoid timestamps, dates, internal identifiers, build numbers, and hypothesis names in library paths. Use those names inside artifact case directories instead.

#### Examples
Submodule examples: `apple-intelligence` with a `apple-foundation-models` submodule; `edge` with an `edge-app-container` submodule.

Markdown examples: `amf-3-core-model.md`, `amf-3-core-advanced-model.md`, `pcc-server-model.md` in an `apple-foundation-models` submodule; `browser-process.md`, `renderer-process.md`, `extension-system.md` in an `edge-app-container` submodule.

Tool names such as `opengrep`, `r2`, `ghidra`, `jadx`, `adb`, `ipsw`, or `frida` usually belong below `artifacts/` because they describe how evidence was produced, not what system is being modeled. Create a tool-named research submodule only when the tool itself is the research target, and include real subsystem markdown in it.

### Large Markdown
A large markdown file is a sign that a single document should be broken into a submodule. If a large markdown file (> 300 lines) is found, create the new submodule and rewrite the large markdown core information under several research files. Also copy any relevant artifacts into the new submodule. Only after verifying the key information was transcribed, delete the old markdown file and old artifacts.

### Branch Closure

Every substantial scan, RE branch, proof branch, or negative result should close with a persistence decision:

- **Incorporated**: reusable knowledge was rewritten into a named research-library markdown file, with artifact links.
- **Artifact-only**: no reusable system knowledge was produced; keep only raw evidence and state why.
- **Deferred**: the branch is incomplete; leave a pointer in `tmp/`, `workspace.sqlite`, or a ledger evidence link, not as a misleading library chapter.

This prevents session goals from becoming the library structure and prevents `artifacts/` from becoming a hidden markdown knowledge base.

### Attention Cadence

Long-running research has two common failure modes: tunnel vision inside one submodule, and shallow hopping across many surfaces without enough depth. Do not let the current context decide the next move by inertia.

At the start of a session, after a phase change, every 45-60 minutes of active research, after about 10-15 meaningful workspace writes, and before continuing a branch that has stopped producing new evidence, run `workspace_status` or:

```
python <skill-dir>/scripts/workspace.py status --root <workspace-root>
```

The status helper uses phase timestamps, ledger file timestamps, recent research-library file mtimes, and recent evidence/artifact mtimes to report attention warnings. Treat these warnings as a required decision point, not an automatic stop. Choose and record one action:

- **Deepen**: continue the same subsystem only with a narrower evidence target, a specific caller/callee, a proof gate, or a short next checkpoint.
- **Pivot**: move to a sibling or child subsystem, a new bug-class route, or a different phase when the current branch is stale.
- **Consolidate**: stop exploratory work and rewrite reusable knowledge into the research library, update the ledger, or close the branch as artifact-only.
- **Phase-shift**: use `workspace_phase --note ...` when the work has crossed from prepare to scan, scan to validation, validation to proof, or back to a prior phase.
- **Delegate-review**: spawn a goal-bounded auditor/debater to independently judge whether to deepen, pivot, consolidate, or de-escalate.

Intentional deep work is allowed, but the attention budget must be renewed by new evidence, a branch closure, a ledger milestone, or a timestamped phase note. Do not spend more than one attention interval in the same subsystem or phase without one of those renewals. Likewise, do not open more surfaces after a shallow-hopping warning until one branch has been deepened or consolidated.

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

#### Target Setup
Determine if a stable subsystem submodule relevant to this session activity already exists, and if not, create one. Use the associated submodule for durable security research: documenting architecture, trust boundaries, invariants, and cross-session knowledge as markdown, while placing raw supporting files in `artifacts/`. Avoid recreating similar submodules as it may cause duplicate work, but create child submodules when the research moves to a distinct subsystem.

Next, identify which installed domain pack owns the target method:

- Source/SAST: source repositories, existing decompiler output, optional codebase-memory graph queries, static reachability, guard dominance, and OpenGrep evidence.
- Binary: native binaries, firmware payloads, reverse engineering, crash replay, native instrumentation, and systems fuzzing.
- Web: web applications, APIs, sessions, browser state, tenants, and SaaS workflows.
- Cloud: AWS, Azure, GCP, IAM, storage, data plane, runtime metadata, workload identity, managed Kubernetes, and cloud network boundaries.
- Supply Chains: dependency graphs, package managers, CI/CD, artifact provenance, signing, containers, and release pipelines.
- Android: APK/DEX/resource reverse engineering, Android components, ADB/logcat/JDWP/Frida evidence, IPC, WebView, storage, and permissions.
- Apple Systems or Microsoft Systems: program-specific proof and mitigation rules.

Core creates the workspace and records durable knowledge; the active domain pack chooses the concrete tools, triage packet, and auditor catalog.

### 2. Scan
Go to this phase after the Prepare phase or when additional vulnerability discovery is required.

#### Surface Triage
Use the installed domain pack that matches the target. Produce a compact triage packet or evidence note that names the target slice, actor, trust boundary, controlled inputs, security invariant, suspect guard or sink, evidence already collected, and suggested auditor filters.

When source code or existing decompiler output is available, the Source pack can produce SAST, control-flow, and OpenGrep packets. When the target is web, cloud, supply-chain, binary, Android, Apple, or Microsoft-specific, use that pack's triage guidance before spawning auditors.

#### Hypothesize
Analyze previously conducted recon, threat modeling, research, and surface triage to come up with at least one new primitive or chain hypothesis. Pay close attention to multi-function, multi-file, multi-system security considerations. Magnetize toward code danger zones and security boundaries. Avoid duplicating previous hypotheses on the same software version.

#### Spawn Auditors
Before spawning a new auditor, search existing audit memory with `audit-helper.py --audit-search "<hypothesis boundary component>"`. If a prior assessment already covers the same boundary, reuse it, write a narrowed delta prompt, or update the ledger/research library instead of repeating the audit.

For each remaining hypothesis, spawn one or more targeted, goal-bounded auditor subagents with `maxtac-core-subagents` skill guidance to scan for unique vulnerabilities. Use the active domain pack's auditor MCP tools or local auditor helper output to select the narrowest suitable auditor set, usually 1-4 auditors. Avoid a broad "logic analysis" audit when a specific business logic, authorization, parser, race, memory safety, platform, supply-chain, or mitigation auditor fits. Each audit results in a hypothesis-evidence packet containing audit methods and security analysis stored in `workspace.sqlite` for later semantic lookup.

#### Update Findings
Based on audit results, use `maxtac-core-ledger` guidance to create or update findings. In most cases, audits result in findings in a `discovered` or `confident` state. Sometimes, an audit will surface evidence that demotes an existing finding to a `de-escalated` or `limited` state.

During scan, do not write unvalidated vulnerability claims into the research library as facts. Do update research markdown for stable system knowledge learned during the branch, especially architecture, reachability gates, authorization invariants, and negative results that will prevent future duplicate work. Keep speculative packets, broad match sets, and raw branch notes in `workspace.sqlite`, `tmp/`, or `artifacts/` until they are rewritten into book-like subsystem notes.

### 3. Validation
Go to this phase after the Scan phase or when additional pre-proofing validation is required.

#### Spawn Debaters
For each new finding or pre-proofing requirement, spawn three goal-bounded subagents with the `maxtac-core-subagents` skill to judge its validity. If the finding is a chain, also judge its reachability and exploitability. Each debater votes each finding as valid or invalid. Debate tallies are indexed into `workspace.sqlite`; use `debate-helper.py --list`, `--show`, or `--search` to review previous votes before promoting, de-escalating, or reopening the same proposition.

#### Update Findings
If at least two subagents vote invalid, go to the Scan phase where more auditing may be conducted, or the finding may be `de-escalated`. If at least two subagents vote valid, the finding is promoted to `validated` using `maxtac-core-ledger` guidance and update the research (see next section). Before any promotion action, search the finding ledger to determine if the finding already exists, and if it does, use `maxtac-core-ledger` guidance to mark the `duplicate` state. If the finding is original, move to the Proof phase.

#### Update Research
After promoting any finding to `validated`, evidence from its audit(s) is incorporated into the research workspace. Determine whether a stable subsystem submodule and markdown file already exists; if not, create them. Do not copy audit information directly; instead, rewrite the information into fluent library prose and link to exact audit or artifact evidence.

### 4. Primitive Proof
Go to this phase after the Validation phase completes with at least one valid non-duplicate finding.

#### Proof-of-Vulnerability (PoV) Primitive
Construct and execute an isolated proof-of-vulnerability (PoV) primitive that plausibly validates the vulnerable behavior, inputs, and pre-conditions. Primitive proofing is intentionally more lax than chain proofing. This stage is meant to prove a standalone flaw exists, but it does not guarantee a reportable chain. Spawn three goal-bounded debater subagents using `maxtac-core-subagents` guidance to vote whether the PoV reproduces the described primitive: `valid` or `invalid`.

#### Update Findings
If at least two subagents vote invalid, revise the PoV or use `maxtac-core-ledger` guidance to de-escalate the primitive as debunked or out-of-scope. Confirmed primitives are marked as proofed according to `maxtac-core-ledger` guidance, even if they are not reachable or exploitable. If a primitive cannot be proven nor debunked, it is marked as `limited`.

#### Update Research
After executing any primitive PoV, identify the stable subsystem markdown for the related system. These file system resources were likely already created during the Validation phase flow; however, if there was a deletion or mistake, they may be recreated. For negative results, rewrite stale or invalid information to prevent confusing search results. For positive results, do not overwrite information that may be important later; append a concise library update and link to proof artifacts.

#### Chain Planning
For each proven primitive, first analyze whether the primitive is exploitable and reachable as a standalone chain. If so, no further scanning is needed; a validated chain may be created based on the single primitive, then go to the Chain Proof phase. If the primitive is not reachable or exploitable on its own, use creative thinking to generate at least two chains and their hypotheses. If all chain primitives are already proven, go to the Chain Proof phase; otherwise, go to the Scan phase to audit the chain gaps.

### 5. Chain Proof
Go to this phase after a Primitive Proof or Scanning phase results in one or more validated chains.

#### Proof-of-Vulnerability (PoV) Chain
For each validated chain, create and execute a realistic end-to-end proof-of-vulnerability (PoV) reproduction of the vulnerability. The PoV must not mock any portion of the chain. The PoV chain must be reachable from a non-self or security sandboxed vector. The PoV chain must demonstrate an exploitable vulnerability that is not documented as an accepted risk or shared responsibility. Spawn three goal-bounded debater subagents using `maxtac-core-subagents` guidance to vote whether the PoV reproduces the described chain: `valid` or `invalid`.

#### Update Findings
If at least two subagents vote invalid, revise the PoV or use `maxtac-core-ledger` guidance to de-escalate the chain. If at least two subagents vote the PoV as valid, promote it to `proofed`. After marking a PoV as `proofed`, write a submission-ready report which includes it.

#### Update Research
After executing any chain PoV, identify the stable subsystem markdown file(s) for every related subsystem. Since chains combine primitives, research may span multiple submodules or markdown files. These resources were likely created during the Validation or Primitive Proof phase flows; however, if there was a deletion or mistake, they may be recreated. For negative results, rewrite stale or invalid information to prevent confusing search results. For positive results, append concise library updates and link to proof artifacts without burying the chain inside a session-named folder.

### 6. Reporting
Go to this phase after Chain Proof produces at least one proofed chain with accepted evidence.

Run `workspace_report_ready` or `python3 <skill-dir>/scripts/workspace.py report-ready` before drafting or finalizing a submission report. If the helper reports missing proof, scope, ledger, or phase evidence, return to the phase that can produce the missing artifact.

For bounded reviews, source scans, or handoffs, use `maxtac-core-contracts` to create and validate a canonical result bundle under `contracts/` before drafting prose. The contract should preserve findings, evidence references, coverage decisions, limitations, and deterministic report output.

Write submission-ready reports under `<workspace-root>/reporting/`. Reports should be based on proofed chains, not standalone primitives. Include the validated chain summary, attacker reachability, exploitability, affected versions or targets, reproduction steps, observed impact, proof artifacts, limitations, and any program-specific evidence requirements.
