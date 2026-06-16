# Radare2 Search

Use radare2 search features to turn vague binary hypotheses into concrete
offsets, flags, code references, and follow-up targets. Prefer `rafind2` for
quick command-line searches across files or directories. Prefer the in-session
`/` command family when search hits need immediate context, flags, xrefs,
disassembly, ESIL, memory maps, or debugger state.

## Contents

- [Quick Commands](#quick-commands)
- [Rafind2 Command-Line Search](#rafind2-command-line-search)
- [In-Session Search Basics](#in-session-search-basics)
- [Search Ranges and Options](#search-ranges-and-options)
- [Strings, Regex, Bytes, and Values](#strings-regex-bytes-and-values)
- [Patterns, Magic, and File Carving](#patterns-magic-and-file-carving)
- [Assembly, References, and ESIL Search](#assembly-references-and-esil-search)
- [Gadget Search](#gadget-search)
- [Cryptographic Material and Entropy](#cryptographic-material-and-entropy)
- [Hit Automation](#hit-automation)
- [Vulnerability Research Search Sets](#vulnerability-research-search-sets)
- [Evidence Checklist](#evidence-checklist)
- [Official References](#official-references)

## Quick Commands

Command-line searches:

```bash
rafind2 -s "password" "$BIN"
rafind2 -S "ServiceName" "$BIN"
rafind2 -x "7f454c46" "$BIN"
rafind2 -e "https?://" "$BIN"
rafind2 -z "$BIN"
rafind2 -j -s "token" "$BIN"
```

In-session searches:

```text
/ password
/i password
/w ServiceName
/x 7f454c46
/e /https?:\/\//
/z 4 128
/m
/a call eax
/g pop;ret
/ca aes
```

Set search boundaries before expensive searches:

```text
e search.in=bin.sections.rx
e search.align=4
e search.maxhits=100
```

Inspect hits:

```text
fs searches
f~hit
px 64 @ hit0_0
ps @ hit0_0
pd 8 @ hit0_0
axt @ hit0_0
```

## Rafind2 Command-Line Search

`rafind2` is the command-line frontend for radare2's search engine. Use it when
you need fast offsets without opening an interactive session.

Common options:

- `-s <str>`: Search for an ASCII string. Can be repeated.
- `-S <str>`: Search for a wide string. Can be repeated.
- `-x <hex>`: Search for hex bytes. Can be repeated.
- `-e <regex>`: Search with a regular expression. Can be repeated.
- `-a <align>`: Only report aligned hits.
- `-f <from>` and `-t <to>`: Restrict the address or offset range.
- `-M <mask>`: Apply a binary mask to keyword searches.
- `-m`: Run magic/file-type carving.
- `-i`: Identify file type using radare2 magic.
- `-j`: Emit JSON.
- `-r`: Emit radare2 commands.
- `-X`: Show a hexdump around hits.
- `-z`: Search for zero-terminated strings.
- `-Z`: Show the string at each hit.
- `-n`: Continue across read errors.
- `-q`: Quiet output.

Examples:

```bash
rafind2 -s "Authorization" -s "Bearer" "$BIN"
rafind2 -e "sqlite|SELECT|INSERT|UPDATE" "$BIN"
rafind2 -x "41414141" -a 4 "$BIN"
rafind2 -m "$FIRMWARE"
rafind2 -z "$BIN" | rg -i "http|token|password|secret"
```

Use `rafind2` output as input to later context collection:

```bash
for off in $(rafind2 -s "token" "$BIN"); do
  r2 -q -n -s "$off" -c "px 64" -c "pd 8" -c q "$BIN"
done
```

Use `rafind2 -r` when hits should become flags in a reproducible r2 script.
Use `rafind2 -j` when search output will be stored in a finding packet or
processed by a script.

## In-Session Search Basics

Inside `r2`, search commands start with `/`. Search hits are normally flagged so
they can be referenced later.

Useful forms:

```text
/ foo\x00           search for a string
/j foo\x00          search for a string with JSON output
//                  repeat the last search
/i foo              case-insensitive string search
/w foo              wide string search
/wi foo             case-insensitive wide string search
/x 7f454c46         hex-byte search
/x ff..33           hex search with wildcard nibbles
/x ff43:ffd0        hex search with a mask
/e /regex/i         regular-expression search
/z 4 128            search for strings in a size range
```

Hit handling:

- Use `fs searches` to switch to the search flag space.
- Use `f~hit` or `f~search` to list generated hit flags.
- Use `ps @ hit0_0` for strings, `px 64 @ hit0_0` for bytes, and
  `pd 8 @ hit0_0` for nearby code.
- Use `axt @ hit0_0` to find xrefs to a hit after analysis has run.
- Use `s hit0_0` to seek to a hit.

Use `/b` to search backward from the current seek. It composes with other search
forms, such as `/bx 90` for backward hex-byte search.

## Search Ranges and Options

Always check the search range when expected hits are missing. The most important
setting is `search.in`.

Common range settings:

```text
e search.in=bin.sections      search recognized binary sections
e search.in=bin.sections.r    search readable sections
e search.in=bin.sections.rx   search executable sections
e search.in=bin.sections.rw   search writable sections
e search.in=io.maps           search all mapped IO regions
e search.in=io.maps.rw        search writable mapped regions
e search.in=dbg.maps          search all debugger maps
e search.in=dbg.heap          search debugger heap
e search.in=dbg.stack         search debugger stack
e search.in=anal.fcn          search current analyzed function
e search.in=anal.bb           search current analyzed basic block
```

Other useful options:

```text
e search.from=0
e search.to=0
e search.align=4
e search.flags=true
e search.maxhits=100
e search.overlap=true
e search.prefix=hit
e search.verbose=true
```

Use `search.align` when looking for pointers, integers, instruction patterns,
or structure fields that should be naturally aligned. Use `search.maxhits` to
keep broad regex or byte searches from flooding the session. Use `search.flags`
when hits need later xrefing, looping, or evidence capture.

For raw firmware, memory dumps, packed data, or nonstandard mappings, compare
results across `raw`, `io.maps`, and `bin.sections`-style ranges before
assuming there are no hits.

## Strings, Regex, Bytes, and Values

Use strings first when looking for feature names, protocol markers, error text,
routes, configuration keys, service identifiers, or hardcoded secrets:

```text
/ login
/i password
/w com.example.service
/e /https?:\/\//
/z 8 256
```

Use hex-byte search when searching magic values, encoded constants,
instruction bytes, serialized fields, or non-printable markers:

```text
/x 7f454c46
/x cafebabe
/x 504b0304
/x 30..02..30
/x ff43:ffd0
```

Use value search for integers and pointers. The `/v` and `/V` forms respect
`cfg.bigendian`.

```text
/v4 0x1000
/v8 0x4141414141414141
/V4 0x100 0x400
```

Use file-content search when a known blob, certificate, serialized fragment, or
payload file should appear inside a larger binary or memory image:

```text
/F known_blob.bin
/F known_blob.bin 0 128
```

Use hash search when the only known artifact is a digest:

```text
/h sha256 <digest> 512
```

## Patterns, Magic, and File Carving

Use pattern search to find repeated data without knowing the exact bytes:

```text
/p 16
/P 32
/d 0102
```

Use these when looking for:

- Repeated table rows, serialized records, dispatch entries, jump tables, or
  encoded configuration chunks.
- Repeated padding, key schedules, bytecode structures, or resource indexes.
- Differential byte patterns where adjacent bytes follow a recognizable delta.

Use magic search to identify embedded formats and filesystem fragments:

```text
/m
/M
rafind2 -m "$FIRMWARE"
```

Follow up on hits that indicate archives, images, certificates, compressed
streams, databases, bytecode, plist/XML/JSON stores, firmware partitions, or
nested executables. Confirm with `px`, `ps`, extraction tooling, or a narrower
`rafind2 -f/-t` search over the hit range.

## Assembly, References, and ESIL Search

Use assembly search when the bug hypothesis depends on machine-code behavior
rather than raw bytes:

```text
/a jmp eax           assemble an instruction and search for its bytes
/ad/ jmp qword [rdx] search disassembly text category/mnemonic matches
/c jmp [esp]         search assembly text matching a string
/A call              find analyzed instructions by operation type
```

Use opcode-reference search when locating code that references an address,
symbol, string, or imported API:

```text
/r sym.imp.strcpy
/r hit0_0
/re hit0_0
axt @ hit0_0
```

Use ESIL search when the condition is semantic rather than textual:

```text
/ce rsp,rbp
/E <esil-expression>
```

Search for code patterns that often matter in vulnerability research:

- Indirect calls or jumps: callbacks, vtables, dispatch tables, JITs, parser
  state machines, or attacker-influenced control flow.
- Stack pointer changes and frame pivots: exploitability, stack switching, or
  unusual ABI transitions.
- Writes through registers or computed pointers: potential memory corruption
  sinks.
- Bounds-check idioms and error paths: compare checked and unchecked parser
  branches.
- Syscall or privileged instruction use: sandbox, broker, driver, or low-level
  service boundaries.

Validate assembly-search hits with disassembly and xrefs. Raw instruction bytes
can appear inside data, and text matches can miss equivalent instruction forms.

## Gadget Search

Use `/g` for gadget discovery. The old `/R` form is obsolete in current radare2
documentation.

```text
/g              list gadgets in the current search range
/g pop;ret      filter gadgets by opcode substrings
/gR pop;ret     return-terminated gadgets
/gC call        call-terminated gadgets
/gJ jmp         jump-terminated gadgets
/gj pop;ret     JSON output
/gq pop;ret     quiet address/size output
/g* pop;ret     radare2 command output
```

Tune gadget searches:

```text
e gadget.len=5
e gadget.cond=true
e gadget.esil=true
e gadget.subchains=true
e gadget.comments=true
```

Use gadget classes in JSON output to prioritize useful primitives:

- `pivot`: stack pointer changes.
- `memread` and `memwrite`: memory access side effects.
- `rww`: read-what-where style primitive.
- `syscall`: syscall or software interrupt.
- `jop` and `cop`: jump-oriented or call-oriented candidates.

Treat gadget availability as exploitability support, not a finding by itself.
Restrict gadget searches to executable ranges and record architecture, bitness,
base address, and binary hash when preserving evidence.

## Cryptographic Material and Entropy

Use crypto-specific search for expanded keys, certificates, and private keys:

```text
/ca aes
/ca sm4
/cr
/cd
```

Important caveat: `/ca` searches expanded AES/SM4 key schedules, not arbitrary
plaintext keys. A miss does not prove keys are absent.

Use entropy search for packed, encrypted, or compressed regions:

```text
b 4096
/s
/s*
./s*
px 32 @@ entropy*
```

Use hash matching when validating that a known block, embedded artifact, or
malware/config fragment appears in the target:

```text
/h sha256 <digest> 512
```

Follow up crypto and entropy hits with section metadata, xrefs, nearby strings,
imports, and runtime behavior. High entropy can indicate compression or media
data, not only secrets or encryption.

## Hit Automation

Use `cmd.hit` to run a command on every search hit:

```text
e cmd.hit='px 32'
/ token
```

For multiple commands, use semicolons or a script:

```text
e cmd.hit='?v $$; px 32; pd 6'
/x 504b0304
```

Use this to capture context while searching:

- `px 64`: bytes around the hit.
- `ps`: string at the hit.
- `pd 8`: nearby disassembly.
- `axt`: xrefs to the hit after analysis.
- `?v $$`: current address in a stable numeric form.

Prefer JSON forms (`/j`, `/gj`, `rafind2 -j`) when a script will post-process
hits. Prefer flag output (`/g*`, `rafind2 -r`) when hits should be imported into
an r2 session.

## Vulnerability Research Search Sets

Suspicious input and parser surface:

```text
/i parse
/i decode
/i deserialize
/i inflate
/i unpack
/e /(xml|json|asn1|protobuf|pickle|yaml|plist)/i
```

Command execution and script injection:

```text
/i system
/i exec
/i powershell
/i cmd.exe
/i /bin/sh
/e /(%s|%q|shell|script|spawn|popen)/i
```

Path traversal and file handling:

```text
/ ../
/ ..\\
/i tempfile
/i download
/i upload
/e /(open|read|write|rename|delete|mkdir|symlink)/i
```

Format strings and logging:

```text
/ %n
/ %s
/ %p
/e /printf|sprintf|snprintf|NSLog|syslog|OutputDebugString/i
```

Secrets, credentials, and tokens:

```text
/i password
/i secret
/i token
/i bearer
/i private key
/e /(api[_-]?key|client[_-]?secret|authorization|cookie)/i
```

IPC, services, and privilege boundaries:

```text
/i ioctl
/i xpc
/i dbus
/i com.
/i service
/i entitlement
/e /(broker|sandbox|policy|privilege|admin|root|setuid)/i
```

Crypto and certificate handling:

```text
/i aes
/i rsa
/i ecdsa
/i certificate
/i verify
/i trust
/ca aes
/cr
/cd
```

Use these as starting points only. For each hit, determine whether attacker
controlled input can reach the code or data that references it.

## Evidence Checklist

Capture:

- Binary path, hash, architecture, bitness, and base-address assumptions.
- Search command, `search.in`, `search.from`, `search.to`, `search.align`, and
  `search.maxhits` settings.
- Hit offsets, generated flag names, and whether offsets are virtual or
  physical.
- Context around each relevant hit: bytes, string, disassembly, xrefs, function
  name, and section/map permissions.
- JSON output for scripted searches and r2 command output for imported flags.
- Notes explaining why a hit is a lead, confirmed issue, or false positive.

## Official References

- https://book.rada.re/tools/rafind2/intro.html
- https://book.rada.re/search/intro.html
- https://book.rada.re/search/basic_searches.html
- https://book.rada.re/search/search_options.html
- https://book.rada.re/search/pattern_search.html
- https://book.rada.re/search/automation.html
- https://book.rada.re/search/backward_search.html
- https://book.rada.re/search/search_in_assembly.html
- https://book.rada.re/search/rop_gadgets.html
- https://book.rada.re/search/searching_crypto.html
