---
name: maxtac-sast-opengrep
description: Use this skill to perform code searches using OpenGrep for static application security testing (SAST). Provides guidance on how to use OpenGrep for SAST, including how to write effective search queries, interpret results, and OpenGrep features for the security testing workflow.
---

## Check Readiness
Before using this skill, ensure OpenGrep is installed and properly configured on the system. Check if OpenGrep is accessible by running:
```
opengrep --version
```

## Effective Rules
Search queries consist of rules, which are sets of pattern matching logic and data flow analysis. Rules are used for scanning code to identify potential security vulnerabilities. When writing rules for SAST, consider the following:
- **Narrow Focus**: Focus on specific vulnerability types (e.g., SQL injection, cross-site scripting) to narrow down results.
- **Data Flow Analysis**: Use data flow analysis to track how data moves through the application, which can help identify vulnerabilities that may not be apparent from simple pattern matching.
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
