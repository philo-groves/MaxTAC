# Ghidra Install and Build Reference

Use this reference only when Ghidra is missing, a release install needs to be checked, or a source/native build is needed. Verify current upstream instructions before changing these commands.

## Release Install

The official prebuilt release path is:

1. Install a 64-bit JDK 21.
2. Download the official release asset named like `ghidra_<version>_<release>_<date>.zip` from GitHub Releases. Do not use the GitHub-generated "Source Code" archives as an installable Ghidra release.
3. Extract the release archive to a new directory. Do not extract over an existing installation.
4. Launch with `ghidraRun` or `ghidraRun.bat`; launch PyGhidra with `support/pyghidraRun` or `support\pyghidraRun.bat`.

Read the release's bundled `GhidraDocs/GettingStarted.md` when Java, macOS quarantine, native components, debugger support, or upgrade behavior matters.

## Source Build

Official build prerequisites currently include:

- 64-bit JDK 21.
- Gradle 8.5+ or the provided Gradle wrapper when Internet access is available.
- Python 3.9 to 3.14 with bundled pip.
- Linux/macOS: GCC or Clang and `make`.
- Windows: Visual Studio 2017+ or Microsoft C++ Build Tools with MSVC, Windows SDK, and C++ ATL.

```bash
git clone https://github.com/NationalSecurityAgency/ghidra.git
cd ghidra
gradle -I gradle/support/fetchDependencies.gradle
gradle buildGhidra
```

When Gradle is not installed and Internet access is available, use the wrapper:

```bash
./gradlew -I gradle/support/fetchDependencies.gradle
./gradlew buildGhidra
```

On Windows, use `gradlew.bat`.

## Native Components

Official releases include native binaries for common platforms, but some platforms require local native builds. From an extracted Ghidra installation:

```bash
cd <ghidra-install>/support/gradle
gradle buildNatives
```

With the wrapper:

```bash
cd <ghidra-install>/support/gradle
./gradlew buildNatives
```

## Verify

```bash
java -version
<ghidra-install>/support/analyzeHeadless -help
<ghidra-install>/ghidraRun
```

## Source Anchors

- https://github.com/NationalSecurityAgency/ghidra
- https://github.com/NationalSecurityAgency/ghidra/blob/master/GhidraDocs/GettingStarted.md
