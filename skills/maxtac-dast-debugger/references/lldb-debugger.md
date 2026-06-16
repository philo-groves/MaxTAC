# LLDB Debugger

Use LLDB for native runtime debugging, especially macOS, iOS, Objective-C,
Swift, C, C++, and LLVM/Clang-built targets. Prefer the installed `help`
output for exact option spelling because LLDB command support varies by build,
platform plugin, and Xcode or LLVM release.

Treat LLDB as mutable execution. It can change process state through
expressions, register writes, memory writes, signal delivery, breakpoint
commands, and launch settings. Keep final evidence separate from observations
that only happen because the debugger changed timing, ASLR, permissions, or
target state.

## Contents

- [Quick Commands](#quick-commands)
- [Command Model](#command-model)
- [Toolchain and Session Setup](#toolchain-and-session-setup)
- [Launch, Attach, and Core Files](#launch-attach-and-core-files)
- [Runtime Settings](#runtime-settings)
- [Breakpoints and Stop Hooks](#breakpoints-and-stop-hooks)
- [Watchpoints](#watchpoints)
- [Process, Thread, and Frame Control](#process-thread-and-frame-control)
- [Registers and Instruction State](#registers-and-instruction-state)
- [Memory and Regions](#memory-and-regions)
- [Images, Symbols, and Source Paths](#images-symbols-and-source-paths)
- [Variables and Expressions](#variables-and-expressions)
- [macOS and iOS Notes](#macos-and-ios-notes)
- [Remote Debugging](#remote-debugging)
- [Automation and Scripting](#automation-and-scripting)
- [Agent Control](#agent-control)
- [Evidence Automation](#evidence-automation)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Toolchain sanity:

```text
lldb --version
lldb --help
lldb -x --version
xcrun --find lldb
xcrun lldb --version
```

Start, attach, or inspect a core:

```text
lldb -x -- ./target arg1 arg2
lldb -x ./target
lldb -x -p "$PID"
lldb -x -n "$PROCESS_NAME" -w
lldb -x -c ./corefile
```

Inside LLDB:

```text
help
apropos memory
version
settings list
settings show target.run-args
file ./target
run arg1 arg2
process launch --stop-at-entry -- arg1 arg2
process launch -E DEBUG=1 -- arg1 arg2
process attach --pid "$PID"
process attach --name "$PROCESS_NAME" --waitfor
process status
process interrupt
process continue
process detach
process kill
```

Crash triage after a stop:

```text
thread list
thread backtrace all
frame info
frame variable
register read
disassemble --frame --mixed
disassemble --frame --bytes
memory region --all
memory read --format x --size 8 --count 16 $sp
image list
image lookup --address $pc
```

Batch crash capture:

```text
lldb -b -x -- ./target input.bin \
  -o "settings set interpreter.save-transcript true" \
  -o "run" \
  -k "thread backtrace all" \
  -k "register read" \
  -k "memory region --all" \
  -k "image list"
```

## Command Model

LLDB commands usually follow:

```text
<noun> <verb> [-options [option-value]] [argument [argument...]]
```

Use full commands in documentation and automation. Short forms such as
`br s -n main`, `bt`, `c`, `n`, and `si` are useful interactively, but full
forms are clearer in evidence.

Important parser rules:

- Use `--` to end LLDB options before passing target arguments or raw
  expressions that begin with `-`.
- Use backticks to evaluate a scalar expression and pass the result to another
  command, such as `memory read -c \`len\` 0x12345`.
- Use `help <command>` on the installed debugger before scripting advanced
  options.
- Use `apropos <keyword>` when the exact command name is unknown.
- Use `-x` or `--no-lldbinit` for reproducible sessions that must not load
  user startup commands.

## Toolchain and Session Setup

Record the exact debugger:

```text
lldb --version
lldb --python-path
```

On Apple hosts, prefer the LLDB selected by the active Xcode:

```text
xcode-select --print-path
xcodebuild -version
xcrun --find lldb
xcrun lldb --version
```

Start LLDB without local init files when reproducibility matters:

```text
lldb -x -- ./target arg1 arg2
```

Enable transcript capture early:

```text
settings set interpreter.save-transcript true
settings set interpreter.save-session-on-quit true
settings set interpreter.save-session-directory ./lldb-transcripts
```

Use `help` to verify transcript commands on the installed build. LLDB's
interpreter transcript settings are versioned behavior, not a target property.

## Launch, Attach, and Core Files

Launch with arguments:

```text
lldb -x -- ./target arg1 arg2
(lldb) run
```

Or set arguments inside the session:

```text
file ./target
settings set target.run-args arg1 arg2
settings show target.run-args
run
```

Launch with environment:

```text
process launch -E FEATURE_FLAG=1 -- arg1 arg2
settings set target.env-vars FEATURE_FLAG=1
settings remove target.env-vars FEATURE_FLAG
```

Stop before target code:

```text
process launch --stop-at-entry -- arg1 arg2
```

Attach:

```text
process attach --pid "$PID"
process attach --name "$PROCESS_NAME"
process attach --name "$PROCESS_NAME" --waitfor
```

Inspect core files:

```text
lldb -x -c ./corefile
thread backtrace all
register read
image list
```

Save a live process core when supported:

```text
process save-core ./core.$PID
```

Record whether the evidence came from a fresh launch, attach, wait-for attach,
or core file. Launch and attach paths can differ because launch settings,
environment, stdio, ASLR, parent process, sandbox, and permissions can differ.

## Runtime Settings

Use settings to make launches deterministic:

```text
settings show target.run-args
settings set target.run-args arg1 arg2
settings set target.input-path ./stdin.bin
settings set target.output-path ./stdout.log
settings set target.error-path ./stderr.log
settings set target.launch-working-dir /tmp/repro
settings set target.env-vars KEY=VALUE
settings set target.inherit-env false
```

Check ASLR and debugger launch behavior:

```text
settings show target.disable-aslr
settings set target.disable-aslr false
settings show target.process.stop-on-exec
settings show target.process.stop-on-sharedlibrary-events
```

For GUI or service-like programs that should not share the LLDB terminal:

```text
settings show target.disable-stdio
settings set target.disable-stdio true
process launch --no-stdio -- arg1 arg2
```

Record every setting that changes target execution. `target.disable-aslr`,
environment inheritance, stdio routing, source maps, and process plugin
settings can explain debugger-only differences.

## Breakpoints and Stop Hooks

Set common breakpoints:

```text
breakpoint set --name main
breakpoint set --file parser.c --line 120
breakpoint set --address 0x100003f20
breakpoint set --method parse
breakpoint set --selector application:openURL:options:
breakpoint set --shlib libtarget.dylib --name target_function
breakpoint set --func-regex '^parse_'
```

Manage them:

```text
breakpoint list
breakpoint list --full
breakpoint disable 1
breakpoint enable 1
breakpoint delete 1
```

Set conditions:

```text
breakpoint set --name parse --condition 'len > 4096'
breakpoint modify 1 --condition 'ptr == 0'
```

Add breakpoint commands for evidence:

```text
breakpoint command add 1
> thread backtrace
> register read
> disassemble --frame
> DONE
```

Use a target stop hook for repeated capture at every stop:

```text
target stop-hook add
> thread backtrace
> disassemble --pc
> DONE
```

Or as a one-liner:

```text
target stop-hook add --one-liner "thread backtrace"
target stop-hook add --one-liner "frame variable"
```

LLDB creates logical breakpoints that may resolve to zero, one, or many
locations. Always check `breakpoint list --full`; unresolved or pending
breakpoints are common when modules load later, symbols are missing, or the
wrong image was selected.

## Watchpoints

Use watchpoints for concrete data mutation questions:

```text
watchpoint set variable global_var
watchpoint set expression -- my_ptr
watchpoint modify -c '(global_var == 5)'
watchpoint list
watchpoint delete 1
```

Hardware watchpoint capacity is limited and platform dependent. If LLDB cannot
set the requested watchpoint, narrow the watched address and size, or fall back
to breakpoints around the suspected writes.

Capture on watchpoint stop:

```text
thread backtrace all
frame info
register read
memory region --all
memory read --format x --size 8 --count 16 $sp
```

## Process, Thread, and Frame Control

Control execution:

```text
process continue
process interrupt
thread step-in
thread step-over
thread step-inst
thread step-inst-over
thread step-out
thread until 120
thread return
```

Inspect threads and frames:

```text
thread list
thread select 2
thread backtrace
thread backtrace all
thread backtrace -c 5
frame select 0
frame info
up
down
```

Step filters:

```text
settings show target.process.thread.step-avoid-regexp
settings set target.process.thread.step-avoid-regexp '^std::|^objc_'
```

`thread return`, expression calls, register writes, and skipped instructions
are invasive. Use them for experiments, not as the sole basis for final target
behavior.

## Registers and Instruction State

Read and write registers:

```text
register read
register read pc
register read sp
register read --format x
register read/d
register write rax 123
register write pc `$pc+8`
```

Disassemble:

```text
disassemble --frame
disassemble --frame --mixed
disassemble --frame --bytes
disassemble --name main
disassemble --start-address 0x100003f20 --count 20
disassemble --start-address 0x100003f20 --end-address 0x100004020
```

For crash evidence, capture:

```text
register read
disassemble --frame --bytes
memory region --all
image lookup --address $pc
thread backtrace all
```

Use architecture-neutral names such as `pc` and `sp` when possible in notes.
Also record the concrete architecture because register names, calling
conventions, pointer authentication, and exception details are platform
specific.

## Memory and Regions

Read memory:

```text
memory read $sp
memory read --format x --size 1 --count 64 "$ADDR"
memory read --format x --size 8 --count 16 "$ADDR"
memory read --outfile ./mem.txt --count 512 "$ADDR"
memory read --outfile ./mem.bin --binary "$START" "$END"
```

Use GDB-style aliases when faster interactively:

```text
x/32bx "$ADDR"
x/16gx $sp
```

Inspect mappings:

```text
memory region "$ADDR"
memory region --all
```

Memory writes are state-changing. If used, isolate them as experiments, record
the exact command, and rerun without them before making target-behavior claims:

```text
help memory write
memory write --help
```

On macOS, LLDB ships heap helper scripts on supported installations:

```text
command script import lldb.macosx.heap
process launch --environment MallocStackLogging=1 -- arg1 arg2
malloc_info --stack-history 0x10010d680
malloc_info --type 0x10010d680
ptr_refs EXPR
cstr_refs CSTRING
```

Heap helper availability and output are platform-specific. Record whether
`MallocStackLogging` or other allocator diagnostics were enabled, because they
can change allocation timing and memory layout.

## Images, Symbols, and Source Paths

List loaded images and sections:

```text
image list
image dump sections
image dump symtab
image dump symtab ./target libtarget.dylib
```

Resolve addresses:

```text
image lookup --address 0x100003f20
image lookup -v --address 0x100003f20
image lookup --address 0x100003f20 ./target
image lookup -r -n '^parse'
image lookup -r -s '^_objc'
image lookup --type SomeType
```

Add symbols:

```text
target symbols add ./Target.dSYM
add-dsym ./Target.dSYM
settings set target.debug-file-search-paths ./symbols
```

Remap source paths when debug info was produced elsewhere:

```text
settings set target.source-map /buildbot/path /local/source/path
settings show target.source-map
```

For Apple crash or core analysis, record UUIDs from `image list` and match them
to the executable, dylibs, frameworks, and dSYM bundles used for symbolication.

## Variables and Expressions

Inspect frame variables without running target code:

```text
frame variable
frame variable argc argv
frame variable some_struct.field
frame variable -o self
target variable global_name
parray 10 ptr
```

Evaluate expressions:

```text
expr -- len
expr -- (int)strcmp(a, b)
print -- value
po object
expr -d no-run-target -- someCPPObjectPtr
```

Expression evaluation can call target code:

```text
expr -i 0 -- function_with_a_breakpoint()
expr -u 0 -- function_which_crashes()
```

Use expressions deliberately. They may allocate memory, call functions, acquire
locks, trigger breakpoints, change errno or thread-local state, or crash the
process. Prefer `frame variable`, `register read`, `memory read`, and
`image lookup` when passive observation is enough.

## macOS and iOS Notes

On macOS, use the LLDB selected by Xcode when debugging Apple-platform targets:

```text
xcrun --find lldb
xcrun lldb --version
xcrun lldb -x -- ./Target.app/Contents/MacOS/Target
```

For apps, record:

- Xcode version and selected developer directory.
- Target path and signing/provisioning context when relevant.
- Whether the target was launched by LLDB, Xcode, Finder, `open`, a service, or
  a harness.
- `target.disable-aslr`, environment, stdio, and working directory settings.
- dSYM paths and UUID matches from `image list`.

For iOS, use the `xcrun` reference for device discovery, install, launch, and
CoreDevice tunnel setup. LLDB is the debugger side of the attach; it is not the
device-management tool.

Useful iOS-side handoff pattern after `xcrun devicectl` setup:

```text
xcrun devicectl device process launch --device "$UDID" --start-stopped "$BUNDLE_ID"
xcrun devicectl device info processes --device "$UDID"
lldb
(lldb) gdb-remote "$DEBUGPROXY_HOST:$DEBUGPROXY_PORT"
(lldb) process attach --pid "$PID"
```

If attach fails on Apple platforms, preserve the failure output and host/device
state. Do not reinterpret a debugger attach denial as target application
behavior.

## Remote Debugging

LLDB remote debugging uses a client/server model with the gdb-remote protocol.
For Linux and many non-Apple targets, deploy `lldb-server` on the remote side.
For macOS and iOS, the remote stub is typically `debugserver` through Apple
tooling.

Platform-server mode:

```text
# remote
lldb-server platform --listen "*:1234" --server

# local
lldb
(lldb) platform list
(lldb) platform select remote-linux
(lldb) platform connect connect://remote:1234
(lldb) platform status
(lldb) file ./target
(lldb) run
```

Direct gdbserver mode:

```text
# remote
lldb-server gdbserver :1234 -- ./target arg1 arg2

# local
lldb ./target
(lldb) gdb-remote remote:1234
```

Attach through `lldb-server`:

```text
# remote
lldb-server gdbserver :1234 --attach "$PID"

# local
lldb ./target
(lldb) gdb-remote remote:1234
```

Remote platform helpers:

```text
platform process list
platform put-file ./seed.bin /tmp/seed.bin
platform get-file /tmp/out.bin ./out.bin
platform shell uname -a
platform settings -w /tmp
platform status
```

Remote evidence must record the local LLDB version, remote `lldb-server` or
`debugserver` version/path, platform plugin, architecture triple, connection
address, working directory, uploaded files, and whether the executable or
libraries were copied automatically.

Bind remote debug servers only on the intended lab interface. Prefer loopback
or a controlled network segment for repeatable work.

## Automation and Scripting

Use batch mode for repeatable one-shot sessions:

```text
lldb -b -x -- ./target input.bin \
  -o "settings set target.input-path ./stdin.bin" \
  -o "breakpoint set --name main" \
  -o "run" \
  -o "thread backtrace all" \
  -o "quit"
```

Use command files when the command list gets long:

```text
lldb -b -x -s ./commands.lldb -- ./target arg1 arg2
```

Example `commands.lldb`:

```text
settings set interpreter.save-transcript true
settings set target.input-path ./stdin.bin
breakpoint set --name main
run
thread backtrace all
register read
memory region --all
quit
```

Python inside LLDB:

```text
script
script import lldb
command script import ./lldb_helpers.py
breakpoint command add -s python 1
```

Standalone Python:

```text
lldb --python-path
python3 ./drive_lldb.py
```

Prefer LLDB command files for simple evidence capture. Use Python when the
workflow needs structured parsing, conditional breakpoint behavior, or repeated
state extraction across many stops.

## Agent Control

Recent LLDB builds include a Model Context Protocol server:

```text
protocol-server start MCP listen://localhost:59999
```

Use it only on a local or otherwise trusted interface. Treat agent-driven LLDB
sessions like scripted debugging: record the command stream, transcript, target
state, and every state-changing operation.

## Evidence Automation

Create a run directory:

```text
RUN_DIR="evidence/$(date +%Y%m%d-%H%M%S)-lldb"
mkdir -p "$RUN_DIR"
lldb --version > "$RUN_DIR/lldb-version.txt"
```

Create `triage.lldb`:

```text
settings set interpreter.save-transcript true
settings set interpreter.save-session-on-quit true
settings set interpreter.save-session-directory ./evidence
settings show target.disable-aslr
settings show target.run-args
settings show target.env-vars
run
process status
thread list
thread backtrace all
frame info
frame variable
register read
disassemble --frame --bytes
memory region --all
image list
```

Run it:

```text
lldb -b -x -s ./triage.lldb -- ./target "$INPUT" > "$RUN_DIR/lldb.log" 2>&1
```

For a crashing target, add crash-only commands:

```text
lldb -b -x -- ./target "$INPUT" \
  -o "run" \
  -k "thread backtrace all" \
  -k "register read" \
  -k "disassemble --frame --bytes" \
  -k "memory region --all" \
  -k "image list" \
  > "$RUN_DIR/lldb-crash.log" 2>&1
```

If the process is still live and the platform supports it:

```text
process save-core "$RUN_DIR/core"
```

Record command files next to logs so another researcher can replay the same
debugger actions.

## Failure Modes

`lldb: command not found`

- Use the LLVM toolchain path or `xcrun --find lldb` on macOS.
- Record whether the LLDB comes from Xcode, Command Line Tools, LLVM packages,
  or a distro package.

Unexpected aliases, startup commands, or prompt behavior

- Rerun with `lldb -x`.
- Inspect `~/.lldbinit` only if local policy allows using user init files.

Breakpoint stays pending

- Check `breakpoint list --full`.
- Confirm symbols and source paths.
- Confirm the target module is loaded.
- Use `breakpoint set --shlib ...` or an address breakpoint when needed.

Attach denied or process disappears

- Preserve the exact attach error.
- Confirm PID/name, target owner, sandbox, signing, debugger permissions, and
  platform policy.
- On iOS, confirm Developer Mode, trust, device state, and CoreDevice tunnel in
  the `xcrun` workflow before blaming LLDB commands.

No useful variables

- The binary may be optimized, stripped, or missing debug info.
- Fall back to `register read`, `memory read`, `disassemble`, and `image lookup`.
- Add dSYM or external debug files when available.

Expression fails or changes behavior

- Confirm `target.language`, debug info, imports, and runtime state.
- Prefer `frame variable` for passive inspection.
- Remember expressions may run target code.

Addresses do not match across runs

- Capture `memory region --all` and `image list`.
- Check `settings show target.disable-aslr`.
- Do not report static addresses without runtime module bases.

Remote target launches locally by mistake

- Confirm `platform select`, `platform connect`, `platform status`, and working
  directory before `run`.
- Confirm the executable was uploaded or that platform file specs are correct.

Core file lacks expected memory

- Core dumps are platform policy and process-state dependent.
- Capture live `memory region --all` before `process save-core` when possible.
- Keep original crash reports, tombstones, or system crash logs.

## Evidence Checklist

Collect:

- LLDB version, path, Python path, and host toolchain selection.
- Target path, hash, architecture, platform, debug info state, and symbols used.
- Launch versus attach versus core-file mode.
- Exact command line, command file, LLDB transcript, and batch output.
- Target arguments, environment, stdin/stdout/stderr paths, working directory,
  ASLR setting, and stdio setting.
- PID, process status, thread list, selected thread/frame, stop reason, and
  signal or exception.
- `thread backtrace all`, `register read`, `disassemble --frame --bytes`,
  `memory region --all`, and `image list`.
- Address resolution with `image lookup --address` for faulting or important
  addresses.
- Breakpoints, watchpoints, conditions, stop hooks, and breakpoint commands.
- Any state-changing operations: expressions, function calls, register writes,
  memory writes, `thread return`, skipped instructions, signal delivery,
  process kill, or changed launch settings.
- Core file or crash report when available.
- Remote debug server details, platform plugin, connection address, uploaded
  files, and working directory for remote sessions.
- Apple-platform details: Xcode version, selected developer directory, dSYM UUID
  matches, device UDID or simulator ID when applicable, and CoreDevice/debugproxy
  endpoint when used.

## References

- https://lldb.llvm.org/
- https://lldb.llvm.org/man/lldb.html
- https://lldb.llvm.org/use/tutorial.html
- https://lldb.llvm.org/use/map.html
- https://lldb.llvm.org/use/settings.html
- https://lldb.llvm.org/use/remote.html
- https://lldb.llvm.org/man/lldb-server.html
- https://lldb.llvm.org/use/python-reference.html
- https://lldb.llvm.org/use/tutorials/script-driven-debugging.html
- https://lldb.llvm.org/use/variable.html
- https://lldb.llvm.org/use/symbols.html
- https://lldb.llvm.org/use/mcp.html
- https://developer.apple.com/library/archive/documentation/General/Conceptual/lldb-guide/chapters/Introduction.html
- https://developer.apple.com/library/archive/documentation/General/Conceptual/lldb-guide/chapters/C2-Understanding-LLDB-Command-Syntax.html
- https://developer.apple.com/library/archive/documentation/IDEs/Conceptual/gdb_to_lldb_transition_guide/document/lldb-terminal-workflow-tutorial.html
