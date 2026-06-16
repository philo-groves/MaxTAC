# Frida Instrumentation

Use Frida for dynamic instrumentation when the task needs in-process runtime
observation or controlled runtime changes across Android, iOS, desktop, or
server targets. Prefer Frida for hooks, runtime API inspection, message-driven
instrumentation, generated function tracing, and automation around JavaScript
instrumentation. Prefer a traditional debugger when the task needs precise
single-step control, core dump analysis, or kernel-mode debugging.

Prefer the installed `--help` output and official Frida docs for exact option
spelling. Frida CLI tools, frida-server, Frida Gadget, the JavaScript runtime,
and language bridges change across releases.

Treat Frida as mutable execution. It can change target state through hooks,
method replacement, native calls, memory writes, register/context writes,
thread scheduling, spawned-process timing, Gadget load behavior, and generated
trace handlers. Keep final evidence separate from observations that only happen
because instrumentation changed timing, process state, app state, or memory.

## Contents

- [Quick Commands](#quick-commands)
- [Toolchain and Session Setup](#toolchain-and-session-setup)
- [Device Discovery and Connection](#device-discovery-and-connection)
- [Modes of Operation](#modes-of-operation)
- [Launch, Attach, and Process Control](#launch-attach-and-process-control)
- [Scripts, Messages, and RPC](#scripts-messages-and-rpc)
- [Native Hooks and Calls](#native-hooks-and-calls)
- [Java and Android Runtime](#java-and-android-runtime)
- [Objective-C, Swift, and Apple Runtime](#objective-c-swift-and-apple-runtime)
- [Modules, Memory, and Backtraces](#modules-memory-and-backtraces)
- [frida-trace and Handler Files](#frida-trace-and-handler-files)
- [Stalker and Instruction Tracing](#stalker-and-instruction-tracing)
- [Gadget and Embedded Instrumentation](#gadget-and-embedded-instrumentation)
- [Python Automation](#python-automation)
- [Evidence Automation](#evidence-automation)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Install and record versions:

```text
python -m pip install --upgrade frida-tools
python -m pip show frida frida-tools
frida --version
frida --help
frida-trace --help
```

List devices, processes, and apps:

```text
frida-ls-devices
frida-ps -U
frida-ps -Ua
frida-ps -Uai
frida-ps -D "$DEVICE_ID"
```

Attach or spawn with a script:

```text
frida -U -n "$PROCESS_NAME" -l observe.js
frida -U -p "$PID" -l observe.js
frida -U -f "$BUNDLE_OR_PACKAGE" -l early.js
frida -H 127.0.0.1:27042 -n Gadget -l observe.js
```

Trace generated handlers:

```text
frida-trace -U -i "open" -N "$PACKAGE"
frida-trace -U -f "$BUNDLE_OR_PACKAGE" -i "open"
frida-trace --decorate -i "recv*" -i "send*" "$PROCESS_NAME"
frida-trace -p "$PID" -i "module.dll!*mem*"
frida-trace -p "$PID" -a "libtarget.so!0x1234"
```

Android frida-server setup on a rooted or lab device:

```text
adb shell getprop ro.product.cpu.abilist
adb push frida-server /data/local/tmp/frida-server
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c /data/local/tmp/frida-server &"
frida-ps -U
```

Basic JavaScript probe:

```javascript
console.log(JSON.stringify({
  pid: Process.id,
  arch: Process.arch,
  platform: Process.platform,
  modules: Process.enumerateModules().length
}));
```

Run it:

```text
frida -U -n "$PROCESS_NAME" -l probe.js
```

## Toolchain and Session Setup

Install Frida CLI tools with Python:

```text
python -m pip install --upgrade frida-tools
```

Record exact tool versions:

```text
python --version
python -m pip show frida frida-tools
frida --version
frida-trace --version
frida-ls-devices
```

Use local help before relying on advanced flags:

```text
frida --help
frida-trace --help
frida-ps --help
frida-ls-devices --help
frida-kill --help
```

For remote-device work, record both sides:

```text
frida --version
adb shell "/data/local/tmp/frida-server --version"
```

If the remote side uses a built-in frida-server or Gadget, record where it came
from and how it was started. Version skew between local client tools, bindings,
frida-server, and Gadget is a common source of confusing behavior.

Keep scripts in an evidence directory, not only in REPL history. Prefer one
short script per observation so the final command stream is replayable.

## Device Discovery and Connection

List Frida-visible devices:

```text
frida-ls-devices
```

List processes on the default USB device:

```text
frida-ps -U
```

List running apps and installed apps:

```text
frida-ps -Ua
frida-ps -Uai
```

Target a specific device:

```text
frida-ps -D "$DEVICE_ID"
frida -D "$DEVICE_ID" -n "$PROCESS_NAME" -l observe.js
frida-trace -D "$DEVICE_ID" -i "open" -N "$PACKAGE"
```

Connect to a remote frida-server:

```text
frida-ps -H "$HOST:$PORT"
frida -H "$HOST:$PORT" -n "$PROCESS_NAME" -l observe.js
frida-trace -H "$HOST:$PORT" -i "open" "$PROCESS_NAME"
```

For Android, the `-U` path depends on Android platform tools and device
visibility:

```text
adb devices -l
adb shell getprop ro.product.cpu.abilist
frida-ps -U
```

For iOS, use the `xcrun` reference for device pairing, installation, launch,
and debug tunnel setup. Use Frida after the device and target app are reachable
through the chosen Frida mode.

Record:

- Host OS, Python, `frida`, and `frida-tools` versions.
- Device ID, USB versus remote transport, and frida-server or Gadget version.
- Target process name, PID, package ID, bundle ID, and app version.
- Whether the session used attach, spawn, await, Gadget, or frida-trace.

## Modes of Operation

Frida documents three core modes:

- Injected: spawn or attach to an existing process and inject the Frida
  runtime through frida-core, often using frida-server on mobile devices.
- Embedded: load Frida Gadget inside the program when injected mode is not
  suitable.
- Preloaded: use a dynamic linker preload path, usually with Gadget configured
  to run autonomously.

Injected mode is the normal first choice for rooted Android, jailbroken iOS,
desktop processes you own, and lab targets where injection is allowed.

Embedded or preloaded mode is useful when the app must carry Gadget itself,
when early instrumentation must happen before normal attach is possible, or
when the target platform blocks normal injection.

Record the mode because it changes evidence:

- Injected mode depends on attach/spawn timing and frida-server state.
- Gadget listen mode may block process startup until a controller attaches or
  resumes it.
- Gadget script mode can execute without a live host controller.
- Preload mode changes loader state and environment.

## Launch, Attach, and Process Control

Attach by process name:

```text
frida -U -n "$PROCESS_NAME" -l observe.js
```

Attach by PID:

```text
frida -U -p "$PID" -l observe.js
```

Spawn a package, bundle, or executable and load early instrumentation:

```text
frida -U -f "$BUNDLE_OR_PACKAGE" -l early.js
```

Attach to an application identifier when the installed tool supports it:

```text
frida -U -N "$BUNDLE_OR_PACKAGE" -l observe.js
```

Await a spawn in `frida-trace`:

```text
frida-trace -U -W "$SPAWN_PATTERN" -i "open"
```

Kill by PID through Frida:

```text
frida-kill -D "$DEVICE_ID" "$PID"
```

Attach and spawn paths differ. Spawn can catch startup behavior, but it changes
parentage, timing, environment, and sometimes app lifecycle behavior. Attach is
closer to an already-running target, but can miss early initialization.

For spawned targets, record whether the main thread was resumed manually or by
the tool. Local CLI behavior has changed across Frida releases, so preserve
the exact command output around spawn and resume.

## Scripts, Messages, and RPC

Use console output for quick manual probes:

```javascript
console.log("loaded pid=" + Process.id);
```

Use `send()` for structured messages that host tooling can capture:

```javascript
send({
  type: "module-count",
  pid: Process.id,
  count: Process.enumerateModules().length
});
```

Send binary data separately from the JSON message:

```javascript
const bytes = ptr("0x100000000").readByteArray(64);
send({ type: "memory", address: "0x100000000", length: 64 }, bytes);
```

Receive host messages in JavaScript:

```javascript
recv("control", message => {
  console.log("control=" + JSON.stringify(message.payload));
}).wait();
```

Expose RPC methods for automation:

```javascript
rpc.exports = {
  ping() {
    return {
      pid: Process.id,
      arch: Process.arch,
      platform: Process.platform
    };
  }
};
```

Use messages and RPC instead of scraping REPL text when an observation matters.
Keep the host script, target script, and output together.

Performance note: avoid calling `send()` on every hit of a hot function. Batch
events, sample, use counters, or move hot-path callbacks into lower-overhead
code when needed.

## Native Hooks and Calls

Resolve a module export:

```javascript
const libc = Process.getModuleByName("libc.so");
const openPtr = libc.getExportByName("open");
```

Attach to a native function:

```javascript
Interceptor.attach(openPtr, {
  onEnter(args) {
    this.path = args[0].readUtf8String();
  },
  onLeave(retval) {
    send({
      type: "open",
      path: this.path,
      result: retval.toInt32()
    });
  }
});
```

Call a native function:

```javascript
const strlen = new NativeFunction(
  Module.getGlobalExportByName("strlen"),
  "ulong",
  ["pointer"]
);

const text = Memory.allocUtf8String("test");
send({ type: "strlen", value: strlen(text).toString() });
```

Replace a native function only for explicit experiments:

```javascript
const original = new NativeFunction(openPtr, "int", ["pointer", "int"]);

Interceptor.replace(openPtr, new NativeCallback((pathPtr, flags) => {
  const path = pathPtr.readUtf8String();
  send({ type: "open-replaced", path });
  return original(pathPtr, flags);
}, "int", ["pointer", "int"]));
```

Replacing, calling, or modifying native functions can change program behavior.
For final evidence, prefer passive `Interceptor.attach()` logging when that is
enough. If replacement is used, record the original behavior and the exact
replacement script.

## Java and Android Runtime

Use `Java.perform()` when accessing app classes:

```javascript
Java.perform(() => {
  const Activity = Java.use("android.app.Activity");
  Activity.onResume.implementation = function () {
    send({ type: "Activity.onResume", className: this.$className });
    return this.onResume();
  };
});
```

Hook an overload explicitly:

```javascript
Java.perform(() => {
  const StringBuilder = Java.use("java.lang.StringBuilder");
  StringBuilder.append.overload("java.lang.String").implementation = function (s) {
    send({ type: "append", value: String(s) });
    return this.append(s);
  };
});
```

Run code on the main thread when the Android API requires it:

```javascript
Java.perform(() => {
  Java.scheduleOnMainThread(() => {
    send({ type: "main-thread", ok: true });
  });
});
```

Enumerate methods for targeting:

```javascript
Java.perform(() => {
  const groups = Java.enumerateMethods("*example*!on*/su");
  send({ type: "methods", groups });
});
```

Enumerate live instances carefully:

```javascript
Java.perform(() => {
  Java.choose("android.app.Activity", {
    onMatch(instance) {
      send({ type: "activity", className: instance.$className });
    },
    onComplete() {
      send({ type: "choose-complete" });
    }
  });
});
```

For Frida 17+ Gadget autonomous scripts, language bridges are no longer bundled
the same way as older runtime assumptions. When using Gadget script mode with
Java, Objective-C, or Swift bridges, check the installed Frida docs and bundle
imports as required by that release.

Record whether the target was a debuggable build, rooted device, emulator,
Gadget build, or normal release app. Those contexts change what Frida can see
and how defensible the evidence is.

## Objective-C, Swift, and Apple Runtime

Check Objective-C availability before using the API:

```javascript
if (ObjC.available) {
  send({ type: "objc-runtime", classCount: Object.keys(ObjC.classes).length });
}
```

Hook an Objective-C method implementation:

```javascript
if (ObjC.available) {
  const klass = ObjC.classes.NSFileManager;
  const method = klass["- fileExistsAtPath:"];

  Interceptor.attach(method.implementation, {
    onEnter(args) {
      const path = new ObjC.Object(args[2]).toString();
      send({ type: "fileExistsAtPath", path });
    }
  });
}
```

Schedule UI-affecting Objective-C work on the main queue:

```javascript
if (ObjC.available) {
  ObjC.schedule(ObjC.mainQueue, () => {
    send({ type: "main-queue", ok: true });
  });
}
```

For Swift, prefer symbol and trace discovery before hard-coding names:

```text
frida-trace -U -f "$BUNDLE_ID" -y "*TargetName*"
```

Apple platform observations depend heavily on launch path, signing, Developer
Mode, jailbreak state, Gadget embedding, debugserver state, and app lifecycle.
Record those details with the Frida command line.

## Modules, Memory, and Backtraces

List modules:

```javascript
send({
  type: "modules",
  modules: Process.enumerateModules().map(m => ({
    name: m.name,
    base: m.base.toString(),
    size: m.size,
    path: m.path
  }))
});
```

List exports for one module:

```javascript
const moduleName = "libtarget.so";
const moduleObj = Process.getModuleByName(moduleName);
send({
  type: "exports",
  module: moduleName,
  exports: moduleObj.enumerateExports().slice(0, 100)
});
```

Scan memory:

```javascript
const moduleObj = Process.getModuleByName("libtarget.so");
Memory.scan(moduleObj.base, moduleObj.size, "41 42 43 ??", {
  onMatch(address, size) {
    send({ type: "scan-match", address: address.toString(), size });
  },
  onComplete() {
    send({ type: "scan-complete" });
  }
});
```

Dump a small byte range:

```javascript
const address = Process.getModuleByName("libtarget.so").base;
const bytes = address.readByteArray(128);
send({ type: "bytes", address: address.toString(), length: 128 }, bytes);
```

Capture a backtrace from a hook:

```javascript
Interceptor.attach(Module.getGlobalExportByName("read"), {
  onEnter(args) {
    const frames = Thread.backtrace(this.context, Backtracer.ACCURATE)
      .map(DebugSymbol.fromAddress)
      .map(String);
    send({ type: "backtrace", frames });
  }
});
```

Memory reads and scans can fail if the range is unmapped, paged out, protected,
or interpreted in the wrong process. Memory writes, `Memory.patchCode()`, and
register/context modifications are state-changing and should be isolated as
experiments.

## frida-trace and Handler Files

Use `frida-trace` for quick function-tracing setup and handler generation:

```text
frida-trace -U -i "open" -N "$PACKAGE"
frida-trace -U -f "$PACKAGE" -i "open" -i "read"
frida-trace --decorate -i "recv*" -i "send*" "$PROCESS_NAME"
```

Include or exclude modules:

```text
frida-trace -p "$PID" -I "libtarget.so"
frida-trace -p "$PID" -I "libtarget.so" -x "libtarget.so!noisy_*"
frida-trace -p "$PID" -i "*open*" -X "msvcrt.dll"
```

Trace runtime-specific methods:

```text
frida-trace -U -f "$PACKAGE" -j "*!*onResume*/su"
frida-trace -U -f "$BUNDLE_ID" -m "-[ClassName methodName:]"
frida-trace -U -f "$BUNDLE_ID" -y "*SwiftSymbol*"
```

Trace by module offset when the function is not exported:

```text
frida-trace -p "$PID" -a "libtarget.so!0x4793c"
```

Put large option sets in a file:

```text
frida-trace -p "$PID" -O trace-options.txt
```

Remember:

- `frida-trace` generates JavaScript handler files.
- Generated handlers are examples meant to be edited.
- Include and exclude options are procedural; order affects the working set.
- `-o` can write messages to a file.
- `-S` can initialize the session with one or more scripts.
- `-P` exposes JSON parameters to handlers.

Keep the generated `__handlers__` directory with evidence when handler edits
matter. Do not summarize trace output without preserving the option list and
handler files that produced it.

## Stalker and Instruction Tracing

Use Stalker when function-level hooks are too coarse and instruction, block, or
call coverage matters.

Minimal pattern:

```javascript
const tid = Process.getCurrentThreadId();

Stalker.follow(tid, {
  events: {
    call: true,
    ret: false,
    exec: false,
    block: false,
    compile: false
  },
  onReceive(events) {
    send({ type: "stalker-events", byteLength: events.byteLength });
  }
});

setTimeout(() => {
  Stalker.unfollow(tid);
  Stalker.flush();
}, 1000);
```

Exclude known-noisy module ranges:

```javascript
const libc = Process.getModuleByName("libc.so");
Stalker.exclude({ base: libc.base, size: libc.size });
```

Stalker can be expensive and architecture-sensitive. Use short windows,
specific threads, module exclusions, and clear start/stop markers. Record event
types, target thread ID, excluded ranges, and duration.

## Gadget and Embedded Instrumentation

Use Gadget when injected mode is not suitable. Gadget is a shared library loaded
by the target program and controlled through a configuration file or autonomous
script mode.

Common Gadget configuration names:

```text
FridaGadget.config
libgadget.config.so
```

Minimal listen configuration:

```json
{
  "interaction": {
    "type": "listen",
    "address": "127.0.0.1",
    "port": 27042,
    "on_load": "wait"
  }
}
```

Attach to Gadget:

```text
frida -H 127.0.0.1:27042 -n Gadget -l observe.js
frida-trace -H 127.0.0.1:27042 -n Gadget -i "open"
```

Autonomous script configuration:

```json
{
  "interaction": {
    "type": "script",
    "path": "observe.js",
    "on_change": "reload"
  }
}
```

Record:

- Gadget binary name, architecture, source release, and file hash.
- Config file path and contents.
- Interaction type: listen, connect, script, or script-directory.
- Listen address, port, token, certificate, and `on_load` behavior.
- Whether target startup was blocked waiting for a controller.
- Whether script reload was enabled.

Do not expose Gadget or frida-server on shared networks without authentication
and scope controls. Treat a reachable Frida endpoint as control over the target
process.

## Python Automation

Use Python when the workflow needs repeatable device selection, structured
messages, RPC calls, or multiple scripts.

Basic attach:

```python
import frida
import json

def on_message(message, data):
    print(json.dumps({"message": message, "data_len": 0 if data is None else len(data)}))

device = frida.get_usb_device(timeout=5)
session = device.attach("target")
script = session.create_script("""
send({ type: "loaded", pid: Process.id });
""")
script.on("message", on_message)
script.load()
input("Press Enter to detach...")
session.detach()
```

Spawn, instrument, then resume:

```python
import frida

package = "com.example.app"
device = frida.get_usb_device(timeout=5)
pid = device.spawn([package])
session = device.attach(pid)
script = session.create_script("""
send({ type: "early", pid: Process.id });
""")
script.load()
device.resume(pid)
input("Press Enter to detach...")
session.detach()
```

RPC:

```python
import frida

device = frida.get_usb_device(timeout=5)
session = device.attach("target")
script = session.create_script("""
rpc.exports = {
  ping() {
    return { pid: Process.id, arch: Process.arch };
  }
};
""")
script.load()
print(script.exports_sync.ping())
session.detach()
```

Always handle detach, crash, and lost-device events in longer harnesses. Keep
Python output machine-readable when it will be used as evidence.

## Evidence Automation

Create a run directory:

```text
RUN_DIR="evidence/$(date +%Y%m%d-%H%M%S)-frida"
mkdir -p "$RUN_DIR"
python -m pip show frida frida-tools > "$RUN_DIR/pip-frida.txt"
frida --version > "$RUN_DIR/frida-version.txt"
frida-ls-devices > "$RUN_DIR/devices.txt"
frida-ps -Uai > "$RUN_DIR/apps.txt"
```

Create `probe.js`:

```javascript
send({
  type: "session",
  pid: Process.id,
  arch: Process.arch,
  platform: Process.platform,
  pointerSize: Process.pointerSize
});

send({
  type: "modules",
  modules: Process.enumerateModules().map(m => ({
    name: m.name,
    base: m.base.toString(),
    size: m.size,
    path: m.path
  }))
});
```

Run an attach capture:

```text
frida -U -n "$PROCESS_NAME" -l "$RUN_DIR/probe.js" \
  > "$RUN_DIR/frida-session.log" 2>&1
```

Run a generated trace:

```text
frida-trace -U -N "$PACKAGE" -i "open" -o "$RUN_DIR/frida-trace.log"
```

After a mobile run, pair Frida evidence with platform evidence:

```text
adb -s "$SERIAL" logcat -b main,system,crash -v threadtime -d \
  > "$RUN_DIR/logcat.txt"

xcrun devicectl device info processes --device "$UDID" \
  > "$RUN_DIR/ios-processes.txt"
```

Keep:

- Target script files.
- Host automation files.
- CLI command lines.
- Generated handler directories.
- Frida logs and platform logs.
- App inputs, package or bundle metadata, target hashes, and device metadata.

## Failure Modes

`frida: command not found`

- Install `frida-tools` in the active Python environment.
- Check `python -m pip show frida frida-tools`.
- Record whether the command came from a virtual environment, system Python, or
  packaged toolchain.

No USB device

- Confirm platform tooling first: `adb devices -l` for Android or `xcrun`
  device state for iOS.
- Run `frida-ls-devices`.
- Prefer a direct USB connection for report evidence.
- Confirm frida-server or Gadget is actually running on the device when needed.

Cannot attach

- Confirm PID, process name, app identifier, and target bitness.
- Check permissions, sandbox policy, root/jailbreak state, code signing, and
  whether the target allows injection.
- Try attach by PID after listing processes with `frida-ps`.
- Preserve the exact Frida error.

Spawn succeeds but behavior changes

- Spawn timing, parent process, app lifecycle, stdio, environment, and main
  thread resume behavior may differ from a normal launch.
- Reproduce with attach to an already-running process when final evidence
  should reflect normal launch behavior.

Script loads but hook never fires

- Confirm the module is loaded.
- Use `Process.enumerateModules()` and module-specific `enumerateExports()`.
- For late-loaded modules, use spawn/early attach, await spawn, or hook loader
  behavior first.
- Confirm symbol spelling, method overload, Objective-C selector, or module
  offset.

`Java.perform()` work is missing app classes

- The app class loader may not be ready yet.
- Use `Java.perform()`, not top-level `Java.use()` for app classes.
- Confirm process/package selection and profile/user selection.
- For Gadget script mode on newer Frida, confirm bridge imports and bundling.

Objective-C API unavailable

- Check `ObjC.available`.
- Confirm the process actually has the Objective-C runtime loaded.
- Confirm Apple platform, target process, and launch path.

Trace output is too noisy

- Narrow `-i`, `-I`, `-m`, `-j`, or `-y` patterns.
- Use exclusions after inclusions in the intended order.
- Edit generated handlers to filter before sending logs.
- Batch messages instead of sending per call on hot paths.

Frida endpoint exposed unintentionally

- Check frida-server, Gadget listen address, and port.
- Bind to loopback or a controlled lab interface.
- Use tokens or TLS where supported by the selected mode.
- Remove port forwards and stop servers after the run.

Instrumentation changed the observation

- Identify replacements, native calls, memory writes, context writes,
  Java/ObjC method implementations, thread scheduling, Stalker overhead, and
  spawn timing.
- Rerun with passive hooks or platform logs before reporting normal target
  behavior.

## Evidence Checklist

Collect:

- Frida, frida-tools, Python, frida-server, and Gadget versions.
- Host OS, target OS, target architecture, and target process bitness.
- Device ID, transport (`-U`, `-D`, `-H`, remote, Gadget), and endpoint details.
- Target package, bundle ID, process name, PID, app version, and launch state.
- Mode of operation: injected, embedded Gadget, preloaded, frida-trace,
  Python API, or CLI REPL.
- Exact command lines, scripts, generated handlers, and host automation.
- Spawn versus attach path, resume behavior, stdio behavior, and environment
  differences.
- Module list, relevant exports or symbols, target addresses, and ASLR module
  bases.
- Hook definitions, method overloads, selectors, replacement functions, and
  message schema.
- Raw message logs, trace output, platform logs, crash logs, and screenshots or
  recordings when UI state matters.
- All state-changing operations: replacements, calls, memory writes, register
  or context writes, Java/ObjC implementation changes, Gadget config changes,
  frida-kill, and platform cleanup commands.
- Security-sensitive endpoint details: listen address, port, token, TLS
  certificate, port forwards, and remote host.

## References

- https://frida.re/docs/home/
- https://frida.re/docs/quickstart/
- https://frida.re/docs/installation/
- https://frida.re/docs/modes/
- https://frida.re/docs/gadget/
- https://frida.re/docs/android/
- https://frida.re/docs/ios/
- https://frida.re/docs/frida-cli/
- https://frida.re/docs/frida-ps/
- https://frida.re/docs/frida-trace/
- https://frida.re/docs/frida-ls-devices/
- https://frida.re/docs/frida-kill/
- https://frida.re/docs/functions/
- https://frida.re/docs/messages/
- https://frida.re/docs/javascript-api/
- https://frida.re/docs/stalker/
- https://frida.re/docs/best-practices/
- https://frida.re/docs/troubleshooting/
- https://github.com/frida/frida
- https://github.com/frida/frida-tools
