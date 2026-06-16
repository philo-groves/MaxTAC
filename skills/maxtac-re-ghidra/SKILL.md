---
name: maxtac-re-ghidra
description: "Use this skill when binary reverse engineering needs Ghidra for headless analysis, decompilation, p-code inspection, scripting automation, binary search, data type recovery, version tracking, BSim similarity, debugging, or emulation."
---

# MaxTAC RE Ghidra
Ghidra is an NSA-maintained software reverse engineering framework with GUI and automated modes. It provides disassembly, decompilation, graphing, scripting, debugging, p-code emulation, program diffing, version tracking, BSim function similarity, and extension APIs across many executable formats and processor languages.

Use Ghidra when decompiler output, rich program databases, data type recovery, repeatable headless analysis, or cross-version markup transfer matters more than single-command terminal speed. Treat Ghidra output as an analysis database: record import settings, analysis options, manual repairs, script versions, and whether facts came from loader metadata, analyzers, decompiler output, or runtime traces.

## Readiness Check
Before using this skill, identify the Ghidra installation and the automation entrypoint. A release install normally exposes these launchers:

```bash
ghidraRun
support/analyzeHeadless
support/pyghidraRun
```

On Windows:

```powershell
ghidraRun.bat
support\analyzeHeadless.bat
support\pyghidraRun.bat
```

Check Java and Ghidra paths:

```bash
java -version
"$GHIDRA_HOME/support/analyzeHeadless" -help
python -c "import pyghidra; print(pyghidra.__version__)"
```

If Ghidra is not installed, ask before installing. Official prebuilt releases require a 64-bit JDK 21, and the correct release asset is the `ghidra_<version>_<release>_<date>.zip` archive, not GitHub's generated source archives.

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
