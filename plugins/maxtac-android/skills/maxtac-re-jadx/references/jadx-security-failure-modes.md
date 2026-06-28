# JADX Security and Failure Modes

Use this reference when handling hostile APKs, malformed ZIPs, resource bombs,
broken XML, third-party plugins, partial decompilation, or unexpected output.
The defaults include safety checks. Disable them only for an isolated disposable
reproduction and document that choice.

## Contents

- [Default Security Model](#default-security-model)
- [Environment Overrides](#environment-overrides)
- [ZIP and Archive Risks](#zip-and-archive-risks)
- [XML and Package Risks](#xml-and-package-risks)
- [Plugin Risk](#plugin-risk)
- [Failure Modes](#failure-modes)
- [Isolation Pattern](#isolation-pattern)
- [Evidence Checklist](#evidence-checklist)
- [Official Source Paths](#official-source-paths)

## Default Security Model

`JadxArgs` defaults to `JadxSecurity` with all security flags:

```text
VERIFY_APP_PACKAGE
SECURE_XML_PARSER
SECURE_ZIP_READER
```

ZIP security checks include:

- Entry name validation.
- Path traversal detection for `../` and `..\\`.
- Normalized path containment checks.
- Zip bomb detection using compressed and uncompressed sizes.
- Maximum entry count.
- Limited streams for uncompressed entry data.

XML security config disables external and risky parser features when the secure
parser flag is enabled.

Guidance:

- Leave defaults enabled for untrusted APKs and archives.
- Treat disabled checks as a material analysis condition.
- Record security-related environment variables in every hostile-sample run.

## Environment Overrides

Security and location environment variables:

```text
JADX_DISABLE_XML_SECURITY=true
JADX_DISABLE_ZIP_SECURITY=true
JADX_ZIP_MAX_ENTRIES_COUNT=<int>
JADX_ZIP_BOMB_MIN_UNCOMPRESSED_SIZE=<int>
JADX_ZIP_BOMB_DETECTION_FACTOR=<int>
JADX_CONFIG_DIR=<path>
JADX_CACHE_DIR=<path>
JADX_TMP_DIR=<path>
```

Important source behavior:

- `JADX_DISABLE_XML_SECURITY=true` removes `SECURE_XML_PARSER` and, for
  compatibility, also removes `VERIFY_APP_PACKAGE`.
- `JADX_DISABLE_ZIP_SECURITY=true` removes `SECURE_ZIP_READER` and uses disabled
  ZIP security.
- If `JADX_ZIP_MAX_ENTRIES_COUNT` is set, it overrides the max entries count on
  the ZIP security object.
- `JADX_TMP_DIR` is used as a parent directory for a per-instance temp directory.
- `JADX_CONFIG_DIR` and `JADX_CACHE_DIR` override system app directories.

Use overrides only in a controlled disposable workspace:

```bash
export JADX_CONFIG_DIR="$PWD/.jadx-config"
export JADX_CACHE_DIR="$PWD/.jadx-cache"
export JADX_TMP_DIR="$PWD/.jadx-tmp"
jadx --print-files
```

Avoid disabling XML or ZIP security unless the task is specifically to reproduce
or inspect malformed resource behavior.

## ZIP and Archive Risks

JADX opens APK, AAB, XAPK, APKM, ZIP, AAR, and related archives. A hostile
container can attempt:

- Path traversal through entry names.
- Excessive entry counts.
- Zip bombs or misleading sizes.
- Huge resources that trigger memory pressure.
- Nested archive or split layouts that hide where code/resources came from.

Guidance:

- Keep ZIP security enabled by default.
- Use `-r` to skip resources if code triage is enough.
- Use `-s` for resource-only isolation when code loading is not needed.
- Run in isolated temp/cache/config directories.
- Keep the original archive and record rejected entries or load errors.
- Do not install third-party plugins while testing hostile containers unless
  the plugin itself is part of the test.

## XML and Package Risks

JADX decodes binary XML and resource XML. Secure XML parsing protects against
external-entity style behavior in XML parser paths. Package verification can
replace invalid package names with `INVALID_PACKAGE`.

Guidance:

- If package name or manifest package behavior matters, record whether XML
  security/package verification was disabled.
- Do not treat decoded XML as original bytes.
- For malformed XML, preserve parser errors and the original resource entry.
- If disabling XML security changes output, report both outputs and the reason
  for the unsafe run.

## Plugin Risk

Plugins can load inputs, add passes, customize resources, register options,
touch plugin files, and access configured ZIP readers. Installed plugins can
change generated code and resource output.

Guidance:

- Run `jadx plugins --list-all` before evidence extraction.
- Disable nonessential external plugins for clean runs.
- Preserve plugin versions and options.
- Install plugin JARs only from trusted local paths or expected marketplace
  location IDs.
- Treat plugin output as part of the analysis environment.

## Failure Modes

### No Classes

If no classes are loaded:

- With resources skipped, the CLI treats it as load failure.
- With resources enabled and sources requested, the CLI can warn and switch to
  decoding resources only.

Record whether the input was resource-only, malformed, encrypted, or missing
code.

### Load Errors

JADX can continue after load errors. Preserve:

- Error count and warnings.
- Input files responsible.
- Whether output was partial.
- Exit code.

### Decompilation Errors

For per-class/method errors:

- Re-run with `--show-bad-code`.
- Compare `auto`, `simple`, and `fallback`.
- Use smali or dex offsets for proof.
- Avoid absence claims from failed methods.

### Resource Decode Errors

Resource loading can emit text resources containing decode errors. Preserve
these as failure artifacts and keep the original resource entry.

### Output Collisions

Renaming and filesystem case behavior can alter paths:

- Record `--rename-flags`.
- Record `--fs-case-sensitive`.
- Use raw names for identity claims.

### Memory and Time Pressure

Large apps, nested resources, and decompiler failures can cause long runs or
memory pressure.

Mitigate with:

```bash
jadx -r --single-class <class> app.apk
jadx -s app.apk
jadx --threads-count 2 app.apk
```

For automation, time-box at the wrapper level and preserve partial output.

## Isolation Pattern

Use a case-local run directory:

```bash
mkdir -p case/{input,out,config,cache,tmp,logs}
export JADX_CONFIG_DIR="$PWD/case/config"
export JADX_CACHE_DIR="$PWD/case/cache"
export JADX_TMP_DIR="$PWD/case/tmp"

jadx --print-files > case/logs/files.txt
jadx --config none --threads-count 2 \
  -ds case/out/src -dr case/out/res \
  case/input/app.apk \
  > case/logs/stdout.txt 2> case/logs/stderr.txt
```

For risky resources:

```bash
jadx --config none -r -d case/out/src-only case/input/app.apk
jadx --config none -s -d case/out/res-only case/input/app.apk
```

Keep disabled-security experiments separate:

```bash
JADX_DISABLE_ZIP_SECURITY=true jadx --config none -s -d case/out/unsafe-res app.apk
```

Label unsafe output clearly and do not mix it with default-security output.

## Evidence Checklist

Capture:

- Security-related environment variables and `jadx --print-files`.
- Whether XML or ZIP security was disabled.
- ZIP entry count/zip bomb/path traversal errors when present.
- Package verification impact if manifest/package names are evidence.
- Plugin list, plugin options, and disabled plugins.
- Exit code, errors, warnings, partial output state.
- Decompilation/resource failures and fallback commands used.
- Isolation directory layout and cleanup policy.

## Official Source Paths

- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-cli/src/main/java/jadx/cli/JadxAppCommon.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/JadxArgs.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/security/JadxSecurityFlag.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-core/src/main/java/jadx/api/security/impl/JadxSecurity.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-commons/jadx-zip/src/main/java/jadx/zip/security/JadxZipSecurity.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-commons/jadx-zip/src/main/java/jadx/zip/security/DisabledZipSecurity.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-commons/jadx-app-commons/src/main/java/jadx/commons/app/JadxCommonFiles.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-commons/jadx-app-commons/src/main/java/jadx/commons/app/JadxTempFiles.java
