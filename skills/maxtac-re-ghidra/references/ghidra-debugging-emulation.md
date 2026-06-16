# Ghidra Debugging and Emulation

Use this reference when Ghidra is used for runtime traces, debugger integration,
Trace RMI, logical breakpoints, p-code emulation, or static-program emulation.
Ghidra's debugger is a trace-oriented front-end over backend debuggers and
agents. It is powerful for correlating static and dynamic facts, but it does not
replace backend-specific debugger expertise.

## Contents

- [Quick Surfaces](#quick-surfaces)
- [Debugger Architecture](#debugger-architecture)
- [Backend Agents](#backend-agents)
- [Trace RMI](#trace-rmi)
- [Remote Targets](#remote-targets)
- [Mapping Static and Dynamic State](#mapping-static-and-dynamic-state)
- [Breakpoints](#breakpoints)
- [Trace Evidence](#trace-evidence)
- [P-code Emulation](#p-code-emulation)
- [Program Image Emulation](#program-image-emulation)
- [System Emulation and Userops](#system-emulation-and-userops)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Surfaces

Relevant upstream modules:

```text
Ghidra/Debug/Debugger
Ghidra/Debug/Debugger-agent-gdb
Ghidra/Debug/Debugger-agent-lldb
Ghidra/Debug/Debugger-agent-dbgeng
Ghidra/Debug/Debugger-agent-x64dbg
Ghidra/Debug/Debugger-agent-drgn
Ghidra/Debug/Debugger-rmi-trace
Ghidra/Debug/Framework-TraceModeling
Ghidra/Features/SystemEmulation
Ghidra/Framework/Emulation
```

Launcher directories:

```text
Ghidra/Debug/Debugger-agent-*/data/debugger-launchers/
```

Useful scripts:

```text
ConnectTraceRmiScript.java
ListenTraceRmiScript.java
DemoDebuggerScript.java
RefreshRegistersScript.java
ComputeUnwindInfoScript.java
DebuggerEmuExampleScript.java
StandAloneEmuExampleScript.java
StandAloneSyscallEmuExampleScript.java
StandAloneStructuredSleighScript.java
```

## Debugger Architecture

Ghidra's debugger stores runtime state in traces. A trace can include:

- Snapshots over time.
- Threads.
- Registers.
- Memory regions and bytes.
- Modules and sections.
- Breakpoints.
- Stack frames.
- Dynamic symbols and mappings.

The static listing and decompiler are separate from the dynamic trace, but they
can be mapped together. Evidence should name which side a fact came from:

- Static program database.
- Dynamic trace snapshot.
- Emulator scratch state.
- Backend debugger output.

## Backend Agents

Upstream includes agents for multiple backends:

- GDB.
- LLDB.
- dbgeng.
- x64dbg.
- drgn.
- Java/JDI-related debugger support.

Agent availability depends on platform, installed debugger, Python packages,
and Ghidra release packaging. Use the launchers bundled with the installation
before writing custom bridge glue.

For remote Trace RMI workflows, agent Python packages may need to be installed
on the target side. Upstream courseware references packages such as:

```text
ghidratrace
ghidragdb
ghidralldb
```

Search the Ghidra installation for `.whl` files under debugger module package
directories, or build them from source when necessary.

## Trace RMI

Trace RMI connects external debugger agents to Ghidra. Two common modes:

- Ghidra listens, target-side debugger connects.
- Ghidra launches an agent/debugger and coordinates connection.

Manual GDB Trace RMI shape:

```gdb
python import ghidragdb
file ./target
ghidra trace connect 127.0.0.1:12345
ghidra trace start
ghidra trace sync-enable
starti
```

Use Trace RMI when the debugger must live beside the target, such as remote
Linux, constrained targets, containers, or workflows where Ghidra cannot run in
the target environment.

Security note: treat Trace RMI listeners and debugger agents as high-trust
interfaces. Bind to loopback or controlled networks unless remote access is
explicitly required.

## Remote Targets

Upstream debugger courseware calls out a key caveat: many conveniences assume
the target is running from the same filesystem as Ghidra. For remote targets,
populate the project with programs imported from the target filesystem and
redirect imports to remote paths when prompted.

Common configurations:

- Local Ghidra plus local GDB connecting to remote `gdbserver`.
- Local Ghidra plus remote GDB connecting through Trace RMI over SSH.
- Manual `gdbserver` plus Ghidra remote GDB launcher.
- Manual Trace RMI acceptor plus target-side debugger commands.

Record:

- Where Ghidra runs.
- Where backend debugger runs.
- Where target process runs.
- How files/modules are mapped.
- SSH tunnels, ports, and listeners.
- Exact target binary path on the target.

## Mapping Static and Dynamic State

Static/dynamic mapping is central to useful Ghidra debugging.

Check:

- Module base in trace.
- Static program image base.
- Section mappings.
- ASLR state.
- Symbol/source of imported program.
- Whether Ghidra auto-mapped or you manually mapped.

Bad mappings create misleading decompiler/listing synchronization. Before
using a dynamic PC/register/memory fact in a report, confirm that the trace
address maps to the expected static program and bytes.

## Breakpoints

Ghidra exposes logical breakpoints that can relate static locations to dynamic
target breakpoints. Backends still enforce the actual breakpoint behavior.

Evidence should distinguish:

- Static breakpoint location.
- Dynamic mapped address.
- Backend breakpoint ID/output.
- Whether breakpoint was enabled in target, emulator, or trace.
- Hit snapshot/time.

For exploitability work, backend logs or trace snapshots should support claims
about actual execution, not just static breakpoint placement.

## Trace Evidence

Capture:

- Trace file or exported trace artifact when shareable.
- Snapshot/time of important events.
- Register state.
- Memory bytes around PC, SP, inputs, buffers, and sinks.
- Module map and address translation.
- Stack frames.
- Breakpoint hits.
- Backend command transcript.
- Target stdout/stderr.
- Input files and environment.

If only screenshots are available, also export raw addresses/registers in text.

## P-code Emulation

Ghidra's emulator uses p-code, the same intermediate semantics used by the
decompiler. The debugger UI exposes Control modes:

- Control Target.
- Control Trace.
- Control Emulator.

Use Control Emulator to extrapolate from a live target snapshot without letting
the target execute. This is useful for:

- Trying patches.
- Forcing a branch.
- Testing argument values.
- Inspecting a few instructions or one function.
- Understanding decompiler p-code behavior.

Schedules encode a snapshot plus emulated steps and patches. Examples:

```text
3
3:10
3:t1-10
3:10.4
3:{RAX=0x1234};10
```

Record schedules when emulator state matters. Thread IDs in schedules are
internal to the trace and may not equal OS thread IDs.

## Program Image Emulation

Ghidra can emulate a static program image without a live backend. This works
best when the imported image contains enough code, relocations, stack setup, and
environment state for the slice being tested.

Good uses:

- Short function-level experiments.
- Firmware routines with self-contained state.
- Branch/path exploration.
- P-code semantics debugging.

Weak uses:

- Whole desktop/userland programs needing OS services.
- Code relying on dynamic loader behavior not represented in the program DB.
- External library calls through the `EXTERNAL` block.
- Hardware/device interactions without modeling.

Initialize required state explicitly: parameters, stack, memory regions, return
address, globals, MMIO stubs, and userops.

## System Emulation and Userops

Upstream SystemEmulation includes examples and syscall/userop support classes:

```text
DebuggerEmuExampleScript.java
DemoPcodeUseropLibrary.java
DemoSyscallLibrary.java
StandAloneEmuExampleScript.java
StandAloneSyscallEmuExampleScript.java
EmuLinuxAmd64SyscallUseropLibrary
EmuLinuxX86SyscallUseropLibrary
StructuredSleigh
```

Use these patterns when p-code emulation fails because of:

- Unimplemented userops.
- Syscalls.
- External calls.
- Memory-mapped devices.
- Missing heap/filesystem/process state.

If the emulator halts on unimplemented semantics, report that as a modeling gap.
Do not convert an emulator failure directly into a target crash claim.

## Failure Modes

Backend Python package missing

Install or build the relevant agent package and dependencies for the Python
version embedded in the backend debugger, not merely the system `python3`.

Remote mapping wrong

Import target-side binaries and map modules to those project files. Local paths
with the same filename can be wrong.

Trace connects but no sync

Check Trace RMI connection, `trace start`, `sync-enable`, target state, and
backend agent command output.

Emulator reaches `EXTERNAL` block

The static image called an external function. Step back, stub it, model it, or
switch to live debugging.

Unimplemented userop

Processor p-code or environment modeling is incomplete. Add/stub userops only
if the model is within scope and record the stub behavior.

Decompiler and dynamic state disagree

Check mapping, stale decompiler cache, wrong compiler spec, modified trace
state, and whether dynamic bytes differ from static bytes.

## Evidence Checklist

Capture:

- Ghidra/debugger agent version and backend debugger version.
- Target path, hash, command line, environment, ASLR state, and input.
- Local/remote topology and ports/tunnels.
- Trace RMI connection method.
- Static program to dynamic module mappings.
- Breakpoint locations and backend IDs.
- Snapshot/time, registers, stack, memory, modules.
- Emulator control mode and schedule if emulation was used.
- Patches applied to target, trace, or emulator.
- Userop/syscall stubs or modeling assumptions.
- Backend transcript and trace artifacts.

## Official Source Paths

- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/GhidraDocs/GhidraClass/Debugger/README.md
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/GhidraDocs/GhidraClass/Debugger/B1-RemoteTargets.md
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/GhidraDocs/GhidraClass/Debugger/B2-Emulation.md
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Debug/Debugger-agent-gdb/README.md
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Debug/Debugger-rmi-trace/ghidra_scripts/ListenTraceRmiScript.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/SystemEmulation/ghidra_scripts/StandAloneEmuExampleScript.java
