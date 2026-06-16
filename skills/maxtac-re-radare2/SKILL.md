---
name: maxtac-re-radare2
description: Use the radare2 framework for binary reverse engineering, binary analysis, binary expression/string searches, binary diffing, binary debugging, ESIL emulation, and hex utilities.
---

# MaxTAC RE with Radare2
r2 provides a set of libraries, tools and plugins to ease reverse engineering tasks. r2 can edit files on local hard drives, view kernel memory, and debug programs locally or via a remote gdb/windbg servers. r2's wide architecture support allows you to analyze, emulate, debug, modify, and disassemble any binary.

## Readiness Check
Before using this skill, ensure Radare2 is installed and properly configured on the system. Check if Radare2 is accessible by running:
```
r2 --version
```

If there is no output or an error occurs, Radare2 may not be installed. Follow the installation instructions:

1. Ask the user for permission to install Radare2 if it is not already installed.
2. If permission is granted, install Radare2 using the per-system instructions below.

### Linux / macOS Install
Supports meson/ninja (muon/samu also works) and make builds.

```
git clone https://github.com/radareorg/radare2
radare2/sys/install.sh
```

### Windows Install (Powershell)
Requires meson and msvc or mingw as compilers.

```
git clone https://github.com/radareorg/radare2
preconfigure.bat       REM setup python, meson, ninja
configure.bat          REM run meson b + vs project
make.bat               REM run ninja -C b
prefix\bin\radare2.exe
```

## Usage Guidance

### Binary Triage
Includes `rabin2 -I/-j/-i/-E/-s/-l/-S/-z/-P/-PP` for metadata, hardening flags, imports, symbols, libraries, sections, strings, DWARF/PDB. `rabin2 -I` is especially useful because it exposes NX, RELRO, canary, PIE/PIC, RPATH, stripped/static state, arch, bits, endian, and format data.

See: `<skill-dir>/references/radare2-binary-triage.md`

### Binary Search
Includes `rafind2` plus in-session `/` searching for strings, wide strings, regex, byte patterns, aligned/ranged hits, magic/file carving, JSON output, and r2-command output. Add vulnerability-specific sections for suspicious strings, format strings, command paths, deserialization markers, crypto material, and gadget discovery.

See: `<skill-dir>/references/radare2-search.md`

### Analysis Workflow
Includes `aa/aaa/aab/aaaa`, `r2 -A/-AA, af*`, `afl/aflj`, `afi`, `afv`, `aft`, `ax*`, CFG/call graph workflows, and “do not overtrust auto-analysis” guidance. Use different analysis depths and fine-grained `anal.*` / `emu.*` configuration.

See: `<skill-dir>/references/radare2-analysis-workflow.md`

### ESIL Emulation
Includes ESIL for partial emulation, indirect branch resolution, branch likelihood, computed pointer references, syscall/import simulation, and function-slice execution. This is high-value for exploitability reasoning when source is absent.

See: `<skill-dir>/references/radare2-esil-emulation.md`

### Debugging
Includes local debugging commands (`r2 -d`, `db`, `dc`, `dr`, `drr`, `ds`, `dso`, `dbt`, `dm`, `ood`), plus memory maps, heap, remote GDB/WinDbg as advanced sections.

See: `<skill-dir>/references/radare2-debugging.md`

### Diffing
Includes `radiff2` for patched-vs-vulnerable comparison: raw diff, delta diff, code graph diff, imports/strings diff, architecture/bits settings, JSON output, and r2 patch-script output.

See: `<skill-dir>/references/radare2-diffing.md`

### Utilities
Includes `rax2`, `rasm2`, `rahash2`, maybe `ragg2`. Prioritize `rax2` for conversions/endian/base64/raw-hex tasks and `rasm2` for multi-arch assemble/disassemble and ESIL expression output.

See: `<skill-dir>/references/radare2-utilities.md`

### Automation
Includes `r2pipe`, JSON-first command usage, repeatable command scripts, project/annotation notes. `r2pipe` supports spawn pipes, HTTP, TCP, and JSON-friendly workflows, which fits MaxTAC evidence collection well.

See: `<skill-dir>/references/radare2-automation.md`
