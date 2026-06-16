# Ghidra Decompiler and P-code

Use this reference when decompiler output, p-code, data-flow graphs, or
decompiler scripting are part of a binary-research answer. The decompiler is a
high-value hypothesis engine, not source recovery. Always map important
decompiler statements back to listing addresses, bytes, and p-code or runtime
state before making exploitability claims.

## Contents

- [Quick Commands and Scripts](#quick-commands-and-scripts)
- [Decompiler Mental Model](#decompiler-mental-model)
- [DecompInterface](#decompinterface)
- [FlatDecompilerAPI](#flatdecompilerapi)
- [HighFunction and P-code](#highfunction-and-p-code)
- [Raw Instruction P-code](#raw-instruction-p-code)
- [Decompiler Repair Inputs](#decompiler-repair-inputs)
- [Decompiler Problem Scripts](#decompiler-problem-scripts)
- [P-code Export and Graphs](#p-code-export-and-graphs)
- [Vulnerability Research Patterns](#vulnerability-research-patterns)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands and Scripts

Built-in scripts worth checking before writing a custom script:

```text
ShowCCallsScript.java
ShowConstantUse.java
StringParameterPropagator.java
FindPotentialDecompilerProblems.java
DecompilerStackProblemsFinderScript.java
FixSwitchStatementsWithDecompiler.java
GraphASTScript.java
GraphASTAndFlowScript.java
GraphSelectedASTScript.java
ExportPCodeForSingleFunction.java
ExportPCodeForCTADL.java
```

Minimal Java decompiler skeleton:

```java
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.Function;

DecompInterface ifc = new DecompInterface();
try {
    ifc.openProgram(currentProgram);
    DecompileResults res = ifc.decompileFunction(function, 60, monitor);
    if (!res.decompileCompleted()) {
        printerr(res.getErrorMessage());
        return;
    }
    String c = res.getDecompiledFunction().getC();
    println(c);
}
finally {
    ifc.dispose();
}
```

PyGhidra with `DecompInterface` and the current project APIs:

```python
import pyghidra

pyghidra.start()
with pyghidra.open_project("./projects", "Case001", create=False) as project:
    with pyghidra.program_context(project, "/sample.bin") as program:
        from ghidra.app.decompiler import DecompInterface

        space = program.getAddressFactory().getDefaultAddressSpace()
        addr = space.getAddress(0x401000)
        func = program.getFunctionManager().getFunctionAt(addr)

        ifc = DecompInterface()
        try:
            ifc.openProgram(program)
            res = ifc.decompileFunction(func, 60, pyghidra.task_monitor(60))
            if not res.decompileCompleted():
                raise RuntimeError(res.getErrorMessage())
            print(res.getDecompiledFunction().getC())
        finally:
            ifc.dispose()
```

## Decompiler Mental Model

Ghidra decompilation depends heavily on:

- Correct language ID and compiler spec.
- Function boundaries.
- Calling convention.
- Parameter and return types.
- Stack frame recovery.
- Data type archives and applied debug types.
- References, switch recovery, and no-return functions.
- Context registers such as ARM/Thumb mode.

When decompiler output is wrong, fix the program database first. Re-running the
decompiler without repairing functions, types, references, or stack state often
just produces a cleaner-looking wrong answer.

Decompiler output is strongest for:

- Understanding high-level branch structure.
- Finding candidate checks and sinks.
- Recovering variable roles after type repair.
- Seeing constant propagation and indirect call hints.
- Exporting p-code for programmatic analysis.

Decompiler output is weaker for:

- Precise undefined behavior.
- Volatile/MMIO semantics.
- Hand-written assembly.
- Obfuscated dispatch.
- Unmodeled syscalls/userops.
- Exact stack/register state after unusual ABI boundaries.

## DecompInterface

`DecompInterface` is the direct Java API. Use it when scripts need:

- Decompiler warnings/errors.
- `DecompileResults`.
- `DecompiledFunction.getC()`.
- `HighFunction`.
- Token trees and address mapping.
- Timeout control.

Rules:

- Call `openProgram(currentProgram)` before decompiling.
- Use a bounded timeout for batch automation.
- Check completion and error messages.
- Dispose the interface.
- Keep raw result artifacts next to summaries.

Do not parse only C text when you need addresses. Use token/address mappings or
HighFunction p-code so the evidence can be tied back to the listing.

## FlatDecompilerAPI

`FlatDecompilerAPI` is a convenience wrapper around `DecompInterface` for
scripts using `FlatProgramAPI`. It exposes:

- `decompile(Function function)`
- `decompile(Function function, int timeoutSecs)`
- `getDecompiler()`
- `dispose()`

It returns C text. Use it for quick extraction, but switch to `DecompInterface`
when you need warnings, `HighFunction`, token groups, or structured p-code.

## HighFunction and P-code

`HighFunction` is the decompiler's structured function model. It exposes
decompiler p-code operations and symbols. Use it when tracking:

- Pointer arithmetic.
- Bounds checks.
- Copy lengths.
- Format-string arguments.
- Indirect call targets.
- Data dependencies between parameters, locals, globals, and calls.

Common classes:

```text
HighFunction
HighFunctionDBUtil
PcodeOp
PcodeOpAST
Varnode
ClangToken
ClangTokenGroup
```

P-code caveats:

- Decompiled p-code is not the same as raw instruction p-code.
- Optimizations and type recovery can reshape operations.
- Missing types or wrong prototypes change p-code shape.
- User-defined p-code operations may require processor-specific handling.

Preserve:

- Function entry.
- Decompiler timeout and status.
- P-code operation sequence around the sink/check.
- Varnode definitions and uses for attacker-controlled values.
- Listing addresses for each relevant operation.

## Raw Instruction P-code

Raw instruction p-code comes from instruction semantics, before decompiler
structuring. Use it to verify exact instruction behavior or to debug processor
language issues.

Use cases:

- Compare decompiler interpretation to actual instruction semantics.
- Inspect unusual instructions.
- Debug Sleigh language behavior.
- Model branch conditions for short slices.
- Reason about emulator/userop failures.

Do not assume every processor module was designed primarily for emulation.
Ghidra's debugger courseware explicitly warns that some p-code specs were built
for decompilation first, and emulation may expose unimplemented userops or other
semantic gaps.

## Decompiler Repair Inputs

Improve decompiler output by repairing these first:

- Function start/end.
- Thunks and tail calls.
- No-return functions.
- Stack purge/stack depth.
- Parameter storage and calling convention.
- Function signatures for imports and internal helpers.
- Data types for structs, buffers, handles, messages, and vtables.
- Switch/jump table references.
- External references and library names.

High-impact scripts:

```text
StringParameterPropagator.java
FixSwitchStatementsWithDecompiler.java
RecoverClassesFromRTTIScript.java
ApplyClassFunctionSignatureUpdatesScript.java
ApplyClassFunctionDefinitionUpdatesScript.java
```

After repair, re-open or reset the decompiler interface so stale caches do not
drive the next extraction.

## Decompiler Problem Scripts

Use these scripts as triage leads, not final proof:

```text
FindPotentialDecompilerProblems.java
DecompilerStackProblemsFinderScript.java
FindUnrecoveredSwitchesScript.java
```

Common problem indicators:

- Bad stack offsets.
- Undefined or overlapping variables.
- Unrecovered switch.
- Unexpected external block call.
- Void pointer arithmetic everywhere.
- Missing parameter recovery.
- Large opaque `CONCAT` or `SUB` expressions.

When a decompiler problem is near a suspected vulnerability, collect the raw
listing and consider runtime validation before reporting.

## P-code Export and Graphs

The `DecompilerDependent` feature includes p-code export scripts:

```text
ExportPCodeForSingleFunction.java
ExportPCodeForCTADL.java
ExportSourceSetScript.java
```

Decompiler graph scripts include:

```text
GraphASTScript.java
GraphASTAndFlowScript.java
GraphSelectedASTScript.java
```

Use exported p-code or graphs when:

- A report needs a concise data-flow explanation.
- A script will compare old/new functions.
- The decompiler C is too ambiguous.
- The target uses optimized code where variable names are misleading.

Keep graph evidence scoped. Whole-program graphs are rarely useful; function,
slice, or call-chain graphs are better.

## Vulnerability Research Patterns

Bounds check before sink:

1. Find the sink call in decompiler output.
2. Map the call token to its listing address.
3. Use HighFunction p-code to find argument definitions.
4. Inspect branches guarding the same varnodes.
5. Confirm with disassembly around the branch and call.

Format string:

1. Find calls to printf-like imports or wrappers.
2. Use prototypes to identify format parameter position.
3. Track the format argument varnode.
4. Confirm whether it derives from a constant string or attacker input.
5. Preserve raw callsite argument setup.

Integer truncation:

1. Search decompiler output for casts and small integer types.
2. Inspect p-code for INT_ZEXT, INT_SEXT, SUBPIECE, INT_MULT, INT_ADD.
3. Map operations back to addresses.
4. Confirm allocation/copy length uses the truncated or untruncated value.

Indirect call:

1. Identify decompiler callind/p-code indirect calls.
2. Repair vtables/function pointers/types.
3. Inspect xrefs to pointer stores.
4. Use runtime traces if target set is not statically constrained.

## Evidence Checklist

Capture:

- Decompiler API used and timeout.
- Decompile success/error/warning state.
- Function entry, name, and manually repaired status.
- C text excerpt only as supporting context.
- Token/listing address mapping for key expressions.
- P-code operations and varnode definitions/uses for important data flow.
- Raw bytes and disassembly at checks, writes, branches, and calls.
- Type/signature changes that influenced output.
- Known limitations such as missing userops, unresolved externals, bad stack,
  or unmodeled environment.

## Official Source Paths

- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Decompiler/src/main/java/ghidra/app/decompiler/DecompInterface.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Decompiler/src/main/java/ghidra/app/decompiler/flatapi/FlatDecompilerAPI.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Decompiler/ghidra_scripts/FindPotentialDecompilerProblems.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Decompiler/ghidra_scripts/FixSwitchStatementsWithDecompiler.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/DecompilerDependent/ghidra_scripts/ExportPCodeForSingleFunction.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/GhidraDocs/GhidraClass/Debugger/B2-Emulation.md
