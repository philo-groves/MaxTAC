# Ghidra Analysis Workflow

Use this reference when turning an imported binary into reliable functions,
xrefs, symbols, call paths, stack facts, and vulnerability evidence. Ghidra's
auto-analysis is strong, but it is still a chain of analyzers triggered by
program changes. Treat analyzer output as a hypothesis until important claims
are confirmed with bytes, disassembly, decompiler mappings, or runtime traces.

## Contents

- [Quick Workflow](#quick-workflow)
- [Import Discipline](#import-discipline)
- [Auto-Analysis Model](#auto-analysis-model)
- [Analyzer Options](#analyzer-options)
- [Function Repair](#function-repair)
- [Disassembly Repair](#disassembly-repair)
- [References and Reachability](#references-and-reachability)
- [Stack and Calling Convention Repair](#stack-and-calling-convention-repair)
- [Switches, Tables, and Indirect Flow](#switches-tables-and-indirect-flow)
- [Architecture-Specific Notes](#architecture-specific-notes)
- [Workflow Patterns](#workflow-patterns)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Workflow

Start with an evidence-preserving import:

```bash
analyzeHeadless ./projects Case001 \
  -import ./sample.bin \
  -analysisTimeoutPerFile 600 \
  -log evidence/case001/analyze.log \
  -scriptlog evidence/case001/script.log
```

For ambiguous input, import without analysis first:

```bash
analyzeHeadless ./projects Case001 \
  -import ./sample.bin \
  -noanalysis \
  -processor "DATA:LE:64:default" \
  -overwrite
```

Then inspect and re-import with the correct language, compiler spec, loader, and
base assumptions before broad analysis.

GUI workflow:

1. Import the file.
2. Record loader/language/compiler/image-base decisions.
3. Run Auto Analysis with visible options.
4. Review warnings, memory map, entry points, sections, imports, strings.
5. Repair missed code/data/function boundaries.
6. Re-run targeted analysis after repair.
7. Use xrefs, call trees, graphs, and decompiler output only after checking the
   underlying disassembly.

## Import Discipline

Record these immediately after import:

- Original file path and hash.
- Ghidra version and project name.
- Loader selected.
- Language ID and compiler spec ID.
- Image base and memory blocks.
- External library search paths.
- Import warnings and unresolved externals.
- Whether PDB/DWARF/debug files were found and applied.

Do not normalize away loader uncertainty. For raw blobs and firmware, the
loader/language/base decision often dominates every later conclusion.

For raw firmware, create an "import assumptions" note containing:

- CPU family, endianness, bitness, and mode.
- ROM/RAM address map.
- Vector table or reset handler source.
- Whether code is position-dependent.
- Any manually-created memory blocks or overlays.

## Auto-Analysis Model

Ghidra Auto Analysis watches program changes such as new disassembly and
function creation. Analyzers can create more changes, which can trigger other
analyzers. Examples include function creation, stack analysis, operand reference
analysis, data reference analysis, strings, and format-specific analyzers.

Implications:

- One manual disassembly action can cascade into new functions, references, and
  data definitions.
- Analyzer priority matters; a later analyzer may depend on references created
  by an earlier one.
- Selection-restricted analysis may still affect referenced locations outside
  the selection.
- "Analyze All Open" uses options based on the current program's architecture;
  mismatched open programs may not be analyzed by that action.
- Prototype analyzers can be useful but should be called out in evidence.

Use staged analysis:

1. Baseline import and default analysis.
2. Inspect warnings and high-value regions.
3. Repair obvious disassembly/function issues.
4. Re-run targeted analysis on repaired selections.
5. Enable expensive or prototype analyzers only when justified.

## Analyzer Options

Analyzer options live in Program Options under the Analysis tree. They are
architecture and analyzer dependent. Yellow-highlighted analyzer rows indicate
non-default enablement or options in the GUI.

Capture option deltas when they matter:

- Function start discovery options.
- Stack analyzers.
- Non-returning function discovery.
- Constant propagation and reference propagation.
- ASCII/Unicode string analyzer thresholds.
- DWARF/PDB/debug info settings.
- Format-specific analyzers such as PE, ELF, Mach-O, Go, CLI metadata.

For PyGhidra automation, analysis options are accessible with:

```python
analysis_props = pyghidra.analysis_properties(program)
```

Wrap option changes in a transaction and save the program only if persistence is
intended.

## Function Repair

Function facts that often need manual repair:

- Start address.
- End address.
- Calling convention.
- Parameters and return type.
- Stack purge/stack depth change.
- No-return behavior.
- Thunks and wrappers.
- Shared returns and tail-call edges.
- ARM/Thumb mode or other context register state.

Built-in scripts that are useful leads:

```text
FindUndefinedFunctionsScript.java
FindInstructionsNotInsideFunctionScript.java
FindSharedReturnFunctionsScript.java
ClearOrphanFunctions.java
CreateFunctionAfterTerminals.java
ComputeCyclomaticComplexity.java
ExportFunctionInfoScript.java
```

Function repair discipline:

- Preserve the original bytes and disassembly around the suspected function.
- Note whether the function was auto-created or manually created.
- Re-run stack/function analyzers after changing boundaries.
- Re-check xrefs and decompiler output after repair.
- For vulnerability evidence, identify the exact function entry and callsite
  addresses, not just decompiler names.

## Disassembly Repair

Disassembly repair is common in packed code, obfuscated code, mixed code/data,
firmware, hand-written assembly, and unusual compiler output.

Use installed script helpers when present:

```text
DoARMDisassemble.java
DoThumbDisassemble.java
ArmThumbFunctionTableScript.java
DebugSleighInstructionParse.java
ReloadSleighLanguage.java
```

Developer scripts in the upstream source tree, such as
`RangeDisassemblerScript.java` and `ForceRedisassembly.java`, are also useful
in development builds, but do not assume they are present in every release
script path.

Repair workflow:

1. Confirm bytes with the Bytes view or listing.
2. Check memory block permissions and address space.
3. Clear bad code/data only for the affected range.
4. Set required context register/mode state before redisassembly.
5. Disassemble from a known entry or branch target.
6. Create or repair the containing function.
7. Re-run targeted analysis.

Avoid broad redisassembly until you know why analysis failed. A bad base address
or wrong language ID will produce a clean-looking but false database.

## References and Reachability

Use references to answer:

- Who calls this function?
- What does this function call?
- What code references this string, global, vtable, pointer, or import?
- Is an exported/API-facing entry connected to a sink?

Relevant Ghidra surfaces:

- Location References provider.
- References plugin and Edit References provider.
- Function Call Trees.
- Function Graph.
- Symbol Tree.
- Search for Direct References.
- Program Text search for labels/comments/functions.

Reference repair scripts:

```text
AddReferencesInSwitchTable.java
AddSingleReferenceInSwitchTable.java
CreateOperandReferencesInSelectionScript.java
CreateRelocationBasedOperandReferences.java
LabelDirectFunctionReferencesScript.java
LabelIndirectReferencesScript.java
LabelIndirectStringReferencesScript.java
PropagateConstantReferences.java
PropagateX86ConstantReferences.java
ResolveExternalReferences.java
```

Reachability caveats:

- A Ghidra reference is not runtime proof.
- Missing xrefs can mean indirect flow, missed disassembly, bad data types,
  unresolved relocations, wrong language/context, or intentionally computed
  addresses.
- Imported symbols and thunk functions can hide the real sink.
- Decompiler call expressions should be mapped back to listing addresses before
  reporting.

## Stack and Calling Convention Repair

Stack facts affect parameter recovery, local variables, decompiler output, and
sink argument analysis.

Useful surfaces:

- Stack Editor.
- Function Signature editor.
- Function Purge / Stack Depth Change actions.
- Parameter ID analyzer.
- Calling convention fields.
- Function variable and parameter windows.

Relevant scripts/classes in upstream tree:

```text
MakeStackRefs.java
TurnOffStackAnalysis.java
FunctionStackAnalysisCmd
SetStackDepthChangeCommand
ApplyFunctionDataTypesCmd
CaptureFunctionDataTypesCmd
```

Repair guidance:

- Verify the ABI and compiler spec before changing parameter locations.
- For x86 stdcall/fastcall/cdecl confusion, record stack purge assumptions.
- For optimized code, do not overfit variable names to decompiler guesses.
- When proving a bug, identify the registers/stack slots used at the sink.
- Preserve raw disassembly for bounds checks and argument setup.

## Switches, Tables, and Indirect Flow

Indirect control flow often needs manual help before Ghidra xrefs are complete.

Built-in scripts:

```text
FixSwitchStatementsWithDecompiler.java
AddReferencesInSwitchTable.java
AddSingleReferenceInSwitchTable.java
FindUnrecoveredSwitchesScript.java
FindRunsOfPointersScript.java
SearchForImageBaseOffsetsScript.java
```

Workflow:

1. Identify the dispatcher and table region.
2. Confirm table element width, base, signedness, and relocation behavior.
3. Create missing references or switch overrides.
4. Re-run analysis on the dispatcher.
5. Verify branch targets in listing and graph views.

For C++ or plugin dispatch, combine vtable/class recovery, xrefs to constructor
stores, indirect call sites, and decompiler p-code. Do not report an indirect
edge as confirmed unless the target address is constrained.

## Architecture-Specific Notes

ARM/Thumb:

- Wrong mode creates wrong instruction lengths and false control flow.
- Use context-aware disassembly and Thumb helper scripts.
- Check vector tables and function pointer low-bit conventions.

MIPS/PPC/RISC:

- References may be built across multiple instructions.
- Constant/reference propagation options matter.
- Delay slots and TOC/global pointer behavior can affect decompiler output.

x86/x64:

- Calling convention and stack purge assumptions are common failure points.
- Tail calls and thunks can make call trees look incomplete.
- SEH and C++ exception tables may create non-obvious control flow.

Firmware/raw blobs:

- The language ID may be correct while memory map/base is wrong.
- Hardware registers and MMIO regions need explicit notes.
- External calls may be firmware vectors, not normal imports.

## Workflow Patterns

String to sink:

1. Search for protocol/error/config strings.
2. Follow references to containing functions.
3. Inspect callers and call tree.
4. Confirm argument setup in listing.
5. Use decompiler only after mapping tokens to addresses.

Crash offset to function:

1. Map crash address to image base and Ghidra address.
2. Confirm memory block and instruction bytes.
3. Find containing function or create one if missed.
4. Repair stack/signature as needed.
5. Compare crashing instruction with runtime registers.

Patch diff:

1. Import both versions with identical language/compiler/import options.
2. Run comparable analysis.
3. Use Version Tracking or Function Comparison.
4. Inspect changed functions in listing and decompiler.
5. Export function bytes, decompiler output, xrefs, and graph evidence.

## Evidence Checklist

Capture:

- Import settings, language ID, compiler spec, loader, image base.
- Analysis options and non-default analyzers.
- Timeout/cancel state.
- Manual repairs: functions, data, references, stack, signatures, no-return.
- Function addresses and raw bytes around key instructions.
- Xrefs and call paths with addresses.
- Decompiler output only with mapped listing addresses.
- Graphs or screenshots only as supporting evidence, not sole proof.
- Limitations: unresolved externals, missing debug symbols, packed code, bad
  context state, or architecture-specific analyzer gaps.

## Official Source Paths

- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/AutoAnalysisPlugin/AutoAnalysis.htm
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/ghidra_scripts/FindUndefinedFunctionsScript.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/ghidra_scripts/FindInstructionsNotInsideFunctionScript.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/ghidra_scripts/ExportFunctionInfoScript.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/ReferencesPlugin/References.htm
