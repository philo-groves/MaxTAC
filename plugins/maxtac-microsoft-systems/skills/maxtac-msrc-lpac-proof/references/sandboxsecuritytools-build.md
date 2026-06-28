# Microsoft SandboxSecurityTools Build Reference

Use this reference only when `SandboxSecurityTools` is missing or `LaunchAppContainer` / `EdgeSandboxTestTool` must be rebuilt. Verify current upstream instructions before changing these commands.

## Clone Once

```powershell
git clone https://github.com/microsoft/SandboxSecurityTools.git
cd SandboxSecurityTools
```

Record the repository commit hash used in the proof packet.

## Build LaunchAppContainer

From the `SandboxSecurityTools` repository root:

```powershell
msbuild .\LaunchAppContainer\LaunchAppContainer.sln /p:Configuration=Release /p:Platform=x64
```

Use the included MSRC batch file for eligible LPAC proof launches:

```powershell
.\LaunchAppContainer\LaunchSandboxMSRC.bat C:\path\to\pov.exe
```

The current batch expands to:

```powershell
LaunchAppContainer.exe -m 1.0.0.0_x86_en-us_TestProgram_wvx3sa3v3dj1m -c lpacCom;registryRead -w -l -k -i %*
```

Do not remove `-k`, change the command-line options, or add capabilities for Attack Scenario submissions unless Microsoft's current instructions or a real eligible sandbox requires a different configuration.

## Build EdgeSandboxTestTool

From the `SandboxSecurityTools` repository root:

```powershell
cd .\EdgeSandboxTestTool
mkdir build
cd build
cmake ..\src
cmake --build . --config Release
```

`EdgeSandboxTestTool` produces `estt.exe` and `renderer.exe`. To run custom code in the Chromium renderer sandbox approximation, edit `src\child\renderer\renderer.cc` from the `EdgeSandboxTestTool` directory, add the trigger in `custom()`, rebuild, then run from the build directory:

```powershell
.\Release\estt.exe .\Release\renderer.exe
```

Do not use `estt.exe` to run an arbitrary executable; the paired `renderer.exe` must complete the expected sandbox initialization routine.

## Source Anchors

- https://github.com/microsoft/SandboxSecurityTools
- https://github.com/microsoft/SandboxSecurityTools/blob/main/LaunchAppContainer/README.md
- https://github.com/microsoft/SandboxSecurityTools/blob/main/LaunchAppContainer/LaunchSandboxMSRC.bat
- https://github.com/microsoft/SandboxSecurityTools/blob/main/EdgeSandboxTestTool/README.md
