# Source Code Preparation

Use source preparation to turn a large native codebase into a map of attacker-controlled entry points, trust boundaries, object lifetimes, and candidate primitives. Prefer durable maps and short evidence packets over one-off notes. Preparation should make later scan, debate, primitive proof, and chain proof phases faster.

## Source Code Mapping

Build a repository map that explains how untrusted input enters privileged code and how authority, memory ownership, and object lifetime move across files.

### Native Entry Point Inventory

Create an entry-point index before deep auditing. Include the wrapper, policy gate, object lookup, core implementation, cleanup path, and copyout path where applicable.

- Syscalls and private syscalls: syscall tables, argument structs, `copyin`, `copyout`, `copyinstr`, file descriptor lookup, process credential checks, and compatibility wrappers.
- Mach and MIG: subsystem definitions, generated server stubs, descriptor counts, out-of-line memory, port right consumption, reply construction, and audit-token use.
- IOKit and DriverKit: user client external methods, scalar and structure input/output sizes, async callbacks, shared memory mappings, memory descriptors, registry properties, and entitlement gates.
- BSD kernel interfaces: `ioctl`, `fcntl`, `setsockopt`, `getsockopt`, `sysctl`, `proc_info`, `getattrlist`, `setattrlist`, `fsctl`, kqueue, workqueue, event, audit, and networking control paths.
- IPC services in source form: XPC/Mach service handlers, launchd labels, sandbox extensions, entitlement checks, fileport/taskport transfer, and audit-token-derived identity.
- Parsers and loaders: Mach-O, dyld metadata, code signatures, certificates, property lists, fonts or binary formats only when they cross a native privilege boundary.

### Cross-File Call Graphs

For high-value entry points, build a compact call graph from user input to impact. Keep the graph security-oriented rather than exhaustive.

- Start at the public entry point and follow input validation, privilege checks, object lookup, locking, allocation, and copyout.
- Mark each reference transfer: retain, release, borrowed return, move semantics, port right transfer, file descriptor install, vnode reference, task reference, map reference, mbuf ownership, and memory-entry ownership.
- Mark each lock and lifetime boundary: lock dropped before use, continuation return, async callback, workloop dispatch, thread wakeup, deferred free, garbage collection, or teardown path.
- Mark each authority transition: credential adoption, MAC policy decision, sandbox profile check, entitlement check, code-signing flag mutation, persona transition, task/port right creation, or cross-process object lookup.

### Generated and Build Artifacts

Generated code often hides the real boundary. Include it in the map when it validates counts, sizes, descriptors, or rights.

- MIG generated stubs and `.defs` files.
- Syscall tables and generated argument declarations.
- IOKit external method dispatch tables.
- Entitlement, sandbox, profile, or policy manifests.
- Tests that encode expected native error behavior.

## Data Flow Analysis

Track attacker-controlled data as typed native values, not just strings. Record where values are trusted, widened, truncated, copied, retained, or reinterpreted.

### Common Native Sources

- Raw syscall arguments, packed structs, user pointers, lengths, flags, offsets, counts, and enum selectors.
- Mach message bodies, port rights, descriptors, voucher data, audit tokens, and out-of-line memory.
- File descriptors, vnodes, paths, extended attributes, fork attributes, ACLs, fileports, and memory-backed files.
- Socket data, control messages, mbufs, route messages, NECP parameters, packet metadata, and shared ring indices.
- IOKit scalar inputs, structure inputs, memory mappings, notification ports, async references, and registry properties.
- Shared memory, commpage values, VM map ranges, memory entries, code-signing blobs, loader metadata, and slide/fixup records.
- Process identity material: pid, pidversion, uniqueid, uid/gid, audit token, persona id, coalition id, task port, thread port, and entitlement-derived booleans.

### Common Native Sinks

- Pointer arithmetic, array indexing, bitmap access, variable-length record parsing, and descriptor walking.
- Allocation sizes, copy sizes, element counts, page counts, offset plus length arithmetic, and integer casts.
- `copyout`, `copyoutstr`, reply message construction, external method outputs, and variable-size kernel-to-user records.
- Reference count changes, object install/remove, borrowed-object returns, cleanup labels, and error paths.
- VM map operations, memory object creation, remap/protect transitions, executable mapping, code-signing checks, and pager operations.
- Credential, task, port, sandbox, entitlement, MAC policy, TCC, persona, coalition, or code-signing state changes.
- Kernel callbacks reached after generic validation, including driver vtables, socket protocol callbacks, filesystem operations, and workqueue continuations.

## Threat Modeling

Build the threat model around attacker reachability and chain potential. A primitive can be valuable even when it does not satisfy the current session goal.

### Attacker Models

Define the weakest plausible attacker for each surface.

- Regular sandboxed app with no private entitlement.
- Sandboxed app with user-granted resource access.
- Same-user unprivileged process on macOS.
- Network input reaching Apple-owned userspace or kernel parsing.
- File or document opened by a privileged Apple component.
- IPC client with only a public Mach service name or inherited send right.
- Compromised lower-privilege service attempting to cross into a more privileged service, kernel, or driver.

### Native Trust Boundaries

Prefer concrete boundary statements:

- User memory to kernel memory.
- Untrusted Mach message to trusted server object.
- User-controlled file descriptor to kernel object.
- Sandboxed process identity to privileged policy decision.
- External packet/file/parser input to privileged native parser.
- Driver shared memory to kernel/firmware/provider logic.
- Borrowed object reference to owned object reference.
- Validated size/count to later size/count in a different subsystem.

### Chain Hooks

For each real behavior that is not reportable alone, preserve why it might matter later.

- Information leak that could defeat ASLR, PAC signing context secrecy, heap layout uncertainty, or pointer authentication assumptions.
- Metadata spoofing that reaches a later policy decision or attribution sink.
- Resource accounting mismatch that can shape timing, allocation, pressure, or scheduler state for another primitive.
- Parser gap that is gated by timing, entitlement, file format, launch path, or artifact availability.
- Same-process primitive that may become non-self when paired with IPC, shared memory, file import, or service-mediated execution.

## Native Bug Class Checklist

Use this checklist to seed scan hypotheses. For high-value surfaces, audit several classes rather than one narrow bug shape.

### Memory Safety

- UAF from cleanup races, async callbacks, borrowed returns, stale list entries, or reference transfer mismatches.
- OOB read/write from count confusion, descriptor walking, variable record parsing, page-boundary logic, or signedness mistakes.
- Integer overflow/truncation in `offset + size`, `count * elem_size`, page rounding, 32-bit compatibility, and userspace-to-kernel type conversion.
- Uninitialized or stale kernel data copied out through partial structure initialization, error exits, or variable-length records.
- Type confusion across port kobject types, file types, vnode types, memory-entry flavors, socket protocols, or driver user-client methods.

### Authorization and Policy

- Entitlement checked after object lookup or after side effects.
- Sandbox/MAC policy applied to one identity but action performed on another.
- Audit token, pid, pidversion, uniqueid, persona, or credential checked before a ref-dropping race.
- Capability transfer bugs: fileport, task port, thread port, memory entry, vnode, send right, or shared-memory mapping handed to the wrong subject.
- Public metadata accepted where downstream code assumes kernel-verified identity.

### Race and Lifetime

- Check/use split across lock drops, callbacks, continuations, blocking copyin/copyout, vnode recycle, process exit, thread exit, or object teardown.
- Error path cleanup that releases more references than it owns.
- Success path that returns a borrowed object as owned.
- Shared state updated before all preconditions are committed.
- Retry loops that revalidate size but not identity, type, generation, or policy.

### Parser and Format Logic

- Header fields validated independently but inconsistent together.
- Nested offsets validated against the wrong base or total size.
- First element, sentinel, or zero-count case handled differently from the general loop.
- Multiple format versions sharing one walker with version-specific layout assumptions.
- Kernel parser trusts userspace prevalidation from dyld, launchd, securityd, or another component.

### Resource and Accounting

- Per-message limit checked but aggregate limit skipped.
- Charge/debit performed against the wrong task, coalition, ledger, socket, vnode, or memory object.
- Cleanup fails to undo partial accounting.
- Quota or pressure state can force rare allocation, bind, reclaim, or error paths useful for chaining.

## Static Analysis

Use `rg` first for fast source mapping. Use `opengrep` when a structural rule will be reused or when many call sites share one vulnerability shape. Persist reusable rules and results under `data/maxtac/static/`.

Useful rule families for native targets:

- Usercopy size flows: user-controlled length reaches allocation, copy, descriptor, or reply size without shared bounds.
- Reference transfer contracts: functions named like create/copy/get/lookup/find return objects whose caller releases inconsistently.
- Policy-before-use: object mutation, port right creation, copyout, or cross-process lookup happens before entitlement, sandbox, MAC, or credential checks.
- Integer shape: `count * size`, `offset + length`, page rounding, and 32-bit compatibility conversions.
- Cleanup labels: error paths with multiple releases, partial initialization, or state insertion before failure-prone calls.
- Parser walkers: offset arrays, variable records, versioned structs, descriptor loops, and sentinel handling.

Validate custom `opengrep` rules before large scans, cap noisy rules, and save the exact command line with the results. Static findings should become primitive candidates only when the source path, attacker-controlled fields, and plausible impact are documented.

## Bug History Assessment

Analyze public CVEs, security release notes, and available commits to learn local bug patterns. For Apple-style source drops, compare source versions and adjacent subsystem changes when direct fix commits are unavailable.

- Identify the vulnerable function family and the boundary it served.
- Look for recurring fix shapes: added retain, moved entitlement check, bounded count, extra generation check, new MAC policy call, additional vnode/task/map ref, or parser range check.
- Search nearby code for the same pre-fix pattern.
- Record both the fixed sink and adjacent unfixed variants as future primitive hypotheses.

## Native STRIDE Prompts

Use STRIDE as a prompt set, but translate each category into native security terms.

- Spoofing: pid, audit token, persona, code-signing identity, bundle id, entitlement, port right, vnode, interface, or network endpoint confusion.
- Tampering: unauthorized mutation of kernel object state, privileged service state, code-signing flags, MAC labels, sandbox extensions, VM mappings, or driver/provider state.
- Repudiation: audit/session attribution mismatch, coalition/accounting mismatch, or log identity confusion with security impact.
- Information disclosure: kernel pointers, PAC material, heap/layout state, credentials, task metadata, vnode paths, sandbox decisions, or privileged parser state.
- Denial of service: only preserve if it can force a rare race, allocation shape, state transition, or chain-enabling side effect.
- Elevation of privilege: credential changes, sandbox escape, task/port acquisition, code execution, arbitrary read/write, TCC modification, or target-flag-capable register control.

## Preparation Output

End preparation with a short research packet under `data/maxtac/research/<domain>/<target>/` containing:

- Entry-point inventory and trust-boundary map.
- High-value call graphs with source paths.
- Attacker-controlled fields and their sinks.
- Policy and lifetime invariants the code appears to rely on.
- Candidate primitives, chain hooks, blockers, and suggested dynamic probes.
- Static-analysis rules or commands saved under `data/maxtac/static/` when used.
