---
name: maxtac-dast-debugger
description: "Use this skill when dynamic analysis requires debugger, instrumentation, device, browser, or runtime tooling such as Radare2 DBG, LLDB, GDB, x64dbg, WinDbg, Frida, ADB, xcrun, CDP, WebDriver BiDi, or WebKit debugging."
---

# MaxTAC DAST Debugger

## Evidence Helper

Use `python3 <skill-dir>/scripts/debug-evidence.py` to collect debugger, instrumentation, replay, device, browser, or crash evidence into `<workspace-root>/proof/<case-id>/`.

When the MaxTAC MCP server is available, prefer the `debug_evidence` tool before invoking the script directly. Set `action` to `init`, `capture`, `add-artifact`, `lint`, or `summary`; the MCP tool calls the same helper and returns captured stdout plus parsed JSON for summaries.

Initialize a debug evidence case:

```
python3 <skill-dir>/scripts/debug-evidence.py init \
  --tool lldb \
  --version-command "lldb --version" \
  --target "local parser harness" \
  --target-version "1.2.3 build 456" \
  --target-file ./harness \
  --scope "authorized local lab target" \
  --environment "macOS VM snapshot abc123" \
  --command-line "lldb -- ./harness crash.min"
```

Capture command output:

```
python3 <skill-dir>/scripts/debug-evidence.py capture debug-20260616T000000Z-abc123 \
  --label replay \
  --command "lldb --batch -o run -o bt -- ./harness crash.min"
```

Attach artifacts such as crash logs, traces, bugreports, screenshots, recordings, or core dumps:

```
python3 <skill-dir>/scripts/debug-evidence.py add-artifact debug-20260616T000000Z-abc123 \
  --category crash-log \
  --artifact ./crash.log
```

Before proof or report handoff, run:

```
python3 <skill-dir>/scripts/debug-evidence.py lint debug-20260616T000000Z-abc123 --strict
python3 <skill-dir>/scripts/debug-evidence.py summary debug-20260616T000000Z-abc123
```

## Tool Selection

Read only the reference for the selected runtime or evidence source.

| Need | Prefer | Reference |
| --- | --- | --- |
| macOS native binaries, Apple-platform C/C++/Objective-C/Swift, iOS device debugging | LLDB | `<skill-dir>/references/lldb-debugger.md` |
| Linux native binaries or portable ELF crash replay | GDB | `<skill-dir>/references/gdb-debugger.md` |
| Windows user-mode binary debugging | x64dbg | `<skill-dir>/references/x64dbg-debugger.md` |
| Windows kernel-mode, crash dump, or deep OS-component debugging | WinDbg | `<skill-dir>/references/windbg-debugger.md` |
| Fallback binary debugging inside an r2 workflow | Radare2 DBG | `<plugin-root>/skills/maxtac-re-radare2/references/radare2-debugging.md` |
| Android device control, logs, shell, install, or harness launch | ADB | `<skill-dir>/references/adb-cli.md` |
| iOS simulator or connected-device control | xcrun | `<skill-dir>/references/xcrun-cli.md` |
| Runtime instrumentation, mobile hooks, or API tracing | Frida | `<skill-dir>/references/frida-instrumentation.md` |
| Modern browser debugging with bidirectional events | WebDriver BiDi | `<skill-dir>/references/webdriver-bidi-debugger.md` |
| Chromium-family protocol debugging | CDP | `<skill-dir>/references/chrome-devtools-protocol-debugger.md` |
| Safari or WebKit target debugging | WebKit Debugging | `<skill-dir>/references/webkit-debugging.md` |
