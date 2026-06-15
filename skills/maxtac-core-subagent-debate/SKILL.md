---
name: maxtac-core-subagent-debate
description: Flows for working with debater subagents to vote on the reachability and exploitability of findings before proofing. After proofing, these same subagents are used to validate the PoC is correct.
---

# MaxTAC Core Subagent Debate
Use this skill for spawning debater subagents and managing the artifical debate floor. Each debater subagent independently analyzes a finding and outputs a vote: `valid`, `invalid`, or `unsure`. A debate is over when all subagents vote and none are `unsure`. A debate uses three debaters, guaranteeing a majority.

## Model Selection
All debater subagents use gpt-5.4-mini to save on cost.

## Debate Flow
Each debate is created by the main agent, but all assessments and votes are delegated to debater subagents. The flow is:

1. Main agent generates a unique debate ID, then creates a `debates/<debate-id>/` directory and a `debates/<debate-id>/floor.jsonl` file.
2. Main agent generates a debate prompt that is shared between debater subagents. Prefer the format in `<skill-dir>/assets/debate.template.md` file.
3. Persist the raw debate prompt in a `debates/<debate-id>/debate.md` file (without subagent field), then spawn three debater subagents with the same prompt (but include unique subagent fields).
4. Each subagent appends the `floor.jsonl` with their vote and reason: `valid`, `invalid`, or `unsure`.
5. At the end of each round (every three votes), check if there were any `unsure` debaters. If there were, agents which responded `valid` or `invalid` write a clarification response to this `unsure` vote in the next round; then, the `unsure` subagent(s) reacts and revotes based on that information. In some cases, an `unsure` subagent may influence and change an already-confirmed subagent vote, which is allowed.
5. After a debate has settled with no `unsure` agents, continue and complete the current phase as described in the primary workflow.

## JSONL Structure

The JSON structure for `floor.jsonl` only contains `subagent`, `vote` and `reason` fields. Additional information is expected to be placed in the same directory if needed.

```
{ subagent: "A", "vote": "valid", "reason": "<yada yada>" }
{ subagent: "B", "vote": "invalid", "reason": "<tada tada>" }
{ subagent: "C", "vote": "valid", "reason": "<wada wada>" }
```
