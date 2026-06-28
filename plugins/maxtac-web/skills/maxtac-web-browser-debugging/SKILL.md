---
name: maxtac-web-browser-debugging
description: "Use this skill when web research needs browser debugging, protocol instrumentation, DOM or storage evidence, request timing, frame/process state, CDP, WebDriver BiDi, or WebKit inspection."
---

# MaxTAC Web Browser Debugging

Use this skill when browser-observed state is part of the vulnerability evidence: DOM mutation, frame routing, storage, cookies, service workers, request timing, CORS behavior, CSP, postMessage, navigation, renderer crashes, or browser-specific behavior.

## Evidence Helper

Use `python3 <skill-dir>/scripts/debug-evidence.py` to collect browser debugging, protocol, replay, screenshot, trace, or recording evidence into `<workspace-root>/proof/<case-id>/`.

Initialize a browser evidence case:

```bash
python3 <skill-dir>/scripts/debug-evidence.py init \
  --tool "Chrome DevTools Protocol" \
  --version-command "chrome --version" \
  --target "checkout origin transition" \
  --target-version "2026-06-28 deploy" \
  --scope "authorized test tenant" \
  --environment "fresh browser profile" \
  --command-line "node replay-cdp.js"
```

Attach captures:

```bash
python3 <skill-dir>/scripts/debug-evidence.py add-artifact <case-id> \
  --category screenshot \
  --artifact ./evidence/final-state.png
```

## Tool Selection

Read only the reference that matches the browser surface:

| Need | Prefer | Reference |
| --- | --- | --- |
| Chromium-family protocol instrumentation | CDP | `<skill-dir>/references/chrome-devtools-protocol-debugger.md` |
| Standards-oriented cross-browser automation and events | WebDriver BiDi | `<skill-dir>/references/webdriver-bidi-debugger.md` |
| Safari, WebKit, WKWebView, WebKitGTK, or WPE inspection | WebKit debugging | `<skill-dir>/references/webkit-debugging.md` |

## Evidence Rules

Record browser name/version, profile state, URL origin, cookies/storage state, permissions, frame tree, service worker state, network requests, console errors, screenshots or recordings, and any protocol commands that changed browser state. Pair browser evidence with Source/SAST or API replay when the root cause is server-side.
