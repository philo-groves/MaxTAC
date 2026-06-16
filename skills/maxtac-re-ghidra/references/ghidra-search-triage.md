# Ghidra Search Triage

Use this reference when searching a binary for strings, bytes, instruction
patterns, scalars, direct references, tables, suspicious imports, or
vulnerability-specific markers. Ghidra search results are most valuable when
immediately tied to functions, xrefs, and evidence artifacts.

## Contents

- [Quick Targets](#quick-targets)
- [Search Surfaces](#search-surfaces)
- [Strings](#strings)
- [Memory Search](#memory-search)
- [Program Text Search](#program-text-search)
- [Instruction Pattern Search](#instruction-pattern-search)
- [Scalars and Constants](#scalars-and-constants)
- [Direct References and Address Tables](#direct-references-and-address-tables)
- [Built-in Search Scripts](#built-in-search-scripts)
- [Vulnerability Patterns](#vulnerability-patterns)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Targets

Search for:

- Error strings near parser code.
- Format strings and printf-like calls.
- Command execution strings and shell paths.
- File paths, registry keys, URL schemes, IPC names, mutex names.
- Magic bytes, protocol markers, TLV tags, and version constants.
- Hardcoded keys, salts, IVs, certificates, and JWT/OAuth markers.
- Deserialization/class names.
- Dangerous imports and wrapper functions.
- Instruction patterns around sinks or patch sites.
- Scalar constants such as size limits, opcodes, auth flags, and masks.

For every hit, capture:

- Hit address and memory block.
- Defined data or raw bytes.
- References to/from the hit.
- Containing function.
- Nearby imports/calls.
- Whether the hit is in loaded memory, overlay, external block, debug data, or
  dead data.

## Search Surfaces

Ghidra exposes several distinct search paths:

- Search Memory: bytes, strings, regex, numeric formats.
- Search for Strings / Defined Strings.
- Search Program Text: labels, comments, functions, instructions, operands.
- Search for Instruction Patterns: byte-backed instruction sequence search with
  masks.
- Search for Scalars.
- Search for Direct References.
- Search for Address Tables.
- Data Type Manager search.
- Symbol Tree filtering.
- Decompiler text finder when the DecompilerDependent feature is present.

Do not confuse program text search with memory search. Program text searches
the analysis database; memory search searches bytes.

## Strings

Useful string workflows:

1. Use Search for Strings to create candidate strings when the analyzer missed
   them.
2. Use Defined Strings to filter, sort, and navigate already-defined strings.
3. Follow references to each string.
4. If no references exist, inspect nearby pointer tables, relocation tables, or
   manual address references.

Relevant scripts:

```text
CountAndSaveStrings.java
CreateStringScript.java
FindTextScript.java
SearchMemoryForStringsRegExScript.java
TranslateStringsScript.java
LabelIndirectStringReferencesScript.java
```

String caveats:

- Auto-created strings depend on analyzer thresholds.
- UTF-16, Pascal strings, packed strings, and encoded strings may be missed.
- Dead strings can survive in unused sections.
- Referenced strings can be reached only through pointer tables or computed
  offsets.

## Memory Search

Use memory search for bytes and encodings:

- Hex byte patterns.
- ASCII/UTF-16 strings.
- Regular expressions.
- Integers and floats.
- Masked values when supported by the search UI/API.

Constrain scope when possible:

- Executable blocks for gadgets/instructions.
- Read-only data for constants.
- Writable data for globals/state.
- File-backed blocks only when excluding synthetic externals.

For evidence, export the bytes around each hit and the memory block name.

## Program Text Search

Program text search is useful after analysis:

- Labels and namespaces.
- Function names.
- Comments.
- Instruction mnemonics and operands.
- Data mnemonics and operands.

Use it to find analyst-created markup or imported debug names, but do not treat
it as a byte search. A text hit can disappear if analysis is reset, names are
changed, or display formatting changes.

## Instruction Pattern Search

Instruction Pattern Search builds byte patterns from selected instructions.
Operands and mnemonics can be masked for more flexible matching.

Good uses:

- Find repeated compiler idioms.
- Find patched instruction sequences.
- Find likely copies of a vulnerable function.
- Locate gadgets or indirect branch patterns in the same architecture.

Important limitation:

Instruction pattern search matches byte patterns, not mnemonic intent. A `ret`
pattern from one architecture or mode is not portable to another architecture
or mode. Mask operands/scalars/addresses when searching for code shape rather
than exact constants.

Manual entry requires full bytes. Use it when carrying a pattern from a report
or patch diff.

## Scalars and Constants

Use scalar search for:

- Length limits.
- Magic constants.
- Flags and bitmasks.
- Syscall or IOCTL numbers.
- Error codes.
- Protocol tags.
- Structure offsets.

After finding a scalar:

1. Check whether it is an immediate, address, enum, or data value.
2. Find containing function.
3. Inspect operand references and decompiler use.
4. Rename/equate only after confirming semantics.

Constants often appear in optimized code because of compiler transforms. Do not
assume identical constants mean identical semantics.

## Direct References and Address Tables

Search for Direct References and Address Tables helps recover:

- Jump tables.
- Vtables.
- Callback tables.
- Handler arrays.
- Dispatch tables.
- Pointers to strings/globals/functions.

Relevant scripts:

```text
FindRunsOfPointersScript.java
SearchForImageBaseOffsetsScript.java
CreateOperandReferencesInSelectionScript.java
CreateRelocationBasedOperandReferences.java
AddReferencesInSwitchTable.java
AddSingleReferenceInSwitchTable.java
```

Use table recovery before drawing reachability conclusions from xrefs. Missing
table references often explain why an exported parser appears disconnected from
dangerous code.

## Built-in Search Scripts

High-value built-in scripts:

```text
CountAndSaveStrings.java
FindTextScript.java
FindAudioInProgramScript.java
FindImagesScript.java
EmbeddedFinderScript.java
FindRunsOfPointersScript.java
FindInstructionsNotInsideFunctionScript.java
InstructionSearchScript.java
SearchMemoryForStringsRegExScript.java
SearchMnemonicsNoOpsNoConstScript.java
SearchMnemonicsOpsConstScript.java
SearchMnemonicsOpsNoConstScript.java
SearchForImageBaseOffsetsScript.java
```

Use built-ins to learn API patterns and avoid rewriting fragile search logic.
When a built-in asks for GUI input, copy it and make arguments explicit for
headless use.

## Vulnerability Patterns

Format string triage:

- Search strings for `%n`, `%s`, `%p`, positional format syntax, and logging
  templates.
- Search imports for printf-like calls.
- Use prototypes to identify format argument position.
- Follow decompiler p-code or raw argument setup to determine control.

Command execution:

- Search for shell paths, command fragments, environment variables, and process
  APIs.
- Check references to imports/wrappers and string concatenation code.
- Confirm whether user-controlled data reaches command arguments.

Unsafe copy/parse:

- Search imports and wrappers for copy/move/format functions.
- Search constants around buffer sizes.
- Find callers and inspect bounds checks.
- Preserve callsite disassembly and decompiler data-flow.

Crypto/key material:

- Search for PEM headers, ASN.1 markers, algorithm names, constants, IV sizes.
- Check whether material is in dead/debug data or live referenced code.
- Capture xrefs and storage location.

Patch diff:

- Use instruction patterns from changed code.
- Mask relocations and addresses.
- Check all hits manually; pattern reuse can reflect compiler output, not the
  vulnerability.

## Evidence Checklist

Capture:

- Search type and settings.
- Search scope and memory blocks.
- Pattern, string, regex, scalar, or instruction selection.
- Hit addresses and surrounding bytes.
- Containing function and xrefs.
- Whether hit data was auto-created, manual, or raw.
- Any masks used for instruction pattern search.
- False-positive filtering criteria.
- Scripts used and script logs.

## Official Source Paths

- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/Search/Search_Memory.htm
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/Search/Search_for_Strings.htm
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/Search/Search_Instruction_Patterns.htm
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/Search/Search_for_DirectReferences.htm
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/ghidra_scripts/SearchMemoryForStringsRegExScript.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/ghidra_scripts/InstructionSearchScript.java
