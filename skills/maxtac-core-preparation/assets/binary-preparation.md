# Binary Preparation

## Binary Recon

### Binary Deompilation and Disassembly
Decompile or disassemble the binary to build a source map. These methods serve as the "bridge" between an executable and readable logic.

#### Disassembly
Use disassembly when you need absolute precision and low-level detail. Since decompilers make assumptions about variables, types, and compiler optimizations, they can sometimes omit or misinterpret critical nuances that disassemblers expose directly.

- Bug Proofing: Precisely calculate stack offsets, identify gadget locations for Return-Oriented Programming (ROP), and construct specific payloads.
- Analyzing Compiler-Specific Code: Debug highly optimized, obfuscated, or custom binaries where the decompiler fails to generate valid C pseudo-code.
- Instruction-Level Verification: Confirm exactly how specific hardware registers, interrupts, or memory addresses are handled.

#### Decompilation
Use decompilation for high-level, broad analysis of a binary. Because the pseudo-code summarizes multiple assembly instructions into single logic blocks, it reads much faster.

- Identifying Logic Bugs: Quickly spot flaws like off-by-one errors, missing authentication checks, or improper arithmetic.
- Understanding Algorithm Flow: Grasp the overarching architecture and data structures of a program.
- Searching for Known Vulnerabilities: Trace how variables are passed through different functions without getting bogged down in CPU-specific registers.

### Binary Technology Fingerprinting
Investigate the binary composition to determine which language or framework was used to create it.

#### Cryptographic and Fuzzy Hashing
- Cryptographic Hashing: Techniques like MD5, SHA-256, or SSDEEP to identify exact binary matches or slightly modified versions of a file.
- Fuzzy Hashing: Tools such as ssdeep or tlsh generate piecewise hashes that can identify binaries with minor alterations (e.g., recompiled versions of the same library).

#### Static Binary Analysis and CFG Matching
- Control Flow Graph (CFG) Hashing: CFGs map the logical structure of a program by representing basic blocks and their branching paths. Create graph hashes to identify logically similar code even if the assembly instructions differ due to compiler flags.
- Abstract Syntax Tree (AST) & Feature Extraction: Extracting semantic properties, instruction counts, and mnemonic sequences to spot identical functions implemented in different architectures (e.g., ARM vs. x86).

## Binary Threat Modeling
Using publicly documented information and inputs, build a threat model of the binary.

### Function and Text Danger Areas
Perform static binary analysis, decompilation, and taint analysis to trace insecure user inputs to dangerous "sink" functions and embedded text.

#### Finding Dangerous Functions (Sinks)
Certain standard library functions are inherently risky because they lack bounds checking or format validation. Common targets include:

- Buffer Overflow: `strcpy`, `strcat`, `gets`, `sprintf`.
- Format String: `printf`, `sprintf`, `syslog` without explicit format specifiers (e.g., `printf(input)` rather than `printf("%s", input)`).
- Command Injection: `system`, `popen`, `exec`

#### Finding Dangerous Text and Strings
Embedded text and strings within a binary can reveal sensitive data, API endpoints, debugging commands, or vulnerable path strings.

- Hardcoded Credentials: API keys, passwords, database URIs.
- Debugging/Log Strings: "Password accepted", "Debug mode enabled", or specific error logs that expose internal logic.
- Command Strings: Text strings that match command patterns being passed directly to `system()`.
- Path Traversal Patterns: Strings like `../..` or directory paths.

### Binary Symbolic Execution
Use tools like angr to explore all possible execution paths mathematically, identifying inputs required to trigger specific crash states.

- Exhaustive Path Coverage: Instead of manually testing different inputs, symbolic execution systematically forces branches and tracks the path constraints required to reach vulnerable states.
- Math-Based Verification: It provides formal proof of whether a security property holds true for all possible inputs (e.g., proving that an attacker cannot execute a buffer overflow past a certain boundary).
- Automated Exploit Generation: By querying Satisfiability Modulo Theories (SMT) solvers like Z3, the engine can automatically generate the precise payload required to trigger a bug.

### Binary Static Analysis
The primary source code static analysis engine is `opengrep`, expected to be available on the CLI. Instead of manually auditing thousands of lines of code or guessing where a vulnerability lives, Opengrep allows describing the structure of security flaws using YAML rules. All opengrep research files should be persisted to `data/maxtac/static/`

Unlike source code targets, `opengrep` cannot directly analyze binaries. However, `opengrep` is compatible with decompiled C and C-psuedocode. Before performing static analysis on a binary target with `opengrep`, it should be decompiled.

- Custom Taint Analysis: Opengrep tracks data from unverified sources (e.g., HTTP requests or external APIs) to dangerous sinks (e.g., SQL execution or command line). Use the `--taint-intrafile` flag to map how untrusted data propagates through the application to enforce strict trust boundaries.
- Security Control Verification: Write custom rules to verify that internal API calls bypass unencrypted connections, restrict sensitive actions to specific user roles, or enforce mandatory data sanitization.
- Dependency & API Mapping: Use semantic patterns to immediately find where deprecated libraries or forbidden cloud SDKs are imported into a codebase.

Opengrep rules use code syntax patterns rather than complex Abstract Syntax Tree (AST) manipulation. This makes it easy to translate your system's data flows into rules. For an example, see: `opengrep-sql-injection-example.yml`

#### Opengrep Best Practices
Best practices involve writing modular rules and properly leveraging advanced taint features.

- Validate Before Scanning: Always run `opengrep validate <rules_directory>` to verify that your rules parse correctly before executing a full repository scan.
- Apply Dynamic Timeouts: Enable `--dynamic-timeout` to automatically scale timeouts based on file size, optimizing scan speeds for small vs. large codebases.
- Limit Matches: Use `max_match_per_file: 5` to prevent OpenGrep from overwhelming your output or slowing down when it hits a repetitive, large-scale issue.
- Utilize Cross-Function Taint: Take advantage of OpenGrep's open features by using `--taint-intrafile` to track user-controlled input across different functions within the same file. See the [Intrafile Taint Analysis](https://github.com/opengrep/opengrep/wiki/Intrafile-tainting-tutorial) tutorial for more information.
- Handle Higher-Order Functions: If your codebase relies on JavaScript/TypeScript, ensure you utilize OpenGrep's taint-tracking support for higher-order functions ⁠[Higher Order Functions Tutorial](https://github.com/opengrep/opengrep/wiki/Higher-order-functions-tutorial) (e.g., `.map()`, `.forEach()`) to find vulnerabilities hidden in callback logic.

### Binary Bug History Assessment
Analyze CVEs and cross-reference them with changelog items (if a changelog exists) for additional information. If the relevant binary is small enough, perform binary diffing and decomp/disassembly to understand the exact fix that was implemented.

### Binary STRIDE Modeling
The STRIDE threat model is a developer-focused model to identify and classify threats under 6 types of attacks – Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service DoS, and elevation of privilege.

- Spoofing Identity: Attackers impersonate legitimate users, devices, or systems to bypass authentication mechanisms and gain unauthorized access.
- Tampering with Data: Attackers modify data, code, or system components without authorization to alter system behavior or compromise data integrity.
- Repudiation: Users or attackers deny performing specific actions, making it difficult to prove accountability or trace malicious activities.
- Information Disclosure: Attackers gain unauthorized access to confidential data through system vulnerabilities, misconfigurations, or weak access controls.
- Denial of Service (DoS): Attackers disrupt system availability by consuming resources, exploiting vulnerabilities, or overwhelming services to prevent legitimate access.
- Elevation of Privilege: Attackers exploit system weaknesses to gain higher privileges than intended, accessing restricted resources or administrative functions.

#### STRIDE Step 1: Decompose
- Break the system into smaller modules or services.
- Identify all entry points where data enters the system.
- Map data flows to understand how information moves logically.

#### STRIDE Step 2: Categorize
- Apply the STRIDE mnemonic to each system component.
- Check for Spoofing, Tampering, Repudiation, and Information Disclosure.
- Evaluate risks of Denial of Service and Elevation of Privilege.

#### STRIDE Step 3: Mitigate
- Prioritize threats based on their potential business impact.

### Mitigations & Evasion Assessment
Determine the binary’s resilience against modern exploitation techniques.

- Security Controls: Check for standard compiler-level protections like Stack Canaries, NX/DEP (No-Execute), ASLR (Address Space Layout Randomization), and CFG (Control Flow Guard).
- Bypass Requirements: A threat model should document exactly what primitives (e.g., an information leak to defeat ASLR, or a write-what-where primitive) are required to execute a successful attack.
