Use this skill when subagents should be spawned for auditing or debating.

## Parallel or Sequential
Ideally, subagents would always run in parallel, but system resources sometimes prevent that. When resources are limited, subagents must be spawned sequentially to prevent RAM overload. Otherwise, subagents may be spawned in parallel.

To determine whether to run in parallel or sequentially, run:
```
python3 <skill-dir>/scripts/system-check.py --subagents <count>
```

The script prints `parallel` or `sequential` after checking available system resources against the requested subagent count.

## Auditor Subagents
An auditor subagent is a specialist vulnerability researcher for an individual bug class, mitigation, or other security topic.

### Auditor Flow
Every audit follows the same 5-step flow.

1. **Choose the auditor**: a collection of specialist security auditors exist in `<skill-dir>/assets/auditors.json`. Use this information to select the appropriate auditor. Do not read the large JSON file directly; instead, run:

```
python3 <skill-dir>/scripts/audit-helper.py --list
python3 <skill-dir>/scripts/audit-helper.py --search <filter>
```

Each of the above scripts result in a condensed list of auditors.

2. **Write the audit prompt**: after reading the specialist usage and related markdown, write a prompt for its subject matter and the current target, then run:

```
python3 <skill-dir>/scripts/audit-helper.py --prompt <prompt>
```

The above script results in an enriched prompt; enrichment appends instructions to persist audit assessment files to `audits/<id>/`. The script also creates the `audits/<id>/` directory, then persists the subagent prompt there.

3. **Spawn the auditor**: use the enriched prompt to spawn the auditor subagent. There is no script for this phase; use standard Codex subagent spawning mechanisms. If the session is at maximum subagents and one is stopped, replace a stopped subagent. These subagents use gpt-5.5 as a model with xhigh reasoning effort.



4. **Wait for the auditor**: during the wait, continue normal operations as the main agent in parallel, even for serial subagent spawns. During its work, the subagent persists evidence to `audits/<id>/`.

5. **Complete the audit**: after the auditor subagent finishes its work, verify `audits/<id>/assessment.md` was persisted by the subagent. If not, quickly remediate by reviewing the subagent session and persisting a proper assessment.

## Debater Subagents
A debater subagent reviews a debate topic, then votes on a ballot and explains its reasoning.

### Debater Flow
Every debate follows the same 5-step flow.

1. **Write the debate prompt**: write a prompt for the debate topic, then run:

```
python3 <skill-dir>/scripts/debate-helper.py --prompt <prompt>
```

The above script results in an enriched prompt; enrichment appends instructions to persist debate ballot files to `debates/<id>/`. The script also creates the `debates/<id>/` directory, then persists the subagent prompt there.

2. **Spawn debater subagents**: use the enriched prompt to spawn three debater subagents. There is no script for this phase; use standard Codex subagent spawning mechanisms. If the session is at maximum subagents and one is stopped, replace a stopped subagent. These subagents use gpt-5.4-mini as a model.

3. **Wait for the debaters**: during the wait, continue normal operations as the main agent in parallel, even for serial subagent spawns. During the debate, each subagent persists its ballot with:

```
python3 <skill-dir>/scripts/debate-helper.py --debate <id> --subagent <subagent name> --choice <yes/no> --reasoning <detailed reasoning>
```

The above script results in a ballot persisted to `debates/<id>/ballot-<subagent-name>.json`.

4. **Complete the debate**: after the debater subagents finish their work, verify `debates/<id>/ballot-<subagent-name>.json` was persisted by each subagent. If not, quickly remediate by reviewing the subagent session(s) and persisting appropriate ballot(s).

5. **Tally the debate**: after all ballots are persisted, tally the debate by reviewing each ballot and writing a summary of the results, including which side won and why, supported by evidence from the ballots. Persist the summary to `debates/<id>/summary.md`. To review all ballots for a debate, run:

```
python3 <skill-dir>/scripts/debate-helper.py --debate <id> --tally
```