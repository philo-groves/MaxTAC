---
name: maxtac-dast-debugger
description: "Use this skill when dynamic analysis requires debugger, instrumentation, device, browser, or runtime tooling such as Radare2 DBG, LLDB, GDB, x64dbg, WinDbg, Frida, ADB, xcrun, CDP, WebDriver BiDi, or WebKit debugging."
---

# MaxTAC DAST Debugger
MaxTAC performs debugging to understand the runtime behavior of the target and identify vulnerabilities that may not be apparent through static analysis.

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

## Binary Debuggers

### LLDB
Preferred for macOS binaries. All desktop platforms supported, but only iOS for mobile. A high-performance, open-source debugger developed as part of the LLVM project. It serves as the default debugger in Xcode on macOS and is widely used across Linux and other platforms. LLDB is primarily utilized to debug C, C++, Objective-C, and Swift code.

See: `<skill-dir>/references/lldb-debugger.md`

### GDB (GNU Debugger)
Preferred for Linux binaries. Linux and macOS only. A powerful command-line tool for C, C++, and other compiled languages that lets researchers inspect what is happening "inside" a program while it runs or after it crashes. It allows researchers to pause execution, step through code line-by-line, and modify variables to test bug fixes.

See: `<skill-dir>/references/gdb-debugger.md`

### x64dbg
Preferred for user-mode Windows binaries. Windows only. A user-mode debugger built for reverse engineering and malware analysis without source code. It supports both x86 and x64 binaries and provides a graphical interface for analyzing and debugging Windows applications.

See: `<skill-dir>/references/x64dbg-debugger.md`

### WinDbg
Preferred for kernel-mode Windows binaries. Windows only. A low-level symbolic debugger maintained by Microsoft designed for kernel-mode debugging, crash dump analysis, and deep Windows internals exploration. It supports both user-mode and kernel-mode debugging, but is particularly powerful for analyzing Windows operating system components, drivers, and complex applications.

See: `<skill-dir>/references/windbg-debugger.md`

### Radare2 DBG
Preferred when a first-choice debug option is not available. All desktop and most mobile platforms supported.

See the `maxtac-re-radare2` skill debugging reference: `<plugin-root>/skills/maxtac-re-radare2/references/radare2-debugging.md`

## Mobile Debuggers

### Android Debug Bridge (ADB)
Required for interacting with Android devices. Android only. A versatile command-line tool that lets researchers and power users communicate with Android devices to install apps, debug software, and run Unix shell commands.

See: `<skill-dir>/references/adb-cli.md`

### xcrun
Required for interacting with iOS devices. iOS only. Includes `xcrun simctl` for interacting with iOS simulators and `xcrun devicectl` for managing connected devices.

See: `<skill-dir>/references/xcrun-cli.md`

### Frida
Preferred for all mobile platforms, supplementing other mobile debug tools like `adb` and `xcrun`. Primarily used for dynamic instrumentation rather than traditional debugging.

See: `<skill-dir>/references/frida-instrumentation.md`

## Web Debuggers

### WebDriver BiDi
Preferred for modern web browsers. Newest web debugging protocol. Unlike classic WebDriver's request-response (HTTP) model, BiDi uses WebSockets to enable real-time, two-way communication.

See: `<skill-dir>/references/webdriver-bidi-debugger.md`

### Chrome DevTools Protocol (CDP)
Preferred for Chromium-based browsers without support for WebDriver BiDi. A set of APIs that allows researchers to instrument, inspect, debug, and profile Chromium-based browsers (like Google Chrome and Microsoft Edge) over a WebSocket connection.

See: `<skill-dir>/references/chrome-devtools-protocol-debugger.md`

### WebKit Debugging
Preferred for Safari and WebKit-based mobile browsers. Safari and WebKit-based mobile browsers only. Techniques and tools used to troubleshoot web content running on the WebKit engine (like Safari) or to debug the compiled WebKit source code itself.

See: `<skill-dir>/references/webkit-debugging.md`
