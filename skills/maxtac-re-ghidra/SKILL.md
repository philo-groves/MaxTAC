---
name: maxtac-re-ghidra
description: "Use this skill when binary reverse engineering needs Ghidra for headless analysis, decompilation, p-code inspection, scripting automation, binary search, data type recovery, version tracking, BSim similarity, debugging, or emulation."
---

# MaxTAC RE Ghidra
Use Ghidra when decompiler output, rich program databases, data type recovery, repeatable headless analysis, or cross-version markup transfer matters more than single-command terminal speed. Treat Ghidra output as an analysis database: record import settings, analysis options, manual repairs, script versions, and whether facts came from loader metadata, analyzers, decompiler output, or runtime traces.

## Readiness Check
Identify the installation, automation entrypoint, and Java/PyGhidra state before report-grade work:

```bash
java -version
"$GHIDRA_HOME/support/analyzeHeadless" -help
python -c "import pyghidra; print(pyghidra.__version__)"
```

If Ghidra is not installed or a source/native build is needed, ask first, then read `<skill-dir>/references/ghidra-install-build.md`.

Use the readiness helper when Ghidra evidence needs to be repeatable or compared with radare2/JADX evidence:

```
python3 <skill-dir>/scripts/re-readiness.py --tool ghidra --target ./target.bin --output re-readiness.md
```

MaxTAC MCP convention: use `re_readiness_check` for readiness and `ghidra_export` for export when available; otherwise use `re-readiness.py` and `scripts/ghidra-export.py`.

Use `ghidra-export.py` to preserve input hashes, project settings, loader/processor/compiler overrides, script paths, analysis timeouts, and the exact `analyzeHeadless` command before running headless analysis. It plans by default and only executes with `--run`:

```
python3 <skill-dir>/scripts/ghidra-export.py ./target.bin \
  --ghidra-home "$GHIDRA_HOME" \
  --project-dir ./ghidra-projects \
  --project-name target-analysis \
  --output-dir ./ghidra-evidence \
  --analysis-timeout 300 \
  --post-script ExportEvidence.java
```

Add `--run` only after reviewing the generated command in `command.txt`.

## Usage Guidance

### Headless Analysis
Includes `analyzeHeadless` import/process mode, script paths, script logs, read-only runs, language/compiler overrides, loader arguments, analysis timeouts, shared-server URLs, and `HeadlessScript` continuation controls.

See: `<skill-dir>/references/ghidra-headless-analysis.md`

### Analysis Workflow
Includes import discipline, analysis option capture, staged auto-analysis, manual function repair, xrefs, references, call trees, stack fixes, switch recovery, ARM/Thumb and raw firmware caveats, and evidence boundaries.

See: `<skill-dir>/references/ghidra-analysis-workflow.md`

### Decompiler and P-code
Includes `DecompInterface`, `FlatDecompilerAPI`, decompiler timeouts, token to address mapping, high p-code versus raw instruction p-code, p-code graph/export scripts, decompiler problem scripts, and "decompiler output is not source" guidance.

See: `<skill-dir>/references/ghidra-decompiler-pcode.md`

### Scripting and Automation
Includes Java GhidraScript, Jython/PyGhidra differences, `currentProgram`, transactions, monitors, script arguments, properties files, `println` versus stdout, PyGhidra project APIs, and repeatable JSON evidence extraction.

See: `<skill-dir>/references/ghidra-scripting-automation.md`

### Binary Search
Includes memory search, strings, defined strings, program text search, scalar search, direct-reference search, instruction pattern search, masked operands, and built-in search scripts for vulnerability triage.

See: `<skill-dir>/references/ghidra-search-triage.md`

### Data Types and Symbols
Includes GDT archives, PDB/DWARF ingestion, demangling, function signatures, stack variables, structure recovery, C++ RTTI/class recovery scripts, Function ID, and type-propagation evidence rules.

See: `<skill-dir>/references/ghidra-types-symbols.md`

### Diffing, Version Tracking, and BSim
Includes Program Diff, CodeCompare/Function Comparison, Version Tracking preconditions and correlator order, `AutoVersionTrackingScript`, BSim CLI, local H2 versus PostgreSQL databases, and patch-diff evidence bundles.

See: `<skill-dir>/references/ghidra-diffing-bsim-version-tracking.md`

### Debugging and Emulation
Includes GDB/LLDB/dbgeng/x64dbg/drgn agents, Trace RMI, remote target mapping, logical breakpoints, trace snapshots, Control Target/Trace/Emulator modes, p-code emulation schedules, unimplemented userops, and evidence capture.

See: `<skill-dir>/references/ghidra-debugging-emulation.md`
