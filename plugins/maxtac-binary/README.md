# MaxTAC for Binary

MaxTAC for Binary adds native reverse engineering, debugger, crash replay, instrumentation, and systems fuzzing workflows.

Use this pack with MaxTAC Core when the target is a native binary, firmware component, parser, protocol implementation, kernel-adjacent component, native library, or decompiler-heavy system.

## When To Use

- Ghidra or radare2 reverse engineering.
- Native debugger or instrumentation evidence with LLDB, GDB, x64dbg, WinDbg, Frida, or radare2 debugger mode.
- Crash replay and runtime state capture.
- Coverage-guided fuzzing, harness selection, grammar fuzzing, or systems dynamic testing.
- Binary diffing, decompilation, p-code, ESIL, emulation, or function similarity work.

## Skills

- `maxtac-re-ghidra`: Ghidra headless analysis, decompilation, p-code, scripting, type recovery, BSim, debugging, and emulation.
- `maxtac-re-radare2`: radare2 binary analysis, search, diffing, debugging, ESIL, and hex utilities.
- `maxtac-dast-debugger`: debugger, instrumentation, crash replay, and runtime evidence capture.
- `maxtac-dast-fuzzer`: fuzzing strategy, harness selection, coverage, grammar fuzzing, and crash triage.

## Typical Pairings

- Binary + Source when decompiler output needs static packet work or OpenGrep/CFG evidence.
- Binary + Apple Systems for kernelcache, dyld shared cache, firmware, or ASB proof paths.
- Binary + Android for native libraries inside APKs.
- Binary + Microsoft Systems for Windows mitigation and MSRC proof workflows.
- Binary + Supply Chains for native release artifacts, installers, or binary package integrity.

## Output Artifacts

Binary workflows commonly produce:

- Reverse-engineering notes and function maps.
- Decompiled snippets and cross-reference evidence.
- Debugger transcripts, crash logs, register state, memory maps, and replay commands.
- Fuzzing harnesses, corpora, minimization notes, coverage, and crash buckets.

## Boundary

This pack avoids web, source-only, package registry, Android platform, Apple ASB, and Microsoft MSRC-specific policy guidance unless paired with those packs.
