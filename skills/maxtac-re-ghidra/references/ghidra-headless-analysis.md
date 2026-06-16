# Ghidra Headless Analysis

Use this reference when a Ghidra task needs repeatable import, analysis,
scripting, or evidence extraction without the GUI. `analyzeHeadless` is the
supported command-line entrypoint for local projects and Ghidra Server
repositories. It can create/populate projects, analyze imported or existing
programs, run pre/post scripts, and control program disposition.

## Contents

- [Quick Commands](#quick-commands)
- [Mental Model](#mental-model)
- [Import Versus Process](#import-versus-process)
- [Project Layout](#project-layout)
- [Script Loading](#script-loading)
- [Logging and Evidence](#logging-and-evidence)
- [Language, Compiler, and Loader Control](#language-compiler-and-loader-control)
- [Analysis Control](#analysis-control)
- [HeadlessScript Controls](#headlessscript-controls)
- [Shared Project Mode](#shared-project-mode)
- [Wildcards and Recursion](#wildcards-and-recursion)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

Locate the launcher:

```bash
ls "$GHIDRA_HOME/support/analyzeHeadless"
```

Windows:

```powershell
Get-Item "$env:GHIDRA_HOME\support\analyzeHeadless.bat"
```

Create a project, import one sample, analyze it, and keep the project:

```bash
"$GHIDRA_HOME/support/analyzeHeadless" ./ghidra-projects Case001 \
  -import ./samples/target.bin \
  -overwrite \
  -analysisTimeoutPerFile 600 \
  -log evidence/case001/analyze.log \
  -scriptlog evidence/case001/script.log
```

Import without analysis when loader/language assumptions need inspection first:

```bash
"$GHIDRA_HOME/support/analyzeHeadless" ./ghidra-projects Case001 \
  -import ./samples/blob.bin \
  -noanalysis \
  -processor "x86:LE:64:default" \
  -cspec "gcc" \
  -overwrite
```

Process an existing project file with a post-script:

```bash
"$GHIDRA_HOME/support/analyzeHeadless" ./ghidra-projects Case001 \
  -process target.bin \
  -postScript ExportFunctionInfoScript.java functions.json \
  -readOnly \
  -scriptlog evidence/case001/functions.script.log
```

Use a custom script directory:

```bash
"$GHIDRA_HOME/support/analyzeHeadless" ./ghidra-projects Case001 \
  -process target.bin \
  -scriptPath "$PWD/ghidra_scripts;$GHIDRA_HOME/Ghidra/Features/Base/ghidra_scripts" \
  -postScript CaseExport.java evidence/case001
```

Create a disposable project:

```bash
"$GHIDRA_HOME/support/analyzeHeadless" ./scratch ScratchCase \
  -import ./sample.bin \
  -postScript CaseExport.java evidence/scratch \
  -deleteProject
```

## Mental Model

Headless execution has three phases per program:

- Pre-scripts.
- Analysis, unless disabled with `-noanalysis` or a pre-script.
- Post-scripts.

Use pre-scripts for import placement, analyzer option changes, disabling
analysis, library paths, or other setup that must happen before analysis. Use
post-scripts for extraction after analyzers and decompiler-facing metadata have
settled.

Do not treat a headless run as a stateless CLI query. It mutates a Ghidra
project unless `-readOnly`, `-deleteProject`, script continuation controls, or
script logic prevent persistence. Record whether the run saved program changes.

## Import Versus Process

`-import` and `-process` are mutually exclusive.

Use `-import` when:

- The binary is not already in the Ghidra project.
- Loader/language/compiler settings need to be applied.
- A directory or supported container should be imported recursively.
- You want a clean project state per case.

Use `-process` when:

- The program already exists in the project.
- You want to run analysis or scripts over a known project file.
- You need to re-run evidence extraction without re-importing.
- You are processing a shared Ghidra repository object.

`-process` without a project file processes all files in the selected project
folder. Quote wildcard patterns to stop the shell from expanding them first:

```bash
"$GHIDRA_HOME/support/analyzeHeadless" ./ghidra-projects Case001 \
  -process '*.exe' \
  -recursive \
  -postScript CaseExport.java evidence/case001
```

## Project Layout

The first positional argument is either:

- Local project parent directory plus project name/folder path.
- A `ghidra://` server repository URL.

Local example:

```bash
analyzeHeadless ./projects Case001/Firmware -import firmware.bin
```

This creates or opens project `Case001` under `./projects` and imports beneath
project folder `/Firmware`.

Do not run headless against a project that is open in the GUI. Upstream
documentation notes that the Headless Analyzer may not run when the project is
already open.

## Script Loading

`-preScript` and `-postScript` take script names, not paths:

```bash
-postScript CaseExport.java arg1 arg2
```

Find scripts through:

- `$USER_HOME/ghidra_scripts`
- Every `ghidra_scripts` directory inside the Ghidra distribution
- Extra paths supplied by `-scriptPath`

On Windows and Unix, `-scriptPath` uses semicolon-separated paths. In Unix
shells, escape `$GHIDRA_HOME` if the value should be expanded by Ghidra instead
of the shell:

```bash
-scriptPath "\$GHIDRA_HOME/Ghidra/Features/Base/ghidra_scripts;/case/scripts"
```

Use `-propertiesPath` for `.properties` files consumed by `askXxx()` methods.
Script-specific arguments are consumed before properties-file values.

## Logging and Evidence

Use both logs:

```bash
-log evidence/case001/analyze.log
-scriptlog evidence/case001/script.log
```

`-log` captures analysis and non-script processing. `-scriptlog` captures
GhidraScript logging. Java scripts should use `println`, `printf`, or
`printerr`. In Python scripts, ordinary `print` writes to stdout; use
`println` for the script log.

Capture:

- Full command line.
- Ghidra version and install path.
- Project path and project folder path.
- Import/process target names.
- `-processor`, `-cspec`, `-loader`, and `-loader-*` values.
- `-analysisTimeoutPerFile`, `-max-cpu`, and analysis option changes.
- Script names, hashes, arguments, and logs.

## Language, Compiler, and Loader Control

For raw blobs, firmware, odd containers, and misdetected binaries, force loader
settings instead of accepting a guessed language:

```bash
-processor "ARM:LE:32:v8"
-cspec "default"
-loader "BinaryLoader"
```

Language IDs and compiler spec IDs are defined in processor `.ldefs` files
under:

```text
Ghidra/Processors/<processor>/data/languages/*.ldefs
```

Rules:

- `-processor` can be used without `-cspec`.
- `-cspec` requires `-processor`.
- The IDs are case-sensitive.
- Loader-specific arguments use `-loader-<argument-name> <value>`.
- `-librarySearchPaths` affects library resolution during import/analysis.

Evidence should preserve the exact language and compiler spec because calling
conventions, decompiler parameter recovery, stack analysis, and p-code
semantics depend on them.

## Analysis Control

Analysis runs by default during import or process unless `-noanalysis` is set.

Set a hard per-file timeout:

```bash
-analysisTimeoutPerFile 600
```

If analysis times out, completed analyzer results may still be saved. A
post-script can detect timeout status with the headless API and should record it
as a limitation, not as absence of findings.

Use `-max-cpu` to cap parallelism in shared hosts or CI:

```bash
-max-cpu 4
```

Do not assume all analyzers are available for every target. Analyzer
availability and options depend on processor language, compiler spec, file
format, installed extensions, and whether an analyzer is marked prototype.

## HeadlessScript Controls

Use `HeadlessScript` only for headless-specific control. It extends
`GhidraScript`, but calling headless-only methods in the GUI can throw.

Pre-script: enable or disable analysis for subsequent programs:

```java
enableHeadlessAnalysis(false);
boolean enabled = isHeadlessAnalysisEnabled();
```

Pre-script: change import folder for future imported programs:

```java
setHeadlessImportDirectory("triage/interesting");
setHeadlessImportDirectory(null);
```

Pass state between headless scripts:

```java
storeHeadlessValue("caseId", "CASE-001");
Object caseId = getStoredHeadlessValue("caseId");
boolean exists = headlessStorageContainsKey("caseId");
```

Control disposition after the current script completes:

```java
setHeadlessContinuationOption(HeadlessContinuationOption.ABORT);
setHeadlessContinuationOption(HeadlessContinuationOption.ABORT_AND_DELETE);
setHeadlessContinuationOption(HeadlessContinuationOption.CONTINUE_THEN_DELETE);
setHeadlessContinuationOption(HeadlessContinuationOption.CONTINUE);
```

Deletion in `-process` mode requires `-okToDelete`. Use deletion options only in
disposable projects or with explicit evidence policy.

## Shared Project Mode

Use `ghidra://<server>[:<port>]/<repository_name>[/folder]` for a Ghidra Server
repository:

```bash
analyzeHeadless ghidra://server.example:13100/Repo/Firmware \
  -process target.bin \
  -postScript CaseExport.java evidence/case001 \
  -connect analyst \
  -p \
  -commit "case001 evidence extraction"
```

Shared-mode options include:

- `-connect [userID]`
- `-p` for password prompt
- `-keystore <path>` for PKI/SSH authentication
- `-commit ["comment"]`

Treat shared project runs as evidence-custody events. Record checkout/checkin
state, commit comments, and whether scripts modified destination programs.

## Wildcards and Recursion

In `-import` mode, wildcard expansion is performed by the operating-system
shell. In `-process` mode, Ghidra expands `*` and `?` against project files.

Use `-recursive [depth]` for filesystem/project recursion. When importing
containers, the depth controls nested container recursion. A depth of `0`
prevents recursion into container files.

Hidden files whose names start with `.` are ignored by default during bulk
directory import unless explicitly named.

## Failure Modes

Project is already open

Close the GUI project or use a separate copy. Do not force-delete lock files.

Script not found

Pass the script name only to `-postScript` or `-preScript`, and put its
directory in `-scriptPath`.

Unexpected language or decompiler output

Re-import with explicit `-processor`, `-cspec`, loader, and base settings. Do
not repair a mis-imported program and then forget to record the import
override.

No output in `script.log`

Use GhidraScript `println`/`printerr`; Python `print` goes to stdout.

Timeout but partial facts exist

Capture timeout status. Partial analyzer output is useful for triage but weak
as proof.

Deletion did not occur

`-process` deletion controls require `-okToDelete`. `-readOnly` prevents
deleting processed programs.

## Evidence Checklist

Capture:

- Ghidra version, install path, Java version, and host OS.
- Upstream source/release version if using development builds.
- Full headless command and environment variables.
- Project location, project name, project folder path, and shared URL if used.
- Target hashes before import.
- Loader, language ID, compiler spec ID, image base, and library search paths.
- Analysis timeout, CPU cap, analyzer option changes, and timeout status.
- Script file hashes, arguments, properties files, script output, and logs.
- Whether the project/program was saved, read-only, deleted, or committed.
- Any headless continuation options used by scripts.

## Official Source Paths

- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/RuntimeScripts/support/analyzeHeadlessREADME.md
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/HeadlessAnalyzer/HeadlessAnalyzer.htm
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/java/ghidra/app/util/headless/HeadlessScript.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/ghidra_scripts/SetHeadlessContinuationOptionScript.java
