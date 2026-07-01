---
name: maxtac-binary-decompile-loop
description: "Use this skill when MaxTAC Binary needs a loop to model how a binary was compiled and loaded, preserve reverse-engineering provenance, prioritize executable functions by reachability or call frequency, systematically decompile or parse functions and data structures, and produce durable functionality and security evidence."
---

# MaxTAC Binary Decompile Loop

Use this loop for systematic binary understanding before or during security review. It is not a replacement for Ghidra, radare2, debugger, or fuzzer skills; it orchestrates them into repeatable function and data-structure coverage.

## Setup

1. Record target identity: path, hashes, format, architecture, bitness, endianness, stripped/static state, imports, exports, sections, libraries, hardening, debug symbols, and provenance.
2. Run `maxtac-re-ghidra` readiness for report-grade Ghidra work or `maxtac-re-radare2` triage for terminal-first analysis.
3. Model the compile/load stack: compiler or toolchain clues, language/runtime, loader, relocation model, symbol sources, dyld/ELF/PE metadata, packed/encrypted state, and analysis caveats.
4. Create Core loop state:

```text
python3 <core-workflow-skill-dir>/scripts/loop.py init \
  --root <workspace-root> \
  --loop-id <id> \
  --kind binary-decompile \
  --owner-plugin maxtac-binary \
  --target "<binary path or component>" \
  --scope "<functions, ranges, symbols, or data structures>" \
  --summary "Systematically recover binary functionality and security-relevant behavior." \
  --positive-gate "Function or data item has provenance, decompile/disassembly evidence, caller/callee context, security sensitivity, and durable disposition." \
  --negative-gate "Function or data item has unresolved loader/analysis caveat, missing xrefs, bad decompilation, unknown calling convention, or unmodeled security effect." \
  --output "research/artifacts/binary-decompile/<id>/" \
  --output "models/<model-id>/" \
  --output "contracts/loops/<id>/"
```

5. Add loop items for entrypoints, exported symbols, imported-call wrappers, parser functions, command handlers, IPC handlers, allocator/copy functions, security checks, suspicious strings, data structures, and unresolved indirect calls.

## Prioritization

For executables, prioritize:

- program entrypoints and init routines;
- exported commands, request handlers, selectors, or dispatch table targets;
- functions with many xrefs or high dynamic frequency if trace/profiling data exists;
- functions near dangerous imports, syscalls, file/network/IPC APIs, crypto, decompression, parsing, or privilege boundaries.

For libraries, prioritize:

- exported APIs, registration tables, callbacks, parser entrypoints, object constructors/destructors, and functions reachable from host application imports.

## Iterate

For each loop item:

1. Preserve evidence source: loader metadata, auto-analysis, manual repair, decompiler output, disassembly, p-code/ESIL, debug trace, or string/xref evidence.
2. Repair function boundaries, types, calling convention, stack variables, switch tables, and data structures before making security claims.
3. Summarize behavior in one sentence and record caller/callee edges.
4. Identify security role: entrypoint, guard, sink, parser, allocator, policy, state transition, cleanup, debug path, or unknown.
5. Add model entities/relations/invariants when the recovered function explains architecture or a security rule.
6. Route memory-safety, parser, race, or exploitability questions into targeted Binary auditors, debugger evidence, or fuzzing.
7. Update the loop item with evidence, blockers, model refs, and ledger refs.

## Gates

Positive closure requires:

- repeatable RE provenance and tool settings;
- decompile/disassembly evidence or documented reason decompilation is not reliable;
- caller/callee or xref context;
- security sensitivity and disposition;
- durable model/corpus update when reusable functionality was learned.

Negative closure requires:

- unresolved packed/encrypted code, missing relocation context, bad function recovery, unknown ABI, unresolved indirect dispatch, or binary-only caller gap;
- blocker recorded in the loop item and model unknown when it affects a security conclusion.

## Output

Keep raw RE exports under `research/artifacts/binary-decompile/<id>/`. Use Core models for architecture and invariants. Use corpus notes for compact durable behavior. Use ledgers only when a primitive or chain hypothesis survives analysis.

## Hard Rules

- Do not treat decompiler output as source truth without provenance and caveats.
- Do not claim function coverage when function discovery is known incomplete.
- Do not skip compile/load modeling for stripped, packed, obfuscated, or unusual ABI binaries.
- Do not let broad RE notes become the durable knowledge base; project stable facts into Core corpus and models.
