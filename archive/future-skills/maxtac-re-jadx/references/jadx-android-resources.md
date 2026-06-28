# JADX Android Resources

Use this reference when AndroidManifest.xml, `resources.arsc`, XML, assets,
native libraries, split containers, or resource names are part of the reversing
question. Resource decoding is analysis, not a neutral file copy: record
resource options, aliases, failures, and skipped files.

## Contents

- [Quick Commands](#quick-commands)
- [Resource Loading Model](#resource-loading-model)
- [Manifest Triage](#manifest-triage)
- [Resource Name Recovery](#resource-name-recovery)
- [Resource Search and Size Limits](#resource-search-and-size-limits)
- [Native Libraries and Assets](#native-libraries-and-assets)
- [Split and Library Containers](#split-and-library-containers)
- [Gradle Export Type Detection](#gradle-export-type-detection)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick Commands

Decode resources only:

```bash
jadx -s -d out-res app.apk
```

Decode sources but skip resources:

```bash
jadx -r -d out-src app.apk
```

Separate output:

```bash
jadx -ds out/src -dr out/res app.apk
```

Recover obfuscated resource extensions using file headers:

```bash
jadx --use-headers-for-detect-resource-extensions -d out app.apk
```

Choose resource name source:

```bash
jadx --deobf-res-name-source resources -d out app.apk
jadx --deobf-res-name-source code -d out app.apk
```

Preserve raw numeric values around resource IDs:

```bash
jadx --integer-format hexadecimal --no-replace-consts -d out app.apk
```

## Resource Loading Model

JADX loads resources from input files and ZIP-like containers. Resource types are
classified by path and extension, including:

```text
CODE: .dex, .jar, .class
XML: .xml
ARSC: .arsc and resources.pb
APK/APKM/APKS
IMG, FONT, ARCHIVE, VIDEOS, SOUNDS, JSON, TEXT, HTML, LIB .so
MANIFEST
UNKNOWN/UNKNOWN_BIN
```

Important behavior:

- `AndroidManifest.xml` is processed first during save so the resource ID table
  is available for later resource decoding.
- Code-source resources such as DEX and class files are not emitted as ordinary
  resources during save.
- Binary XML and ARSC are decoded into text/resource containers when possible.
- Images are usually linked as files; 9-patch PNG images can be decoded.
- Custom resource loaders can be added through the API/plugin path.

Guidance:

- Keep undecoded originals. Decoded XML is more readable but not the original
  bytes.
- If a resource load error occurs, preserve the generated error text and logs.
- For hostile APKs, prefer resource-only or source-only runs to isolate failures.

## Manifest Triage

Use the decoded manifest to drive code review:

- Package name and whether package verification was enabled.
- Application class and backup/debug/network settings.
- Exported activities, services, receivers, and providers.
- Intent filters, schemes, hosts, paths, MIME types, and priorities.
- Permissions, custom permissions, protection levels, and SDK gates.
- Provider authorities and grant URI permission patterns.
- Instrumentation, queries, and metadata entries.

Follow every reachable component into code:

```text
manifest component -> class alias/raw name -> lifecycle/entry method -> xrefs -> sinks
```

For Android 12+ exported semantics, rely on target SDK and manifest attributes,
not decompiler guesses.

## Resource Name Recovery

Resource names can come from resource tables or code-side `R` fields:

```text
--deobf-res-name-source auto
--deobf-res-name-source resources
--deobf-res-name-source code
```

Use cases:

- `resources`: prefer names from the resource table when the table is intact.
- `code`: prefer names from `R` class fields when resource table names are
  obfuscated but code names are better.
- `auto`: accept JADX's best selection when no comparison is needed.

Resource aliasing builds names like:

```text
res/<type><config>/<key><extension>
```

When `--use-headers-for-detect-resource-extensions` is set, JADX reads at most
the first 4096 bytes to infer an extension for obfuscated resource files.

Guidance:

- Record the resource name source used in every resource-name claim.
- Use hexadecimal integer output and avoid constant replacement when resource ID
  values themselves are evidence.
- Do not assume a recovered resource filename existed in the original APK.
  Preserve `ResourceFile.getOriginalName()` and the recovered alias.

## Resource Search and Size Limits

GUI resource search loads resource nodes and applies type and size filtering.
It can search only an active resource or walk the resource tree. Generated ARSC
subfiles are treated specially so a size check on the ARSC parent does not skip
all decoded child XML.

Resource search can skip files because of:

- Type filters.
- Size limits.
- Resource load errors.
- Binary or unknown content classification.

Guidance:

- When a GUI search is used as evidence, capture the resource filter and size
  limit.
- Reproduce important resource hits with CLI output or API extraction.
- For secrets or URLs, search decoded text and original assets; either side can
  miss transformed data.

## Native Libraries and Assets

JADX classifies `.so` files as library resources and does not reverse native
code. Use JADX to locate and preserve native libraries, then hand them to native
RE tooling.

Resource triage for native or asset-heavy apps:

- `lib/<abi>/*.so`: JNI exports, string references from Java, `System.load*`.
- `assets/`: WebView content, JS bridges, ML models, databases, configs.
- `res/raw/`: certificates, serialized data, compressed/encrypted blobs.
- `META-INF/`: signatures and packaging metadata.

Do not report native behavior from Java decompilation alone. Pair Java JNI
callers with native symbol/string/disassembly evidence.

## Split and Library Containers

JADX supports APK, XAPK, APKM, AAB, AAR, ZIP, and related inputs. For split apps:

- Keep the original split set and install metadata.
- Record which files were provided to one JADX run.
- Check whether classes/resources are spread across base and config splits.
- Preserve ABI, density, language, and feature split names.

For AARs:

- Android library export is selected when a manifest and `classes.jar` resource
  are present.
- Resource IDs and consumer app behavior may differ from the final APK.

For AABs:

- Treat output as bundle analysis, not a device-specific generated APK.
- If reachability depends on a split, build or obtain the actual APK set used on
  the target device.

## Gradle Export Type Detection

JADX export type detection:

- Manifest plus `classes.jar`: Android library.
- Manifest plus ARSC resource: Android app.
- Otherwise: simple Java.

Use explicit export type for partial or unusual samples:

```bash
jadx --export-gradle-type android-app -d out app.apk
jadx --export-gradle-type android-library -d out lib.aar
jadx --export-gradle-type simple-java -d out classes.jar
```

Guidance:

- Gradle export is a convenience for navigation and experiments.
- Generated Gradle files are not evidence that the original app is rebuildable.
- Keep the raw manifest/resources and JADX options with the export.

## Evidence Checklist

Capture:

- Input container list, hashes, split names, and whether files were analyzed
  together.
- `-s`, `-r`, source/resource output dirs, and resource name options.
- Decoded manifest plus original APK/DEX/container hash.
- Resource original names, recovered aliases, and resource ID values.
- Resource load errors, skipped files, and GUI resource search filters.
- Native libraries and asset paths handed off to other tools.
- Gradle export type, whether auto-detected or explicit.

## Official Source Paths

- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/README.md
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/ResourceFile.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/ResourceType.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/ResourcesLoader.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/args/ResourceNameSource.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/core/export/ExportGradle.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/search/providers/ResourceSearchProvider.java
