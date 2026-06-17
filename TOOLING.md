## MaxTAC Tooling Inventory

MaxTAC's core workflow only needs Python and Codex. The research skills route to many external tools, but they are target-specific. Install the tools that match the current program, artifact type, and proof strategy instead of trying to install everything.

## Core Runtime

| Tool | Used for | Notes |
| --- | --- | --- |
| Python | MCP server, workspace helpers, ledger helpers, evidence bundle scripts | Required for MaxTAC's deterministic helper tools. `.mcp.json` currently invokes `python`. |
| Codex subagents and goals | Auditor prompts, verifier debates, workflow orchestration | Required by the workflow model, not an external binary. |
| ripgrep (`rg`) | Fast source search during surface triage and CFG fact collection | Recommended for source-code research. |

## Static Analysis

| Tool | Used for | Skills |
| --- | --- | --- |
| OpenGrep (`opengrep`) | Rule authoring, pattern matching, taint-style source-to-sink checks, result packets | `maxtac-sast-opengrep`, `maxtac-sast-surface-triage` |
| Compiler, AST, language-server, static-analysis, code-index, or route-map tools | CFG/call-graph facts, guard dominance, framework routes, reachability evidence | `maxtac-sast-control-flow-graph` |
| DOT or Mermaid-compatible graph output | Persisted control-flow, call-graph, state-machine, or ownership evidence | `maxtac-sast-control-flow-graph` |

## Reverse Engineering

| Tool | Used for | Skills |
| --- | --- | --- |
| Ghidra, `analyzeHeadless`, Java, PyGhidra | Headless import, decompilation, p-code, scripting, type recovery, BSim, version tracking, emulation | `maxtac-re-ghidra` |
| JADX, `jadx-gui`, Java | APK/DEX/JAR/AAR/AAB decompilation, Android resources, mappings, GUI search, smali debugging, JSON/API export | `maxtac-re-jadx` |
| radare2 suite: `r2`, `rabin2`, `rahash2`, `rafind2`, `radiff2`, `rax2`, `rasm2`, `ragg2`, `r2pipe` | Binary triage, imports, symbols, hashes, search, diffing, ESIL, debugging, scripting, utilities | `maxtac-re-radare2`, `maxtac-dast-debugger` |

## Dynamic Analysis and Debugging

| Tool | Used for | Skills |
| --- | --- | --- |
| LLDB | macOS, iOS, C/C++/Objective-C/Swift crash replay and debugging | `maxtac-dast-debugger` |
| GDB | Linux and portable ELF crash replay/debugging | `maxtac-dast-debugger` |
| x64dbg | Windows user-mode binary debugging | `maxtac-dast-debugger` |
| WinDbg | Windows kernel-mode, crash dump, and deep OS-component debugging | `maxtac-dast-debugger` |
| ADB | Android device control, logs, shell, install, harness launch, screenshots, bugreports | `maxtac-dast-debugger`, `maxtac-dast-virtualization`, `maxtac-re-jadx` |
| xcrun | iOS simulator or connected-device control | `maxtac-dast-debugger`, `maxtac-dast-virtualization` |
| Frida | Runtime instrumentation, mobile hooks, API tracing | `maxtac-dast-debugger` |
| WebDriver BiDi | Browser debugging with bidirectional events | `maxtac-dast-debugger` |
| Chrome DevTools Protocol (CDP) | Chromium-family protocol debugging | `maxtac-dast-debugger` |
| WebKit debugging tools | Safari or WebKit target debugging | `maxtac-dast-debugger` |

## Fuzzing

| Tool family | Used for | Skills |
| --- | --- | --- |
| AFL++, libFuzzer, FuzzTest | Native parser, codec, library, CLI, or binary fuzzing with source/build flags | `maxtac-dast-fuzzer` |
| LibAFL | Custom instrumentation, emulation, snapshotting, schedulers | `maxtac-dast-fuzzer` |
| WinAFL, AFL++ FRIDA/QEMU/Wine paths | Windows or binary-only target fuzzing | `maxtac-dast-fuzzer` |
| Honggfuzz | Multi-process campaigns or existing honggfuzz integrations | `maxtac-dast-fuzzer` |
| cargo-fuzz, Go fuzzing, Jazzer, Atheris | Rust, Go, JVM, Python, and CPython-extension fuzzing | `maxtac-dast-fuzzer` |
| RESTler, Schemathesis | Stateful REST/OpenAPI or schema-backed API fuzzing | `maxtac-dast-fuzzer` |
| Nuclei, Burp Intruder, ZAP Fuzzer, ffuf | Captured HTTP traffic, templates, parameter fuzzing, manual request fuzzing | `maxtac-dast-fuzzer` |
| syzkaller, boofuzz, Fuzzilli, Domato | Kernels, syscalls, drivers, OS services, custom protocols, browser engines | `maxtac-dast-fuzzer` |
| Android Monkey | Repeatable Android UI stress when lower-level harnessing is unavailable | `maxtac-dast-fuzzer` |
| libprotobuf-mutator, Nautilus, Grammarinator, Radamsa | Structured text, protobuf-like data, grammar fuzzing, seed expansion | `maxtac-dast-fuzzer` |
| OSS-Fuzz, ClusterFuzzLite, FuzzBench | Continuous fuzzing, CI fuzzing, fuzzer evaluation | `maxtac-dast-fuzzer` |

## Lab and Virtualization

| Tool or environment | Used for | Skills |
| --- | --- | --- |
| Docker | Containerized app or service isolation and reproducible dependencies | `maxtac-dast-virtualization` |
| Tart | macOS VM snapshot workflows | `maxtac-dast-virtualization` |
| Hyper-V | Windows desktop or driver-adjacent targets | `maxtac-dast-virtualization` |
| QEMU | Linux desktop, kernel, appliance-like, or cross-architecture targets | `maxtac-dast-virtualization` |
| Physical iOS device | Report-grade iOS behavior when simulator evidence is insufficient | `maxtac-dast-virtualization`, `maxtac-dast-debugger` |
| Physical Android device | Report-grade Android behavior when emulator evidence is insufficient | `maxtac-dast-virtualization`, `maxtac-dast-debugger` |

## Apple Security Bounty Workflows

| Tool | Used for | Skills |
| --- | --- | --- |
| `ipsw` | IPSW/OTA acquisition, metadata, extraction, kernelcache, dyld shared cache, DeviceTree, DMG, IMG4, iBoot, SEP, coprocessor, trust cache, filesystem, mounting, firmware diffing | `maxtac-asb-ipsw` |
| Ghidra or radare2 | Firmware payload and kernelcache handoff when deeper binary RE is needed | `maxtac-asb-ipsw`, `maxtac-re-ghidra`, `maxtac-re-radare2` |
| class-dump and swift-dump | Optional Objective-C/Swift metadata inspection for dyld shared cache outputs | `maxtac-asb-ipsw` |
| C compiler and platform SDK tooling | Build Apple proof helpers for arbitrary read/write, code execution, TCC, or other target-flag demonstrations | `maxtac-asb-flag-proof` |

## MSRC Workflows

| Tool | Used for | Skills |
| --- | --- | --- |
| Microsoft SandboxSecurityTools | LPAC and eligible sandbox proof setup | `maxtac-msrc-lpac-proof` |
| LaunchAppContainer, LaunchSandboxMSRC.bat | Generic LPAC baseline and local proof launching | `maxtac-msrc-lpac-proof` |
| EdgeSandboxTestTool | Edge renderer sandbox proof routing | `maxtac-msrc-lpac-proof` |
| PowerShell, `whoami`, `Get-Process`, `icacls`, `reg` | Windows build, token, process, ACL, and registry evidence | `maxtac-msrc-lpac-proof` |
| WinDbg or x64dbg | Optional debugger-assisted Windows proof reproduction when not required for the exploit | `maxtac-msrc-lpac-proof`, `maxtac-dast-debugger` |

## Practical Install Order

1. Start with Python and `rg`.
2. For source-heavy work, add OpenGrep and any project-native compiler, language-server, route-map, or static-analysis tooling.
3. For binary work, add Ghidra and radare2; add JADX for Android artifacts.
4. For dynamic proof, add the debugger, device-control, virtualization, and fuzzer tools that match the target.
5. For Apple or Microsoft bounty-specific work, add `ipsw` or SandboxSecurityTools only when that domain pack is in use.
