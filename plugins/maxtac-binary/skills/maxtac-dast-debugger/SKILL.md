---
name: maxtac-dast-debugger
description: "Use this skill when binary or systems dynamic analysis requires debugger, instrumentation, crash replay, or runtime tooling such as Radare2 DBG, LLDB, GDB, x64dbg, WinDbg, or Frida."
---

# MaxTAC DAST Debugger

## Evidence Helper

Use `python3 <skill-dir>/scripts/debug-evidence.py` to collect debugger, instrumentation, replay, or crash evidence into `<workspace-root>/proof/<case-id>/`.

Initialize a debug evidence case:

```
python3 <skill-dir>/scripts/debug-evidence.py init \
  --tool lldb \
  --version-command "lldb --version" \
  --target "local parser harness" \
  --target-version "1.2.3 build 456" \
  --target-file ./harness \
  --scope "authorized local test target" \
  --environment "local macOS test host" \
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
| macOS native binaries, Linux native binaries with LLDB support, or LLVM-centered crash replay | LLDB | `<skill-dir>/references/lldb-debugger.md` |
| Linux native binaries or portable ELF crash replay | GDB | `<skill-dir>/references/gdb-debugger.md` |
| Windows user-mode binary debugging | x64dbg | `<skill-dir>/references/x64dbg-debugger.md` |
| Windows kernel-mode, crash dump, or deep OS-component debugging | WinDbg | `<skill-dir>/references/windbg-debugger.md` |
| Fallback binary debugging inside an r2 workflow | Radare2 DBG | `<plugin-root>/skills/maxtac-re-radare2/references/radare2-debugging.md` |
| Runtime instrumentation, native hooks, or API tracing | Frida | `<skill-dir>/references/frida-instrumentation.md` |
