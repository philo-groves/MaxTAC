# JADX GUI Debugging and Evidence

Use this reference when `jadx-gui` is part of the analysis: navigation, search,
manual renaming, comments, saved projects, GUI export, or smali debugging over
JDWP. Treat the GUI project as evidence state, not as invisible analyst scratch.

## Contents

- [Quick Checks](#quick-checks)
- [Project Files](#project-files)
- [GUI Cache Behavior](#gui-cache-behavior)
- [Search and Navigation Evidence](#search-and-navigation-evidence)
- [Manual Renames and Comments](#manual-renames-and-comments)
- [GUI Export](#gui-export)
- [Smali Debugger Model](#smali-debugger-model)
- [Debugger Evidence](#debugger-evidence)
- [Handoff Pack](#handoff-pack)
- [Official Source Paths](#official-source-paths)

## Quick Checks

Launch:

```bash
jadx-gui app.apk
```

Command-line options generally overlap with CLI options and override GUI
preferences for that launch:

```bash
jadx-gui --deobf --mappings-path mappings.tiny app.apk
jadx-gui --config none app.apk
```

Before relying on GUI state, save a project file:

```text
case-name.jadx
```

Keep the project file with the APK/DEX hash and JADX version.

## Project Files

JADX GUI project files use the `.jadx` extension. Source shows project data
includes:

- Input file paths.
- Tree expansions.
- Open tabs.
- Code data: comments and renames.
- Mappings path.
- Plugin options.
- Cache directory reference.
- Live reload setting.
- Search history.
- Resource search filter and size limit.

Guidance:

- Save the `.jadx` file before handoff.
- Preserve mapping files referenced by the project.
- Preserve plugin options if they affect decompilation or resources.
- Do not assume another analyst can reproduce GUI state from exported Java
  files alone.

## GUI Cache Behavior

The GUI wrapper initializes code and usage caches based on settings. It can use
memory or disk caches and uses the project cache directory for disk-backed
cache. Code cache registration is delayed through a prepare pass so plugins can
use cache-enabled decompilation after classes load.

Guidance:

- If GUI output differs from a clean CLI run, check settings, cache mode, plugin
  list, mappings, and project file.
- Use a clean `--config none` CLI run to reproduce final evidence.
- Preserve cache only when it is needed to explain GUI behavior; otherwise
  preserve the project and generated artifacts.

## Search and Navigation Evidence

GUI navigation features include decompiled code view, jump to declaration, find
usage, full-text search, and search providers for classes, methods, fields,
code, comments, and resources.

Evidence discipline:

- For "Find Usage", record whether the hit is a decompiler metadata use,
  unresolved use, override-related method, or text search result.
- For class/method/field search, record raw names and aliases.
- For code search, note that the search can trigger lazy decompilation.
- For resource search, record resource filters and size limits.
- For comments, preserve the project file.

Use GUI search as triage, then reproduce important hits through CLI/API output
or screenshots paired with raw artifacts.

## Manual Renames and Comments

Manual renames and comments are stored as code data in the project. They can be
applied back into `JadxArgs` when the project is opened.

Use them to document:

- Why an alias was chosen.
- Which smali offset verifies a decompiled claim.
- Whether a class was mapped from a stack trace, manifest component, or runtime
  event.
- Which search or debugger session produced the evidence.

Do not overwrite imported mappings with manual GUI edits unless that is the
intended workflow. Use mapping autosave modes intentionally and preserve the
before/after mapping files.

## GUI Export

The GUI export dialog exposes:

- Export path.
- Skip source decode.
- Skip resource decode.
- Export as Gradle project.
- Export Gradle type.

Gradle type is detected through the same export detection logic:

- Manifest plus `classes.jar`: Android library.
- Manifest plus ARSC: Android app.
- Otherwise: simple Java.

Guidance:

- Record export options in the handoff.
- Use CLI export for exact reproduction when possible.
- Do not treat an exported Gradle project as equivalent to the original app.

## Smali Debugger Model

The GUI smali debugger uses JDWP. Source-level behavior includes:

- Attach to host and port.
- JDWP handshake.
- Suspend all threads after successful attach.
- Breakpoints based on class ID, method ID, and code offset.
- Single-step into, over, and out.
- Resume and suspend.
- Read current frame, all frames, all threads, and thread names.
- Read method and class signatures.
- Read registers, fields, strings, arrays, and object signatures.
- Set register and field values.
- Listen for class prepare/unload events, breakpoints, method entry/exit,
  exceptions, field access/modification, monitor events, thread events, VM
  start/death, and single-step events.

Operational guidance:

- JDWP attach requires a debuggable target or an authorized debugging setup.
- If using ADB forwarding, record the device, package, process, local port, and
  forwarding command.
- After attach, the target is suspended. Set breakpoints, then resume.
- Breakpoints map to smali/JDWP locations, not Java source lines alone.
- Reading or setting registers/fields is runtime mutation or observation. Record
  it explicitly.

## Debugger Evidence

Capture for every debugger-backed claim:

- Device/emulator identifier and Android version.
- APK/split hashes installed on the device.
- Package/process name and PID.
- JDWP host and port or ADB forward command.
- JADX version, project file, mappings, and class aliases.
- Breakpoint class signature, method signature, method ID if available, and
  offset.
- Thread ID/name, frame ID, class ID, method ID, and offset at suspend.
- Register values, field values, object/string/array reads.
- Any values written through the debugger.
- Resume/step sequence and whether the app was already suspended.

Pair runtime values with static references: manifest entrypoint, raw class name,
method short ID, smali offset, and decompiled excerpt.

## Handoff Pack

For a GUI-heavy case, preserve:

```text
case/
  input/
    app.apk
  jadx/
    case.jadx
    mappings/
    exported-java/
    exported-json/
    screenshots/
    debugger/
      adb.txt
      breakpoints.txt
      registers.txt
      frames.txt
      notes.md
```

Include:

- `jadx --version`.
- `jadx --print-files` if the same install was used.
- GUI project file.
- Mapping files.
- Search notes and screenshots only as support, not as the sole artifact.
- CLI/API reproduction for final claims.

## Official Source Paths

- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/README.md
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/JadxWrapper.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/settings/JadxProject.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/ui/export/ExportProjectProperties.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/ui/export/ExportProjectDialog.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/device/debugger/SmaliDebugger.java
- https://github.com/skylot/jadx/blob/9d4babcdce555ec8f84ecf5b197b3cedfe3b40d3/jadx-gui/src/main/java/jadx/gui/search/providers/MergedSearchProvider.java
