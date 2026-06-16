# ADB CLI

Use `adb` for physical Android device control, app lifecycle work, log capture,
and repeatable DAST setup. Treat `adb shell` as a powerful local research
principal, not as proof that an untrusted app or remote attacker has the same
access.

## Contents

- [Quick Commands](#quick-commands)
- [Platform Tools and Server State](#platform-tools-and-server-state)
- [Device Discovery and Targeting](#device-discovery-and-targeting)
- [USB and Wireless Debugging](#usb-and-wireless-debugging)
- [Shell Execution and Quoting](#shell-execution-and-quoting)
- [Install and Package State](#install-and-package-state)
- [App Lifecycle and Intents](#app-lifecycle-and-intents)
- [Users and Work Profiles](#users-and-work-profiles)
- [Files and App Data](#files-and-app-data)
- [Logs](#logs)
- [Bugreports, Dumpsys, and Tombstones](#bugreports-dumpsys-and-tombstones)
- [Port Forwarding and Network Setup](#port-forwarding-and-network-setup)
- [Permissions, AppOps, and Settings](#permissions-appops-and-settings)
- [App Links and Deep Links](#app-links-and-deep-links)
- [Compatibility and Power-State Controls](#compatibility-and-power-state-controls)
- [Debugging Hooks](#debugging-hooks)
- [Evidence Automation](#evidence-automation)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Host and server sanity:

```text
adb version
adb server-status
adb start-server
adb kill-server
adb devices -l
adb reconnect
```

Target a device:

```text
adb -s "$SERIAL" get-state
adb -s "$SERIAL" shell getprop ro.product.model
adb -s "$SERIAL" shell getprop ro.build.fingerprint
adb -s "$SERIAL" shell getprop sys.boot_completed
ANDROID_SERIAL="$SERIAL" adb shell id
```

Wireless debugging:

```text
adb pair "$PAIR_HOST:$PAIR_PORT"
adb connect "$DEVICE_HOST:$ADB_PORT"
adb mdns services
adb mdns track-services --proto-text
```

Package and launch:

```text
adb -s "$SERIAL" install -r -d -g ./target.apk
adb -s "$SERIAL" install-multiple -r base.apk split_config.arm64_v8a.apk split_config.xxhdpi.apk
adb -s "$SERIAL" shell pm list packages -U -f --user 0
adb -s "$SERIAL" shell dumpsys package "$PACKAGE"
adb -s "$SERIAL" shell am force-stop "$PACKAGE"
adb -s "$SERIAL" shell am start -W -S -n "$PACKAGE/.MainActivity"
```

Logs and evidence:

```text
adb -s "$SERIAL" logcat -c
adb -s "$SERIAL" logcat -b main,system,crash -v threadtime
adb -s "$SERIAL" bugreport "./bugreport-$SERIAL.zip"
adb -s "$SERIAL" exec-out screencap -p > screen.png
adb -s "$SERIAL" shell screenrecord /sdcard/repro.mp4
adb -s "$SERIAL" pull /sdcard/repro.mp4 .
```

Networking:

```text
adb -s "$SERIAL" forward tcp:8081 tcp:8081
adb -s "$SERIAL" reverse tcp:8080 tcp:8080
adb -s "$SERIAL" forward --list
adb -s "$SERIAL" reverse --list
adb -s "$SERIAL" forward --remove-all
adb -s "$SERIAL" reverse --remove-all
```

State-changing controls:

```text
adb -s "$SERIAL" shell pm grant "$PACKAGE" android.permission.POST_NOTIFICATIONS
adb -s "$SERIAL" shell cmd appops set "$PACKAGE" RUN_ANY_IN_BACKGROUND ignore
adb -s "$SERIAL" shell cmd appops set "$PACKAGE" RUN_ANY_IN_BACKGROUND allow
adb -s "$SERIAL" shell dumpsys battery unplug
adb -s "$SERIAL" shell dumpsys battery reset
```

## Platform Tools and Server State

Use the `adb` from Android SDK Platform Tools, not an old copy from a vendor
bundle. On macOS and Linux this is usually under `$ANDROID_HOME/platform-tools`
or `$ANDROID_SDK_ROOT/platform-tools`; on Windows it is usually
`%LOCALAPPDATA%\Android\Sdk\platform-tools`.

Record the tool version:

```text
adb version
adb server-status
```

`adb` is a client/server system. The server listens on host TCP port `5037` by
default and multiplexes commands to devices. If commands hang, restart the
server before changing device state:

```text
adb kill-server
adb start-server
adb devices -l
```

Use environment variables only when they make automation simpler:

```text
ANDROID_SERIAL="$SERIAL" adb shell id
ADB_TRACE=all adb start-server
```

When debugging wireless or server discovery failures, `adb server-status`
reports the server version and log path. Attach that server log with bugreports
when the transport layer itself is failing.

## Device Discovery and Targeting

Always target by serial in research automation. `adb -d` means "the only USB
device"; it fails or picks wrong when more devices are attached. `adb -e` means
"the only emulator"; this skill prefers physical devices for Android research.

List devices with metadata:

```text
adb devices -l
```

Interpret states carefully:

- `unauthorized`: unlock the device and accept the RSA prompt.
- `offline`: restart the server or reconnect the transport.
- `device`: adbd is connected, but Android may still be booting.
- no row: USB, driver, cable, wireless pairing, or developer options problem.

Wait for adbd and then wait for Android boot completion:

```text
adb -s "$SERIAL" wait-for-device
adb -s "$SERIAL" shell 'while [ "$(getprop sys.boot_completed)" != "1" ]; do sleep 1; done'
```

Capture identifying state:

```text
adb -s "$SERIAL" shell getprop ro.product.manufacturer
adb -s "$SERIAL" shell getprop ro.product.model
adb -s "$SERIAL" shell getprop ro.product.device
adb -s "$SERIAL" shell getprop ro.build.version.release
adb -s "$SERIAL" shell getprop ro.build.version.sdk
adb -s "$SERIAL" shell getprop ro.build.fingerprint
adb -s "$SERIAL" shell getprop ro.boot.verifiedbootstate
adb -s "$SERIAL" shell getprop ro.debuggable
adb -s "$SERIAL" shell getenforce
```

Do not rely only on model names. Android OEM builds vary by carrier, patch
level, bootloader state, build type, and security patch.

## USB and Wireless Debugging

For physical-device evidence, prefer USB unless the behavior specifically
depends on Wi-Fi. Wireless ADB adds mDNS, network trust, firewall, VPN, and
sleep-state variables.

USB checklist:

- Enable Developer options.
- Enable USB debugging.
- Unlock the device and accept the RSA prompt.
- Use a data cable and a stable hub-free port.
- Confirm `adb devices -l` shows state `device`.

Modern wireless debugging uses pairing:

```text
adb pair "$PAIR_HOST:$PAIR_PORT"
adb connect "$DEVICE_HOST:$ADB_PORT"
adb devices -l
```

Wireless troubleshooting:

```text
adb server-status
adb mdns services
adb mdns track-services --proto-text
ADB_MDNS=1 adb kill-server
ADB_MDNS=1 adb start-server
ADB_MDNS_OPENSCREEN=0 adb kill-server
ADB_MDNS_OPENSCREEN=0 adb start-server
```

For older or lab-only flows after an initial USB connection:

```text
adb tcpip 5555
adb connect "$DEVICE_IP:5555"
adb usb
```

Use `adb usb` to return a device to USB transport. Do not leave lab devices
listening on TCP if the network is shared.

## Shell Execution and Quoting

Prefer one-shot shell commands for evidence and scripts:

```text
adb -s "$SERIAL" shell id
adb -s "$SERIAL" shell 'getprop | sort'
```

Use `exec-out` when bytes must be preserved:

```text
adb -s "$SERIAL" exec-out screencap -p > screen.png
adb -s "$SERIAL" exec-out run-as "$PACKAGE" cat files/repro.bin > repro.bin
```

`adb shell` is suitable for text. `adb exec-out` avoids interactive shell noise
and is safer for screenshots, tar streams, sqlite databases, protobufs, heap
dumps, and other binary artifacts.

Probe command help on the target OS before relying on advanced flags:

```text
adb -s "$SERIAL" shell am --help
adb -s "$SERIAL" shell pm help
adb -s "$SERIAL" shell cmd -l
adb -s "$SERIAL" shell cmd package help
adb -s "$SERIAL" shell cmd appops help
adb -s "$SERIAL" logcat --help
```

Android shell commands vary across API level, OEM build, and build type. Prefer
capability probes over hard-coded assumptions in reusable scripts.

## Install and Package State

Install common APK builds:

```text
adb -s "$SERIAL" install -r ./target.apk
adb -s "$SERIAL" install -r -d ./target.apk
adb -s "$SERIAL" install -r -g ./target.apk
adb -s "$SERIAL" install -r -t ./target.apk
```

Common install flags:

- `-r`: replace an existing package.
- `-d`: allow versionCode downgrade where the build permits it.
- `-g`: grant runtime permissions declared in the manifest.
- `-t`: allow test-only packages.
- `--user USER_ID`: install for a specific Android user where supported.

Install split APKs together:

```text
adb -s "$SERIAL" install-multiple -r \
  base.apk \
  split_config.arm64_v8a.apk \
  split_config.en.apk \
  split_config.xxhdpi.apk
```

Use `install-multiple` for APK sets extracted from bundles. Installing only
`base.apk` can produce false crashes caused by missing ABI, resources, or
dynamic feature splits.

Inspect package state:

```text
adb -s "$SERIAL" shell pm list packages -U -f --user 0
adb -s "$SERIAL" shell pm path "$PACKAGE"
adb -s "$SERIAL" shell dumpsys package "$PACKAGE"
adb -s "$SERIAL" shell dumpsys package "$PACKAGE" | grep -E 'versionCode|versionName|targetSdk|userId|dataDir|signatures|Signing'
```

Enable or install an already-present package for a user:

```text
adb -s "$SERIAL" shell pm install-existing --user 0 "$PACKAGE"
adb -s "$SERIAL" shell pm enable --user 0 "$PACKAGE"
adb -s "$SERIAL" shell pm disable-user --user 0 "$PACKAGE"
```

Clear app data only when the test plan allows it:

```text
adb -s "$SERIAL" shell pm clear "$PACKAGE"
```

`pm clear` erases evidence in the app data directory. Pull logs, databases, and
crash outputs first.

Uninstall:

```text
adb -s "$SERIAL" uninstall "$PACKAGE"
adb -s "$SERIAL" uninstall --user 10 "$PACKAGE"
adb -s "$SERIAL" uninstall -k "$PACKAGE"
```

`-k` keeps data and cache. Use it deliberately; stale state can hide or create
bugs.

## App Lifecycle and Intents

Force-stop before deterministic launches:

```text
adb -s "$SERIAL" shell am force-stop "$PACKAGE"
```

Start an explicit activity and wait for timing:

```text
adb -s "$SERIAL" shell am start -W -S -n "$PACKAGE/.MainActivity"
```

Start a deep link:

```text
adb -s "$SERIAL" shell am start -W \
  -a android.intent.action.VIEW \
  -d 'https://example.test/path?case=1'
```

Start with extras:

```text
adb -s "$SERIAL" shell am start -W -n "$PACKAGE/.MainActivity" \
  --es token 'abc123' \
  --ez debug true \
  --ei count 7
```

Broadcast an intent:

```text
adb -s "$SERIAL" shell am broadcast \
  -a com.example.ACTION_REPRO \
  -n "$PACKAGE/.Receiver" \
  --es payload 'value'
```

Start services only if the platform allows the requested service type:

```text
adb -s "$SERIAL" shell am startservice -n "$PACKAGE/.ExampleService"
adb -s "$SERIAL" shell am start-foreground-service -n "$PACKAGE/.ExampleService"
```

Important security caveat: `adb shell am` runs as the shell UID. It is useful
for exercising components, but it is not a substitute for a third-party PoV app
when proving exported-component reachability, permission bypass, or intent
spoofing impact. For exploit claims, reproduce from an app with realistic
permissions.

## Users and Work Profiles

Many app, package, and activity-manager commands operate per user. Work-profile
devices commonly have user `0` for personal and another ID such as `10` for the
profile.

List users:

```text
adb -s "$SERIAL" shell pm list users
```

Launch in a specific user/profile:

```text
adb -s "$SERIAL" shell am start --user 10 \
  -n "$PACKAGE/.MainActivity" \
  -a android.intent.action.MAIN \
  -c android.intent.category.LAUNCHER
```

Inspect package state for a user:

```text
adb -s "$SERIAL" shell pm list packages --user 10 -U -f
adb -s "$SERIAL" shell dumpsys package "$PACKAGE" | grep -A 30 'User 10'
```

Always record the user ID for findings involving:

- managed profiles;
- cross-profile intents;
- account or credential separation;
- app links;
- package visibility;
- permissions and appops;
- storage visibility.

## Files and App Data

Push and pull accessible files:

```text
adb -s "$SERIAL" push ./seed.json /sdcard/Download/seed.json
adb -s "$SERIAL" pull /sdcard/Download/repro.log .
```

Inspect debuggable app private data with `run-as`:

```text
adb -s "$SERIAL" shell run-as "$PACKAGE" pwd
adb -s "$SERIAL" shell run-as "$PACKAGE" ls -la
adb -s "$SERIAL" shell run-as "$PACKAGE" ls -la files databases shared_prefs cache
```

Pull a private file without using shared storage:

```text
adb -s "$SERIAL" exec-out run-as "$PACKAGE" cat files/repro.log > repro.log
```

Archive common private data paths:

```text
adb -s "$SERIAL" exec-out run-as "$PACKAGE" sh -c \
  'tar -cf - files databases shared_prefs cache 2>/dev/null' > appdata.tar
```

Use `run-as` only when the package is debuggable and the device supports it:

```text
adb -s "$SERIAL" shell run-as "$PACKAGE" pwd
```

If `run-as` fails on a release build, that is expected. Do not switch to root or
backup extraction unless the research scope and device type allow it. Rooted,
userdebug, and eng builds can change app sandbox assumptions.

For content-provider DAST, the shell `content` tool is useful for mapping
behavior:

```text
adb -s "$SERIAL" shell content query --uri 'content://authority/path'
adb -s "$SERIAL" exec-out content read --uri 'content://authority/blob/1' > blob.bin
```

Shell-provider access is not proof of third-party access. Use it to discover
shape and errors, then prove exposure from an unprivileged app or instrumentation
context with comparable permissions.

## Logs

Clear logs immediately before a focused repro:

```text
adb -s "$SERIAL" logcat -c
```

Capture useful buffers:

```text
adb -s "$SERIAL" logcat -b main,system,crash -v threadtime
adb -s "$SERIAL" logcat -b all -v threadtime -d > logcat-all.txt
adb -s "$SERIAL" logcat -b events -v threadtime -d > logcat-events.txt
adb -s "$SERIAL" logcat -b radio -v threadtime -d > logcat-radio.txt
```

Filter by tag and priority:

```text
adb -s "$SERIAL" logcat 'ActivityManager:I MyApp:D *:S'
adb -s "$SERIAL" logcat '*:W'
```

Filter by PID after launch:

```text
PID="$(adb -s "$SERIAL" shell pidof -s "$PACKAGE" | tr -d '\r')"
adb -s "$SERIAL" logcat --pid="$PID" -b main,system,crash -v threadtime
```

High-value DAST tags:

- `ActivityManager`, `ActivityTaskManager`, `PackageManager`, `InputDispatcher`.
- `AndroidRuntime`, `libc`, `DEBUG`, `crash_dump`, `tombstoned`.
- `StrictMode`, `NetworkSecurityConfig`, `Conscrypt`.
- target app tags and SDK/library tags.
- OEM-specific permission, account, keystore, and IPC services.

Limitations:

- Release builds may strip debug logs.
- Some buffers require root or privileged access for full content.
- `logcat -c` destroys historical evidence.
- `--pid` misses early startup logs if started after process creation.
- Android log buffers are circular; collect promptly after a crash.

## Bugreports, Dumpsys, and Tombstones

Collect a full bugreport after reproducing a crash, system-service issue, power
issue, permission issue, or cross-profile behavior:

```text
adb -s "$SERIAL" bugreport "./bugreport-$SERIAL.zip"
```

Bugreports contain `dumpsys`, `dumpstate`, and `logcat` output. They can also
include files copied from device paths under an `FS/` directory. Treat them as
sensitive artifacts because they may contain account, network, package, path,
and app data.

If an older bugreport was generated on device:

```text
adb -s "$SERIAL" shell ls /bugreports/
adb -s "$SERIAL" pull /bugreports/bugreport-*.zip .
```

Focused `dumpsys` commands:

```text
adb -s "$SERIAL" shell dumpsys package "$PACKAGE"
adb -s "$SERIAL" shell dumpsys activity activities
adb -s "$SERIAL" shell dumpsys activity services "$PACKAGE"
adb -s "$SERIAL" shell dumpsys activity broadcasts
adb -s "$SERIAL" shell dumpsys window
adb -s "$SERIAL" shell dumpsys jobscheduler
adb -s "$SERIAL" shell dumpsys alarm
adb -s "$SERIAL" shell dumpsys deviceidle
adb -s "$SERIAL" shell dumpsys usagestats
adb -s "$SERIAL" shell dumpsys netstats
adb -s "$SERIAL" shell dumpsys batterystats --charged "$PACKAGE"
adb -s "$SERIAL" shell dumpsys platform_compat
```

Get a stack trace from a live process where supported:

```text
PID="$(adb -s "$SERIAL" shell pidof -s "$PACKAGE" | tr -d '\r')"
adb -s "$SERIAL" shell debuggerd -b "$PID" > "backtrace-$PID.txt"
```

Tombstone access varies by build and Android version. On user builds, prefer
bugreport and crash log buffers. On userdebug/eng or rooted devices, also check:

```text
adb -s "$SERIAL" shell ls -la /data/tombstones
adb -s "$SERIAL" pull /data/tombstones .
```

Do not claim exploitability from a tombstone alone. Pair it with the triggering
input, command sequence, app/package version, device build, and whether control
exists over PC, pointer, length, index, or object state.

## Port Forwarding and Network Setup

Host to device:

```text
adb -s "$SERIAL" forward tcp:8081 tcp:8081
adb -s "$SERIAL" forward tcp:8700 jdwp:"$PID"
adb -s "$SERIAL" forward --list
adb -s "$SERIAL" forward --remove tcp:8081
```

Device to host:

```text
adb -s "$SERIAL" reverse tcp:8080 tcp:8080
adb -s "$SERIAL" reverse --list
adb -s "$SERIAL" reverse --remove tcp:8080
```

Use `reverse` when an app on the device should reach a server running on the
workstation at `127.0.0.1:<port>`. Use `forward` when a host tool should reach a
service on the device.

System HTTP proxy setup for exploratory traffic capture:

```text
adb -s "$SERIAL" shell settings put global http_proxy "$HOST:$PORT"
adb -s "$SERIAL" shell settings get global http_proxy
adb -s "$SERIAL" shell settings delete global http_proxy
adb -s "$SERIAL" shell settings delete global global_http_proxy_host
adb -s "$SERIAL" shell settings delete global global_http_proxy_port
```

Proxy caveats:

- Apps may ignore the system proxy.
- Apps targeting Android 7+ do not trust user CAs by default unless configured.
- Certificate pinning, private DNS, VPNs, QUIC, and native stacks can bypass or
  break interception.
- Proxy settings are stateful; record and clean them up.

Basic radio toggles for controlled tests:

```text
adb -s "$SERIAL" shell svc wifi disable
adb -s "$SERIAL" shell svc wifi enable
adb -s "$SERIAL" shell svc data disable
adb -s "$SERIAL" shell svc data enable
```

OEM builds may restrict these. Record failures rather than forcing privileged
state unless the scope calls for it.

## Permissions, AppOps, and Settings

Grant and revoke runtime permissions:

```text
adb -s "$SERIAL" shell pm grant "$PACKAGE" android.permission.POST_NOTIFICATIONS
adb -s "$SERIAL" shell pm revoke "$PACKAGE" android.permission.POST_NOTIFICATIONS
```

Reset denial flags so permission prompts can appear again:

```text
adb -s "$SERIAL" shell pm clear-permission-flags \
  "$PACKAGE" android.permission.CAMERA user-set user-fixed
```

Inspect permission state:

```text
adb -s "$SERIAL" shell dumpsys package "$PACKAGE" | grep -A 80 'runtime permissions'
```

Use AppOps for behaviors not represented by plain runtime permissions:

```text
adb -s "$SERIAL" shell cmd appops get "$PACKAGE"
adb -s "$SERIAL" shell cmd appops set "$PACKAGE" RUN_ANY_IN_BACKGROUND ignore
adb -s "$SERIAL" shell cmd appops set "$PACKAGE" RUN_ANY_IN_BACKGROUND allow
adb -s "$SERIAL" shell cmd appops reset "$PACKAGE"
```

Probe appops names and modes on the target:

```text
adb -s "$SERIAL" shell cmd appops help
```

Settings writes are high-impact:

```text
adb -s "$SERIAL" shell settings list global
adb -s "$SERIAL" shell settings put global low_power 1
adb -s "$SERIAL" shell settings delete global low_power
```

Record every permission, appop, and settings mutation. Restore the prior value
or state before moving to the next finding.

## App Links and Deep Links

Inspect Android App Links state:

```text
adb -s "$SERIAL" shell pm get-app-links "$PACKAGE"
adb -s "$SERIAL" shell pm get-app-link-owners --user 0 example.com
```

Reset and reverify:

```text
adb -s "$SERIAL" shell pm reset-app-links "$PACKAGE"
adb -s "$SERIAL" shell pm verify-app-links --re-verify "$PACKAGE"
adb -s "$SERIAL" shell pm get-app-links "$PACKAGE"
```

Manually force state for controlled tests:

```text
adb -s "$SERIAL" shell pm set-app-links --package "$PACKAGE" 2 example.com
adb -s "$SERIAL" shell pm set-app-links-user-selection --user 0 --package "$PACKAGE" true example.com
adb -s "$SERIAL" shell pm set-app-links-allowed --user 0 --package "$PACKAGE" true
```

State values used by `pm set-app-links`:

- `0`: reset to no response.
- `1`: mark verification success.
- `2`: force approved.
- `3`: force denied.

Trigger links:

```text
adb -s "$SERIAL" shell am start -W \
  -a android.intent.action.VIEW \
  -d 'https://example.com/repro?x=1'

adb -s "$SERIAL" shell am start -W \
  -a android.intent.action.VIEW \
  -d 'myapp://repro/path?x=1'
```

For link-handling findings, collect `pm get-app-links`, the exact URL, selected
user, browser/source app if any, and whether the dispatch came from shell or an
unprivileged app.

## Compatibility and Power-State Controls

List platform compatibility changes:

```text
adb -s "$SERIAL" shell dumpsys platform_compat
```

Toggle one change for a package where allowed:

```text
adb -s "$SERIAL" shell am compat enable CHANGE_ID_OR_NAME "$PACKAGE"
adb -s "$SERIAL" shell am compat disable CHANGE_ID_OR_NAME "$PACKAGE"
adb -s "$SERIAL" shell am compat reset CHANGE_ID_OR_NAME "$PACKAGE"
```

Toggling compatibility changes kills the app so the override applies. Record the
change ID/name and reset it after the test.

Power-state tests:

```text
adb -s "$SERIAL" shell dumpsys battery unplug
adb -s "$SERIAL" shell am set-standby-bucket "$PACKAGE" rare
adb -s "$SERIAL" shell am get-standby-bucket "$PACKAGE"
adb -s "$SERIAL" shell cmd appops set "$PACKAGE" RUN_ANY_IN_BACKGROUND ignore
adb -s "$SERIAL" shell settings put global low_power 1
```

Cleanup:

```text
adb -s "$SERIAL" shell settings put global low_power 0
adb -s "$SERIAL" shell cmd appops set "$PACKAGE" RUN_ANY_IN_BACKGROUND allow
adb -s "$SERIAL" shell dumpsys battery reset
```

Use these to test background execution, delayed jobs, alarm behavior, sync
logic, token refresh, and network retry handling under realistic Android
constraints.

## Debugging Hooks

Start an app waiting for a Java debugger:

```text
adb -s "$SERIAL" shell am set-debug-app -w "$PACKAGE"
adb -s "$SERIAL" shell am start -W -n "$PACKAGE/.MainActivity"
adb -s "$SERIAL" shell am clear-debug-app
```

One-shot debug launch:

```text
adb -s "$SERIAL" shell am start -D -W -n "$PACKAGE/.MainActivity"
```

List JDWP-capable processes:

```text
adb -s "$SERIAL" jdwp
```

Forward a JDWP process to the host:

```text
adb -s "$SERIAL" forward tcp:8700 jdwp:"$PID"
```

Check `run-as` and ptrace preconditions for native debugging:

```text
adb -s "$SERIAL" shell run-as "$PACKAGE" pwd
adb -s "$SERIAL" shell sysctl kernel.yama.ptrace_scope
```

Heap/profile helpers from ActivityManager:

```text
adb -s "$SERIAL" shell am dumpheap "$PACKAGE" /sdcard/"$PACKAGE".hprof
adb -s "$SERIAL" pull /sdcard/"$PACKAGE".hprof .
adb -s "$SERIAL" shell am profile start "$PACKAGE" /sdcard/"$PACKAGE".trace
adb -s "$SERIAL" shell am profile stop "$PACKAGE"
adb -s "$SERIAL" pull /sdcard/"$PACKAGE".trace .
```

Debuggable builds, `run-as`, JDWP, and ptrace change the target's security and
timing surface. Keep final vulnerability evidence separate from debugger-only
observations unless debug mode is itself in scope.

## Evidence Automation

Create a run directory:

```text
RUN_DIR="evidence/$(date +%Y%m%d-%H%M%S)-$SERIAL"
mkdir -p "$RUN_DIR"
adb version > "$RUN_DIR/adb-version.txt"
adb server-status > "$RUN_DIR/adb-server-status.txt" 2>&1
adb devices -l > "$RUN_DIR/devices.txt"
```

Capture device metadata:

```text
adb -s "$SERIAL" shell getprop > "$RUN_DIR/getprop.txt"
adb -s "$SERIAL" shell pm list users > "$RUN_DIR/users.txt"
adb -s "$SERIAL" shell dumpsys package "$PACKAGE" > "$RUN_DIR/package.txt"
```

Focused repro wrapper:

```text
adb -s "$SERIAL" logcat -c
adb -s "$SERIAL" shell am force-stop "$PACKAGE"
adb -s "$SERIAL" shell am start -W -S -n "$PACKAGE/.MainActivity" \
  > "$RUN_DIR/am-start.txt" 2>&1
sleep 5
adb -s "$SERIAL" logcat -b main,system,crash -v threadtime -d \
  > "$RUN_DIR/logcat.txt"
adb -s "$SERIAL" exec-out screencap -p > "$RUN_DIR/screen.png"
```

Collect after crashes:

```text
adb -s "$SERIAL" bugreport "$RUN_DIR/bugreport.zip"
PID="$(adb -s "$SERIAL" shell pidof -s "$PACKAGE" | tr -d '\r')"
if [ -n "$PID" ]; then
  adb -s "$SERIAL" shell debuggerd -b "$PID" > "$RUN_DIR/backtrace-$PID.txt"
fi
```

Keep a state log:

```text
printf '%s\n' \
  "pm grant $PACKAGE android.permission.POST_NOTIFICATIONS" \
  "cmd appops set $PACKAGE RUN_ANY_IN_BACKGROUND ignore" \
  "settings put global low_power 1" \
  > "$RUN_DIR/state-mutations.txt"
```

## Failure Modes

`adb: command not found`

- Add Android SDK Platform Tools to `PATH`.
- Prefer `$ANDROID_HOME/platform-tools/adb` or
  `$ANDROID_SDK_ROOT/platform-tools/adb`.

`unauthorized`

- Unlock the device and accept the RSA prompt.
- Revoke USB debugging authorizations on the device if the prompt is stale.
- Restart the adb server after reauthorizing.

`offline`

- Run `adb reconnect`.
- Replug USB or reconnect wireless transport.
- Restart the server with `adb kill-server; adb start-server`.

`more than one device/emulator`

- Use `adb -s "$SERIAL" ...` or set `ANDROID_SERIAL`.
- Avoid `-d` in automation unless the lab guarantees one USB target.

Install fails with downgrade or test-only errors

- Use `-d` only when downgrade is expected.
- Use `-t` only for packages marked test-only.
- Confirm split APKs are installed together.
- Check `dumpsys package` for existing version and signatures.

`run-as: Package is not debuggable`

- Expected for release builds.
- Use app-visible exports or in-app logging for release evidence.
- Do not silently switch to root and call it equivalent.

`Permission Denial` from `am start`, `broadcast`, or `content`

- The component/provider may be non-exported or permission-protected.
- Shell UID is privileged but not all-powerful.
- Prove third-party exploitability with a realistic app PoV when needed.

No traffic in proxy

- App may ignore system proxy.
- User CAs may not be trusted.
- Certificate pinning or native networking may block interception.
- QUIC, VPN, private DNS, and direct sockets can bypass expected capture.

No crash file found

- Check `logcat -b crash`.
- Pull a bugreport.
- Check whether the process was killed by LMKD, ANR, watchdog, or background
  restriction instead of a native/Java crash.

## Evidence Checklist

Collect:

- `adb version`, `adb server-status`, and `adb devices -l`.
- Device serial, model, build fingerprint, SDK level, security patch, verified
  boot state, SELinux mode, and `ro.debuggable`.
- Transport type: USB, paired wireless debugging, or legacy TCP.
- Android user/profile ID used for each command.
- Package version, versionCode, signatures, target SDK, UID, install path, data
  directory, and split APK state.
- Exact install, launch, intent, extras, deep link, and cleanup commands.
- Runtime permission state, appops, settings writes, compatibility overrides,
  app-link overrides, and power-state changes.
- Logcat buffers with timestamps and crash buffer.
- Bugreport zip for system-level behavior, crashes, ANRs, permission failures,
  background execution, or power/network issues.
- Screenshots or screen recordings where UI state matters.
- Private app data pulled with `run-as`, noting debuggable-build dependency.
- Whether evidence came from `adb shell`, `run-as`, root/userdebug, or an
  unprivileged app PoV.

## References

- https://developer.android.com/tools/adb
- https://developer.android.com/tools/logcat
- https://developer.android.com/studio/debug/bug-report
- https://source.android.com/docs/core/tests/debug/read-bug-reports
- https://developer.android.com/tools/dumpsys
- https://developer.android.com/guide/app-compatibility/test-debug
- https://developer.android.com/topic/performance/power/test-power
- https://developer.android.com/studio/debug
- https://source.android.com/docs/core/tests/debug
- https://developer.android.com/work/managed-profiles
