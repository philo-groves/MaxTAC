# Radare2 Diffing

Use radare2 diffing when comparing vulnerable versus patched binaries,
firmware revisions, unpacked payloads, crash repro variants, or runtime memory
states. Prefer `radiff2` for repeatable command-line comparisons and the `c`
command family inside an r2 session when the comparison depends on current seek,
debugger memory, mapped files, or interactive context.

Diffing is a triage accelerator, not proof by itself. Always connect a changed
byte, function, import, string, or graph edge to reachable behavior before
claiming vulnerability impact.

## Contents

- [Quick Commands](#quick-commands)
- [Diffing Mental Model](#diffing-mental-model)
- [Prepare Inputs](#prepare-inputs)
- [Raw Byte and Data Diffing](#raw-byte-and-data-diffing)
- [Similarity, Distance, and Counts](#similarity-distance-and-counts)
- [Disassembly and Opcode Diffing](#disassembly-and-opcode-diffing)
- [Code Graph Diffing](#code-graph-diffing)
- [Imports, Strings, and Binary Metadata](#imports-strings-and-binary-metadata)
- [JSON and Machine-Readable Output](#json-and-machine-readable-output)
- [Patch Script Output](#patch-script-output)
- [In-Session Compare Commands](#in-session-compare-commands)
- [Compare Watchers](#compare-watchers)
- [Vulnerability Research Patterns](#vulnerability-research-patterns)
- [Evidence Checklist](#evidence-checklist)
- [Cautions](#cautions)
- [Official References](#official-references)

## Quick Commands

Basic file diff:

```text
radiff2 old.bin new.bin
radiff2 -c old.bin new.bin
radiff2 -s old.bin new.bin
radiff2 -ss old.bin new.bin
radiff2 -x old.bin new.bin
radiff2 -X old.bin new.bin
radiff2 -u old.bin new.bin
radiff2 -U old.bin new.bin
radiff2 -d old.bin new.bin
radiff2 -j -d old.bin new.bin
```

Code-oriented diff:

```text
radiff2 -D -a x86 -b 64 old.bin new.bin
radiff2 -O -a x86 -b 64 old.bin new.bin
radiff2 -C old.bin new.bin
radiff2 -AC -a x86 -b 64 old.bin new.bin
radiff2 -AAC -a x86 -b 64 old.bin new.bin
radiff2 -C -t 90 old.bin new.bin
radiff2 -C -S dist old.bin new.bin
radiff2 -g sym.func old.bin new.bin
radiff2 -g 0x401000,0x402000 old.bin new.bin
radiff2 -md -g sym.func old.bin new.bin > func.dot
radiff2 -mj -g sym.func old.bin new.bin > func.json
```

Metadata and strings:

```text
radiff2 -z old.bin new.bin
radiff2 -i old.bin new.bin
radiff2 -i imports old.bin new.bin
radiff2 -i symbols old.bin new.bin
rabin2 -Ij old.bin > old.info.json
rabin2 -Ij new.bin > new.info.json
rabin2 -ij old.bin > old.imports.json
rabin2 -ij new.bin > new.imports.json
rabin2 -zj old.bin > old.strings.json
rabin2 -zj new.bin > new.strings.json
```

Patch-script output:

```text
radiff2 -r old.bin new.bin > patch.r2
Copy-Item old.bin candidate.bin
radare2 -qnw -i patch.r2 candidate.bin
rahash2 -a sha256 candidate.bin new.bin
```

In-session comparison:

```text
c?                  compare command help
cx 7f454c46         compare hex bytes at current seek
cc sym.new @ sym.old
ccc sym.new @ sym.old
ccd sym.new @ sym.old
cf other.bin
cu <addr> @ <addr>
cud <addr> @ <addr>
cg other.bin
```

Runtime watchers:

```text
cw <addr> <size> p8
cwu
cw
cw*                 emit watcher setup as r2 commands
cwq                 quiet watcher output
cwj                 JSON watcher output
cwr                 revert watcher base
cwd <addr>          delete watcher
```

## Diffing Mental Model

Use the cheapest useful diff first:

- Raw byte diff answers "what bytes changed?"
- Delta diff answers "what insertion/deletion explains different-size files?"
- Similarity and count answer "are these comparable at all?"
- Disassembly diff answers "what instructions changed linearly?"
- Opcode-only diff answers "did instruction bytes change while syntax/noisy
  operands may differ?"
- Graph diff answers "which functions or basic blocks changed?"
- Metadata diff answers "which imports, symbols, sections, classes, fields, or
  strings changed?"
- In-session compare answers "how does this mapped data or runtime memory differ
  right now?"

For vulnerability research, rank changed regions by security relevance:

- Bounds checks, length calculations, signedness conversions, allocation sizes.
- Parser dispatch, table indexing, and indirect calls.
- Authentication, authorization, signature checks, and sandbox policy.
- Crypto parameter handling, random generation, and key parsing.
- Dangerous imports or wrappers around copy, format, command, file, socket, or
  deserialization APIs.
- Error handling and cleanup paths that affect object lifetime.

Keep file order explicit. In this guide, `old.bin` usually means vulnerable or
baseline, and `new.bin` means patched or changed. Some visual and graph outputs
are easier to read in the opposite order, so record the order used.

## Prepare Inputs

Before diffing, confirm that both files are comparable:

```text
rabin2 -I old.bin
rabin2 -I new.bin
rahash2 -a sha256 old.bin new.bin
```

Check:

- Format, architecture, bits, endian, class, and machine.
- PIE/PIC, stripped state, canary, NX, RELRO, and compiler metadata when present.
- File size and section layout.
- Build IDs, timestamps, version resources, or firmware version fields.
- Packing, signing, compression, encryption, or container wrappers.

If files are wrapped in firmware images or archives, extract comparable members
first. Diffing two whole firmware blobs may identify container churn instead of
the vulnerable component.

If addresses differ because of rebasing:

```text
radiff2 -p old.bin new.bin
radiff2 -e io.va=false old.bin new.bin
```

Use physical addressing when file offsets matter more than virtual addresses.
Use virtual addresses when comparing disassembly, symbols, and function graphs.
Check `radiff2 -h` for the exact option behavior in the installed version.

For raw shellcode or architecture-ambiguous blobs, always specify architecture
and bits:

```text
radiff2 -D -a x86 -b 64 old.bin new.bin
radiff2 -D -a arm -b 16 old.bin new.bin
```

## Raw Byte and Data Diffing

Default `radiff2` output shows changed bytes and offsets:

```text
radiff2 old.bin new.bin
```

Use it for quick patch triage:

- Small NOP patches.
- Changed constants.
- Short branch opcode changes.
- Byte-level edits in packed data.
- File-format field changes.

Show two-column hexdump and ASCII:

```text
radiff2 -x old.bin new.bin
```

Show two-column hexII:

```text
radiff2 -X old.bin new.bin
```

Use unified output:

```text
radiff2 -u old.bin new.bin
radiff2 -U old.bin new.bin
```

Use delta diffing for files with insertions or deletions:

```text
radiff2 -d old.bin new.bin
radiff2 -j -d old.bin new.bin
```

Default byte diff truncates at the shorter file when sizes differ. Delta diffing
is slower but better for inserted strings, added functions, shifted tables, and
file-format chunks that changed size.

Triage steps:

1. Run `radiff2 -s` and `radiff2 -c`.
2. If file sizes differ, run `radiff2 -d`.
3. If changed regions are small, inspect bytes with `radiff2 -x`.
4. Convert changed instruction bytes with `rasm2 -d` or use `radiff2 -D`.
5. Map changed offsets into sections and functions with `rabin2 -S`, `r2`, or
   graph diffing.

## Similarity, Distance, and Counts

Compute similarity and edit distance:

```text
radiff2 -s old.bin new.bin
```

Use Levenshtein-style distance with substitutions:

```text
radiff2 -ss old.bin new.bin
```

Count changes:

```text
radiff2 -c old.bin new.bin
```

Use these commands to decide if a pair is worth deeper comparison:

- Very high similarity with few changed regions: ideal for patch diffing.
- High similarity with many shifted regions: try `-d`, metadata diff, and graph
  diff.
- Low similarity: confirm same component/version family before investing time.
- Identical raw bytes but different runtime behavior: compare metadata, loader
  state, signatures, external config, and environment.

Do not treat high similarity as safety. A one-byte branch change can remove an
auth check or bounds check.

## Disassembly and Opcode Diffing

Show changed bytes as disassembly:

```text
radiff2 -D -a x86 -b 64 old.bin new.bin
```

Use this for:

- Shellcode changes.
- Short patch hunks.
- Packed or raw code blobs.
- Branch inversion, added NOPs, changed call targets, and constant changes.

Compare opcode bytes only:

```text
radiff2 -O -a x86 -b 64 old.bin new.bin
```

Opcode-only diff can reduce noise from operands, addresses, relocations, or
rendering differences. If opcode-only output is quiet but graph or disassembly
changed, inspect relocations, immediates, call targets, and data references.

When disassembly looks wrong:

- Confirm `-a` and `-b`.
- Confirm ARM Thumb versus ARM mode.
- Confirm endianness when relevant.
- Avoid linear disassembly across mixed code/data regions.
- Use `r2 -A` and `pdf` on mapped functions for context.

## Code Graph Diffing

List function-level matches:

```text
radiff2 -C old.bin new.bin
```

Ask radiff2 to analyze first:

```text
radiff2 -AC -a x86 -b 64 old.bin new.bin
radiff2 -AAC -a x86 -b 64 old.bin new.bin
```

`-A` runs analysis before graph diffing. `-AA` asks for deeper analysis. Use the
same analysis depth for both files and note it in evidence, because function
recovery quality changes the result.

Set threshold:

```text
radiff2 -C -t 90 old.bin new.bin
```

Sort graph diff output:

```text
radiff2 -C -S dist old.bin new.bin
radiff2 -C -S size old.bin new.bin
radiff2 -C -S name old.bin new.bin
```

Diff one function by name:

```text
radiff2 -g sym.parser old.bin new.bin
```

Diff functions with different names or offsets:

```text
radiff2 -g 0x401000,0x402000 old.bin new.bin
```

Choose graph output mode:

```text
radiff2 -ma -g sym.parser old.bin new.bin
radiff2 -md -g sym.parser old.bin new.bin > parser.dot
radiff2 -mj -g sym.parser old.bin new.bin > parser.json
radiff2 -mJ -g sym.parser old.bin new.bin > parser.disasm.json
radiff2 -ms -g sym.parser old.bin new.bin > parser.r2
```

Common graph modes:

- `a`: ASCII art.
- `d`: Graphviz dot.
- `j`: JSON.
- `J`: JSON with disassembly.
- `s`: r2 commands.
- `g`: GML.
- `t`: tiny ASCII art.
- `i`: interactive ASCII art.

Graph diff triage:

- Start with `-C` to find unmatched or low-similarity functions.
- Focus on changed functions connected to imports, parser entrypoints, or
  externally reachable strings.
- Use `-g` on high-value functions.
- Follow changed basic blocks to branch conditions, lengths, allocation sizes,
  and sink calls.
- Re-open each binary in r2 and inspect the changed functions with `pdf`,
  `agf`, `axt`, and `afi`.

## Imports, Strings, and Binary Metadata

Diff extracted strings:

```text
radiff2 -z old.bin new.bin
```

Diff binary information:

```text
radiff2 -i old.bin new.bin
```

Some builds accept selectors for imports, fields, symbols, classes, or similar
binary information:

```text
radiff2 -i imports old.bin new.bin
radiff2 -i symbols old.bin new.bin
radiff2 -i sections old.bin new.bin
```

Check live help:

```text
radiff2 -h
radiff2 -i help old.bin new.bin
```

Use `rabin2` when you need stable, scriptable metadata artifacts:

```text
rabin2 -Ij old.bin > old.info.json
rabin2 -Ij new.bin > new.info.json
rabin2 -ij old.bin > old.imports.json
rabin2 -ij new.bin > new.imports.json
rabin2 -zj old.bin > old.strings.json
rabin2 -zj new.bin > new.strings.json
rabin2 -Sj old.bin > old.sections.json
rabin2 -Sj new.bin > new.sections.json
```

High-value metadata changes:

- New or removed dangerous imports.
- Added crypto, decompression, scripting, or deserialization libraries.
- Added command strings, URLs, paths, SQL, format strings, or protocol markers.
- Removed validation/error strings after a patch.
- Added stack canary, PIE, NX, RELRO, or code-signing metadata.
- Section permission changes, especially writable/executable mappings.
- Exported API changes in shared libraries.

Metadata diff is often the fastest path to a candidate function. Use strings and
imports to seed xrefs, then confirm behavior with analysis or debugging.

## JSON and Machine-Readable Output

Use JSON for automation:

```text
radiff2 -j old.bin new.bin
radiff2 -j -d old.bin new.bin
radiff2 -mj -g sym.func old.bin new.bin
radiff2 -mJ -g sym.func old.bin new.bin
```

Useful workflow:

```text
radiff2 -j -d old.bin new.bin > data-diff.json
radiff2 -AC -t 90 old.bin new.bin > graph-summary.txt
radiff2 -mJ -g sym.parser old.bin new.bin > parser-graph.json
```

Capture both machine-readable and human-readable artifacts:

- JSON for exact offsets, hashes, and changes.
- Text summaries for review notes.
- `dot` or SVG for changed function graphs when useful.
- `rabin2` JSON for metadata baseline.

Do not depend on one output format alone. JSON schemas and option behavior can
shift across radare2 versions, while text output is easier for humans but harder
to parse safely.

## Patch Script Output

Generate an r2 patch script:

```text
radiff2 -r old.bin new.bin > patch.r2
```

Inspect it before applying:

```text
Get-Content patch.r2
```

Apply to a copy:

```text
Copy-Item old.bin candidate.bin
radare2 -qnw -i patch.r2 candidate.bin
rahash2 -a sha256 candidate.bin new.bin
```

The generated script usually contains `wx` writes at offsets. Applying it with
`radare2 -qnw -i` means:

- `-q`: quiet and quit after commands.
- `-n`: do not parse binary headers.
- `-w`: open writable.
- `-i`: run the script.

Use patch output for:

- Creating minimal byte-change candidates.
- Validating that a raw diff can transform one sample into another.
- Isolating the effect of a vendor patch.
- Testing whether one changed hunk is sufficient to alter behavior.

Never patch the only copy of evidence. Record the original hashes, candidate
hashes, script content, and command used.

## In-Session Compare Commands

Inside r2, `c` commands expose comparison features without leaving the current
session. This is useful when comparing:

- Two functions in the same binary.
- A mapped file against the current seek.
- Debugger memory before and after a breakpoint.
- Runtime-unpacked memory against an on-disk sample.
- Bytes from two addresses or sections.

Show help:

```text
c?
```

Compare bytes at current seek:

```text
cx 7f454c46
cx 7f45..46
c1 0x90
c2 0x4142
c4 0x41424344
c8 0x4142434445464748
```

Compare current seek with a file:

```text
cf other.bin
```

Compare two areas:

```text
cc <addr> @ <addr>
ccc <addr> @ <addr>
cX <addr> @ <addr>
```

Compare disassembly:

```text
ccd <addr> @ <addr>
cud <addr> @ <addr>
```

Compare decompiler output when configured:

```text
e cmd.pdc=pdg
ccdd <addr> @ <addr>
```

Graph diff current file and another file:

```text
cg other.bin
```

Use `bf` to set block size to a function before comparing:

```text
s sym.old_func
bf sym.old_func
cc sym.new_func @ sym.old_func
ccd sym.new_func @ sym.old_func
```

Use in-session compare after analysis has created useful function flags:

```text
aaa
afl
cc sym.candidate2 @ sym.candidate1
```

## Compare Watchers

Compare watchers record bytes at one point in time and report whether they
changed later. They are useful in debugging, emulation, patch testing, and
runtime unpacking.

Create a watcher:

```text
cw <addr> <size> p8
```

Update and show:

```text
cwu
cw
```

Use JSON, quiet, or r2-command output:

```text
cwj
cwq
cw*
```

Revert or delete:

```text
cwr
cwd <addr>
```

Watch code as disassembly:

```text
cw <addr> <size> pD
cwu
cw
```

Vulnerability uses:

- Watch a destination buffer before and after a copy.
- Watch an object header before and after parser mutation.
- Watch heap metadata before and after free/realloc.
- Watch an import table, vtable, callback table, or dispatch table.
- Watch unpacked code after a decrypt/decompress loop.

Be careful with overlapping watchers. Update all relevant watchers before
interpreting results.

## Vulnerability Research Patterns

### Patch Diff Triage

Goal: identify the security-relevant change between vulnerable and patched
builds.

Commands:

```text
rahash2 -a sha256 old.bin new.bin
rabin2 -I old.bin
rabin2 -I new.bin
radiff2 -s old.bin new.bin
radiff2 -c old.bin new.bin
radiff2 -AC -a <arch> -b <bits> old.bin new.bin
radiff2 -z old.bin new.bin
```

Then:

```text
radiff2 -g sym.changed old.bin new.bin
radiff2 -mJ -g sym.changed old.bin new.bin > changed.json
r2 -A old.bin
r2 -A new.bin
```

Look for added checks, changed comparisons, new error paths, length clamping,
allocation-size fixes, removed unsafe calls, or altered cleanup behavior.

### Small Byte Patch

Goal: understand a tiny binary patch.

Commands:

```text
radiff2 old.bin new.bin
radiff2 -x old.bin new.bin
radiff2 -D -a <arch> -b <bits> old.bin new.bin
radiff2 -r old.bin new.bin > patch.r2
```

Then inspect the changed offset in both files:

```text
r2 -A old.bin
s <changed-offset-or-vaddr>
pd 12
aoj
```

Check whether the change flips a branch, NOPs a check, changes a constant,
changes a call target, or patches an immediate length.

### Firmware Revision

Goal: avoid drowning in container-level churn.

Commands:

```text
rabin2 -I firmware-old.bin
rabin2 -I firmware-new.bin
radiff2 -s firmware-old.bin firmware-new.bin
radiff2 -d firmware-old.bin firmware-new.bin
```

Then extract matching components and compare those:

```text
rahash2 -a sha256 component-old component-new
radiff2 -AC component-old component-new
radiff2 -z component-old component-new
```

Prioritize network daemons, parsers, update handlers, IPC services, web
interfaces, and privileged helpers.

### Import or Library Change

Goal: determine whether a patch moved logic into a library or changed dangerous
API usage.

Commands:

```text
radiff2 -i old.bin new.bin
radiff2 -z old.bin new.bin
rabin2 -ij old.bin > old.imports.json
rabin2 -ij new.bin > new.imports.json
rabin2 -lj old.bin > old.libs.json
rabin2 -lj new.bin > new.libs.json
```

Follow new or removed imports into xrefs:

```text
r2 -A new.bin
axt sym.imp.<import>
pdf @ <caller>
```

### Runtime Memory Change

Goal: compare state before and after a suspicious operation.

Commands:

```text
r2 -d ./target
db sym.parser
dc
cw <dst> <size> p8
dcu <after-copy>
cwu
cw
```

Use disassembly watchers for self-modifying or unpacking code:

```text
cw <code-addr> <size> pD
cwu
cw
```

Pair watcher output with debugger state: `dr`, `drr`, `dbt`, `dm. @ <addr>`, and
the input offset responsible for the change.

### Function Clone or Variant Diff

Goal: compare two similar functions inside one binary.

Commands:

```text
r2 -A target.bin
s sym.func_a
bf sym.func_a
cc sym.func_b @ sym.func_a
ccd sym.func_b @ sym.func_a
```

Use this for:

- Debug versus release paths.
- Safe versus unsafe parser variants.
- Architecture-specific dispatch functions.
- Old compatibility handler versus new handler.
- Similar command handlers with one missing authorization check.

### Zignature-Assisted Diff

Goal: match renamed or shifted functions across variants.

Commands:

```text
r2 -A old.bin
zaf sym.target target
zos old-target.sdb
```

Then:

```text
r2 -A new.bin
zo old-target.sdb
zb
zbr target 10
```

Use best-match scores as leads, not proof. Confirm with graph diff,
disassembly, xrefs, and behavior.

## Evidence Checklist

Collect:

- File identities: paths, hashes, sizes, versions, architecture, bits, format,
  stripped state, and build IDs when available.
- Pair order: which file is old/vulnerable and which file is new/patched.
- Diff commands: exact `radiff2`, `rabin2`, `rahash2`, and r2 commands used.
- Analysis settings: `-A` versus `-AA`, architecture, bits, physical versus
  virtual addressing, thresholds, graph mode, and sort field.
- Raw changes: offsets, byte values, unified diff, JSON, or patch script.
- Code changes: function names or offsets, graph similarity, changed basic
  blocks, changed conditions, changed calls, and changed constants.
- Metadata changes: imports, strings, libraries, sections, exports, symbols, and
  security-hardening fields.
- Reachability: xrefs, call paths, exposed inputs, runtime evidence, or debugger
  proof that the changed code affects attacker-controlled data.
- Impact reasoning: why the old behavior is vulnerable and how the new behavior
  mitigates or changes it.
- Limitations: stripped symbols, weak analysis, packed code, compiler churn,
  unrelated refactors, reordered functions, or unverified runtime behavior.

## Cautions

- A diff identifies change, not vulnerability. Connect the change to reachable
  behavior.
- Reordered, relinked, or rebuilt binaries can create noisy diffs. Use metadata
  and graph similarity to regain anchors.
- Analysis quality affects `-C` and `-g`. Record `-A`/`-AA` and verify important
  functions manually.
- Strings and imports can be optimized away, added by unrelated libraries, or
  hidden behind dynamic resolution.
- Virtual addresses and physical offsets answer different questions. Be explicit.
- Default byte diff can truncate different-size files. Use `-d` when insertions
  or deletions matter.
- Patch scripts mutate files. Apply only to copies and verify hashes.
- Graph output direction can affect visual interpretation. Record file order.
- Similarity thresholds can hide small but security-critical changes.
- Zignature matches and best-match scores are leads; verify before reporting.

## Official References

- https://book.rada.re/tools/radiff2/intro.html
- https://book.rada.re/tools/radiff2/datadiff.html
- https://book.rada.re/tools/radiff2/codediff.html
- https://book.rada.re/tools/radiff2/bindiff.html
- https://book.rada.re/tools/radiff2/binary_diffing.html
- https://book.rada.re/commandline/comparing_bytes.html
- https://book.rada.re/commandline/cmp_watchers.html
- https://book.rada.re/signatures/zignatures.html
