---
name: maxtac-android-surface-triage
description: "Use this skill when Android application or platform research needs manifest, component, permission, IPC, WebView, storage, crypto, dynamic-code, or native-library surface triage."
---

# MaxTAC Android Surface Triage

Use this skill before deep reverse engineering or runtime testing of an Android target. Keep the output narrow enough to route into Source, Binary, JADX, runtime debugging, or auditor subagents.

## Intake

Record:

- Authorized target name, package name, version, build, signing certificate fingerprint, acquisition source, and hash of every APK/AAB/DEX/JAR/AAR input.
- Whether source is available, decompiled output is available, or the target is binary-only.
- Device/API assumptions that affect reachability, such as Android API level, work profile, managed device state, permissions already granted, app role, and install channel.
- Program exclusions around accounts, data, device state, network traffic, or third-party services.

## First-Pass Map

Build a surface map from the manifest, resources, decompiled code, and runtime metadata:

- Components: exported and non-exported activities, services, receivers, providers, aliases, app widgets, shortcuts, and intent filters.
- Entry points: deep links, app links, custom schemes, pending intents, notifications, share targets, widgets, accessibility services, input methods, backup/restore, document providers, and broadcast receivers.
- Trust boundaries: calling package/UID, Binder caller identity, URI permission grants, content-provider paths, file paths, WebView origins, JavaScript bridges, native JNI boundaries, and IPC services.
- Sensitive assets: auth tokens, session cookies, cryptographic keys, account data, device identifiers, local files, media, contacts, location, notifications, enterprise state, and server-side account actions.
- Configuration: `android:exported`, permissions, `debuggable`, `allowBackup`, `usesCleartextTraffic`, network security config, `FileProvider` roots, backup rules, signing config, and min/target SDK behavior.
- Code-loading paths: `DexClassLoader`, `PathClassLoader`, reflection, dynamic feature modules, native libraries, plugin systems, scripting engines, deserialization, and asset unpacking.

## Triage Questions

Ask:

- Can another app, browser, notification, share sheet, or IPC caller reach this entry point?
- Is caller identity checked with the correct primitive, such as UID/package/signature permission/Binder identity, rather than caller-supplied fields?
- Does a component trust extras, URI paths, MIME types, file names, serialized objects, pending intents, or WebView messages without binding them to the caller and expected state?
- Can a lower-privileged caller read, write, trigger, or confuse protected app state?
- Does decompiled Java/Kotlin hide a native, reflection, generated-code, or resource-driven behavior that needs Binary or Source follow-up?

## Routing

- Use `maxtac-re-jadx` for APK/DEX/resource export, decompiled call paths, manifest/resource evidence, and smali/JDWP-backed checks.
- Use `maxtac-android-runtime-debugging` for ADB, logcat, JDWP, Frida, component launches, content-provider probes, and runtime evidence.
- Use MaxTAC for Source when source is available and the hypothesis needs OpenGrep, CFG, or source-level packets.
- Use MaxTAC for Binary when native libraries, JNI, memory safety, binary-only parsers, or native fuzzing dominate the evidence path.
- Use Core subagents after the triage packet names one entry point, one actor model, one protected asset, and one concrete hypothesis.

## Output

Persist an Android surface packet with:

- Target identity, hashes, signing fingerprint, acquisition source, and API/device assumptions.
- Component and entrypoint table with exported state, permissions, caller model, and protected assets.
- Top hypotheses, confidence, missing facts, and exact artifacts supporting each route.
- Auditor routing hints, such as `intent`, `deeplink`, `provider`, `webview`, `ipc`, `permissions`, `storage`, `crypto`, `dynamic-code`, `native`, or `auth`.
