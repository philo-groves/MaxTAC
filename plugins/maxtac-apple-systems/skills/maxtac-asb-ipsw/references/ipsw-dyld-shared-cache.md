# IPSW dyld Shared Cache

Use this reference when extracting or triaging iOS userspace frameworks,
private frameworks, Objective-C/Swift metadata, symbols, strings, imports, or
cross-version dyld shared cache changes.

## Contents

- [Quick Commands](#quick-commands)
- [Cache Handling](#cache-handling)
- [Extracted Dylibs](#extracted-dylibs)
- [Metadata Search](#metadata-search)
- [Address and Symbol Workflows](#address-and-symbol-workflows)
- [Class and Swift Dumps](#class-and-swift-dumps)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

Extract a cache from firmware:

```bash
ipsw extract --dyld --dyld-arch arm64e -o dyld/ firmware.ipsw
ipsw extract --dyld --driverkit -o dyld-driverkit/ macOS.ipsw
```

Inspect cache contents:

```bash
ipsw dyld info dyld_shared_cache_arm64e --dylibs --json > dsc-dylibs.json
ipsw dyld info dyld_shared_cache_arm64e --closures > dsc-closures.txt
ipsw dyld info dyld_shared_cache_arm64e --sig > dsc-codesig.txt
```

Extract one or many dylibs:

```bash
ipsw dyld extract dyld_shared_cache_arm64e /System/Library/Frameworks/Foundation.framework/Foundation -o dylibs/
ipsw dyld extract dyld_shared_cache_arm64e Foundation -o dylibs/
ipsw dyld extract dyld_shared_cache_arm64e --all --objc --stubs --slide -o dylibs-all/
```

Inspect an in-cache dylib without extraction:

```bash
ipsw dyld macho dyld_shared_cache_arm64e /System/Library/Frameworks/Foundation.framework/Foundation --loads --symbols --strings --json
ipsw dyld macho dyld_shared_cache_arm64e UIKitCore --objc --objc-refs --swift --starts
```

Search:

```bash
ipsw dyld str dyld_shared_cache_arm64e "NSFileProtectionComplete"
ipsw dyld str dyld_shared_cache_arm64e --pattern "TCC|Transparency"
ipsw dyld search --class '.*UserClient.*'
ipsw dyld search --sel '.*set.*Delegate.*'
ipsw dyld search --section '__DATA_CONST.*'
```

## Cache Handling

Keep all sibling cache files and subcache files together. Modern dyld shared
caches may depend on nearby cache files, symbols, or architecture-specific
companions. Moving only the visible `dyld_shared_cache_arm64e` file can break
metadata resolution or confuse later tools.

Record:

- Cache filename and hash.
- Extraction command and `--dyld-arch` value.
- Whether it came from IPSW, OTA, DriverKit, Exclave, simulator, or macOS.
- Any sibling files retained with the cache.
- The `ipsw dyld info --json` or `--dylibs --json` output.

Prefer `arm64e` for physical modern iOS device analysis. Do not mix simulator
cache evidence with physical-device exploitability unless that is the exact
target.

## Extracted Dylibs

`ipsw dyld extract` produces standalone Mach-O dylibs intended for RE tools.
The official docs note that extraction is cross-platform and can produce
standalone dylibs with segment layout, section offsets, and symbol tables useful
for IDA, Ghidra, and other tools.

Important flags:

- `--all`: extract every dylib.
- `--objc`: add ObjC runtime symbols to the extracted symbol table.
- `--stubs`: add stub island symbols.
- `--slide`: apply DSC slide info to help resolve PACed pointers.
- `--cache`: use an `.a2s` address-to-symbol cache to speed analysis.
- `--force`: overwrite existing extraction output.

`--objc` and `--stubs` add analysis symbols. They do not repair Objective-C
runtime data or patch stubs. Treat extracted dylibs as reconstructed views and
map critical addresses back to the original DSC before reporting.

## Metadata Search

Use `ipsw dyld search` for ObjC and Mach-O structure search across the cache:

```bash
ipsw dyld search --class 'LAContext|AKAppleIDAuthentication'
ipsw dyld search --protocol '.*Delegate'
ipsw dyld search --sel 'initWith.*'
ipsw dyld search --ivar '.*token.*'
ipsw dyld search --load-command 'LC_LOAD.*'
ipsw dyld search --section '__objc.*'
```

Use `ipsw dyld objc` and `ipsw dyld swift` for optimization metadata:

```bash
ipsw dyld objc dyld_shared_cache_arm64e --class --sel --proto > objc-opt.txt
ipsw dyld swift dyld_shared_cache_arm64e --types --metadata --foreign --demangle > swift-opt.txt
```

Use `ipsw dyld imports` when a library edge matters:

```bash
ipsw dyld imports dyld_shared_cache_arm64e /usr/lib/libMobileGestalt.dylib
ipsw dyld imports dyld_shared_cache_arm64e /usr/lib/libMobileGestalt.dylib --ipsw firmware.ipsw
```

The `--ipsw` scan helps find Mach-O files outside the DSC that import a target
dylib.

## Address and Symbol Workflows

Use dyld address helpers to keep crash logs, strings, symbols, and disassembly
in the same coordinate system:

```bash
ipsw dyld symaddr dyld_shared_cache_arm64e --image UIKitCore --in symbols.json --output symaddrs.json
ipsw dyld a2s dyld_shared_cache_arm64e 0x1abcdef00
ipsw dyld a2o dyld_shared_cache_arm64e 0x1abcdef00
ipsw dyld o2a dyld_shared_cache_arm64e 0x123456
ipsw dyld a2f dyld_shared_cache_arm64e 0x1abcdef00
ipsw dyld xref dyld_shared_cache_arm64e 0x1abcdef00 --image UIKitCore
```

`xref` is marked WIP in the official CLI docs. Treat it as a lead generator and
confirm important references with disassembly, decompiler output, or another RE
tool.

For string-to-code triage:

1. Search with `ipsw dyld str`.
2. Identify the containing image and address.
3. Convert address/offset as needed.
4. Inspect with `ipsw dyld macho`, extracted Mach-O in Ghidra/radare2, or both.
5. Preserve mappings from DSC address to extracted Mach-O address.

## Class and Swift Dumps

Use `ipsw class-dump` for Objective-C interfaces:

```bash
ipsw class-dump dyld_shared_cache_arm64e /System/Library/Frameworks/Foundation.framework/Foundation --headers --output headers/Foundation
ipsw class-dump dyld_shared_cache_arm64e UIKitCore --class 'UIViewController' --re
ipsw class-dump new_dsc UIKitCore --diff old_dsc --color
```

Use `ipsw swift-dump` for Swift interfaces:

```bash
ipsw swift-dump dyld_shared_cache_arm64e SwiftUI --interface --headers --output swift/SwiftUI
ipsw swift-dump dyld_shared_cache_arm64e SomeFramework --type '.*Manager.*' --demangle
```

Headers and Swift interfaces are recovered metadata, not source. Validate
security-sensitive method bodies in the Mach-O or DSC.

## Evidence Checklist

Capture:

- DSC path, hash, architecture, and sibling files retained.
- Extraction command, flags, and output paths.
- Whether facts came from DSC metadata, reconstructed dylib, class-dump,
  swift-dump, `dyld macho`, or external RE tooling.
- Address coordinate system: DSC address, file offset, extracted Mach-O address,
  and slide/PAC handling.
- ObjC/Swift search criteria and outputs.
- Import edges and whether `--ipsw` filesystem scanning was used.
- For report evidence, pair class/header findings with disassembly or
  decompiler addresses.

## Official Source Paths

- https://blacktop.github.io/ipsw/docs/guides/dyld/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/info/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/extract/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/macho/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/str/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/search/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/symaddr/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/imports/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/objc/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/dyld/swift/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/class-dump/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/swift-dump/
- https://github.com/apple-oss-distributions/dyld
