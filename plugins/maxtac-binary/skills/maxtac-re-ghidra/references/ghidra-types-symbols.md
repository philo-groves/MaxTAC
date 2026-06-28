# Ghidra Data Types and Symbols

Use this reference when analysis depends on structures, function prototypes,
debug symbols, demangling, PDB/DWARF, vtables, class recovery, Function ID, or
type propagation. Type work can radically improve decompiler output, but it can
also create false confidence. Record which types were imported, inferred, or
manual.

## Contents

- [Quick Targets](#quick-targets)
- [Data Type Archives](#data-type-archives)
- [Function Signatures](#function-signatures)
- [PDB and DWARF](#pdb-and-dwarf)
- [Demangling](#demangling)
- [Structures and Globals](#structures-and-globals)
- [C++ and RTTI](#c-and-rtti)
- [Function ID](#function-id)
- [Type Propagation Discipline](#type-propagation-discipline)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Targets

Prioritize type work for:

- Parser state objects.
- Request/message structs.
- IOCTL buffers.
- File headers and chunk tables.
- Network protocol frames.
- Allocation/copy helper prototypes.
- Callback tables and vtables.
- Auth/session/user objects.
- Cryptographic contexts.
- Imports and wrappers around risky APIs.

Every high-impact type change should note:

- Source: PDB, DWARF, GDT, header import, inferred, or manual.
- Address/function where applied.
- Before/after decompiler effect.
- Whether the type is partial.

## Data Type Archives

Ghidra data types live in program data type managers and archives such as GDT
files. Use the Data Type Manager to:

- Open archives.
- Associate archives.
- Apply and replace data types.
- Find data types by name or size.
- Merge conflicts.
- Capture/apply function data types.

Relevant UI/actions/classes exist for:

```text
ApplyFunctionDataTypesAction
CaptureFunctionDataTypesAction
FindReferencesToDataTypeAction
FindReferencesToFieldByNameOrOffsetAction
DataTypeSync
DataTypeArchiveUtility
```

Use GDT archives for reusable OS/library/vendor types. For one-off inferred
structures, keep names case-scoped and record uncertainty.

## Function Signatures

Function signatures drive:

- Parameter recovery.
- Return value interpretation.
- Decompiler variable naming.
- Callsite argument mapping.
- Stack purge and calling convention behavior.
- Type propagation into callers/callees.

Repair order:

1. Confirm function boundary and calling convention.
2. Fix import or wrapper prototypes first.
3. Fix internal helper prototypes.
4. Apply struct/pointer types to parameters.
5. Re-decompile callers and sinks.

Do not change a signature just to make decompiler output pretty. A signature is
evidence-affecting metadata.

## PDB and DWARF

PDB/DWARF can supply symbols, source mapping, function signatures, types, and
line information. Their availability depends on files, analyzer settings, debug
file search paths, and target format.

Relevant scripts/features:

```text
DWARFAnalyzer
DWARFExternalDebugFilesPlugin
DWARFLineInfoCommentScript.java
DWARFLineInfoSourceMapScript.java
DWARFMacroScript.java
DWARFSetExternalDebugFilesLocationPrescript.java
PDB feature and developer scripts
```

Evidence guidance:

- Record symbol/debug file path and hash.
- Record whether symbols are from the shipped binary, symbol server, local
  cache, or external debug file.
- Treat private symbols as sensitive.
- Do not mix debug info from mismatched builds without noting it.

## Demangling

Demangling can recover namespaces, method names, overloads, and type hints.
Ghidra includes demangler analyzers and scripts:

```text
DemangleAllScript.java
DemangleSymbolScript.java
AbstractDemanglerAnalyzer
MicrosoftDmang feature
GPL/DemanglerGnu
```

Demangling caveats:

- Demangled names are not prototypes unless type information is present and
  applied.
- Names can be stripped, obfuscated, duplicated, or compiler-specific.
- Class names do not prove runtime type reachability.

Use demangled names as navigation and triage aids; confirm semantics in code.

## Structures and Globals

Structure recovery workflow:

1. Identify candidate object base pointer or global.
2. Collect field offsets from loads/stores.
3. Create a partial struct with known fields only.
4. Apply the struct pointer to the relevant parameter/global.
5. Re-decompile and inspect whether field access improves or distorts output.
6. Rename fields based on behavior, not wishful names.

Relevant scripts:

```text
CreateStructure.java
ChooseDataTypeScript.java
FindDataTypeScript.java
FindDataTypeConflictCauseScript.java
FixArrayStructReferencesScript.java
FixupCompositeDataTypesScript.java
```

Partial structures are acceptable evidence if labeled as partial. Do not fill
unknown fields with invented names.

## C++ and RTTI

Ghidra has decompiler scripts and class-recovery helpers:

```text
RecoverClassesFromRTTIScript.java
ApplyClassFunctionDefinitionUpdatesScript.java
ApplyClassFunctionSignatureUpdatesScript.java
AddVfunctionCallRefScript.java
classrecovery/*
```

Use class recovery for:

- Vtable mapping.
- Constructor/destructor identification.
- Virtual dispatch targets.
- Type confusion and UAF research.
- Plugin/interface surfaces.

Caveats:

- Optimized/stripped binaries can have incomplete RTTI.
- Multiple inheritance and thunks complicate vtable interpretation.
- Virtual call xrefs are hypotheses until pointer provenance is constrained.
- Class recovery changes decompiler output; record scripts/options used.

## Function ID

Function ID (FID) identifies known library functions using function hashes and
databases. It is useful for removing library noise and recognizing statically
linked code.

Relevant scripts:

```text
AttachFidDatabase.java
CreateEmptyFidDatabase.java
FIDHashCurrentFunction.java
FidStatistics.java
FindFunctionByHash.java
FindNamedFunction.java
FunctionIDHeadlessPrescript.java
FunctionIDHeadlessPostscript.java
ListFunctions.java
```

Use FID to:

- Label known library functions.
- Separate first-party code from static library code.
- Find reused vulnerable library functions.
- Seed patch-diff or BSim workflows.

Evidence caveats:

- Hash matches depend on database quality.
- Compiler options and code changes can defeat matching.
- A library function match does not prove reachability.

## Type Propagation Discipline

Before applying a type:

- Confirm address and storage.
- Check whether the target is code, data, external, overlay, or dynamic trace.
- Confirm the type width and packing for the target ABI.
- Record source and confidence.

After applying a type:

- Re-check decompiler output.
- Confirm raw accesses still match field offsets.
- Check callers/callees for propagated assumptions.
- Preserve before/after artifacts for important findings.

Avoid:

- Applying host headers blindly to firmware ABIs.
- Assuming Windows/Linux struct layouts are interchangeable.
- Applying a vtable/class type solely because one method name matches.
- Reporting a field name as fact when it is analyst-assigned.

## Evidence Checklist

Capture:

- Type source and hash/path where applicable.
- Data type archive names and versions.
- PDB/DWARF/debug file paths, hashes, and mismatch warnings.
- Manual structure definitions and unknown fields.
- Function signature changes and calling convention changes.
- Demangling source and unresolved symbols.
- FID database names and match confidence.
- Before/after decompiler or listing effects for high-impact type changes.
- Any type conflicts or merge choices.

## Official Source Paths

- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/DataTypeManagerPlugin/data_type_manager_description.htm
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/DWARFExternalDebugFilesPlugin/DWARFExternalDebugFilesPlugin.html
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/ghidra_scripts/DemangleAllScript.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Decompiler/ghidra_scripts/RecoverClassesFromRTTIScript.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/FunctionID/src/main/help/help/topics/FunctionID/FunctionID.html
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/FunctionID/ghidra_scripts/FunctionIDHeadlessPrescript.java
