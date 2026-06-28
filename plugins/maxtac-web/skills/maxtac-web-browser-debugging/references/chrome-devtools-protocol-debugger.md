# Chrome DevTools Protocol Debugger

Use Chrome DevTools Protocol (`CDP`) for browser DAST when the target is a
Chromium-based browser and the task needs Chromium-specific instrumentation
that is unavailable, incomplete, or easier to validate outside WebDriver BiDi.
Prefer CDP for DevTools-level page, runtime, network, target, tracing,
performance, storage, emulation, input, and browser control on Chrome, Chrome
for Testing, Chromium, and Microsoft Edge.

Prefer WebDriver BiDi when the task needs a standard cross-browser protocol.
Prefer WebKit debugging for Safari and WebKit targets.

Prefer the live protocol viewer, the browser's `/json/protocol` endpoint,
Chrome documentation, Edge documentation, and installed browser output for
exact command names and parameter shapes. CDP has stable protocol snapshots and
a tip-of-tree protocol that changes frequently. Browser version, channel,
command-line flags, headless mode, client library, and target type can all
change what is available.

Treat CDP as mutable execution. It can change browser state through navigation,
script evaluation, script compilation, breakpoints, input events, cookies,
storage, browser contexts, headers, downloads, permissions, emulation, network
request handling, tracing, profiling, and browser lifecycle commands. Keep
final evidence separate from observations that only happen because automation
changed timing, cache state, user activation, origin state, network behavior,
or target attachment.

## Contents

- [Quick Commands](#quick-commands)
- [Launch and Discovery](#launch-and-discovery)
- [Protocol Model](#protocol-model)
- [Targets and Sessions](#targets-and-sessions)
- [Raw WebSocket Frames](#raw-websocket-frames)
- [Core Enable Sequence](#core-enable-sequence)
- [Page Navigation and Frames](#page-navigation-and-frames)
- [Runtime, Console, and Exceptions](#runtime-console-and-exceptions)
- [JavaScript Debugger Domain](#javascript-debugger-domain)
- [Network Events and Bodies](#network-events-and-bodies)
- [Fetch Request Control](#fetch-request-control)
- [DOM, Accessibility, and Snapshots](#dom-accessibility-and-snapshots)
- [Storage, Cookies, and Browser Contexts](#storage-cookies-and-browser-contexts)
- [Input, Downloads, and Emulation](#input-downloads-and-emulation)
- [Performance and Tracing](#performance-and-tracing)
- [DevTools, Extensions, and Client Libraries](#devtools-extensions-and-client-libraries)
- [Evidence Automation](#evidence-automation)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Start Chrome with a fresh test profile and a local CDP endpoint:

```text
chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/cdp-profile \
  --no-first-run \
  --no-default-browser-check
```

Start Chrome for Testing or Chromium in headless mode:

```text
chrome \
  --headless=new \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/cdp-profile \
  https://example.test/
```

Windows examples:

```text
"%ProgramFiles%\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\cdp-profile"
"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\edge-cdp-profile"
```

Discover the browser endpoint and page targets:

```text
curl -s http://127.0.0.1:9222/json/version
curl -s http://127.0.0.1:9222/json/list
curl -s http://127.0.0.1:9222/json/protocol
```

Common protocol frames:

```json
{"id":1,"method":"Browser.getVersion","params":{}}
{"id":2,"method":"Target.getTargets","params":{}}
{"id":3,"method":"Target.createTarget","params":{"url":"about:blank"}}
{"id":4,"method":"Target.attachToTarget","params":{"targetId":"TARGET_ID","flatten":true}}
{"id":5,"sessionId":"SESSION_ID","method":"Page.enable","params":{}}
{"id":6,"sessionId":"SESSION_ID","method":"Runtime.enable","params":{}}
{"id":7,"sessionId":"SESSION_ID","method":"Network.enable","params":{}}
{"id":8,"sessionId":"SESSION_ID","method":"Page.navigate","params":{"url":"https://example.test/"}}
```

Use one of these clients for practical work:

```text
Raw WebSocket client for protocol-level debugging
Puppeteer CDPSession for Node.js page-level CDP
Playwright CDPSession for Chromium-only CDP access
chrome.debugger API for Chrome extension tooling
DevTools Protocol Monitor for interactive command discovery
```

Record:

```text
Browser executable path
Browser channel and version
Profile directory
Remote debugging address and port
/json/version response
/json/list response
/json/protocol response or protocol viewer URL
Client library name and version
```

## Launch and Discovery

CDP is exposed through a WebSocket endpoint. A browser launched with
`--remote-debugging-port=PORT` exposes HTTP discovery endpoints on that port.

Use an isolated profile. Chrome documentation states that newer Chrome builds
only honor remote debugging switches when a non-default `--user-data-dir` is
used. For repeatable evidence, always launch a fresh profile path and record it.

Use loopback unless the authorized test explicitly requires remote access:

```text
--remote-debugging-address=127.0.0.1
--remote-debugging-port=9222
--user-data-dir=/tmp/cdp-profile
```

Avoid reusing a personal browser profile. Profile reuse can mix cookies,
extensions, cached resources, permissions, service workers, storage, and
download state into the evidence.

Discovery endpoints:

```text
GET /json/version
GET /json/list
GET /json/protocol
```

`/json/version` identifies the browser and returns the browser-level
`webSocketDebuggerUrl`.

Example response fields to preserve:

```text
Browser
Protocol-Version
User-Agent
V8-Version
WebKit-Version
webSocketDebuggerUrl
```

`/json/list` returns inspectable targets. Page entries usually include:

```text
id
type
title
url
webSocketDebuggerUrl
devtoolsFrontendUrl
```

`/json/protocol` returns the protocol schema supported by that running browser.
Prefer it over a remembered command shape when a command fails unexpectedly.

Use `--remote-debugging-port=0` when a fixed port is not acceptable. Read the
chosen port from the browser output or the `DevToolsActivePort` file in the
profile directory.

## Protocol Model

CDP messages are JSON objects sent over WebSocket.

Command:

```json
{"id":1,"method":"Runtime.evaluate","params":{"expression":"document.title"}}
```

Result:

```json
{"id":1,"result":{"result":{"type":"string","value":"Example"}}}
```

Error:

```json
{"id":1,"error":{"code":-32601,"message":"'Runtime.evaluate' wasn't found"}}
```

Event:

```json
{"method":"Page.loadEventFired","params":{"timestamp":12345.678}}
```

CDP is asynchronous. Command responses can arrive out of order. Always match
responses by `id`.

Most command names use `Domain.method`:

```text
Browser.getVersion
Target.getTargets
Page.navigate
Runtime.evaluate
Network.enable
Fetch.enable
Storage.getCookies
Emulation.setTimezoneOverride
Tracing.start
```

Important protocol versions:

- Stable protocol snapshots cover a conservative subset.
- Tip-of-tree protocol documents the current development surface.
- The running browser's `/json/protocol` endpoint is the best local truth.

Do not assume one Chromium version has the same domains, parameters, enum
values, or events as another. Record the browser version with every run.

## Targets and Sessions

CDP has browser-level targets and page-level targets.

Browser WebSocket:

```text
Use the webSocketDebuggerUrl from /json/version.
Use Browser.* and Target.* commands here.
Create targets and attach to them from here.
```

Page WebSocket:

```text
Use the webSocketDebuggerUrl from /json/list.
Useful for simple single-page Page.*, Runtime.*, Network.*, DOM.*, and Log.*
work.
```

Prefer the browser WebSocket plus flat target sessions for reliable automation.
Flat sessions carry a `sessionId` on every command and event.

List targets:

```json
{"id":10,"method":"Target.getTargets","params":{}}
```

Create a blank page target:

```json
{"id":11,"method":"Target.createTarget","params":{"url":"about:blank"}}
```

Attach to a target:

```json
{
  "id": 12,
  "method": "Target.attachToTarget",
  "params": {
    "targetId": "TARGET_ID",
    "flatten": true
  }
}
```

The result contains a `sessionId`:

```json
{"id":12,"result":{"sessionId":"SESSION_ID"}}
```

Send page-domain commands through that session:

```json
{"id":13,"sessionId":"SESSION_ID","method":"Page.enable","params":{}}
```

Discover and attach to new targets:

```json
{
  "id": 14,
  "method": "Target.setDiscoverTargets",
  "params": {
    "discover": true
  }
}
```

Auto-attach to related targets:

```json
{
  "id": 15,
  "method": "Target.setAutoAttach",
  "params": {
    "autoAttach": true,
    "waitForDebuggerOnStart": false,
    "flatten": true
  }
}
```

Useful target events:

```text
Target.targetCreated
Target.targetInfoChanged
Target.targetDestroyed
Target.attachedToTarget
Target.detachedFromTarget
```

Detach when done:

```json
{"id":16,"method":"Target.detachFromTarget","params":{"sessionId":"SESSION_ID"}}
```

Close a target:

```json
{"id":17,"method":"Target.closeTarget","params":{"targetId":"TARGET_ID"}}
```

Record every target ID, target type, URL, and session ID. Pages, workers,
service workers, iframes, and background pages can emit separate events.

## Raw WebSocket Frames

Use a raw WebSocket client when debugging protocol support, client-library
behavior, event order, or target-session routing.

Minimal Python pattern:

```python
import asyncio
import json
import websockets

CDP_URL = "ws://127.0.0.1:9222/devtools/browser/BROWSER_ID"

async def main():
    next_id = 1
    async with websockets.connect(CDP_URL) as ws:
        await ws.send(json.dumps({
            "id": next_id,
            "method": "Browser.getVersion",
            "params": {}
        }))
        print(await ws.recv())

asyncio.run(main())
```

For evidence, wrap send and receive with:

```text
timestamp
direction
WebSocket URL
targetId when known
sessionId when present
raw JSON frame
parsed command or event name
```

Do not rely on message order. CDP can interleave command results with events
from multiple sessions.

## Core Enable Sequence

Most events are silent until their domain is enabled. Enable the domains needed
before navigation or interaction.

Single-page baseline:

```json
{"id":20,"sessionId":"SESSION_ID","method":"Page.enable","params":{}}
{"id":21,"sessionId":"SESSION_ID","method":"Runtime.enable","params":{}}
{"id":22,"sessionId":"SESSION_ID","method":"Log.enable","params":{}}
{"id":23,"sessionId":"SESSION_ID","method":"Network.enable","params":{}}
```

Navigation lifecycle:

```json
{"id":24,"sessionId":"SESSION_ID","method":"Page.setLifecycleEventsEnabled","params":{"enabled":true}}
```

Debugger only when needed:

```json
{"id":25,"sessionId":"SESSION_ID","method":"Debugger.enable","params":{}}
```

Fetch request control only when mutation is part of the experiment:

```json
{"id":26,"sessionId":"SESSION_ID","method":"Fetch.enable","params":{"patterns":[{"urlPattern":"*"}]}}
```

Disable domains during cleanup:

```json
{"id":27,"sessionId":"SESSION_ID","method":"Fetch.disable","params":{}}
{"id":28,"sessionId":"SESSION_ID","method":"Debugger.disable","params":{}}
{"id":29,"sessionId":"SESSION_ID","method":"Network.disable","params":{}}
{"id":30,"sessionId":"SESSION_ID","method":"Log.disable","params":{}}
{"id":31,"sessionId":"SESSION_ID","method":"Runtime.disable","params":{}}
{"id":32,"sessionId":"SESSION_ID","method":"Page.disable","params":{}}
```

## Page Navigation and Frames

Navigate:

```json
{
  "id": 40,
  "sessionId": "SESSION_ID",
  "method": "Page.navigate",
  "params": {
    "url": "https://example.test/"
  }
}
```

The result can include:

```text
frameId
loaderId
errorText
isDownload
```

Track frame and lifecycle events:

```text
Page.frameStartedNavigating
Page.frameNavigated
Page.frameStartedLoading
Page.domContentEventFired
Page.loadEventFired
Page.lifecycleEvent
Page.frameStoppedLoading
Page.navigatedWithinDocument
Page.frameDetached
```

Get the frame tree:

```json
{"id":41,"sessionId":"SESSION_ID","method":"Page.getFrameTree","params":{}}
```

Reload:

```json
{"id":42,"sessionId":"SESSION_ID","method":"Page.reload","params":{"ignoreCache":false}}
```

Stop loading:

```json
{"id":43,"sessionId":"SESSION_ID","method":"Page.stopLoading","params":{}}
```

Capture a screenshot:

```json
{
  "id": 44,
  "sessionId": "SESSION_ID",
  "method": "Page.captureScreenshot",
  "params": {
    "format": "png",
    "fromSurface": true,
    "captureBeyondViewport": true
  }
}
```

Print to PDF in headless-capable contexts:

```json
{
  "id": 45,
  "sessionId": "SESSION_ID",
  "method": "Page.printToPDF",
  "params": {
    "printBackground": true
  }
}
```

Preserve screenshots and PDFs as separate files. Record the command frame, the
frame tree, viewport, device scale factor, and URL at capture time.

## Runtime, Console, and Exceptions

Enable runtime events before navigation when console or exception evidence
matters:

```json
{"id":50,"sessionId":"SESSION_ID","method":"Runtime.enable","params":{}}
```

Useful runtime events:

```text
Runtime.consoleAPICalled
Runtime.exceptionThrown
Runtime.exceptionRevoked
Runtime.executionContextCreated
Runtime.executionContextDestroyed
Runtime.executionContextsCleared
```

Evaluate a passive expression:

```json
{
  "id": 51,
  "sessionId": "SESSION_ID",
  "method": "Runtime.evaluate",
  "params": {
    "expression": "document.title",
    "awaitPromise": true,
    "returnByValue": true,
    "objectGroup": "evidence"
  }
}
```

Call a function:

```json
{
  "id": 52,
  "sessionId": "SESSION_ID",
  "method": "Runtime.callFunctionOn",
  "params": {
    "functionDeclaration": "function () { return location.href; }",
    "executionContextId": 1,
    "awaitPromise": true,
    "returnByValue": true,
    "objectGroup": "evidence"
  }
}
```

Release remote objects:

```json
{"id":53,"sessionId":"SESSION_ID","method":"Runtime.releaseObjectGroup","params":{"objectGroup":"evidence"}}
```

Compile a script without running it:

```json
{
  "id": 54,
  "sessionId": "SESSION_ID",
  "method": "Runtime.compileScript",
  "params": {
    "expression": "document.title",
    "sourceURL": "cdp-evidence.js",
    "persistScript": false,
    "executionContextId": 1
  }
}
```

Add a script to run on future document creation:

```json
{
  "id": 55,
  "sessionId": "SESSION_ID",
  "method": "Page.addScriptToEvaluateOnNewDocument",
  "params": {
    "source": "window.__cdpRunId = 'RUN_ID';"
  }
}
```

Remove the injected script by identifier:

```json
{
  "id": 56,
  "sessionId": "SESSION_ID",
  "method": "Page.removeScriptToEvaluateOnNewDocument",
  "params": {
    "identifier": "SCRIPT_IDENTIFIER"
  }
}
```

Script evaluation can change page state. Separate passive reads from setup
actions and record every expression, execution context, result object, and
cleanup command.

## JavaScript Debugger Domain

Use the `Debugger` domain for source mapping, script discovery, breakpoints,
and pause state. Keep it disabled unless needed because it changes timing and
execution flow.

Enable and collect script events:

```json
{"id":60,"sessionId":"SESSION_ID","method":"Debugger.enable","params":{}}
```

Useful debugger events:

```text
Debugger.scriptParsed
Debugger.scriptFailedToParse
Debugger.paused
Debugger.resumed
Debugger.breakpointResolved
```

Pause on exceptions:

```json
{"id":61,"sessionId":"SESSION_ID","method":"Debugger.setPauseOnExceptions","params":{"state":"uncaught"}}
```

Set a breakpoint by URL:

```json
{
  "id": 62,
  "sessionId": "SESSION_ID",
  "method": "Debugger.setBreakpointByUrl",
  "params": {
    "lineNumber": 10,
    "url": "https://example.test/app.js",
    "columnNumber": 0
  }
}
```

Get script source:

```json
{
  "id": 63,
  "sessionId": "SESSION_ID",
  "method": "Debugger.getScriptSource",
  "params": {
    "scriptId": "SCRIPT_ID"
  }
}
```

Resume:

```json
{"id":64,"sessionId":"SESSION_ID","method":"Debugger.resume","params":{}}
```

Disable:

```json
{"id":65,"sessionId":"SESSION_ID","method":"Debugger.disable","params":{}}
```

Record breakpoint IDs, script IDs, source URLs, execution contexts, pause
reasons, call frames, and resume commands. Do not treat a paused state as
normal page timing.

## Network Events and Bodies

Enable network events before navigation:

```json
{
  "id": 70,
  "sessionId": "SESSION_ID",
  "method": "Network.enable",
  "params": {
    "maxTotalBufferSize": 10485760,
    "maxResourceBufferSize": 5242880,
    "maxPostDataSize": 1048576
  }
}
```

Useful network events:

```text
Network.requestWillBeSent
Network.requestWillBeSentExtraInfo
Network.responseReceived
Network.responseReceivedExtraInfo
Network.dataReceived
Network.loadingFinished
Network.loadingFailed
Network.webSocketCreated
Network.webSocketFrameSent
Network.webSocketFrameReceived
Network.webTransportCreated
Network.eventSourceMessageReceived
```

Retrieve request body when available:

```json
{
  "id": 71,
  "sessionId": "SESSION_ID",
  "method": "Network.getRequestPostData",
  "params": {
    "requestId": "REQUEST_ID"
  }
}
```

Retrieve response body after `Network.loadingFinished`:

```json
{
  "id": 72,
  "sessionId": "SESSION_ID",
  "method": "Network.getResponseBody",
  "params": {
    "requestId": "REQUEST_ID"
  }
}
```

The response body result can include base64-encoded data:

```text
body
base64Encoded
```

Read cookies visible to the network stack:

```json
{"id":73,"sessionId":"SESSION_ID","method":"Network.getCookies","params":{"urls":["https://example.test/"]}}
```

Set extra headers only when the experiment requires it:

```json
{
  "id": 74,
  "sessionId": "SESSION_ID",
  "method": "Network.setExtraHTTPHeaders",
  "params": {
    "headers": {
      "X-Lab-Run": "RUN_ID"
    }
  }
}
```

Disable cache only when the experiment requires it:

```json
{"id":75,"sessionId":"SESSION_ID","method":"Network.setCacheDisabled","params":{"cacheDisabled":true}}
```

Network capture is sensitive to timing and buffering. Record:

```text
requestId
loaderId
frameId
documentURL
initiator
redirectResponse
request headers and post data availability
response status and headers
encodedDataLength
body retrieval command and result
cache setting
extra headers setting
```

Prefer passive `Network.*` events for final evidence. Header changes, cache
changes, and request handling can change server-side logs and browser behavior.

## Fetch Request Control

Use the `Fetch` domain only when controlled request handling is the point of
the experiment. It can pause requests and responses, which changes timing.

Enable Fetch for matching URLs:

```json
{
  "id": 80,
  "sessionId": "SESSION_ID",
  "method": "Fetch.enable",
  "params": {
    "patterns": [
      {
        "urlPattern": "https://example.test/api/*",
        "requestStage": "Request"
      }
    ]
  }
}
```

Use a response-stage pattern when response bodies or response continuation are
needed:

```json
{
  "id": 81,
  "sessionId": "SESSION_ID",
  "method": "Fetch.enable",
  "params": {
    "patterns": [
      {
        "urlPattern": "https://example.test/api/*",
        "requestStage": "Response"
      }
    ]
  }
}
```

Paused request event:

```text
Fetch.requestPaused
```

Continue a paused request unchanged:

```json
{
  "id": 82,
  "sessionId": "SESSION_ID",
  "method": "Fetch.continueRequest",
  "params": {
    "requestId": "FETCH_REQUEST_ID"
  }
}
```

Continue a paused response unchanged:

```json
{
  "id": 83,
  "sessionId": "SESSION_ID",
  "method": "Fetch.continueResponse",
  "params": {
    "requestId": "FETCH_REQUEST_ID"
  }
}
```

Get a paused response body:

```json
{
  "id": 84,
  "sessionId": "SESSION_ID",
  "method": "Fetch.getResponseBody",
  "params": {
    "requestId": "FETCH_REQUEST_ID"
  }
}
```

Disable Fetch during cleanup:

```json
{"id":85,"sessionId":"SESSION_ID","method":"Fetch.disable","params":{}}
```

Record every paused request ID, the matching pattern, request stage, continue
command, body command, and cleanup command.

## DOM, Accessibility, and Snapshots

Use DOM domains for evidence about page structure, selected nodes, computed
styles, and accessibility state.

Get the DOM document:

```json
{
  "id": 90,
  "sessionId": "SESSION_ID",
  "method": "DOM.getDocument",
  "params": {
    "depth": 2,
    "pierce": true
  }
}
```

Query a selector:

```json
{
  "id": 91,
  "sessionId": "SESSION_ID",
  "method": "DOM.querySelector",
  "params": {
    "nodeId": 1,
    "selector": "form"
  }
}
```

Resolve a DOM node to a runtime object:

```json
{
  "id": 92,
  "sessionId": "SESSION_ID",
  "method": "DOM.resolveNode",
  "params": {
    "nodeId": 2,
    "objectGroup": "evidence"
  }
}
```

Capture a DOM snapshot:

```json
{
  "id": 93,
  "sessionId": "SESSION_ID",
  "method": "DOMSnapshot.captureSnapshot",
  "params": {
    "computedStyles": ["display", "visibility", "position"]
  }
}
```

Get full accessibility tree:

```json
{"id":94,"sessionId":"SESSION_ID","method":"Accessibility.getFullAXTree","params":{}}
```

DOM node IDs are session-local and can become invalid after navigation or DOM
mutation. Record the frame ID, URL, node ID, backend node ID, selector, and
timestamp with each DOM observation.

## Storage, Cookies, and Browser Contexts

Use browser contexts to isolate runs:

```json
{"id":100,"method":"Target.createBrowserContext","params":{}}
```

Create a page in that context:

```json
{
  "id": 101,
  "method": "Target.createTarget",
  "params": {
    "url": "about:blank",
    "browserContextId": "BROWSER_CONTEXT_ID"
  }
}
```

Dispose of the context during cleanup:

```json
{
  "id": 102,
  "method": "Target.disposeBrowserContext",
  "params": {
    "browserContextId": "BROWSER_CONTEXT_ID"
  }
}
```

Read cookies through the Storage domain:

```json
{
  "id": 103,
  "method": "Storage.getCookies",
  "params": {
    "browserContextId": "BROWSER_CONTEXT_ID"
  }
}
```

Clear origin storage only when the experiment requires cleanup:

```json
{
  "id": 104,
  "method": "Storage.clearDataForOrigin",
  "params": {
    "origin": "https://example.test",
    "storageTypes": "cookies,local_storage,indexeddb,cache_storage"
  }
}
```

Manage permissions only in an isolated profile or browser context:

```json
{
  "id": 105,
  "method": "Browser.setPermission",
  "params": {
    "permission": {"name":"geolocation"},
    "setting": "granted",
    "origin": "https://example.test",
    "browserContextId": "BROWSER_CONTEXT_ID"
  }
}
```

Reset permissions:

```json
{
  "id": 106,
  "method": "Browser.resetPermissions",
  "params": {
    "browserContextId": "BROWSER_CONTEXT_ID"
  }
}
```

Storage and permissions are high-impact. Record the profile path, browser
context ID, origin, storage type, cookie partition details when present, and
cleanup commands.

## Input, Downloads, and Emulation

CDP can synthesize input and alter the browser environment. Use these commands
only when the test requires them and record the resulting state.

Mouse event:

```json
{
  "id": 110,
  "sessionId": "SESSION_ID",
  "method": "Input.dispatchMouseEvent",
  "params": {
    "type": "mousePressed",
    "x": 100,
    "y": 200,
    "button": "left",
    "clickCount": 1
  }
}
```

Keyboard event:

```json
{
  "id": 111,
  "sessionId": "SESSION_ID",
  "method": "Input.dispatchKeyEvent",
  "params": {
    "type": "keyDown",
    "key": "Enter",
    "code": "Enter",
    "windowsVirtualKeyCode": 13
  }
}
```

Set device metrics:

```json
{
  "id": 112,
  "sessionId": "SESSION_ID",
  "method": "Emulation.setDeviceMetricsOverride",
  "params": {
    "width": 1280,
    "height": 720,
    "deviceScaleFactor": 1,
    "mobile": false
  }
}
```

Set geolocation:

```json
{
  "id": 113,
  "sessionId": "SESSION_ID",
  "method": "Emulation.setGeolocationOverride",
  "params": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "accuracy": 10
  }
}
```

Set timezone, locale, and user agent:

```json
{"id":114,"sessionId":"SESSION_ID","method":"Emulation.setTimezoneOverride","params":{"timezoneId":"America/New_York"}}
{"id":115,"sessionId":"SESSION_ID","method":"Emulation.setLocaleOverride","params":{"locale":"en-US"}}
{"id":116,"sessionId":"SESSION_ID","method":"Emulation.setUserAgentOverride","params":{"userAgent":"TestAgent/1.0"}}
```

Configure downloads:

```json
{
  "id": 117,
  "method": "Browser.setDownloadBehavior",
  "params": {
    "behavior": "allow",
    "downloadPath": "/absolute/path/to/downloads",
    "eventsEnabled": true
  }
}
```

Download events:

```text
Browser.downloadWillBegin
Browser.downloadProgress
```

Clear emulation where supported:

```json
{"id":118,"sessionId":"SESSION_ID","method":"Emulation.clearGeolocationOverride","params":{}}
{"id":119,"sessionId":"SESSION_ID","method":"Emulation.clearDeviceMetricsOverride","params":{}}
```

Input and emulation can change event order, layout, permission prompts,
server-side negotiation, and visible evidence. Capture screenshots after state
changes.

## Performance and Tracing

Use `Performance` for metrics and `Tracing` for timeline evidence. Tracing can
generate large files and affect timing.

Enable performance metrics:

```json
{"id":120,"sessionId":"SESSION_ID","method":"Performance.enable","params":{}}
```

Read metrics:

```json
{"id":121,"sessionId":"SESSION_ID","method":"Performance.getMetrics","params":{}}
```

Start tracing:

```json
{
  "id": 122,
  "method": "Tracing.start",
  "params": {
    "categories": "devtools.timeline",
    "transferMode": "ReturnAsStream"
  }
}
```

End tracing:

```json
{"id":123,"method":"Tracing.end","params":{}}
```

When `Tracing.tracingComplete` returns a stream handle, read it through the
`IO` domain:

```json
{"id":124,"method":"IO.read","params":{"handle":"STREAM_HANDLE"}}
{"id":125,"method":"IO.close","params":{"handle":"STREAM_HANDLE"}}
```

Record trace categories, trace start and end time, stream reads, output file
hash, and browser version.

## DevTools, Extensions, and Client Libraries

Chrome DevTools includes Protocol Monitor. Use it to inspect DevTools traffic
and test protocol commands interactively when validating command shape.

Chrome extensions can use the `chrome.debugger` API as an alternate transport.
The extension must declare the `debugger` permission. The API exposes methods
to attach to targets, send CDP commands, and receive CDP events, but it does
not expose every protocol domain.

Puppeteer CDPSession:

```javascript
const client = await page.createCDPSession();
await client.send('Network.enable');
client.on('Network.requestWillBeSent', event => {
  console.log(event.request.url);
});
```

Playwright CDPSession for Chromium:

```javascript
const session = await page.context().newCDPSession(page);
await session.send('Runtime.enable');
const result = await session.send('Runtime.evaluate', {
  expression: 'document.title',
  returnByValue: true
});
```

Playwright can also connect to an existing CDP endpoint for Chromium:

```javascript
const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
```

Record the abstraction layer used:

```text
Raw WebSocket
Puppeteer CDPSession
Playwright CDPSession
chrome.debugger extension API
DevTools Protocol Monitor
Other client and version
```

Client libraries can rename helpers, hide target sessions, attach
automatically, or buffer events. Preserve raw protocol frames when exact
evidence matters.

## Evidence Automation

Create a run directory:

```text
RUN_DIR="evidence/$(date +%Y%m%d-%H%M%S)-cdp"
mkdir -p "$RUN_DIR"
```

Record discovery output:

```text
curl -s http://127.0.0.1:9222/json/version > "$RUN_DIR/json-version.json"
curl -s http://127.0.0.1:9222/json/list > "$RUN_DIR/json-list.json"
curl -s http://127.0.0.1:9222/json/protocol > "$RUN_DIR/json-protocol.json"
```

Record browser process details:

```text
ps -ef | grep -E 'chrome|chromium|msedge'
```

Capture baseline protocol state:

```json
{"id":130,"method":"Browser.getVersion","params":{}}
{"id":131,"method":"Target.getTargets","params":{}}
```

For each target, preserve:

```text
targetId
sessionId
target type
initial URL
attached time
enabled domains
navigation command and result
event stream
screenshot or PDF command and output file
network request map
runtime console and exception events
storage and cookie observations
cleanup commands
```

Save screenshots:

```text
Decode Page.captureScreenshot result.data from base64 into a .png file.
Record the frame ID, URL, viewport, timestamp, and command ID.
```

Save network bodies:

```text
Call Network.getResponseBody after Network.loadingFinished.
Decode body when base64Encoded is true.
Store metadata and body separately.
```

Close cleanly:

```json
{"id":132,"method":"Target.detachFromTarget","params":{"sessionId":"SESSION_ID"}}
{"id":133,"method":"Target.closeTarget","params":{"targetId":"TARGET_ID"}}
{"id":134,"method":"Target.disposeBrowserContext","params":{"browserContextId":"BROWSER_CONTEXT_ID"}}
{"id":135,"method":"Browser.close","params":{}}
```

Do not close a shared browser that the user is actively using. Prefer isolated
profiles and isolated browser processes for evidence runs.

## Failure Modes

Remote debugging flag appears ignored:

- Use a non-default `--user-data-dir`.
- Confirm the browser process command line.
- Confirm no existing process reused a default profile.
- Check `DevToolsActivePort` in the profile directory.

Cannot connect to WebSocket:

- Confirm the port is listening on loopback.
- Re-read `/json/version` and `/json/list`.
- Use the exact `webSocketDebuggerUrl`.
- Check proxy, firewall, container, or WSL port forwarding.

Command not found:

- Compare the command against `/json/protocol`.
- Confirm browser channel and version.
- Confirm whether the command is experimental or deprecated.
- Confirm whether the command belongs on the browser session or page session.

No events:

- Enable the domain before navigation or interaction.
- Confirm the command included the correct `sessionId`.
- Confirm the client is attached to the target emitting the event.
- Attach to workers or related targets when needed.

Wrong target:

- Use `Target.getTargets`.
- Record target type and URL.
- Attach from the browser WebSocket with flat sessions.
- Avoid assuming the first `/json/list` entry is the page under test.

Response bodies unavailable:

- Enable Network before navigation.
- Increase buffer sizes where needed.
- Request the body after `Network.loadingFinished`.
- Preserve request IDs across redirects.
- Expect some cached, streaming, or failed resources to lack bodies.

Script evaluation fails:

- Wait for `Runtime.executionContextCreated`.
- Use the intended execution context or frame.
- Avoid stale object IDs after navigation.
- Use `Runtime.releaseObjectGroup` after remote object use.

Target detaches:

- Check for page close, navigation, crash, browser shutdown, or competing
  debugger attachment.
- Re-run `Target.getTargets`.
- Reattach and re-enable domains.

Evidence changes after automation:

- Compare passive observation runs against mutation runs.
- Record every state-changing command.
- Use fresh profiles and browser contexts.
- Keep screenshots and protocol logs tied to exact command IDs.

## Evidence Checklist

Collect:

- Official documentation URLs consulted, protocol viewer version, and
  `/json/protocol` from the running browser when available.
- Browser executable path, channel, version, user agent, command line, profile
  path, and headless setting.
- Remote debugging address, port, and all discovery endpoint responses.
- Client type, client version, WebSocket URL, and whether browser or page
  endpoint was used.
- Raw WebSocket frames with send/receive direction, timestamps, IDs, methods,
  target IDs, and session IDs.
- `Browser.getVersion`, `Target.getTargets`, target creation, attachment, and
  detach or close commands.
- Enabled domains and their enable command results.
- Navigation command, frame tree, lifecycle events, URL, loader IDs, and final
  screenshot or PDF.
- Console, log, runtime exception, and JavaScript debugger events.
- Network events, request IDs, redirect chain, headers, body retrieval commands,
  body files, and buffer settings.
- Fetch request-control patterns, paused requests, continuation commands, and
  disable command when used.
- DOM snapshots, selectors, node IDs, frame IDs, and runtime object cleanup.
- Storage, cookies, permissions, browser contexts, and cleanup commands.
- Input, emulation, downloads, tracing, and performance commands.
- Every state-changing operation before final evidence capture.

## References

- https://chromedevtools.github.io/devtools-protocol/
- https://chromedevtools.github.io/devtools-protocol/tot/
- https://chromedevtools.github.io/devtools-protocol/1-3/
- https://chromedevtools.github.io/devtools-protocol/tot/Browser/
- https://chromedevtools.github.io/devtools-protocol/tot/Target/
- https://chromedevtools.github.io/devtools-protocol/tot/Page/
- https://chromedevtools.github.io/devtools-protocol/tot/Runtime/
- https://chromedevtools.github.io/devtools-protocol/tot/Debugger/
- https://chromedevtools.github.io/devtools-protocol/tot/Network/
- https://chromedevtools.github.io/devtools-protocol/tot/Fetch/
- https://chromedevtools.github.io/devtools-protocol/tot/DOM/
- https://chromedevtools.github.io/devtools-protocol/tot/DOMSnapshot/
- https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/
- https://chromedevtools.github.io/devtools-protocol/tot/Storage/
- https://chromedevtools.github.io/devtools-protocol/tot/Input/
- https://chromedevtools.github.io/devtools-protocol/tot/Emulation/
- https://chromedevtools.github.io/devtools-protocol/tot/Performance/
- https://chromedevtools.github.io/devtools-protocol/tot/Tracing/
- https://developer.chrome.com/docs/devtools/protocol/
- https://developer.chrome.com/blog/remote-debugging-port
- https://developer.chrome.com/docs/extensions/reference/api/debugger
- https://github.com/ChromeDevTools/devtools-protocol
- https://pptr.dev/api/puppeteer.cdpsession
- https://playwright.dev/docs/api/class-cdpsession
- https://playwright.dev/docs/api/class-browsertype#browser-type-connect-over-cdp
