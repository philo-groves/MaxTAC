# Radare2 ESIL Emulation

Use ESIL when static disassembly is not enough and a small amount of execution
semantics can answer a vulnerability-research question. ESIL is best for short
instruction windows, computed references, branch likelihood, unpacking or
decode loops, syscall/import modeling, and exploitability probes. Treat it as
partial and imprecise emulation, not as a replacement for native debugging,
full-system emulation, or proof on the real target.

## Contents

- [Quick Commands](#quick-commands)
- [What ESIL Is](#what-esil-is)
- [View ESIL and Emulation Comments](#view-esil-and-emulation-comments)
- [Manual ESIL Setup](#manual-esil-setup)
- [Stepping and State](#stepping-and-state)
- [Computed Analysis](#computed-analysis)
- [Searching with ESIL](#searching-with-esil)
- [Pins for Imports and Helpers](#pins-for-imports-and-helpers)
- [Traps and Memory Protections](#traps-and-memory-protections)
- [ESIL Debug Backend](#esil-debug-backend)
- [Vulnerability Research Use Cases](#vulnerability-research-use-cases)
- [Limitations and Failure Modes](#limitations-and-failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [Official References](#official-references)

## Quick Commands

Inspect ESIL for current code:

```text
ao~esil
aoj
e asm.esil=true
pdf @ sym.func
e asm.esil=false
```

Show lightweight emulation comments in disassembly:

```text
e asm.emu=true
e emu.str=true
pdf @ sym.func
```

Initialize and step manually:

```text
aei                 initialize ESIL VM
aeim                initialize ESIL VM memory and stack
aeip                set ESIL instruction pointer to current seek
aer                 show ESIL registers
aer rip=0x401000    set register value, name depends on architecture
aes                 step one instruction
10aes               step ten instructions
aeso                step over
aesu 0x401050       step until address
aesue <expr>        step until ESIL expression is met
aec                 continue until break or limit
```

Safety and bounded execution:

```text
e esil.maxsteps=1000
e esil.timeout=5
e esil.iotrap=true
e esil.exectrap=true
e cmd.esil.trap='?e ESIL trap'
```

Computed references and search:

```text
aae                 ESIL-assisted analysis
aaaa                deeper analysis that may include ESIL stages
/re <addr-or-flag>  find computed pointer references
/ce rsp,rbp         search ESIL expressions matching text
/E <expr>           search offsets matching an ESIL expression
```

## What ESIL Is

ESIL is radare2's "Evaluable Strings Intermediate Language." It represents
instruction semantics as comma-separated, stack-machine expressions. For
example, a `push ebp` style operation can be represented as stack-pointer
arithmetic plus a memory write.

Important mental model:

- ESIL expressions describe instruction effects.
- `ao` and `aoj` expose instruction metadata, including ESIL where available.
- `ae` evaluates an ESIL expression directly.
- `aes` and related commands step target instructions using the ESIL VM.
- ESIL can be used during analysis, during disassembly display, manually, or as
  a debugger backend.

Use ESIL for local reasoning:

- Resolve indirect branches or computed references.
- Estimate whether a conditional branch is likely.
- Track register, stack, and memory effects across a short code slice.
- Model syscalls, imports, helper functions, or stubs with pins.
- Probe whether a write, pointer calculation, or bounds check behaves as
  expected under chosen initial state.

## View ESIL and Emulation Comments

To see how a single instruction is lifted:

```text
ao
aoj
ao~esil
```

To show ESIL expressions instead of normal disassembly:

```text
e asm.esil=true
pd 10
pdf @ sym.func
e asm.esil=false
```

To show emulated register and memory effects as comments:

```text
e asm.emu=true
pdf @ sym.func
```

To reduce noise and focus on useful annotations such as strings and likely
branches:

```text
e emu.str=true
pdf @ sym.func
```

Use these display modes to understand:

- Whether an instruction has an ESIL expression at all.
- Which registers and memory locations an instruction reads or writes.
- Whether a branch is predicted as likely under the current emulation state.
- Whether a pointer resolves to a string, mapped address, or invalid region.

Toggle these settings off after the focused inspection if they make later
disassembly too noisy.

## Manual ESIL Setup

A minimal manual setup:

```text
s sym.target
aei
aeim
aeip
aer
```

Set architecture-specific registers before stepping:

```text
aer rip=0x401000
aer rsp=0x7fffffffe000
aer rdi=0x100000
aer rsi=0x200000
aer rdx=0x40
```

The register names must match the target architecture. Use:

```text
dr
aer
ar
```

Use `aeim` to create VM memory/stack. Tune stack settings before
initialization when defaults are not suitable:

```text
e esil.stack.addr=0x7fffffffe000
e esil.stack.size=0x10000
e esil.stack.depth=256
e esil.fillstack=sequence
aeim
```

When modeling a function call, seed the call ABI:

- Set argument registers or stack slots.
- Set stack pointer and return address when needed.
- Write pointed-to buffers or structs into mapped memory.
- Initialize globals, GOT entries, or table pointers used by the slice.
- Pin imports or helper functions that cannot be emulated directly.

Use small slices. Prefer stepping a parser branch, pointer calculation,
decode loop, or check/sink pair over trying to emulate the whole program.

## Stepping and State

Core stepping commands:

```text
aes                 step one instruction
10aes               step ten instructions
aeso                step over function calls
aesu 0xADDR         step until address
aesue <expr>        step until expression
aec                 continue until break, timeout, or Ctrl-C
```

State commands:

```text
aer                 show or set ESIL registers
ar                  show or modify ESIL registry in some ESIL contexts
px 64 @ <addr>      inspect bytes affected by emulation
ps @ <addr>         inspect string affected by emulation
dr                  compare debugger-like register view when applicable
```

Record and replay support:

```text
aets                list ESIL record/replay sessions
aets+               create a new session
aesb                step back in current session
```

Practical stepping pattern:

```text
s sym.parse_len
aei
aeim
aeip
aer rdi=<input-buffer>
aer rsi=<input-len>
e esil.maxsteps=200
e esil.iotrap=true
10aes
aer
px 64 @ <input-buffer>
```

Prefer `aesu` or `aesue` over open-ended `aec` when possible. Unbounded
continuation can walk into imports, syscalls, unimplemented instructions, or
path explosion.

## Computed Analysis

ESIL can participate in radare2 analysis. The `aae` command performs
ESIL-assisted analysis, and deeper `aaaa` analysis may include ESIL-related
stages.

```text
aa
aae
afl
axt @ <computed-target>
```

Useful settings:

```text
e anal.esil=true
e asm.emu=true
e emu.str=true
e emu.write=false
```

Notes:

- `anal.esil` controls ESIL participation in analysis.
- `emu.write` allows the ESIL VM to modify memory during analysis. Enable it
  only when the target requires it, such as unpacking or deobfuscation.
- `asm.emu=true` shows calculated values and likely branches as comments.
- `emu.str=true` reduces noise by showing especially useful annotations.

Use computed analysis for:

- Recovering computed pointer references.
- Improving xrefs through simple register arithmetic.
- Resolving jump table or indirect branch targets.
- Annotating likely branches and strings.
- Identifying syscalls or computed addresses that pure static analysis misses.

Do not assume ESIL-computed xrefs are complete. Verify with disassembly, search,
runtime traces, or targeted manual stepping.

## Searching with ESIL

ESIL-aware search can find semantic patterns that do not have a stable byte
sequence.

```text
/re <addr-or-flag>  find computed pointer references using ESIL
/ce rsp,rbp         search ESIL expressions matching text
/E <expr>           search offsets matching an ESIL expression
```

Use ESIL search for:

- Computed references to strings, globals, tables, vtables, or buffers.
- Instructions that modify the stack pointer or program counter.
- Candidate indirect calls and jumps.
- Memory writes whose exact instruction encoding varies across builds.
- Conditions involving flags, comparisons, or nested arithmetic.

ESIL-string quick checks:

- `[` means memory is read.
- `=[` means memory is written.
- `pc,=` or architecture-specific IP assignment means control flow changes.
- `sp,=` or stack pointer arithmetic means stack state changes.
- `$` can indicate flags, interrupts, or syscalls depending on expression.
- `TRAP` indicates an exception-like condition.
- `?{` indicates conditional execution.

These are heuristics. Confirm with `aoj`, disassembly, and local emulation
before turning a search hit into a claim.

## Pins for Imports and Helpers

ESIL pins let you hook an address and run custom radare2 commands instead of
the standard ESIL expression at that address. Use pins to model behavior that
ESIL cannot emulate directly, such as imports, syscalls, allocators, string
helpers, or platform APIs.

List pins:

```text
aep
```

Set a default command for pins:

```text
e cmd.esil.pin='?e hit ESIL pin'
```

Define and attach a pin:

```text
aep ret0='dr R0=0;aexa ret'
aep ret0 @ 0x1000
```

Remove pins:

```text
aep- 0x1000
aep-*
```

Check current-address pin:

```text
aep.
```

Pin categories:

- Soft pins use a `soft.` prefix. They are for disassembly and analysis-time
  annotations, especially with `asm.emu`.
- Hard pins do not use `soft.`. They execute during ESIL stepping and can
  modify registers, memory, and flow.

Useful pin patterns:

```text
aep ret0='dr R0=0;aexa ret'
aep log='?e reached interesting address'
aep strlen='dr R0=`pszl@r:A0`;aexa ret'
```

Architecture note: register names such as `R0`, `A0`, or return registers are
target-specific. Rewrite pins for the target ABI before relying on results.

Use pins to:

- Make external calls return deterministic success or failure.
- Simulate `memcpy`, `strlen`, allocation, or parser helpers.
- Log that a specific address or branch was reached.
- Skip anti-analysis or environment checks for a narrow local question.

Be explicit in evidence when a result depends on pinned behavior. A pin is a
model, not real execution.

## Traps and Memory Protections

Traps help detect exceptional conditions during ESIL evaluation.

Enable common traps:

```text
e esil.iotrap=true
e esil.exectrap=true
e esil.traprevert=true
e cmd.esil.trap='?e ESIL trap'
```

Trigger a simple explicit trap:

```text
ae 2,1,TRAP
```

Common trap classes include:

- Unhandled interrupt or exception.
- Breakpoint-like conditions.
- Divide by zero.
- Invalid read or write.
- Execution in non-executable memory.
- Invalid instruction or unimplemented operation.
- Unaligned access.
- Halt.

Use traps for vulnerability research:

- Catch null or unmapped pointer reads/writes while modeling a sink.
- Detect writes through attacker-influenced pointers.
- Detect attempted execution in non-executable memory during ROP/JOP modeling.
- Stop on unimplemented instructions instead of silently drifting.
- Log emulation failures during automated slices.

Trap caveats:

- A trap in ESIL is evidence about the model and current state, not proof that
  the real process will fault.
- Missing traps do not prove safety; memory maps, initial state, and unsupported
  instructions may be incomplete.
- Record trap configuration and initial register/memory state with any result.

## ESIL Debug Backend

Radare2 can use ESIL as a debugger backend:

```text
dL
dL esil
```

After selecting ESIL, many `d` commands can be used with the internal emulation
logic, such as changing registers, stepping, skipping, and setting breakpoints.

Use this mode when:

- You want debugger-like controls without launching the real process.
- The target platform cannot run locally.
- A small code slice needs breakpoint-style navigation.

Prefer native debugging, QEMU, Unicorn, Bochs, or target hardware when the proof
depends on OS behavior, memory layout, threads, signals, syscalls, loader state,
or exact exception behavior.

## Vulnerability Research Use Cases

Resolve a computed branch or table target:

```text
aa
aae
axt @ <target>
aoj @ <branch>
e asm.emu=true
pdf @ <function>
```

Check a bounds-check-to-sink slice:

```text
s sym.parse
aei
aeim
aeip
aer <arg-reg>=<input>
aer <len-reg>=0x100
e esil.iotrap=true
aesu <sink-address>
aer
px 64 @ <input>
```

Model a helper function:

```text
aep ret0='dr R0=0;aexa ret'
aep ret0 @ sym.imp.verify_signature
aei; aeim; aeip
aesu <post-check-address>
```

Inspect likely branch behavior:

```text
e asm.emu=true
e emu.str=true
pdf @ sym.check_policy
```

Probe a write-what-where candidate:

```text
aei
aeim
aeip
aer <dst-reg>=0x41410000
aer <src-reg>=0x42420000
e esil.iotrap=true
aesu <write-address>
px 32 @ 0x41410000
```

Unpack or decode a small loop:

```text
e emu.write=true
aei
aeim
aeip
e esil.maxsteps=5000
aesu <loop-exit>
px 256 @ <decoded-buffer>
e emu.write=false
```

For each use case, define the initial state, execute the smallest useful slice,
and validate the resulting state with raw bytes and normal disassembly.

## Limitations and Failure Modes

ESIL commonly fails or misleads when:

- The path space explodes.
- Stack contents or size are wrong.
- TLS, custom segments, or memory maps are missing.
- Instructions are unimplemented or modeled imprecisely.
- SIMD, vector, floating-point, or architecture-specific features matter.
- External calls, syscalls, imports, or callbacks are not pinned or modeled.
- Undefined behavior, races, signals, threads, or OS state shape execution.
- Memory writes are disabled when the slice depends on them.
- Memory writes are enabled and mutate analysis state in unexpected ways.
- The target uses anti-analysis, self-modifying code, JIT code, or packed code.

Practical guardrails:

- Keep `esil.maxsteps` and `esil.timeout` bounded.
- Enable `esil.iotrap` and `esil.exectrap` when modeling memory safety.
- Avoid broad `aaaa` or unbounded `aec` when a targeted slice answers the
  question.
- Prefer pins for known external helpers rather than stepping into unknown
  imports.
- Record all non-default `esil.*`, `emu.*`, `asm.*`, and pin settings.
- Confirm important results with a debugger or emulator that runs the real code
  path whenever impact depends on exact runtime behavior.

## Evidence Checklist

Capture:

- Binary path, hash, architecture, bitness, OS, and base address.
- ESIL setup commands: `aei`, `aeim`, `aeip`, register writes, memory writes,
  and stack settings.
- Non-default `esil.*`, `emu.*`, `asm.*`, and `anal.esil` settings.
- Search or analysis commands that used ESIL, such as `aae`, `/re`, `/ce`, or
  `/E`.
- Pins, trap handlers, and any modeled import/syscall behavior.
- Initial and final register state.
- Initial and final bytes for buffers, pointers, or memory regions involved in
  the claim.
- Disassembly and ESIL expressions around key branches, writes, indirect calls,
  and sinks.
- Whether the result was confirmed with native debugging, target emulation, or
  independent static analysis.

## Official References

- https://book.rada.re/emulation/intro.html
- https://book.rada.re/emulation/esil.html
- https://book.rada.re/emulation/pins.html
- https://book.rada.re/emulation/traps.html
- https://book.rada.re/emulation/analysis.html
