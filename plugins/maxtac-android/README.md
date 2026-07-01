# MaxTAC for Android

MaxTAC for Android adds APK/DEX/resource reverse engineering, Android component surface triage, Android input loops, ADB/logcat/JDWP/Frida runtime evidence, and Android-focused auditor routing.

Use this pack with MaxTAC Core when the target is an Android application, Android platform component, APK, AAB, DEX/JAR/AAR, Android IPC surface, WebView flow, or mobile runtime proof.

## When To Use

- APK, DEX, JAR, AAR, AAB, smali, resource decoding, and JADX workflows.
- Manifest, component, permission, IPC, WebView, storage, crypto, dynamic-code, and native-library surface triage.
- User-facing Android input loops for activities, screens, deep links, forms, WebViews, share targets, file pickers, notifications, and settings flows.
- ADB, logcat, JDWP, Frida, component launch, content-provider probing, appops, dumpsys, or runtime evidence capture.
- Android-specific auditor routing.

## Skills

- `maxtac-android-surface-triage`: Android manifest, component, permission, IPC, WebView, storage, crypto, dynamic-code, and native-library triage.
- `maxtac-re-jadx`: JADX workflows for APK, DEX, JAR, AAR, AAB, smali, resources, mappings, GUI search, debugging, automation, and plugins.
- `maxtac-android-runtime-debugging`: ADB, logcat, JDWP, Frida, component launch, content providers, appops, dumpsys, and runtime evidence.
- `maxtac-android-input-loop`: Android user-facing input worklist loop for systematic deep input auditing under scope and rate limits.

## Typical Pairings

- Android + Source when JADX output or available source needs static triage.
- Android + Binary when native libraries dominate the evidence path.
- Android + Web when WebView, OAuth, API, account, or browser-mediated workflows matter.
- Android + Cloud when mobile proof depends on cloud identity, signed URLs, backend cloud storage, or cloud-hosted runtime boundaries.
- Android + Supply Chains when APK provenance, build pipelines, signing, dependencies, or release artifacts are central.

## Output Artifacts

Android workflows commonly produce:

- Decompiled source/resource notes.
- `contracts/loops/<loop-id>/` Android input loop worklists, gates, events, and next-action prompts.
- Manifest and component maps.
- ADB/logcat transcripts, app state, dumpsys output, and runtime traces.
- Frida or JDWP observations.
- APK signing and package metadata evidence.

## Boundary

This pack focuses on Android-specific research. Use Source for broad static code closure, Binary for native RE/fuzzing, Web for API/browser flows, Cloud for cloud identity or storage proof, and Supply Chains for build or release provenance.
