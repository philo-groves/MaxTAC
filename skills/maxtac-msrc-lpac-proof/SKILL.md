---
name: maxtac-msrc-lpac-proof
description: "Use this skill when proving Microsoft Windows Insider Preview local sandbox attack scenarios for MSRC bounty submissions, especially LPAC sandbox escapes or private data access using microsoft/SandboxSecurityTools LaunchAppContainer or EdgeSandboxTestTool."
---

# MaxTAC MSRC LPAC Proof

Use this skill when a Windows vulnerability candidate needs proof that it qualifies for the Windows Insider Preview local Attack Scenario Award. Microsoft requires local Attack Scenario proofs to demonstrate elevation or private-data access from the restricted context of an eligible sandbox. For LPAC testing, the restricted context is achieved with Microsoft `SandboxSecurityTools`, especially the `LaunchAppContainer` tool using the LPAC flag.

Do not treat "runs from AppContainer" as enough. For the larger local sandbox award, the PoV must run from an eligible sandbox context, trigger a vulnerability in shipped Windows code, reproduce on the latest Windows Insider Preview Canary Channel build, and demonstrate the security impact.

## Award and Eligibility Rules

Maximum local Attack Scenario Awards are currently:

- Sandbox escape with little or no user interaction: up to $30,000.
- Unauthorized access to private user data, or data that can weaken existing user protections, from a sandboxed process with no user interaction: up to $30,000.

Eligible sandboxes for these local Attack Scenario Awards:

- New Microsoft Edge based on Chromium renderer process.
- Windows Defender Sandbox, `MsMpEngCP`.
- WinHTTP Web Proxy Auto-Discovery Service, WPAD sandboxed process.
- `UtcDecoderHost.exe` sandboxed process.

Ineligible sandboxes for Attack Scenario Awards:

- Generic AppContainer (AC).
- Internet Explorer sandbox.

Ineligible AC/IE sandbox findings may still qualify only for General Awards. General Award amounts are much lower and are based on security impact and finishing privilege.

## Required MSRC Environment Evidence

For every LPAC proof package, capture:

- Windows Insider Preview Canary Channel build used for the original PoV.
- `BuildLabEx` from:

```powershell
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' |
  Select-Object CurrentBuild, UBR, BuildLabEx
```

- Date tested.
- `SandboxSecurityTools` commit hash.
- Exact command line used to launch the PoV.
- Whether the PoV targets an eligible sandbox or only a generic LPAC/AC context.
- Whether any debugger was used, and whether the exploit depends on the debugger.

MSRC states that Attack Scenario submissions relying exclusively on a debugger for suspending threads or modifying memory/code are not eligible. A debugger can be included only as an optional aid for faster reproduction when the vulnerability is otherwise demonstrated without it.

## Proof Evidence Helper

Use `python3 <skill-dir>/scripts/lpac-proof.py` to collect and lint the LPAC proof packet before report drafting. The helper creates a proof bundle under `<workspace-root>/proof/<case-id>/`, copies source/binary/evidence artifacts, records command output, and checks the report packet checklist below.

When the MaxTAC MCP server is available, prefer the `lpac_proof` tool before invoking the script directly. Set `action` to `init`, `capture`, `add-artifact`, `lint`, or `summary`; the MCP tool calls the same helper and returns captured stdout plus parsed JSON for summaries.

Initialize a proof case:

```powershell
python3 <skill-dir>/scripts/lpac-proof.py init `
  --attack-scenario sandbox-escape `
  --eligible-sandbox edge-renderer `
  --canary-build "Canary 99999.1" `
  --build-lab-ex "99999.1.amd64fre.canary.260616-0000" `
  --sandbox-tools-commit "<SandboxSecurityTools commit>" `
  --tool-used LaunchAppContainer `
  --launch-command "LaunchSandboxMSRC.bat C:\path\to\pov.exe" `
  --no-debugger-used `
  --debugger-dependency none `
  --pov-source .\pov.cpp `
  --pov-binary .\pov.exe `
  --build-instructions "msbuild pov.sln /p:Configuration=Release /p:Platform=x64" `
  --baseline-denied-operation "direct access returns access denied" `
  --exploit-success-operation "vulnerable path grants access" `
  --finishing-privilege-or-data "file written outside AppContainer profile" `
  --shipped-component "Windows component reached from the sandbox" `
  --vulnerability-path "explain the shipped-code path"
```

Attach checklist artifacts with explicit categories:

```powershell
python3 <skill-dir>/scripts/lpac-proof.py add-artifact <case-id> --category token-dump --artifact .\token.txt
python3 <skill-dir>/scripts/lpac-proof.py add-artifact <case-id> --category baseline-denied --artifact .\baseline.txt
python3 <skill-dir>/scripts/lpac-proof.py add-artifact <case-id> --category exploit-success --artifact .\success.txt
python3 <skill-dir>/scripts/lpac-proof.py add-artifact <case-id> --category finishing-proof --artifact .\finish.txt
```

Capture launcher, token, or system evidence command output:

```powershell
python3 <skill-dir>/scripts/lpac-proof.py capture <case-id> --label launch --command "LaunchSandboxMSRC.bat C:\path\to\pov.exe"
```

Before claiming Attack Scenario readiness, run:

```powershell
python3 <skill-dir>/scripts/lpac-proof.py lint <case-id> --strict
python3 <skill-dir>/scripts/lpac-proof.py summary <case-id>
```

## Build the Microsoft Tools

Use the official repository:

```powershell
git clone https://github.com/microsoft/SandboxSecurityTools.git
cd SandboxSecurityTools\LaunchAppContainer
msbuild LaunchAppContainer.sln /p:Configuration=Release /p:Platform=x64
```

For Edge renderer sandbox testing:

```powershell
cd SandboxSecurityTools\EdgeSandboxTestTool
mkdir build
cd build
cmake ..\src
cmake --build . --config Release
```

`EdgeSandboxTestTool` produces `estt.exe` and `renderer.exe`. Edit `EdgeSandboxTestTool\src\child\renderer\renderer.cc`, put the exploit trigger in `custom()`, rebuild, then run:

```powershell
.\Release\estt.exe .\Release\renderer.exe
```

Do not use `estt.exe` to run arbitrary executables. The repository warns that the sandbox process must complete a specific initialization routine, and using ESTT to run something other than `renderer.exe` is not supported and may not match the Chromium renderer sandbox restrictions.

## LaunchAppContainer MSRC Mode

For LPAC proofing, prefer the included MSRC batch file:

```powershell
.\LaunchSandboxMSRC.bat C:\path\to\poc.exe
```

The batch file currently expands to:

```powershell
LaunchAppContainer.exe -m 1.0.0.0_x86_en-us_TestProgram_wvx3sa3v3dj1m -c lpacCom;registryRead -w -l -k -i <PoV>
```

Meaning:

- `-m`: package moniker for the AppContainer profile.
- `-c lpacCom;registryRead`: predefined eligible capabilities.
- `-w`: wait for the AppContainer process to exit.
- `-l`: create the process as Less Privileged AppContainer.
- `-k`: enable disallow-win32k process mitigation.
- `-i`: executable to launch.

For Attack Scenario Awards, do not change these command line options and do not add capabilities unless Microsoft's current instructions or the real eligible sandbox requires them. The `LaunchAppContainer` README states that changes to the MSRC command line options, or use of capabilities not included in the batch file, are not eligible for bounty submissions.

## LPAC Meaning for Proofs

LPAC is stricter than regular AppContainer. Regular AppContainers receive access to some common files, registry keys, and COM objects through broad `ALL_APPLICATION_PACKAGES` access. LPAC opts out of that broad access by setting the `PROC_THREAD_ATTRIBUTE_ALL_APPLICATION_PACKAGES_POLICY` attribute to `PROCESS_CREATION_ALL_APPLICATION_PACKAGES_OPT_OUT`.

Consequences:

- LPAC cannot use COM without `lpacCom`.
- LPAC cannot open registry keys without `registryRead`.
- LPAC should not have ambient access to resources that regular AppContainer can reach through `ALL_APPLICATION_PACKAGES`.
- Access checks are still an intersection of the user SID/group rights and the AppContainer package/capability SIDs.
- The process runs at Low Integrity Level, but "Low IL" and "AppContainer" are different token properties.

The `-k` flag enables `PROCESS_CREATION_MITIGATION_POLICY_WIN32K_SYSTEM_CALL_DISABLE_ALWAYS_ON`. That means no win32k system calls and no UI element creation. Console output is redirected to the parent console. PoVs run with `-k` should avoid imports or runtimes that call win32k; the tool README recommends static VC runtime linking for console applications that must run under win32k lockdown.

## Proof Goals

For a sandbox escape, demonstrate a clear transition from the LPAC sandbox to a more privileged context. Good proof artifacts include:

- A file written outside the AppContainer profile that the LPAC token cannot directly write.
- A process created outside the LPAC token or with stronger rights.
- A handle, token, ALPC, COM, service, registry, filesystem, or broker action that crosses the sandbox boundary.
- A before/after token comparison proving the starting LPAC context and finishing privilege.
- A deterministic action that succeeds only because the vulnerable shipped Windows component was reachable from the sandbox.

For private-data access, demonstrate retrieval of data protected behind a Windows security boundary:

- User files, emails, photos, credentials-adjacent material, or data that can weaken user protections.
- The exact path, object, or API requested.
- The failed baseline access from plain LPAC.
- The successful access through the vulnerability.

Do not claim maximum-award eligibility from a crash, denial of service, Low IL only escape, or normal resource access granted by the supplied capabilities.

## Baseline Then Exploit

Structure the PoV as two phases:

1. Baseline restrictions:
   - Print process ID.
   - Print token AppContainer/LPAC state, integrity level, package SID, and capabilities.
   - Attempt the target operation directly and show it fails with the expected access-denied result.
2. Exploit path:
   - Trigger the shipped Windows component vulnerability.
   - Repeat the target operation through the vulnerable path.
   - Print or save the resulting privilege/data proof.

Useful commands around the PoV:

```powershell
whoami /all
Get-Process -Id <pid> | Format-List *
icacls <target-path>
reg query <target-key>
```

For token-level proof, prefer a tiny helper in the PoV that calls `OpenProcessToken` and `GetTokenInformation` for `TokenIntegrityLevel`, `TokenIsAppContainer`, `TokenAppContainerSid`, `TokenCapabilities`, and `TokenUser`. Do not rely only on screenshots.

## Eligible Sandbox Routing

Choose the harness based on the claim:

- Edge renderer process: use `EdgeSandboxTestTool`, place the trigger in `custom()`, and run via `estt.exe renderer.exe`.
- Generic LPAC approximation for local Attack Scenario proof: use `LaunchSandboxMSRC.bat`.
- Defender sandbox, WPAD sandbox, or `UtcDecoderHost.exe`: use `LaunchSandboxMSRC.bat` only as the restricted-context verification baseline; also explain how the shipped sandboxed component reaches the same vulnerable code in the real product.

The MSRC local Attack Scenario language requires the PoV to elevate privileges under the restricted context of an eligible sandbox. If the PoV only works from generic LPAC and there is no path from an eligible sandboxed Windows component, route the finding as a possible General Award instead.

## Common Failure Modes

- Adding broad capabilities to make the PoV work. This usually destroys Attack Scenario eligibility.
- Dropping `-k` because a GUI/runtime import fails. MSRC requires disallow win32k for the LaunchAppContainer LPAC flow.
- Testing on Windows 10, Windows Server, Beta/Dev, or a stale Canary build. Current bounty eligibility requires the latest Canary Channel build.
- Exercising a vulnerability only in a custom server, custom client, custom harness, or fuzz target. Attack Scenario PoVs must exercise shipped Windows application, service, or component code.
- Using a debugger to suspend threads, rewrite memory, bypass checks, or create the primitive. That is not an eligible Attack Scenario proof.
- Reporting a generic AppContainer or IE sandbox escape as a local Attack Scenario. These are listed as ineligible sandboxes for that award class.
- Showing Low IL escape but not proving a sandbox boundary escape or private data access.

## Report Packet Checklist

Include:

- Attack scenario claimed: sandbox escape or sandboxed private-data access.
- Eligible sandbox name: Edge renderer, `MsMpEngCP`, WPAD sandboxed process, or `UtcDecoderHost.exe`.
- Canary build and `BuildLabEx`.
- `SandboxSecurityTools` commit and tool used.
- Exact command line, preferably `LaunchSandboxMSRC.bat <PoV>` output.
- PoV source and binary, with build instructions.
- Token/capability dump from inside the sandbox before exploitation.
- Baseline denied operation.
- Exploit success operation.
- Finishing privilege or data accessed.
- Explanation of the shipped Windows component and vulnerability path.
- Statement that the PoV does not rely exclusively on debugger actions.
- Any optional debugger-assisted reproduction steps clearly marked optional.

## Source Anchors

- Windows Insider Preview Bounty Program: https://www.microsoft.com/en-us/msrc/bounty-windows-insider-preview
- Microsoft SandboxSecurityTools: https://github.com/microsoft/SandboxSecurityTools
- LaunchAppContainer README: https://github.com/microsoft/SandboxSecurityTools/blob/main/LaunchAppContainer/README.md
- LaunchSandboxMSRC batch: https://github.com/microsoft/SandboxSecurityTools/blob/main/LaunchAppContainer/LaunchSandboxMSRC.bat
- EdgeSandboxTestTool README: https://github.com/microsoft/SandboxSecurityTools/blob/main/EdgeSandboxTestTool/README.md
- Microsoft AppContainer/LPAC launch documentation: https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer
- Microsoft AppContainer isolation documentation: https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation
