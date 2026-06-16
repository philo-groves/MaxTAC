# IPSW Kernelcache and KEXTs

Use this reference when preparing an iOS kernelcache for reverse engineering,
extracting KEXTs, finding kernel-facing attack surfaces, or preserving kernel
symbolication evidence.

## Contents

- [Quick Commands](#quick-commands)
- [Kernelcache Preparation](#kernelcache-preparation)
- [KEXT Extraction](#kext-extraction)
- [Kernel Entry Surfaces](#kernel-entry-surfaces)
- [C++ Class Recovery](#c-class-recovery)
- [Symbolication](#symbolication)
- [Handoff to RE Tools](#handoff-to-re-tools)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

Extract and prepare:

```bash
ipsw extract --kernel --device iPhone16,1 -o kernel/ firmware.ipsw

# Only for raw/compressed kernelcache payloads pulled directly from the archive.
ipsw kernel dec raw-kernelcache.im4p -o kernel/kernelcache.dec
```

List and extract KEXTs:

```bash
ipsw kernel kexts kernelcache.release.iPhone16,1 --json > kexts.json
ipsw kernel extract kernelcache.release.iPhone16,1 --all --imports -o kexts/
ipsw kernel extract kernelcache.release.iPhone16,1 com.apple.iokit.IOUSBHostFamily --imports -o kexts/
```

Triage kernel-facing surfaces:

```bash
ipsw kernel mig kernelcache.release.iPhone16,1 > mig.txt
ipsw kernel mach kernelcache.release.iPhone16,1 > mach-traps.txt
ipsw kernel syscall kernelcache.release.iPhone16,1 > syscalls.txt
ipsw kernel syscall kernelcache.release.iPhone16,1 --gen -o syscalls.gz
```

Recover C++/IOKit structure:

```bash
ipsw kernel cpp kernelcache.release.iPhone16,1 --json > kernel-cpp.json
ipsw kernel cpp kernelcache.release.iPhone16,1 --inheritance > kernel-cpp-inheritance.txt
ipsw kernel cpp kernelcache.release.iPhone16,1 --entry com.apple.kernel --json > kernel-entry-cpp.json
ipsw kernel cpp kernelcache.release.iPhone16,1 --class IOService
```

Symbolicate with a signature corpus:

```bash
ipsw kernel symbolicate --signatures sigs/ --json kernelcache.release.iPhone16,1
ipsw kernel symbolicate --lookup 0xfffffe000aecb258 kernelcache.release.iPhone16,1.symbols.json
```

## Kernelcache Preparation

Prefer `ipsw extract --kernel`; the official kernel guide notes this is usually
the right path instead of manually pulling an IM4P from the archive and running
`ipsw kernel dec`. Use `dec` when you intentionally have a raw/compressed
kernelcache payload from the ZIP, and record why.

Keep the original kernelcache and any decompressed form. Record which one each
tool consumed. A successful decompression changes the container but should not
replace the original evidence artifact.

Before broad RE:

1. Confirm product/build identity and the kernelcache path from `ipsw info`.
2. Hash the original and decompressed kernelcache, if both exist.
3. List KEXTs and save JSON before extraction.
4. Extract only the KEXTs needed for triage first; extract all when building a
   full analysis corpus.
5. Preserve import-resolution flags such as `--imports`.

Do not assume a string or class name implies reachability. Kernelcache metadata
is a map of possibilities; vulnerability proof still needs caller, input,
constraint, and sink evidence.

## KEXT Extraction

Use `ipsw kernel kexts` to get exact bundle IDs before extraction. Extract by
bundle ID when a specific driver family is under review:

```bash
ipsw kernel kexts kernelcache.release.iPhone16,1 --json | jq '.[].id'
ipsw kernel extract kernelcache.release.iPhone16,1 com.apple.driver.AppleAVE2 --imports -o kexts/
```

Use `--all` for whole-build diffing or when class inheritance and vtables cross
bundle boundaries:

```bash
ipsw kernel extract kernelcache.release.iPhone16,1 --all --imports -o kexts-all/
```

`--imports` helps extracted KEXTs carry names from the kernelcache. Treat those
names as analysis aids, then verify important callsites in the original
kernelcache or a consistent extracted image.

## Kernel Entry Surfaces

Use `mig`, `mach`, and `syscall` output as triage front doors:

- `mig`: Mach Interface Generator subsystems and message handlers.
- `mach`: mach trap table.
- `syscall`: Unix syscall table and generated syscall data.

Workflow for a suspected entry:

1. Save the generated table output.
2. Map handler names or addresses into Ghidra/radare2.
3. Confirm the exact function body and references in the kernelcache.
4. Trace argument decoding and user/kernel copy boundaries.
5. Check entitlement, sandbox, platform, and device-family gates outside the
   handler before marking reachability.

MIG output is not proof that an unprivileged process can call the handler. It is
a lead for message ID, subsystem, and implementation location.

## C++ Class Recovery

Use `ipsw kernel cpp` for IOKit and C++ structure leads:

```bash
ipsw kernel cpp kernelcache.release.iPhone16,1 --class IOUserClient
ipsw kernel cpp kernelcache.release.iPhone16,1 --inheritance --json > inheritance.json
```

High-value patterns:

- `IOService` subclasses for device matching and lifecycle.
- `IOUserClient` subclasses for userland method dispatch.
- External method tables, selector ranges, and entitlement checks.
- Vtable or override changes across patched builds.

Class recovery can miss optimized or unusual layouts. Validate class methods
with vtable references, constructors, `OSMetaClass` usage, and callsites.

## Symbolication

Use signature folders when available:

```bash
ipsw kernel symbolicate --signatures sigs/ --json kernelcache.release.iPhone16,1 \
  > kernel-symbols.json
ipsw kernel symbolicate --lookup 0xfffffe000aecb258 kernel-symbols.json
```

Keep generated symbol maps next to the exact kernelcache hash. Do not reuse a
symbol map across builds unless the build identity and kernelcache hash match.

For macOS kernel diffs, `ipsw diff` can take KDK paths. For iOS kernelcache
work, expect fewer public symbols and lean on signature corpora, KEXT metadata,
C++ recovery, and cross-version diffs.

## Handoff to RE Tools

Use `maxtac-re-ghidra` when decompiler output, type recovery, and persistent
program databases matter. Use `maxtac-re-radare2` when quick command-line
triage, scripted search, or patch diff automation is more useful.

Prepare the handoff:

- Original and decompressed kernelcache paths.
- KEXT JSON and extracted KEXTs.
- Symbol map and signature source.
- MIG/mach/syscall output.
- `ipsw kernel cpp` JSON.
- Import-resolution settings and architecture.
- Manual assumptions about base addresses or slides, if any.

For IDA-specific workflows, `ipsw kernel ida` can run IDA headless, delete or
reuse databases, pass scripts, and optionally use a Docker image. Do not use
that command as a substitute for Ghidra/radare evidence unless IDA is the chosen
analysis backend.

## Evidence Checklist

Capture:

- Kernelcache filename, hash, product type, version, build, and architecture.
- Whether `ipsw kernel dec` was used and hash of decompressed output.
- KEXT list JSON, extracted KEXT paths, and `--imports` usage.
- Entry-surface outputs from `mig`, `mach`, and `syscall`.
- C++ class output and inheritance output when used.
- Symbolication signature path, generated symbol map, and lookup commands.
- RE tool import settings, base assumptions, and manual repairs.
- Address mappings from table output to disassembly/decompiler locations.

## Official Source Paths

- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/dec/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/kexts/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/extract/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/cpp/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/mig/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/mach/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/syscall/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/symbolicate/
- https://blacktop.github.io/ipsw/docs/cli/ipsw/kernel/ida/
- https://blacktop.github.io/ipsw/docs/guides/kernel/
