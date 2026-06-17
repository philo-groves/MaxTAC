# JADX Install and Build Reference

Use this reference only when JADX is missing or a source build is needed. Verify current upstream instructions before changing these commands.

## Package Installs

Official upstream README install options currently include:

```bash
# Arch Linux
sudo pacman -S jadx

# macOS
brew install jadx

# Flathub
flatpak install flathub com.github.skylot.jadx
```

Release archives also provide CLI and GUI launchers under `bin`; on Windows, use `jadx.bat` and `jadx-gui.bat` when the release `bin` directory is not on `PATH`.

## Source Build

The upstream README currently requires JDK 17 or higher to build from source:

```bash
git clone https://github.com/skylot/jadx.git
cd jadx
./gradlew dist
```

On Windows:

```powershell
git clone https://github.com/skylot/jadx.git
cd jadx
.\gradlew.bat dist
```

The generated launch scripts are placed in `build/jadx/bin`, and the packaged archive is placed under `build/`.

## Verify

```bash
jadx --version
jadx --help
jadx-gui --help
java -version
```

## Source Anchors

- https://github.com/skylot/jadx
