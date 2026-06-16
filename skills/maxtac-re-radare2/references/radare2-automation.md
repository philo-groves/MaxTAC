# Radare2 Automation

Use radare2 automation when a binary-research task needs repeatable evidence,
batch processing, structured output, or consistent analysis across many samples.
Prefer JSON-first commands and small scripts that record their inputs, analysis
depth, radare2 version, and output files.

Automation should make evidence more reliable, not hide uncertainty. Keep raw
artifacts, command transcripts, and versioned scripts with every finding. Treat
debugging, patching, shell execution, and writable sessions as state-changing
operations that must be called out explicitly.

## Contents

- [Quick Commands](#quick-commands)
- [Automation Mental Model](#automation-mental-model)
- [Command-Line Batch Runs](#command-line-batch-runs)
- [JSON-First Command Usage](#json-first-command-usage)
- [Command Syntax for Automation](#command-syntax-for-automation)
- [Loops and Foreach](#loops-and-foreach)
- [Macros and Aliases](#macros-and-aliases)
- [R2pipe](#r2pipe)
- [R2pipe2](#r2pipe2)
- [R2JS](#r2js)
- [Search Hooks](#search-hooks)
- [RTables and Comma Queries](#rtables-and-comma-queries)
- [Projects, Scripts, and Annotations](#projects-scripts-and-annotations)
- [Automation Patterns for Vulnerability Research](#automation-patterns-for-vulnerability-research)
- [Evidence Checklist](#evidence-checklist)
- [Cautions](#cautions)
- [Official References](#official-references)

## Quick Commands

One-shot r2 runs:

```text
r2 -q -c "iIj" -c "q" sample.bin
r2 -Aq -c "aflj" -c "q" sample.bin
r2 -q -i triage.r2 sample.bin
r2 -qi triage.r2 sample.bin
r2 -q -c "aaa" -c "aflj" -c "q" sample.bin > funcs.json
```

Script file:

```text
e scr.color=false
e scr.utf8=false
e cfg.sandbox=true
aaa
iIj > info.json
iSj > sections.json
aflj > functions.json
q
```

JSON-oriented r2 commands:

```text
ij
iIj
iSj
iij
isj
izj
aflj
afij @ sym.func
pdfj @ sym.func
pdj 20 @ sym.func
aoj @ sym.func
axtj @ sym.func
agfj @ sym.func
```

Offline utility JSON:

```text
rabin2 -Ij sample.bin > info.json
rabin2 -Sj sample.bin > sections.json
rabin2 -ij sample.bin > imports.json
rabin2 -sj sample.bin > symbols.json
rabin2 -zj sample.bin > strings.json
radiff2 -j -d old.bin new.bin > data-diff.json
rafind2 -j -S passwd sample.bin > hits.json
```

R2pipe Python skeleton:

```python
import json
import pathlib
import r2pipe

path = pathlib.Path("sample.bin")
r2 = r2pipe.open(str(path))
try:
    r2.cmd("e scr.color=false")
    r2.cmd("aaa")
    data = {
        "info": r2.cmdj("iIj"),
        "functions": r2.cmdj("aflj"),
        "imports": r2.cmdj("iij"),
        "strings": r2.cmdj("izj"),
    }
finally:
    r2.quit()

path.with_suffix(".r2triage.json").write_text(
    json.dumps(data, indent=2, sort_keys=True)
)
```

Loops and output evaluation:

```text
afi @@f ~name
ao @@=$$ $$+2
pi 1 @@.offsets.txt
.!rabin2 -rs $R2_FILE
f* > flags.r2
. flags.r2
```

R2JS:

```text
r2 -qi script.r2.js sample.bin
r2 -j
-j
```

Search hook:

```text
e cmd.hit = p8 16
/ lib
e cmd.hit = . hit-script.r2
```

Projects and annotations:

```text
P+case-name
P* > project-state.r2
Pze case-name.zrp
Pzi case-name.zrp
ano=base64:...
anos
ano*
```

## Automation Mental Model

Radare2 automation has four useful layers:

- Single-command batch runs with `r2 -q -c ...`.
- Repeatable `.r2` command scripts loaded with `-i` or `.`.
- In-process shell features such as `;`, `@`, `@@`, backticks, `~`, `*`, and
  redirection.
- External language bindings through `r2pipe`, or embedded JavaScript through
  `r2js`.

Choose the smallest layer that keeps the task repeatable:

- Use `rabin2`, `rafind2`, `radiff2`, `rasm2`, and `rahash2` for direct
  command-line facts.
- Use `r2 -q -c` for a short, deterministic r2 query.
- Use `.r2` scripts when you need multiple commands, flags, comments, or
  repeatable setup.
- Use `r2pipe` when you need loops, joins, filtering, JSON validation, file
  output, or cross-sample logic.
- Use `r2js` when you want an embedded script without depending on external
  Python, Node, or shell tooling.
- Use projects for analyst session state, not as the only source of truth for
  evidence automation.

Good automation records:

- Input hash and path.
- Tool versions.
- Analysis depth and configuration.
- Exact commands and scripts.
- JSON and human-readable artifacts.
- Any mutable state changes.

## Command-Line Batch Runs

Use quiet batch runs for simple extraction:

```text
r2 -q -c "iIj" -c "q" sample.bin
r2 -q -c "aaa" -c "aflj" -c "q" sample.bin
```

The common pattern is:

- `-q`: quiet output.
- `-c`: execute one command.
- `-i`: run a script file.
- `q`: quit explicitly after command execution.

Use `-A` only when automatic analysis is part of the evidence:

```text
r2 -Aq -c "aflj" -c "q" sample.bin > functions.json
```

Prefer explicit analysis commands inside scripts when you need to record the
exact depth:

```text
e scr.color=false
e scr.utf8=false
aa
aflj > functions-aa.json
aaa
aflj > functions-aaa.json
q
```

Batch script example:

```text
r2 -qi triage.r2 sample.bin
```

`triage.r2`:

```text
e scr.color=false
e scr.utf8=false
e asm.bytes=false
iIj > info.json
iSj > sections.json
iij > imports.json
izj > strings.json
aaa
aflj > functions.json
q
```

Use deterministic settings:

```text
e scr.color=false
e scr.utf8=false
e cfg.sandbox=true
```

`cfg.sandbox` restricts filesystem, socket, and execution APIs. Enable it for
read-only extraction scripts unless the script intentionally needs shell or file
write behavior.

## JSON-First Command Usage

Prefer commands ending in `j` when a script will parse output:

```text
ij
iIj
iSj
iij
isj
izj
aflj
afij @ sym.func
pdfj @ sym.func
pdj 20 @ sym.func
aoj @ 0x401000
axtj @ sym.func
agfj @ sym.func
```

Useful JSON groups:

- `ij`: broad binary and core information.
- `iIj`: binary header and hardening-oriented info.
- `iSj`: sections.
- `iij`: imports.
- `isj`: symbols.
- `izj`: strings.
- `aflj`: function list.
- `afij`: function details.
- `pdfj` or `pdj`: disassembly details.
- `aoj`: one or more analyzed opcodes.
- `axtj`: xrefs.
- `agfj`: function graph.

Use utility JSON for facts that do not require an r2 session:

```text
rabin2 -Ij sample.bin
rabin2 -Sj sample.bin
rabin2 -ij sample.bin
rabin2 -sj sample.bin
rabin2 -zj sample.bin
rafind2 -j -S marker sample.bin
radiff2 -j -d old.bin new.bin
```

Pretty-print inside r2 when reading manually:

```text
ij~{}
aflj~{}
```

Use JSON as the parser boundary:

- Do not scrape columns when a `j` variant exists.
- Validate that `cmdj` returned a list or object before indexing it.
- Keep the raw JSON artifact next to summarized findings.
- Note the radare2 version because JSON shape can shift across versions.

When no JSON variant exists, prefer:

- `*` output as r2 commands for reloadable state.
- `~` filters for quick interactive narrowing.
- RTables or comma queries for table-like output.
- A small wrapper that keeps the raw text with parsed output.

## Command Syntax for Automation

Radare2 command syntax is automation-friendly. Important operators:

```text
cmd1 ; cmd2          run commands sequentially
cmd | external       pipe r2 output to external shell command
cmd~filter           use built-in grep/filter
cmd > file           redirect output
cmd >> file          append output
cmd @ addr           run at temporary seek
cmd @@ items         foreach over items
`cmd`                substitute command output as an argument
. cmd                evaluate command output as r2 commands
* suffix             emit r2 commands when supported
j suffix             emit JSON when supported
```

Examples:

```text
pd 20~call
pd 5 @ sym.main
px 32 @ `ao~ptr[1]`
px 32 @ sym.buf > buf.hex
f* > flags.r2
. flags.r2
.!rabin2 -rs $R2_FILE
```

Use `~` instead of shell pipes when portability matters:

```text
afl~sym.imp
iij~strcpy
pd 200~call
ij~{}
```

Use shell pipes only when external tooling is explicitly available:

```text
aflj | jq length
pd 200 | grep call
```

Environment variables are exposed to shell commands launched by r2:

```text
%~R2
!export | grep R2_
```

This can be useful for shell scripts, but it also expands the attack surface.
Avoid shell execution on untrusted samples unless the lab and script are
configured for that risk.

## Loops and Foreach

Use foreach syntax for interactive or script-level repetition.

Loop over flags:

```text
afi @@ fcn.*
afi @@f
afi @@f ~name
```

Loop over explicit expressions:

```text
ao @@=$$ $$+2
pd 1 @@=0x401000 0x401020 0x401040
```

Loop over offsets from a file:

```text
pi 1 @@.offsets.txt
```

Generate offsets:

```text
?v sym.main > offsets.txt
?v sym.main+4 >> offsets.txt
```

Common predefined iterators:

```text
@@f       all functions
@@i       all imports when supported by current command/context
@@s       symbols or strings depending on command/context
```

Use `@@?` and command-specific help in the live session because foreach
shortcuts vary by version and command.

Good loop uses:

- Print `afi` or `afij` for every function.
- Dump callsites for every dangerous import.
- Search each section or mapped range.
- Apply a comment or flag to a known offset list.
- Extract opcode metadata around candidate sinks.

Avoid loops for large exports when JSON list commands already exist. For example,
prefer `aflj` over scraping `afi @@f` when you only need function metadata.

## Macros and Aliases

Macros group commands inside an r2 session:

```text
(triage; iIj; iij; izz)
.(triage)
```

List macros:

```text
(*
```

Remove a macro:

```text
(-triage)
```

Macros can take positional arguments:

```text
(around n step; pd $0; s +$1)
.(around 8 4)
```

Command aliases use `$`:

```text
$disas=pdf
$disas @ main
$pmore='b 300; px'
$pmore?
$pmore=
```

Aliases can also hold data or virtual files:

```text
$blob=base64:QUJDRA==
$note=$candidate sink reached by parser
echo hello > $world
cat $world
rm $world
```

Use macros and aliases for:

- Repeated interactive triage commands.
- Short-lived analyst helpers.
- Local views such as "show function, xrefs, and strings."
- Reducing typo risk during a live session.

For durable automation, prefer `.r2` files or r2pipe scripts over macros typed
only in an interactive session.

## R2pipe

`r2pipe` controls radare2 from external languages. The book describes support
for spawn pipes, HTTP queries, TCP sockets, and other transports across multiple
language bindings. Use r2pipe when the task needs real programming features:
loops, joins, JSON validation, multiple files, stable output paths, or report
bundles.

Python install:

```text
python -m pip install r2pipe
```

Minimal Python:

```python
import r2pipe

r2 = r2pipe.open("sample.bin")
try:
    r2.cmd("aaa")
    print(r2.cmd("afl"))
    funcs = r2.cmdj("aflj")
finally:
    r2.quit()
```

Batch triage script:

```python
import json
import pathlib
import subprocess

import r2pipe

def run_text(args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)

def triage(path):
    path = pathlib.Path(path)
    r2 = r2pipe.open(str(path))
    try:
        r2.cmd("e scr.color=false")
        r2.cmd("e scr.utf8=false")
        r2.cmd("aaa")
        return {
            "file": str(path),
            "sha256": run_text(["rahash2", "-a", "sha256", str(path)]).strip(),
            "info": r2.cmdj("iIj"),
            "sections": r2.cmdj("iSj"),
            "imports": r2.cmdj("iij"),
            "symbols": r2.cmdj("isj"),
            "strings": r2.cmdj("izj"),
            "functions": r2.cmdj("aflj"),
        }
    finally:
        r2.quit()

for sample in pathlib.Path("samples").glob("*"):
    if sample.is_file():
        out = triage(sample)
        sample.with_suffix(sample.suffix + ".r2.json").write_text(
            json.dumps(out, indent=2, sort_keys=True)
        )
```

Use r2pipe patterns:

- Call `cmdj()` only for commands that actually return JSON.
- Close the pipe in `finally`.
- Keep analysis depth explicit: `aa`, `aaa`, or `aaaa`.
- Disable color and UTF-8 for text artifacts.
- Put one sample's artifacts in one directory.
- Store exceptions and partial output instead of silently skipping a sample.
- Time-box slow samples externally when batch processing unknown files.

R2pipe transports:

- Spawn pipe: local automation against one file.
- HTTP: remote or cloud-friendly command access.
- TCP: long-lived command transport.
- RAP and debugger transports: advanced cases where normal spawn is not enough.

Prefer spawn pipes for ordinary evidence scripts. Use HTTP/TCP only when there is
a specific operational reason, and protect the service from untrusted networks.

## R2pipe2

R2pipe2 adds a JSON request/response style using the `{` command introduced in
the radare2 5.9.x line. It returns more than plain command output, including
fields such as output, return value, return code, error state, and logs.

Interactive shape:

```text
{?
'{"cmd":"?e hello"}'
'{"cmd":"ij","json":true,"trim":true}'
```

R2pipe2 APIs expose helpers such as:

```text
r2.cmd2(...)
r2.cmd2j(...)
```

Use r2pipe2 when:

- You need error state, return code, and logs, not just stdout.
- You want to distinguish empty output from command failure.
- You are writing robust automation that must fail closed.
- You need a JSON envelope around non-JSON command output.

Fallback:

- If the installed radare2 or binding lacks r2pipe2 helpers, use `cmdj()` for
  JSON commands and keep explicit error handling around `cmd()` calls.
- Check `{?` in the target environment before committing to this path.

## R2JS

`r2js` is radare2's embedded QuickJS runtime. Use it for scripts that should run
inside radare2 without external language dependencies.

Run a script on launch:

```text
r2 -i foo.r2.js sample.bin
r2 -qi foo.r2.js sample.bin
```

Enter the JavaScript REPL:

```text
r2 -j
```

or from inside r2:

```text
-j
```

Inside r2js, the classic command interface is exposed through `R2Pipe`, and a
higher-level API is available through `R2Papi`:

```javascript
var r2 = new R2Pipe();
var R = new R2Papi(r2);
```

Use r2js for:

- Portable scripts distributed with analysis notes.
- Quick graph or metadata extraction.
- Project-local helpers without Python package installation.
- Scripts that benefit from running in the r2 process.

Use external r2pipe when:

- You need Python ecosystem libraries.
- You need filesystem traversal, multiprocessing, or rich report generation.
- You want independent process isolation from the r2 session.

## Search Hooks

`cmd.hit` runs a command for each search hit.

Simple hit action:

```text
e cmd.hit = p8 8
/ lib
```

Multiple commands:

```text
e cmd.hit = "s $$; pd 4; px 32"
/x 41414141
```

Scripted action:

```text
e cmd.hit = . hit-script.r2
/ command
```

Example `hit-script.r2`:

```text
?v $$ >> hit-offsets.txt
p8 16 @ $$ >> hit-bytes.txt
pd 6 @ $$ >> hit-disasm.txt
```

Use search hooks for:

- Recording context around suspicious strings.
- Dumping bytes around magic values.
- Collecting candidate format-string sites.
- Capturing disassembly around byte-pattern hits.
- Building an offset list for later `@@.offsets.txt` loops.

Keep hit actions bounded. A broad search plus expensive `cmd.hit` action can
create very large outputs or long runtimes.

## RTables and Comma Queries

The comma operator exposes RTables in the r2 shell. It is useful for querying,
sorting, filtering, and exporting table-like command output.

Show help:

```text
,?
```

Common forms:

```text
,                   show current table
,-                  reset current table
,j                  print current table as JSON
,,                  print current table as CSV
,. file.csv         load CSV
,h name addr size   define headers
,r foo 0x100 32     add row
```

Useful table output examples:

```text
afl,:json
is,:fancy
f,:json
```

Filtering and sorting examples:

```text
afl,size/sort/dec,any/head/20
afl,name/str/mem
afl,size/gt/0x100
afl,name/cols/name/size
```

Use RTables when:

- The command naturally produces rows.
- You need quick sorting or slicing.
- You need CSV, JSON, SQL, HTML, or table output.
- A one-liner is enough and a full r2pipe script would be overkill.

Prefer command-specific JSON when scripting complex analysis. Use RTables for
interactive triage and compact exports.

## Projects, Scripts, and Annotations

Projects save and restore session metadata. The book notes that projects are a
complex and historically sensitive feature, so use them carefully. For MaxTAC
evidence, prefer versioned scripts as the source of truth and use projects as
analyst convenience state.

Project basics:

```text
e dir.projects
Pl
P+case-name
P case-name
P.
P* > project-state.r2
Pze case-name.zrp
Pzi case-name.zrp
```

Project options:

```text
e prj.
e prj.files=false
e prj.history=false
e prj.vc=true
e prj.vc.type=git
```

Use project export when sharing a session:

```text
Pze case-name.zrp
```

Use project import when receiving one:

```text
Pzi case-name.zrp
```

Handmade projects are often better for repeatable research. Keep scripts in a
normal version-controlled directory:

```text
project/
  bins/
  scripts/
    setup.r2
    triage.r2
    notes.r2
  output/
```

Example launcher:

```text
r2 -q -i scripts/setup.r2 -i scripts/triage.r2 bins/sample.bin
```

Save and reload r2 command state:

```text
f* > scripts/flags.r2
CC* > scripts/comments.r2
afn* @@f > scripts/function-names.r2
. scripts/flags.r2
. scripts/comments.r2
```

Annotations store function-associated notes globally:

```text
ano=base64:<text>
anoe
anos
anol
ano*
ano-$$
ano-*
```

Use annotations for analyst reminders, not for canonical evidence. They are
stored globally by filename and function address, so record exported notes if
they matter to a report.

## Automation Patterns for Vulnerability Research

### Batch Binary Triage

Goal: inventory many samples consistently.

Commands:

```text
rabin2 -Ij sample.bin > sample.info.json
rabin2 -Sj sample.bin > sample.sections.json
rabin2 -ij sample.bin > sample.imports.json
rabin2 -zj sample.bin > sample.strings.json
r2 -q -c "aaa" -c "aflj" -c "q" sample.bin > sample.functions.json
```

Capture:

- Hashes.
- Header info.
- Hardening flags.
- Imports, strings, sections, and functions.
- Analysis depth and radare2 version.

Use this before expensive debugging or deep analysis.

### Dangerous Import Caller Report

Goal: find callers of risky imports such as copy, format, command execution, or
file/socket APIs.

R2 commands:

```text
aaa
axtj @ sym.imp.memcpy > memcpy-xrefs.json
axtj @ sym.imp.strcpy > strcpy-xrefs.json
axtj @ sym.imp.system > system-xrefs.json
```

R2pipe sketch:

```python
danger = ["memcpy", "memmove", "strcpy", "sprintf", "snprintf", "system"]
r2.cmd("aaa")
imports = r2.cmdj("iij") or []
for imp in imports:
    name = imp.get("name", "")
    if any(x in name for x in danger):
        xrefs = r2.cmdj(f"axtj @ {name}") or []
        print(name, xrefs)
```

For each caller, collect:

- Caller function.
- Argument setup near callsite.
- Input reachability.
- Bounds checks before the call.
- Runtime validation if needed.

### Patch-Diff Evidence Bundle

Goal: collect stable artifacts for vulnerable-versus-patched comparison.

Commands:

```text
rahash2 -a sha256 old.bin new.bin > hashes.txt
rabin2 -Ij old.bin > old.info.json
rabin2 -Ij new.bin > new.info.json
radiff2 -j -d old.bin new.bin > data-diff.json
radiff2 -AC old.bin new.bin > graph-summary.txt
radiff2 -z old.bin new.bin > string-diff.txt
```

Then use r2pipe for changed high-value functions:

```text
r2 -q -c "aaa" -c "pdfj @ sym.changed" -c "q" old.bin > old.changed.json
r2 -q -c "aaa" -c "pdfj @ sym.changed" -c "q" new.bin > new.changed.json
```

Record file order and architecture settings.

### Search Context Collection

Goal: search for suspicious values and capture surrounding evidence.

Script:

```text
e scr.color=false
e cmd.hit = "s $$; ?v $$ >> hits.txt; p8 32 @ $$ >> hit-bytes.txt; pd 8 @ $$ >> hit-disasm.txt"
/x 25732573
e cmd.hit =
q
```

Use for:

- Format strings.
- Magic headers.
- Command strings.
- Embedded keys or protocol markers.
- Known vulnerable constants.

### Function Graph Export

Goal: export function graph data for review or comparison.

Commands:

```text
r2 -Aq -c "agfj @ sym.parser" -c "q" sample.bin > parser.graph.json
r2 -Aq -c "agfd @ sym.parser" -c "q" sample.bin > parser.graph.dot
r2 -Aq -c "agfm @ sym.parser" -c "q" sample.bin > parser.graph.mmd
```

Use JSON for scripts, dot or Mermaid for review artifacts, and text disassembly
for report excerpts.

### Debugging Evidence Capture

Goal: automate repeatable crash evidence without hiding runtime mutation.

Use a rarun2 profile:

```text
program=./target
arg1=input.bin
stdin=input.bin
stdout=stdout.log
stderr=stderr.log
timeout=5
aslr=no
```

Capture state:

```text
r2 -r run.rr2 -d ./target
dc
dr > regs.txt
drr > regrefs.txt
dbt > backtrace.txt
pd 12 @ PC > fault-disasm.txt
dmj > maps.json
q
```

If automating with r2pipe, clearly record:

- Spawn profile.
- Breakpoints.
- Signal handling.
- Any register or memory writes.
- Whether ASLR was disabled.

### Project Handoff Pack

Goal: preserve analyst state without relying only on hidden local state.

Commands:

```text
P+case-name
P* > case-project.r2
f* > flags.r2
CC* > comments.r2
ano* > annotations.r2
Pze case-name.zrp
```

Also include:

- Input hashes.
- Scripts used to generate artifacts.
- JSON outputs.
- Notes explaining analysis depth and assumptions.

## Evidence Checklist

Collect:

- Target identifiers: path, hash, architecture, bits, format, version.
- Tool identifiers: `r2 -v`, utility versions, Python package versions when
  r2pipe is used.
- Automation entrypoint: command line, `.r2` script, `.r2.js` script, or r2pipe
  script path.
- Analysis depth: `aa`, `aaa`, `aaaa`, ESIL settings, debug settings, and
  architecture overrides.
- Configuration: `scr.color`, `scr.utf8`, `cfg.sandbox`, `io.va`, `bin.baddr`,
  `asm.arch`, `asm.bits`, `cfg.bigendian`, and any relevant `anal.*` settings.
- Output artifacts: raw JSON, text summaries, graphs, logs, hashes, generated
  scripts, and parsed reports.
- Runtime setup for debug automation: rarun2 profile, ASLR state, environment,
  working directory, input files, descriptors, and timeout.
- Mutations: writes, patches, register changes, memory changes, skipped signals,
  project saves, annotations, and generated output files.
- Parser assumptions: JSON schema assumptions, command output parsing, fallback
  behavior, and unsupported commands.
- Limitations: missing symbols, analysis failures, packed code, timeout, crash
  during analysis, nondeterminism, or version-specific behavior.

Keep the automation script and the generated artifacts together. A finding is
much easier to trust when rerunning one command can regenerate the evidence.

## Cautions

- Do not scrape text when a JSON command exists.
- Do not assume all `j` outputs are stable across radare2 versions.
- `-A` hides analysis-depth choices; explicit script commands are clearer.
- `aaaa` can be slow and may use emulation. Record why it was needed.
- `cmd.hit` can create huge outputs if the search is broad.
- `!`, `|`, and external shell calls can execute attacker-influenced data paths.
- `cfg.sandbox=true` helps restrict risky APIs, but test scripts before relying
  on it as a security boundary.
- Writable sessions, `wa`, `wx`, patch scripts, debug commands, and descriptor
  manipulation mutate state.
- Projects may save local state that is hard to review. Export scripts and JSON
  artifacts for evidence.
- Annotations are global and filename/address based. Export them if they matter.
- r2pipe HTTP/TCP endpoints should not be exposed to untrusted networks.
- Always close r2pipe sessions; leaked child processes make batch results messy.
- Treat parse errors, empty JSON, and command failures as findings about the
  automation run, not as absence of risk.

## Official References

- https://book.rada.re/scripting/intro.html
- https://book.rada.re/first_steps/syntax.html
- https://book.rada.re/scripting/loops.html
- https://book.rada.re/scripting/macros.html
- https://book.rada.re/scripting/r2pipe.html
- https://book.rada.re/scripting/r2pipe2.html
- https://book.rada.re/scripting/r2js.html
- https://book.rada.re/search/automation.html
- https://book.rada.re/commandline/comma.html
- https://book.rada.re/projects/usage.html
- https://book.rada.re/projects/annotations.html
- https://book.rada.re/projects/handmade.html
