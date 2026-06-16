# WebDriver BiDi Debugger

Use WebDriver BiDi for browser DAST when the task needs standard,
cross-browser, event-driven browser automation over WebSockets. Prefer it for
browser console logs, JavaScript exception capture, navigation events, network
events, script evaluation, browser contexts, user input, cookies, downloads,
and environment emulation when the target browser and driver support the needed
module.

Prefer Chrome DevTools Protocol when the required Chromium-only debugging
surface is not exposed through WebDriver BiDi. Prefer WebKit debugging for
Safari/WebKit targets where BiDi support is unavailable or incomplete.

Prefer the W3C specification, MDN module reference, installed driver help, and
client-library docs for exact command names and parameter shapes. WebDriver
BiDi is actively evolving, and browser, driver, Selenium, and WebdriverIO
support can differ by version.

Treat WebDriver BiDi as mutable execution. It can change browser state through
navigation, script evaluation, preload scripts, input events, cookies, user
contexts, download settings, network intercepts, headers, emulation settings,
permissions, and browser lifecycle commands. Keep final evidence separate from
observations that only happen because automation changed timing, cache, user
activation, origin state, storage, or network behavior.

## Contents

- [Quick Commands](#quick-commands)
- [Protocol Model](#protocol-model)
- [Starting a BiDi Session](#starting-a-bidi-session)
- [Raw WebSocket Frames](#raw-websocket-frames)
- [Session Subscriptions](#session-subscriptions)
- [Browsing Contexts and Navigation](#browsing-contexts-and-navigation)
- [Logs and JavaScript Exceptions](#logs-and-javascript-exceptions)
- [Script Evaluation and Realms](#script-evaluation-and-realms)
- [Network Events and Intercepts](#network-events-and-intercepts)
- [Storage, Cookies, and User Contexts](#storage-cookies-and-user-contexts)
- [Input, Files, Downloads, and Emulation](#input-files-downloads-and-emulation)
- [Selenium and WebdriverIO Clients](#selenium-and-webdriverio-clients)
- [Evidence Automation](#evidence-automation)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Start a local driver:

```text
chromedriver --port=9515 --verbose --log-path=chromedriver.log
geckodriver --port 4444 --log trace
java -jar selenium-server.jar standalone --port 4444
```

Ask for a WebDriver session with a BiDi WebSocket URL:

```text
curl -s -X POST "$WD_URL/session" \
  -H "Content-Type: application/json" \
  --data '{"capabilities":{"alwaysMatch":{"browserName":"chrome","webSocketUrl":true}}}'
```

Firefox example:

```text
curl -s -X POST "$WD_URL/session" \
  -H "Content-Type: application/json" \
  --data '{"capabilities":{"alwaysMatch":{"browserName":"firefox","webSocketUrl":true}}}'
```

Record the returned fields:

```text
sessionId
capabilities.browserName
capabilities.browserVersion
capabilities.platformName
capabilities.webSocketUrl
```

Useful BiDi command frames:

```json
{"id":1,"method":"session.status","params":{}}
{"id":2,"method":"browsingContext.getTree","params":{}}
{"id":3,"method":"session.subscribe","params":{"events":["log.entryAdded","network.beforeRequestSent"]}}
{"id":4,"method":"browsingContext.navigate","params":{"context":"CONTEXT_ID","url":"https://example.test/","wait":"complete"}}
{"id":5,"method":"script.evaluate","params":{"expression":"document.title","target":{"context":"CONTEXT_ID"},"awaitPromise":true,"resultOwnership":"none"}}
```

Use one of these clients for practical work:

```text
Selenium 4 BiDi APIs
WebdriverIO WebDriver BiDi protocol APIs
Puppeteer with protocol set to webDriverBiDi where supported
Raw WebSocket client for protocol-level debugging
```

## Protocol Model

WebDriver BiDi extends WebDriver with bidirectional browser communication. A
classic WebDriver command is HTTP request/response. A BiDi connection is a
WebSocket that can carry command responses and browser events in both
directions during the same session.

The spec uses these terms:

- Local end: automation client.
- Remote end: browser or driver endpoint.
- Command: async operation sent by the local end.
- Result: success response matched to a command by `id`.
- Error: error response matched to a command by `id`.
- Event: browser-originated notification with `type` set to `event`.
- Module: command and event group with names like `script.evaluate` or
  `network.responseCompleted`.

Command responses can finish out of order. Always correlate by numeric `id`,
not by response order.

Protocol frames use module-prefixed methods:

```json
{"id":10,"method":"browsingContext.getTree","params":{}}
```

Successful responses:

```json
{"type":"success","id":10,"result":{"contexts":[]}}
```

Errors:

```json
{"type":"error","id":10,"error":"invalid argument","message":"..."}
```

Events:

```json
{"type":"event","method":"log.entryAdded","params":{}}
```

The W3C Working Draft currently defines core modules such as `session`,
`browser`, `browsingContext`, `emulation`, `network`, `script`, `storage`,
`log`, `input`, and `webExtension`. MDN and browser projects may document
additional or evolving modules. Verify current browser support before relying
on one module in final evidence.

## Starting a BiDi Session

The common route is:

1. Start a WebDriver-compatible driver or Selenium Grid.
2. Create a WebDriver session with `webSocketUrl` set to `true`.
3. Read `capabilities.webSocketUrl` from the new-session response.
4. Connect a WebSocket client to that URL.
5. Subscribe to events or send BiDi commands.
6. End the session and close the WebSocket.

Generic WebDriver new-session request:

```json
{
  "capabilities": {
    "alwaysMatch": {
      "webSocketUrl": true
    }
  }
}
```

Browser-specific example:

```json
{
  "capabilities": {
    "alwaysMatch": {
      "browserName": "firefox",
      "webSocketUrl": true,
      "acceptInsecureCerts": false
    }
  }
}
```

The response should include a string WebSocket URL in the returned
capabilities:

```json
{
  "value": {
    "sessionId": "SESSION_ID",
    "capabilities": {
      "browserName": "firefox",
      "browserVersion": "VERSION",
      "platformName": "PLATFORM",
      "webSocketUrl": "ws://127.0.0.1:4444/session/SESSION_ID"
    }
  }
}
```

Some implementations also support BiDi-only sessions where `session.new` is
sent over an out-of-band WebSocket endpoint. For DAST evidence, prefer the
ordinary WebDriver new-session path unless the test environment explicitly
uses a BiDi-only endpoint.

Record:

- Driver command line and logs.
- Browser executable path, version, and profile directory.
- Full new-session request and response.
- Returned `sessionId` and `webSocketUrl`.
- Whether the session is local driver, Selenium Grid, cloud provider, or
  browser-specific remote endpoint.

## Raw WebSocket Frames

Use a raw WebSocket client when debugging protocol support, client-library
behavior, or event ordering.

Minimal Python pattern:

```python
import asyncio
import json
import websockets

BIDI_URL = "ws://127.0.0.1:4444/session/SESSION_ID"

async def main():
    async with websockets.connect(BIDI_URL) as ws:
        await ws.send(json.dumps({
            "id": 1,
            "method": "session.status",
            "params": {}
        }))
        print(await ws.recv())

asyncio.run(main())
```

Send commands with monotonically increasing IDs:

```json
{"id":1,"method":"session.status","params":{}}
{"id":2,"method":"browsingContext.getTree","params":{}}
```

Handle every incoming message by `type`:

- `success`: match `id`, store `result`.
- `error`: match `id`, store `error`, `message`, and optional `stacktrace`.
- `event`: dispatch by `method`.

Keep raw frames in evidence when investigating protocol behavior. Client
libraries can hide event ordering, implicit subscriptions, default contexts,
and automatic cleanup.

## Session Subscriptions

Most event streams require `session.subscribe`.

Subscribe globally:

```json
{
  "id": 20,
  "method": "session.subscribe",
  "params": {
    "events": [
      "log.entryAdded",
      "browsingContext.navigationStarted",
      "browsingContext.load",
      "network.beforeRequestSent",
      "network.responseCompleted"
    ]
  }
}
```

Subscribe to a specific context:

```json
{
  "id": 21,
  "method": "session.subscribe",
  "params": {
    "events": ["log.entryAdded"],
    "contexts": ["CONTEXT_ID"]
  }
}
```

Subscribe by user context when supported:

```json
{
  "id": 22,
  "method": "session.subscribe",
  "params": {
    "events": ["network.beforeRequestSent"],
    "userContexts": ["USER_CONTEXT_ID"]
  }
}
```

Unsubscribe by subscription ID returned from `session.subscribe`, or by event
attributes if the implementation supports that form:

```json
{"id":23,"method":"session.unsubscribe","params":{"subscriptions":["SUBSCRIPTION_ID"]}}
{"id":24,"method":"session.unsubscribe","params":{"events":["log.entryAdded"]}}
```

Record the subscription command, returned subscription IDs, context filters,
user-context filters, and unsubscribe commands. Missing events are often caused
by subscribing too late or subscribing to the wrong context.

## Browsing Contexts and Navigation

Use `browsingContext.getTree` to map tabs, windows, frames, and context IDs:

```json
{"id":30,"method":"browsingContext.getTree","params":{}}
```

Create a tab or window:

```json
{
  "id": 31,
  "method": "browsingContext.create",
  "params": {
    "type": "tab"
  }
}
```

Navigate:

```json
{
  "id": 32,
  "method": "browsingContext.navigate",
  "params": {
    "context": "CONTEXT_ID",
    "url": "https://example.test/",
    "wait": "complete"
  }
}
```

Reload:

```json
{
  "id": 33,
  "method": "browsingContext.reload",
  "params": {
    "context": "CONTEXT_ID",
    "wait": "interactive"
  }
}
```

Capture a screenshot:

```json
{
  "id": 34,
  "method": "browsingContext.captureScreenshot",
  "params": {
    "context": "CONTEXT_ID"
  }
}
```

Relevant events:

```text
browsingContext.contextCreated
browsingContext.contextDestroyed
browsingContext.navigationStarted
browsingContext.navigationCommitted
browsingContext.domContentLoaded
browsingContext.load
browsingContext.navigationFailed
browsingContext.navigationAborted
browsingContext.userPromptOpened
browsingContext.userPromptClosed
browsingContext.downloadWillBegin
browsingContext.downloadEnd
```

Record context IDs and URLs together. A top-level context, child frame context,
user context, and client window are different identifiers.

## Logs and JavaScript Exceptions

Subscribe:

```json
{
  "id": 40,
  "method": "session.subscribe",
  "params": {
    "events": ["log.entryAdded"],
    "contexts": ["CONTEXT_ID"]
  }
}
```

Trigger and capture console output:

```json
{
  "id": 41,
  "method": "script.evaluate",
  "params": {
    "expression": "console.log('bidi-log-probe')",
    "target": {"context":"CONTEXT_ID"},
    "awaitPromise": true,
    "resultOwnership": "none"
  }
}
```

`log.entryAdded` is useful for:

- Console API calls.
- Unhandled JavaScript exceptions.
- Log level, text, timestamp, source, and stack details where provided.

Do not rely only on browser console text for exploit or impact claims. Pair log
events with the triggering navigation, input, request, screenshot, and script
or page state that produced them.

## Script Evaluation and Realms

Get realms:

```json
{
  "id": 50,
  "method": "script.getRealms",
  "params": {
    "context": "CONTEXT_ID"
  }
}
```

Evaluate a simple expression:

```json
{
  "id": 51,
  "method": "script.evaluate",
  "params": {
    "expression": "document.location.href",
    "target": {"context":"CONTEXT_ID"},
    "awaitPromise": true,
    "resultOwnership": "none"
  }
}
```

Call a function with arguments:

```json
{
  "id": 52,
  "method": "script.callFunction",
  "params": {
    "functionDeclaration": "(selector) => document.querySelector(selector)?.textContent",
    "target": {"context":"CONTEXT_ID"},
    "arguments": [
      {"type":"string","value":"h1"}
    ],
    "awaitPromise": true,
    "resultOwnership": "none"
  }
}
```

Add a preload script:

```json
{
  "id": 53,
  "method": "script.addPreloadScript",
  "params": {
    "functionDeclaration": "() => { window.__maxtacLoaded = Date.now(); }",
    "contexts": ["CONTEXT_ID"]
  }
}
```

Remove a preload script:

```json
{
  "id": 54,
  "method": "script.removePreloadScript",
  "params": {
    "script": "PRELOAD_SCRIPT_ID"
  }
}
```

Use `resultOwnership` carefully:

- `none`: serialized value only; less cleanup risk.
- `root`: remote handles may remain until disowned.

Disown handles when the session uses remote object handles:

```json
{
  "id": 55,
  "method": "script.disown",
  "params": {
    "target": {"context":"CONTEXT_ID"},
    "handles": ["HANDLE_ID"]
  }
}
```

Script evaluation changes target state if the expression has side effects.
Separate passive reads from setup actions and record every preload script and
script command.

## Network Events and Intercepts

Subscribe to passive network events:

```json
{
  "id": 60,
  "method": "session.subscribe",
  "params": {
    "events": [
      "network.beforeRequestSent",
      "network.responseStarted",
      "network.responseCompleted",
      "network.fetchError",
      "network.authRequired"
    ],
    "contexts": ["CONTEXT_ID"]
  }
}
```

Common network events:

```text
network.beforeRequestSent
network.responseStarted
network.responseCompleted
network.fetchError
network.authRequired
```

Create an intercept only for controlled experiments:

```json
{
  "id": 61,
  "method": "network.addIntercept",
  "params": {
    "phases": ["beforeRequestSent"],
    "contexts": ["CONTEXT_ID"],
    "urlPatterns": [
      {"type":"string","pattern":"https://example.test/api/*"}
    ]
  }
}
```

Continue a blocked request unchanged:

```json
{
  "id": 62,
  "method": "network.continueRequest",
  "params": {
    "request": "REQUEST_ID"
  }
}
```

Remove an intercept:

```json
{
  "id": 63,
  "method": "network.removeIntercept",
  "params": {
    "intercept": "INTERCEPT_ID"
  }
}
```

Collect request or response data when the implementation supports collectors:

```json
{
  "id": 64,
  "method": "network.addDataCollector",
  "params": {
    "dataTypes": ["response"],
    "maxEncodedDataSize": 1048576,
    "contexts": ["CONTEXT_ID"]
  }
}
```

Retrieve collected data:

```json
{
  "id": 65,
  "method": "network.getData",
  "params": {
    "dataType": "response",
    "collector": "COLLECTOR_ID",
    "request": "REQUEST_ID",
    "disown": true
  }
}
```

Network interception is state-changing. It can change request timing, headers,
cache behavior, body availability, authentication flow, redirects, service
worker behavior, and server-side logs. For final evidence, prefer passive
events unless mutation is the point of the experiment.

## Storage, Cookies, and User Contexts

List user contexts:

```json
{"id":70,"method":"browser.getUserContexts","params":{}}
```

Create an isolated user context:

```json
{
  "id": 71,
  "method": "browser.createUserContext",
  "params": {}
}
```

Create a tab in that user context:

```json
{
  "id": 72,
  "method": "browsingContext.create",
  "params": {
    "type": "tab",
    "userContext": "USER_CONTEXT_ID"
  }
}
```

Read cookies:

```json
{
  "id": 73,
  "method": "storage.getCookies",
  "params": {}
}
```

Set a cookie:

```json
{
  "id": 74,
  "method": "storage.setCookie",
  "params": {
    "cookie": {
      "name": "case",
      "value": {"type":"string","value":"1"},
      "domain": "example.test",
      "path": "/"
    }
  }
}
```

Delete cookies:

```json
{
  "id": 75,
  "method": "storage.deleteCookies",
  "params": {
    "filter": {"domain":"example.test"}
  }
}
```

Remove an isolated user context when finished:

```json
{
  "id": 76,
  "method": "browser.removeUserContext",
  "params": {
    "userContext": "USER_CONTEXT_ID"
  }
}
```

Storage state is high-impact. Record profile path, user context, cookie
partition details, origin, and cleanup commands for every storage mutation.

## Input, Files, Downloads, and Emulation

Perform input actions:

```json
{
  "id": 80,
  "method": "input.performActions",
  "params": {
    "context": "CONTEXT_ID",
    "actions": []
  }
}
```

Release input state:

```json
{
  "id": 81,
  "method": "input.releaseActions",
  "params": {
    "context": "CONTEXT_ID"
  }
}
```

Set files for a file input:

```json
{
  "id": 82,
  "method": "input.setFiles",
  "params": {
    "context": "CONTEXT_ID",
    "element": {"sharedId":"SHARED_NODE_ID"},
    "files": ["/absolute/path/to/file.txt"]
  }
}
```

Configure downloads where supported:

```json
{
  "id": 83,
  "method": "browser.setDownloadBehavior",
  "params": {
    "downloadBehavior": {
      "type": "allowed",
      "destinationFolder": "/absolute/path/to/downloads"
    }
  }
}
```

Use emulation commands only when the test requires them:

```json
{"id":84,"method":"emulation.setGeolocationOverride","params":{"coordinates":{"latitude":37.7749,"longitude":-122.4194,"accuracy":10}}}
{"id":85,"method":"emulation.setUserAgentOverride","params":{"userAgent":"TestAgent/1.0"}}
{"id":86,"method":"emulation.setLocaleOverride","params":{"locale":"en-US"}}
{"id":87,"method":"emulation.setTimezoneOverride","params":{"timezone":"America/New_York"}}
```

Input, downloads, and emulation change visible browser behavior. Capture
screenshots, event logs, and cleanup state after using them.

## Selenium and WebdriverIO Clients

Selenium exposes BiDi APIs and can enable the underlying WebSocket URL through
browser options.

Selenium examples by language use forms such as:

```text
options.setCapability("webSocketUrl", true)
options.enable_bidi = True
UseWebSocketUrl = true
options.web_socket_url = true
Options().enableBidi()
```

Use Selenium BiDi APIs for normal automation when they expose the needed
module. Drop to raw WebSocket only when:

- You need a command not wrapped by the binding.
- You are debugging event ordering or protocol support.
- You need to capture raw frames as evidence.
- A client abstraction is hiding subscriptions or cleanup.

WebdriverIO exposes WebDriver BiDi protocol commands based on the living spec
when `webSocketUrl: true` is set in capabilities.

Record client-library version and generated protocol version when using a
wrapper. Client APIs can lag or lead browser support.

## Evidence Automation

Create a run directory:

```text
RUN_DIR="evidence/$(date +%Y%m%d-%H%M%S)-webdriver-bidi"
mkdir -p "$RUN_DIR"
```

Record driver and browser versions:

```text
chromedriver --version > "$RUN_DIR/chromedriver-version.txt" 2>&1
geckodriver --version > "$RUN_DIR/geckodriver-version.txt" 2>&1
google-chrome --version > "$RUN_DIR/chrome-version.txt" 2>&1
firefox --version > "$RUN_DIR/firefox-version.txt" 2>&1
```

Save the new-session request:

```json
{
  "capabilities": {
    "alwaysMatch": {
      "browserName": "firefox",
      "webSocketUrl": true,
      "acceptInsecureCerts": false
    }
  }
}
```

Save all raw BiDi frames as JSON Lines:

```json
{"direction":"send","frame":{"id":1,"method":"session.status","params":{}}}
{"direction":"recv","frame":{"type":"success","id":1,"result":{"ready":true,"message":""}}}
{"direction":"recv","frame":{"type":"event","method":"log.entryAdded","params":{}}}
```

Minimum useful capture:

```json
{"id":1,"method":"session.status","params":{}}
{"id":2,"method":"browsingContext.getTree","params":{}}
{"id":3,"method":"session.subscribe","params":{"events":["log.entryAdded","browsingContext.load","network.beforeRequestSent","network.responseCompleted"]}}
{"id":4,"method":"browsingContext.navigate","params":{"context":"CONTEXT_ID","url":"https://target.example/","wait":"complete"}}
{"id":5,"method":"script.evaluate","params":{"expression":"document.documentElement.outerHTML.length","target":{"context":"CONTEXT_ID"},"awaitPromise":true,"resultOwnership":"none"}}
```

Capture artifacts:

- Driver logs.
- Browser logs if separate from BiDi logs.
- WebDriver new-session request and response.
- BiDi raw frames.
- Context tree before and after navigation.
- Screenshots after important state changes.
- HAR-like request/response summaries built from network events.
- Download files and paths when downloads are in scope.
- Profile directory or user context ID when storage is in scope.

End cleanly:

```json
{"id":90,"method":"session.unsubscribe","params":{"events":["log.entryAdded","network.beforeRequestSent","network.responseCompleted"]}}
{"id":91,"method":"session.end","params":{}}
```

Then close the WebSocket and stop the driver.

## Failure Modes

No `webSocketUrl` in returned capabilities

- The browser or driver may not support WebDriver BiDi for that version.
- The client did not request `webSocketUrl: true`.
- Selenium Grid or a cloud provider may have stripped the capability.
- Preserve the new-session request and response.

WebSocket connects but commands fail

- Confirm the URL belongs to the same active session.
- Send `session.status` first.
- Check command names against the W3C spec and MDN reference.
- Check whether the module is implemented by that browser version.
- Preserve `error`, `message`, and `stacktrace`.

Events never arrive

- Confirm `session.subscribe` succeeded.
- Subscribe before navigation or before triggering the action.
- Check `contexts` and `userContexts` filters.
- Confirm the target event name is supported.
- Log every incoming frame, not only frames your client recognizes.

Network events are incomplete

- Browser support may not include all network commands or data collection.
- Service workers, cache, redirects, authentication, and CORS can change event
  sequences.
- Subscribe before navigation.
- Record cache, profile, user context, and network intercept state.

Script evaluation returns handles or huge objects

- Use `resultOwnership: "none"` for passive evidence.
- Set serialization limits where needed.
- Disown handles created with root ownership.
- Prefer small explicit expressions over dumping entire DOM objects.

Context IDs change unexpectedly

- Navigations, popups, frames, reloads, and crashes can create or destroy
  browsing contexts.
- Refresh `browsingContext.getTree`.
- Subscribe to `contextCreated` and `contextDestroyed`.

Browser behavior differs under automation

- WebDriver launch arguments, profile path, user context, permissions,
  downloads, certificate settings, cache, window state, and emulation can
  change target behavior.
- Reproduce outside automation or with fewer mutations before making final
  target-behavior claims.

Command responses appear out of order

- This is allowed by the protocol.
- Match every response by `id`.
- Avoid clients that assume FIFO command completion.

## Evidence Checklist

Collect:

- W3C spec version or URL consulted, MDN module pages consulted, and client
  library documentation version.
- Browser name, browser version, driver name, driver version, Selenium/Grid
  version, and client-library version.
- Driver command line, driver logs, browser profile path, and environment.
- WebDriver new-session request and full response, including capabilities.
- `sessionId` and `capabilities.webSocketUrl`.
- Raw WebSocket frames with send/receive direction and timestamps.
- `session.status`, `browsingContext.getTree`, and subscription results.
- Context IDs, user context IDs, URLs, frame tree, and navigation IDs.
- Subscribed events, context filters, user-context filters, and unsubscribe
  commands.
- Network event sequence, request IDs, response IDs, redirect chain, headers
  captured, body collector settings, and any intercept commands.
- Script commands, preload scripts, result ownership, handles, disown commands,
  and script exception details.
- Storage and cookie commands, partition/user context details, and cleanup.
- Input actions, file paths, download behavior, emulation settings, and
  screenshots after state changes.
- Every state-changing operation before final evidence capture.

## References

- https://www.w3.org/TR/webdriver-bidi/
- https://w3c.github.io/webdriver-bidi/
- https://github.com/w3c/webdriver-bidi
- https://wpt.fyi/results/webdriver/tests/bidi
- https://developer.mozilla.org/en-US/docs/Web/WebDriver/Reference/BiDi
- https://developer.mozilla.org/en-US/docs/Web/WebDriver/Reference/BiDi/Modules
- https://www.selenium.dev/documentation/webdriver/bidi/
- https://www.selenium.dev/documentation/webdriver/bidi/w3c/browsing_context/
- https://www.selenium.dev/documentation/webdriver/bidi/w3c/log/
- https://www.selenium.dev/documentation/webdriver/bidi/w3c/network/
- https://www.selenium.dev/documentation/webdriver/bidi/w3c/script/
- https://webdriver.io/docs/api/webdriverBidi/
- https://firefox-source-docs.mozilla.org/remote/index.html
- https://firefox-source-docs.mozilla.org/testing/geckodriver/index.html
- https://github.com/GoogleChromeLabs/chromium-bidi
