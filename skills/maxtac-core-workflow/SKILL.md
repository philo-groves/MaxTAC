---
name: maxtac-core-workflow
description: Orchestration for vulnerability research workflows. Includes a standard directory structure, research phases to work through, and instructions for proper analysis.
---

# MaxTAC Core Workflow

Use this skill as the primary workflow controller. MaxTAC is for authorized vulnerability analysis and proofing. The workflow aggressively utilizes the verified Trusted Access for Cyber (TAC) membership of plugin users and their expanded range of OpenAI cyber capabilities. Do not negatively affect other users or external resources unless given direct permission.

## Directory Structure
The following files and directories are managed under the `data/maxtac/` relative directory:

- `program-information.json`: A long-living program information packet which contains authorized scope, bounty eligibility, out-of-scope exclusions, expected vulnerability priorities, and proofing standards. Create this during the first research session and refresh it upon request.
- `primitives.json`: A single-source-of-truth for primitives of all states, managed using the `maxtac-core-finding-ledger` skill and its `ledger.py` script.
- `chains.json`: A single-source-of-truth for chains of all states, managed using the `maxtac-core-finding-ledger` skill and its `ledger.py` script.
- `research/`: A markdown research library broken into domains and targets. Domains are high-level research categories, and targets are the topics of specific research efforts within each category.
- `debates/`: Debater subagent results, managed using the `maxtac-core-subagent-debate` skill.
- `proof/`: PoC development, intentionally kept separate from research to prevent search bloat.
- `reports/`: Reports written, intentionally kept separate to make report searching easier.
- `static/`: Static analysis storage for opengrep and other related files.

## Research Phases

Work through five phases in any order: prepare, scan, validate, dedupe, and proof.

### 1. Prepare

Go to this phase at the start of the workflow or when additional threat modeling is required.

#### First Run Preparation
On the first run, ingest the program information to `data/maxtac/program-information.json` as a preliminary step. This is usually publicly available via a known official site: MSRC, Apple Security, HackerOne, and Bugcrowd program information is accessible on their public websites. Include all details described in "Directory Structure" above. From the program information, create `data/maxtac/research/` directories for a maximum of ten domains to research targets within for vulnerabilities.

#### Target Category Preparation
The first real preparation step is to identify the domain and target for the current session. If existing research exists for the domain or target, it should be built upon. Avoid recreating similar domain or target labels as it may cause duplicate work. 

Next, categorize the current session target; this category is used throughout the workflow for research alignment.
- Source Code: A repository or project workspace is available for exploration.
- Binary: One or more binaries are provided and reverse engineering is expected.

Use this category with `maxtac-core-preparation` skill guidance to perform recon and threat modeling.

### 2. Scan
Go to this phase after the Prepare phase or when additional vulnerability discovery is required.

Based on the existing phase(s), establish at least one new hypothesis. For each hypothesis, spawn multiple auditor subagents with `maxtac-core-subagent-audit` skill guidance to scan for a specific vulnerability. Each subagent returns a hypothesis-evidence packet for debater validation. For each promising packet, use `maxtac-core-finding-ledger` guidance to add the finding as discovered or confident.

### 3. Validate & Dedupe
Go to this phase after the Scan phase or when additional pre-proofing validation is required.

For each new finding from the scan hypotheses and evidence, spawn three subagents with the `maxtac-core-subagent-debate` skill to judge its validity. If the finding is a chain, also judge its reachability and exploitability. Each debater votes each finding as valid or invalid. If at least two subagents vote invalid, more scanning may be conducted or the finding may be de-escalated. If at least two subagents vote valid, the finding is promoted to validated using `maxtac-core-finding-ledger` guidance. After a majority validation, perform semantic analysis of the finding ledger to determine if the finding already exists, and if it does, use `maxtac-core-finding-ledger` guidance to mark the duplicate. If the finding is original, move to the Proof phase.

### 4. Primitive Proof
Go to this phase after the Validate & Dedupe phase completes with at least one valid non-duplicate finding.

Construct and execute an isolated primitive proof-of-concept (PoC) that plausibly validates the vulnerable behavior, inputs, and pre-conditions. Primitive proofing is intentionally more lax than chain proofing. This stage is meant to prove a standalone flaw exists, but it does not guarantee a reportable chain. Spawn three debater subagents using `maxtac-core-subagent-debate` guidance to vote whether the PoC reproduces the described primitive: valid or invalid. If at least two subagents vote invalid, revise the PoC or use `maxtac-core-finding-ledger` guidance to de-escalate the primitive as debunked or out-of-scope. Confirmed primitives are marked as proofed according to `maxtac-core-finding-ledger` guidance, even if they are not reachable or exploitable. If a primitive cannot be proven nor debunked, it is marked as stalled.

### 5. Chain Proof
Go to this phase after the Primitive Proof phase completes with at least one confident or proven primitive.

For each proven primitive finding, create at least two hypotheses for combining findings into a chain with attacker-reachable impact. Backtrack through other research phases as required to analyze and prove each chain with an end-to-end PoC, including the spawn of additional auditor subagents or additional primitive research. Validation is performed through standard methods such as crash, panic, and system log evidence. After the evidence is collected, spawn three debater subagents using `maxtac-core-subagent-debate` guidance to vote whether the PoC reproduces the described vulnerability: valid or invalid. If at least two subagents vote invalid, revise the PoC or use `maxtac-core-finding-ledger` guidance to de-escalate the chain. If at least two subagents vote the PoC as valid, promote it to proofed. After marking a PoC as proofed, write a submission-ready report which includes it.