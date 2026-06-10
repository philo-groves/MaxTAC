---
name: maxtac-core-workflow
description: Orchestration for vulnerability research workflows. Includes a standard directory structure, research phases to work through, and instructions for proper analysis.
---

# MaxTAC Core Workflow

Use this skill as the primary workflow controller. MaxTAC is for authorized vulnerability analysis and proofing. The workflow aggressively utilizes the verified Trusted Access for Cyber (TAC) membership of plugin users and their expanded range of OpenAI cyber capabilities. Do not negatively affect other users or external resources unless given direct permission.

## Directory Structure
The following files and directories are managed under the `data/maxtac/` relative directory:

```
program-info.md    # authorized scope and exclusions
primitives.json    # individual findings (primitives) of all states
chains.json        # combined findings (chains) of all states
research/          # scalable markdown research library
debates/           # debater subagent results
audits/            # auditor subagent results
proof/             # proof-of-concept (PoC) development
```

## Research Workspace
MaxTAC is designed as a modular research workspace meant to scale for scopes of any size, continuously building a knowledge base that provides better context than most security researchers traditionally have access to. Models often persist every research file to the base directory, or fail to persist important knowledge at all; this guidance prevents that behavior.

### Submodule Structure

The base module exists at `data/maxtac/research/`, containing a hierarchy of agent-driven submodules. Each submodule contains one or more markdown files which act as the knowledge base for that localized system. For non-markdown files related to any submodule, persist them to a submodule-relative `artifacts/` directory. Submodules may have their own child submodules. There is no child submodule limit.

Example Submodule:
```
artifacts/
example-submodule/
another-submodule-same-module/
example-research.md
more-research-same-module.md
```

### Naming Conventions
Due to search noise and loss in large research workspaces, naming is more important than it may seem. Submodule directory names should label the localized system that is being researched. Markdown file names should label the subsystem the module that is being documented. Avoid timestamps, dates, and internal identifiers in names.

Example submodules: `apple-intelligence` with a `apple-foundation-models` submodule; `edge` with an `edge-app-container` submodule.

Example markdown: `amf-3-core-model.md`, `amf-3-core-advanced-model.md`, `pcc-server-model.md` in an `apple-foundation-models` submodule; `browser-process.md`, `renderer-process.md`, `extension-system.md` in an `edge-app-container` submodule.

### Large Markdown
A large markdown file is a sign that a single document should be broken into a submodule. If a large markdown file (> 300 lines) is found, create the new submodule and rewrite the large markdown core information under several research files. Also copy any relevant artifacts into the new submodule. Only after verifying the key information was transcribed, delete the old markdown file and old artifacts.

## Research Phases

The workflow is optimized for three primary goals:

1. Build a scalable security knowledge base of the program and technology.
2. Identify and verify individual code or system flaws known as primitives.
3. Combine primitives into chains with proven reachabilty and exploitability.

### 1. Prepare

Go to this phase at the start of the workflow or when additional threat modeling is required.

#### First Run Setup
Assume the first run is active if `data/maxtac/program-info.md` does not exist. Ingest the program information to `data/maxtac/program-info.md` as a preliminary step. Use `assets/program-info.template.md` relative to this skill as a template and fill in the missing pieces. Key information is usually publicly available via an official site: MSRC, Apple Security, Google VRP, Meta Security, HackerOne, and Bugcrowd program information is accessible on their public websites.

#### Target Setup
Determine if a submodule relevant to this session activity already exists, and if not, create a submodule. Use the associated submodule for persisting security research: documenting markdown and creating child submodules as needed. Avoid recreating similar submodules as it may cause duplicate work. 

Next, categorize the current session target; this category is used throughout the workflow for research alignment.
- Source Code: A repository or project workspace is available for exploration.
- Binary: One or more binaries are provided and reverse engineering is expected.

Use this category with `maxtac-core-preparation` skill guidance to perform recon and threat modeling.

### 2. Scan
Go to this phase after the Prepare phase or when additional vulnerability discovery is required.

#### Hypothesis
Analyze previously conducted recon, threat modeling, and research to come up with at least one new primitive or chain hypothesis. Pay close attention to multi-function, multi-file, multi-system security considerations. Magnetize toward code danger zones and security boundaries. Avoid duplicating previous hypotheses on the same software version.

#### Spawn Auditors
For each hypothesis, spawn one or more auditor subagents with `maxtac-core-subagent-audit` skill guidance to scan for unique vulnerabilities. Each audit results in a hypothesis-evidence packet containing audit methods and security analysis. Audit results are stored in the `maxtac/data/audits/` directory.

#### Record Findings
Based on audit results, use `maxtac-core-finding-ledger` guidance to create or update findings. In most cases, audits result in findings in a `discovered` or `confident` state. Sometimes, an audit will surface evidence that demotes an existing finding to a `de-escalated` or `limited` state. Only update `research/` markdown or submodules in the scan phase if it relates to a finding demotion; research for new findings is persisted after validation.

### 3. Validate & Dedupe
Go to this phase after the Scan phase or when additional pre-proofing validation is required.

For each new finding from the scan hypotheses and evidence, spawn three subagents with the `maxtac-core-subagent-debate` skill to judge its validity. If the finding is a chain, also judge its reachability and exploitability. Each debater votes each finding as valid or invalid. If at least two subagents vote invalid, more scanning may be conducted or the finding may be de-escalated. If at least two subagents vote valid, the finding is promoted to validated using `maxtac-core-finding-ledger` guidance. After a majority validation, perform semantic analysis of the finding ledger to determine if the finding already exists, and if it does, use `maxtac-core-finding-ledger` guidance to mark the duplicate. If the finding is original, move to the Proof phase.

### 4a. Primitive Proof
Go to this phase after the Validate & Dedupe phase completes with at least one valid non-duplicate finding.

Construct and execute an isolated primitive proof-of-concept (PoC) that plausibly validates the vulnerable behavior, inputs, and pre-conditions. Primitive proofing is intentionally more lax than chain proofing. This stage is meant to prove a standalone flaw exists, but it does not guarantee a reportable chain. Spawn three debater subagents using `maxtac-core-subagent-debate` guidance to vote whether the PoC reproduces the described primitive: valid or invalid. If at least two subagents vote invalid, revise the PoC or use `maxtac-core-finding-ledger` guidance to de-escalate the primitive as debunked or out-of-scope. Confirmed primitives are marked as proofed according to `maxtac-core-finding-ledger` guidance, even if they are not reachable or exploitable. If a primitive cannot be proven nor debunked, it is marked as limited.

### 4b. Chain Proof
Go to this phase after the Primitive Proof phase completes with at least one confident or proven primitive.

For each proven primitive finding, create at least two hypotheses for combining findings into a chain with attacker-reachable impact. Backtrack through other research phases as required to analyze and prove each chain with an end-to-end PoC, including the spawn of additional auditor subagents or additional primitive research. Validation is performed through standard methods such as crash, panic, and system log evidence. After the evidence is collected, spawn three debater subagents using `maxtac-core-subagent-debate` guidance to vote whether the PoC reproduces the described vulnerability: valid or invalid. If at least two subagents vote invalid, revise the PoC or use `maxtac-core-finding-ledger` guidance to de-escalate the chain. If at least two subagents vote the PoC as valid, promote it to proofed. After marking a PoC as proofed, write a submission-ready report which includes it.