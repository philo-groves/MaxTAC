---
name: maxtac-core-subagents
description: "Use this skill when MaxTAC research needs goal-bounded auditor subagents, verifier debate subagents, specialist bug-class review, mitigation review, or independent votes on a vulnerability hypothesis or PoV."
---

## Parallel or Sequential
Use this guidance before spawning any group of auditor or debater subagents. Ideally, subagents would always run in parallel, but system resources sometimes prevent that. When resources are limited, subagents must be spawned sequentially to prevent RAM overload. Otherwise, subagents may be spawned in parallel.

Debater agents are always spawned in groups of three, so the parallel vs sequential decision is especially important for them. Auditor agents are spawned in groups of any size; the maximum number of auditors is 6, the Codex limit.

Use the active Python executable for helper scripts. If `python` is not on PATH in Codex Desktop, call `codex_app.load_workspace_dependencies` and use the bundled Python executable it returns.

To determine whether to spawn subagents in parallel or sequentially, run:
```
python <skill-dir>/scripts/readiness-check.py --kind auditor --subagents <count>
python <skill-dir>/scripts/readiness-check.py --kind debater --subagents <count>
```

Use the local helper scripts for readiness checks, prompt enrichment, and debate ballot validation. Domain packs may expose auditor catalogs through MCP tools; the parent still owns final summaries.

The script prints `parallel` or `sequential` after checking available system resources against the requested subagent count. It reserves 4 GiB of available memory per requested subagent plus 1 GiB of headroom. Auditor subagents have an additional safety gate: if total system RAM is unknown or below 17 GiB, auditor readiness returns `sequential` regardless of available memory. Debaters and generic subagents are unaffected by the 17 GiB total-RAM gate.

If the result is `parallel`, spawn subagents using standard Codex subagent spawning mechanisms without waiting for each to finish. If the result is `sequential`, spawn one subagent at a time, waiting for it to finish before spawning the next.

## Goal-Bounded Subagent Runs
Always spawn auditor and debater subagents with a Codex goal prompt, not only a task prompt. Do not spawn a MaxTAC subagent from a raw audit or debate prompt. First run `audit-helper.py --prompt-file`, `debate-helper.py --prompt-file`, `audit_prompt_create`, or `debate_prompt_create`, then pass the enriched prompt to the subagent unchanged.

The enriched prompt must make goal activation the first action. The subagent's first tool call should be `create_goal` when available; if `create_goal` is unavailable but slash commands are available, the subagent should send `/goal ...` before doing any analysis. The goal must include a positive objective and a negative end outcome: the positive objective names the useful artifact the subagent should produce, while the negative end outcome names when the subagent should stop and persist blockers instead of expanding scope.

The generated prompt also requires a visible goal-activation record in the persisted artifact. Audit assessments must include a `Goal Activation` section. Debate ballots must include a `goal_activation` field with `create_goal`, `/goal`, or `unavailable`. Treat a missing goal-activation record as a prompt or execution defect to remediate before trusting the subagent result.

Bound each subagent goal tightly enough to avoid long-running drift but wide enough to be useful. For auditors, bound the goal to one hypothesis, one auditor specialty, the supplied packet/evidence, directly referenced files/functions, and immediately necessary callers/callees. For debaters, bound the goal to one binary proposition and the supplied or directly referenced evidence. Subagents must not broaden into repo-wide discovery, new fuzzing campaigns, new PoV construction, or unrelated refactors unless the prompt explicitly grants that scope.

## Attention Review Subagents
When `workspace_status` reports an attention-lock warning, the parent may spawn a single goal-bounded auditor as an independent attention reviewer. The prompt should include the attention report, current phase, recent ledger summary, active branch, and the exact decision options: deepen, pivot, consolidate, phase-shift, or delegate-review. Use `audit-helper.py --prompt-file` or `audit_prompt_create`; do not spawn the reviewer from a raw prompt. The reviewer should persist an assessment under `audits/` that recommends one action and names the evidence or absence of evidence behind it.

## Auditor Subagents
An auditor subagent is a specialist vulnerability researcher for an individual bug class, mitigation, program, or other security topic. Core owns the goal-bounded prompt, persistence, and debate mechanics. Installed domain packs own most auditor catalogs.

### Auditor Flow
Every audit follows the same 5-step flow.

1. **Choose the auditor**: prefer the active domain pack's auditor MCP tools, such as Web, Binary, Supply Chains, Android, Apple Systems, or Microsoft Systems auditor list/filter/show tools. If no domain pack provides a suitable auditor, Core includes a small fallback catalog in `<skill-dir>/references/auditors.json`. Do not read the JSON file directly; instead, run:

```
python <skill-dir>/scripts/audit-helper.py --list
python <skill-dir>/scripts/audit-helper.py --filter <filter>
python <skill-dir>/scripts/audit-helper.py --show <auditor id>
```

Each of the above scripts results in one or more fallback auditors. The `--list` and `--filter` options print condensed information for a list of auditors, while the `--show` option prints the full markdown instructions for a specific auditor. When a domain triage packet suggests auditor filters, use those filters against the matching domain pack first.

Prefer focused auditors over broad review. For example, use a specific `logic-*` auditor for authentication state, entitlement, replay, approval, tenant relationship, destructive action, AI-agent authority, or specification drift instead of asking for generic logic analysis. Use generic business logic only when the target is truly workflow-centered and no narrower logic auditor fits.

2. **Write the audit prompt**: after reading the specialist usage and related markdown, write a prompt for its subject matter and the current target. Do not use the specialist markdown directly as a prompt; instead, adapt its guidance for the current context. Persist the prompt draft to `<workspace-root>/tmp/`, then run:

```
python <skill-dir>/scripts/audit-helper.py --root <workspace-root> --prompt-file tmp/<prompt-name>.md
```

The above script prints an enriched prompt; enrichment prepends Codex goal instructions and appends instructions to persist audit assessment files to `<workspace-root>/audits/<audit-id>/`. The script also creates the `<workspace-root>/audits/<audit-id>/` directory, then persists the subagent prompt there.

Include the triage packet, relevant graph evidence, OpenGrep result summaries, and exact file/function references in the prompt. Omit unrelated checklist text and avoid asking the auditor to rediscover the whole target.

3. **Spawn the auditor**: use the enriched prompt unchanged, including its first-action goal activation instructions, to spawn the auditor subagent. There is no script for this phase; use standard Codex subagent spawning mechanisms. If the session is at maximum subagents and one is stopped, replace a stopped subagent. See the "Parallel or Sequential" section above for parallelism guidance.

4. **Wait for the auditor**: during the wait, continue normal operations as the main agent in parallel, even for serial subagent spawns. During its work, the subagent persists evidence to `<workspace-root>/audits/<audit-id>/`.

5. **Complete the audit**: after the auditor subagent finishes its work, verify `<workspace-root>/audits/<audit-id>/assessment.md` was persisted by the subagent. If not, quickly remediate by reviewing the subagent session and persisting a proper assessment.

## Debater Subagents
A debater subagent reviews a debate topic, then votes on a ballot and explains its reasoning.

### Debater Flow
Every debate follows the same 5-step flow.

1. **Write the debate prompt**: write a prompt for the debate topic. Since each debater must rate yes or no, the prompt requires a precise binary proposition: "yes means X, no means Y." Persist the prompt draft to `<workspace-root>/tmp/`, then run:

```
python <skill-dir>/scripts/debate-helper.py --root <workspace-root> --prompt-file tmp/<prompt-name>.md
```

The above script prints an enriched prompt; enrichment prepends Codex goal instructions and appends instructions to persist debate ballot files to `<workspace-root>/debates/<debate-id>/`. The script also creates the `<workspace-root>/debates/<debate-id>/` directory, then persists the subagent prompt there.

2. **Spawn debater subagents**: use the enriched prompt unchanged, including its first-action goal activation instructions, to spawn three debater subagents. There is no script for this phase; use standard Codex subagent spawning mechanisms. If the session is at maximum subagents and one is stopped, replace a stopped subagent. See the "Parallel or Sequential" section above for parallelism guidance.

3. **Wait for the debaters**: during the wait, continue normal operations as the main agent in parallel, even for serial subagent spawns. Each subagent persists its ballot to `<workspace-root>/debates/<debate-id>/ballot-<subagent-name>.json`, with a JSON structure as follows:

```
{
  "debate": "debate-id",
  "subagent": "subagent-name",
  "goal_activation": "create_goal",
  "choice": "yes",
  "confidence": 85,
  "reasoning": "detailed reasoning for the choice",
  "evidence": "detailed evidence supporting the reasoning",
  "blockers": "nullable; any blockers or concerns about the debate topic"
}
```

4. **Complete the debate**: after the debater subagents finish their work, verify `<workspace-root>/debates/<debate-id>/ballot-<subagent-name>.json` was persisted by each subagent. If not, quickly remediate by reviewing the subagent session(s) and persisting appropriate ballot(s).

5. **Tally the debate**: after all ballots are persisted, tally the debate by reviewing each ballot and writing a summary of the results, including which side won and why, supported by evidence from the ballots. Persist the machine totals to `<workspace-root>/debates/<debate-id>/tally.json`, the ballot-by-ballot review to `<workspace-root>/debates/<debate-id>/tally.md`, and the parent-facing summary to `<workspace-root>/debates/<debate-id>/summary.md`. To generate these outputs, run:

```
python <skill-dir>/scripts/debate-helper.py --root <workspace-root> --debate <debate-id> --tally
```

The parent agent owns the final decision. Review `summary.md` against `tally.md` and the source ballots before using the result for a ledger state transition.
