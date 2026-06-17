---
name: maxtac-sast-opengrep
description: "Use this skill when SAST needs OpenGrep rule authoring, static vulnerability search, taint or pattern matching, result interpretation, or packaging evidence for MaxTAC analysis."
---

## Check Readiness
Check the installed tool surface:

```
opengrep --version
opengrep --help
```

If OpenGrep is not installed, ask first, then read `<skill-dir>/references/opengrep-install.md`.

## Effective Rules
Use `maxtac-sast-surface-triage` first when the target is not already narrowed. Let the triage packet provide entrypoints, controlled inputs, sinks, guards, invariants, and auditor filters.

When writing rules for SAST, consider the following:
- **Narrow Focus**: Target one boundary, sink, guard, or bug class at a time.
- **Data Flow Analysis**: Track how attacker-controlled data moves through the application when simple pattern matching is too shallow.
- **Evidence Handoff**: Summarize matches as paths, guard questions, and file/function references for CFG analysis or targeted, goal-bounded auditors.

### Custom Rules
- **Rule Structure Syntax**: See `<skill-dir>/references/opengrep-rule-structure-syntax.md`
- **Rule Pattern Syntax**: See `<skill-dir>/references/opengrep-rule-pattern-syntax.md`

### Data Flow Analysis
- **Taint Analysis**: See `<skill-dir>/references/opengrep-taint-analysis.md`
- **Constant Propagation**: See `<skill-dir>/references/opengrep-constant-propagation.md`
- **Symbolic Propagation**: See `<skill-dir>/references/opengrep-symbolic-propagation.md`

### Generic Pattern Matching
For generic pattern matching, see `<skill-dir>/references/opengrep-rule-structure-syntax.md`

## Interpreting Results
Treat OpenGrep results as leads until the relevant path and guard behavior are manually checked.

- Confirm the matched code is reachable from the actor and entrypoint in the surface triage packet.
- Confirm the dangerous argument, receiver, index, length, path, credential, or state field is attacker-influenced.
- Confirm whether a sanitizer, authorization check, type check, bounds check, entitlement check, or state check dominates the sink.
- Deduplicate repeated framework patterns before sending results to goal-bounded auditors.
- Preserve negative evidence when it closes a hypothesis, such as a guard that dominates every matched sink.
- Use `maxtac-sast-control-flow-graph` when a result depends on interprocedural reachability, callbacks, cleanup paths, or guard ordering.

### Result Packet
Use this shape when handing results to `maxtac-core-subagents`:

```markdown
## OpenGrep Result Packet

- Rule or search:
- Target slice:
- Matched files/functions:
- Source or controlled input:
- Sink or protected transition:
- Expected guard or invariant:
- Confirmed path:
- False-positive reasons removed:
- Remaining uncertainty:
- Suggested auditor filters:
```
