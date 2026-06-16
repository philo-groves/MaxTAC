# JADX Search, Renaming, and Mappings

Use this reference when names, aliases, mappings, GUI search results, comments,
or deobfuscation output affect the analysis. Always separate raw identities from
JADX aliases. A readable name is a lead until it is tied back to the original
class, method, field, resource, or dex offset.

## Contents

- [Quick Commands](#quick-commands)
- [Raw Names, Aliases, and Evidence](#raw-names-aliases-and-evidence)
- [GUI Search Semantics](#gui-search-semantics)
- [Rename Flags and Filesystem Case](#rename-flags-and-filesystem-case)
- [User Mappings](#user-mappings)
- [Generated JOBF Mappings](#generated-jobf-mappings)
- [Source Name and Kotlin Name Aids](#source-name-and-kotlin-name-aids)
- [Comments and Project Code Data](#comments-and-project-code-data)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

Disable all safety renames to compare raw names:

```bash
jadx --rename-flags none -d out-rawnames app.apk
```

Use only valid/printable identifier fixes:

```bash
jadx --rename-flags valid,printable -d out-valid app.apk
```

Enable deobfuscation with stable generated mapping behavior:

```bash
jadx --deobf \
  --deobf-cfg-file case.jobf \
  --deobf-cfg-file-mode read-or-save \
  -d out-deobf app.apk
```

Load user mappings:

```bash
jadx --mappings-path mappings.tiny --mappings-mode read -d out-mapped app.apk
```

Control source-name aliases:

```bash
jadx --use-source-name-as-class-name-alias if-better \
  --source-name-repeat-limit 10 \
  -d out app.apk
```

## Raw Names, Aliases, and Evidence

JADX APIs expose several identities:

- Class raw name.
- Class full name.
- Alias full name.
- Field/method raw names and aliases.
- Method short IDs and full IDs.
- Resource original name and deobfuscated alias.

Evidence guidance:

- Record raw and alias names for every class/method/field in a finding.
- Use method short signatures for overloaded methods.
- Keep mappings files with reports and scripts.
- When a stack trace, crash log, or runtime class name uses raw names, do not
  translate it silently. Show the mapping.
- When a GUI result came from an alias search, verify the raw node before
  reporting.

## GUI Search Semantics

JADX GUI search is not one generic grep. Different providers search different
data and can trigger decompilation or resource loading.

Class search matches:

- Short class name.
- Full class name.
- Alias full name.
- Raw name.

Method search matches:

- Method short ID.
- Method alias.
- Method full ID.
- Alias full name.

Field search matches:

- Field name.
- Field alias.
- Field full ID.

Code search:

- Reads from the code cache when available.
- Decompiles top-level classes as needed.
- Resolves enclosing nodes through code metadata.
- Can force decompilation of classes excluded from the current package filter.

Comment search:

- Reads comments from project code data.
- Resolves class, field, and method references back to nodes.
- Can resolve code comments to instruction offsets through `InsnCodeOffset`.

Resource search:

- Loads resource nodes.
- Applies resource type and extension filters.
- Applies a resource size limit.
- Reports resource load errors and size-limit skips.

Guidance:

- Capture search scope, string, case/regex settings if used, active package
  filters, resource filters, and size limits.
- Reproduce reportable hits with CLI/API output when possible.
- Treat code search as a decompilation action. It can populate caches and expose
  decompiler errors.

## Rename Flags and Filesystem Case

`--rename-flags` controls automatic fixes:

```text
case       fix case-sensitivity issues according to --fs-case-sensitive
valid      make Java identifiers valid
printable  remove non-printable characters
none       disable all rename fixes
all        enable all fixes
```

JADX defaults to all rename fixes and treats the filesystem as not
case-sensitive unless `--fs-case-sensitive` is set.

Use cases:

- `none`: compare raw obfuscated names, reproduce stack traces, or detect
  collisions.
- `valid,printable`: keep output parsable without case-collision changes.
- `all`: normal analyst reading.
- `--fs-case-sensitive`: use when output paths will be stored on a
  case-sensitive filesystem and case collisions matter.

Record these flags whenever file paths, class names, or compileability are part
of the finding.

## User Mappings

`--mappings-path` points to a deobfuscation mappings file or directory. CLI help
explicitly lists Tiny/Tiny v2 and Enigma file/directory formats. The bundled
rename-mappings plugin exposes additional format controls through
`-Prename-mappings.format`, including AUTO and many common mapping families.

Modes:

```text
read
read-and-autosave-every-change
read-and-autosave-before-closing
ignore
```

Guidance:

- Use `read` for evidence runs where mappings should not mutate.
- Use autosave modes only when the GUI workflow intentionally edits mappings.
- Use `ignore` to avoid project-file referenced mappings in a clean run.
- Preserve mapping file hash and whether the mapping was inverted.

Plugin options:

```bash
jadx -Prename-mappings.format=AUTO --mappings-path mapping.txt app.apk
jadx -Prename-mappings.invert=yes --mappings-path mapping.txt app.apk
```

## Generated JOBF Mappings

JADX generated deobfuscation uses a JOBF mapping file:

```bash
jadx --deobf \
  --deobf-cfg-file app.jobf \
  --deobf-cfg-file-mode read-or-save \
  app.apk
```

Modes:

```text
read          read if found, do not save
read-or-save  read if found, otherwise save without overwrite
overwrite     do not read, always save
ignore        do not read and do not save
```

Guidance:

- Use `read-or-save` for first-run stabilization.
- Use `read` when reproducing a report with a known mapping file.
- Use `overwrite` only when intentionally regenerating aliases.
- Never compare two JADX deobfuscation outputs without preserving both JOBF
  files and modes.

## Source Name and Kotlin Name Aids

Class aliases can use source file names:

```text
--use-source-name-as-class-name-alias always|if-better|never
--source-name-repeat-limit <n>
```

Kotlin-aware naming:

```text
--use-kotlin-methods-for-var-names disable|apply|apply-and-hide
-Pkotlin-metadata.method-args=yes|no
-Pkotlin-metadata.fields=yes|no
-Pkotlin-smap.class-alias-source-dbg=yes|no
```

Guidance:

- Source filenames are useful for stack trace and source map correlation, but
  can collide heavily in obfuscated apps.
- Lower the repeat limit only after checking collision impact.
- Avoid hiding Kotlin intrinsic methods when proving data flow through those
  calls.
- Treat Kotlin metadata names as recovered labels, not source-of-truth behavior.

## Comments and Project Code Data

GUI projects store code data containing comments and renames. The project file
uses serialized comment and rename references tied to Java node refs and
optional code refs.

Use comments for analyst notes:

- Why a name was assigned.
- Whether a branch or sink was verified against smali.
- Which runtime test produced a value.
- Whether a mapping was imported or manually edited.

Evidence rule:

- Export or preserve the `.jadx` project file when comments/renames affect a
  finding.
- Do not rely on local GUI state alone. Pair it with CLI/API artifacts.

## Evidence Checklist

Capture:

- Raw names, aliases, short IDs, full IDs, and resource original names.
- `--rename-flags`, `--fs-case-sensitive`, source-name alias options, and
  Kotlin naming options.
- User mappings path, format, mode, invert flag, and file hash.
- JOBF mapping path, mode, and file hash.
- GUI project file if comments or manual renames were used.
- Search query, provider/scope, filters, resource size limit, and whether search
  forced decompilation or resource loading.

## Official Source Paths

- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-cli/src/main/java/jadx/cli/JadxCLIArgs.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/JadxArgs.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/data/ICodeData.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/data/ICodeRename.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/data/impl/JadxCodeData.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/settings/JadxProject.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/search/providers/ClassSearchProvider.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/search/providers/CodeSearchProvider.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/search/providers/CommentSearchProvider.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/search/providers/ResourceSearchProvider.java
