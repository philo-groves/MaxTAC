---
name: maxtac-auditor-router
description: Select and prepare MaxTAC specialized Auditor subagent packets for XNU, Windows kernel-adjacent, binary patch-diff, crash root-cause, fuzzability, and open-source systems targets. Use after maxtac-prepare has created a target profile or when choosing per-bug-type Auditor agents.
---

# MaxTAC Auditor Router

Use this skill to choose Auditor agents from the systems-focused catalog and create sealed investigation packets. The initial catalog does not include browser/API application auditors and intentionally excludes Linux kernel work.

## Catalog

Read `references/auditor-catalog.yaml` when selecting Auditors. It defines:

- `platforms`, `target_kinds`, `surfaces`, and `bug_classes`
- required inputs and output expectations
- negative routing rules such as `disabled_for`
- prompt focus for each Auditor

## Selection Workflow

1. Load `data/maxtac/target-profile.json`.
2. Use `scripts/select_auditors.py` to rank matching catalog entries:

```bash
python <skill-dir>/scripts/select_auditors.py --profile data/maxtac/target-profile.json --limit 6 --format markdown
```

3. Prefer 3-8 Auditors per discovery wave.
4. Avoid duplicate Auditors that inspect the same files and boundary unless the second pass has a different bug class.
5. Create one packet per Auditor under `data/maxtac/auditor-packets/`.
6. Spawn subagents only when the user requested MaxTAC/multi-agent/delegated work and subagent tools are available. Otherwise, run packets sequentially.

## Packet Shape

Each packet should include:

```text
Auditor id:
Objective:
Scope brief:
Target profile excerpts:
Allowed operations:
Exact files, binaries, symbols, logs, or diffs:
Focus surfaces:
Bug classes:
Search seeds or tools:
Do not do:
Output schema:
```

Tell Auditors to return candidates only. They must not update `data/maxtac/findings.json`.

## Auditor Output Schema

Require concise JSON or Markdown with these fields:

```json
{
  "auditor": "windows-driver-ioctl-auditor",
  "claim": "...",
  "affected_surface": "...",
  "entrypoint": "...",
  "attacker_control": "...",
  "missing_guard": "...",
  "impact": "...",
  "evidence": ["..."],
  "confidence": "low|medium|high",
  "validation_steps": ["..."],
  "deescalation_reason": null
}
```

## Routing Notes

- XNU source targets usually start with IOKit/MIG, VFS/sandbox, memory/lifetime, and parser Auditors.
- Windows targets usually start with driver IOCTL, object/token, memory, and filesystem filter Auditors when artifacts support them.
- Binary-only targets usually start with binary patch diff, crash root cause, native parser fuzzability, and generic systems code Auditors.
- Open-source native targets usually start with OSS systems code, native parser fuzzability, memory/lifetime, and file/path surfaces.
- If the target is Linux kernel or a web application, record that it is outside the initial MaxTAC Auditor family and ask whether to route through another plugin or an explicit custom packet.
