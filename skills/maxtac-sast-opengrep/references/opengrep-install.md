# OpenGrep Install Reference

Use this reference only when OpenGrep is missing. Verify current upstream install scripts before changing these commands.

## Linux and macOS

The upstream install script supports latest-version installs, `-v <version>`, `--verify-signatures`, `-l`, and `-h`.

```bash
curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash
```

With signature verification:

```bash
curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash -s -- --verify-signatures
```

The script installs under `~/.opengrep/cli/<version>/opengrep` and maintains a `~/.opengrep/cli/latest` symlink. It creates a `~/.local/bin/opengrep` symlink only when that directory exists and is writable; otherwise add `~/.opengrep/cli/latest` to `PATH`.

## Windows PowerShell

The upstream PowerShell installer supports latest-version installs, `-Version <version>`, `-VerifySignatures`, `-List`, and `-Help`.

```powershell
irm https://raw.githubusercontent.com/opengrep/opengrep/main/install.ps1 | iex
```

With parameters:

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/opengrep/opengrep/main/install.ps1))) -Version v1.15.0
```

The script installs under `%USERPROFILE%\.opengrep\cli\<version>\opengrep.exe`, maintains a `latest` junction or copy, and prints PATH instructions rather than modifying PATH automatically.

## Verify

```bash
opengrep --version
opengrep --help
```

On Windows, use the installed `latest\opengrep.exe` path if it is not yet on `PATH`.

## Source Anchors

- https://github.com/opengrep/opengrep
- https://github.com/opengrep/opengrep/blob/main/install.sh
- https://github.com/opengrep/opengrep/blob/main/install.ps1
