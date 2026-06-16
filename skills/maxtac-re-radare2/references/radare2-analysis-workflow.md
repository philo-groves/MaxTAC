# Radare2 Analysis Workflow

Use this reference when turning binary metadata, strings, imports, or crash
offsets into functions, control-flow facts, xrefs, variable/type hypotheses, and
evidence. Radare2 analysis is powerful but approximate: run enough analysis to
answer the current question, then verify suspicious results with bytes,
disassembly, xrefs, types, and runtime evidence where possible.

## Contents

- [Quick Commands](#quick-commands)
- [Analysis Depth](#analysis-depth)
- [Function Analysis](#function-analysis)
- [Manual Function and Basic-Block Repair](#manual-function-and-basic-block-repair)
- [Xrefs and Reachability](#xrefs-and-reachability)
- [Opcode and Address Inspection](#opcode-and-address-inspection)
- [Variables and Arguments](#variables-and-arguments)
- [Types and Type Links](#types-and-type-links)
- [Calling Conventions and Signatures](#calling-conventions-and-signatures)
- [Virtual Tables and C++ RTTI](#virtual-tables-and-c-rtti)
- [Syscalls](#syscalls)
- [Graphs](#graphs)
- [Analysis Configuration](#analysis-configuration)
- [Vulnerability Research Use Cases](#vulnerability-research-use-cases)
- [Evidence Checklist](#evidence-checklist)
- [Official References](#official-references)

## Quick Commands

Start light:

```text
aa                  basic analysis: functions and basic blocks
afl                 list functions
aflj                list functions as JSON
pdf @ main          print function disassembly
afi @ main          function metadata
axt @ str.foo       xrefs to an address, flag, string, or import
axf @ sym.func      refs from an address or function
```

Increase depth only when needed:

```text
aaa                 deeper automatic analysis
aaaa                deeper analysis including more expensive passes
aab                 analyze basic blocks
aae                 ESIL-assisted analysis
aar                 analyze references
aav                 analyze values and local variables
```

Inspect and repair:

```text
af @ 0xADDR         analyze function at address
afr @ 0xADDR        recursively analyze function
af+ 0xADDR name     create a function manually
afb                 list basic blocks for current function
afn new_name        rename current function
afS 0xSIZE          set stack frame size
afC                 calculate cycles
afCc                calculate cyclomatic complexity
```

Use JSON when results will feed scripts or notes:

```text
aflj
afij @ sym.func
axj @ sym.func
agfj @ sym.func
afvj @ sym.func
```

## Analysis Depth

Radare2 exposes multiple auto-analysis passes. The `aa` command performs basic
analysis, while `aaa`, `aab`, `aaaa`, and other `a*` commands add deeper or more
specialized passes. The CLI shortcuts `r2 -A` and `r2 -AA` map to common
analysis depths.

Use a staged approach:

```bash
r2 -n "$BIN"                  # no analysis, fastest open
r2 -A "$BIN"                  # initial automatic analysis
r2 -AA "$BIN"                 # deeper automatic analysis
```

Inside a session:

```text
aa
afl
pdf @ entry0
aaa
afl~?
```

Guidance:

- Start with `aa` for triage. It is usually enough to list functions, inspect
  imports, and follow obvious string references.
- Use `aaa` or targeted `a*` commands when function boundaries, xrefs, or
  variables are missing.
- Use `aaaa` cautiously on large binaries, obfuscated code, firmware, or memory
  dumps; it can be slow and can create confident-looking wrong results.
- Re-run targeted analysis after changing architecture, bits, base address,
  prelude settings, types, calling conventions, or function boundaries.
- Treat auto-analysis output as a hypothesis. Confirm important claims with raw
  bytes, disassembly, xrefs, debugger traces, or independent tooling.

## Function Analysis

The `af` namespace controls function analysis.

Common function commands:

```text
af                  analyze function at current seek
afr                 recursively analyze function
af+ addr name       hand-create a function
af-                 delete current function analysis
afi                 show function information
afij                show function information as JSON
afl                 list functions
aflj                list functions as JSON
afll                list functions with more detail
afn name            rename current function
afna                suggest a function name
afs                 show or set function signature
afS size            set stack-frame size
afC                 calculate cycle count
afCc                calculate cyclomatic complexity
afB 16              mark current function as Thumb
```

Useful inspection commands:

```text
pdf @ sym.func      print disassembly for function
pdr @ sym.func      recursive disassembly view
agf @ sym.func      function basic-block graph
agfj @ sym.func     function graph JSON
```

Function triage fields to preserve:

- Address, size, name, and containing section.
- Number of basic blocks, edges, and cyclomatic complexity.
- Calls to sensitive imports or functions.
- Xrefs to the function and from the function.
- Strings, constants, and type/variable hints used in the function.
- Whether the function was auto-discovered or manually repaired.

Use `afl` and `aflj` to identify large, complex, imported-adjacent, exported,
or suspiciously named functions. Use `afi` before making manual edits so you can
record what radare2 believed before correction.

## Manual Function and Basic-Block Repair

Manual repair matters when auto-analysis misses code, splits one function into
many pieces, merges unrelated regions, misreads Thumb/ARM state, or stops at an
unusual jump.

Common repair commands:

```text
af+ 0xADDR name             create a function
afu 0xEND                  resize/analyze function until address
afm other_name             merge current function with another
af- @ 0xADDR               remove a bad function
afb                        list function basic blocks
afb+ fcn bb size [j] [f]   add a basic block with jump/fail edges
afb- addr                  remove a basic block
afB 16                     set current function to Thumb
```

Repair checklist:

- Confirm the bytes at the start address with `px` and `pd`.
- Check whether the address is code, data, thunk, jump table, or alignment.
- List existing blocks with `afb` before editing.
- Use branch targets and fallthrough targets as basic-block boundaries.
- Re-run local function analysis after manual edits.
- Re-check xrefs with `axt`, `axf`, and graph views.
- Record manual changes in notes or comments so later analysis does not treat
  repaired output as pure auto-analysis.

Use `anal.prelude` before analysis when functions use a recognizable prologue
that radare2 is missing:

```text
e anal.prelude=0x554889e5
aa
```

## Xrefs and Reachability

The `ax` namespace manages refs and xrefs. Use it to answer "who reaches this?"
and "what does this reach?"

Common commands:

```text
axt @ target        references to target
axf @ source        references from source
ax. @ addr          references to and from address
axff @ sym.func     references from function
axv @ sym.func      local variable read/write/exec references
axj @ addr          refs as JSON
axq @ addr          quiet refs
axg target          xref graph path to target
axtg                generate graph commands for xrefs to current seek
axt*                generate r2 commands for xrefs to current seek
```

Use xrefs for:

- String-to-code mapping: `axt @ str.error_message`.
- Import-to-call-site mapping: `axt @ sym.imp.strcpy`.
- Export reachability: `axt @ sym.exported_entry`.
- Dispatcher analysis: `axf @ sym.dispatch`.
- Data-flow landmarks: references to global pointers, tables, locks, vtables,
  config flags, and parser state.

Reachability notes:

- Xrefs are analysis results, not proof of runtime reachability.
- Missing xrefs can mean analysis did not discover code, indirect calls are not
  resolved, relocation metadata is absent, or the target is computed.
- Use `axg` or graph output to build a candidate path, then inspect each call
  edge and condition manually.
- For indirect calls, combine xrefs with types, vtables, jump tables, ESIL, or
  debugger traces.

## Opcode and Address Inspection

Use opcode and address analysis when a single instruction or address matters.

```text
ao                  analyze current opcode
aoj                 analyze current opcode as JSON
ao 8                analyze several opcodes
a8 <hexpairs>       analyze raw bytes
aO <len>            analyze N instructions in M bytes
ai @ addr           show address information: perms, stack, heap, etc.
ah?                 analysis hints
```

Useful follow-ups:

- Use `aoj` when extracting instruction type, size, jump/fail target, stack
  effects, ESIL, or pointer references for scripts.
- Use `ah` hints when the disassembler chose the wrong size, immediate,
  jump/fail target, bitness, or opcode interpretation.
- Use `ai` before declaring that an address is stack, heap, mapped file, code,
  or data.

When proving a vulnerability, preserve the bytes and decoded instruction around
important sinks, bounds checks, branches, and writes. The disassembly alone is
not enough if a later analyst cannot verify the raw bytes.

## Variables and Arguments

The `afv` namespace manages function variables and arguments. Auto variable
analysis is enabled by default but can be controlled with `anal.vars`.

Common commands:

```text
afv                 list variables and arguments
afv=                list variables and args with disassembly refs
afvj                variables as JSON
afva                analyze arguments and locals
afvn new old        rename a variable
afvt name type      change variable type
afvR name           list reads of variable
afvW name           list writes of variable
afvx                show variable xrefs
afvd name           debugger display command for a variable
afvr                register-based arguments
afvb                base-pointer/frame-pointer variables
afvs                stack-pointer variables
```

Use variables to:

- Track buffer sizes, length fields, indexes, loop counters, and allocation
  results.
- Distinguish source pointers from destination pointers in copy/parse code.
- Identify variables written before authentication or validation.
- Confirm whether a bounds check guards the same variable later used by a sink.
- Improve decompiler or pseudo-code readability if another tool consumes r2
  output.

Be careful:

- Variable recovery depends on function boundaries, calling conventions,
  prototypes, stack-frame size, and compiler optimizations.
- Register-based arguments can be misidentified in hand-written assembly,
  thunks, syscalls, callbacks, or unusual ABIs.
- Rename and retype only after checking disassembly and usage, not just names.

## Types and Type Links

Radare2 stores C-like types in SDB. Use types to make structures, function
prototypes, globals, and variable roles explicit.

Common type commands:

```text
t                   list loaded types
tj                  list types as JSON
ts                  list structs
tu                  list unions
te                  list enums
tf                  list function signatures
td "struct foo { int len; char *buf; }"
to header.h         load C types from a header
to -                edit/load types in cfg.editor
tp foo @ addr       temporarily print data as type
tpx foo <hexpairs>  print bytes as type
tl Type = addr      link type to address
tll                 list linked types
tx                  type xrefs
```

Use type links for:

- Parser state structs, request objects, IPC messages, ioctl buffers, file
  headers, serialized records, vtables, and callback tables.
- Clarifying whether a length field, tag, pointer, or flags field is read before
  use.
- Making global objects and arrays easier to inspect across sessions.

Practical sequence:

```text
"td struct msg { uint32_t len; uint32_t type; char *data; }"
tp msg @ hit0_0
tl msg = hit0_0
```

Type caveats:

- Imported headers may require include-path configuration via `dir.types`.
- C integer widths depend on target platform assumptions; verify `asm.bits`,
  `asm.arch`, and ABI settings.
- Type links explain data layout; they do not prove attacker control or runtime
  reachability.

## Calling Conventions and Signatures

Calling conventions guide argument recovery, return types, type propagation, and
function prototypes.

Commands:

```text
afc                 show current function calling convention
afc <cc>            set current function calling convention
afc=                show or select default calling convention
afcl                list calling conventions for current architecture
afca                analyze current calling convention
afcr                show register usage for current function
afcf printf         print known function prototype
afs                 show or set function signature
aft                 type matching and propagation
```

Use these when:

- A function's arguments are wrong or missing.
- The binary uses non-default ABI boundaries, callbacks, syscalls, firmware
  conventions, Objective-C/Swift/C++ thunks, or Windows vs SysV x64 mismatch.
- You need a cleaner function signature for a report, script, or decompiler.

Check before changing:

- `asm.arch`, `asm.bits`, `asm.os`, and binary format metadata.
- Whether the function is a real function, thunk, tail-call stub, import stub,
  interrupt/syscall wrapper, or hand-written assembly.
- Whether the prototype is inferred, from symbols/debug info, or manually set.

## Virtual Tables and C++ RTTI

Use `av` commands for basic vtable and RTTI inspection. Before vtable analysis,
check `anal.cpp.abi` and set it for the target ABI if needed.

Commands:

```text
e anal.cpp.abi
e anal.cpp.abi=itanium
av                  search/list vtables in data sections
avj                 vtables as JSON
av*                 vtables as r2 commands
avr @ addr          parse RTTI at a vtable address
avra                search vtables and parse RTTI
```

Use vtable analysis for:

- C++ virtual dispatch and plugin surfaces.
- UAF and type-confusion hypotheses.
- Mapping object methods to call sites.
- Identifying class-like structures in stripped binaries.

Be careful with stripped, optimized, or nonstandard C++ binaries. Vtable output
is a lead; confirm with section permissions, constructor/destructor xrefs,
indirect call sites, and object layout.

## Syscalls

Syscall analysis depends on platform settings such as `asm.os`, `asm.bits`, and
`asm.arch`.

Commands:

```text
e asm.os
e asm.bits
e asm.arch
asl                 list supported syscalls for current platform
/ad/ syscall        search syscall-like instructions on x86
/ad/ svc            search syscall-like instructions on ARM
aei                 initialize ESIL VM
/as                 search/list syscalls
e asm.emu=true      show emulated syscall arguments in disassembly
dcs                 debug: continue to next syscall
dcs*                debug: trace syscalls
```

Use syscall analysis for:

- Broker, sandbox, seccomp, syscall-filter, or firmware API boundaries.
- Direct syscalls that bypass library wrappers or hooks.
- Ioctl, file, process, memory, and network operations in stripped binaries.
- Comparing static syscall intent with dynamic traces.

Restrict expensive syscall searches to executable ranges when possible:

```text
/as @e:search.in=io.maps.x
```

If `aae` or `aaaa` finds syscalls, radare2 may add them to a `syscall.*`
flagspace. Use that flagspace for navigation and evidence.

## Graphs

The `ag` namespace renders analysis graphs.

Common graph commands:

```text
agf                 current function basic-block graph
agfj                function graph as JSON
agfm                function graph as Mermaid
agc                 function call graph
agC                 global call graph
aga                 data references graph
agA                 global data references graph
agr                 references graph
agx                 cross-references graph
agi                 imports graph
```

Useful output formats:

```text
agf                 ASCII graph
agfv                interactive ASCII graph
agfj                JSON
agfd                Graphviz dot
agfm                Mermaid
agf*                r2 commands
agfw                render with external graph tools/viewer
```

Use graphs to:

- Identify complex parser branches, loops, dispatchers, and error exits.
- Compare checked and unchecked flows to the same sink.
- Show reachability between exported/API-facing functions and risky internals.
- Summarize a function or call chain in research notes.

For custom evidence graphs:

```text
agn source "attacker-controlled input"
agn sink "memcpy without length clamp"
age source sink
aggm
```

Avoid rendering huge graphs directly in the terminal. Prefer JSON, Mermaid, dot,
or an interactive graph for large binaries.

## Analysis Configuration

Radare2 exposes analysis controls in `anal.*`, `emu.*`, and related namespaces.
Check and set options before analysis when the target needs special handling.

Useful checks:

```text
e asm.arch
e asm.bits
e asm.os
e bin.baddr
e anal.vars
e anal.prelude
e??anal
e??emu
```

Common reasons to change configuration:

- Architecture, bitness, OS, or endian assumptions are wrong.
- Firmware or raw blobs need a base address or manual map assumptions.
- Function preludes are nonstandard.
- Jump tables are missed.
- Analysis stops too early after unconditional jumps or unusual control flow.
- Variable analysis is noisy or wrong.
- ESIL-assisted analysis should be enabled or avoided for a specific region.

Configuration discipline:

- Set configuration before broad analysis whenever possible.
- Record non-default settings in notes and evidence.
- Re-run targeted analysis after changing important settings.
- Prefer targeted settings and re-analysis over repeatedly running `aaaa` and
  hoping the result improves.

## Vulnerability Research Use Cases

Map a dangerous import to callers:

```text
aa
axt @ sym.imp.memcpy
pdf @ <caller>
afv= @ <caller>
```

Map an error string or protocol marker to code:

```text
/i "invalid length"
axt @ hit0_0
pdf @ <xref-function>
```

Check whether a bounds check guards a sink:

```text
pdf @ sym.parse_message
afv= @ sym.parse_message
axt @ <length-field-or-string>
agf @ sym.parse_message
```

Repair a missed function before drawing conclusions:

```text
pd 20 @ 0xADDR
af+ 0xADDR suspected_parser
afb
afva
axt @ suspected_parser
```

Investigate indirect dispatch:

```text
/A call
/ad/ jmp qword
av
axt @ <vtable-or-table>
axf @ <dispatcher>
```

Identify privileged or sandbox-sensitive operations:

```text
e asm.os=<target-os>
asl
/as @e:search.in=bin.sections.x
fs syscalls
f~syscall
```

Generate graph evidence:

```text
agfj @ sym.parser
agfm @ sym.parser
axg sym.imp.memcpy
```

## Evidence Checklist

Capture:

- Binary path, hash, architecture, bitness, OS, base address, and analysis
  settings.
- Auto-analysis depth used (`aa`, `aaa`, `aaaa`, targeted commands, `r2 -A`,
  `r2 -AA`).
- Function addresses, names, sizes, basic-block counts, complexity, and whether
  functions were auto-discovered or manually repaired.
- Xrefs from attacker-facing inputs to sensitive functions, imports, globals, or
  strings.
- Variable/type/calling-convention changes made manually.
- Graph output for important functions or chains, preferably JSON, Mermaid, or
  dot when the output is large.
- Raw bytes and disassembly around key checks, branches, indirect calls, writes,
  and sinks.
- Notes separating confirmed facts from auto-analysis hypotheses.

## Official References

- https://book.rada.re/analysis/intro.html
- https://book.rada.re/analysis/code_analysis.html
- https://book.rada.re/analysis/variables.html
- https://book.rada.re/analysis/types.html
- https://book.rada.re/analysis/calling_conventions.html
- https://book.rada.re/analysis/vtables.html
- https://book.rada.re/analysis/syscalls.html
- https://book.rada.re/signatures/zignatures.html
- https://book.rada.re/analysis/graphs.html
