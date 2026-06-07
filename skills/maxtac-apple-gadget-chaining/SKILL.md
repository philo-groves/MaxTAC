---
name: maxtac-apple-gadget-chaining
description: Inventory Apple code-reuse gadget constraints for authorized MaxTAC research. Use when dyld shared cache, kernelcache, arm64e, PAC, BTI, indirect branch gadgets, call surfaces, side-effect gadgets, or gadget provenance affects a JOP or call-oriented chain.
---

# MaxTAC Apple Gadget Chaining

Use this skill to inventory gadget evidence and provenance without assembling a weaponized chain. The goal is to decide whether the target has credible call surfaces, dispatchers, and side-effect candidates for a specific build.

## Source Anchors

- Apple Platform Security, OS integrity and PAC: `https://support.apple.com/guide/security/operating-system-integrity-sec8b776536b/web`
- Apple open-source dyld: `https://github.com/apple-oss-distributions/dyld`
- Apple security updates index: `https://support.apple.com/en-us/100100`

## Apple-Specific Mitigations

- Gadgets are build, image, cache UUID, architecture slice, and slide dependent.
- arm64e PAC and BTI constrain indirect branches, returns, function pointers, block pointers, and method/vtable paths.
- Kernelcache, dyld shared cache, app binary, JIT region, and shared library gadgets are not interchangeable.
- SPTM/PPL and code signing generally push research toward code reuse or data-only effects rather than writable executable pages.

## Common Bypass Directions

- Inventory provenance first: exact image, UUID, symbol state, architecture, and source artifact.
- Prefer side-effect calls and legitimate dispatch surfaces over raw "pop register; branch" thinking.
- Track clobbers, required register state, memory reads/writes, PAC status, BTI landing status, and cleanup.
- If gadget quality is poor, redirect to heap grooming, PAC reuse, stack/context pivoting, or data-only impact.

## CVE Precedents

- CVE-2016-4657: WebKit memory corruption, a historical code-reuse chain component.
- CVE-2020-27930: FontParser memory corruption with code-execution impact.
- CVE-2023-41064: ImageIO buffer overflow with reported active exploitation.
- CVE-2023-32439: WebKit type confusion with code-execution impact.

## Workflow Example

Hypothetical dyld shared cache inventory:

1. Record dyld shared cache UUID, OS build, target process, and architecture slice.
2. Disassemble only the exact artifact in scope.
3. Run `scripts/gadget_inventory.py` on the disassembly text to summarize indirect-branch, call, PAC, BTI, and return-like instructions.
4. Manually classify candidates by side effect and mitigation constraints.
5. Store the inventory under the domain target directory and route any chain feasibility question to `maxtac-apple-jop-chaining`.

## Helper Script

```bash
otool -tvV TargetBinary > target.disasm.txt
python <skill-dir>/scripts/gadget_inventory.py target.disasm.txt --output data/maxtac/research/webkit/candidate/gadget-inventory.md
```

## Handoff

Return:

```text
Gadget inventory:
Domain:
Artifact identity:
Architecture and UUID:
Candidate classes:
PAC/BTI constraints:
Missing chain primitive:
Next skill:
Ledger action:
```
