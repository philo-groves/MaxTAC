# Xcrun CLI

Use `xcrun` as the stable entrypoint for Xcode-private tools. For physical iOS
research, the important subcommand is usually `devicectl`, which speaks to
CoreDevice-backed services on paired devices. Prefer it over simulator commands
when validating behavior on real iOS hardware.

## Contents

- [Quick Commands](#quick-commands)
- [Xcode Selection](#xcode-selection)
- [Device Discovery](#device-discovery)
- [Pairing, Trust, and Developer Mode](#pairing-trust-and-developer-mode)
- [Developer Disk Images](#developer-disk-images)
- [App Install and Lifecycle](#app-install-and-lifecycle)
- [Launch Inputs](#launch-inputs)
- [Files, Containers, and Crash Artifacts](#files-containers-and-crash-artifacts)
- [Process and Device State](#process-and-device-state)
- [Logs and Diagnostics](#logs-and-diagnostics)
- [CoreDevice Debug Tunnel](#coredevice-debug-tunnel)
- [Automation Patterns](#automation-patterns)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Toolchain sanity:

```text
xcode-select --print-path
xcodebuild -version
xcrun --version
xcrun --find devicectl
xcrun --kill-cache
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun --find devicectl
```

Device discovery:

```text
xcrun devicectl list devices
xcrun devicectl list devices -q --json-output devices.json
xcrun devicectl list devices --hide-default-columns --columns Identifier,Name,Platform,State
xcrun devicectl list devices --filter "Platform == 'iOS' AND State == 'connected'"
```

Device readiness:

```text
xcrun devicectl manage pair --device "$UDID"
xcrun devicectl list preferredDDI
xcrun devicectl manage ddis update
xcrun devicectl device info details --device "$UDID"
xcrun devicectl device info lockState --device "$UDID"
xcrun devicectl device info ddiServices --device "$UDID"
```

App lifecycle:

```text
xcrun devicectl device install app --device "$UDID" ./Target.app
xcrun devicectl device uninstall app --device "$UDID" "$BUNDLE_ID"
xcrun devicectl device process launch --device "$UDID" --terminate-existing "$BUNDLE_ID"
xcrun devicectl device process launch --device "$UDID" --console --terminate-existing "$BUNDLE_ID"
xcrun devicectl device process launch --device "$UDID" --start-stopped "$BUNDLE_ID"
xcrun devicectl device info processes --device "$UDID"
```

App data:

```text
xcrun devicectl device info files \
  --device "$UDID" \
  --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID"

xcrun devicectl device copy from \
  --device "$UDID" \
  --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID" \
  --source "Documents/repro.log" \
  --destination "./repro.log"

xcrun devicectl device copy to \
  --device "$UDID" \
  --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID" \
  --source "./seed.db" \
  --destination "Documents/seed.db"
```

## Xcode Selection

`xcrun` resolves tools through the active developer directory. Do not assume the
system-wide selection is the desired Xcode, especially on hosts with stable and
beta Xcodes installed.

Prefer one-shot selection for research sessions:

```text
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun devicectl list devices
DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer xcrun devicectl list devices
```

Use a system-wide switch only when the whole host should follow that Xcode:

```text
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
```

If tool lookup looks stale after switching Xcodes:

```text
xcrun --no-cache --find devicectl
xcrun --kill-cache
```

Useful lookup probes:

```text
xcrun --find devicectl
xcrun --log --find devicectl
xcrun --verbose --find devicectl
xcrun --sdk iphoneos --show-sdk-path
xcrun --sdk iphoneos --show-sdk-version
xcodebuild -showsdks
```

Do not use the Command Line Tools-only developer directory for physical device
work. If `xcode-select --print-path` returns `/Library/Developer/CommandLineTools`
and `devicectl` is missing, select a full Xcode.app.

## Device Discovery

Prefer UDIDs over names. Names collide, contain spaces, and can change during a
session. Use names only for manual one-offs.

Human-readable listing:

```text
xcrun devicectl list devices
```

Column-filtered listing:

```text
xcrun devicectl list devices \
  --hide-default-columns \
  --columns Identifier,Name,Platform,OSVersion,State \
  --filter "Platform == 'iOS' AND State == 'connected'"
```

JSON listing:

```text
xcrun devicectl list devices -q --json-output devices.json
jq . devices.json
```

For scripts, parse the JSON output, not the terminal table. The human stdout is
for people and changes across Xcode versions. If the JSON schema is unfamiliar,
inspect it first and then select by identifiers, platform, state, and transport.

Resilient recursive extraction for quick triage:

```text
jq -r '.. | objects
  | select(has("identifier") and has("name"))
  | [.name, .identifier] | @tsv' devices.json
```

Record the host Xcode version with device listings because CoreDevice behavior
and JSON shape are Xcode-coupled:

```text
xcodebuild -version
xcrun devicectl list devices -q --json-output devices.json
```

## Pairing, Trust, and Developer Mode

For a physical iOS target, check these before deeper troubleshooting:

- The device is unlocked.
- The host is trusted on the device.
- Developer Mode is enabled on the device.
- A full Xcode.app, not only Command Line Tools, is active.
- The cable supports data, not only charging.
- The device is visible to `devicectl`, not only Finder.

Pair explicitly:

```text
xcrun devicectl manage pair --device "$UDID"
```

If pairing state is wedged, remove the device from Xcode Devices and Simulators,
disconnect it, reconnect it, accept the trust prompt, and pair again. Avoid
unpairing casually during a long research session because it can invalidate
service state and force another physical trust flow.

For wireless device work, prefer USB when collecting report evidence. Wireless
CoreDevice paths add local-network permissions, Bonjour discovery, VPN/proxy
interference, and stale tunnel state.

## Developer Disk Images

Modern iOS development services depend on Developer Disk Image state managed by
CoreDevice. Do not search only the old Xcode bundle `DeviceSupport` path when
debugging iOS 17+ failures.

Inspect DDI state:

```text
xcrun devicectl list preferredDDI
xcrun devicectl device info ddiServices --device "$UDID"
```

Refresh DDI state:

```text
xcrun devicectl manage ddis update
```

Useful failure interpretation:

- `No usable DDI found`: active Xcode is too old, DDI cache is stale, or the
  device OS is newer than the selected Xcode supports.
- `CoreDeviceError` around DDI compatibility: run `list preferredDDI`, update
  DDIs, then update Xcode if the host still reports incompatible content.
- Device preparation loops: check pairing/trust first, then DDI state, then
  close Xcode/Console/Safari and retry with a clean `devicectl` command.

Record the DDI state when a finding depends on debugging, installation, launch,
or on-device service availability.

## App Install and Lifecycle

Install the device build product, not the simulator product:

```text
xcrun devicectl device install app \
  --device "$UDID" \
  "DerivedData/Build/Products/Debug-iphoneos/Target.app"
```

Install may accept `.ipa` on current toolchains, but `.app` is the predictable
debug path. Use `xcrun devicectl help device install app` on the host before
depending on package formats in automation.

Uninstall by bundle identifier:

```text
xcrun devicectl device uninstall app --device "$UDID" "$BUNDLE_ID"
```

List installed apps and confirm the exact bundle identifier before launching:

```text
xcrun devicectl device info apps --device "$UDID"
```

Launch with stale-process cleanup:

```text
xcrun devicectl device process launch \
  --device "$UDID" \
  --terminate-existing \
  "$BUNDLE_ID"
```

Stream stdout/stderr and wait for exit:

```text
xcrun devicectl device process launch \
  --device "$UDID" \
  --console \
  --terminate-existing \
  "$BUNDLE_ID" > launch.log 2>&1
```

`--console` is intentionally blocking. For long tests, run it in a managed
background process and write to a file. Do not confuse a blocked terminal with a
hung install.

Start stopped for debugger attach:

```text
xcrun devicectl device process launch \
  --device "$UDID" \
  --start-stopped \
  "$BUNDLE_ID"
```

Stop a process by PID when `--terminate-existing` is not enough:

```text
xcrun devicectl device info processes --device "$UDID"
xcrun devicectl device process signal --device "$UDID" --pid "$PID" --signal SIGTERM
xcrun devicectl device process signal --device "$UDID" --pid "$PID" --signal SIGKILL
```

Prefer `SIGTERM` first when preserving crash evidence matters. Use `SIGKILL`
only to clear a wedged state.

## Launch Inputs

Pass process arguments after `--`:

```text
xcrun devicectl device process launch \
  --device "$UDID" \
  "$BUNDLE_ID" -- arg1 arg2
```

Set environment variables as a JSON object when the host help supports it:

```text
xcrun devicectl device process launch \
  --device "$UDID" \
  --terminate-existing \
  --environment-variables '{"USE_PORT":"8100","FEATURE_FLAG":"1"}' \
  "$BUNDLE_ID"
```

Open a deep link or Universal Link payload:

```text
xcrun devicectl device process launch \
  --device "$UDID" \
  --terminate-existing \
  --payload-url "myapp://repro/path?case=1" \
  "$BUNDLE_ID"
```

Payload URL launch is useful for DAST because it exercises URL parsing,
navigation dispatch, app delegate/scene delegate handling, and auth-bound route
logic without manually tapping through the UI.

When a launch option is rejected, run the host-local help before rewriting the
workflow:

```text
xcrun devicectl help device process launch
xcrun devicectl device process launch --help
```

`devicectl` options have changed across Xcode releases. Treat local help as the
source of truth for option spelling.

## Files, Containers, and Crash Artifacts

List an app container:

```text
xcrun devicectl device info files \
  --device "$UDID" \
  --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID"
```

Restrict listing to a subdirectory:

```text
xcrun devicectl device info files \
  --device "$UDID" \
  --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID" \
  --subdirectory "Documents"
```

Pull a file:

```text
xcrun devicectl device copy from \
  --device "$UDID" \
  --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID" \
  --source "Documents/repro.log" \
  --destination "./repro.log"
```

Push a seed file:

```text
xcrun devicectl device copy to \
  --device "$UDID" \
  --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID" \
  --source "./seed.json" \
  --destination "Documents/seed.json"
```

Directory copy behavior has varied by Xcode and domain. If a directory pull
fails, list first, then copy explicit files. For automated evidence collection,
write target output to a known file under `Documents` or `Library/Caches`.

Avoid `/tmp` for durable PoV output. On iOS it is inside the app sandbox and may
be cleared across reinstall, relaunch, or cleanup paths. Resolve the app's
Documents directory at runtime and write evidence there.

List system crash logs:

```text
xcrun devicectl device info files \
  --device "$UDID" \
  --domain-type systemCrashLogs
```

After a crash, collect both:

- app-owned logs from `appDataContainer`;
- system crash artifacts from `systemCrashLogs`.

Jetsam reports, assertion failures, and signal crashes may appear outside the
app container. Always check system crash logs before concluding the app merely
exited.

## Process and Device State

Process list:

```text
xcrun devicectl device info processes --device "$UDID"
```

Device details:

```text
xcrun devicectl device info details --device "$UDID"
xcrun devicectl device info hardware --device "$UDID"
xcrun devicectl device info displays --device "$UDID"
xcrun devicectl device info lockState --device "$UDID"
xcrun devicectl device info apps --device "$UDID"
xcrun devicectl device info ddiServices --device "$UDID"
```

Use `details` and `hardware` to record device model, OS build, architecture, and
connection state. Use `lockState` before launch or file operations; locked
devices can produce misleading service failures.

Reboot as a last-mile cleanup step:

```text
xcrun devicectl device reboot --device "$UDID"
```

Rebooting changes state. Capture current errors and diagnostics first.

## Logs and Diagnostics

Collect CoreDevice diagnostics:

```text
xcrun devicectl diagnose --devices "$UDID"
```

On Xcode versions with device sysdiagnose support:

```text
xcrun devicectl help device sysdiagnose
xcrun devicectl device sysdiagnose --device "$UDID"
```

Use `diagnose` for host/device communication failures and bug reports. Use
device sysdiagnose when the target behavior involves system services, crashes,
networking, power, background execution, or profile/entitlement enforcement.

`--console` captures app stdout/stderr for a launched process. It is not a full
substitute for OSLog, system logs, or crash reports. If a finding depends on
`os_log`, subsystem logs, SpringBoard events, networking daemons, or
entitlementd/profiled behavior, gather system logs separately.

## CoreDevice Debug Tunnel

iOS 17+ device services use the newer CoreDevice/remoted path. Some debuggers
need the `debugproxy` address and port instead of the older MobileDevice
debugserver flow.

One practical way to keep a trusted tunnel alive is to observe a Darwin
notification that will not be posted:

```text
xcrun devicectl --timeout 3000 device notification observe \
  --device "$UDID" \
  --name "com.maxtac.never-posted"
```

Run that in a separate terminal. Then extract recent tunnel/debugproxy messages
from host logs:

```text
log show --last 5m --info \
  --predicate '((eventMessage CONTAINS "Adding remote service") && (eventMessage CONTAINS "debugproxy")) || (eventMessage CONTAINS "Tunnel established - interface")' \
  --style compact
```

Use the latest matching tunnel address and debugproxy port. Older entries may
refer to stale tunnels kept open by Xcode, Console, Safari, or previous
sessions.

Launch the target stopped at entry:

```text
xcrun devicectl device process launch \
  --device "$UDID" \
  --start-stopped \
  "$BUNDLE_ID"
```

Get the PID:

```text
xcrun devicectl device info processes --device "$UDID"
```

Attach from the debugger using the discovered debugproxy endpoint and PID. If no
fresh tunnel log appears, close Xcode/Console/Safari and retry. Killing
`remotepairingd` can force recreation, but only do that deliberately because it
disturbs all active CoreDevice sessions on the host.

## Automation Patterns

Use a run directory per device/session:

```text
RUN_DIR="evidence/$(date +%Y%m%d-%H%M%S)-$UDID"
mkdir -p "$RUN_DIR"
xcodebuild -version > "$RUN_DIR/xcode-version.txt"
xcrun --version > "$RUN_DIR/xcrun-version.txt"
xcrun devicectl list devices -q --json-output "$RUN_DIR/devices.json"
xcrun devicectl list preferredDDI > "$RUN_DIR/preferred-ddi.txt"
```

Capture launch output deterministically:

```text
xcrun devicectl device process launch \
  --device "$UDID" \
  --console \
  --terminate-existing \
  "$BUNDLE_ID" > "$RUN_DIR/launch-console.log" 2>&1
```

Collect app data after a repro:

```text
xcrun devicectl device info files \
  --device "$UDID" \
  --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID" \
  -q --json-output "$RUN_DIR/app-files.json"
```

Use timeouts around blocking commands:

```text
timeout 60 xcrun devicectl device process launch \
  --device "$UDID" \
  --console \
  --terminate-existing \
  "$BUNDLE_ID"
```

If macOS lacks GNU `timeout`, use the shell, Python, or the harness runner's
native timeout mechanism. Do not leave long-running `--console` or notification
observers orphaned in the background.

## Failure Modes

`xcrun: error: invalid active developer path`

- Active developer directory is missing or stale.
- Check `xcode-select --print-path`.
- Select a full Xcode.app or set `DEVELOPER_DIR` for the command.

`xcrun: error: unable to find utility "devicectl"`

- Command Line Tools-only path is active, or Xcode is too old.
- Run `xcrun --kill-cache` after changing Xcode selection.

`No devices found`

- Device may be locked, not trusted, not in Developer Mode, or connected with a
  charge-only cable.
- Finder visibility is not enough; require `devicectl list devices`.
- For wireless devices, check VPN/proxy/filtering and prefer USB.

DDI compatibility errors

- Run `xcrun devicectl list preferredDDI`.
- Run `xcrun devicectl manage ddis update`.
- Update Xcode if the device OS is newer than available DDI content.

Launch reports success but app disappears

- Use `--console`.
- Check `systemCrashLogs`.
- Confirm the developer certificate is trusted on device.
- Confirm the installed bundle ID with `device info apps`.
- Account for iOS suspension if the app has no UI/background mode and exits its
  run loop.

`kLSApplicationNotFoundErr` or launch cannot find app

- Wrong bundle identifier or app not installed for that device.
- Re-run `device info apps --device "$UDID"` and launch the exact bundle ID.

File copy cannot find expected output

- App wrote to a container path that changed after reinstall.
- `/tmp` or caches were cleared.
- The output path was created in a different app group/container.
- List files before copying and write future PoV output to `Documents`.

## Evidence Checklist

Collect:

- `xcodebuild -version`, `xcrun --version`, and active `xcode-select` path.
- Full `devicectl list devices` JSON.
- Device UDID, model, OS version, OS build, lock state, and transport.
- `list preferredDDI` and `device info ddiServices` when debug/install services
  matter.
- Exact install path, bundle ID, signing/provisioning notes, and install output.
- Exact launch command, launch options, environment variables, payload URL, and
  `--console` output.
- Process list before and after launch when proving liveness or PID selection.
- App container files and pulled artifacts.
- System crash logs or sysdiagnose for crashes, jetsam, entitlement failures,
  or service-level behavior.
- Any tunnel/debugproxy endpoint used for debugger attach.
- State-changing cleanup: uninstall, signal, reboot, DDI update, pair/unpair, or
  daemon restart.

## References

- https://developer.apple.com/documentation/xcode/xcode-command-line-tool-reference
- https://developer.apple.com/documentation/xcode/installing-the-command-line-tools
- https://developer.apple.com/library/archive/technotes/tn2339/_index.html
- https://leancrew.com/all-this/man/man1/xcrun.html
- https://theapplewiki.com/wiki/Devicectl
- https://docs.hex-rays.com/9.1/user-guide/debugger/debugger-tutorials/ios_debugging_coredevice
