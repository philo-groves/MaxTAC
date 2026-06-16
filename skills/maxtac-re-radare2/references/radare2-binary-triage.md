# Radare2 Binary Triage

Use `rabin2` for fast, scriptable binary inventory before deeper reverse
engineering. Prefer it when the immediate questions are: what format is this,
what hardening is present, what code/data regions exist, which external APIs are
used, are symbols or debug metadata available, and what initial strings or
entrypoints deserve follow-up.

## Contents

- [Quick Commands](#quick-commands)
- [Output Modes](#output-modes)
- [Header and Hardening Fields](#header-and-hardening-fields)
- [Entrypoints and Startup Code](#entrypoints-and-startup-code)
- [Imports, Exports, Symbols, and Libraries](#imports-exports-symbols-and-libraries)
- [Sections, Segments, and Relocations](#sections-segments-and-relocations)
- [Strings](#strings)
- [Debug Symbols and PDBs](#debug-symbols-and-pdbs)
- [Fat Binaries and Embedded Files](#fat-binaries-and-embedded-files)
- [Interactive Radare2 Equivalents](#interactive-radare2-equivalents)
- [Vulnerability Research Notes](#vulnerability-research-notes)
- [Evidence Checklist](#evidence-checklist)
- [Official References](#official-references)

## Quick Commands

Start with a compact profile:

```bash
rabin2 -I "$BIN"
rabin2 -Ij "$BIN"
```

Pull the first useful attack-surface summary:

```bash
rabin2 -I -e -M -l -i -E -s -S -SS -R -z "$BIN"
```

Use JSON for automation and evidence bundles:

```bash
rabin2 -Ij "$BIN"      # binary info / hardening / format data
rabin2 -ij "$BIN"      # imports
rabin2 -Ej "$BIN"      # exports
rabin2 -sj "$BIN"      # symbols
rabin2 -Sj "$BIN"      # sections
rabin2 -lj "$BIN"      # linked libraries
rabin2 -zj "$BIN"      # parsed strings
```

Generate radare2 commands that can be imported into a later `r2` session:

```bash
rabin2 -Ir "$BIN"      # analysis/config hints
rabin2 -er "$BIN"      # entrypoint flags and seek
rabin2 -sr "$BIN"      # symbol flags and ranges
rabin2 -zr "$BIN"      # string flags and ranges
```

## Output Modes

- Use plain text for quick human triage and shell filtering.
- Add `-j` for JSON whenever another tool, script, or finding ledger will
  consume the output.
- Add `-r` when the output should become an r2 script or session setup.
- Add `-q` or `-qq` to reduce headings in logs where stable parsing matters.
- Use `-n <name>` or `-@ <addr>` to answer narrow questions about a specific
  symbol, import, section, or address.

## Header and Hardening Fields

Run:

```bash
rabin2 -I "$BIN"
```

Record these fields when present:

- `arch`, `bits`, `endian`, `machine`, `os`, `subsys`: architecture and ABI
  assumptions for later disassembly, emulation, and exploitability checks.
- `bintype`, `class`, `lang`, `havecode`, `va`: container format, code
  presence, language hints, and virtual-address behavior.
- `binsz`, `static`, `stripped`, `lsyms`, `linenum`: file size, linking model,
  and symbol/debug metadata expectations.
- `intrp`, `rpath`, `runpath`: dynamic loader and library search-path signals.
- `nx`, `canary`, `relro`, `pic` or `pie`: common hardening flags.
- `crypto`: weak signal only; use it as a hint to inspect strings/imports and
  crypto searches, not as proof that cryptography is or is not relevant.

Interpretation notes:

- Missing `nx`, missing `canary`, weak `relro`, or non-PIE state can matter for
  exploitability, but do not make a bug by themselves.
- `rpath` or `runpath` values outside trusted system paths can point to library
  hijacking or packaging mistakes.
- `stripped=true` means source-level names may be absent; lean harder on
  imports, strings, xrefs, and function-shape analysis.
- `static=true` can hide external API boundaries inside the binary; expect more
  code and fewer useful imports.
- For PIE or rebased samples, use `-B <addr>` to override the base address when
  correlating offsets with a debugger, crash, or memory map.

## Entrypoints and Startup Code

Run:

```bash
rabin2 -e "$BIN"
rabin2 -ee "$BIN"
rabin2 -M "$BIN"
```

Use `-e` for program entrypoints, `-ee` for constructor/destructor entrypoints,
and `-M` for the main symbol when it can be recovered. Follow up on:

- Custom or unusual entrypoints.
- Constructors that parse configuration, environment variables, command-line
  arguments, IPC endpoints, plugins, or sandbox policy before `main`.
- Multiple entrypoints in firmware, loaders, fat binaries, packed samples, or
  unusual object formats.

When a later r2 session should start at the same location, save:

```bash
rabin2 -er "$BIN"
```

## Imports, Exports, Symbols, and Libraries

Run:

```bash
rabin2 -i "$BIN"       # imports
rabin2 -E "$BIN"       # exports
rabin2 -s "$BIN"       # symbols
rabin2 -l "$BIN"       # linked libraries
rabin2 -D all "$BIN"   # demangle when supported
```

Imports are one of the fastest ways to classify behavior. Prioritize follow-up
when imports suggest:

- Memory hazards: `strcpy`, `strcat`, `sprintf`, `gets`, `memcpy`, custom
  allocators, parser or decompression libraries.
- Command or process execution: `system`, `popen`, `exec*`, `CreateProcess*`,
  `ShellExecute*`, script engine APIs.
- Filesystem and path handling: `open`, `fopen`, `CreateFile*`, archive APIs,
  symlink or temporary-file functions.
- Network and IPC surface: sockets, HTTP/RPC libraries, D-Bus, XPC, COM, named
  pipes, shared memory, ioctl-facing APIs.
- Privilege or sandbox boundaries: `setuid`, token APIs, entitlement or code
  signing APIs, authentication/authorization libraries.
- Deserialization and parsing: XML, JSON, ASN.1, image/media codecs, archive,
  compression, protobuf, pickle-like, or object-stream APIs.
- Crypto and secrets handling: OpenSSL/CommonCrypto/BCrypt/CNG calls, keychain
  APIs, certificate parsing, password hashing.

Exports and symbols identify callable surface and semantic anchors. Prioritize:

- Exported plugin, extension, RPC, JNI, COM, Objective-C, Swift, driver, or
  service-entry functions.
- Names containing `parse`, `decode`, `deserialize`, `load`, `import`,
  `verify`, `auth`, `token`, `policy`, `sandbox`, `ipc`, `message`, `ioctl`,
  `copy`, `unpack`, `inflate`, `compress`, or `crypto`.
- Large or complex exported functions, especially when paired with unsafe
  imports or attacker-reachable file/network inputs.

Linked libraries help classify the binary before disassembly:

- GUI-only libraries may lower remote attack-surface priority unless file
  handlers or IPC imports are present.
- Parser, codec, archive, font, image, database, scripting, or network libraries
  usually deserve immediate source/sink mapping.
- Unexpected private or writable-path libraries can indicate search-path risk.

## Sections, Segments, and Relocations

Run:

```bash
rabin2 -S "$BIN"       # sections
rabin2 -SS "$BIN"      # segments
rabin2 -SSS "$BIN"     # section-to-segment mapping
rabin2 -R "$BIN"       # relocations
```

Use sections and segments to identify:

- Writable and executable regions, or sections with surprising permissions.
- Large executable regions that may contain packed or generated code.
- Unusual named sections, custom metadata, resources, or embedded blobs.
- Code/data address ranges for targeted search and later analysis boundaries.
- Relocation-heavy code paths, dynamic dispatch tables, imported function
  pointers, callback tables, or C++/Objective-C runtime structures.

Follow up when:

- A writable section is executable, or an executable section appears writable in
  loaded mappings.
- `.init`, `.fini`, constructors, TLS callbacks, Mach-O init arrays, or PE TLS
  callbacks perform parsing or security decisions before normal startup.
- A section name implies compression, encryption, bytecode, policy, plugins,
  scripts, firmware partitions, or serialized configuration.

## Strings

Run:

```bash
rabin2 -z "$BIN"       # parsed strings from recognized data/code sections
rabin2 -zz "$BIN"      # raw strings
rabin2 -zzz "$BIN"     # raw strings to stdout for very large files
```

Adjust string behavior when needed:

```bash
RABIN2_DEBASE64=1 rabin2 -z "$BIN"
RABIN2_STRFILTER=?? rabin2 -z "$BIN"
rabin2 -N 4:256 -z "$BIN"
```

Prioritize strings that reveal:

- File formats, magic values, protocol verbs, routes, IPC names, registry keys,
  plist keys, entitlement names, or service identifiers.
- Error messages near parsing, authorization, sandbox, crypto, update, plugin,
  decompression, or deserialization code.
- Hardcoded credentials, tokens, private endpoints, certificate material, test
  keys, debug flags, or feature gates.
- Format strings, shell snippets, command templates, path templates, SQL/LDAP
  fragments, JavaScript snippets, or unsafe interpreter inputs.

Use `-zr` when string offsets should become flags in a follow-up r2 session.
Use raw strings (`-zz`) when the binary is packed, section metadata is missing,
or the file is firmware/flat/raw data rather than a normal executable.

## Debug Symbols and PDBs

Run:

```bash
rabin2 -d "$BIN"       # DWARF/debug information
rabin2 -P "$BIN"       # PDB information
rabin2 -PP "$BIN"      # attempt PDB download when appropriate
```

Notes:

- DWARF is commonly embedded in the executable or separate debug files.
- PDB data is usually external; radare2 can use symbol-server settings such as
  `pdb.server` to locate it.
- Treat downloaded symbols as analysis aids, not trust anchors. Record symbol
  server, GUID/signature, and binary hash when evidence quality matters.
- If symbols are available, preserve function names, source paths, line info,
  type names, and structure names that explain reachability or security intent.

## Fat Binaries and Embedded Files

Run:

```bash
rabin2 -A "$BIN"       # list sub-binaries and arch/bit pairs
rabin2 -f <name> "$BIN"
rabin2 -x "$BIN"       # extract contained binaries when useful
```

Use this for Mach-O universal binaries, firmware containers, archives, installer
payloads, packed resources, or multi-architecture samples. Triage each relevant
architecture separately; hardening, imports, and strings can differ by slice.

## Interactive Radare2 Equivalents

Inside `r2`, use the `i` command family for similar information:

```text
iI      binary info
ie      entrypoints
ii      imports
iE      exports
is      symbols
iS      sections
iSS     segments
il      linked libraries
iz      strings
iR      relocations
i?      list other info commands
```

Use external `rabin2` when collecting a broad first-pass inventory or scripting
many binaries. Use interactive `i*` commands when already inside an analysis
session and correlating metadata with xrefs, disassembly, or debugger state.

## Vulnerability Research Notes

Use triage output to form hypotheses, not conclusions:

- Import presence suggests capability, not reachability. Confirm with xrefs,
  call graph analysis, or dynamic traces.
- Strings suggest features and inputs. Confirm how the string is referenced and
  whether attacker-controlled data can reach that path.
- Hardening flags affect exploitability and proof strategy. They do not prove
  memory safety or lack of impact.
- Debug symbols and demangled names can be stale, misleading, or stripped from
  release builds. Verify behavior in code.
- Section permissions and relocation data are strong leads for exploitability,
  packers, loaders, hooks, dispatch tables, and writable function pointers.

Good first questions:

- Which externally controlled inputs exist: files, network, IPC, environment,
  command line, registry/plist/config, plugins, updates, or device IO?
- Which imports or symbols operate on those inputs before authentication,
  sandboxing, bounds checks, or signature verification?
- Which exported functions or entrypoints are callable by lower-privileged
  users or remote peers?
- Which hardening flags will shape crash proofing or exploitability claims?

## Evidence Checklist

Capture enough context to make later analysis reproducible:

- Binary path, file hash, size, timestamp, package/version, and source URL or
  acquisition method.
- `rabin2 -Ij` output.
- `rabin2 -ij -Ej -sj -lj -Sj -SSj -Rj -zj` output when relevant.
- Entrypoints, constructors/destructors, main address, and any unusual section
  or segment permissions.
- Debug-symbol source and whether symbols were embedded, local, or downloaded.
- Notable imports, exports, strings, and sections with short analyst notes.
- Any base-address override used for correlating crash/debugger evidence.

## Official References

- https://book.rada.re/tools/rabin2/intro.html
- https://book.rada.re/tools/rabin2/headers.html
- https://book.rada.re/tools/rabin2/entrypoints.html
- https://book.rada.re/tools/rabin2/imports.html
- https://book.rada.re/tools/rabin2/symbols.html
- https://book.rada.re/tools/rabin2/debug_symbols.html
- https://book.rada.re/tools/rabin2/libraries.html
- https://book.rada.re/tools/rabin2/strings.html
- https://book.rada.re/tools/rabin2/program_sections.html
