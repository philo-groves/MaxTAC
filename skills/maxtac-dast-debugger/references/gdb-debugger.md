# GDB Debugger

Use GDB for native runtime debugging on Linux and other GNU-oriented targets,
especially C, C++, Fortran, Ada, Rust, and mixed native code. Prefer the
installed `help` output for exact option spelling because distro builds,
architecture ports, Python support, remote stubs, and target OS support vary.

Treat GDB as mutable execution. It can change target state through function
calls, assignments, register writes, memory writes, signal handling changes,
breakpoint commands, inferior control, and launch settings. Keep final evidence
separate from observations that only happen because GDB changed timing, ASLR,
environment, process control, or target state.

## Contents

- [Quick Commands](#quick-commands)
- [Command Model](#command-model)
- [Toolchain and Session Setup](#toolchain-and-session-setup)
- [Launch, Attach, and Core Files](#launch-attach-and-core-files)
- [Runtime Settings](#runtime-settings)
- [Breakpoints and Command Lists](#breakpoints-and-command-lists)
- [Watchpoints and Catchpoints](#watchpoints-and-catchpoints)
- [Process, Thread, Fork, and Inferior Control](#process-thread-fork-and-inferior-control)
- [Signals](#signals)
- [Stack, Registers, and Instruction State](#stack-registers-and-instruction-state)
- [Memory and Process Maps](#memory-and-process-maps)
- [Symbols, Files, and Source Paths](#symbols-files-and-source-paths)
- [Variables, Expressions, and Calls](#variables-expressions-and-calls)
- [Reverse Debugging and Record Replay](#reverse-debugging-and-record-replay)
- [Remote Debugging](#remote-debugging)
- [Automation and Scripting](#automation-and-scripting)
- [Evidence Automation](#evidence-automation)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Toolchain sanity:

```text
gdb --version
gdb --configuration
gdb --help
gdb -q -nx --version
gdbserver --version
```

Start, attach, or inspect a core:

```text
gdb -q -nx --args ./target arg1 arg2
gdb -q -nx ./target
gdb -q -nx -p "$PID"
gdb -q -nx ./target ./core
gdb -q -nx -c ./core
```

Inside GDB:

```text
help
apropos memory
show version
show configuration
file ./target
run arg1 arg2
start
starti
attach "$PID"
detach
continue
interrupt
kill
quit
```

Crash triage after a stop:

```text
info program
info inferiors
info threads
thread apply all bt full
bt full
frame
info frame
info args
info locals
info registers
x/16gx $sp
x/8i $pc
info proc mappings
info files
info sharedlibrary
```

Batch crash capture:

```text
gdb -q -nx -batch \
  -ex "set pagination off" \
  -ex "set confirm off" \
  -ex "run" \
  -ex "thread apply all bt full" \
  -ex "info registers" \
  -ex "info proc mappings" \
  -ex "info files" \
  --args ./target input.bin
```

## Command Model

GDB uses a command-line interpreter with abbreviated command names, command
classes, `info` commands for target state, and `show` commands for debugger
settings.

Use full commands in documentation and automation. Short forms such as `b`,
`r`, `c`, `n`, `s`, `bt`, `p`, and `x` are useful interactively, but full forms
are clearer in evidence.

Useful command discovery:

```text
help
help running
help breakpoints
help data
help files
help info
apropos syscall
complete info
show
info
```

Important parser rules:

- `run arg1 arg2` passes arguments through a shell on Unix by default.
- `set args ...` controls arguments for the next `run`.
- `--args` on the host command line stops GDB option parsing and treats
  following arguments as inferior arguments.
- `-nx` disables all init files; use it for reproducible sessions.
- `-iex "set auto-load off"` disables project auto-loads early enough to affect
  startup.
- Use `set variable name=value` instead of plain `set name=value` when the
  program variable name could collide with a GDB setting.

## Toolchain and Session Setup

Record the exact debugger:

```text
gdb --version
gdb --configuration
show version
show configuration
```

Start reproducibly:

```text
gdb -q -nx --args ./target arg1 arg2
gdb -q -nx -iex "set auto-load off" --args ./target arg1 arg2
```

Enable readable noninteractive output:

```text
set pagination off
set confirm off
set print pretty on
set print elements 0
set print repeats 0
set print frame-arguments all
set print address on
set print symbol-filename on
```

Enable logging:

```text
set logging file gdb.log
set logging overwrite on
set logging redirect off
set logging enabled on
show logging
```

Use `-nx` and `set auto-load off` when opening untrusted binaries, core files,
or working directories. GDB can auto-load local init files and extension scripts
when safe-path policy permits it.

## Launch, Attach, and Core Files

Launch with arguments:

```text
gdb -q -nx --args ./target arg1 arg2
(gdb) run
```

Or set arguments inside the session:

```text
file ./target
set args arg1 arg2
show args
run
```

Stop at a higher-level entrypoint:

```text
start
start arg1 arg2
```

Stop at the first instruction:

```text
starti
```

Attach:

```text
gdb -q -nx ./target "$PID"
gdb -q -nx -p "$PID"
attach "$PID"
detach
```

Inspect a core:

```text
gdb -q -nx ./target ./core
gdb -q -nx -c ./core
core-file ./core
thread apply all bt full
info registers
info files
```

Generate a live core when supported:

```text
gcore ./core.live
generate-core-file ./core.live
```

Record whether the evidence came from launch, attach, remote attach, or a core
file. Launch and attach paths can differ because arguments, environment, ASLR,
stdio, parent process, permissions, and shell startup behavior can differ.

## Runtime Settings

Arguments:

```text
set args --parse input.bin
show args
run
run --parse input.bin
```

Environment:

```text
show environment
show environment LD_PRELOAD
set environment KEY=VALUE
unset environment KEY
path /tmp/tools
show paths
```

Working directory:

```text
pwd
cd /tmp/repro
set cwd /tmp/repro
show cwd
```

Standard I/O:

```text
run < stdin.bin > stdout.log 2> stderr.log
tty /dev/pts/7
show inferior-tty
set inferior-tty
```

Shell and wrapper behavior:

```text
show startup-with-shell
set startup-with-shell off
set exec-wrapper env LD_PRELOAD=./libtest.so
show exec-wrapper
unset exec-wrapper
```

ASLR:

```text
show disable-randomization
set disable-randomization off
set disable-randomization on
```

On GNU/Linux, GDB may disable address randomization for launched programs by
default. Use `set disable-randomization off` when reproducing behavior that
depends on normal process layout.

## Breakpoints and Command Lists

Set common breakpoints:

```text
break main
break parser.c:120
break *0x401234
break namespace::Class::method
rbreak '^parse_'
tbreak main
hbreak *0x401234
```

Manage them:

```text
info breakpoints
info breakpoints $_hit_bpnum
disable 1
enable 1
delete 1
clear parser.c:120
save breakpoints breakpoints.gdb
source breakpoints.gdb
```

Set conditions and ignore counts:

```text
break parse if len > 4096
condition 1 len > 4096
ignore 1 10
```

Use breakpoint command lists for repeated evidence:

```text
break parse
commands
silent
printf "hit parse len=%zu\n", len
bt
info registers
x/16gx $sp
continue
end
```

If a command list resumes execution with `continue`, `step`, or another run
command, later commands in the same list are ignored. Put capture commands
before the resume command.

Check multi-location breakpoints carefully:

```text
info breakpoints
print $bpnum
print $_hit_bpnum
print $_hit_locno
```

Templates, overloaded functions, inlined functions, and shared libraries can
resolve one logical breakpoint to many concrete locations.

## Watchpoints and Catchpoints

Watch writes:

```text
watch global_var
watch -location *(int *)0x12345678
watch *ptr thread 2
```

Watch reads or reads/writes where supported:

```text
rwatch global_var
awatch global_var
info breakpoints
delete 2
```

Hardware watchpoint capacity is limited and architecture dependent. Software
watchpoints can be very slow because GDB may single-step and compare values.

Catch program events:

```text
catch throw
catch catch
catch signal SIGSEGV
catch syscall
catch syscall openat
catch syscall group:process
catch fork
catch vfork
catch exec
catch load
catch unload
```

Use catchpoints to observe runtime events without guessing the exact code
address first. Availability varies by OS, ABI, debug info, C++ runtime, syscall
database, and remote stub support.

## Process, Thread, Fork, and Inferior Control

Threads:

```text
info threads
thread 2
thread apply all bt
thread apply all bt full
thread apply 1 3 info registers
set print thread-events off
show print thread-events
```

Stepping:

```text
continue
next
step
finish
until
advance parser.c:120
stepi
nexti
display/i $pc
```

Multiple inferiors:

```text
info inferiors
inferior 2
add-inferior
remove-inferiors 2
detach inferiors 2
kill inferiors 2
info connections
```

Forks and exec:

```text
show follow-fork-mode
set follow-fork-mode child
set follow-fork-mode parent
show detach-on-fork
set detach-on-fork off
info inferiors
inferior 1
show follow-exec-mode
set follow-exec-mode new
```

By default, fork handling often follows the parent and detaches the child. If a
finding depends on child process behavior, record `follow-fork-mode`,
`detach-on-fork`, `follow-exec-mode`, and the selected inferior.

## Signals

Inspect signal handling:

```text
info signals
info signals SIGSEGV
info handle
```

Change signal handling:

```text
handle SIGPIPE nostop noprint pass
handle SIGSEGV stop print nopass
signal 0
signal SIGTERM
catch signal SIGSEGV
```

Signal policy changes can hide or create debugger-only behavior. Record every
`handle` change and distinguish "GDB stopped on a signal" from "the program
would terminate outside GDB."

## Stack, Registers, and Instruction State

Stack and frames:

```text
bt
bt full
thread apply all bt full
frame
frame 3
up
down
info frame
info args
info locals
```

Registers:

```text
info registers
info all-registers
info registers pc sp
p/x $pc
p/x $sp
set $pc = 0x401000
set $sp += 8
```

Disassembly:

```text
x/i $pc
x/8i $pc
disassemble
disassemble /m
disassemble /r
disassemble 0x401000,0x401080
```

For crash evidence, capture:

```text
info program
info registers
x/8i $pc
x/16gx $sp
bt full
thread apply all bt
info proc mappings
```

Use `$pc`, `$sp`, `$fp`, and `$ps` where available, but record the concrete
architecture because canonical register names, calling conventions, frame
unwinding, pointer authentication, and signal frames are target-specific.

## Memory and Process Maps

Examine memory:

```text
x/64bx $sp
x/16gx $sp
x/32i $pc
x/s $rdi
x/32xb 0x401000
```

Print values:

```text
print var
print/x var
print/a ptr
ptype var
whatis var
```

Dump memory:

```text
dump binary memory mem.bin 0x400000 0x401000
append binary memory mem.bin 0x401000 0x402000
restore mem.bin binary 0x500000
```

Process maps and descriptors where supported:

```text
info proc
info proc mappings
info proc files
info proc status
info files
maint info sections -all-objects
```

Memory restore, assignment, register writes, and binary patching are
state-changing. Use them for controlled experiments, record the exact command,
and rerun without them before making target-behavior claims.

## Symbols, Files, and Source Paths

Load files and symbols:

```text
file ./target
symbol-file ./target.debug
exec-file ./target
core-file ./core
add-symbol-file ./module.o 0x100000
```

Inspect files, sections, and shared libraries:

```text
info files
info target
info sharedlibrary
sharedlibrary
nosharedlibrary
maint info sections -all-objects
```

Source paths:

```text
directory /local/source/root
show directories
set substitute-path /build/root /local/source/root
show substitute-path
info source
list
```

Separate debug info:

```text
show debug-file-directory
set debug-file-directory /usr/lib/debug:./debug
show debuginfod enabled
set debuginfod enabled off
```

For remote or container targets, make host symbols and target binaries match.
Sourceware's GDB manual warns that mismatched or missing host-side files can
produce confusing debugging results and can affect multi-threaded GNU/Linux
debugging through `gdbserver`.

## Variables, Expressions, and Calls

Inspect without intentionally changing target state:

```text
print var
print/x var
print *ptr@10
ptype var
whatis var
info args
info locals
```

Assign values:

```text
set variable len = 0
print len = 4
set {int}0x601050 = 7
```

Call target functions:

```text
print function_name(arg1, arg2)
call function_name(arg1, arg2)
```

Use calls and assignments deliberately. They may allocate memory, acquire locks,
invoke signal handlers, change globals, perturb heap state, or crash the
process. Prefer passive `print`, `x`, `info registers`, and `info locals` when
that is enough.

Binary patching:

```text
show write
set write on
exec-file ./target
```

`set write on` opens executable and core files read/write after reload. Treat it
as a patching operation, not a normal debugging setting.

## Reverse Debugging and Record Replay

Start recording where supported:

```text
record full
info record
record stop
```

Branch tracing where supported:

```text
record btrace
record btrace pt
info record
```

Reverse execution:

```text
reverse-continue
reverse-step
reverse-stepi
reverse-next
reverse-nexti
reverse-finish
```

Process record/replay support is platform and architecture dependent. GDB's
manual documents support on several GNU/Linux architectures and notes that
`record btrace` does not record data, so variables and registers may be
unavailable during reverse execution. Confirm `info record` before relying on
reverse evidence.

## Remote Debugging

GDB remote debugging uses `target remote` or `target extended-remote` over the
GDB remote serial protocol. Use `gdbserver` on Unix-like targets when the target
can run it.

Basic `gdbserver` launch:

```text
# target
gdbserver :2345 ./target arg1 arg2

# host
gdb -q -nx ./target
(gdb) target remote target-host:2345
```

Attach through `gdbserver`:

```text
# target
gdbserver --attach :2345 "$PID"

# host
gdb -q -nx ./target
(gdb) target remote target-host:2345
```

Extended remote multi-process mode:

```text
# target
gdbserver --multi :2345

# host
gdb -q -nx ./target
(gdb) target extended-remote target-host:2345
(gdb) set remote exec-file /tmp/target
(gdb) run arg1 arg2
(gdb) monitor exit
(gdb) disconnect
```

Host-side symbols and libraries:

```text
file ./unstripped-target
set sysroot /path/to/target-root
set solib-search-path /path/to/target-libs
show sysroot
show solib-search-path
```

Remote diagnostics:

```text
set remotetimeout 10
show remotetimeout
set remotelogfile remote.log
set remotelogbase hex
monitor help
monitor set debug remote on
monitor set debug-file /tmp/gdbserver.log
```

Key mode differences:

- `target remote`: the program is already selected by `gdbserver`; `run` is not
  supported, and the connection usually closes on detach or process exit.
- `target extended-remote`: GDB can remain connected after exit or detach, and
  can run or attach after connecting when the remote stub supports it.

Do not expose `gdbserver` on public or shared networks. The official manual
states that `gdbserver` has no built-in security and a GDB connection runs with
the privileges of the user that started `gdbserver`.

## Automation and Scripting

Batch mode:

```text
gdb -q -nx -batch \
  -ex "set pagination off" \
  -ex "run" \
  -ex "thread apply all bt full" \
  -ex "info registers" \
  --args ./target input.bin
```

Command file:

```text
gdb -q -nx -x ./triage.gdb --args ./target input.bin
```

Example `triage.gdb`:

```text
set pagination off
set confirm off
set logging file gdb.log
set logging overwrite on
set logging enabled on
run
thread apply all bt full
info registers
info proc mappings
info files
quit
```

GDB command files support comments, `if`, `else`, `while`, `loop_break`,
`loop_continue`, and `end`.

Controlled output:

```text
echo stopped\n
output/x $pc
printf "pc=%p sp=%p\n", $pc, $sp
```

Python inside GDB:

```text
python print(23)
python
>import gdb
>print(gdb.execute("info registers", to_string=True))
>end
source ./helpers.py
```

GDB must be built with Python support. Check:

```text
python-interactive import sys; print(sys.version)
python help(gdb)
```

Machine-oriented control:

```text
gdb -q -nx --interpreter=mi3 ./target
interpreter-exec mi "-data-list-register-names"
```

Use CLI command files for simple evidence capture. Use Python or GDB/MI when
you need structured parsing, IDE integration, conditional automation, or
machine-readable control.

## Evidence Automation

Create a run directory:

```text
RUN_DIR="evidence/$(date +%Y%m%d-%H%M%S)-gdb"
mkdir -p "$RUN_DIR"
gdb --version > "$RUN_DIR/gdb-version.txt"
gdb --configuration > "$RUN_DIR/gdb-configuration.txt"
```

Create `triage.gdb`:

```text
set pagination off
set confirm off
set print pretty on
set print elements 0
set print repeats 0
set print frame-arguments all
set logging file evidence/gdb-session.log
set logging overwrite on
set logging redirect off
set logging enabled on
show version
show configuration
show args
show environment
show disable-randomization
run
info program
info inferiors
info threads
thread apply all bt full
info registers
x/8i $pc
x/16gx $sp
info proc mappings
info proc files
info files
info sharedlibrary
set logging enabled off
quit
```

Run it:

```text
gdb -q -nx -x ./triage.gdb --args ./target "$INPUT" > "$RUN_DIR/gdb.out" 2>&1
```

For a crashing target:

```text
gdb -q -nx -batch \
  -ex "set pagination off" \
  -ex "run" \
  -ex "thread apply all bt full" \
  -ex "info registers" \
  -ex "x/8i \$pc" \
  -ex "x/16gx \$sp" \
  -ex "info proc mappings" \
  -ex "info files" \
  --args ./target "$INPUT" \
  > "$RUN_DIR/gdb-crash.log" 2>&1
```

If the process is still live and the platform supports it, generate the core
from inside GDB before quitting:

```text
gcore ./core.live
generate-core-file ./core.live
```

Keep command files, logs, core files, input files, target hashes, and version
metadata together so the debugging actions are replayable.

## Failure Modes

`gdb: command not found`

- Install GDB or use the toolchain-provided path.
- Record whether the build is distro GDB, cross-GDB, vendor GDB, or self-built.

Unexpected commands or startup behavior

- Rerun with `gdb -q -nx`.
- Add `-iex "set auto-load off"` before loading an untrusted target.
- Check `show auto-load` and `info auto-load`.

Breakpoint stays pending or resolves wrong

- Check `info breakpoints`.
- Confirm the shared library is loaded with `info sharedlibrary`.
- Confirm source paths, symbols, and build IDs.
- Use an address breakpoint only after recording runtime mappings.

No useful variables

- The binary may be optimized, stripped, or missing debug info.
- Fall back to `info registers`, `x`, `disassemble`, and `info files`.
- Add separate debug files or install debuginfo packages.

Backtrace is corrupt

- Stack memory or frame pointers may be corrupted or optimized out.
- Capture `info frame`, `x/16gx $sp`, and `info registers`.
- Use all-thread backtraces and runtime mappings to corroborate.

Attach denied

- Confirm PID, ownership, ptrace policy, namespaces, containers, seccomp,
  Yama `ptrace_scope`, and capabilities.
- Preserve the exact attach error.

Addresses differ across runs

- Capture `show disable-randomization`, `info proc mappings`, and `info files`.
- Turn normal ASLR back on with `set disable-randomization off` when needed.

Remote target launches locally by mistake

- Confirm `target remote` or `target extended-remote`.
- In extended mode, confirm `set remote exec-file`.
- Confirm `file`, `set sysroot`, and `set solib-search-path`.

`gdbserver` connection refused or stale

- Start `gdbserver` before `target remote`.
- Check host, port, firewall, bind address, container network, and whether a
  previous `gdbserver` is still holding the port.
- Use `monitor exit` and `disconnect` for extended remote cleanup.

Watchpoint fails or slows execution badly

- Hardware watchpoint slots may be exhausted.
- Remote stubs may limit watchpoint count.
- Software watchpoints can single-step every instruction.

Expression or function call changes behavior

- Prefer passive inspection first.
- Record every `call`, `print function(...)`, `set variable`, register write,
  memory restore, and signal delivery.

## Evidence Checklist

Collect:

- GDB version, configuration, target architecture, and host OS.
- Target path, hash, build ID, architecture, debug info state, and symbols used.
- Launch, attach, remote, or core-file mode.
- Exact command line, GDB command file, log output, and batch output.
- Arguments, environment, working directory, stdio routing, shell/wrapper state,
  and ASLR setting.
- PID, inferior list, thread list, selected thread/frame, stop reason, signal,
  and process status.
- `thread apply all bt full`, `info registers`, `x/8i $pc`, `x/16gx $sp`,
  `info proc mappings`, `info files`, and `info sharedlibrary`.
- Breakpoints, watchpoints, catchpoints, conditions, ignore counts, and command
  lists.
- Signal handling changes from `handle`.
- Fork/exec settings: `follow-fork-mode`, `detach-on-fork`,
  `follow-exec-mode`, and selected inferior.
- Any state-changing operations: calls, assignments, register writes, memory
  writes, restore operations, `jump`, `return`, `signal`, `kill`, patching, or
  changed launch settings.
- Core file or original crash core when available.
- Remote details: `gdbserver` version/path, command line, transport, host/port,
  mode (`remote` or `extended-remote`), `sysroot`, `solib-search-path`, remote
  exec path, and monitor/debug logs.
- Record/replay method and `info record` output when reverse debugging is used.

## References

- https://sourceware.org/gdb/current/onlinedocs/gdb.html/
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Invoking-GDB.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Mode-Options.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Startup.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Logging-Output.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Starting.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Arguments.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Environment.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Input_002fOutput.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Attach.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Set-Breaks.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Set-Watchpoints.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Set-Catchpoints.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Break-Commands.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Signals.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Threads.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Forks.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Inferiors-Connections-and-Programs.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Backtrace.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Frame-Info.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Registers.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Memory.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Assignment.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Patching.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Dump_002fRestore-Files.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Core-File-Generation.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Files.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Source-Path.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Separate-Debug-Files.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Process-Information.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Reverse-Execution.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Process-Record-and-Replay.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Remote-Debugging.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Connecting.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Server.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Remote-Configuration.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Command-Files.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Output.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Python.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Python-Commands.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/Python-API.html
- https://sourceware.org/gdb/current/onlinedocs/gdb.html/GDB_002fMI.html
- https://man7.org/linux/man-pages/man1/gdb.1.html
