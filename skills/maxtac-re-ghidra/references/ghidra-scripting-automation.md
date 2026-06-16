# Ghidra Scripting and Automation

Use this reference when a Ghidra task needs repeatable extraction, batch
processing, project walking, custom analysis, or evidence generation. Prefer
small scripts that record input hashes, import settings, analysis options,
Ghidra version, script version, and output paths.

## Contents

- [Quick Patterns](#quick-patterns)
- [Script Types](#script-types)
- [Script Locations and Metadata](#script-locations-and-metadata)
- [Headless Arguments and Properties](#headless-arguments-and-properties)
- [Program Access](#program-access)
- [Transactions](#transactions)
- [Task Monitors](#task-monitors)
- [Logging](#logging)
- [PyGhidra](#pyghidra)
- [Java Script Skeleton](#java-script-skeleton)
- [PyGhidra Skeleton](#pyghidra-skeleton)
- [Automation Patterns](#automation-patterns)
- [Cautions](#cautions)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Patterns

Run a script over an existing program:

```bash
analyzeHeadless ./projects Case001 \
  -process target.bin \
  -scriptPath ./ghidra_scripts \
  -postScript CaseExport.java evidence/case001 \
  -readOnly
```

Run a PyGhidra CPython script through headless Ghidra:

```bash
analyzeHeadless ./projects Case001 \
  -process target.bin \
  -scriptPath ./ghidra_scripts \
  -postScript case_export.py evidence/case001
```

Use PyGhidra as a standalone Python library:

```python
import pyghidra

pyghidra.start(install_dir="/opt/ghidra")
with pyghidra.open_project("./projects", "Case001", create=False) as project:
    with pyghidra.program_context(project, "/target.bin") as program:
        print(program.getName())
```

## Script Types

Ghidra supports:

- Java `GhidraScript`.
- Java `HeadlessScript` for headless-only controls.
- Jython scripts from the Jython extension.
- PyGhidra CPython 3 scripts through the PyGhidra feature.
- Standalone PyGhidra Python using JPype to access Ghidra APIs.

Choose:

- Java for maximum compatibility with Ghidra APIs and existing scripts.
- PyGhidra for CPython libraries, JSON/report generation, and integration with
  external Python tooling.
- HeadlessScript only when script logic must control headless analysis or
  disposition.
- Jython only for legacy scripts; it is Python 2 semantics.

## Script Locations and Metadata

Default script locations include:

- `$USER_HOME/ghidra_scripts`
- `Ghidra/**/ghidra_scripts` inside the distribution
- Paths supplied with `-scriptPath`

Add a category header:

```java
//@category MaxTAC
```

Keep scripts deterministic:

- Avoid GUI prompts in headless paths.
- Accept output directories as script args.
- Fail closed on missing args.
- Use `monitor.isCancelled()` in loops.
- Write JSON/text artifacts explicitly.
- Keep the script source with evidence.

## Headless Arguments and Properties

Headless script arguments follow the script name:

```bash
-postScript CaseExport.java evidence/case001 strict
```

In Java:

```java
String[] args = getScriptArgs();
```

`askXxx()` methods consume script arguments in order. If arguments run out,
headless scripts can read values from a matching `.properties` file. Use
`-propertiesPath` when properties live outside the script directory.

Use explicit args for automation. Use `.properties` only when reusing scripts
that already depend on `askFile`, `askString`, `askAddress`, and related
methods.

## Program Access

Common GhidraScript globals:

```text
currentProgram
currentAddress
currentSelection
currentLocation
monitor
state
tool
```

Common program APIs:

```text
currentProgram.getListing()
currentProgram.getFunctionManager()
currentProgram.getSymbolTable()
currentProgram.getReferenceManager()
currentProgram.getMemory()
currentProgram.getDataTypeManager()
```

Useful `FlatProgramAPI` helpers:

```text
toAddr(...)
getFunctionAt(...)
getFunctionContaining(...)
getDataAt(...)
getInstructionAt(...)
getReferencesTo(...)
getReferencesFrom(...)
analyzeAll(...)
```

Avoid hidden GUI state in evidence scripts. Resolve addresses, functions, and
selections from explicit arguments whenever possible.

## Transactions

Program mutations must occur in a transaction. In Java GhidraScript, use:

```java
int tx = currentProgram.startTransaction("case edit");
try {
    // mutate symbols, comments, data types, references, bytes, etc.
}
finally {
    currentProgram.endTransaction(tx, true);
}
```

In PyGhidra:

```python
with pyghidra.transaction(program, "case edit"):
    # mutate program
```

Evidence rule:

- Read-only extraction scripts should not start write transactions.
- Scripts that mutate names, comments, types, references, or bytes must record
  the mutation summary.
- Do not save changed programs unless persistence is intentional.

## Task Monitors

Use `monitor` in Java scripts and `pyghidra.task_monitor()` in PyGhidra. Batch
scripts should support cancellation and timeouts.

PyGhidra timeout monitor:

```python
analysis_log = pyghidra.analyze(program, pyghidra.task_monitor(600))
```

Java loop pattern:

```java
while (iter.hasNext() && !monitor.isCancelled()) {
    Function f = iter.next();
}
```

## Logging

Use `println`, `printf`, and `printerr` in Java GhidraScript so output lands in
`-scriptlog`.

In Python scripts run by headless, ordinary `print` writes to stdout. Use
`println` when the script log is the evidence target.

Always produce machine-readable artifacts separately from logs. Logs are useful
for provenance and errors; JSON/CSV/text files are better for parsed evidence.

## PyGhidra

PyGhidra provides CPython 3 access to Ghidra APIs through JPype, plus a GUI
plugin and script provider. It is first-class in current Ghidra releases.

Setup:

```bash
pip install pyghidra
pip install ghidra-stubs==<version>
set GHIDRA_INSTALL_DIR=C:\Tools\ghidra
```

Linux/macOS:

```bash
export GHIDRA_INSTALL_DIR=/opt/ghidra
```

Key APIs:

```text
pyghidra.start()
pyghidra.started()
pyghidra.open_project(path, name, create=False)
pyghidra.open_filesystem(path)
pyghidra.program_loader()
pyghidra.consume_program(project, path)
pyghidra.program_context(project, path)
pyghidra.analyze(program, monitor)
pyghidra.ghidra_script(path, project, program=None)
pyghidra.transaction(program, description)
pyghidra.analysis_properties(program)
pyghidra.program_info(program)
pyghidra.task_monitor(timeout=None)
pyghidra.walk_project(project, callback)
pyghidra.walk_programs(project, callback)
```

Deprecated PyGhidra APIs such as `open_program()` and `run_script()` still exist
for compatibility, but prefer the newer project/program APIs for new
automation.

## Java Script Skeleton

```java
//@category MaxTAC

import java.io.File;
import java.io.FileWriter;

import com.google.gson.stream.JsonWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class CaseFunctionExport extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            printerr("usage: CaseFunctionExport <out.json>");
            return;
        }

        File out = new File(args[0]);
        try (JsonWriter w = new JsonWriter(new FileWriter(out))) {
            w.setIndent("  ");
            w.beginArray();
            FunctionIterator funcs = currentProgram.getListing().getFunctions(true);
            while (funcs.hasNext() && !monitor.isCancelled()) {
                Function f = funcs.next();
                w.beginObject();
                w.name("name").value(f.getName());
                w.name("entry").value(f.getEntryPoint().toString());
                w.name("body_size").value(f.getBody().getNumAddresses());
                w.endObject();
            }
            w.endArray();
        }
        println("wrote " + out.getAbsolutePath());
    }
}
```

## PyGhidra Skeleton

```python
import json
import pathlib

import pyghidra

project_dir = pathlib.Path("projects")
out_dir = pathlib.Path("evidence/case001")
out_dir.mkdir(parents=True, exist_ok=True)

pyghidra.start()
with pyghidra.open_project(project_dir, "Case001", create=False) as project:
    with pyghidra.program_context(project, "/target.bin") as program:
        listing = program.getListing()
        funcs = []
        it = listing.getFunctions(True)
        while it.hasNext():
            f = it.next()
            funcs.append({
                "name": str(f.getName()),
                "entry": str(f.getEntryPoint()),
                "body_size": int(f.getBody().getNumAddresses()),
            })

(out_dir / "functions.json").write_text(
    json.dumps(funcs, indent=2, sort_keys=True),
    encoding="utf-8",
)
```

## Automation Patterns

Batch function inventory:

- Export functions, entry points, body sizes, thunks, external status, tags.
- Include hashes and import settings.
- Preserve the script and raw output.

Dangerous import caller map:

- Enumerate imports and symbols.
- Filter risky names.
- Use `ReferenceManager` to find references to import addresses.
- Export callsite address, containing function, and decompiler snippet only as
  supporting context.

String xref bundle:

- Enumerate defined strings or memory-search hits.
- Find references to each string address.
- Export containing functions, string values, addresses, and xref types.

Decompiler export:

- Use `DecompInterface` with timeout.
- Export status, warnings, C text, and selected p-code facts.
- Record function repair/type assumptions.

Project walker:

- Use PyGhidra `walk_programs`.
- Catch and record per-program exceptions.
- Avoid silently skipping unsupported files.

## Cautions

- Java scripts and PyGhidra scripts run inside the Ghidra trust boundary. Do not
  execute untrusted scripts from samples.
- Script Manager GUI state is not evidence. Save scripts and output files.
- CPython/PyGhidra and Jython differ; do not assume one script runs unchanged in
  the other.
- Long-running decompiler or analysis loops need timeouts and cancellation.
- Ghidra Java objects often need explicit release or context management.
- Mutating scripts can change later analysis results; record all changes.
- Do not scrape GUI text when APIs expose structured objects.

## Evidence Checklist

Capture:

- Ghidra install/release and PyGhidra version.
- Script source path and hash.
- Script arguments and properties files.
- Project path, program path, and target hash.
- Whether the script mutates program state.
- Transaction descriptions for mutations.
- Timeout/cancel/error state.
- Raw JSON/text artifacts and script logs.
- Known API assumptions and fallback behavior.

## Official Source Paths

- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/java/ghidra/app/script/GhidraScript.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/GhidraScriptMgrPlugin/ScriptDevelopment.htm
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/PyGhidra/README.md
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/PyGhidra/src/main/py/README.md
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/ghidra_scripts/ExportFunctionInfoScript.java
