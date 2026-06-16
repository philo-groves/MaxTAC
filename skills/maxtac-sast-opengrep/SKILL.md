---
name: maxtac-sast-opengrep
description: "Use this skill when SAST needs OpenGrep rule authoring, static vulnerability search, taint or pattern matching, result interpretation, or packaging evidence for MaxTAC analysis."
---

## Check Readiness
Before using this skill, ensure OpenGrep is installed and properly configured on the system. Check if OpenGrep is accessible by running:
```
opengrep --version
```

If there is no output or an error occurs, OpenGrep may not be installed. Follow the installation instructions:

1. Ask the user for permission to install OpenGrep if it is not already installed.
2. If permission is granted, install OpenGrep using the per-system instructions below.

### Linux / macOS Install
```
curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash
```

### Windows Install (Powershell)
```
irm https://raw.githubusercontent.com/opengrep/opengrep/main/install.ps1 | iex
```

## Effective Rules
Search queries consist of rules, which are sets of pattern matching logic and data flow analysis. Use `maxtac-sast-surface-triage` first when the target is not already narrowed. Let the triage packet provide entrypoints, controlled inputs, sinks, guards, invariants, and auditor filters.

When writing rules for SAST, consider the following:
- **Narrow Focus**: Target one boundary, sink, guard, or bug class at a time.
- **Data Flow Analysis**: Track how attacker-controlled data moves through the application when simple pattern matching is too shallow.
- **Evidence Handoff**: Summarize matches as paths, guard questions, and file/function references for CFG analysis or targeted auditors.
- **Comprehensive Coverage**: Leverage OpenGrep's ability to analyze both source code and decompiled binaries for comprehensive coverage.

### Custom Rules
OpenGrep allows for the creation of custom rules to target specific vulnerabilities or coding patterns. When creating custom rules, consider the following:
- **Rule Structure Syntax**: Describes the YAML rule structure of OpenGrep. See `<skill-dir>/references/opengrep-rule-structure-syntax.md`
- **Rule Pattern Syntax**: Describes how to write custom rule pattern syntax. See `<skill-dir>/references/opengrep-rule-pattern-syntax.md`

### Data Flow Analysis
OpenGrep's data flow analysis capabilities allow for tracking the flow of data through the application. When performing data flow analysis, consider the following:

- **Taint Analysis**: Tracks potentially dangerous input data through the application to identify vulnerabilities. See `<skill-dir>/references/opengrep-taint-analysis.md`
- **Constant Propagation**: Tracks constant value logic through the application to identify potential vulnerabilities. See `<skill-dir>/references/opengrep-constant-propagation.md`
- **Symbolic Propagation**: Tracks symbolic value usage through the application to identify potential vulnerabilities. See `<skill-dir>/references/opengrep-symbolic-propagation.md`

### Generic Pattern Matching
Generic pattern matching allows OpenGrep to scan files using code-aware syntax even when a dedicated language parser does not exist. When using generic pattern matching, see `<skill-dir>/references/opengrep-rule-structure-syntax.md`

## Interpreting Results
Treat OpenGrep results as leads until the relevant path and guard behavior are manually checked.

- Confirm the matched code is reachable from the actor and entrypoint in the surface triage packet.
- Confirm the dangerous argument, receiver, index, length, path, credential, or state field is attacker-influenced.
- Confirm whether a sanitizer, authorization check, type check, bounds check, entitlement check, or state check dominates the sink.
- Deduplicate repeated framework patterns before sending results to auditors.
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
