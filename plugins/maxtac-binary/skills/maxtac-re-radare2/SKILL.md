---
name: maxtac-re-radare2
description: "Use this skill when binary reverse engineering needs radare2 for binary analysis, expression or string search, binary diffing, debugging, ESIL emulation, or hex utilities."
---

# MaxTAC RE Radare2
Use radare2 when binary triage, search, diffing, ESIL, quick disassembly, or terminal-first automation is more useful than a persistent GUI project.

## Readiness Check
Check the installed tool surface:

```
r2 -v
rabin2 -v
rahash2 -v
```

If radare2 is not installed or a source build is needed, ask first, then read `<skill-dir>/references/radare2-install-build.md`.

Use the generic RE readiness helper from the Ghidra skill to record tool versions and target hashes before report-grade RE work:

```
python3 <plugin-root>/skills/maxtac-re-ghidra/scripts/re-readiness.py --tool radare2 --target ./target.bin --output re-readiness.md
```

Use `python3 <skill-dir>/scripts/r2-triage.py` to collect repeatable binary triage evidence with `rabin2`, `rahash2`, and optional read-only `r2` analysis:

```
python3 <skill-dir>/scripts/r2-triage.py ./target.bin --output-dir ./r2-evidence
```

Use `--skip-r2` when only metadata/hashes are needed, and `--deep` only when deeper `r2` analysis is worth the runtime.

Store r2 scripts, command transcripts, JSON, disassembly dumps, graph exports, and hashes as artifacts. When RE establishes reusable subsystem behavior, rewrite the conclusion into the stable research-library markdown and link to the artifact directory. Avoid creating `research/<component>/r2/` as a research submodule unless radare2 itself is the target.

## Usage Guidance

### Binary Triage
Includes `rabin2 -I/-j/-i/-E/-s/-l/-S/-z/-P/-PP` for metadata, hardening flags, imports, symbols, libraries, sections, strings, DWARF/PDB. `rabin2 -I` is especially useful because it exposes NX, RELRO, canary, PIE/PIC, RPATH, stripped/static state, arch, bits, endian, and format data.

See: `<skill-dir>/references/radare2-binary-triage.md`

### Binary Search
Includes `rafind2` plus in-session `/` searching for strings, wide strings, regex, byte patterns, aligned/ranged hits, magic/file carving, JSON output, and r2-command output. Add vulnerability-specific sections for suspicious strings, format strings, command paths, deserialization markers, crypto material, and gadget discovery.

See: `<skill-dir>/references/radare2-search.md`

### Analysis Workflow
Includes `aa/aaa/aab/aaaa`, `r2 -A/-AA, af*`, `afl/aflj`, `afi`, `afv`, `aft`, `ax*`, CFG/call graph workflows, and "do not overtrust auto-analysis" guidance. Use different analysis depths and fine-grained `anal.*` / `emu.*` configuration.

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
