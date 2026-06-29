---
name: maxtac-sast-surface-triage
description: "Use this skill when starting static surface triage for source code or existing decompiler output to map trust boundaries, dangerous code areas, entrypoints, sinks, invariants, and route hypotheses to auditors, OpenGrep, or control-flow graph analysis."
---

# MaxTAC SAST Surface Triage

Use this skill as the first static-analysis pass for a target slice. The goal is a small, evidence-oriented surface map that helps the parent agent choose focused tools and auditor subagents. Do not use this skill as a broad proof engine, final vulnerability classifier, or replacement for targeted auditors.

## Operating Rules

- Start from reachable entrypoints and security boundaries, not from a global keyword sweep.
- Keep the output small enough to paste into an auditor prompt or research note.
- Capture why a path matters: actor, trust boundary, controlled fields, protected asset, and security invariant.
- Prefer 2-4 strong hypotheses over many shallow guesses.
- Use `maxtac-source-codebase-memory` first when codebase-memory-mcp is available and architecture, route, symbol, or call-path orientation would reduce broad file exploration.
- Use `maxtac-sast-opengrep` for repeatable source-to-sink searches and `maxtac-sast-control-flow-graph` when reachability, guard ordering, state transitions, locks, or cleanup paths matter.
- Use `maxtac-core-subagents` after triage to route each hypothesis to a targeted, goal-bounded auditor.
- Do not create or promote findings from triage alone. Triage produces candidate hypotheses and evidence plans.
- Persist triage packets as audit or artifact evidence. If triage teaches durable subsystem behavior, rewrite that knowledge into the stable research library note instead of leaving the packet as the only markdown record.

## Triage Workflow

1. Define the target slice.
   - Name the component, version, language, and relevant source files or existing decompiler output.
   - Identify the expected attacker actor and any required starting privileges.
   - State the protected asset or boundary, such as kernel memory, tenant data, code execution, payment state, privacy data, or sandbox policy.

2. Inventory entrypoints.
   - List externally reachable APIs, RPC handlers, syscalls, IOCTLs, routes, parsers, file watchers, plugin hooks, message handlers, jobs, or helpers.
   - Record caller identity sources such as credentials, tokens, audit tokens, entitlements, file descriptors, ports, handles, session state, request metadata, or tenant IDs.
   - Mark entrypoints that deserialize, parse, copy, allocate, spawn, authorize, mutate state, or cross privilege boundaries.

3. Identify trust boundaries.
   - Userspace to kernel: syscalls, `ioctl`, `fcntl`, `setsockopt`, `sysctl`, `copyin`, `copyout`, user pointers, and kernel object handles.
   - IPC and messages: Mach messages, MIG stubs, XPC handlers, RPC services, shared descriptors, port rights, audit tokens, and message bodies crossing process or privilege domains.
   - Driver and user clients: IOKit user clients, DriverKit methods, external method tables, scalar inputs, structure inputs, async callbacks, shared memory mappings, and memory descriptors.
   - File, descriptor, vnode, and path: paths, file descriptors, fileports, vnodes, symlinks, mount state, extended attributes, and privileged filesystem operations.
   - Parser and loader: Mach-O, ELF, PE, dyld metadata, code signatures, certificates, fonts, images, archives, firmware blobs, property lists, packets, or custom binary formats.
   - Shared memory and DMA: ring buffers, mapped memory, memory entries, device buffers, firmware queues, packet descriptors, or DMA regions another actor can mutate asynchronously.
   - Credential, entitlement, and policy: credentials, audit tokens, sandbox state, MAC labels, code-signing flags, entitlements, task ports, persona identity, tenant IDs, or role claims.
   - Object lifetime and ownership: retain/release, get/put, borrowed versus owned returns, cleanup paths, callback registration, lock drops, teardown, or deferred frees.
   - Type and handle conversion: generic handles, selectors, ports, file descriptors, opaque pointers, message fields, vtables, operations tables, or protocol-specific structures.
   - Network to native parser: packet input, socket options, control messages, routing messages, mbufs, interface metadata, protocol state machines, and firewall or filter hooks.
   - Data to code: JITs, bytecode interpreters, BPF-style filters, plugin loading, `dlopen`, firmware loading, callback tables, function pointers, vtables, and indirect dispatch influenced by parsed or user-controlled state.
   - Privilege-separated helpers: launchd jobs, privileged helpers, broker services, sandbox escape surfaces, task or port transfer, fileport transfer, and service-mediated filesystem access.

4. Mark danger areas.
   - Command execution and privileged RCE: `system`, `popen`, `execve`, `posix_spawn`, `fork`, `dlopen`, `dlsym`, `request_firmware`, helper launch, plugin loading, callbacks, vtables, or function pointers.
   - Lifetime and refcounting: `malloc`, `free`, `new`, `delete`, `kalloc`, `kfree`, `retain`, `release`, `refcount`, `get`, `put`, cleanup labels, async callbacks, worker queues, and lock drops.
   - Buffer bounds and copies: `memcpy`, `memmove`, `bcopy`, `strcpy`, `sprintf`, `copyin`, `copyout`, `copy_from_user`, `copy_to_user`, fixed buffers, flexible arrays, indexes, lengths, counts, and offsets.
   - Integer arithmetic: allocation sizes, copy lengths, page rounding, element counts, offset math, multiplication, addition, truncation, signedness, and 32-bit to 64-bit conversions.
   - Path and object confusion: `open`, `openat`, `namei`, `lookup`, `vnode`, `realpath`, `readlink`, `unlink`, `rename`, mounts, symlinks, hardlinks, `../`, and missing no-follow or root constraints.
   - Usercopy and disclosure: partial initialization, structure padding, kernel pointers, privileged memory copied out, `printf("%p")`, `kprintf`, debug dumps, and inconsistent copy sizes.
   - Races and TOCTOU: checks separated from use by unlocks, sleeps, retries, callbacks, filesystem lookup, cache revalidation, async execution, or object teardown.
   - Type confusion: casts, `void *`, `container_of`, `dynamic_cast`, `static_cast`, `reinterpret_cast`, selectors, flavors, variant tags, vtables, ops tables, and opaque handles.
   - Parser bugs: magic values, headers, versions, flags, offsets, lengths, sections, segments, descriptors, TLVs, records, recursive structures, compression, and nested encodings.
   - Authorization and capability transfer: credentials, UIDs, GIDs, capabilities, entitlements, sandbox checks, task ports, file descriptors, handles, delegation, ownership, and access checks.
   - Secrets and debug backdoors: embedded tokens, private keys, debug unlock strings, test entitlements, hidden command modes, production bypass flags, and default credentials.

5. Identify invariants.
   - Write the intended rule in one sentence: "Only X may do Y to Z after condition C."
   - Check whether the invariant is enforced server-side or only in a client, caller, config, test, or documentation.
   - Find split enforcement, such as one function validating identity and another using object state later.
   - Note state transitions, one-time actions, quotas, ownership changes, role changes, privilege changes, and rollback behavior.

6. Rank hypotheses.
   - Prefer hypotheses with an attacker-controlled input, a clear security boundary, a plausible missing or reordered guard, and a reachable sink or state transition.
   - Demote hypotheses when the actor is not realistic, the dangerous operation is unreachable, or a guard dominates all uses.
   - Preserve uncertain but promising paths as "needs CFG" or "needs targeted auditor" instead of overclaiming.

## Auditor Routing

Use `maxtac-core-subagents` and `audit-helper.py --filter "<text>"` to find the final auditor IDs. The filters below are starting points, not fixed assignments.

| Triage signal | Useful auditor filters |
| --- | --- |
| Workflow invariant, skipped step, valid actions in invalid sequence | `business-logic`, `logic`, `state-machine`, `specification` |
| Login, MFA, recovery, partial authentication, session promotion | `logic-auth-state-machine`, `authn`, `session` |
| Role, group, invitation, admin bootstrap, delegated permissions | `logic-self-service-privilege`, `authz`, `access-control` |
| Premium feature, quota, license, subscription, plan checks | `logic-entitlement-bypass`, `entitlement`, `quota` |
| Refunds, discounts, balances, credits, purchases, reconciliation | `logic-payment-credit-abuse`, `payment`, `balance` |
| Duplicate submission, webhook retry, one-time action, replay | `logic-idempotency-replay`, `replay`, `race` |
| Approval, moderation, reviewer separation, maker-checker flow | `logic-approval-gate-bypass`, `approval`, `workflow` |
| Tenant, ownership, sharing, object relationship, IDOR | `logic-cross-tenant-relationship`, `tenant`, `authz` |
| Delete, disable, reset, destructive bulk action, integrity loss | `logic-destructive-action`, `integrity`, `dos` |
| AI tool authority, delegated identity, prompt-controlled action | `logic-ai-agent-authority`, `ai-agent`, `authorization` |
| Parser, decoder, packet framing, archive, structured data | `parser`, `deserialization`, `protocol-parser-framing`, `memory-oob-read` |
| Object lifetime, callback teardown, refcount, concurrent cleanup | `memory-uaf`, `memory-double-free`, `race` |
| Allocation/copy size mismatch, fixed buffer, attacker length | `memory-heap-overflow`, `memory-oob-read`, `memory-integer-overflow` |
| Type tags, opaque handles, selectors, vtables, object layout | `memory-type-confusion`, `type-confusion`, `dispatch` |
| Check/use split, namespace swap, symlink, mutable shared state | `race-toctou`, `race`, `filesystem` |
| Path traversal, archive extraction, symlink or platform path semantics | `path`, `filesystem`, `archive`, `cross-platform` |
| Secrets, credentials, token lifecycle, debug backdoor | `secrets`, `credential`, `asset-exposure` |
| Known primitive that may compose into a stronger impact | `chain-builder`, `exploitability`, `composition` |

## Handoff Template

Use `python3 <skill-dir>/scripts/packet.py` to create, lint, and convert SAST packets instead of relying on loose prose. The helper supports these packet types:

- `surface`: this skill's Surface Triage Packet.
- `cfg`: `maxtac-sast-control-flow-graph` Control-Flow Evidence.
- `opengrep`: `maxtac-sast-opengrep` Result Packet.

Use `packet.py lint` before routing packets into auditors or ledger updates. When handing packets to Core subagents, prefer `packet.py prompt` so persisted auditor prompts keep packet evidence structured.

Create a blank packet:

```
python3 <skill-dir>/scripts/packet.py create surface --output surface-packet.md
```

Create a packet with fields populated:

```
python3 <skill-dir>/scripts/packet.py create surface --output surface-packet.md \
  --set "Target slice=..." \
  --set "Actor and starting privileges=..." \
  --set "Protected asset or trust boundary=..." \
  --set "Candidate hypothesis=..." \
  --set "Confidence=medium"
```

Lint packets before they are used for auditor routing or finding updates:

```
python3 <skill-dir>/scripts/packet.py lint surface-packet.md cfg-evidence.md opengrep-result.md --strict
```

Convert one or more valid packets into a focused auditor prompt:

```
python3 <skill-dir>/scripts/packet.py prompt surface-packet.md cfg-evidence.md opengrep-result.md \
  --auditor-filter authz \
  --focus "Check actor reachability and guard dominance" \
  --output audit-prompt.md
```

The helper refuses to convert invalid packets unless `--allow-invalid` is passed. Do not use `--allow-invalid` for normal workflow handoff. The generated auditor prompt explicitly tells auditors that packets are structured triage and evidence, not proof of a validated, proofed, or reportable finding. Before spawning a subagent from a generated auditor prompt, pass it through `maxtac-core-subagents` via `audit-helper.py --prompt-file` or `audit_prompt_create` so the final subagent prompt includes Codex goal instructions and persistence paths.

Store generated packets in `tmp/` or the relevant subsystem's `artifacts/`. Do not let packets become the durable research library. When a packet closes a path or captures a reusable invariant, incorporate the conclusion into the corresponding system-focused markdown file and link back to the packet.

Produce this compact packet before spawning auditors or writing rules:

```markdown
## Surface Triage Packet

- Target slice:
- Actor and starting privileges:
- Protected asset or trust boundary:
- Entry points:
- Controlled inputs:
- Security invariant:
- Suspect guard, sink, or state transition:
- Key files/functions:
- Evidence collected:
- Evidence still needed:
- Suggested tools: OpenGrep / CFG / RE / DAST
- Suggested auditor filters:
- Candidate hypothesis:
- Confidence: low / medium / high
```

## Tool Handoff

- Use `maxtac-sast-opengrep` when a hypothesis needs repeatable searches across many files, taint-like source-to-sink checks, constant or symbolic propagation, or rule tests.
- Use `maxtac-sast-control-flow-graph` when a hypothesis depends on path feasibility, guard dominance, call chains, callbacks, lock order, cleanup paths, or multi-function state transitions.
- Use `maxtac-source-codebase-memory` when codebase-memory-mcp can provide architecture summaries, symbol discovery, route maps, call paths, ADRs, or diff impact before narrowing the packet.
- Use Android JADX for APK/DEX/resource decompiler output, or Binary RE skills such as Ghidra and Radare2 for native binaries, firmware payloads, binary-level xrefs, and call graphs.
- Use DAST skills when the triage path needs runtime confirmation, fuzzing, debugging, or a controlled proof environment.
- Use `maxtac-core-subagents` when linted packets are clear enough for a targeted, goal-bounded auditor to assess a bug class or mitigation boundary. Prefer an auditor prompt produced by `packet.py prompt` so surface, CFG, and OpenGrep evidence stay structured, then wrap it with the subagent helper before spawning.

## Output Quality

Good triage names a narrow boundary and explains why it is security-relevant. Weak triage lists dangerous keywords without actor control, reachability, or a protected asset. If the output is noisy, reduce scope to one entrypoint, one subsystem, or one invariant and repeat the workflow.
