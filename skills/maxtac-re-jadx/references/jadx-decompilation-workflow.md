# JADX Decompilation Workflow

Use this reference when JADX output is being used to explain behavior, identify
security-sensitive paths, compare obfuscation mappings, or produce reportable
evidence. The decompiled Java is not source code. Verify important conclusions
against smali, dex offsets, control-flow output, metadata, resources, or runtime
state.

## Contents

- [Quick Commands](#quick-commands)
- [Decompilation Modes](#decompilation-modes)
- [Transformation Toggles](#transformation-toggles)
- [Bad Code and Errors](#bad-code-and-errors)
- [Debug Lines, Source Lines, and Offsets](#debug-lines-source-lines-and-offsets)
- [Smali Comparison](#smali-comparison)
- [CFG Output](#cfg-output)
- [Kotlin and Synthetic Code](#kotlin-and-synthetic-code)
- [Vulnerability Research Patterns](#vulnerability-research-patterns)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

Default best-effort output:

```bash
jadx -d out-auto app.apk
```

Compare modes for one class:

```bash
jadx --single-class com.example.Parser -d out-auto app.apk
jadx --single-class com.example.Parser -m simple -d out-simple app.apk
jadx --single-class com.example.Parser -m fallback -d out-fallback app.apk
```

Expose inconsistent generated code:

```bash
jadx --show-bad-code -d out-bad app.apk
```

Reduce transformations around a suspicious method:

```bash
jadx --no-inline-methods --no-inline-anonymous \
  --no-inline-kotlin-lambda --no-move-inner-classes \
  --respect-bytecode-access-modifiers \
  --single-class com.example.Parser \
  -d out-conservative app.apk
```

Add debug line comments when available:

```bash
jadx --add-debug-lines --comments-level debug -d out-debug app.apk
```

Emit method CFG dot files:

```bash
jadx --cfg -d out-cfg app.apk
jadx --raw-cfg -d out-raw-cfg app.apk
```

## Decompilation Modes

JADX exposes four output modes:

```text
auto         best options, default
restructure  restore normal Java structure
simple       simplified linear instructions with gotos
fallback     raw instructions without modifications
```

Use `auto` for normal reading. Switch modes when the output is suspicious:

- Use `simple` when structured Java hides branch order, exception edges, or a
  suspicious conditional.
- Use `fallback` when the decompiler fails or when raw control-flow evidence is
  more valuable than readable Java.
- Use `restructure` when comparing with default behavior and you want to
  isolate the impact of automatic mode selection.

For reportable findings, preserve the mode used for each excerpt. Do not mix a
readable `auto` excerpt with a `fallback` offset claim without explaining the
relationship.

## Transformation Toggles

JADX performs transformations that improve readability but can hide bytecode
shape. Disable them when a hypothesis depends on exact ordering, access checks,
or object structure.

Useful toggles:

```text
--no-imports
--no-debug-info
--add-debug-lines
--no-inline-anonymous
--no-inline-methods
--no-move-inner-classes
--no-inline-kotlin-lambda
--no-finally
--no-restore-switch-over-string
--no-replace-consts
--respect-bytecode-access-modifiers
--integer-format decimal|hexadecimal|auto
--type-update-limit <n>
```

Guidance:

- Disable method and anonymous-class inlining when tracking callsites,
  callbacks, or object lifetimes.
- Disable Kotlin lambda inlining when the original synthetic class or method
  boundary matters.
- Disable `finally` extraction and string-switch restoration when exception
  edges or branch recovery look wrong.
- Disable constant replacement when the numeric value, resource ID, or bitmask
  is the evidence.
- Use `--respect-bytecode-access-modifiers` when access changes affect a patch
  diff, reflective access, or rebuildability claim.
- Use `--integer-format hexadecimal` for flag, resource ID, protocol, crypto,
  and offset-heavy analysis.

## Bad Code and Errors

By default, inconsistent code is not shown as normal output. `--show-bad-code`
shows code that JADX considers incorrectly decompiled.

Use it to inspect failures, not as final proof:

```bash
jadx --show-bad-code --single-class com.example.Parser -d out-bad app.apk
```

When JADX reports errors:

- Keep the error report and exit code.
- Re-run the impacted class with `simple` and `fallback`.
- Compare method bodies with `JavaClass.getSmali()` through the API or with
  external smali/dex tooling.
- Check whether an exception edge, switch, inlining decision, or type update
  limit caused the distortion.
- Do not claim absence of a check or call from a method that failed
  decompilation unless fallback/smali confirms it.

The CLI can finish with errors and return exit code `3`. Treat that output as
partial.

## Debug Lines, Source Lines, and Offsets

JADX can parse debug info by default, add debug line comments, and emit JSON
metadata that includes source lines and dex offsets where available.

Commands:

```bash
jadx --add-debug-lines --comments-level debug -d out-lines app.apk
jadx --output-format json -d out-json app.apk
```

API points:

- `JavaClass.getCodeInfo().getCodeMetadata().getLineMapping()` maps decompiled
  lines to source lines when debug info exists.
- `JavaClass.getSourceLine(decompiledLine)` exposes that mapping.
- JSON method output includes method offsets and per-line offsets where code
  metadata has `InsnCodeOffset`.
- `JadxDecompiler.getJavaNodeAtPosition`, `getClosestJavaNode`, and
  `getEnclosingNode` connect code positions to classes, methods, fields, and
  variables.

Evidence rule:

- Decompiled line numbers are not dex offsets.
- Source lines can come from debug metadata and may be absent, stale, or
  obfuscated.
- Dex offsets are stronger anchors for bytecode-level claims, but still need
  the original DEX hash and method identity.

## Smali Comparison

Use smali when:

- Decompiled code is marked bad or incomplete.
- A security check appears to be optimized away or inverted.
- A try/catch/finally path matters.
- Kotlin, synthetic, bridge, or lambda code changes the apparent call graph.
- You need register-level argument flow.

API:

```java
for (JavaClass cls : jadx.getClasses()) {
    if (cls.getFullName().equals("com.example.Parser")) {
        System.out.println(cls.getSmali());
    }
}
```

Workflow:

1. Identify the Java method and short signature.
2. Locate the same method in smali.
3. Compare branch targets, invoke instructions, constants, register moves, and
   exception handlers.
4. Record the decompilation mode and the smali excerpt side by side.

## CFG Output

`--cfg` and `--raw-cfg` save method control-flow graphs to dot files.

Use CFG output to:

- Confirm branch structure around bounds checks.
- Compare normal and raw instruction control flow.
- Show exception-heavy or dispatcher-heavy code without relying on Java
  formatting.
- Identify methods where decompiler structure diverges from bytecode flow.

Prefer raw CFG when decompiler repair is suspect. Prefer normal CFG when you
need analyst-readable structure after transformations.

## Kotlin and Synthetic Code

JADX includes Kotlin-aware options and bundled plugin options:

```text
--use-kotlin-methods-for-var-names disable|apply|apply-and-hide
-Pkotlin-metadata.class-alias=yes|no
-Pkotlin-metadata.method-args=yes|no
-Pkotlin-metadata.fields=yes|no
-Pkotlin-smap.class-alias-source-dbg=yes|no
```

Guidance:

- Kotlin metadata can improve names, but names are not proof of original
  semantics.
- `apply-and-hide` can remove useful evidence of intrinsic calls from the
  generated code. Avoid it when documenting how a value is named or propagated.
- SMAP/source debug extension aliases may be useful for stack traces, but source
  names can collide or be misleading in obfuscated builds.
- Synthetic accessors, default-argument methods, companion objects, lambdas, and
  data-class helpers can move behavior away from the source-looking method.

## Vulnerability Research Patterns

### Missing Bounds Check

```bash
jadx --single-class com.example.Parser -d out-auto app.apk
jadx --single-class com.example.Parser -m simple --show-bad-code -d out-simple app.apk
jadx --output-format json --single-class com.example.Parser -d out-json app.apk
```

Check:

- Java branch structure.
- Simple/fallback branch order.
- Smali registers used for length and index.
- JSON/dex offset anchors for the sink.
- Resource or intent path that reaches the method.

### Dangerous API Reachability

Start from Java search or JSON, then verify:

- Caller class and method signature.
- Original/raw class name and alias.
- Invoke instruction in smali.
- Android component, exported service, receiver, provider, or webview bridge
  path.
- Runtime constraints such as permissions, SDK checks, feature flags, or
  reflection.

### Patch or Version Comparison

Run both versions with the same options:

```bash
jadx --config none --output-format json -d old-json old.apk
jadx --config none --output-format json -d new-json new.apk
```

Compare:

- Raw class and method identities, not just alias paths.
- Method offsets and signatures.
- Constants with `--integer-format hexadecimal` if relevant.
- Deobfuscation mapping files and rename modes.
- Error counts for both versions.

## Evidence Checklist

Capture:

- JADX version, command line, config, plugin options, and decompilation mode.
- Exact class and method names: raw name, alias name, full name, short
  signature.
- Whether output came from Java, JSON, smali, CFG, GUI, or API.
- Error count, bad-code markers, and transformation toggles.
- Decompiled excerpt plus smali/dex offset evidence for critical claims.
- Source-line/debug-line mapping only when used and with caveats.
- Original APK/DEX hash and mapping files used for aliases.

## Official Source Paths

- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-cli/src/main/java/jadx/cli/JadxCLIArgs.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/JadxArgs.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/JadxDecompiler.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/JavaClass.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/JavaMethod.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/core/codegen/json/JsonCodeGen.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/metadata/ICodeMetadata.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/metadata/annotations/InsnCodeOffset.java
