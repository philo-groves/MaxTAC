---
name: maxtac-android-runtime-debugging
description: "Use this skill when Android research needs authorized ADB, logcat, JDWP, Frida, component launch, content-provider probing, appops, dumpsys, or runtime evidence capture."
---

# MaxTAC Android Runtime Debugging

Use this skill for authorized Android runtime observation and proof collection. Prefer the simplest device workflow that reproduces the behavior. Do not add virtualization or emulator setup guidance here; keep any future environment-management pack separate.

## Readiness

Record versions and target identity:

```text
adb version
adb devices -l
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk
adb shell getprop ro.product.cpu.abilist
adb shell pm list packages | grep <target>
adb shell dumpsys package <package>
```

Preserve package version, installer, signing certificate digest when available, granted permissions, app ops, target SDK, data directory ownership, and device/API level.

## Evidence Capture

Use Core proof or research folders for durable evidence. Capture raw command output, logs, screenshots, recordings, scripts, inputs, and package metadata.

Common captures:

```text
adb logcat -c
adb logcat -v threadtime
adb bugreport bugreport.zip
adb shell screencap -p /sdcard/maxtac-screen.png
adb pull /sdcard/maxtac-screen.png .
adb shell screenrecord /sdcard/maxtac-run.mp4
adb pull /sdcard/maxtac-run.mp4 .
```

Use package-scoped logs when possible:

```text
adb shell pidof <package>
adb logcat --pid=<pid> -v threadtime
```

## Component and IPC Probes

Launch activities and send explicit broadcasts only inside authorized scope:

```text
adb shell am start -n <package>/<activity> --es key value
adb shell am start -a android.intent.action.VIEW -d '<uri>'
adb shell am broadcast -n <package>/<receiver> -a <action> --es key value
adb shell am startservice -n <package>/<service>
```

Probe content providers cautiously and record both the command and returned rows/errors:

```text
adb shell content query --uri content://<authority>/<path>
adb shell content insert --uri content://<authority>/<path> --bind key:s:value
adb shell content update --uri content://<authority>/<path> --bind key:s:value --where '<where>'
```

For Binder or service hypotheses, record caller identity assumptions and use focused traces or Frida hooks before claiming an authorization bypass.

## JDWP and Debuggable Apps

Only attach to debuggable or otherwise authorized targets. Record whether debugger attachment is required for the behavior.

```text
adb jdwp
adb forward tcp:8700 jdwp:<pid>
jdb -attach localhost:8700
```

If a finding requires a debugger to alter control flow, memory, fields, or timing, keep that separate from report-ready proof unless the program accepts debugger-dependent evidence.

## Frida on Android

Use Frida for hooks, Java method observation, native JNI tracing, and targeted runtime state checks. Record Frida, frida-tools, frida-server or Gadget version, transport, target PID/package, and every script.

```text
frida-ls-devices
frida-ps -Uai
frida -U -n <package-or-process> -l observe.js
frida -U -f <package> -l early.js --no-pause
frida-trace -U -f <package> -j '*!*check*/su'
```

Basic Java probe:

```javascript
Java.perform(() => {
  const Build = Java.use("android.os.Build");
  send({ type: "device", sdk: Build.VERSION.SDK_INT.value });
});
```

Native library probe:

```javascript
const lib = Process.findModuleByName("libtarget.so");
if (lib) {
  send({ type: "module", name: lib.name, base: lib.base, size: lib.size });
}
```

Prefer passive hooks for final evidence. If scripts replace methods, call native functions, write memory, or change fields, record the mutation and reproduce without mutation before promoting the finding.

## Output

Persist:

- Device/API state, target package metadata, signing and install facts, and exact commands.
- Logs, screenshots, recordings, Frida/JDWP scripts, content-provider outputs, and raw errors.
- Whether the behavior reproduces from a clean app state and whether debugger/instrumentation changed execution.
- A concise handoff to Core, Source, Binary, JADX, or Android auditors with the actor, entry point, protected asset, and observed impact.
