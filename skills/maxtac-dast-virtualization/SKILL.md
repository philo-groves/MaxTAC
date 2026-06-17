---
name: maxtac-dast-virtualization
description: "Use this skill when dynamic testing or exploit validation needs controlled virtualized environments, snapshots, isolation, guest networking, hypervisors, containers, or repeatable lab setup."
---

# MaxTAC DAST Virtualization
Use isolation by default for dynamic testing, fuzzing, and exploit validation. If no lab mechanism is available, ask before continuing on the host and record the resulting limits.

## Environment Selection

| Target | Prefer | Notes and reference |
| --- | --- | --- |
| Containerized app or service | Docker | Use for service isolation and reproducible dependencies. See `<skill-dir>/references/docker-virtualization.md`. |
| macOS desktop target | Tart | Use when a VM snapshot is safer than host testing. See `<skill-dir>/references/tart-virtualization.md`. |
| Windows desktop or driver-adjacent target | Hyper-V | Check feature state with `Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V`. See `<skill-dir>/references/hyper-v-virtualization.md`. |
| Linux desktop, kernel, or appliance-like target | QEMU | Use when full VM control or architecture flexibility matters. See `<skill-dir>/references/qemu-virtualization.md`. |
| iOS target | Physical iOS device | Prefer physical devices before simulator testing. Use the `xcrun` reference at `<plugin-root>/skills/maxtac-dast-debugger/references/xcrun-cli.md`. |
| Android target | Physical Android device | Prefer physical devices before emulator testing. Use the `adb` reference at `<plugin-root>/skills/maxtac-dast-debugger/references/adb-cli.md`. |

Do not treat simulator or emulator behavior as final evidence for mobile OS security properties without documenting the gap from physical-device behavior.

## Evidence Handoff

Treat the lab environment as evidence whenever it affects reachability, reproducibility, isolation, exploitability, or report eligibility. Do not leave VM, container, emulator, simulator, or device setup only in chat history.

Persist environment evidence with the artifact it supports:

- Proof or exploit validation: write a lab note to `<workspace-root>/proof/<case-id>/lab.md` and place copied configs, command output, screenshots, exported settings, or snapshot metadata under `<workspace-root>/proof/<case-id>/artifacts/lab/`. Use `evidence_pack` when available for generic proof bundles.
- Fuzzing: record the lab in `<workspace-root>/fuzz/<campaign-id>/environment.md` and attach setup scripts, container manifests, VM configs, snapshot metadata, and network notes to the fuzz campaign artifacts.
- Debugging or runtime reproduction: include the lab identifier, snapshot, command lines, and device or guest state in the related `maxtac-dast-debugger` evidence case.
- Recon-only research: summarize durable setup facts in the relevant `research/` submodule and put supporting files under that submodule's `artifacts/lab/`.

Every lab handoff should include:

- Authorization scope, target name/version, date tested, and why virtualization or a physical device was chosen.
- Host OS and hardware facts that affect behavior, including CPU architecture, virtualization support, nested virtualization, GPU/device passthrough, and relevant security features.
- Hypervisor, container runtime, emulator, simulator, or device-control tool name and exact version.
- Guest OS, kernel/build, image source, image hash when available, installed dependencies, and target binaries or packages added after the base image.
- Snapshot, checkpoint, container image tag/digest, or physical-device state used before the test, plus restore or cleanup instructions.
- Network topology, exposed ports, DNS/proxy/VPN state, egress limits, rate limits, shared folders, clipboard or drive mounts, and host-to-guest management channels.
- Resource limits and nondeterminism sources such as CPU count, memory, disk, clock, ASLR/KASLR mode, debug flags, sanitizer state, or instrumentation.
- Exact setup, launch, revert, and teardown commands. Preserve config files such as Dockerfiles, compose files, QEMU command lines, Hyper-V VM exports, Tart commands, device-control commands, and firewall rules.
- Limitations: emulator/simulator gaps, missing hardware, snapshot drift, disabled mitigations, non-default capabilities, or host-only assumptions that weaken report-grade confidence.

Before handing a result to proof, validation, or reporting, confirm that a clean restore from the recorded snapshot or image can reproduce the relevant setup steps. If the lab cannot be restored, state that explicitly and keep the finding out of report-ready status until a reproducible environment exists.
