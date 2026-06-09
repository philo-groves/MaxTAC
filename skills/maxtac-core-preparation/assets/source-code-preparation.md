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

### Identify Trust Boundaries
Locate where data leaves an authenticated, safe zone and enters an unvalidated state, for example:

- API Endpoints: Controller or route handlers accepting HTTP requests (e.g., REST, GraphQL, webhooks).
- Deserialization Points: Locations in code where raw strings or bytes are converted into complex objects or code states.
- CLI/Terminal Inputs: Code reading execution arguments, environment variables, or standard input streams.
- Microservice Communication: RPC, gRPC, or message queues (e.g., Kafka, RabbitMQ) crossing service domains.
- Admin vs. User Roles: Code sections that switch operational contexts based on JWT claims, session cookies, or RBAC (Role-Based Access Control) checks.
- Compiled vs. Interpreted: Dynamic code execution functions (e.g., eval(), exec(), reflection) that transition strings into executable code.

### Source Code Danger Areas
Inspect code comments, string, and documentation gaps in the source code. Use `rg` expressions or `opengrep` rules to quickly locate functions known to cause remote command execution, buffer overflows, and other vulnerabilities. For large source code workspaces, verify the expression is filtered correctly to reduce noise. If still too noisy, only search one specific module or file at a time.

- Command Injection / RCE: Search for string patterns involving system calls and execution. Keywords: `eval()`, `system()`, `exec()`, `passthru()`.
- Use-After-Free (UAF) / Buffer Overflow: Dangerous functions because they are "memory-unsafe" and require manual management of the heap. Keywords: `malloc()`, `calloc()`, `realloc()`, `free()`
- SQL Injection (SQLi): Search for user inputs directly concatenated or interpolated into database query strings. Keywords: `SELECT`, `UPDATE`, `INSERT` combined with string concatenation operators (e.g., `.`, `+`, or string formatting like `%s`).
- Cross-Site Scripting (XSS): Look for untrusted data being passed directly into output printing functions without sanitization or encoding. Keywords: `echo()`, `print()`, `innerHTML`. 
- Path Traversal / File Inclusion: Check for file system operations using unsanitized variables. Keywords: `include()`, `require()`, `open()`, `file_get_contents()`.
- Hard-Coded Secrets (CWE-540): Scan for sensitive information like API keys, encryption keys, or passwords embedded in plaintext strings. Keywords: Keywords: "secret", "password", "apiKey". Regex patterns: `AKIA` (AWS keys), `eyJhbGciOi` (JWT tokens).

### Source Code Static Analysis
The primary source code static analysis engine is `opengrep`, expected to be available on the CLI. Instead of manually auditing thousands of lines of code or guessing where a vulnerability lives, Opengrep allows describing the structure of security flaws using YAML rules. All opengrep research files should be persisted to `data/maxtac/static/`

- Custom Taint Analysis: Opengrep tracks data from unverified sources (e.g., HTTP requests or external APIs) to dangerous sinks (e.g., SQL execution or command line). Use the `--taint-intrafile` flag to map how untrusted data propagates through the application to enforce strict trust boundaries.
- Security Control Verification: Write custom rules to verify that internal API calls bypass unencrypted connections, restrict sensitive actions to specific user roles, or enforce mandatory data sanitization.
- Dependency & API Mapping: Use semantic patterns to immediately find where deprecated libraries or forbidden cloud SDKs are imported into a codebase.

Opengrep rules use code syntax patterns rather than complex Abstract Syntax Tree (AST) manipulation. This makes it easy to translate your system's data flows into rules. For an example, see: `opengrep-sql-injection-example.yml`

#### Opengrep Best Practices
Write modular rules and properly leverage advanced taint features.

- Validate Before Scanning: Always run `opengrep validate <rules_directory>` to verify that your rules parse correctly before executing a full repository scan.
- Apply Dynamic Timeouts: Enable `--dynamic-timeout` to automatically scale timeouts based on file size, optimizing scan speeds for small vs. large codebases.
- Limit Matches: Use `max_match_per_file: 5` to prevent OpenGrep from overwhelming your output or slowing down when it hits a repetitive, large-scale issue.
- Utilize Cross-Function Taint: Take advantage of OpenGrep's open features by using `--taint-intrafile` to track user-controlled input across different functions within the same file. See the [Intrafile Taint Analysis](https://github.com/opengrep/opengrep/wiki/Intrafile-tainting-tutorial) tutorial for more information.
- Handle Higher-Order Functions: If your codebase relies on JavaScript/TypeScript, ensure you utilize OpenGrep's taint-tracking support for ⁠[Higher Order Functions](https://github.com/opengrep/opengrep/wiki/Higher-order-functions-tutorial) (e.g., `.map()`, `.forEach()`) to find vulnerabilities hidden in callback logic.

### Source Code Bug History Assessment
Analyze publicly posted CVEs and cross-reference them with commits for additional information. Most CVEs are public by their nature to inform developers to update. However, they often lack details of the vulnerable behavior and scope of fix. Through cross-referencing, a full picture of historical bug root causes and fixes can be assessed. 

#### Vulnerability Contributing Commit (VCC).
The most critical part of bug history assessment is finding the Vulnerability Contributing Commit (VCC) - the exact change where the bug was introduced, rather than just where it was fixed.

- Git Blame: Use `git blame` and `git log -S [string]` to trace the lifespan of a specific vulnerable code block.
- Commit Messages: Review historical developer notes, ticket IDs, and PR comments associated with previous bug fixes, as they often hint at edge cases the developers missed.
- Historical Tracking: Utilize historical databases and academic frameworks to study the lineage of known CVEs in similar codebases.

### Source Code STRIDE Modeling
Use the STRIDE threat model as a developer-focused model to identify and classify threats.

- Spoofing Identity: Attackers impersonate legitimate users, devices, or systems to bypass authentication mechanisms and gain unauthorized access.
- Tampering with Data: Attackers modify data, code, or system components without authorization to alter system behavior or compromise data integrity.
- Repudiation: Users or attackers deny performing specific actions, making it difficult to prove accountability or trace malicious activities.
- Information Disclosure: Attackers gain unauthorized access to confidential data through system vulnerabilities, misconfigurations, or weak access controls.
- Denial of Service (DoS): Attackers disrupt system availability by consuming resources, exploiting vulnerabilities, or overwhelming services to prevent legitimate access.
- Elevation of Privilege: Attackers exploit system weaknesses to gain higher privileges than intended, accessing restricted resources or administrative functions.

#### Step 1: Decompose
- Break the system into smaller modules or services.
- Identify all entry points where data enters the system.
- Map data flows to understand how information moves logically.

#### Step 2: Categorize
- Apply the STRIDE mnemonic to each system component.
- Check for Spoofing, Tampering, Repudiation, and Information Disclosure.
- Evaluate risks of Denial of Service and Elevation of Privilege.

#### Step 3: Mitigate
- Prioritize threats based on their potential business impact.