---
name: maxtac-core-static-analysis
description: Static analysis guidance, including code danger areas and static analysis engine (opengrep) usage.
---

# MaxTAC Core Static Analysis
Use this skill when static analysis must be performed at any stage of research, from recon to proofing. Includes instructions for opengrep, guidance for code danger areas, and how to identify trust boundaries.

## Static Analysis Engine
The primary source code static analysis engine is `opengrep`, expected to be available on the CLI. Instead of manually auditing thousands of lines of code or guessing where a vulnerability lives, Opengrep allows describing the structure of security flaws using YAML rules. All opengrep research files should be persisted to `static/`

Unlike source code targets, `opengrep` cannot directly analyze binaries. However, `opengrep` is compatible with decompiled C and C-psuedocode. Before performing static analysis on a binary target with `opengrep`, it should be decompiled.

- Custom Taint Analysis: Opengrep tracks data from unverified sources (e.g., HTTP requests or external APIs) to dangerous sinks (e.g., SQL execution or command line). Use the `--taint-intrafile` flag to map how untrusted data propagates through the application to enforce strict trust boundaries.
- Security Control Verification: Write custom rules to verify that internal API calls bypass unencrypted connections, restrict sensitive actions to specific user roles, or enforce mandatory data sanitization.
- Dependency & API Mapping: Use semantic patterns to immediately find where deprecated libraries or forbidden cloud SDKs are imported into a codebase.

Opengrep rules use code syntax patterns rather than complex Abstract Syntax Tree (AST) manipulation. This makes it easy to translate your system's data flows into rules. For an example, see: `opengrep-sql-injection-example.yml`

### Opengrep Best Practices
Best practices involve writing modular rules and properly leveraging advanced taint features.

- Validate Before Scanning: Always run `opengrep validate <rules_directory>` to verify that your rules parse correctly before executing a full repository scan.
- Apply Dynamic Timeouts: Enable `--dynamic-timeout` to automatically scale timeouts based on file size, optimizing scan speeds for small vs. large codebases.
- Limit Matches: Use `max_match_per_file: 5` to prevent OpenGrep from overwhelming your output or slowing down when it hits a repetitive, large-scale issue.
- Utilize Cross-Function Taint: Take advantage of OpenGrep's open features by using `--taint-intrafile` to track user-controlled input across different functions within the same file. See the [Intrafile Taint Analysis](https://github.com/opengrep/opengrep/wiki/Intrafile-tainting-tutorial) tutorial for more information.
- Handle Higher-Order Functions: If your codebase relies on JavaScript/TypeScript, ensure you utilize OpenGrep's taint-tracking support for higher-order functions ⁠[Higher Order Functions Tutorial](https://github.com/opengrep/opengrep/wiki/Higher-order-functions-tutorial) (e.g., `.map()`, `.forEach()`) to find vulnerabilities hidden in callback logic.

## Source Code Danger Areas
Inspect code comments, string, and documentation gaps in the source code. Use `rg` expressions or `opengrep` rules to quickly locate functions known to cause remote command execution, buffer overflows, and other vulnerabilities. For large source code workspaces, verify the expression is filtered correctly to reduce noise. If still too noisy, only search one specific module or file at a time.

- Command Execution / Privileged RCE: Look for attacker-controlled data reaching command execution, helper launch, module/plugin loading, firmware loading, or indirect function dispatch. Keywords: `system()`, `popen()`, `execve()`, `posix_spawn()`, `fork()`, `dlopen()`, `dlsym()`, `call_usermodehelper`, `request_firmware`, function pointers, vtables, callbacks.
- Use-After-Free / Double-Free / Bad Refcounting: Audit ownership transfers, cleanup paths, async callbacks, and lock drops where an object may be freed while still reachable. Keywords: `malloc()`, `calloc()`, `realloc()`, `free()`, `new`, `delete`, `kalloc`, `kfree`, `kmem_alloc`, `kmem_free`, `retain`, `release`, `refcount`, `get`, `put`, `cleanup`, `goto fail`.
- Buffer Overflow / OOB Read-Write: Search for unchecked copies, variable-length records, descriptor walking, fixed-size stack buffers, and array indexing from user-controlled lengths or counts. Keywords: `memcpy()`, `memmove()`, `bcopy()`, `strcpy()`, `strcat()`, `sprintf()`, `snprintf()`, `copyin`, `copyout`, `copy_from_user`, `copy_to_user`, `buf`, `len`, `count`, `offset`.
- Integer Overflow / Truncation / Sign Confusion: Look for size calculations that feed allocation, copy, indexing, page rounding, or structure parsing. Keywords: `size_t`, `uint32_t`, `int`, `long`, `count *`, `offset +`, `len +`, `round_page`, `PAGE_SIZE`, casts between signed/unsigned or 32/64-bit types.
- Path Traversal / Filesystem Object Confusion: Check path-based operations where untrusted paths, file descriptors, vnodes, symlinks, mount points, or relative paths cross a privilege boundary. Keywords: `open()`, `openat()`, `namei`, `lookup`, `vnode`, `realpath`, `readlink`, `unlink`, `rename`, `mount`, `../`, `O_NOFOLLOW`, `chroot`.
- Usercopy / Kernel-User Boundary Bugs: Audit transitions between user memory and kernel memory, especially size validation mismatches and partial initialization before copyout. Keywords: `copyin`, `copyout`, `copyinstr`, `copy_from_user`, `copy_to_user`, `get_user`, `put_user`, `user_addr_t`, `__user`, `uaddr`, `ulen`.
- Race Conditions / TOCTOU: Look for checks separated from use by lock drops, blocking calls, callbacks, retries, object lookup, or filesystem operations. Keywords: `lock`, `unlock`, `mutex`, `spinlock`, `rwlock`, `atomic`, `sleep`, `wait`, `wakeup`, `async`, `workqueue`, `dispatch_async`, `lookup`, `revalidate`.
- Type Confusion / Object Confusion: Search where generic handles, ports, descriptors, vtables, or opaque pointers are cast into specific object types. Keywords: `void *`, `casts`, `container_of`, `dynamic_cast`, `static_cast`, `reinterpret_cast`, `vtable`, `ops`, `kobject`, `ioctl`, `selector`, `flavor`, `type`.
- Parser / Binary Format Bugs: Focus on native parsers for Mach-O, ELF, PE, firmware blobs, fonts, images, archives, certificates, IPC messages, or driver-specific structures. Keywords: `magic`, `header`, `version`, `flags`, `offset`, `length`, `section`, `segment`, `descriptor`, `TLV`, `record`, `parse`, `decode`.
- Info Leak / Uninitialized Memory Disclosure: Look for kernel or privileged memory copied back to userspace before full initialization, or logs/errors exposing pointers and layout. Keywords: `copyout`, `copy_to_user`, `memset`, `bzero`, `struct`, `padding`, `uninitialized`, `printf("%p")`, `kprintf`, `debug`, `dump`.
- Authorization / Capability Transfer Bugs: Audit where credentials, entitlements, sandbox checks, file descriptors, handles, ports, or task references are checked too late or transferred to the wrong subject. Keywords: `cred`, `uid`, `gid`, `capable`, `entitlement`, `sandbox`, `MAC`, `audit_token`, `task`, `port`, `handle`, `fd`, `permission`, `access`.
- Hard-Coded Secrets / Debug Backdoors: Still useful, but reframe toward privileged binaries and firmware: embedded keys, debug unlock strings, test entitlements, hidden command modes, or production bypass flags. Keywords: `secret`, `password`, `token`, `private key`, `debug`, `test`, `backdoor`, `unlock`, `admin`, `entitlement`, `AKIA`, `BEGIN PRIVATE KEY`.

## Identify Trust Boundaries
- Userspace to Kernel Boundary: Syscalls, `ioctl`, `fcntl`, `setsockopt`, `sysctl`, `proc_info`, `copyin`, `copyout`, and user pointers crossing into kernel memory.
- IPC / Message Boundaries: Mach messages, MIG stubs, XPC handlers, RPC-like native services, shared descriptors, port rights, audit tokens, and message bodies crossing process or privilege domains.
- Driver / User Client Interfaces: IOKit user clients, DriverKit methods, external method dispatch tables, scalar inputs, structure inputs, async callbacks, shared memory mappings, and memory descriptors.
- File Descriptor / Vnode / Path Boundaries: Code that turns user-controlled paths, file descriptors, fileports, vnodes, symlinks, mount state, or extended attributes into privileged filesystem operations.
- Parser / Loader Boundaries: Native parsers that convert raw bytes into trusted structures: Mach-O, ELF, PE, dyld metadata, code signatures, certificates, fonts, images, archives, firmware blobs, property lists, or protocol packets.
- Shared Memory / DMA Boundaries: Ring buffers, mapped memory, memory entries, device buffers, firmware queues, packet descriptors, or DMA regions where another actor can mutate data asynchronously.
- Credential / Entitlement / Policy Boundaries: Transitions where code checks or derives authority from credentials, audit tokens, sandbox state, MAC labels, code-signing flags, entitlements, task ports, or persona identity.
- Object Lifetime / Ownership Boundaries: Places where references change ownership or validity: retain/release, get/put, borrowed vs. owned returns, cleanup paths, callback registration, lock drops, teardown, or deferred frees.
- Type / Handle Conversion Boundaries: Code that converts generic handles, selectors, ports, file descriptors, opaque pointers, or message fields into real kernel objects, vtables, operations tables, or protocol-specific structures.
- Network to Kernel / Native Parser Boundary: Packet input, socket options, control messages, routing messages, mbufs, interface metadata, protocol state machines, and firewall/filter hooks.
- Data-to-Code Boundaries: JITs, bytecode interpreters, BPF/eBPF-style filters, plugin loading, dlopen, firmware loading, callback tables, function pointers, vtables, and indirect dispatch influenced by parsed or user-controlled state.
- Privilege-Separated Helper Boundaries: Launchd jobs, privileged helpers, sandbox escape surfaces, task/port transfer, fileport transfer, service-mediated filesystem access, and any helper that performs privileged work for a less-privileged caller.