---
name: maxtac-re-jadx
description: "Use this skill when Android reverse engineering needs JADX for APK, DEX, JAR, AAR, AAB, smali, resource decoding, deobfuscation, mappings, GUI search, smali debugging, API automation, or plugin workflows."
---

# MaxTAC RE JADX
Use JADX when readable Java/Kotlin-adjacent output, decoded Android resources, manifest triage, deobfuscation mappings, GUI navigation, or repeatable JSON/API extraction is more useful than raw Dalvik disassembly alone.

Treat JADX output as a decompiler hypothesis. Preserve the original APK/DEX, record tool version and options, and verify security-sensitive claims against smali, dex offsets, resource tables, runtime behavior, or independent tooling when the decompiled Java is ambiguous.

## Readiness Check
Identify the installed CLI/GUI entrypoints and Java state:

```bash
jadx --version
jadx --help
jadx-gui --help
java -version
```

On Windows, use the `.bat` launchers when the release `bin` directory is not on `PATH`. If JADX is not installed, ask before installing.

Use the generic RE readiness helper from the Ghidra skill to record Java/JADX availability and input hashes before report-grade Android RE work:

```
python3 <plugin-root>/skills/maxtac-re-ghidra/scripts/re-readiness.py --tool jadx --target ./target.apk --output re-readiness.md
```

When the MaxTAC MCP server is available, prefer `re_readiness_check` for this readiness evidence before falling back to `re-readiness.py`.

Use `python3 <skill-dir>/scripts/jadx-export.py` to preserve input hashes, JADX version, export mode, deobfuscation flags, plugin options, CFG settings, and the exact command line. It plans by default and only executes with `--run`:

```
python3 <skill-dir>/scripts/jadx-export.py ./target.apk \
  --output-dir ./jadx-evidence \
  --mode all \
  --deobf \
  --cfg
```

When the MaxTAC MCP server is available, prefer `jadx_export` before invoking `jadx-export.py` directly. It calls the same planner/runner and returns the generated manifest JSON.

Add `--run` only after reviewing the generated command in `command.txt`.

## Usage Guidance

### CLI, Export, and Batch Runs
Includes output directory controls, source/resource-only runs, single-class decompilation, JSON output, Gradle export templates, configs, plugin options, exit-code handling, logs, filesystem/cache/temp locations, and repeatable evidence capture.

See: `<skill-dir>/references/jadx-cli-export.md`

### Decompilation Workflow
Includes decompilation modes, transformation toggles, bad-code handling, debug line metadata, raw smali comparison, dex offset evidence, fallback/simple modes, CFG dot output, Kotlin/anonymous/inner-class caveats, and correctness checks.

See: `<skill-dir>/references/jadx-decompilation-workflow.md`

### Android Resources
Includes manifest and `resources.arsc` decoding, resource-only workflows, resource aliasing, obfuscated resource extensions, APK/AAB/AAR/XAPK/APKM inputs, native library/assets triage, Gradle export type detection, and resource evidence checklists.

See: `<skill-dir>/references/jadx-android-resources.md`

### Search, Renaming, and Mappings
Includes GUI search provider behavior, raw versus alias names, comment search, resource search size/type filters, mapping formats and modes, JOBF generated renames, source-name aliases, rename flags, filesystem case handling, and deobfuscation evidence rules.

See: `<skill-dir>/references/jadx-search-renaming-mappings.md`

### Automation, API, and Plugins
Includes `JadxArgs`, `JadxDecompiler`, lazy class decompilation, `JavaClass` and `JavaMethod` APIs, code metadata, resource loading, JSON evidence extraction, custom code/resource inputs, plugin passes, plugin options, plugin installation, and cache/hash discipline.

See: `<skill-dir>/references/jadx-automation-api-plugins.md`

### GUI Debugging and Evidence
Includes `.jadx` project files, code/comment/rename persistence, GUI cache behavior, smali debugger/JDWP attachment, breakpoints, stepping, runtime register/field reads and writes, export dialog behavior, and handoff artifacts.

See: `<skill-dir>/references/jadx-gui-debugging-evidence.md`

### Security and Failure Modes
Includes default XML/ZIP protections, path traversal and zip bomb checks, environment-variable overrides, hostile archive handling, no-class/resource-only runs, analysis errors, plugin risk, and lab-only safety controls.

See: `<skill-dir>/references/jadx-security-failure-modes.md`
