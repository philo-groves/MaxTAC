---
name: maxtac-dast-debugger
description: Use debugging to learn about runtime behavior and perform controlled instrumentation of software. Documented tools include Radare2 DBG, LLDB, GDB, x64dbg, WinDbg, Frida, ADB, xcrun, Chrome DevTools Protocol (CDP), WebDriver BiDi, and WebKit Debugging.
---

# MaxTAC DAST Debugger
MaxTAC performs debugging to understand the runtime behavior of the application and identify vulnerabilities that may not be apparent through static analysis.

## Binary Debuggers

### LLDB
Preferred for macOS binaries. All desktop platforms supported, but only iOS for mobile.

### GDB (GNU Debugger)
Preferred for Linux binaries. Linux and macOS only.

### x64dbg
Preferred for user-mode Windows binaries. Windows only.

### WinDbg
Preferred for kernel-mode Windows binaries. Windows only.

### Radare2 DBG
Preferred when a first-choice debug option is not available. All desktop and most mobile platforms supported.

## Mobile Debuggers

### Android Debug Bridge (ADB)
Required for interacting with Android devices. Android only.

### xcrun
Required for interacting with iOS devices. iOS only. Includes `xcrun simctl` for interacting with iOS simulators and `xcrun devicectl` for managing connected devices.

### Frida
Preferred for all mobile platforms, supplementing other mobile debug tools like `adb` and `xcrun`. Primarily used for dynamic instrumentation rather than traditional debugging.

## Web Debuggers

## WebDriver BiDi
Preferred for modern web browsers. Newest web debugging protocol.

### Chrome DevTools Protocol (CDP)
Preferred for Chromium-based browsers without support for WebDriver BiDi. A mature but limited web debugging protocol.

## WebKit Debugging
Preferred for Safari and WebKit-based mobile browsers. Safari and WebKit-based mobile browsers only.