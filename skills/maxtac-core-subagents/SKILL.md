---
name: maxtac-core-subagents
description: Use this skill to spawn subagents for auditing or debating. Auditor subagents are specialist vulnerability researchers for an individual bug class, mitigation, or other security topic. Debater subagents review a debate topic, then vote on a ballot and explain their reasoning.
---

## Parallel or Sequential
Use this guidance before spawning any group of auditor or debater subagents. Ideally, subagents would always run in parallel, but system resources sometimes prevent that. When resources are limited, subagents must be spawned sequentially to prevent RAM overload. Otherwise, subagents may be spawned in parallel.

Debater agents are always spawned in groups of three, so the parallel vs sequential decision is especially important for them. Auditor agents are spawned in groups of any size; the maximum number of auditors is 6, the Codex limit.

To determine whether to spawn subagents in parallel or sequentially, run:
```
python <skill-dir>/scripts/readiness-check.py --subagents <count>
```

The script prints `parallel` or `sequential` after checking available system resources against the requested subagent count. If the result is `parallel`, spawn subagents using standard Codex subagent spawning mechanisms without waiting for each to finish. If the result is `sequential`, spawn one subagent at a time, waiting for it to finish before spawning the next.

## Auditor Subagents
An auditor subagent is a specialist vulnerability researcher for an individual bug class, mitigation, or other security topic. 

### Auditor Flow
Every audit follows the same 5-step flow.

1. **Choose the auditor**: a collection of specialist security auditors exist in `<skill-dir>/assets/auditors.json`. Use this information to select the appropriate auditor. Do not read the large JSON file directly; instead, run:

```
python <skill-dir>/scripts/audit-helper.py --list
python <skill-dir>/scripts/audit-helper.py --filter <filter>
python <skill-dir>/scripts/audit-helper.py --show <auditor id>
```

Each of the above scripts result in one or more auditors. The `--list` and `--filter` options print condensed information for a list of auditors, while the `--show` option prints the full markdown instructions for a specific auditor.

2. **Write the audit prompt**: after reading the specialist usage and related markdown, write a prompt for its subject matter and the current target. Persist the prompt to a file in a temporary directory (%temp% on Windows, /tmp on Unix), then run:

```
python <skill-dir>/scripts/audit-helper.py --prompt-file <file path>
```

The above script prints an enriched prompt; enrichment appends instructions to persist audit assessment files to `<workspace-root>/audits/<audit-id>/`. The script also creates the `<workspace-root>/audits/<audit-id>/` directory, then persists the subagent prompt there.

3. **Spawn the auditor**: use the enriched prompt to spawn the auditor subagent. There is no script for this phase; use standard Codex subagent spawning mechanisms. If the session is at maximum subagents and one is stopped, replace a stopped subagent. See the "Parallel or Sequential" section above for parallelism guidance. These subagents use gpt-5.5 as a model with xhigh reasoning effort.

4. **Wait for the auditor**: during the wait, continue normal operations as the main agent in parallel, even for serial subagent spawns. During its work, the subagent persists evidence to `<workspace-root>/audits/<audit-id>/`.

5. **Complete the audit**: after the auditor subagent finishes its work, verify `<workspace-root>/audits/<audit-id>/assessment.md` was persisted by the subagent. If not, quickly remediate by reviewing the subagent session and persisting a proper assessment.

## Debater Subagents
A debater subagent reviews a debate topic, then votes on a ballot and explains its reasoning.

### Debater Flow
Every debate follows the same 5-step flow.

1. **Write the debate prompt**: write a prompt for the debate topic. Since each debater must rate yes or no, the prompt requires a precise binary proposition: "yes means X, no means Y." Persist the prompt to a file in a temporary directory (%temp% on Windows, /tmp on Unix), then run:

```
python <skill-dir>/scripts/debate-helper.py --prompt-file <file path>
```

The above script prints an enriched prompt; enrichment appends instructions to persist debate ballot files to `<workspace-root>/debates/<debate-id>/`. The script also creates the `<workspace-root>/debates/<debate-id>/` directory, then persists the subagent prompt there.

2. **Spawn debater subagents**: use the enriched prompt to spawn three debater subagents. There is no script for this phase; use standard Codex subagent spawning mechanisms. If the session is at maximum subagents and one is stopped, replace a stopped subagent. See the "Parallel or Sequential" section above for parallelism guidance. These subagents use gpt-5.4-mini as a model.

3. **Wait for the debaters**: during the wait, continue normal operations as the main agent in parallel, even for serial subagent spawns. Each subagent persists its ballot to `<workspace-root>/debates/<debate-id>/ballot-<subagent-name>.json`, with a JSON structure as follows:

```
{
  "debate": "debate-id",
  "subagent": "subagent-name",
  "choice": "yes",
  "confidence": 85,
  "reasoning": "detailed reasoning for the choice",
  "evidence": "detailed evidence supporting the reasoning",
  "blockers": "nullable; any blockers or concerns about the debate topic"
}
```

4. **Complete the debate**: after the debater subagents finish their work, verify `<workspace-root>/debates/<debate-id>/ballot-<subagent-name>.json` was persisted by each subagent. If not, quickly remediate by reviewing the subagent session(s) and persisting appropriate ballot(s).

5. **Tally the debate**: after all ballots are persisted, tally the debate by reviewing each ballot and writing a summary of the results, including which side won and why, supported by evidence from the ballots. Persist the summary to `<workspace-root>/debates/<debate-id>/summary.md`. To review all ballots for a debate, run:

```
python <skill-dir>/scripts/debate-helper.py --debate <debate-id> --tally
```

The above script combines the debate ballots into a single markdown file for easier review during tallying, but the tallying and `<workspace-root>/debates/<debate-id>/summary.md` persistence is a manual process for the main agent.