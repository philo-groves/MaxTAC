# Radare2 Debugging

Use radare2 debugging when static analysis or ESIL cannot answer a runtime
question: crash state, register control, heap layout, loaded modules, signal
behavior, descriptors, environment, or remote target state. Treat debugging as
mutable execution. Capture exact commands, runtime maps, and any state changes
made during the session.

## Contents

- [Quick Commands](#quick-commands)
- [Debugger Mental Model](#debugger-mental-model)
- [Session Setup](#session-setup)
- [Rarun2 Runtime Profiles](#rarun2-runtime-profiles)
- [Entrypoints and Early Code](#entrypoints-and-early-code)
- [Breakpoints and Control Flow](#breakpoints-and-control-flow)
- [Registers and Arguments](#registers-and-arguments)
- [Memory Maps and Modules](#memory-maps-and-modules)
- [Memory Inspection and Snapshots](#memory-inspection-and-snapshots)
- [Heap Inspection](#heap-inspection)
- [Signals and Exceptions](#signals-and-exceptions)
- [File Descriptors and I/O](#file-descriptors-and-io)
- [Reverse Debugging](#reverse-debugging)
- [Visual Debugging](#visual-debugging)
- [Remote Debugging](#remote-debugging)
- [Vulnerability Research Patterns](#vulnerability-research-patterns)
- [Evidence Checklist](#evidence-checklist)
- [Cautions](#cautions)
- [Official References](#official-references)

## Quick Commands

Start or attach:

```text
r2 -d ./target              start target in native debugger mode
r2 -d <pid>                 attach to a running process
r2 -d gdb://host:port       connect to a gdbserver
r2 -D gdb gdb://host:port   force the gdb debug backend
r2 -r run.rr2 -d ./target   run with a rarun2 profile
r2 -R aslr=no -d ./target   pass one rarun2 directive
```

Debugger setup:

```text
d?                  debugger help
dL                  list or change debugger backend
di                  show debugger backend information
e dbg.bep=entry     break at binary entrypoint
e dbg.bep=main      break at main when available
ood                 reopen in debug mode
ood arg1 arg2       reopen with arguments
doof <uri-or-file>  reopen and rebase session data
```

Break, run, and step:

```text
db sym.main         set breakpoint at flag
db 0x401234         set breakpoint at address
db                  list breakpoints
db- 0x401234        remove breakpoint
dc                  continue
dcu sym.main        continue until address or flag
dcs                 continue until syscall
ds                  step into one instruction
3ds                 step three instructions
dso                 step over
dbt                 show backtrace
```

Inspect process state:

```text
dr                  show registers
dr rip              show one register
dr rip=0x401000     set one register
dro                 show old register values
drr                 show register references
pd 10 @ rip         disassemble at current PC
px 64 @ rsp         dump stack bytes
ps @ rdi            print string at pointer register
```

Maps, modules, heap, descriptors, and signals:

```text
dm                  list memory maps
dmj                 list memory maps as JSON
dm. @ rip           show map for current PC
dmm                 list loaded modules
dmi libc            list symbols from loaded library
dmS libc            list sections from loaded library
dmd dump.bin        dump current map region
dmh                 show heap chunks
dmhg                show heap graph
dmhc @ <chunk>      show malloc_chunk at chunk
dk                  list signal handlers
dko SIGSEGV skip    configure signal handling
dd                  list file descriptors
ddr <fd> <addr> <size>
ddw <fd> <addr> <size>
```

Reverse debugging:

```text
dts+                save current debug state
dts                 list saved states
dtsC 0 before-copy  comment a saved state
dsb                 step backward
dcb                 continue backward to latest breakpoint
dtst name           export recorded states
dtsf name           import recorded states
```

Remote GDB extras:

```text
:?                  gdb IO plugin help
:pktsz              show packet size
:pktsz 512          set packet size
:monitor help       send monitor command
:detach             detach remote target
```

## Debugger Mental Model

Radare2 debuggers are IO plugins. The same `d*` command family works across
native, `gdb://`, `winkd://`, and other debug-capable backends where supported.
Process memory is treated like mapped data: read it, disassemble it, dump it,
compare it, or inspect it with ordinary `p*`, `x*`, `a*`, and `i*` commands.

Use the debugger when the question depends on runtime state:

- What exact instruction faults?
- Is `PC`, a branch target, a function pointer, or a vtable controlled?
- Which input offset becomes a register, pointer, size, or index?
- Which map contains a pointer or crash address?
- Which module implementation is called at runtime?
- What allocator state exists before and after a write, free, or realloc?
- Which signal, exception, descriptor, environment value, or working directory
  changes the behavior?

Prefer static analysis or ESIL for local deterministic questions. Move to native
or remote debugging when loader state, syscalls, imports, ASLR, heap behavior,
threads, signals, or concrete crash reproduction matters.

## Session Setup

Start a target:

```text
r2 -d ./target
```

Attach to a running process:

```text
r2 -d <pid>
```

The debugger may stop in the dynamic loader before the executable entrypoint.
That is normal. Decide whether the session should stop early, at entry, or at
`main`:

```text
e dbg.bep=entry
e dbg.bep=main
ood
```

Continue to a known point:

```text
dcu main
dcu sym.target_parser
dcu 0x401234
```

Capture baseline metadata:

```text
iI
ij
dmj
dmm
dr
e dbg.*
```

Record:

- Target path, hash, architecture, bits, and format.
- Spawn versus attach.
- Exact command line and input.
- Runtime maps from `dm` or `dmj`.
- Backend from `di` or `dL`.
- Breakpoint strategy.
- Any mutations made with `dr`, `dmp`, `dd`, memory writes, or signal controls.

## Rarun2 Runtime Profiles

Use `rarun2` when reproduction depends on arguments, stdin/stdout, environment,
ASLR, preloads, network sockets, working directory, or timeouts. Profiles are
plain `key=value` files.

Example:

```text
program=./target
arg1=--parse
arg2=input.bin
stdin=input.bin
stdout=stdout.log
stderr=stderr.log
setenv=FOO=BAR
timeout=5
aslr=no
```

Run it:

```text
r2 -r run.rr2 -d ./target
```

Pass one directive:

```text
r2 -R aslr=no -d ./target
```

Useful keys:

- `program`, `arg0`, `arg1`, `arg2`: executable and arguments.
- `stdin`, `stdout`, `stderr`, `stdio`, `input`: deterministic I/O.
- `setenv`, `unsetenv`, `clearenv`, `envfile`: environment control.
- `aslr=no`: reduce address variance when appropriate.
- `timeout`, `timeoutsig`: bound runaway inputs.
- `chdir`, `chroot`: reproduce path-sensitive behavior.
- `preload`, `libpath`, `r2preload`: dynamic loader behavior.
- `connect`, `listen`: socket-backed protocol tests.

Prefer a profile over an ad hoc shell wrapper for reportable evidence.

## Entrypoints and Early Code

Do not assume `main` is the first relevant code. Constructors, TLS callbacks,
library initialization, loader hooks, anti-debug checks, and signal setup may run
first.

Break early:

```text
e dbg.bep=entry
ood
dc
```

Break at main:

```text
e dbg.bep=main
ood
dc
```

Investigate early paths:

```text
db entry0
db sym._init
db sym.imp.__libc_start_main
dc
pd 20 @ rip
dr
dbt
```

For packed, protected, or malware-like samples, prefer early breakpoints. The
target may unpack code, patch imports, resolve APIs, or check tracing before the
obvious application entrypoint.

## Breakpoints and Control Flow

Set and list breakpoints:

```text
db sym.main
db sym.parser
db sym.imp.memcpy
db 0x401234
db
```

Remove one:

```text
db- 0x401234
```

Continue:

```text
dc
dcu sym.parser
dcu 0x401300
dcs
```

Step:

```text
ds
10ds
dso
```

Use `db?` in-session for conditional breakpoints, hardware breakpoints,
command-on-hit behavior, and backend-specific variants. Syntax and support vary
by version and backend, so confirm live help before scripting advanced forms.

High-value breakpoint targets:

- Parser entrypoints found from strings, imports, or xrefs.
- Input APIs: `read`, `recv`, `fgets`, protocol callbacks.
- Copy and format APIs: `memcpy`, `memmove`, `strcpy`, `snprintf`, `printf`.
- Allocation APIs: `malloc`, `calloc`, `realloc`, `free`, `mmap`,
  `VirtualAlloc`.
- Bounds checks and error handling around suspicious values.
- Indirect calls, virtual dispatch, and callback invocation.
- Crash addresses rebased into runtime maps.

At each important breakpoint, capture:

```text
dr
drr
pd 12 @ rip
px 64 @ rsp
dbt
```

## Registers and Arguments

Show and modify registers:

```text
dr
dr rip
dr rip=0x401000
dro
drr
```

Dump register values as flags:

```text
dr*
.dr*
```

Use generic aliases where supported:

```text
dr PC
dr SP
dr BP
```

Calling-convention reminders:

- x86-64 System V: `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`.
- x86-64 Windows: `rcx`, `rdx`, `r8`, `r9`.
- i386: stack arguments are common.
- ARM/AArch64: `r0`-`r3` or `x0`-`x7`.

Always confirm with the actual callsite and ABI. Optimized code and wrappers can
make generic recipes wrong.

Argument inspection examples:

```text
dr rdi
ps @ rdi
px 64 @ rsi
?v rdx
```

Crash control checks:

```text
dr
drr
pd 8 @ rip
px 128 @ rsp
dm. @ rip
```

Look for input influence over:

- Program counter or indirect branch target.
- Faulting memory operand.
- Stack pointer, frame pointer, or return address.
- Length, index, offset, or allocation size.
- Vtable pointer, function pointer, callback, or exception handler data.
- Freed or stale heap pointer.

## Memory Maps and Modules

List maps and modules:

```text
dm
dmj
dm=
dm. @ rip
dmm
```

Inspect loaded libraries:

```text
dmi libc
dmi libc system
dmS libc
```

Change page permissions only in controlled experiments:

```text
dmp <addr> <size> rwx
```

Map triage:

- Identify whether an address is unmapped, stack, heap, executable code,
  library data, JIT/unpacked code, or a guard page.
- Record runtime bases under ASLR.
- Check whether faulting data is in writable, executable, or read-only memory.
- Compare loaded modules with static imports to find runtime-only code paths.
- Use `dmj` for machine-readable evidence.

## Memory Inspection and Snapshots

Runtime memory uses ordinary print commands:

```text
px 64 @ rsp
pxw 32 @ rsp
pxq 16 @ rsp
ps @ rdi
pz @ rdi
pc 64 @ rdi
```

Dump current map region:

```text
dmd dump.bin
```

Dump all maps when supported:

```text
dmda all-maps
```

Take and restore snapshots:

```text
dms snap1 <addr>
dms- snap1 <addr>
```

Use snapshots for short, controlled windows:

- Before and after a copy, decode loop, free, realloc, or indirect call.
- Before a destructive parser path.
- Before continuing from a near-crash state.

For overwrite triage:

```text
px 128 @ <dst>
dms before <dst>
dc
px 128 @ <dst>
```

Use `dm?`, `dmd?`, and `dms?` in-session because dump and snapshot support can
vary by platform and version.

## Heap Inspection

Show heap state:

```text
dmh
dmhg
dmhc @ <chunk_addr>
dmha
dmhm
dmhb
dmhf
dmht
```

Use `dmh?` for the current allocator and backend. Heap helpers are platform- and
allocator-sensitive; glibc-oriented output may not apply to Windows heaps, musl,
jemalloc, tcmalloc, hardened allocators, or custom allocators.

Heap triage loop:

```text
db sym.imp.malloc
db sym.imp.free
dc
dr
dbt
drr
dmh
dmhc @ <chunk>
px 128 @ <chunk>
```

Capture:

- Allocation callsite and requested size.
- Returned pointer and map.
- Free callsite and pointer.
- Chunk metadata before and after corruption.
- Bin, fastbin, or tcache state when available.
- Input offset responsible for overwrite or stale use.

## Signals and Exceptions

List and inspect signals:

```text
dk
dkj
dk?SIGSEGV
dk?11
```

Send or configure:

```text
dk SIGTERM
dko SIGSEGV
dko SIGSEGV skip
dko SIGSEGV cont
```

Radare2 abstracts signals across platforms, so Windows exceptions may be exposed
through this command family.

Crash capture:

```text
dc
dk
dr
drr
dbt
pd 12 @ rip
px 128 @ rsp
dm. @ rip
```

Do not skip a crash signal in final evidence unless the target intentionally
handles it and that behavior is part of the finding.

## File Descriptors and I/O

List descriptors:

```text
dd
```

Open, close, seek, duplicate, pipe, read, and write:

```text
dd /path/to/file
dd+ /path/to/file
dd- <fd>
dds <fd> <offset>
ddd <oldfd> <newfd>
ddf <addr>
ddr <fd> <addr> <size>
ddw <fd> <addr> <size>
```

Use descriptor commands to confirm files, pipes, sockets, and terminal routing.
Prefer `rarun2` for baseline reproduction. Treat descriptor mutation as invasive
because some `dd` operations inject code or otherwise alter target state.

## Reverse Debugging

Native reverse debugging records states and replays from saved points. Use it
for short crash windows, not full-program time travel.

Commands:

```text
dts+
dts
dtsC 0 before-copy
dsb
dcb
dtst records_for_test
dtsf records_for_test
```

Use cases:

- Save state before a decode loop, copy, free, branch, or indirect call.
- Step forward to the crash, then backward toward the corrupting instruction.
- Comment records with `dtsC` so the trail remains readable.

Limitations:

- External I/O, threads, timers, and signals can make replay misleading.
- Backend support varies.
- ESIL reverse stepping uses `aets+` and `aesb`, covered in the ESIL reference.

## Visual Debugging

Enter visual debugger mode:

```text
Vpp
```

Useful keys:

- `p` and `P`: rotate print modes.
- `F7` or `s`: step into.
- `F8` or `S`: step over.
- `F2`: set breakpoint.
- `c`: cursor mode for byte-range selection.

Visual mode is good for manual inspection. For reportable evidence, still
capture textual state with `dr`, `drr`, `dbt`, `pd`, `px`, `dm`, and `dmj`.

## Remote Debugging

### GDB Remote

Connect:

```text
r2 -d gdb://<host>:<port>
r2 -D gdb gdb://<host>:<port>
r2 -d gdb://<host>:<port>/<pid>
```

Reopen through gdb after static analysis:

```text
doof gdb://<host>:<port>/<pid>
```

Load symbols from a local binary:

```text
r2 -e dbg.exe.path=<path> -d gdb://<host>:<port>
```

Set a base address if symbols load at the wrong base:

```text
r2 -e bin.baddr=<baddr> -e dbg.exe.path=<path> -d gdb://<host>:<port>
```

GDB IO plugin commands:

```text
:?
:pktsz
:pktsz 512
:monitor help
:detach
```

Remote workflow:

- Keep a local copy of the exact binary and relevant libraries.
- Record architecture, bitness, endianness, base address, and backend.
- Use normal `db`, `dc`, `dr`, `drr`, `dbt`, `dm`, `pd`, and `px` after connect.
- Capture backend-specific monitor or packet commands when they matter.

### WinDbg KD

Use `winkd://` for Windows kernel debugging in a VM or lab. The book describes
this support as work in progress, so validate backend behavior before relying on
it for final evidence.

Examples:

```text
r2 -a x86 -b 32 -D winkd winkd:///tmp/winkd.pipe
radare2 -D winkd winkd://\\.\pipe\com_1
r2 -a x86 -b 32 -d winkd://<hostip>:<port>:w.x.y.z
```

Record VM type, transport, guest architecture, bitness, boot debug settings, and
any backend limitations.

## Vulnerability Research Patterns

### Crash Triage

```text
r2 -r run.rr2 -d ./target
dc
dr
drr
dbt
pd 12 @ rip
px 128 @ rsp
dm. @ rip
dmj
```

Decide whether the crash is:

- Program-counter or control-flow corruption.
- Input-derived invalid read or write.
- Stack, heap, or object corruption.
- Expected abort after validation.
- Library crash caused by target-controlled arguments.

### Parser Boundary Check

```text
db sym.parser
dcu sym.parser
dr
drr
pd 20 @ rip
db <copy-or-branch-site>
dc
dr
px 64 @ <src>
px 64 @ <dst>
```

Look for signedness bugs, integer wrap, trusted input lengths, unchecked offsets,
and destination sizes smaller than copy lengths.

### Import Sink Inspection

```text
db sym.imp.memcpy
db sym.imp.strcpy
db sym.imp.printf
dc
dr
drr
dbt
ps @ rdi
px 64 @ rsi
?v rdx
```

Adjust registers for the target ABI. Capture caller, argument values, pointed-to
memory, and input derivation.

### Heap Lifetime Bug

```text
db sym.imp.malloc
db sym.imp.free
dc
dr
dbt
drr
dmh
dmhc @ <chunk>
px 128 @ <chunk>
```

Look for double free, use after free, stale aliases, overwritten metadata, or
reallocation of a chunk still reachable through an old pointer.

### Indirect Call or Vtable Control

```text
db <indirect-call-site>
dc
pd 8 @ rip
dr
drr
px 64 @ <object-or-vtable>
dm. @ <target-pointer>
```

Check whether the target pointer comes from attacker-controlled input, a freed
object, writable memory, or an out-of-bounds table lookup.

### Runtime Unpacking or Code Generation

```text
dm
db sym.imp.mmap
db sym.imp.VirtualAlloc
db sym.imp.mprotect
dc
dm
dm. @ rip
px 128 @ rip
dmd unpacked.bin
```

Look for new executable maps, writable-to-executable transitions, code executing
from heap or anonymous memory, and import patching before transfer.

## Evidence Checklist

Collect:

- Target path, hash, architecture, bitness, format, and version.
- Command line, `rarun2` profile, environment, ASLR state, working directory,
  input file, timeout, and network setup if any.
- Spawn or attach details, backend, PID, breakpoints, and runtime maps.
- Reproducer input and shortest command sequence to reach the state.
- Signal or exception, `PC`, faulting instruction, registers, `drr`, stack bytes,
  and `dm. @ PC`.
- Backtrace plus target-owned caller or callsite validation.
- Source and destination buffers, heap chunks, object/vtable memory, and map
  permissions relevant to the finding.
- Input offset to runtime value mapping when claiming control.
- Any state mutations: register writes, page-permission changes, descriptor
  manipulation, memory writes, restored snapshots, or skipped signals.
- Limitations: nondeterminism, threads, missing symbols, corrupted backtraces, or
  backend gaps.

Prefer JSON-friendly outputs for scripts:

```text
ij
dmj
dkj
aflj
```

Pair them with human-readable excerpts:

```text
pd 12 @ rip
px 128 @ rsp
drr
dbt
```

## Cautions

- `-d` may stop in the loader before entrypoint. Use `dbg.bep` or `dcu`.
- Code may run before `main`, including constructors and TLS callbacks.
- ASLR requires runtime maps for address claims.
- Remote GDB symbols may require `dbg.exe.path` and `bin.baddr`.
- Backtraces can be wrong after stack corruption.
- Heap helpers depend on allocator and platform support.
- Descriptor commands can mutate target state or inject code.
- `dmp` changes page permissions and can change exploitability conditions.
- Signal skipping can hide the real crash.
- Threads, timers, signals, and I/O can make reverse debugging unreliable.
- Anti-debug behavior may produce debugger-only results.

## Official References

- https://book.rada.re/debugger/intro.html
- https://book.rada.re/debugger/getting_started.html
- https://book.rada.re/first_steps/basic_debugger_session.html
- https://book.rada.re/debugger/registers.html
- https://book.rada.re/debugger/memory_maps.html
- https://book.rada.re/debugger/heap.html
- https://book.rada.re/debugger/signals.html
- https://book.rada.re/debugger/files.html
- https://book.rada.re/debugger/revdebug.html
- https://book.rada.re/debugger/remoting_capabilities.html
- https://book.rada.re/debugger/remote_gdb.html
- https://book.rada.re/debugger/windbg.html
- https://book.rada.re/tools/rarun2/intro.html
