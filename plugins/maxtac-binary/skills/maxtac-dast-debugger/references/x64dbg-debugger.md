# x64dbg Debugger

Use x64dbg for user-mode Windows binary debugging, especially GUI-driven
runtime inspection of PE EXE and DLL targets without requiring source code.
Prefer the installed build's help, menus, and command autocomplete for exact
behavior because x64dbg changes frequently and plugins can extend commands,
formatters, and expression functions.

Treat x64dbg as mutable execution. It can change target state through
register writes, memory writes, assembled instructions, breakpoint commands,
thread control, privilege changes, command-line changes, scripts, plugins, and
exception handling choices. Keep final evidence separate from observations that
only happen because the debugger changed timing, state, breakpoints, page
guards, or first-chance exception policy.

## Contents

- [Quick Commands](#quick-commands)
- [Command Model](#command-model)
- [Toolchain and Session Setup](#toolchain-and-session-setup)
- [Launch and Attach](#launch-and-attach)
- [GUI Workflow](#gui-workflow)
- [Debug Control](#debug-control)
- [Breakpoints](#breakpoints)
- [Conditional Breakpoints](#conditional-breakpoints)
- [Exceptions and Events](#exceptions-and-events)
- [Threads and Process State](#threads-and-process-state)
- [Memory, Dumps, and Patches](#memory-dumps-and-patches)
- [Expressions, Values, and Variables](#expressions-values-and-variables)
- [Searching and References](#searching-and-references)
- [Symbols, Modules, and Analysis](#symbols-modules-and-analysis)
- [Tracing](#tracing)
- [Automation and Scripting](#automation-and-scripting)
- [Evidence Automation](#evidence-automation)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Start from Windows command line:

```text
x64dbg.exe C:\work\target.exe
x64dbg.exe -p 1234
x64dbg.exe C:\work\target.exe "--input C:\work\case.bin"
x64dbg.exe C:\work\target.exe "--input C:\work\case.bin" C:\work
```

Use the matching front end for the target bitness when the package provides
both front ends:

```text
x32dbg.exe C:\work\target32.exe
x64dbg.exe C:\work\target64.exe
```

Inside the command bar:

```text
init "C:\work\target.exe", "--input C:\work\case.bin", "C:\work"
attach 1234
detach
stop
run
pause
sti
sto
rtr
skip
con
```

Common inspection commands:

```text
disasm cip
dump csp
sdump csp
memmapdump cip
imageinfo
exinfo
exhandlers
bplist
getcommandline
```

Breakpoint triage:

```text
bp module:entry, "entry"
bp kernel32:CreateFileW, "CreateFileW"
bph cip, x, 1
bpm csp, 0, w
SetExceptionBPX C0000005, first
bplist
```

Capture artifacts:

```text
log "cip={p:cip} instr={i:cip}"
minidump "C:\evidence\target-live.dmp"
savedata "C:\evidence\stack.bin", csp, 1000
scriptload "C:\evidence\triage.x64dbg"
scriptrun
```

## Command Model

x64dbg exposes a command bar and script language. Commands use comma-separated
arguments:

```text
command arg1, arg2, argN
```

Important parser rules:

- Use commas, not spaces, to separate two or more command arguments.
- Integer constants are interpreted as hexadecimal by default.
- Prefix decimal numbers with `.`, such as `.123`.
- In documentation, `[arg]` means an optional command argument, not an x64dbg
  memory dereference.
- In expressions, `[addr]` dereferences target memory.
- `==` tests equality; `=` assigns a value.
- x64dbg expressions are integer-oriented. Strings, floating point, and
  SSE/AVX values need appropriate formatter, register, or plugin support.
- Quote log format strings that contain `;` because `;` separates commands.
- Prefer architecture-neutral registers for scripts that should work in both
  front ends: `cip`, `csp`, `cbp`, `cax`, `cbx`, `ccx`, `cdx`, `csi`, and
  `cdi`.

Use full command names in automation when they clarify intent. Short aliases
such as `bp`, `bpc`, `bph`, `bpm`, `sti`, `sto`, `rtr`, `rtu`, `ticnd`, and
`tocnd` are normal in interactive use, but full names are easier to audit.

## Toolchain and Session Setup

Record the debugger build and target context:

```text
Help -> About
Help -> Calculator
View -> Log
View -> Memory Map
View -> Modules
View -> Threads
View -> Call Stack
View -> Breakpoints
View -> Trace
```

Start a clean evidence directory outside the target tree:

```text
mkdir C:\evidence\target-YYYYMMDD-HHMMSS
```

Record:

- x64dbg or x32dbg executable path.
- x64dbg build date or version string shown in the GUI.
- Windows version and target architecture.
- Target path, file hash, command line, working directory, and input files.
- Loaded plugins and any custom scripts used.
- Whether the session launched, attached to, or reopened a dump from the
  target.

Prefer a stable run configuration:

- Set the command line explicitly before running when arguments matter.
- Use a fixed working directory.
- Keep external files in a reproducible location.
- Save scripts, log files, minidumps, and target inputs together.
- Avoid relying on user database state unless the `.dd32` or `.dd64` database
  is part of the evidence.

## Launch and Attach

Start from Windows:

```text
x64dbg.exe C:\work\target.exe
x64dbg.exe C:\work\target.exe "--input C:\work\case.bin"
x64dbg.exe C:\work\target.exe "--input C:\work\case.bin" C:\work
```

Attach from Windows:

```text
x64dbg.exe -p 1234
```

Start from inside x64dbg:

```text
init "C:\work\target.exe"
init "C:\work\target.exe", "--input C:\work\case.bin"
init "C:\work\target.exe", "--input C:\work\case.bin", "C:\work"
```

Attach from inside x64dbg:

```text
attach 1234
detach
```

Change the target command line:

```text
getcommandline
setcommandline "\"C:\work\target.exe\" --input C:\work\case.bin"
```

The `init` command loads the executable, performs basic checks, sets initial
breakpoints, and returns control after the system breakpoint. It also sets
`$pid` and `$hp`/`$hProcess`. The `attach` command returns after the system
breakpoint and sets the same process variables.

Record whether evidence came from launch or attach. The two paths can differ
because environment, command line, parent process, current directory, handles,
loaded modules, privileges, and timing can differ.

## GUI Workflow

Use the GUI as the primary state surface:

- CPU view: disassembly, registers, dump, stack, and command bar.
- Log view: command output, breakpoint logs, script logs, and diagnostic text.
- Breakpoints view: software, hardware, memory, DLL, and exception breakpoints.
- Memory Map view: regions, permissions, and module-backed mappings.
- Call Stack view: current stack frames.
- Threads view: thread list, IDs, and selected thread context.
- Trace view: trace recording and coverage data.
- Symbols and Modules views: loaded modules and symbol state.
- Notes view: investigator notes local to the workspace.

Useful GUI navigation commands:

```text
disasm cip
dump csp
sdump csp
memmapdump cip
graph cip
guiupdatedisable
guiupdateenable
```

Use `guiupdatedisable` during noisy automation only when the GUI refresh cost is
the problem. Re-enable it before handing the session back to a human.

## Debug Control

Run and pause:

```text
run
run module:entry
pause
stop
```

Step:

```text
sti
sti .10
sto
sto .10
rtr
skip
```

Continue exception handling:

```text
con
con 1
```

`run` frees the debugger lock and lets the target run. With an argument, it
sets a single-shot breakpoint at the specified location before running.

`con` controls debugger continue status after an exception. With an argument,
the exception is handled by the target program. Without an argument, x64dbg
swallows the exception. Record which path was used because it changes target
control flow.

`sti` single-steps with the trap flag. `sto` steps over. `rtr` steps out.
`skip` advances without executing the selected instruction and is therefore a
state-changing command.

## Breakpoints

x64dbg documents five breakpoint classes:

- Software breakpoints.
- Hardware breakpoints.
- Memory breakpoints.
- DLL breakpoints.
- Exception breakpoints.

Software breakpoints:

```text
bp module:entry
bp 401000, "entry"
bp kernel32:CreateFileW, "CreateFileW"
bpc 401000
bpe 401000
bpd 401000
```

Hardware breakpoints:

```text
bph cip, x, 1
bph csp, w, 8
bph rax, r, 4
bphc cip
bphe cip
bphd cip
```

Hardware breakpoint type is `r` for read/write, `w` for write, or `x` for
execute. Size can be `1`, `2`, `4`, or `8` on x64. The address must align to
the selected size.

Memory breakpoints:

```text
bpm csp
bpm csp, 0, w
bpm rax, 1, r
bpmc csp
bpme csp
bpmd csp
```

Memory breakpoints are guard-page breakpoints on the whole memory region
containing the supplied address. x64dbg's own documentation calls out that
fine-grained memory breakpoints are not supported the same way as in some other
debuggers.

Exception breakpoints:

```text
SetExceptionBPX C0000005, first
SetExceptionBPX C0000005, second
SetExceptionBPX C0000005, all
DeleteExceptionBPX C0000005
EnableExceptionBPX C0000005
DisableExceptionBPX C0000005
```

List breakpoints:

```text
bplist
```

`bplist` emits entries in this shape:

```text
STATE:TYPE:ADDRESS[:NAME]
```

Breakpoint type values include `BP`, `SS`, `HW`, and `GP`.

## Conditional Breakpoints

Set conditions, logging, commands, hit counts, and silent behavior:

```text
bpcnd 401000, "cax==1 && ccx==1"
bpcnd 401000, "arg.get(0)==1"
bpcnd 401000, "mem.valid(cax)"
bpcnd 401000, "$breakpointcounter==3"
bplog 401000, "hit cip={p:cip} instr={i:cip}"
SetBreakpointCommand 401000, "mov last_hit, cip"
SetBreakpointFastResume 401000, 1
SetBreakpointSilent 401000, 1
GetBreakpointHitCount 401000
ResetBreakpointHitCount 401000
```

The conditional-breakpoint pipeline:

- Sets `$breakpointexceptionaddress`.
- Increments the hit counter.
- Sets `$breakpointcounter`.
- Evaluates the break condition, defaulting to `1`.
- If fast resume is enabled and the break condition evaluates to `0`, resumes
  without GUI updates, plugin callbacks, logging, or commands.
- Evaluates log and command conditions.
- Emits log text when configured and allowed.
- Executes command text when configured and allowed.
- Breaks only when the final break condition evaluates to a nonzero value.

If an expression is invalid, x64dbg treats the condition as triggered. Validate
conditions with the calculator or command bar before using them in evidence.

Avoid commands that change target running state inside breakpoint commands.
x64dbg documents these as unstable in this context. Use break conditions,
command conditions, or `$breakpointcondition` to control whether execution
pauses.

## Exceptions and Events

Capture a specific exception:

```text
SetExceptionBPX C0000005, first
SetExceptionBPX C0000005, second
SetExceptionBPX C0000005, all
```

Inspect the last exception:

```text
exinfo
```

Print registered exception handlers:

```text
exhandlers
```

Use the Settings dialog to record event policy:

```text
Options -> Preferences -> Events
Options -> Preferences -> Exceptions
```

Settings include system breakpoint, TLS callbacks, entry breakpoint, DLL
events, attach breakpoint, thread events, and debug strings. Exception settings
can add or delete exception ranges. Record these settings when reproducing a
crash because they change what stops the target and what continues.

Expression functions for exception state:

```text
ex.firstchance()
ex.addr()
ex.code()
ex.flags()
ex.infocount()
ex.info(0)
```

## Threads and Process State

Switch, suspend, and resume threads:

```text
switchthread
switchthread 1A4
suspendthread 1A4
resumethread 1A4
suspendallthreads
resumeallthreads
```

`switchthread` changes x64dbg's internal current thread and therefore the
displayed registers and call stack. Without an argument, it switches to the
main thread.

Use the Threads view for thread IDs:

```text
View -> Threads
```

Use thread suspension sparingly. It can hide timing-sensitive behavior or
create observations that never occur in a normal run.

Operating-system control commands can change process privileges or handles:

```text
GetPrivilegeState SeDebugPrivilege
EnablePrivilege SeDebugPrivilege
DisablePrivilege SeDebugPrivilege
handleclose <handle>
```

Record privilege and handle manipulation as debugger intervention.

## Memory, Dumps, and Patches

Navigate memory:

```text
dump csp
dump cax
sdump csp
memmapdump cip
getpagerights csp
```

Save memory and dumps:

```text
savedata "C:\evidence\region.bin", cax, 1000
savedata ":memdump:", csp, 1000
minidump "C:\evidence\target-live.dmp"
```

`savedata` writes a memory region to disk. `:memdump:` creates a file named
with process ID, address, and size in the x64dbg directory. `minidump` creates
a `.dmp` with full memory and handle information from the debuggee.

State-changing memory commands:

```text
mov cax, 1234
mov csp, csp-20
mov [csp], #11 22 33#
asm cip, "nop"
asm cip, "xor eax,eax", 1
setpagerights csp, ReadWrite
alloc 1000
free $lastalloc
```

`mov` can create variables, change registers, and write bytes to process
memory when the value is written as `#11 22 33#`. `asm` writes assembled
instructions at the selected address and sets `$result` to the instruction
size or `0` on failure. Treat these commands as evidence contamination unless
the experiment is explicitly about target mutation.

## Expressions, Values, and Variables

Evaluate expressions in the command bar or calculator:

```text
cax
[csp]
byte:[csp]
qword:[csp]
module:entry
module:$1000
module:#400
```

Number rules:

```text
100       ; hex 0x100
.100      ; decimal 100
0x100     ; explicit hex
```

Common values:

- Registers: `rax`, `eax`, `rip`, `eip`, `cip`, `csp`, and other general
  registers.
- Flags: `_zf`, `_cf`, `_sf`, `_of`, and other documented flag names.
- Memory: `[addr]`, `byte:[addr]`, `word:[addr]`, `dword:[addr]`,
  `qword:[addr]`.
- Module exports: `kernel32:CreateFileW`, `module.dll:api`, or
  `module:ordinal`.
- Module data: `module`, `module:base`, `module:imagebase`, `module:entry`,
  `module:oep`, `module:$rva`, and `module:#file_offset`.

Create variables:

```text
mov myvar, 1234
mov $myvar, 1234
myvar = 1234
$myvar = 1234
myvar += 10
myvar++
varlist
vardel myvar
```

Reserved variables include:

- `$res`/`$result`.
- `$pid`.
- `$hp`/`$hProcess`.
- `$lastalloc`.
- `$breakpointcondition`.
- `$breakpointcounter`.
- `$breakpointlogcondition`.

Useful expression functions:

```text
mem.valid(cax)
ReadByte(cax)
ReadPtr(csp)
arg.get(0)
arg.set(0, 1)
dis.len(cip)
dis.mnemonic(cip)
dis.text(cip)
dis.iscall(cip)
dis.isret(cip)
dis.isbranch(cip)
tr.isrecording()
tr.hitcount(cip)
```

String formatting:

```text
log "cip={p:cip} instr={i:cip}"
log "stack={mem;40@csp}"
log "ascii={ascii@cax}"
log "utf16={utf16@cax}"
log "status={ntstatus@cax}"
```

Use `{p:expr}` for pointer formatting, `{i:expr}` for instruction text,
`{mem;size@addr}` for bytes, `{ascii@addr}` and `{utf16@addr}` for strings,
and `{a:addr}` for address information.

## Searching and References

Search commands:

```text
find cip, 488B
findall cip, 488B
findallmem cip, 488B
findasm "call", cip
refstr
reffind kernel32:CreateFileW
setmaxfindresult .5000
```

Use the References view for search output. For string work, the GUI offers
string reference searches and constant searches. The official tips call out
that UTF-16LE is the code page that matches Windows Unicode encoding.

Treat searches as navigation and evidence indexing, not proof by themselves.
Save the search command, range, result count, and relevant target bytes when a
result matters.

## Symbols, Modules, and Analysis

Module and image commands:

```text
imageinfo
imageinfo module
symdownload
symdownload module
symdownload module, "https://msdl.microsoft.com/download/symbols"
symload module, "C:\symbols\module.pdb"
symload module, "C:\symbols\module.pdb", 1
symunload module
```

Analysis commands:

```text
analyse
analxrefs
analrecur
analadv
```

User database annotations:

```text
dbsave
dbload
commentset cip, "repro stop"
labelset cip, "repro_stop"
bookmarkset cip
commentlist
labellist
bookmarklist
```

x64dbg keeps comments, labels, bookmarks, and related annotations in a user
database. Include the database file when annotations are part of the evidence,
or keep the final report independent of those local names.

## Tracing

Conditional trace into:

```text
ticnd "cax==1", .1000
```

Conditional trace over:

```text
tocnd "cax==1", .1000
```

Run to user code:

```text
rtu
```

Trace logging:

```text
TraceSetLog "{p:cip} {i:cip}", "1"
TraceSetLogFile "C:\evidence\trace.log"
ticnd "$tracecounter==.1000", .1000
```

Trace recording:

```text
opentrace "C:\evidence\run.trace64"
ticnd "$tracecounter==.1000", .1000
tc
```

`opentrace` opens a trace file for recording, but a trace command must actually
run to record instructions. The default `.trace32` or `.trace64` extension is
not appended automatically.

Conditional tracing increments `$tracecounter`, evaluates the break condition,
evaluates log and command conditions, optionally logs formatted text, and breaks
when the break condition evaluates to `1`.

Use `Trace Into` when logs, trace records, or break conditions inside calls
matter. x64dbg documents that `Trace Over` does not pause inside stepped-over
calls even if the condition becomes true there.

## Automation and Scripting

Load and run a script:

```text
scriptload "C:\evidence\triage.x64dbg"
scriptrun
```

Load and execute in one operation:

```text
scriptexec "C:\evidence\triage.x64dbg"
```

Script logging:

```text
log "cip={p:cip} instr={i:cip}"
printstack
```

Example `triage.x64dbg`:

```text
log "=== target ==="
getcommandline
imageinfo
exhandlers
bplist
log "=== state ==="
log "pid={$pid} cip={p:cip} csp={p:csp}"
log "instr={i:cip}"
log "stack={mem;80@csp}"
minidump "C:\evidence\target-live.dmp"
savedata "C:\evidence\stack.bin", csp, 1000
ret
```

Script execution is single-threaded. `scriptrun` runs the loaded script from
the current script instruction pointer and blocks until completion, a stop
line, an error, or manual abort. `scriptexec` loads and runs from the beginning,
then unloads only if execution completes successfully. It cannot be called from
inside a running script.

`scriptcmd` executes a command in the context of a running script and blocks
until that command completes. It is useful for invoking script labels from
breakpoint commands:

```text
bp module:$1000
SetBreakpointCommand module:$1000, "scriptcmd call on_hit"

on_hit:
log "hit cip={p:cip} arg0={arg.get(0)}"
ret
```

Keep scripts short and record them with evidence. Avoid hiding critical
observations inside GUI-only state or unsaved plugin output.

## Evidence Automation

Create an evidence folder:

```text
mkdir C:\evidence\target-YYYYMMDD-HHMMSS
```

Create `C:\evidence\target-YYYYMMDD-HHMMSS\triage.x64dbg`:

```text
log "=== session ==="
getcommandline
log "pid={$pid} hProcess={$hp}"
log "=== breakpoints ==="
bplist
log "=== exception ==="
exinfo
exhandlers
log "=== image ==="
imageinfo
log "=== state ==="
log "cip={p:cip} instr={i:cip}"
log "csp={p:csp} stack={mem;100@csp}"
savedata "C:\evidence\target-YYYYMMDD-HHMMSS\stack.bin", csp, 1000
minidump "C:\evidence\target-YYYYMMDD-HHMMSS\target-live.dmp"
dbsave
ret
```

Run it from the command bar after the target stops:

```text
scriptload "C:\evidence\target-YYYYMMDD-HHMMSS\triage.x64dbg"
scriptrun
```

For a conditional logging breakpoint:

```text
bp module:$1234, "observed"
bpcnd module:$1234, "mem.valid(csp)"
bplog module:$1234, "hit={p:cip} instr={i:cip} stack={mem;40@csp}"
SetBreakpointSilent module:$1234, 1
```

For bounded trace logging:

```text
TraceSetLog "{p:cip} {i:cip}", "1"
TraceSetLogFile "C:\evidence\target-YYYYMMDD-HHMMSS\trace.log"
opentrace "C:\evidence\target-YYYYMMDD-HHMMSS\run.trace64"
ticnd "$tracecounter==.1000", .1000
tc
```

Keep the script, logs, minidump, saved memory, user database, input files,
target hashes, and debugger version together.

## Failure Modes

Wrong debugger front end

- Reopen the target in the matching x32dbg or x64dbg front end.
- Record target bitness and debugger bitness.

Arguments not applied

- Check `getcommandline`.
- Use the documented command-line shape or `setcommandline`.
- Record the working directory supplied to `init` or the Windows command line.

Breakpoint does not bind

- Confirm module load in the Modules view.
- Use `bplist` to inspect enabled state, type, address, and name.
- Confirm symbol state if using symbol names.
- Use module-relative expressions for ASLR-resilient addresses.

Memory breakpoint fires too broadly

- Remember that x64dbg memory breakpoints are guard-page breakpoints over the
  whole region containing the supplied address.
- Use conditional expressions to narrow the stop condition.

Condition always triggers

- Validate expression syntax in the calculator or command bar.
- Remember that invalid conditional-breakpoint expressions are treated as
  triggered.
- Remember numbers are hexadecimal unless prefixed with `.` for decimal.

Trace misses state inside calls

- Use Trace Into instead of Trace Over when state inside called functions
  matters.
- Record maximum step counts to avoid unbounded traces.

Script did not unload

- `scriptexec` leaves the script loaded when execution fails or is aborted.
- Use the Script tab to inspect and abort running scripts.
- Only one script runs at a time.

Log output is ambiguous

- Quote log format strings that contain `;`.
- Include the script and command text with the evidence.
- Include minidumps or saved memory for values that matter.

Debugger changed the observation

- Identify state-changing commands such as `mov`, `asm`, `skip`,
  `setpagerights`, `EnablePrivilege`, `handleclose`, `con`, and thread
  suspension.
- Reproduce without those commands when final evidence must reflect normal
  execution.

## Evidence Checklist

- x64dbg or x32dbg executable path and version/build information.
- Windows version and target architecture.
- Target path, file hash, command line, working directory, and input files.
- Launch or attach path, including PID for attach.
- Breakpoint list from `bplist`.
- Event and exception settings when they affect stopping behavior.
- Last exception details from `exinfo` when applicable.
- Minidump from `minidump` when available.
- Saved memory regions from `savedata` when relevant.
- Trace logs and trace recordings when tracing was used.
- Scripts, plugin list, and user database files used during the session.
- Notes about all state-changing debugger commands.

## References

- https://help.x64dbg.com/en/latest/
- https://help.x64dbg.com/en/latest/introduction/Commandline.html
- https://help.x64dbg.com/en/latest/commands/
- https://help.x64dbg.com/en/latest/commands/debug-control/index.html
- https://help.x64dbg.com/en/latest/commands/debug-control/InitDebug.html
- https://help.x64dbg.com/en/latest/commands/debug-control/AttachDebugger.html
- https://help.x64dbg.com/en/latest/commands/breakpoint-control/index.html
- https://help.x64dbg.com/en/latest/introduction/ConditionalBreakpoint.html
- https://help.x64dbg.com/en/latest/commands/conditional-breakpoint-control/index.html
- https://help.x64dbg.com/en/latest/introduction/ConditionalTracing.html
- https://help.x64dbg.com/en/latest/commands/tracing/index.html
- https://help.x64dbg.com/en/latest/introduction/Values.html
- https://help.x64dbg.com/en/latest/introduction/Expressions.html
- https://help.x64dbg.com/en/latest/introduction/Expression-functions.html
- https://help.x64dbg.com/en/latest/introduction/Formatting.html
- https://help.x64dbg.com/en/latest/introduction/Variables.html
- https://help.x64dbg.com/en/latest/commands/memory-operations/index.html
- https://help.x64dbg.com/en/latest/commands/memory-operations/getpagerights.html
- https://help.x64dbg.com/en/latest/commands/memory-operations/setpagerights.html
- https://help.x64dbg.com/en/latest/commands/memory-operations/savedata.html
- https://help.x64dbg.com/en/latest/commands/memory-operations/minidump.html
- https://help.x64dbg.com/en/latest/commands/searching/index.html
- https://help.x64dbg.com/en/latest/commands/searching/find.html
- https://help.x64dbg.com/en/latest/commands/searching/findasm.html
- https://help.x64dbg.com/en/latest/commands/script/
- https://help.x64dbg.com/en/latest/gui/views/index.html
- https://help.x64dbg.com/en/latest/gui/settings/index.html
- https://help.x64dbg.com/en/latest/introduction/Glossary.html
- https://help.x64dbg.com/en/latest/introduction/Inability.html
- https://x64dbg.com/
