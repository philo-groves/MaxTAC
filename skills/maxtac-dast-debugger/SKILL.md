---
name: maxtac-dast-debugger
description: Use debugging to learn about runtime behavior and perform controlled instrumentation of software. Documented tools include Radare2 DBG, LLDB, GDB, x64dbg, WinDbg, Frida, ADB, xcrun, Chrome DevTools Protocol (CDP), WebDriver BiDi, and WebKit Debugging.
---

# MaxTAC DAST Debugger
MaxTAC performs debugging to understand the runtime behavior of the application and identify vulnerabilities that may not be apparent through static analysis.

## Binary Debuggers

### Radare2 DBG
All desktop and most mobile platforms supported.

### LLDB
All desktop platforms supported, but only iOS for mobile.

### GDB (GNU Debugger)
Linux and macOS only.

### x64dbg
Windows only, often used for debugging user-mode applications.

### WinDbg
Windows only, often used for debugging kernel-mode applications and services.

## Mobile Debuggers

### Frida
All mobile platforms supported, but primarily used for dynamic instrumentation rather than traditional debugging.

### Android Debug Bridge (ADB)
Android only.

### xcrun
iOS only. Includes `xcrun simctl` for interacting with iOS simulators and `xcrun devicectl` for managing connected devices.

## Web Debuggers

### Chrome DevTools Protocol (CDP)
Mature web protocol, supported by most Chromium-based browsers.

## WebDriver BiDi
Newest web debugging protocol, supported by modern desktop browsers like Chrome and Firefox.

## WebKit Debugging
Safari and WebKit-based mobile browsers only.