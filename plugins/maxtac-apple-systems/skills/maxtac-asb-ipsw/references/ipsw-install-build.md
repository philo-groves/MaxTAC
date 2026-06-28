# ipsw Install and Build Reference

Use this reference only when `ipsw` is missing or a source build is needed. Verify current upstream instructions before changing these commands.

## Verified Install Paths

Install from official packages when possible:

```bash
# macOS, blacktop tap with extras
brew install blacktop/tap/ipsw

# macOS, Homebrew core formula
brew install ipsw

# Linux
sudo snap install ipsw
```

On Windows:

```powershell
scoop bucket add blacktop https://github.com/blacktop/scoop-bucket.git
scoop install blacktop/ipsw
```

Prefer `blacktop/tap/ipsw` when device interaction, Frida, or other extras are needed.

## Source Build

The upstream README currently lists Go 1.24+ for source builds.

```bash
git clone https://github.com/blacktop/ipsw.git
cd ipsw
make build
```

## Verify

```bash
ipsw version
ipsw --help
```

On Windows:

```powershell
ipsw.exe version
ipsw.exe --help
```

## Source Anchors

- https://github.com/blacktop/ipsw
