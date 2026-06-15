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

### Binary Bug History Assessment
Analyze CVEs and cross-reference them with changelog items (if a changelog exists) for additional information. If the relevant binary is small enough, perform binary diffing and decomp/disassembly to understand the exact fix that was implemented.

### Mitigations & Evasion Assessment
Determine the binary’s resilience against modern exploitation techniques.

- Security Controls: Check for standard compiler-level protections like Stack Canaries, NX/DEP (No-Execute), ASLR (Address Space Layout Randomization), and CFG (Control Flow Guard).
- Bypass Requirements: A threat model should document exactly what primitives (e.g., an information leak to defeat ASLR, or a write-what-where primitive) are required to execute a successful attack.
