# Frida Instrumentation

Use Frida for dynamic instrumentation when native or server-side runtime
analysis needs in-process observation, API tracing, targeted hooks, or controlled
state changes. Prefer a traditional debugger when the task needs precise
single-step control, core dump analysis, or kernel-mode debugging.

Prefer installed `--help` output and the official Frida docs for exact option
spelling. Frida CLI tools, Frida Gadget, the JavaScript runtime, and language
bridges change across releases.

Treat Frida as mutable execution. Hooks, replacements, native calls, memory
writes, register/context edits, thread scheduling, spawned-process timing, and
Gadget load behavior can all change target state. Keep final evidence separate
from observations that only happen because instrumentation changed timing or
memory.

## Quick Commands

Install and record versions:

```text
python -m pip install --upgrade frida-tools
python -m pip show frida frida-tools
frida --version
frida --help
frida-trace --help
```

List local and remote devices:

```text
frida-ls-devices
frida-ps
frida-ps -D "$DEVICE_ID"
frida-ps -H "$HOST:$PORT"
```

Attach or spawn with a script:

```text
frida -n "$PROCESS_NAME" -l observe.js
frida -p "$PID" -l observe.js
frida -f "$EXECUTABLE" -l early.js
frida -H 127.0.0.1:27042 -n "$PROCESS_NAME" -l observe.js
```

Trace generated handlers:

```text
frida-trace --decorate -i "recv*" -i "send*" "$PROCESS_NAME"
frida-trace -p "$PID" -i "module.dll!*mem*"
frida-trace -p "$PID" -a "libtarget.so!0x1234"
```

## Session Setup

Record:

- Host OS, Python, `frida`, and `frida-tools` versions.
- Local, remote, or Gadget transport and endpoint details.
- Target process name, PID, executable path, target hash, and target version.
- Whether the session used attach, spawn, Gadget, `frida-trace`, or Python API.
- The exact command line and every loaded script or generated handler.

Connect to a remote frida-server:

```text
frida-ls-devices
frida-ps -H "$HOST:$PORT"
frida -H "$HOST:$PORT" -n "$PROCESS_NAME" -l observe.js
frida-trace -H "$HOST:$PORT" -i "open" "$PROCESS_NAME"
```

Bind remote endpoints to loopback or a controlled interface. Record whether any
token, TLS, port forward, or firewall rule was used.

## Modes

Frida documents three core modes:

- Injected: spawn or attach to an existing process and inject the Frida runtime.
- Embedded: load Frida Gadget inside the program when injected mode is not
  suitable.
- Preloaded: use a dynamic linker preload path, usually with Gadget configured
  to run autonomously.

Injected mode is the normal first choice for desktop or server processes you
own and authorized test targets where injection is allowed.

Embedded or preloaded mode is useful when the program must carry Gadget itself,
when early instrumentation must happen before normal attach is possible, or when
the target platform blocks normal injection.

Record the mode because it changes evidence:

- Injected mode depends on attach/spawn timing and target permissions.
- Gadget listen mode may block process startup until a controller attaches or
  resumes it.
- Gadget script mode can execute without a live host controller.

## Native Hooks

Passive native hook:

```javascript
const openPtr = Module.findExportByName(null, "open");

Interceptor.attach(openPtr, {
  onEnter(args) {
    this.path = args[0].readCString();
    this.flags = args[1].toInt32();
  },
  onLeave(retval) {
    send({ type: "open", path: this.path, flags: this.flags, result: retval.toInt32() });
  }
});
```

Hook a module export:

```javascript
const mod = Process.getModuleByName("libtarget.so");
const target = mod.getExportByName("parse_message");

Interceptor.attach(target, {
  onEnter(args) {
    send({ type: "parse_message", size: args[1].toUInt32() });
  }
});
```

Replace a function only when mutation is required:

```javascript
const target = Module.getExportByName(null, "strcmp");
const original = new NativeFunction(target, "int", ["pointer", "pointer"]);

Interceptor.replace(target, new NativeCallback((left, right) => {
  const l = left.readCString();
  const r = right.readCString();
  send({ type: "strcmp", left: l, right: r });
  return original(left, right);
}, "int", ["pointer", "pointer"]));
```

For final evidence, prefer passive `Interceptor.attach()` logging when that is
enough. If replacement is used, record the original behavior and exact
replacement script.

## Memory and Backtraces

Capture module and architecture facts:

```javascript
send({
  type: "process",
  pid: Process.id,
  arch: Process.arch,
  platform: Process.platform,
  pointerSize: Process.pointerSize,
  modules: Process.enumerateModules().map(m => ({ name: m.name, base: m.base, size: m.size }))
});
```

Read memory cautiously:

```javascript
const ptrValue = ptr("0x12345678");
send({ type: "bytes", data: hexdump(ptrValue, { length: 64, ansi: false }) });
```

Backtrace at a hook:

```javascript
Interceptor.attach(Module.getExportByName(null, "malloc"), {
  onEnter(args) {
    send({
      type: "malloc",
      size: args[0].toUInt32(),
      backtrace: Thread.backtrace(this.context, Backtracer.ACCURATE)
        .map(DebugSymbol.fromAddress)
        .map(String)
    });
  }
});
```

Record module base addresses and ASLR state with any address-level claim.

## frida-trace

Use `frida-trace` when broad API observation is more important than hand-written
logic at the start of a pass:

```text
frida-trace -p "$PID" -i "open" -i "read" -i "write"
frida-trace -n "$PROCESS_NAME" -i "module.dll!*Create*"
frida-trace -f "$EXECUTABLE" -i "connect" -i "send" -i "recv"
```

Generated handlers are starting points. Preserve edited handlers, record include
and exclude patterns, and rerun with narrower filters before using trace output
as evidence.

## Python Automation

Use Python when the campaign needs repeatable attach/spawn, message capture, or
artifact writing:

```python
import frida
import json

script_source = open("observe.js", "r", encoding="utf-8").read()
session = frida.attach("target-process")
script = session.create_script(script_source)

def on_message(message, data):
    print(json.dumps({"message": message, "data_len": len(data or b"")}, sort_keys=True))

script.on("message", on_message)
script.load()
input("press enter to detach")
session.detach()
```

Persist raw messages as JSONL and keep script source beside the log.

## Failure Modes

`frida: command not found`

- Install `frida-tools` in the active Python environment.
- Check `python -m pip show frida frida-tools`.
- Record whether the command came from a virtual environment, system Python, or
  packaged toolchain.

Cannot attach

- Confirm PID, process name, executable path, target owner, bitness, sandbox
  policy, code signing, and whether injection is allowed.
- Try attach by PID after listing processes with `frida-ps`.
- Preserve the exact Frida error.

Spawn succeeds but behavior changes

- Spawn timing, parent process, stdio, environment, and main thread resume
  behavior may differ from a normal launch.
- Reproduce with attach to an already-running process when final evidence should
  reflect normal launch behavior.

Script loads but hook never fires

- Confirm the module is loaded.
- Use `Process.enumerateModules()` and module-specific `enumerateExports()`.
- For late-loaded modules, use spawn/early attach, await spawn, or hook loader
  behavior first.
- Confirm symbol spelling and module offset.

Trace output is too noisy

- Narrow `-i`, `-I`, `-m`, `-j`, or `-y` patterns.
- Use exclusions after inclusions in the intended order.
- Edit generated handlers to filter before sending logs.
- Batch messages instead of sending per call on hot paths.

Instrumentation changed the observation

- Identify replacements, native calls, memory writes, context writes, thread
  scheduling, Stalker overhead, and spawn timing.
- Rerun with passive hooks or platform logs before reporting normal target
  behavior.

## Evidence Checklist

Collect:

- Frida, frida-tools, Python, and Gadget versions.
- Host OS, target OS, target architecture, and target process bitness.
- Transport details: local process, remote endpoint, Gadget config, or Python
  API.
- Target executable path, hash, process name, PID, version, and launch state.
- Mode of operation: injected, embedded Gadget, preloaded, frida-trace, Python
  API, or CLI REPL.
- Exact command lines, scripts, generated handlers, and host automation.
- Spawn versus attach path, resume behavior, stdio behavior, and environment
  differences.
- Module list, relevant exports or symbols, target addresses, and ASLR module
  bases.
- Hook definitions, replacement functions, and message schema.
- Raw message logs, trace output, platform logs, crash logs, and screenshots or
  recordings when UI state matters.
- All state-changing operations: replacements, calls, memory writes, register
  or context writes, Gadget config changes, and cleanup commands.
- Security-sensitive endpoint details: listen address, port, token, TLS
  certificate, port forwards, and remote host.

## References

- https://frida.re/docs/home/
- https://frida.re/docs/quickstart/
- https://frida.re/docs/installation/
- https://frida.re/docs/modes/
- https://frida.re/docs/gadget/
- https://frida.re/docs/frida-cli/
- https://frida.re/docs/frida-ps/
- https://frida.re/docs/frida-trace/
- https://frida.re/docs/frida-ls-devices/
- https://frida.re/docs/frida-kill/
- https://frida.re/docs/functions/
- https://frida.re/docs/messages/
- https://frida.re/docs/javascript-api/
