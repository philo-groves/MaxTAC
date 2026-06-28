# JADX Automation, API, and Plugins

Use this reference when JADX needs to be embedded in a Java tool, scripted for
repeatable evidence, extended with plugins, or used to extract structured data
without scraping generated Java text.

## Contents

- [Quick API Skeleton](#quick-api-skeleton)
- [JadxArgs Controls](#jadxargs-controls)
- [Loading, Saving, and Lazy Decompilation](#loading-saving-and-lazy-decompilation)
- [Class, Method, and Metadata APIs](#class-method-and-metadata-apis)
- [Resource APIs](#resource-apis)
- [Structured JSON Extraction](#structured-json-extraction)
- [Plugin Model](#plugin-model)
- [Plugin CLI Operations](#plugin-cli-operations)
- [Cache and Hash Discipline](#cache-and-hash-discipline)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Quick API Skeleton

Minimal batch export:

```java
JadxArgs args = new JadxArgs();
args.getInputFiles().add(new File("app.apk"));
args.setOutDir(new File("jadx-out"));
args.setThreadsCount(4);

try (JadxDecompiler jadx = new JadxDecompiler(args)) {
    jadx.load();
    jadx.save();
    jadx.printErrorsReport();
}
```

Iterate classes without writing files:

```java
try (JadxDecompiler jadx = new JadxDecompiler(args)) {
    jadx.load();
    for (JavaClass cls : jadx.getClasses()) {
        String raw = cls.getRawName();
        String alias = cls.getFullName();
        String code = cls.getCode();
    }
}
```

Always close `JadxDecompiler`. It closes input loaders, custom loaders, plugins,
code caches, usage caches, zip readers, and temp files.

## JadxArgs Controls

High-value `JadxArgs` settings for automation:

```text
inputFiles
outDir, outDirSrc, outDirRes
threadsCount
skipSources, skipResources
decompilationMode
showInconsistentCode
debugInfo, insertDebugLines
inlineAnonymousClasses, inlineMethods, allowInlineKotlinLambda
moveInnerClasses, extractFinally, restoreSwitchOverString
replaceConsts, respectBytecodeAccModifiers
userRenamesMappingsPath, userRenamesMappingsMode
deobfuscationOn, generatedRenamesMappingFile, generatedRenamesMappingFileMode
resourceNameSource, useHeadersForDetectResourceExtensions
renameFlags, fsCaseSensitive
outputFormat
commentsLevel, integerFormat, typeUpdatesLimitCount
classFilter, includeDependencies
pluginOptions, disabledPlugins
security
```

Use `classFilter` for targeted analysis:

```java
args.setClassFilter(name -> name.startsWith("com.example."));
args.setIncludeDependencies(true);
```

Set `includeDependencies` when a filtered class needs referenced classes saved
for context. Leave it false when you intentionally want only the selected class
set.

## Loading, Saving, and Lazy Decompilation

`JadxDecompiler.load()`:

- Validates args.
- Loads plugins.
- Loads code inputs from plugins.
- Loads classes and resources.
- Initializes classpath and passes.
- Runs pre-decompile stages.

`save()` writes resources first, then sources, then Gradle files if Gradle
export is enabled.

Lazy behavior:

- `getClasses()` returns top-level non-inner classes without necessarily
  decompiling every class body.
- `JavaClass.getCode()` or `getCodeInfo()` triggers decompilation if needed.
- `JavaClass.loadingWouldRequireDecompilation()` can detect whether a call would
  be expensive.
- `JavaClass.reload()` re-runs code generation for that class.
- `JavaClass.unload()` clears loaded code/list state.

Guidance:

- Do not iterate `getCode()` over every class unless the task needs full code.
- Use JSON output or metadata-specific APIs instead of text scraping.
- Preserve load errors separately from per-class decompilation errors.

## Class, Method, and Metadata APIs

Useful class APIs:

```text
JavaClass.getCode()
JavaClass.getCodeInfo()
JavaClass.getSmali()
JavaClass.getRawName()
JavaClass.getFullName()
JavaClass.getPackage()
JavaClass.getFields()
JavaClass.getMethods()
JavaClass.getDependencies()
JavaClass.getUsageMap()
JavaClass.getUsePlacesFor(...)
JavaClass.getSourceLine(...)
```

Useful method APIs:

```text
JavaMethod.getName()
JavaMethod.getFullName()
JavaMethod.getArguments()
JavaMethod.getReturnType()
JavaMethod.getUseIn()
JavaMethod.getUsed()
JavaMethod.getUnresolvedUsed()
JavaMethod.getOverrideRelatedMethods()
JavaMethod.getCodeStr()
```

Metadata APIs:

```text
ICodeInfo.getCodeMetadata()
ICodeMetadata.getAt(position)
ICodeMetadata.getClosestUp(position)
ICodeMetadata.getNodeAt(position)
ICodeMetadata.getLineMapping()
JadxDecompiler.getJavaNodeAtPosition(codeInfo, pos)
JadxDecompiler.getClosestJavaNode(codeInfo, pos)
JadxDecompiler.getEnclosingNode(codeInfo, pos)
```

Use metadata to map text positions to classes, methods, fields, variables, and
offset annotations. Do not parse Java syntax when metadata already supplies the
node boundary.

## Resource APIs

Useful APIs:

```text
JadxDecompiler.getResources()
ResourceFile.getOriginalName()
ResourceFile.getDeobfName()
ResourceFile.getType()
ResourceFile.loadContent()
ResourcesLoader.decodeStream(...)
ResourcesLoader.decodeTable(...)
```

Guidance:

- Store original resource names and deobfuscated names together.
- Load only resources needed for the question; resource loading can decode large
  or hostile content.
- For plugin/resource extensions, prefer `CustomResourcesLoader` or resource
  loader providers over external preprocessing hidden from the JADX run.

## Structured JSON Extraction

Prefer one of these:

- CLI `--output-format json`.
- API traversal over `JavaClass`, `JavaMethod`, `ResourceFile`, and metadata.
- A plugin/pass that emits a case-specific JSON artifact.

Avoid:

- Grepping generated Java for method boundaries.
- Parsing file paths as class identities.
- Treating aliases as raw names.
- Ignoring class load/decompile errors in batch scripts.

Example output object fields to preserve:

```text
toolVersion
inputHashes
argsHash
classRawName
classAlias
methodShortId
methodOffset
sourceLine
decompiledLine
resourceOriginalName
resourceAlias
errors
warnings
```

## Plugin Model

Plugins implement `jadx.api.plugins.JadxPlugin` and are discovered through:

```text
META-INF/services/jadx.api.plugins.JadxPlugin
```

Plugin entrypoints:

```java
JadxPluginInfo getPluginInfo();
void init(JadxPluginContext context);
default void unload();
```

`JadxPluginContext` can:

- Access `JadxArgs` and `JadxDecompiler`.
- Register passes.
- Register code inputs.
- Register plugin options.
- Register input-hash suppliers for output/cache correctness.
- Customize resource loading.
- Access GUI context when running in `jadx-gui`.
- Subscribe/send events.
- Access plugin files and the configured `ZipReader`.

Pass types seen in source include:

```text
JadxPreparePass   init(RootNode root)
JadxAfterLoadPass init(JadxDecompiler decompiler)
```

Pass ordering uses `JadxPassInfo`:

```text
getName()
getDescription()
runAfter()
runBefore()
```

Guidance:

- Use `JadxPreparePass` or `JadxAfterLoadPass` for long work instead of doing it
  inside plugin `init`.
- Register an inputs hash supplier for any plugin option or external data that
  changes generated output.
- Use `context.getZipReader()` for archive handling so JADX security checks are
  honored.
- Keep plugin options in the evidence packet.

## Plugin CLI Operations

Manage plugins:

```bash
jadx plugins --list
jadx plugins --list-all
jadx plugins --available
jadx plugins --install <locationId>
jadx plugins --install-jar plugin.jar
jadx plugins --update
jadx plugins --disable <pluginId>
jadx plugins --enable <pluginId>
jadx plugins --uninstall <pluginId>
```

Run with plugin options:

```bash
jadx -Pplugin.option=value app.apk
```

Run with plugin disabled:

```bash
jadx --disable-plugins pluginId -d out app.apk
```

Guidance:

- Use `--list-all` in evidence runs to include bundled, installed, and drop-in
  plugins.
- Disable nonessential third-party plugins for hostile samples.
- Record plugin versions and required JADX versions when installing from the
  marketplace.

## Cache and Hash Discipline

`JadxArgs.makeCodeArgsHash()` combines output-affecting options and plugin input
hashes. GUI code/usage caches can use disk or memory. CLI sets no-op code cache
and empty usage cache.

Guidance:

- In automation, decide whether caches are allowed. For exact reproductions,
  isolate or clear cache directories.
- Include options, plugin hashes, and mapping hashes in cache keys.
- Do not reuse GUI cache output as evidence without the project, settings, and
  JADX version.
- Use `JADX_CACHE_DIR` and `JADX_TMP_DIR` to isolate case runs.

## Evidence Checklist

Capture:

- JADX version and library artifact version if embedded.
- `JadxArgs` values that affect code output.
- Input file hashes and plugin input hashes.
- Plugin list, plugin versions, options, disabled plugins, and external files.
- API script source, build file, and dependency versions.
- Decompile/load errors and warnings.
- Raw and alias identities for every emitted node.
- Cache/config/temp directories used by the run.

## Official Source Paths

- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/JadxArgs.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/JadxDecompiler.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/JavaClass.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/JavaMethod.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/ResourceFile.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/plugins/JadxPlugin.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/plugins/JadxPluginContext.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/plugins/pass/JadxPassInfo.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-plugins/jadx-input-api/src/main/java/jadx/api/plugins/input/JadxCodeInput.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-cli/src/main/java/jadx/cli/commands/CommandPlugins.java
