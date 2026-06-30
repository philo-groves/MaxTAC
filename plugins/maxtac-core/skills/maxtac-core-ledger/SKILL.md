---
name: maxtac-core-ledger
description: "Use this skill when MaxTAC vulnerability research needs finding state tracking, deduplication, promotion, de-escalation, report linkage, or proof status updates."
---

# MaxTAC Ledger
Use this skill as the single-source-of-truth for findings and their states. The parent agent owns ledger writes; subagents return packets for the parent to merge. There are two types of findings: primitives and chains. A primitive is individual code or security flaw, while a chain combines one or more primitives into a reproducible attacker-reachable proof.

The ledger tracks finding state; it is not a replacement for the research library. When a ledger milestone records durable subsystem knowledge, a confirmed negative result, or an architectural invariant, also rewrite that knowledge into the relevant `research/` markdown file and link the ledger entry to the supporting artifact.

Ledger updates are also part of the MaxTAC attention cadence. If a branch produces a promote, de-escalate, duplicate, limited, or no-finding decision, record that decision as a finding update or milestone instead of letting the next session infer it from old artifacts. These timestamps help distinguish useful deep work from tunnel vision.

For MaxTAC thin closure, update the ledger only when a primitive or chain candidate already exists or the branch produced a reusable candidate worth tracking as `limited` or `de-escalated`. Do not create a noisy primitive row for every tiny no-issue helper. In no-finding thin closures, the result contract coverage and corpus `closure` note are the durable closure record.

Before broad negative closure, run a primitive graveyard pass. List every `de-escalated` and `limited` primitive related to the target, then review it as if trying to resurrect it with new caller, patch-diff, model, fuzzing, binary, or chain-composition evidence. Add a milestone to each reviewed primitive with either the reopen evidence or the specific reason it remains closed. Do not let "caller-context" or "non-setuid" become a reusable solvent without a caller-search or authority-boundary receipt.

- Workspace database: `workspace.sqlite`
- Legacy imports: existing `primitives.json` and `chains.json` are imported into `workspace.sqlite` when the database is first created.
- Subagent memory: the same database stores and indexes debate tallies and audit assessments for fast lookup.

## Initialize the Ledger
At the start of the research session, if no finding ledger exists, create it with: `python3 <skill-dir>/scripts/ledger.py init`

## Primitives
Primitives are individual security flaws. A proven primitive does not guarantee a reportable vulnerability. For example, many memory corruption primitives are not exploitable due to ASLR and other defense-in-depth mitigations. Those findings should not be de-escalated because their flaws are real and a bypass, such as additional memory disclosure primitive, may be found later.

## Chains
Chains combine one or more confident or proven primitives for greater impact and reportability. A chain is not proven until it is confirmed to be reachable and exploitable by an attacker through an end-to-end PoV. Only chains have associated reports; if a single primitive exploits a vulnerability, it should still have a chain created and proven.

## Finding States
These states are valid for both primitives and chains.

- `discovered`: plausible candidate but no direct evidence yet.
- `confident`: plausible candidate and direct evidence exists.
- `validated`: primitive passes validity debater votes, or chain passes reachability/exploitability.
- `proofed`: PoV reproduced with accepted evidence and a validated proof packet.
- `duplicate`: same root cause or security boundary as another primitive, or the same primitive combination as another chain.
- `limited`: cannot be promoted to proofed, but cannot be de-escalated either; potential chain primitives or incomplete chains.
- `de-escalated`: debunked if the finding is invalid, or out-of-scope if excluded from program eligibility.

## Script Usage

Use the `scripts/ledger.py` script instead of reading and editing ledger storage directly:

Keep promotions backed by ledger records and use `scripts/ledger.py` as the canonical Core ledger interface.

### Initialize the Ledger
```
python3 <skill-dir>/scripts/ledger.py init
```

### Summarize the Ledger

```
python3 <skill-dir>/scripts/ledger.py summary --type chain
```

### List Findings
```
python3 <skill-dir>/scripts/ledger.py list --type chain
python3 <skill-dir>/scripts/ledger.py list --type primitive --state de-escalated
python3 <skill-dir>/scripts/ledger.py list --type primitive --state limited
```

### Search Findings
```
python3 <skill-dir>/scripts/ledger.py search --title "Unchecked IOCTL output length" --target "example.sys" --category memory-safety --type primitive
```

Use semantic SQLite search when the query is exploratory or spans title, target, category, locations, evidence, related IDs, primitive links, and milestones:

```
python3 <skill-dir>/scripts/ledger.py search --semantic "tenant export guard proof" --type all
```

Before deciding a finding is novel, also search prior audit and debate memory through `maxtac-core-subagents` helper commands when the question may have already been assessed:

```
python3 <core-subagents-skill-dir>/scripts/audit-helper.py --root <workspace-root> --audit-search "tenant export guard proof"
python3 <core-subagents-skill-dir>/scripts/debate-helper.py --root <workspace-root> --search "tenant export guard proof"
```

### Migrate Legacy JSON

```
python3 <skill-dir>/scripts/ledger.py migrate --root <workspace-root>
```

Use `--replace` only when the legacy JSON files should overwrite existing DB findings.

### Add a Finding
```
python3 <skill-dir>/scripts/ledger.py add --title "Unchecked IOCTL output length" --target "example.sys" --category memory-safety --location "DeviceControl 0x222004" --summary "..." --evidence "..." --type primitive
```

### Update a Finding
```
python3 <skill-dir>/scripts/ledger.py update M-0001 --state confident --note "Debaters accepted low-privileged IOCTL reachability and kernel write primitive."  --type primitive
```

### Append a Milestone
```
python3 <skill-dir>/scripts/ledger.py milestone M-0001 --note "Negative control shows METHOD_BUFFERED path is safe." --type primitive
```
