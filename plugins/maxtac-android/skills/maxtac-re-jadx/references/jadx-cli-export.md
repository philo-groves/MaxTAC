# JADX CLI, Export, and Batch Runs

Use this reference when the task needs repeatable JADX output from the command
line: source/resource export, JSON output, Gradle project generation,
single-class extraction, configs, plugin options, or evidence bundles.

## Contents

- [Quick Commands](#quick-commands)
- [Input and Output Layout](#input-and-output-layout)
- [Single-Class and Narrow Runs](#single-class-and-narrow-runs)
- [JSON Output](#json-output)
- [Gradle Export](#gradle-export)
- [Config and Environment Discipline](#config-and-environment-discipline)
- [Plugin Options from the CLI](#plugin-options-from-the-cli)
- [Exit Codes and Error Handling](#exit-codes-and-error-handling)
- [Batch Evidence Pattern](#batch-evidence-pattern)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

Baseline decompile:

```bash
jadx -d out app.apk
```

Separate source and resource output:

```bash
jadx -ds out/src -dr out/res app.apk
```

Source-only and resource-only runs:

```bash
jadx -r -d out-src-only app.apk
jadx -s -d out-res-only app.apk
```

Single class by raw name, alias, or full name:

```bash
jadx --single-class com.example.security.Checks \
  --single-class-output evidence/Checks.java \
  app.apk
```

JSON output for scripted analysis:

```bash
jadx --output-format json -d out-json app.apk
```

Gradle project export:

```bash
jadx -e -d out-gradle app.apk
jadx --export-gradle-type android-app -d out-gradle app.apk
```

Record directories used by the install:

```bash
jadx --print-files
```

Save a named configuration and reuse it:

```bash
jadx --threads-count 4 --comments-level warn --save-config maxtac-cli
jadx --config maxtac-cli -d out app.apk
```

## Input and Output Layout

The CLI accepts multiple input classes and containers. Upstream help lists APK,
DEX, JAR, CLASS, SMALI, ZIP, AAR, ARSC, AAB, XAPK, APKM, and `jadx.kts` inputs.

Use output paths deliberately:

```text
-d / --output-dir       root output directory
-ds / --output-dir-src  source output directory
-dr / --output-dir-res  resource output directory
-r / --no-res           skip resource decoding
-s / --no-src           skip source decompilation
```

Guidance:

- Keep source and resource output separated in evidence runs. Android resource
  findings often need a different review path from decompiled Java.
- Use `-r` when resources are huge, hostile, or irrelevant to the question.
- Use `-s` when the sample has no useful code or the task is manifest/resource
  triage.
- Use `--threads-count` to make runtime predictable in CI or shared hosts.
- Record the exact input list. JADX can load several files in one run, and
  merged classpaths affect decompilation and references.

## Single-Class and Narrow Runs

`--single-class` accepts a full name, raw name, or alias. Use it after GUI
triage, stack trace mapping, or a broad JSON search identifies one class.

Examples:

```bash
jadx --single-class a.b.c -d out-one app.apk
jadx --single-class com.example.LoginActivity \
  --single-class-output LoginActivity.java app.apk
```

Use narrow runs to:

- Capture a stable decompiler excerpt without exporting the entire app.
- Compare `auto`, `simple`, and `fallback` modes for one problematic class.
- Validate whether a renamed alias still maps to the original class.
- Avoid loading risky resources by combining with `-r`.

Do not use a single-class run as the only artifact for a finding. Preserve the
full APK/DEX, relevant mappings, manifest, and enough surrounding classes to
show call paths and Android component reachability.

## JSON Output

`--output-format json` switches code generation to JSON. The generated class
JSON includes structure such as package, class name, alias, class type, access
flags, declaration, fields, methods, method signatures, method code lines,
source-line mappings, and method dex offsets where available.

Example:

```bash
jadx --output-format json --comments-level info -d evidence/jadx-json app.apk
```

Use JSON output when:

- A script needs class/method/field structure without scraping Java text.
- You need dex offsets for method evidence.
- You want source-line mapping fields for decompiler-to-source correlation.
- You need to compare raw names and aliases across deobfuscation runs.

Notes:

- JSON class files are still decompiler output. Treat generated statements as
  hypotheses.
- JSON output uses the annotated code writer so offsets and source-line metadata
  can be attached.
- `mapping.json` is generated in JSON-output runs by the mapping export path.
  Keep it with the class JSON files.
- Do not assume JSON schema stability across JADX versions. Pin the JADX
  version and source commit for long-lived automation.

## Gradle Export

Use Gradle export when the task needs a rebuildable or IDE-friendly project
layout, not just evidence text.

CLI:

```bash
jadx -e -d out-gradle app.apk
jadx --export-gradle-type auto -d out-gradle app.apk
jadx --export-gradle-type android-library -d out-gradle lib.aar
jadx --export-gradle-type simple-java -d out-gradle classes.jar
```

Export types:

```text
auto
android-app
android-library
simple-java
```

Detection behavior from source:

- Android manifest plus `classes.jar` resources selects Android library export.
- Android manifest plus ARSC resources selects Android app export.
- Otherwise, export falls back to a simple Java project.

Guidance:

- Prefer explicit `--export-gradle-type` when the container is odd, trimmed, or
  partially extracted.
- Do not treat Gradle export as proof that the app rebuilds or behaves like the
  original. It is an analysis convenience.
- Keep the original manifest, resources, and DEX hashes next to the exported
  project.

## Config and Environment Discipline

JADX can load and save JSON config files:

```bash
jadx --save-config case-fast
jadx --config case-fast app.apk
jadx --config none app.apk
```

Use `--config none` for hermetic evidence runs where user preferences should not
leak into output.

Useful location controls:

```text
JADX_CONFIG_DIR  custom config directory
JADX_CACHE_DIR   custom cache directory
JADX_TMP_DIR     custom temp root directory
```

Use them in CI or case directories:

```bash
export JADX_CONFIG_DIR="$PWD/.jadx-config"
export JADX_CACHE_DIR="$PWD/.jadx-cache"
export JADX_TMP_DIR="$PWD/.jadx-tmp"
jadx --print-files
```

For hostile samples, use an isolated temp/cache/config directory so output and
plugin state are easy to inspect and remove.

## Plugin Options from the CLI

Plugin options use `-P<name>=<value>`:

```bash
jadx -Pdex-input.verify-checksum=no app.apk
jadx -Psmali-input.api-level=35 sample.smali
jadx -Prename-mappings.invert=yes --mappings-path mapping.txt app.apk
```

Bundled options shown by upstream help include:

- `dex-input.verify-checksum`
- `java-convert.mode`
- `java-convert.d8-desugar`
- `kotlin-metadata.*`
- `kotlin-smap.class-alias-source-dbg`
- `rename-mappings.format`
- `rename-mappings.invert`
- `smali-input.api-level`

Plugin management:

```bash
jadx plugins --list
jadx plugins --list-all
jadx plugins --available
jadx plugins --install <locationId>
jadx plugins --install-jar plugin.jar
jadx plugins --disable <pluginId>
jadx plugins --enable <pluginId>
jadx plugins --update
```

Disable plugins for reproducibility or risk reduction:

```bash
jadx --disable-plugins pluginA,pluginB -d out app.apk
```

Record plugin lists and plugin options in evidence because plugins can change
input loading, renaming, resource decoding, and generated code.

## Exit Codes and Error Handling

From the CLI implementation:

- `0`: normal completion or intentional early exit such as help/version/config
  save.
- `1`: invalid arguments or top-level process error.
- `2`: load failure with no classes when source decompilation was required.
- `3`: decompilation completed but JADX reported errors.

Guidance:

- Treat exit code `3` as partial output, not as clean success.
- Keep `--log-level debug` output for unusual failures, but avoid debug logs as
  the only evidence artifact.
- If a resource-only input has no classes, the CLI can switch to resource-only
  processing when resources are enabled. Record that state.
- `--quiet` can hide progress noise for scripts, but do not suppress logs when
  debugging a decompiler failure.

## Batch Evidence Pattern

Case layout:

```text
case/
  input/
    app.apk
  jadx/
    java/
    json/
    resources/
    logs/
    config/
    cache/
    tmp/
```

Run:

```bash
export JADX_CONFIG_DIR="$PWD/jadx/config"
export JADX_CACHE_DIR="$PWD/jadx/cache"
export JADX_TMP_DIR="$PWD/jadx/tmp"

jadx --print-files > jadx/logs/files.txt
jadx --version > jadx/logs/version.txt
jadx --config none --threads-count 4 \
  -ds jadx/java -dr jadx/resources \
  --comments-level info \
  input/app.apk > jadx/logs/java.stdout.txt 2> jadx/logs/java.stderr.txt

jadx --config none --threads-count 4 \
  --output-format json \
  -d jadx/json \
  input/app.apk > jadx/logs/json.stdout.txt 2> jadx/logs/json.stderr.txt
```

Capture the process exit code after each run in the surrounding script. Keep
stdout/stderr even if JADX writes most logs through the logger.

## Evidence Checklist

Capture:

- `jadx --version`, command line, environment variables, and config reference.
- Input file list, hashes, file sizes, and acquisition source.
- Output directories and whether sources, resources, JSON, or Gradle export were
  generated.
- Decompilation mode and transformation toggles that affect code output.
- Plugin list, disabled plugins, and all `-P` plugin options.
- Exit code, stdout, stderr, and relevant log lines.
- Whether output came from a full run, single-class run, or resource-only run.
- Any manual post-processing scripts and their hashes.

## Official Source Paths

- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/README.md
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-cli/src/main/java/jadx/cli/JadxCLIArgs.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-cli/src/main/java/jadx/cli/JadxCLI.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-cli/src/main/java/jadx/cli/JadxCLICommands.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-cli/src/main/java/jadx/cli/commands/CommandPlugins.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/core/export/ExportGradle.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/core/codegen/json/JsonCodeGen.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/core/codegen/json/JsonMappingGen.java
