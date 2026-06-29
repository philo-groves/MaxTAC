# MaxTAC for Android

MaxTAC for Android adds APK/DEX/resource reverse engineering, Android component surface triage, ADB/logcat/JDWP/Frida runtime evidence, and Android-focused auditor routing.

Use this pack with MaxTAC Core when the target is an Android application, Android platform component, APK, AAB, DEX/JAR/AAR, Android IPC surface, WebView flow, or mobile runtime proof.

## When To Use

- APK, DEX, JAR, AAR, AAB, smali, resource decoding, and JADX workflows.
- Manifest, component, permission, IPC, WebView, storage, crypto, dynamic-code, and native-library surface triage.
- ADB, logcat, JDWP, Frida, component launch, content-provider probing, appops, dumpsys, or runtime evidence capture.
- Android-specific auditor routing.

## Skills

- `maxtac-android-surface-triage`: Android manifest, component, permission, IPC, WebView, storage, crypto, dynamic-code, and native-library triage.
- `maxtac-re-jadx`: JADX workflows for APK, DEX, JAR, AAR, AAB, smali, resources, mappings, GUI search, debugging, automation, and plugins.
- `maxtac-android-runtime-debugging`: ADB, logcat, JDWP, Frida, component launch, content providers, appops, dumpsys, and runtime evidence.

## Typical Pairings

- Android + Source when JADX output or available source needs static triage.
- Android + Binary when native libraries dominate the evidence path.
- Android + Web when WebView, OAuth, API, account, or browser-mediated workflows matter.
- Android + Supply Chains when APK provenance, build pipelines, signing, dependencies, or release artifacts are central.

## Output Artifacts

Android workflows commonly produce:

- Decompiled source/resource notes.
- Manifest and component maps.
- ADB/logcat transcripts, app state, dumpsys output, and runtime traces.
- Frida or JDWP observations.
- APK signing and package metadata evidence.

## Boundary

This pack focuses on Android-specific research. Use Source for broad static code closure, Binary for native RE/fuzzing, Web for API/browser flows, and Supply Chains for build or release provenance.
