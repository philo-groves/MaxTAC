Use this skill when subagents should be spawned for auditing or debate.

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
Every audit follows the same general flow.

1. **Choose the auditor**: a collection of specialist security auditors exist in `<skill-dir>/assets/auditors.json`, but do not read the large JSON file directly; instead, run:

```
python3 <skill-dir>/scripts/audit-helper.py --list             # List all auditors, their usage and markdown.
python3 <skill-dir>/scripts/audit-helper.py --search <filter>  # Filter auditor list with a simple search.
```

Each of the above scripts results in a condensed list of auditors.

2. **Write the audit prompt**: after reading the specialist usage and related markdown, write a prompt for its subject matter and the current target, then run:

```
python3 <skill-dir>/scripts/audit-helper.py --prompt <prompt>  # Prepare the audit directory and enrich the prompt
```

The above script results in an enriched prompt; enrichment appends instructions to persist audit assessment files to `audits/<id>/`. The script also creates the `audits/<id>/` directory, then persists the subagent prompt there.

3. **Spawn the auditor**: use the enriched prompt to spawn an auditor subagent. There is no script for this phase; use standard Codex subagent spawning mechanisms. If the session is at maximum subagents and one is stopped, replace a stopped subagent.

4. **Wait for the auditor**: during the wait, continue normal operations as the main agent in parallel, even for serial subagent spawns. During its work, the subagent persists evidence to `audits/<id>/`.

5. **Complete the audit**: after the auditor subagent finishes its work, verify `audits/<id>/assessment.md` was persisted by the subagent. If not, quickly remediate by reviewing the subagent session and persisting a proper assessment.

## Debater Subagents
A debater subagent reviews a topic, such as a bug finding, then votes on a ballot and explains its reasoning.

For working with debater subagents, read: 
```
<skill-dir>/references/debater-subagents.md
```
