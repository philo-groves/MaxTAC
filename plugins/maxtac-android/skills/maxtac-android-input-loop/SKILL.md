---
name: maxtac-android-input-loop
description: "Use this skill when MaxTAC Android needs a loop that models an Android app's user-facing resources and systematically walks activities, deep links, forms, WebViews, share targets, notifications, and other user-facing inputs for security auditing while respecting scope and safety constraints."
---

# MaxTAC Android Input Loop

Use this loop for user-facing Android input coverage. It complements Android surface triage, JADX export, and runtime debugging. It does not replace a future IPC/component loop; exported services, receivers, providers, and Binder surfaces should stay in Android surface triage unless the user-facing path drives them.

## Setup

1. Record package, version, build, signing hash, APK/AAB source, device/API level, account assumptions, test data limits, network scope, and destructive-action rules.
2. Use `maxtac-re-jadx` to export manifest, resources, strings, navigation, layouts, and decompiled code when available.
3. Use Android surface triage to identify activities, deep links, WebViews, share targets, notifications, widgets, shortcuts, login/account flows, file pickers, and settings screens.
4. Model important invariants: caller/user identity, account ownership, local storage, WebView origin, URI grant, file path trust, server request authority, and state transitions.
5. Create Core loop state:

```text
python3 <core-workflow-skill-dir>/scripts/loop.py init \
  --root <workspace-root> \
  --loop-id <id> \
  --kind android-input \
  --owner-plugin maxtac-android \
  --target "<package and version>" \
  --scope "<activities, resources, and user-facing input classes>" \
  --summary "Systematically audit Android user-facing inputs with runtime and decompiler evidence." \
  --positive-gate "Input has resource/decompiled/runtime evidence, actor/state model, sink or server action, security disposition, and blockers resolved or recorded." \
  --negative-gate "Input lacks resource mapping, safe runtime path, account state, WebView origin, URI/file trust model, or evidence path." \
  --safety "Respect program scope, account/data limits, and device state constraints." \
  --output "research/artifacts/android-input/<id>/" \
  --output "contracts/loops/<id>/"
```

6. Add loop items for activities/screens, text fields, intents/deep links reached from UI, file/media pickers, WebView forms and bridges, share sheet inputs, notification actions, settings toggles, import/export flows, backup/restore UI, and server-backed actions.

## Iterate

For each input:

1. Record UI path, resource IDs, strings, layout, activity/fragment/composable, decompiled handler, and runtime launch method.
2. Identify actor, account state, permissions, local/remote sink, file/URI trust, WebView origin, and server request authority.
3. Choose safe evidence: JADX path, ADB activity launch, logcat, dumpsys, Frida observation, network transcript within scope, or source review.
4. Audit for authz, intent/deep-link trust, unsafe extras, file path/URI grants, WebView bridge exposure, storage disclosure, crypto misuse, server-side authority drift, injection, replay, and state bypass.
5. Update Core model/corpus and the loop item. Route native paths to Binary and backend paths to Web or Source when needed.

## Gates

Positive closure requires:

- resource/decompiled or runtime evidence;
- actor/account/device state;
- input source, sink, and trust boundary;
- safe security disposition;
- evidence references or recorded blocker.

Negative closure requires:

- missing APK/resource provenance, blocked account/device state, unsafe test side effect, unresolved WebView origin, missing URI/file trust proof, or native/backend dependency.

## Output

Keep APK metadata, JADX exports, screenshots, ADB/logcat/dumpsys transcripts, Frida observations, and network captures as artifacts. Use Core corpus and models for durable app behavior. Use ledgers only for surviving primitives or chains.

## Hard Rules

- Do not send traffic or mutate account state outside authorized scope.
- Do not treat UI-only checks as server-side or component-level security controls.
- Do not close WebView or deep-link inputs without origin/caller and state evidence.
- Do not expand this loop into all exported IPC components; split to Android surface triage or a future IPC loop.
