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
