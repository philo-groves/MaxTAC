# radare2 Install and Build Reference

Use this reference only when radare2 is missing or a source build is needed. Verify current upstream instructions before changing these commands.

## Release Install

Download current released binaries when a packaged install is sufficient:

- https://github.com/radareorg/radare2/releases

## Source Install on Linux or macOS

The upstream README recommends installing from the Git repository source:

```bash
git clone https://github.com/radareorg/radare2
cd radare2
sys/install.sh
```

The `cd radare2` step is required before running repo-local scripts.

## Windows Build

Upstream Windows build notes currently require Python 3 with pip, Meson/Ninja, and Visual Studio. Build from the repository root:

```powershell
git clone https://github.com/radareorg/radare2
cd radare2
.\preconfigure.bat
.\configure.bat
.\make.bat
.\prefix\bin\radare2.exe
```

`preconfigure.bat` prepares Python and Visual Studio PATH state for the current console. `configure.bat` runs Meson and creates build directories. `make.bat` runs Ninja and creates the `prefix` directory containing the distribution binaries and support files.

## Verify

```bash
r2 -v
rabin2 -v
rahash2 -v
```

On Windows:

```powershell
.\prefix\bin\radare2.exe -v
```

## Source Anchors

- https://github.com/radareorg/radare2
- https://github.com/radareorg/radare2/blob/master/doc/windows.md
