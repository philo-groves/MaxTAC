# WinDbg Debugger

Use WinDbg for Windows runtime debugging, especially kernel-mode debugging,
driver analysis, crash dump triage, Microsoft symbol workflows, and cases that
need debugger extensions, the debugger data model, or Time Travel Debugging
(`TTD`). Prefer x64dbg for interactive user-mode reversing when WinDbg-specific
kernel, dump, symbol, or extension behavior is not needed.

Prefer Microsoft Learn and the installed debugger help for exact command
behavior. WinDbg, WinDbg Classic, KD, CDB, SDK builds, Store builds, target
Windows versions, processor architectures, and extensions can differ.

Treat WinDbg as mutable execution. It can change target state through register
writes, memory writes, breakpoint commands, exception handling, process and
thread control, extension commands, dump creation, TTD recording, and kernel
debug settings. Keep final evidence separate from observations that only happen
because the debugger changed timing, context, process state, or OS state.

## Contents

- [Quick Commands](#quick-commands)
- [Command Model](#command-model)
- [Toolchain and Session Setup](#toolchain-and-session-setup)
- [Launch, Attach, Dumps, and Kernel Sessions](#launch-attach-dumps-and-kernel-sessions)
- [Symbols, Source, Images, and Extensions](#symbols-source-images-and-extensions)
- [Breakpoints and Watchpoints](#breakpoints-and-watchpoints)
- [Exceptions, Events, and Crash Context](#exceptions-events-and-crash-context)
- [Process, Thread, and Kernel Context](#process-thread-and-kernel-context)
- [Stack, Registers, and Instruction State](#stack-registers-and-instruction-state)
- [Memory and Address Space](#memory-and-address-space)
- [Dump Creation](#dump-creation)
- [Remote Debugging](#remote-debugging)
- [Time Travel Debugging](#time-travel-debugging)
- [Automation and Scripting](#automation-and-scripting)
- [Evidence Automation](#evidence-automation)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Install or update WinDbg:

```text
winget install Microsoft.WinDbg
winget upgrade Microsoft.WinDbg
```

Find the installed executable and command-line support:

```text
where.exe windbg
where.exe windbgx
Get-Command windbg, windbgx -ErrorAction SilentlyContinue
windbg -?
windbgx -?
```

Use whichever executable is present on the host. Microsoft documentation often
shows `windbg`; newer installs may also expose `windbgx`.

Launch, attach, or inspect a dump:

```text
windbg -y srv*C:\Symbols*https://msdl.microsoft.com/download/symbols C:\work\target.exe arg1 arg2
windbg -p 1234
windbg -pn target.exe
windbg -pv -p 1234
windbg -z C:\dumps\target.dmp
windbg -y srv*C:\Symbols*https://msdl.microsoft.com/download/symbols -i C:\symbols\images -z C:\dumps\memory.dmp
```

Start kernel sessions:

```text
windbg -k net:port=50000,key=1.2.3.4
windbg -kl
```

Inside WinDbg:

```text
?
.hh
.symfix C:\Symbols
.sympath
.reload
lm
g
q
```

Crash or stop triage:

```text
!analyze -v
.lastevent
.ecxr
.exr -1
k
kv
~* k
r
u @rip L20
dq @rsp L20
lmv m target
```

Kernel triage:

```text
!analyze -v
.bugcheck
lm
!process 0 1
!thread
.thread <ETHREAD>
k
r
```

## Command Model

WinDbg uses debugger commands, meta-commands, extension commands, and UI
actions that call the same debugging engine.

Common command groups:

- Regular commands: `k`, `r`, `u`, `d*`, `lm`, `bp`, `ba`, `g`, `p`, `t`.
- Dot commands: `.sympath`, `.reload`, `.ecxr`, `.cxr`, `.process`, `.thread`,
  `.dump`, `.logopen`, `.logclose`.
- Extension commands: `!analyze`, `!address`, `!process`, `!thread`,
  `!handle`, `!tt`.
- Data model command: `dx`.
- Help commands: `?`, `.hh`, and command-specific Microsoft Learn pages.

Use full commands in evidence when a short alias would be ambiguous. Short
commands are normal interactively, but command files should be readable on
their own.

Important parser rules:

- Multiple startup commands passed with `-c` are separated with semicolons.
- Target executable arguments appear after the executable name.
- The default expression evaluator can be selected with `-ee masm` or
  `-ee c++`.
- In C++ expression syntax, register references need `@`, such as `@rip`.
- Address ranges often use `L<count>`, such as `dq @rsp L20`.
- Source line breakpoints use backticks, such as ``bp `source.c:31` ``.
- Command files can be loaded with the `$<`, `$><`, `$$<`, `$$><`, and
  `$$>a<` command family.

## Toolchain and Session Setup

Record the debugger and host context:

```text
windbg -?
winget list Microsoft.WinDbg
where.exe windbg
where.exe windbgx
ver
systeminfo
```

Record the session state inside WinDbg:

```text
vertarget
.chain
.sympath
.srcpath
lm
```

Use a local symbol cache:

```text
.symfix C:\Symbols
.sympath
.reload
```

Or set a complete symbol path explicitly:

```text
.sympath srv*C:\Symbols*https://msdl.microsoft.com/download/symbols
.reload /f
```

Enable logging early:

```text
.logopen /t C:\evidence\windbg-session.log
.logclose
```

Prefer absolute paths for logs, dumps, scripts, symbol caches, source paths,
and saved memory. Relative paths depend on the debugger current directory and
can drift across UI launches, command-line launches, and remote sessions.

## Launch, Attach, Dumps, and Kernel Sessions

Launch a user-mode target:

```text
windbg C:\work\target.exe arg1 arg2
windbg -g C:\work\target.exe arg1 arg2
windbg -o C:\work\target.exe arg1 arg2
```

`-g` ignores the initial breakpoint. `-o` debugs child processes launched by
the target.

Attach to a user-mode target:

```text
windbg -p 1234
windbg -pn target.exe
windbg -psn ServiceName
windbg -pv -p 1234
```

`-pv` is noninvasive user-mode attach. Record whether an attach was invasive,
noninvasive, by PID, by process name, or by service name.

Open dump files:

```text
windbg -z C:\dumps\target.dmp
windbg -y srv*C:\Symbols*https://msdl.microsoft.com/download/symbols -i C:\images -z C:\dumps\memory.dmp
.opendump C:\dumps\second.dmp
g
```

Start kernel debugging:

```text
windbg -k net:port=50000,key=1.2.3.4
windbg -kl
```

Kernel debugging usually has a host computer running WinDbg and a target
computer running the code being debugged. The target must be configured for the
chosen transport before the host connects.

Record:

- Launch, attach, dump, local kernel, or remote kernel mode.
- Exact command line and target arguments.
- Symbol path, image path, source path, and extension path.
- Whether initial break, final break, child-process debugging, noninvasive
  attach, debug heap, or handle inheritance settings were changed.
- Kernel transport, target configuration, port, key, and BCDEdit settings when
  kernel debugging is used.

## Symbols, Source, Images, and Extensions

Symbols:

```text
.symfix C:\Symbols
.sympath
.sympath srv*C:\Symbols*https://msdl.microsoft.com/download/symbols
.reload
.reload /f
!sym noisy
```

Modules and symbol lookup:

```text
lm
lmv
lmv m target
x target!*
x target!*main*
ln @rip
```

Source:

```text
.srcpath
.srcpath C:\src\target
.srcfix
```

Extensions:

```text
.chain
.load C:\path\extension.dll
.loadby sos clr
!analyze -v
```

Use `.chain` to record the loaded extension DLLs and search order. For managed
code, load the extension that matches the runtime in the process or dump.

Missing or mismatched symbols are evidence quality problems, not cosmetic
problems. Record `lmv` output for modules that matter to the finding.

## Breakpoints and Watchpoints

Software breakpoints:

```text
bp target!Function
bu target!Function
bm target!*Parse*
bp `source.c:31`
bp target!Function+0x12 7
bl
bc 0
bd 0
be 0
```

Use `bu` for unresolved symbol breakpoints, such as code that will load later.
Use `bm` for symbol patterns. `bp`, `bu`, and `bm` set software breakpoints by
replacing an instruction with a break instruction.

Processor breakpoints:

```text
ba e1 target!Function
ba r4 myVar
ba w8 00000123`45678000
bl
```

Use `ba` for read, write, or execute access breakpoints. Access values include
`e` for execute, `r` for read/write, and `w` for write. Size limits are
architecture-dependent; x64 supports 1, 2, 4, or 8 bytes, with execute
breakpoints using size 1.

Conditional and command breakpoints:

```text
bp target!Function ".printf \"hit rip=%p rsp=%p\n\", @rip, @rsp; k; g"
ba w8 00000123`45678000 ".printf \"write at %p\n\", @rip; k; g"
```

Breakpoint command strings can change execution if they resume with `g`, alter
state, or call extension commands. Record the command string exactly.

## Exceptions, Events, and Crash Context

Exception and event filters:

```text
sx
sxe av
sxd av
sxn av
sxi av
sxr
```

The `sx*` commands control debugger behavior when exceptions or events occur.
Changing first-chance or second-chance behavior can change whether the target
continues normally or stops in the debugger.

Crash context:

```text
.lastevent
!analyze -v
.exr -1
.ecxr
k
kv
r
u @rip L20
```

For user-mode dump triage, `.ecxr` sets the register context to the current
exception context when available. Use `.cxr` with a context-record address when
the relevant context is explicit.

Kernel crash context:

```text
!analyze -v
.bugcheck
.trap <TrapFrame>
.cxr <ContextRecord>
k
kv
r
```

Record whether stack and register output came from the default context, an
exception context, a context record, a trap frame, or a selected kernel thread.

## Process, Thread, and Kernel Context

User-mode process and thread commands:

```text
|
~
~* k
~0s
k
```

Kernel process and thread commands:

```text
!process 0 0
!process 0 1
!process 0 7
!thread
.process /p /r <EPROCESS>
.thread <ETHREAD>
k
```

Process context controls how virtual addresses are interpreted in kernel-mode
debugging. Register context controls which thread or saved context supplies
register values and stack walking.

Context changes can make the same address expression mean different things.
Record `.process`, `.thread`, `.cxr`, `.ecxr`, `.trap`, process selection, and
thread selection before relying on address, stack, or register evidence.

## Stack, Registers, and Instruction State

Stack:

```text
k
kb
kp
kP
kv
~* k
~* kv
```

The `k*` commands display stack backtraces. In user mode, the stack trace is
based on the current thread. In kernel mode, it is based on the current register
context.

Registers:

```text
r
r @rip
r @rsp
r efl
r rip=00007ff6`00001000
```

The `r` command displays or modifies registers, pseudo-registers, flags, and
fixed-name aliases. Register writes are state-changing.

Disassembly:

```text
u @rip
u @rip L20
ub @rip
uf target!Function
```

Stepping and run control:

```text
g
p
t
gu
pa <Address>
ta <Address>
```

Use architecture-specific register names in notes. `@rip` and `@rsp` are x64;
adapt to the target architecture.

## Memory and Address Space

Display memory:

```text
db @rsp L80
dq @rsp L20
dd @rsp L20
du poi(@rsp)
da poi(@rsp)
dps @rsp L20
```

The `d*` commands display memory in different formats. If a range is omitted,
WinDbg continues from the previous display command, which is convenient
interactively but weak in evidence. Use explicit ranges in notes and scripts.

Address-space summary:

```text
!address
!address -summary
!address @rip
```

Save memory:

```text
.writemem C:\evidence\region.bin 00000123`45670000 L1000
```

Memory reads can fail because pages are invalid, paged out, excluded from a
dump, or interpreted under the wrong process context. Record the context and
the exact range.

## Dump Creation

Create a dump from a live target:

```text
.dump /ma C:\evidence\target-full.dmp
.dump /u /ma C:\evidence\target.dmp
```

The `.dump` command creates user-mode or kernel-mode dump files. Dump contents
depend on the selected options and the target state. Keep the dump file, input,
symbols, command log, and exact dump command together.

Use `.writemem` for a specific memory range rather than a full process or
kernel dump:

```text
.writemem C:\evidence\stack.bin @rsp L1000
```

Dump creation itself can expose sensitive process memory, file paths, registry
data, handles, credentials, or kernel state. Treat generated dumps as sensitive
evidence.

## Remote Debugging

Remote debugging can mean either a remote debugging server or a process server.
Use the Microsoft docs terminology in notes.

Create a debugging server from an existing session:

```text
.server tcp:port=5005
```

Connect as a debugging client:

```text
windbg -remote tcp:Port=5005,Server=YourHostComputer
```

Start a remote kernel debugging server from the command line:

```text
windbg -server tcp:port=5005 -k net:port=50000,key=1.2.3.4
windbg -remote tcp:Port=5005,Server=YourHostComputer
```

Process-server sessions are different. A process server runs on the server
computer and a smart client does the debugging work:

```text
dbgsrv -t tcp:port=4000
windbg -premote tcp:server=ServerName,port=4000
```

Record:

- Whether the session used a debugging server, process server, or kernel
  transport.
- Server host, client host, target host, transport, port, and connection
  string.
- Which paths are evaluated on the server versus local client.
- All connected clients when collaborative debugging is used.
- Any security mode or remote-debug security decisions.

Remote debugging exposes debugger control over the target. Keep it on a trusted
lab network or a controlled interface.

## Time Travel Debugging

Use TTD when a user-mode bug is hard to reproduce or when the execution history
matters more than a point-in-time dump.

Core commands and data model queries:

```text
!tt
!tt 0
!tt 50
!tt 100
!tt <Position>
dx Debugger.Sessions
dx -g @$curprocess.TTD.Events
```

Backward navigation commands are available in TTD traces:

```text
p-
t-
g-
```

TTD traces can contain sensitive file paths, registry data, memory contents,
file contents, and process activity. Record how the trace was captured, where
the `.run` trace and index files are stored, and which trace position supports
the observation.

## Automation and Scripting

Start with a command:

```text
windbg -c ".symfix C:\Symbols; .reload; g" C:\work\target.exe arg1
```

Start with a command file:

```text
windbg -c "$$<C:\evidence\triage.wds" -z C:\dumps\target.dmp
```

Run a command file after startup:

```text
$$<C:\evidence\triage.wds
$$>a<C:\evidence\triage-with-args.wds arg1 arg2
```

Loop over command output:

```text
.foreach (mod { lm 1m }) { .echo ${mod} }
```

Use JavaScript scripting or `dx` when the workflow needs debugger data model
objects instead of text parsing:

```text
.scriptload C:\evidence\helpers.js
dx Debugger.Sessions
```

Prefer command files for simple, replayable evidence capture. Use JavaScript
or data model queries when text parsing would hide assumptions.

## Evidence Automation

Create `C:\evidence\target-YYYYMMDD-HHMMSS\triage.wds`:

```text
.logopen /t C:\evidence\target-YYYYMMDD-HHMMSS\windbg.log
vertarget
.sympath
.srcpath
.chain
lmv
.lastevent
!analyze -v
.exr -1
.ecxr
k
kv
~* k
r
u @rip L20
dq @rsp L20
!address -summary
.logclose
q
```

Run it on a dump:

```text
windbg -y srv*C:\Symbols*https://msdl.microsoft.com/download/symbols ^
  -c "$$<C:\evidence\target-YYYYMMDD-HHMMSS\triage.wds" ^
  -z C:\dumps\target.dmp
```

For a live process, attach and create a dump before invasive experiments:

```text
.logopen /t C:\evidence\target-YYYYMMDD-HHMMSS\live.log
.dump /u /ma C:\evidence\target-YYYYMMDD-HHMMSS\target.dmp
~* k
r
lmv
.logclose
```

Keep scripts, logs, dumps, saved memory, target hashes, inputs, symbol paths,
source paths, and extension versions together.

## Failure Modes

`windbg` or `windbgx` not found

- Install WinDbg with Windows Package Manager, Microsoft Store, or direct
  installer.
- Use `where.exe windbg` and `where.exe windbgx`.
- Record the actual executable path.

Symbols do not load

- Check `.sympath` and `_NT_SYMBOL_PATH`.
- Use `.symfix C:\Symbols` and `.reload /f`.
- Use `!sym noisy` for symbol loading diagnostics.
- Check `lmv m <module>` for PDB path, timestamp, checksum, and symbol status.

No source lines

- Check `.srcpath` and `.srcfix`.
- Confirm private symbols contain source path information.
- Record when evidence is assembly-only.

Breakpoint does not hit

- Check `bl`.
- Use `bu` for code that will load later.
- Use `bm` for symbol patterns.
- Confirm module load with `lm`.
- Use module-relative or symbol breakpoints rather than stale absolute
  addresses.

Processor breakpoint fails

- Confirm access type and size.
- Remember hardware breakpoint count is architecture-limited.
- Use `ba e1` for read-only executable code that cannot be patched by a
  software breakpoint.

Stack looks wrong

- Confirm current process, thread, and register context.
- Use `.ecxr`, `.cxr`, `.trap`, or `.thread` only when that context is the one
  being analyzed.
- Capture raw stack memory with `dq @rsp L20`.

Kernel virtual addresses resolve incorrectly

- Confirm `.process` context and whether the address is user or kernel space.
- Refresh process context with `.process /p /r <EPROCESS>` when appropriate.
- Record context changes before address-based claims.

Dump lacks expected memory

- Confirm dump type and `.dump` options.
- Some memory may be absent from minidumps.
- Prefer a full dump when memory contents are central to the claim.

Remote session path confusion

- Record whether paths are resolved on the debugging server, process server,
  smart client, or local WinDbg client.
- Set symbol, image, and source paths explicitly on the side that uses them.

Debugger changed the observation

- Identify state-changing commands: register writes, memory writes,
  breakpoint command strings, exception handling changes, `.process /i`,
  thread freeze/suspend, `.dump`, extension commands with side effects, and TTD
  recording.
- Rerun without state changes before using the observation as final target
  behavior evidence.

## Evidence Checklist

Collect:

- WinDbg executable path, install source, command-line help output, and version
  context when available.
- Windows host version, target Windows version, target architecture, and dump
  architecture.
- Launch, attach, dump, local kernel, remote kernel, TTD, remote-debugging
  server, or process-server mode.
- Exact command line, command file, log file, and UI actions that affected
  execution.
- Target path, hash, command line, working directory, input files, and PID.
- Symbol path, source path, image path, extension path, `.chain`, `lmv`, and
  symbol diagnostics for relevant modules.
- Stop reason from `.lastevent`, exception record from `.exr -1`, bug check
  data from `.bugcheck`, and `!analyze -v` output when applicable.
- Current process, thread, and register context, including `.process`,
  `.thread`, `.ecxr`, `.cxr`, or `.trap` commands used.
- `k` or `kv`, `~* k`, `r`, `u @rip L20`, stack memory, relevant memory
  ranges, `lm`, and `!address -summary`.
- Breakpoints, access breakpoints, conditions, pass counts, and command
  strings from `bl`.
- Exception and event filter settings from `sx`.
- Dump files from `.dump`, memory files from `.writemem`, and TTD trace files
  when generated.
- Kernel transport details: BCDEdit settings, port, key, target name, host,
  target, and whether local kernel debugging was used.
- Remote debugging details: transport, server, client, process server, smart
  client, connected users, ports, and path-resolution assumptions.
- Every state-changing debugger command used before final evidence capture.

## References

- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/windbg-overview
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/windbg-command-line-preview
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/windbg-command-line-options
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/getting-started-with-windbg
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/getting-started-with-windbg--kernel-mode-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/analyzing-a-kernel-mode-dump-file-with-windbg
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/symbol-path
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/symbols
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/microsoft-public-symbols
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/source-path
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-srcpath---lsrcpath--set-source-path-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-reload--reload-module
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/lm--list-loaded-modules-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/x--examine-symbols-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/bp--bu--bm--set-breakpoint-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/ba--break-on-access-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/processor-breakpoints---ba-breakpoints-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/breakpoint-syntax
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/sx--sxd--sxe--sxi--sxn--sxr--sx---set-exceptions-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/controlling-exceptions-and-events
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-analyze
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-exr--display-exception-record-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-ecxr--display-exception-context-record-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-cxr--display-context-record-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/changing-contexts
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-thread--set-register-context-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-process
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/---thread-status-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/controlling-processes-and-threads
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/k--kb--kc--kd--kp--kp--kv--display-stack-backtrace-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/r--registers-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/register-syntax
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/d--da--db--dc--dd--dd--df--dp--dq--du--dw--dw--dyb--dyd--display-memor
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/u--unassemble-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-address
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-dump--create-dump-file-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-writemem--write-memory-to-file-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-logopen--open-log-file-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-logclose--close-log-file-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/remote-debugging-using-windbg
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/windbg-remote-preview
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/controlling-a-remote-debugging-session
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/controlling-a-process-server-session
- https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/bcdedit--dbgsettings
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/setting-up-a-network-debugging-connection
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/time-travel-debugging-overview
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/time-travel-debugging-extension-tt
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/time-travel-debugging-navigation-commands
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/time-travel-debugging-object-model
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/dx--display-visualizer-variables-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-----------------------a---run-script-file-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/using-script-files
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-foreach
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/javascript-debugger-scripting
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-load---loadby--load-extension-dll-
- https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-chain--list-debugger-extensions-
- https://learn.microsoft.com/en-us/dotnet/core/diagnostics/debugger-extensions
- https://learn.microsoft.com/en-us/dotnet/framework/tools/sos-dll-sos-debugging-extension
