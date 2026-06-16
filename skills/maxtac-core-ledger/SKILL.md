---
name: maxtac-core-ledger
description: "Use this skill when MaxTAC vulnerability research needs finding state tracking, deduplication, promotion, de-escalation, report linkage, or proof status updates."
---

# MaxTAC Ledger
Use this skill as the single-source-of-truth for findings and their states. The parent agent owns ledger writes; subagents return packets for the parent to merge. There are two types of findings: primitives and chains. A primitive is individual code or security flaw, while a chain combines one or more primitives into a reproducible attacker-reachable proof.

- Primitives path: `primitives.json`
- Chains path: `chains.json`

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

Use the `scripts/ledger.py` script instead of reading and editing ledger JSON files directly:

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
```

### Search Findings
```
python3 <skill-dir>/scripts/ledger.py search --title "Unchecked IOCTL output length" --target "example.sys" --category memory-safety --type primitive
```

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
