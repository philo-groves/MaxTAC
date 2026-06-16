# WebKit Debugging

Use WebKit debugging for Safari, Safari Technology Preview, iOS Safari,
iPadOS Safari, Home Screen web apps, app-hosted `WKWebView`, app-hosted
`JSContext`, and WebKitGTK/WPE targets. Prefer it when the behavior under test
depends on WebKit or Safari-specific implementation details, Apple platform
browser behavior, or a WebKit embedder.

Prefer WebDriver BiDi when the task needs a standard cross-browser automation
protocol and the target browser supports the required module. Prefer Chrome
DevTools Protocol for Chromium-only debugging. Prefer `lldb` or Xcode when the
task is WebKit engine source debugging rather than web-content inspection.

Prefer Apple Safari Developer Tools documentation, WebKit Web Inspector
reference pages, WebKit source-debugging documentation, installed Safari or
Safari Technology Preview behavior, and WebKitGTK/WPE reference documentation
for exact setup steps. Safari, Safari Technology Preview, iOS, iPadOS, macOS,
WebKitGTK, WPE WebKit, app signing, and inspectability settings can differ by
version.

Treat Web Inspector as mutable execution. It can change page state through
JavaScript evaluation, breakpoints, DOM and CSS edits, Inspector Bootstrap
Script, Local Overrides, user-agent and device settings, storage edits,
cookies, timeline profiling, source-map loading, network inspection, and
debugger pause/resume. Keep final evidence separate from observations that only
happen because inspection changed timing, script state, cache behavior, user
activation, origin state, or target connection state.

## Contents

- [Quick Commands](#quick-commands)
- [Tool Choice](#tool-choice)
- [Enable Web Inspector on macOS](#enable-web-inspector-on-macos)
- [Inspect iOS, iPadOS, and Simulators](#inspect-ios-ipados-and-simulators)
- [Inspect App Web Content](#inspect-app-web-content)
- [Web Inspector Workflow](#web-inspector-workflow)
- [Elements, DOM, CSS, and Layers](#elements-dom-css-and-layers)
- [Console, JavaScript, and Exceptions](#console-javascript-and-exceptions)
- [Sources, Breakpoints, and Bootstrap Scripts](#sources-breakpoints-and-bootstrap-scripts)
- [Network, URL Breakpoints, and Local Overrides](#network-url-breakpoints-and-local-overrides)
- [Storage, Cookies, and Device Settings](#storage-cookies-and-device-settings)
- [Timelines, Performance, and Memory](#timelines-performance-and-memory)
- [Screenshots, Exports, and Evidence](#screenshots-exports-and-evidence)
- [WebKitGTK and WPE Remote Inspector](#webkitgtk-and-wpe-remote-inspector)
- [WebKit Source and Process Debugging](#webkit-source-and-process-debugging)
- [Automation Boundaries](#automation-boundaries)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Open Safari or Safari Technology Preview:

```text
open -a Safari
open -a "Safari Technology Preview"
```

Open a URL in Safari:

```text
open -a Safari "https://example.test/"
```

Enable Safari's internal Debug menu only for WebKit engine debugging:

```text
defaults write com.apple.Safari IncludeInternalDebugMenu 1
defaults read com.apple.Safari IncludeInternalDebugMenu
```

Use iOS Simulator with Safari:

```text
xcrun simctl list devices available
xcrun simctl boot "$SIMULATOR_ID"
xcrun simctl openurl booted "https://example.test/"
```

Attach LLDB to MobileSafari in the iOS Simulator:

```text
xcrun --sdk iphonesimulator lldb --attach-name MobileSafari
xcrun --sdk iphonesimulator lldb --attach-name MobileSafari --wait-for
```

Attach LLDB to the WebKit WebContent process in the iOS Simulator:

```text
xcrun --sdk iphonesimulator lldb --attach-name com.apple.WebKit.WebContent.Development
xcrun --sdk iphonesimulator lldb --attach-name com.apple.WebKit.WebContent.Development --wait-for
```

Start a WPE WebKit remote inspector server:

```text
export WEBKIT_INSPECTOR_SERVER=127.0.0.1:5000
MiniBrowser --enable-developer-extras=true https://example.test/
```

Connect a WebKitGTK MiniBrowser client to a WPE remote inspector:

```text
MiniBrowser inspector://127.0.0.1:5000
```

Record:

```text
macOS version
Safari or Safari Technology Preview version
iOS or iPadOS version
Device or simulator model
Target URL
Target type: Safari page, Home Screen web app, SFSafariViewController, WKWebView, JSContext, WebKitGTK, or WPE WebKit
Whether Web Inspector was already open before navigation
Any Inspector settings, device settings, Local Overrides, bootstrap scripts, or breakpoints
```

## Tool Choice

Use Safari Web Inspector for:

- Safari and Safari Technology Preview web pages.
- iOS and iPadOS Safari pages inspected from a connected Mac.
- iOS and iPadOS simulators.
- Home Screen web apps.
- Developer-enabled `WKWebView` content.
- Developer-enabled `JSContext` JavaScript.
- WebKit-specific layout, rendering, network, storage, JavaScript, and
  performance evidence.

Use WebKitGTK or WPE Web Inspector for:

- Linux WebKit embedders.
- Embedded WebKit environments.
- Headless or device-hosted WPE targets that expose a remote inspector.

Use `lldb` or Xcode for:

- WebKit engine process debugging.
- Crashes in `WebProcess`, `NetworkProcess`, or `StorageProcess`.
- Native stack, symbol, and source-level debugging.
- Issues that require process attachment instead of Web Inspector.

Use WebDriver BiDi or WebDriver when:

- The work requires repeatable browser automation.
- The evidence should be comparable across browsers.
- Safari automation through `safaridriver` is sufficient.

Use Chrome DevTools Protocol only for Chromium targets. CDP and WebKit Web
Inspector are not interchangeable evidence sources.

## Enable Web Inspector on macOS

Enable Safari developer features:

1. Open Safari or Safari Technology Preview.
2. Open `Safari > Settings`.
3. Open the `Advanced` pane.
4. Enable `Show features for web developers`.
5. Use the `Develop` menu to open Web Inspector.

Open Web Inspector for the frontmost Safari page:

```text
Develop > Show Web Inspector
Right-click page > Inspect Element
Option-Command-I
```

Record whether Safari or Safari Technology Preview was used. Safari
Technology Preview may expose newer Web Inspector behavior than the stable
Safari release.

The `Develop` menu is also the entry point for connected devices, simulators,
Mac web apps, app-hosted web content, JavaScript contexts, and some WebKit
developer settings.

## Inspect iOS, iPadOS, and Simulators

Enable remote inspection on a physical iOS or iPadOS device:

1. Open Settings on the device.
2. On newer iOS versions, go to `Apps > Safari > Advanced`.
3. On older iOS versions, go to `Safari > Advanced`.
4. Enable `Web Inspector`.
5. Connect the device to a Mac with a cable or through Xcode wireless
   debugging.
6. Enable Web Inspector on the Mac Safari instance too.
7. Open Safari on the Mac.
8. Use `Develop > DEVICE_NAME > TARGET` to inspect the page or app content.

Physical-device targets can include:

```text
Safari pages
Home Screen web apps
Inspectable SFSafariViewController content
Inspectable WKWebView content
Inspectable JSContext content
```

iOS Simulator inspection is available from the Mac Safari `Develop` menu
without enabling the Web Inspector toggle inside the simulator.

Open a URL in the booted simulator:

```text
xcrun simctl openurl booted "https://example.test/"
```

Use simulator targets when:

- The target behavior is reproducible in the simulator.
- The test requires repeatable device state.
- Physical-device pairing, trust, or cable state is noisy.

Use physical devices when:

- The issue depends on hardware, camera, sensors, cellular networking, memory,
  GPU behavior, device performance, installed apps, or a real device profile.

Record:

```text
Device identifier or simulator identifier
Device model
iOS or iPadOS version
Safari version when visible
Connection type: cable or wireless debugging
Page URL or app name shown in the Develop menu
Whether the page was open before Web Inspector attached
```

## Inspect App Web Content

For app-hosted web content, inspectability depends on app type, signing,
platform version, and app code.

Current Apple and WebKit documentation describe an explicit inspectability API
for `WKWebView` and `JSContext`. The property defaults to disabled and can be
enabled per instance by the app.

Swift `WKWebView` pattern:

```swift
let configuration = WKWebViewConfiguration()
let webView = WKWebView(frame: .zero, configuration: configuration)

if #available(iOS 16.4, macOS 13.4, tvOS 16.4, *) {
    webView.isInspectable = true
}
```

Objective-C `WKWebView` pattern:

```objective-c
WKWebViewConfiguration *configuration = [WKWebViewConfiguration new];
WKWebView *webView = [[WKWebView alloc] initWithFrame:CGRectZero configuration:configuration];

if (@available(iOS 16.4, macOS 13.4, tvOS 16.4, *)) {
    webView.inspectable = YES;
}
```

Swift `JSContext` pattern:

```swift
let context = JSContext()

if #available(iOS 16.4, macOS 13.4, tvOS 16.4, *) {
    context?.isInspectable = true
}
```

C JavaScriptCore pattern:

```c
JSGlobalContextRef context = JSGlobalContextCreate(NULL);
JSGlobalContextSetInspectable(context, true);
```

Only add app-code snippets to a target application when you own the app, have
permission to change the app, or are working in a local development build. For
third-party apps, record whether inspectability is available instead of
modifying app behavior.

When app content appears in the Safari `Develop` menu, record:

```text
App name
Bundle identifier when known
Target type: WKWebView, JSContext, SFSafariViewController, or web extension context
Platform and OS version
Whether app build is development, TestFlight, enterprise, or release
Where inspectability was enabled
```

If app content does not appear, first determine whether the app has opted into
inspection and whether the device and Mac are configured correctly.

## Web Inspector Workflow

Use Web Inspector as an evidence collection surface:

1. Start from a fresh browser profile, simulator, or device state when
   practical.
2. Record the exact target and environment.
3. Open Web Inspector before navigation if early console, network, or source
   events matter.
4. Collect passive observations first.
5. Apply state-changing tools only when the test requires them.
6. Capture screenshots, exports, and logs immediately after each important
   observation.
7. Record cleanup steps.

Core Web Inspector tabs include:

```text
Elements
Console
Sources
Network
Timelines
Storage
Graphics
Layers
Audit
```

Do not assume all tabs or features appear for every target. A Safari page,
remote iOS page, `WKWebView`, `JSContext`, service worker, WebKitGTK view, and
WPE target can expose different inspection surfaces.

Record whether Web Inspector was:

```text
Docked
Undocked
Attached to a local Safari page
Attached to a remote iOS or iPadOS target
Attached to an app web view
Attached to a JavaScript context
Attached to WebKitGTK or WPE
```

## Elements, DOM, CSS, and Layers

Use the `Elements` tab to inspect the DOM and CSS state as WebKit sees it.

Collect:

```text
Selected node path
DOM tree excerpt
Rendered text
Attributes
Computed styles
Matched rules
Box model
Event listeners when relevant
Accessibility details when relevant
Screenshots before and after edits
```

DOM and CSS edits in Web Inspector are state-changing. Record every live edit
and reload the page from a known state before final evidence.

Use `Layers` when compositing, z-order, repaint, or unexpected memory use is
part of the issue. Record:

```text
Layer tree
Selected layer
Compositing reason when available
Screenshot
Viewport size
Device pixel ratio
Remote-device orientation
```

When inspecting remote iOS targets, remember that some settings are per-page
device settings inside Web Inspector rather than global Safari `Develop` menu
settings.

## Console, JavaScript, and Exceptions

Use the `Console` tab for:

```text
console output
JavaScript errors
warnings
interactive JavaScript evaluation
saved console results
stack traces
WebRTC and media logs when enabled
```

Open Web Inspector before reproducing the behavior when console history
matters.

Console evaluation is state-changing. Treat any expression that reads mutable
state carefully, and treat any expression that writes state as setup rather
than passive evidence.

Useful console-side capture notes:

```text
Preserve message text
Preserve severity
Preserve timestamp when available
Preserve source URL and line or column
Preserve stack trace
Preserve selected execution context
Preserve any evaluated expression
```

Prefer explicit, passive expressions for evidence:

```javascript
location.href
document.readyState
document.title
navigator.userAgent
```

Avoid mixing console experiments with final observations. If a console command
changes state, reload or reset before collecting final evidence.

## Sources, Breakpoints, and Bootstrap Scripts

Use the `Sources` tab for:

```text
resource inspection
pretty printing
request and response data views
JavaScript debugging
breakpoints
source maps
console snippets
Inspector Bootstrap Script
Inspector Style Sheet
Local Overrides
```

Use breakpoints to understand control flow, but record that paused execution
changes timing. Pause state can affect timers, network callbacks, UI events,
animation frames, and event order.

Common breakpoint types:

```text
JavaScript line breakpoint
DOM breakpoint
Event breakpoint
URL breakpoint
Symbolic breakpoint
Exception pause
```

Record for each breakpoint:

```text
Type
Source URL or resource
Line and column when available
Condition
Ignore count
Action
Whether it auto-continues
Hit count
Pause reason
Call stack
Resume time
```

Use `Inspector Bootstrap Script` only when early JavaScript setup is required.
It runs before other JavaScript in new global objects while Web Inspector is
open. Because it changes the inspected environment, record:

```text
Full bootstrap script
Creation time
Target scope
Whether it was enabled before navigation
Observed effects
Removal or disable step
```

Use console snippets for repeated local helper code. Record snippet names and
contents if their results are part of evidence.

## Network, URL Breakpoints, and Local Overrides

Use the `Network` tab to inspect page resource loading and API-driven requests.
WebKit documentation describes it as showing resources requested after Web
Inspector is opened, including web resources and API-driven requests such as
XHR, `fetch`, WebSocket, and beacon traffic.

Collect:

```text
URL
Domain
Method
Scheme
Status
Protocol
MIME type
Initiator
Priority when visible
IP address when visible
Connection ID when visible
Transfer size
Resource size
Timing
Request headers
Response headers
Request data when visible
Response body when visible
Redirect count
Load time
```

Open Web Inspector before navigation when complete network evidence matters.
Network entries can be absent if they happened before Web Inspector was open or
if the target changed before capture.

Use URL breakpoints for JavaScript-initiated requests when the goal is to
observe the script location that initiates a request. URL breakpoints can pause
JavaScript before requests initiated by APIs such as `XMLHttpRequest` or
`fetch`.

Record URL breakpoint details:

```text
Containing or matching mode
Configured text or regular expression
Special All Requests mode when used
Condition
Ignore count
Action
Whether auto-continue is enabled
Call stack at pause
```

Use Local Overrides only for controlled experiments. Local Overrides can
replace request or response content and headers while Web Inspector is open.
They can persist across Web Inspector sessions and can affect later page loads.

For every Local Override, record:

```text
Override type: request or response
Configured URL or regular expression
Replacement file or inline content
Headers
Redirect URL when present
Skip Network setting when present
Whether the override matched
Exported override file
Disable or removal step
```

For final evidence, prefer passive Network observations unless the point of
the experiment is to show how the page behaves under a specific local override
or breakpoint condition.

## Storage, Cookies, and Device Settings

Use the `Storage` tab to inspect:

```text
cookies
local storage
session storage
IndexedDB
Cache storage
application cache where present
databases where present
```

Storage edits are state-changing. Record:

```text
Origin
Storage type
Key
Value or value hash
Cookie attributes
Before and after screenshots or exports
Deletion or cleanup step
```

For remote iOS and iPadOS targets, Web Inspector exposes per-page device
settings for some actions that would otherwise be global in the Safari
`Develop` menu. WebKit documentation notes that these settings are not
preserved between Web Inspector sessions, and they are preserved across
navigations only while Web Inspector remains connected.

Record device settings:

```text
User agent
Images setting
Styles setting
JavaScript setting
Site-specific compatibility setting
Cross-origin restrictions setting
ITP debug mode
Ad attribution debug mode
WebRTC toggles
Any reload triggered by a setting change
```

User-agent changes can reload the inspected page. Treat them as setup, not as
passive evidence.

## Timelines, Performance, and Memory

Use the `Timelines` tab for performance profiling and introspection. WebKit
documentation describes timelines for screenshots, network requests, layout
and rendering, media and animations, JavaScript and events, CPU, memory, and
JavaScript allocations.

Timeline recording can affect timing and can disable or change some debugging
features while recording. Capture passive observations first when timing is
important.

Collect:

```text
Recording start time
Recording end time
Selected time range
Timeline categories enabled
Page URL
Viewport and device orientation
Load and DOMContentLoaded markers
Network activity
Layout and rendering activity
JavaScript and event activity
CPU timeline
Memory timeline
Screenshots timeline when enabled
Exported timeline recording
```

Timeline exports can be imported later. Preserve exported recordings alongside
screenshots and written notes.

Use memory and allocation timelines carefully. WebKit documentation notes that
some memory-related timelines can affect page performance during recording.

## Screenshots, Exports, and Evidence

Use visual evidence whenever behavior is user-visible:

```text
Full-window screenshot
Element-focused screenshot
Remote-device screenshot
Network tab screenshot
Console screenshot
Sources paused-state screenshot
Storage screenshot
Timeline export
Local Override export
```

For each screenshot or export, record:

```text
Timestamp
Target URL
Target type
Device or simulator
Orientation
Viewport size
Device scale factor when known
Inspector tab
Selected node, resource, request, breakpoint, or storage item
State-changing settings active at capture time
```

Use built-in Web Inspector export flows where available, such as timeline
export or Local Override export. For network data and storage data, preserve
both the visible UI capture and any exported or copied structured data.

Keep one run log that connects each observation to the relevant screenshot,
export, console note, network request, or debugger event.

## WebKitGTK and WPE Remote Inspector

Use WebKitGTK and WPE documentation for Linux and embedded WebKit targets.
These environments are not configured through Safari's `Develop` menu.

For WebKitGTK `WebKitWebView`, the inspector is available only when developer
extras are enabled in `WebKitSettings`.

C WebKitGTK pattern:

```c
WebKitSettings *settings = webkit_web_view_get_settings(WEBKIT_WEB_VIEW(web_view));
g_object_set(G_OBJECT(settings), "enable-developer-extras", TRUE, NULL);

WebKitWebInspector *inspector = webkit_web_view_get_inspector(WEBKIT_WEB_VIEW(web_view));
webkit_web_inspector_show(WEBKIT_WEB_INSPECTOR(inspector));
```

For WPE WebKit remote inspection, set the inspector server environment
variable and enable developer extras in the target application:

```text
export WEBKIT_INSPECTOR_SERVER=127.0.0.1:5000
MiniBrowser --enable-developer-extras=true https://example.test/
```

Connect from a WebKitGTK browser:

```text
MiniBrowser inspector://127.0.0.1:5000
```

Some WPE builds can expose an HTTP inspector server:

```text
export WEBKIT_INSPECTOR_HTTP_SERVER=127.0.0.1:5000
```

Record:

```text
WebKitGTK or WPE version
Application or MiniBrowser command line
Developer-extras setting
Inspector server address and port
Client browser used for inspection
Target URL
Network path between client and target
```

Bind remote inspector servers to loopback unless the lab explicitly requires a
remote interface. If a remote interface is required, record the network
boundary and firewall state.

## WebKit Source and Process Debugging

Use this section when the task is native WebKit engine debugging, not normal
web-content inspection.

WebKit documentation calls out important process boundaries:

```text
WebProcess: page engine process
NetworkProcess: networking process
StorageProcess: IndexedDB and service worker storage process
UIProcess: browser or embedder process
```

Attach to the process that owns the behavior under test. A page issue may
require the WebContent process. A networking issue may require the
NetworkProcess. A storage or service worker issue may require StorageProcess.

iOS Simulator examples:

```text
xcrun --sdk iphonesimulator lldb --attach-name MobileSafari
xcrun --sdk iphonesimulator lldb --attach-name MobileSafari --wait-for
xcrun --sdk iphonesimulator lldb --attach-name com.apple.WebKit.WebContent.Development
xcrun --sdk iphonesimulator lldb --attach-name com.apple.WebKit.WebContent.Development --wait-for
```

macOS Safari internal Debug menu:

```text
defaults write com.apple.Safari IncludeInternalDebugMenu 1
```

When enabled, use Safari's internal Debug menu to show Web Process IDs in page
titles. Record the displayed process ID before attaching a native debugger.

Record:

```text
Process name
PID
Target URL or tab title
Safari or MiniBrowser process
Symbol path and build configuration
Debugger used: lldb or Xcode
Attach time
Breakpoints
Stack traces
Logs
Detach or process termination
```

Native debugger attachment is highly state-changing. It can pause threads,
change timing, trigger timeouts, and alter crash behavior. Keep engine-debugger
evidence separate from Web Inspector evidence.

## Automation Boundaries

Safari Web Inspector is primarily an interactive debugging surface. For
repeatable browser automation, prefer WebDriver or WebDriver BiDi when the
needed Safari support is available.

Use Web Inspector when:

- The target must be observed exactly in Safari or WebKit.
- The evidence is visual, source-level, or Inspector-specific.
- The target is a remote iOS page or app web view.
- The behavior depends on WebKit-specific tabs, settings, or timelines.

Use `xcrun simctl` around Web Inspector for simulator setup:

```text
xcrun simctl boot "$SIMULATOR_ID"
xcrun simctl openurl booted "https://example.test/"
xcrun simctl io booted screenshot "$RUN_DIR/simulator.png"
```

Use `safaridriver` or WebDriver-oriented tooling for scripted navigation,
clicking, form filling, and cross-browser comparisons. Record when Web
Inspector is open during automated runs, because Inspector attachment can
change timing and resource capture.

Treat third-party iOS WebKit proxy tools as compatibility bridges, not as the
primary source of truth. Validate findings in Safari Web Inspector when
possible.

## Failure Modes

Develop menu missing:

- Enable `Show features for web developers` in Safari `Settings > Advanced`.
- Confirm Safari or Safari Technology Preview is the active browser.
- Restart Safari after changing developer settings.

iOS device missing from Develop menu:

- Enable Web Inspector on the iOS or iPadOS device.
- Enable Web Inspector on the Mac Safari instance.
- Trust the Mac from the device.
- Confirm the device is connected by cable or Xcode wireless debugging.
- Try Safari Technology Preview if stable Safari cannot inspect the target.
- Reconnect the device and reopen Safari.

Simulator missing from Develop menu:

- Confirm the simulator is booted.
- Open Safari or a target app inside the simulator.
- Restart Safari on the Mac.
- Confirm the Mac Safari version can inspect the simulator runtime.

WKWebView or JSContext missing:

- Confirm the app has opted into inspection where required.
- Confirm the target is a `WKWebView` or `JSContext`, not a native view.
- Confirm the app is running and the web content has been created.
- Confirm the app, device, and Mac versions support the inspectability API.
- Ask the app owner for a debug or inspectable build when needed.

SFSafariViewController missing:

- Confirm the content is visible in the app.
- Confirm the app and device are developer-configured for inspection.
- Compare with a plain Safari page on the same device to separate device setup
  problems from app inspectability problems.

No network rows:

- Open Web Inspector before navigation.
- Reload the page while Inspector is open.
- Confirm the correct target is selected.
- Check whether request data is visible in `Sources` or `Network`.
- Record cache and device settings.

No console messages:

- Open Web Inspector before reproducing the issue.
- Confirm the selected execution context or target.
- Check console filters.
- Check whether messages are emitted in a worker, app web view, or JSContext.

Breakpoints do not hit:

- Confirm breakpoints are globally enabled.
- Confirm source maps and pretty-printed resources point to the intended code.
- Confirm the selected target and execution context.
- Reload after setting early breakpoints.
- Check blackboxing settings.

Local Override unexpectedly changes behavior:

- Disable Local Overrides and reload.
- Check whether the override is persistent from a previous session.
- Record matching URL and headers.
- Use a fresh profile or fresh simulator state.

Remote iOS settings do not apply:

- Use Web Inspector device settings for remote targets.
- Keep Web Inspector connected across navigation when the setting must persist.
- Record reloads triggered by user-agent changes.

WPE remote inspector unreachable:

- Confirm developer extras are enabled.
- Confirm `WEBKIT_INSPECTOR_SERVER` or `WEBKIT_INSPECTOR_HTTP_SERVER` is set
  before launching the target.
- Confirm the bind address and port.
- Confirm firewall and network routing.
- Use a WebKitGTK client close to the target WebKit version when possible.

Native process attach misses the right process:

- Identify whether the issue belongs to UIProcess, WebProcess,
  NetworkProcess, or StorageProcess.
- Enable Web Process IDs in page titles when debugging Safari.
- Reattach after navigation if the page uses a new WebProcess.
- Use `--wait-for` when the process starts after launch.

## Evidence Checklist

Collect:

- Official Apple, WebKit, WebKitGTK, WPE, and local version documentation used.
- macOS version, Safari version, Safari Technology Preview version when used,
  Xcode version when relevant, and WebKitGTK or WPE version when relevant.
- Device model, simulator model, iOS or iPadOS version, connection type, and
  trust or pairing state.
- Target type: Safari page, Home Screen web app, SFSafariViewController,
  WKWebView, JSContext, WebKitGTK view, WPE target, or WebKit engine process.
- Target URL, app name, bundle identifier when known, process name, and PID
  when native debugging.
- Whether Web Inspector was opened before navigation or after reproduction.
- Web Inspector tabs used and active filters.
- Screenshots for visible behavior, Elements state, Console messages, Network
  rows, Sources paused state, Storage values, Timelines, and device settings.
- Console expressions, outputs, errors, stack traces, and selected execution
  context.
- Breakpoints, URL breakpoints, bootstrap scripts, snippets, source-map
  settings, blackboxing settings, and pause/resume events.
- Network request metadata, headers, visible request or response bodies,
  redirects, timing, and load markers.
- Local Overrides, exported override files, matching state, and cleanup.
- Storage and cookie observations, edits, origin, attributes, and cleanup.
- Device settings, user-agent changes, reloads, and per-page remote settings.
- Timeline recordings, enabled categories, exported recordings, selected
  ranges, and profiling notes.
- WebKitGTK/WPE inspector server settings, bind address, client, and target
  command line.
- Native debugger attach commands, process names, PIDs, symbols, stack traces,
  and detach steps.
- Every state-changing Web Inspector, app-code, simulator, or debugger action
  before final evidence capture.

## References

- https://developer.apple.com/documentation/safari-developer-tools
- https://developer.apple.com/documentation/safari-developer-tools/web-inspector
- https://developer.apple.com/documentation/safari-developer-tools/enabling-developer-features
- https://developer.apple.com/documentation/safari-developer-tools/inspecting-ios
- https://developer.apple.com/documentation/safari-developer-tools/inspecting-safari-macos
- https://developer.apple.com/documentation/safari-developer-tools/enabling-inspecting-content-in-your-apps
- https://developer.apple.com/documentation/webkit/wkwebview/isinspectable
- https://developer.apple.com/documentation/javascriptcore/jscontext/isinspectable
- https://developer.apple.com/safari/tools/
- https://webkit.org/web-inspector/
- https://webkit.org/web-inspector/enabling-web-inspector/
- https://webkit.org/web-inspector/network-tab/
- https://webkit.org/web-inspector/sources-tab/
- https://webkit.org/web-inspector/timelines-tab/
- https://webkit.org/web-inspector/device-settings/
- https://webkit.org/web-inspector/local-overrides/
- https://webkit.org/web-inspector/inspector-bootstrap-script/
- https://webkit.org/web-inspector/url-breakpoints/
- https://webkit.org/blog/13936/enabling-the-inspection-of-web-content-in-apps/
- https://webkit.org/blog/13966/webkit-features-in-safari-16-4/
- https://webkit.org/debugging-webkit/
- https://webkitgtk.org/reference/webkit2gtk/2.37.1/class.WebInspector.html
- https://people.igalia.com/aperez/Documentation/wpe-webkit/remote-inspector.html
