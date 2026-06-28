# Source Code Preparation

## Source Code Mapping
Build a full repository map of code new and old. Create language-aware call graphs for important functions. Identify test coverage and locations where tests are missing. Trace untrusted user input (sources) directly to dangerous execution points (sinks) like SQL injections or command execution. Unpack complex, undocumented logic, dependencies, and API calls.

### Data Flow Analysis (Taint Analysis)
Tracks how values propagate through the program to identify unverified inputs being processed by sensitive sinks.

- Taint Sources: Web requests, file uploads, environment variables, database inputs.
- Taint Sinks: system(), SQL queries (e.g., SELECT...), deserialization endpoints, output printing.

### Code Property Graph (CPG) Mapping
Combines multiple static analysis representations into a searchable, graph-based database (often using Graphviz or Neo4j). CPGs capture:

- AST (Abstract Syntax Tree): Captures the syntactic structure of the code.
- CFG (Control Flow Graph): Maps execution paths, loops, and conditional branches.
- PDG (Program Dependency Graph): Tracks data and control dependencies between variables and instructions.

### Call Graph Generation
Creates a map of which functions call other functions throughout the entire codebase. This is highly useful for spotting:

- Privilege escalation vectors (e.g., how an unauthenticated route leads to administrative functions).
- Impact analysis when a core library or framework component has a known vulnerability.

### Mapping Best Practices

- Identify Critical Entry Points: Always start by mapping where authentication, authorization, and data processing occur.
- Visualize the Data: Dump call graphs or CPG structures to visualization formats like DOT files or directly into Graph databases to spot architectural flaws manually.

## Source Code Threat Modeling
Using the available code structure and documentation, build a threat model of the repository. Before modeling, build a source code map (described above), unless one already exists. Code-based threat modeling integrates the threat perspective into code review, supplementing the existing source code map with an attacker perspective analysis.

### Source Code Static Analysis
Static analysis is used beyond preparation, but it is relevant here. Use `maxtac-sast-surface-triage` to define the target slice, then use `maxtac-sast-control-flow-graph` or `maxtac-sast-opengrep` when the preparation branch needs reachability, guard dominance, or repeatable source-to-sink searches.

### Source Code Bug History Assessment
Analyze publicly posted CVEs and cross-reference them with commits for additional information. Most CVEs are public by their nature to inform developers to update. However, they often lack details of the vulnerable behavior and scope of fix. Through cross-referencing, a full picture of historical bug root causes and fixes can be assessed. 

#### Vulnerability Contributing Commit (VCC).
The most critical part of bug history assessment is finding the Vulnerability Contributing Commit (VCC) - the exact change where the bug was introduced, rather than just where it was fixed.

- Git Blame: Use `git blame` and `git log -S [string]` to trace the lifespan of a specific vulnerable code block.
- Commit Messages: Review historical developer notes, ticket IDs, and PR comments associated with previous bug fixes, as they often hint at edge cases the developers missed.
- Historical Tracking: Utilize historical databases and academic frameworks to study the lineage of known CVEs in similar codebases.
