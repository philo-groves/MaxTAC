---
name: maxtac-core-subagent-debate
description: Flows for working with debater subagents to vote on the reachability and exploitability of findings before proofing. After proofing, these same subagents are used to validate the PoC is correct.
---

# MaxTAC Core Subagent Debate
Use this skill for spawning and interacting with debater subagents. Each debater subagent independently votes on a topic and outputs its assessment.

## Model Selection

All debater subagents use gpt-5.4-mini to save on cost.

## Debate Flow
Each debate is created by the main agent, but all assessments and votes are delegated to debater subagents. The flow is:

1. Main agent assigns a debate ID and creates `data/maxtac/debates/<debate-id>/`.
2. Main agent spawns three debater subagents, each with a unique subagent ID. They are provided the same information.
3. Each agent votes `valid` or `invalid` based on the provided information.
4. Results from each agent are output to `data/maxtac/debates/<debate-id>/<subagent-id>/vote.json`. Supplemental evidence may be placed in the same directory if needed.

## JSON Structure

The JSON structure for `vote.json` only contains `result` and `reason` fields. Additional information is expected to be placed in the same directory if needed.

```
{
  "result": "valid",
  "reason": "<yada yada>"
}
```
