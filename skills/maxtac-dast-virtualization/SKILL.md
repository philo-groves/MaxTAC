---
name: maxtac-dast-virtualization
description: Use virtualization to create controlled environments for testing and analysis.
---

# MaxTAC DAST Virtualization
Virtualization provides controlled environments for testing and analysis.

## App / Service Research
For application and service vulnerability research, virtualization allows for isolation and easy management of test conditions. If the user does not have any virtualization mechanism available, ask to continue on their host operating system, but convey the limitations of testing without virtualization. Do not virtualize iOS or Android applications; they should be tested on physical devices (see "Mobile OS Research" below).

- **Docker**: Preferred for containerized applications and services. All desktop platforms supported. See: `<skill-dir>/references/docker-virtualization.md`
- **Virtual Machines**: When docker is not suitable, use a virtual machine for the host operating system (see "Desktop OS Research" below).

## Mobile OS Research
For mobile operating system vulnerability research, physical devices provide the most accurate representation of real-world conditions. This is especially important for iOS and Android, where simulators often use non-standard components and do not reflect the security characteristics of physical devices.

### Physical iOS
Prefer to use physical iOS devices instead of simulators. Before any simulator testing, ask the user if they have access to a physical iOS device, and if not, convey the limitations of simulator testing.

Use `xcrun devicectl` to manage and interact with physical iOS devices. If `xcrun` cannot be found from the current shell, check its default location at `/usr/bin/xcrun` and add it to the PATH if necessary.

See the `maxtac-dast-debugger` skill `xcrun` reference: `<plugin-root>/skills/maxtac-dast-debugger/references/xcrun-cli.md`

### Physical Android
Prefer to use physical Android devices instead of emulators. Before any emulator testing, ask the user if they have access to a physical Android device, and if not, convey the limitations of emulator testing.

Use `adb` to manage and interact with physical Android devices. If `adb` cannot be found from the current shell, check its default location at `/usr/local/bin/adb` and add it to the PATH if necessary.

See the `maxtac-dast-debugger` skill `adb` reference: `<plugin-root>/skills/maxtac-dast-debugger/references/adb-cli.md`

## Desktop OS Research
For desktop operating system vulnerability research, virtual machines provide a more controlled and consistent environment compared to physical hardware. This allows for better isolation and easier management of test conditions.

### Virtual macOS
Prefer to use Tart for virtual machines on macOS. If Tart cannot be found from the current shell, check its default location at `/opt/homebrew/bin/tart` and add it to the PATH if necessary.

See: `<skill-dir>/references/tart-virtualization.md`

### Virtual Windows
Prefer to use Hyper-V for virtual machines on Windows. If Hyper-V cannot be found from the current shell, check if it is enabled with: `Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V`

See: `<skill-dir>/references/hyper-v-virtualization.md`

### Virtual Linux
Prefer to use QEMU for virtual machines on Linux. If QEMU cannot be found from the current shell, check its default location at `/usr/local/bin/qemu-system-<arch>` and add it to the PATH if necessary.

See: `<skill-dir>/references/qemu-virtualization.md`