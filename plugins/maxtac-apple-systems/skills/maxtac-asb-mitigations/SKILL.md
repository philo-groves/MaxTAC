---
name: maxtac-asb-mitigations
description: "Use this skill when Apple exploit research has a proven primitive and needs mitigation-bypass direction, controls, and proof artifacts for ASB-quality evidence."
---

# MaxTAC ASB Mitigation Bypass

Use this skill after a primitive is proven and an Apple platform defense is shaping the next exploitation step. The goal is not to explain PAC, PPL, APRR, MTE, AMFI, TCC, sandboxing, or code signing in general. The goal is to convert the observed blocker into a bypass hypothesis, a test plan, and a packet of evidence that another researcher can verify.

Do not treat a mitigation as a dead end by default. Record the exact step blocked, the invariant that should have stopped the chain, and the alternate route being tested.

## Start With The Bypass Packet

Create or update `research/apple/<case-id>/mitigation-bypass-packet.md` with:

- Target product, hardware model or board when known, OS version, build number, architecture, and security state relevant to the claim.
- Target process, binary, service, kernel extension, DriverKit extension, firmware image, or policy component.
- Proven primitive before the mitigation boundary: disclosure, controlled write, pointer corruption, type confusion, object lifetime bug, IPC confusion, entitlement confusion, policy write, or code-loading control.
- Mitigation or policy boundary thought to be active.
- Expected invariant: what the mitigation should prevent on this build and hardware class.
- Observed failure or constraint: crash, panic, denial, code-signing error, permission failure, tag check, PAC failure, missing entitlement, broker refusal, or sandbox denial.
- Bypass hypothesis and why this path is plausible.
- Positive proof, negative control, and remaining blocker.
- Artifact index with hashes for crash logs, panic logs, unified logs, disassembly snippets, entitlements, sandbox profiles, dyld/kernelcache UUIDs, IPSW provenance bundles, and PoV source or binaries.

## Bypass Directions To Test

Prefer directions that can be proven with build-specific artifacts:

- Authorization drift: find where the check uses audit token, code-signing flags, entitlement state, team ID, bundle ID, sandbox profile, TCC attribution, or client identity differently from the later sink.
- Confused deputies: route the primitive through an Apple-signed helper, XPC service, Mach service, daemon, extension point, privileged broker, launchd job, or framework entry that legitimately owns the protected capability.
- Legitimate transition abuse: look for sanctioned state transitions such as JIT copy or unlock paths, `vm_protect` wrappers, signed pointer producers, file-provider or bookmark materialization, sandbox extension issuance, or entitlement-gated broker calls.
- Disclosure before corruption: for PAC, MTE, hardened allocators, ASLR, and pointer-obfuscation blockers, first prove whether the bug or a nearby side path leaks the context needed to make the corruption deterministic.
- Data-only impact: when control-flow takeover is blocked, test whether policy state, authorization state, credential material, task ports, sandbox extensions, TCC rows, launchd state, or trust decisions can be modified without violating the protected code or page-table invariant.
- Patch archaeology: use `maxtac-asb-ipsw` to compare vulnerable and fixed builds for changed checks, tightened entitlements, new sandbox rules, added audit-token validation, changed object lifetime, or new kernel/user boundary validation.
- Earlier-boundary bug: for KIP, PPL, SPTM/TXM, SCIP, SEP, or coprocessor boundaries, prefer bugs before the protection locks, bugs in the monitor or broker interface, or bugs in data consumed by the protected component.

## Mitigation-Specific Questions

Answer only the questions tied to the observed blocker:

- PAC: Which pointer is signed, where is it authenticated, what discriminator or context appears to matter, and is there a reusable producer of a valid signed pointer?
- APRR/JIT: Which thread, entitlement, JIT memory object, copy path, or permission transition is trusted, and can corruption happen before the trusted copy into executable memory?
- PPL/SPTM/TXM/KIP: Is the chain trying to patch protected code or page tables, or can it reach an accepted data-only or monitor-interface outcome?
- MTE/EMTE/TCE/MIE: Which allocation is tagged, where does the tag-bearing pointer originate, when does the tag check fire, and can impact occur before the checked access?
- AMFI/library validation/code signing: Which cdhash, platform bit, entitlement, trust cache, notarization, quarantine, or hardened-runtime condition is being checked, and is there a signed loader or broker path that makes the operation legitimate?
- Sandbox/TCC/privacy: Which actor is attributed, which database or policy file changes, which token or extension grants access, and does the sink trust a different identity than the source check?
- XPC/Mach/DriverKit: Which message fields, voucher, audit token, task identity, or entitlement snapshot are validated, and is the validation bound to the object used at the sink?

## Controls

Capture at least one positive proof and one negative control before calling a bypass viable:

- Same build and hardware with the vulnerable path disabled, patched, or unreachable.
- Same primitive against a value that should not satisfy the protected condition.
- Same PoV without the required entitlement, sandbox extension, launchd context, or TCC attribution.
- Vulnerable build versus fixed build when IPSW or installed-system comparison is available.
- Userland versus kernel or simulator versus physical-device separation when the proof could otherwise be misattributed.

## When To Read The Reference

Read `<skill-dir>/references/apple-platform-mitigations.md` only when exact mitigation properties are needed for the packet. Do not load it as general background. Pair this skill with `maxtac-asb-ipsw` when the bypass question depends on firmware diffs, kernelcache symbols, dyld shared cache changes, entitlements, sandbox profiles, or trust caches.

## Hard Rules

- Do not claim a mitigation bypass from a crash alone.
- Do not count disabled SIP, development mode, test entitlements, ad-hoc signing, injected libraries, or local policy weakening as bypass evidence unless the program explicitly accepts that environment.
- Do not describe a known mitigation at length unless that description explains a tested bypass direction.
- Do not use simulator behavior as physical-device evidence without an explicit reason.
- Do not call an issue exploitable because a historical bypass existed. Verify the current build and hardware path.
