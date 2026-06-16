# Ghidra Diffing, Version Tracking, and BSim

Use this reference when comparing vulnerable and patched binaries, carrying
markup between versions, finding similar functions, or building patch-diff
evidence. Ghidra has three different comparison families: Program Diff/Function
Comparison for direct comparison, Version Tracking for structured markup
transfer, and BSim for function similarity at scale.

## Contents

- [Quick Decision](#quick-decision)
- [Program Diff](#program-diff)
- [Function Comparison and CodeCompare](#function-comparison-and-codecompare)
- [Version Tracking](#version-tracking)
- [Auto Version Tracking Script](#auto-version-tracking-script)
- [BSim](#bsim)
- [Patch-Diff Workflow](#patch-diff-workflow)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Decision

Use Program Diff when:

- You have two programs open and need direct address/data/symbol differences.
- You need to inspect or apply differences inside Ghidra.
- Address layouts are comparable enough for direct diffing.

Use Function Comparison when:

- You already know which functions to compare.
- You need side-by-side listing/decompiler comparison.
- You are reviewing a small patch or candidate match.

Use Version Tracking when:

- The goal is matching source and destination program functions/data.
- You need correlators, accepted matches, markup items, and transfer workflow.
- Addresses changed and direct diffing is too brittle.

Use BSim when:

- You need similarity across many binaries.
- You need to identify reused library or vulnerable functions.
- You need a queryable function-signature database.

## Program Diff

Program Diff is direct binary database comparison. Relevant upstream surfaces:

```text
Ghidra/Features/ProgramDiff
ProgramDiffPlugin
ProgramDiff
ProgramDiffFilter
ProgramDiffDetails
ListingDiff
MemoryDiff
```

Use it for:

- Symbol/name/comment differences.
- Memory and code-unit differences.
- Direct same-base patch review.
- Small binary revisions where addresses mostly align.

Be careful:

- Direct address diffing can miss moved functions.
- Analysis differences can look like patch differences.
- Manual markup differences are not necessarily binary changes.
- Import both programs with comparable loader/language/compiler settings.

## Function Comparison and CodeCompare

Function Comparison/CodeCompare gives side-by-side views, including listing and
decompiler-oriented comparison where available.

Relevant upstream surfaces:

```text
FunctionComparisonPlugin
FunctionComparisonService
DecompilerCodeComparisonView
ListingDiffActionManager
```

Use it after selecting candidate functions from:

- Patch release notes.
- Version Tracking matches.
- BSim matches.
- Exported symbol names.
- Instruction pattern hits.
- Crash or sink functions.

Evidence should include:

- Source and destination function entry addresses.
- Function names and sizes.
- Whether functions were matched by symbol, exact bytes, exact instructions,
  BSim, manual review, or another correlator.
- Decompiled diff as supporting evidence only; preserve listing/bytes.

## Version Tracking

Version Tracking (VT) creates sessions between a source and destination program.
The upstream workflow emphasizes preconditions: both binaries should be
sufficiently and comparably analyzed before correlators run.

Recommended correlator order from upstream workflow:

1. Exact Data Match.
2. Exact Function Bytes.
3. Exact Function Instructions.
4. Symbol Match.
5. Duplicate exact correlators as needed.
6. Less exact correlators only after obvious matches are accepted.

Why:

- Exact unique matches are strong and allow automated markup transfer.
- Accepted matches can improve later correlators.
- Duplicate matches need manual review.
- Less exact matches require more caution before accepting/applying markup.

Check:

- Precondition warnings.
- Percent analyzed.
- Function counts.
- Red flags.
- No-return function issues.
- Offcut references.
- Memory block/layout differences.
- Length deltas, especially for symbol matches.

Do not blindly apply markup from a vulnerable source into a patched destination.
The markup itself can bias later analysis.

## Auto Version Tracking Script

`AutoVersionTrackingScript.java` can run VT from GUI or headless mode.

Headless local-project pattern:

```bash
analyzeHeadless ./projects Case001/DestFolder \
  -process DestinationProgram.exe \
  -postScript SetAutoVersionTrackingOptionsScript.java \
  -postScript AutoVersionTrackingScript.java \
    "/VTSessions" \
    "Case001VT" \
    "/SourceFolder/SourceProgram.exe"
```

Important upstream constraints:

- The current program is the destination program.
- The source program must already be imported and analyzed.
- The destination program is analyzed by the headless run unless `-noanalysis`
  is used.
- The script creates a new session; it cannot run using an existing session.
- An optional options setup script can put an options map into script state.
- Shared project mode requires source and destination programs in version
  control and additional connect/commit arguments.

Use AutoVT for repeatability, but preserve the session and script logs. Human
review is still needed for non-exact or suspicious matches.

## BSim

BSim supports function similarity and database-backed search.

Relevant command-line utilities:

```text
bsim_ctl
bsim
```

`bsim_ctl` manages PostgreSQL-backed BSim servers:

```bash
bsim_ctl start /data/bsim --auth trust
bsim_ctl status /data/bsim
bsim_ctl stop /data/bsim
```

`bsim` manages databases, signatures, metadata, and queries:

```bash
bsim createdatabase postgresql://localhost/repo medium_64
bsim generatesigs ghidra:/path/to/project/Case001 /tmp/sigs --config medium_64
bsim commitsigs postgresql://localhost/repo /tmp/sigs
bsim listexes postgresql://localhost/repo --name target
bsim listfuncs postgresql://localhost/repo --md5 <md5>
bsim dumpsigs postgresql://localhost/repo /tmp/sigs --md5 <md5>
```

BSim URL families include PostgreSQL, HTTPS, and local file/H2 style backends.
The upstream command-line docs warn that placing passwords in URLs is
discouraged because URLs can persist in process tables and logs.

Useful scripts:

```text
CreateH2BSimDatabaseScript.java
AddProgramToH2BSimDatabaseScript.java
GenerateSignatures.java
DumpBSimSignaturesScript.java
CompareBSimSignaturesScript.java
CompareExecutablesScript.java
LocalBSimQueryScript.java
QueryFunction.java
QueryWithFiltersScript.java
UpdateBSimMetadata.java
```

Use BSim to find candidates. Confirm candidates with function comparison,
xrefs, and raw bytes before reporting reuse or patch relevance.

## Patch-Diff Workflow

1. Hash both binaries and preserve originals.
2. Import both with the same Ghidra version and comparable settings.
3. Record loader, language, compiler spec, analysis options, and debug symbols.
4. Run comparable analysis.
5. Use exact symbols/exports/known crash offsets to seed obvious pairs.
6. Use Function Comparison for direct candidates.
7. Use Version Tracking when addresses/functions shifted.
8. Use BSim when candidate functions are unknown or there are many binaries.
9. For changed functions, preserve:
   - Function entries and sizes.
   - Raw bytes.
   - Disassembly.
   - Decompiler output with address mapping.
   - Xrefs/callers/callees.
   - Patch-introduced checks or removed sinks.
10. Validate exploitability with runtime evidence when static diff only shows a
    possible fix.

## Evidence Checklist

Capture:

- Ghidra version and analysis settings for both binaries.
- Source/destination hashes and import settings.
- Matching method: exact, symbol, VT correlator, BSim, manual, or mixed.
- VT session file and accepted/applied match status.
- Correlators run and order.
- BSim database URL/config, signature generation commands, and query results.
- Function comparison artifacts.
- Raw byte/disassembly diff around important changes.
- Decompiler output with mapped addresses.
- Limitations: analysis mismatch, moved code, duplicate matches, unmatched
  functions, debug symbol mismatch, or BSim false positives.

## Official Source Paths

- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/ProgramDiff/src/main/help/help/topics/Diff/Diff.htm
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/Base/src/main/help/help/topics/FunctionComparison/FunctionComparison.htm
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/VersionTracking/src/main/help/help/topics/VersionTrackingPlugin/VT_Workflow.html
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/VersionTracking/ghidra_scripts/AutoVersionTrackingScript.java
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/BSim/src/main/help/help/topics/BSim/CommandLineReference.html
- https://github.com/NationalSecurityAgency/ghidra/blob/6960dd5e19b1c6f866df1a1b91b3f1783ead6e29/Ghidra/Features/BSim/ghidra_scripts/CompareExecutablesScript.java
