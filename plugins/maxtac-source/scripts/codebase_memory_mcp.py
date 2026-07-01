#!/usr/bin/env python3
"""Launch the DeusData codebase-memory-mcp binary for the Source plugin."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


REPO = "DeusData/codebase-memory-mcp"
API_LATEST_RELEASE = f"https://api.github.com/repos/{REPO}/releases/latest"
TOOL_NAME = "codebase-memory-mcp"
USER_AGENT = "MaxTAC-Source/codebase-memory-mcp-launcher"


def log(message: str) -> None:
    print(f"[maxtac-source codebase-memory] {message}", file=sys.stderr, flush=True)


def truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() in {"1", "true", "yes", "on"}


def tool_root() -> Path:
    override = os.environ.get("MAXTAC_CODEBASE_MEMORY_TOOL_DIR")
    if override:
        return Path(override).expanduser().resolve()
    codex_home = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    return (codex_home / "maxtac" / "tools" / TOOL_NAME).resolve()


def platform_parts() -> tuple[str, str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        os_name = "darwin"
        extension = ".tar.gz"
    elif system == "linux":
        os_name = "linux"
        extension = ".tar.gz"
    elif system == "windows":
        os_name = "windows"
        extension = ".zip"
    else:
        raise SystemExit(f"unsupported platform for {TOOL_NAME}: {platform.system()}")

    if machine in {"arm64", "aarch64"}:
        arch = "arm64"
    elif machine in {"x86_64", "amd64"}:
        arch = "amd64"
    else:
        raise SystemExit(f"unsupported architecture for {TOOL_NAME}: {platform.machine()}")
    return os_name, arch, extension


def platform_id() -> str:
    os_name, arch, _ = platform_parts()
    variant = "ui" if truthy(os.environ.get("MAXTAC_CODEBASE_MEMORY_UI")) else "standard"
    return f"{os_name}-{arch}-{variant}"


def binary_name() -> str:
    return f"{TOOL_NAME}.exe" if platform.system().lower() == "windows" else TOOL_NAME


def cached_binary_path() -> Path:
    return tool_root() / "current" / platform_id() / binary_name()


def explicit_binary() -> Path | None:
    value = os.environ.get("MAXTAC_CODEBASE_MEMORY_MCP")
    if not value:
        return None
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"MAXTAC_CODEBASE_MEMORY_MCP points to a missing file: {path}")
    return path


def path_binary() -> Path | None:
    found = shutil.which(TOOL_NAME)
    if found:
        return Path(found).resolve()
    return None


def request_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"unexpected JSON payload from {url}")
    return data


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response:
        destination.write_bytes(response.read())


def asset_name() -> str:
    os_name, arch, extension = platform_parts()
    prefix = TOOL_NAME
    if truthy(os.environ.get("MAXTAC_CODEBASE_MEMORY_UI")):
        prefix = f"{TOOL_NAME}-ui"
    return f"{prefix}-{os_name}-{arch}{extension}"


def asset_by_name(release: dict[str, Any], name: str) -> dict[str, Any]:
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise SystemExit("latest release payload did not include assets")
    for asset in assets:
        if isinstance(asset, dict) and asset.get("name") == name:
            return asset
    for asset in assets:
        candidate = asset.get("name") if isinstance(asset, dict) else None
        if isinstance(candidate, str) and candidate.endswith(name):
            return asset
    available = ", ".join(str(asset.get("name")) for asset in assets if isinstance(asset, dict))
    raise SystemExit(f"release asset not found: {name}. Available assets: {available}")


def checksum_asset(release: dict[str, Any]) -> dict[str, Any]:
    return asset_by_name(release, "checksums.txt")


def browser_download_url(asset: dict[str, Any]) -> str:
    value = asset.get("browser_download_url")
    if not isinstance(value, str) or not value:
        raise SystemExit(f"release asset has no browser_download_url: {asset.get('name')}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_checksums(path: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.strip().replace("*", " ").split()
        if len(parts) < 2:
            continue
        digest = parts[0].lower()
        name = Path(parts[-1]).name
        if len(digest) == 64 and all(char in "0123456789abcdef" for char in digest):
            checksums[name] = digest
    return checksums


def verify_checksum(archive: Path, checksums: Path, expected_name: str) -> None:
    expected = parse_checksums(checksums).get(expected_name)
    if not expected:
        raise SystemExit(f"checksums.txt did not contain an entry for {expected_name}")
    actual = sha256(archive)
    if actual != expected:
        raise SystemExit(f"checksum mismatch for {expected_name}: expected {expected}, got {actual}")


def extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    resolved_destination = destination.resolve()
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as package:
            for member in package.infolist():
                target = (destination / member.filename).resolve()
                try:
                    target.relative_to(resolved_destination)
                except ValueError as exc:
                    raise SystemExit(f"unsafe path in {archive.name}: {member.filename}") from exc
            package.extractall(destination)
        return
    with tarfile.open(archive) as package:
        for member in package.getmembers():
            if member.issym() or member.islnk():
                raise SystemExit(f"unsafe link in {archive.name}: {member.name}")
            target = (destination / member.name).resolve()
            try:
                target.relative_to(resolved_destination)
            except ValueError as exc:
                raise SystemExit(f"unsafe path in {archive.name}: {member.name}") from exc
        package.extractall(destination)


def find_extracted_binary(root: Path) -> Path:
    expected_name = binary_name()
    candidates = [path for path in root.rglob(expected_name) if path.is_file()]
    if not candidates:
        raise SystemExit(f"extracted archive did not contain {expected_name}")
    candidates.sort(key=lambda path: (len(path.parts), str(path)))
    return candidates[0]


def make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if platform.system().lower() == "darwin":
        try:
            subprocess.run(["xattr", "-d", "com.apple.quarantine", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["codesign", "--force", "--sign", "-", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            pass


def download_binary() -> Path:
    if truthy(os.environ.get("MAXTAC_CODEBASE_MEMORY_NO_DOWNLOAD")):
        raise SystemExit("codebase-memory-mcp is not cached and MAXTAC_CODEBASE_MEMORY_NO_DOWNLOAD is set")

    name = asset_name()
    root = tool_root()
    target = cached_binary_path()
    root.mkdir(parents=True, exist_ok=True)
    log(f"downloading {name} from github.com/{REPO}")

    try:
        release = request_json(API_LATEST_RELEASE)
        package_asset = asset_by_name(release, name)
        sums_asset = checksum_asset(release)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to read latest {TOOL_NAME} release metadata: {exc}") from exc

    with tempfile.TemporaryDirectory(prefix="maxtac-cbm-") as temp_text:
        temp = Path(temp_text)
        archive = temp / name
        checksums = temp / "checksums.txt"
        try:
            download(browser_download_url(package_asset), archive)
            download(browser_download_url(sums_asset), checksums)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise SystemExit(f"failed to download {TOOL_NAME} release asset: {exc}") from exc
        verify_checksum(archive, checksums, name)
        extract_dir = temp / "extract"
        extract_archive(archive, extract_dir)
        extracted = find_extracted_binary(extract_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(extracted, target)
        make_executable(target)
        metadata = {
            "repo": REPO,
            "tag_name": release.get("tag_name", ""),
            "asset": name,
            "binary": str(target),
            "sha256": sha256(target),
        }
        (target.parent / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    log(f"installed {TOOL_NAME} at {target}")
    return target


def resolve_binary(download_if_missing: bool) -> tuple[Path | None, str]:
    explicit = explicit_binary()
    if explicit:
        return explicit, "MAXTAC_CODEBASE_MEMORY_MCP"
    cached = cached_binary_path()
    if cached.exists():
        return cached, "plugin-cache"
    existing = path_binary()
    if existing:
        return existing, "PATH"
    if download_if_missing:
        return download_binary(), "downloaded"
    return None, "missing"


def exec_binary(binary: Path, args: list[str]) -> None:
    os.execv(str(binary), [str(binary), *args])


def status() -> None:
    binary, source = resolve_binary(download_if_missing=False)
    metadata_path = cached_binary_path().parent / "metadata.json"
    metadata: dict[str, Any] = {}
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            metadata = {"metadata_error": f"invalid JSON: {metadata_path}"}
    print(json.dumps({"status": source, "binary": str(binary) if binary else "", "cache": str(tool_root()), **metadata}, indent=2))


def main(argv: list[str]) -> None:
    command = argv[0] if argv else "serve"
    rest = argv[1:] if argv else []
    if command == "status":
        status()
        return
    if command in {"ensure", "install"}:
        binary, _ = resolve_binary(download_if_missing=True)
        if not binary:
            raise SystemExit(f"could not install {TOOL_NAME}")
        print(binary)
        return
    if command == "serve":
        binary, source = resolve_binary(download_if_missing=True)
        if not binary:
            raise SystemExit(f"could not find or install {TOOL_NAME}")
        log(f"starting {TOOL_NAME} from {source}")
        extra_args = shlex.split(os.environ.get("MAXTAC_CODEBASE_MEMORY_ARGS", ""))
        exec_binary(binary, [*extra_args, *rest])
    if command == "cli":
        binary, _ = resolve_binary(download_if_missing=True)
        if not binary:
            raise SystemExit(f"could not find or install {TOOL_NAME}")
        exec_binary(binary, ["cli", *rest])
    binary, _ = resolve_binary(download_if_missing=True)
    if not binary:
        raise SystemExit(f"could not find or install {TOOL_NAME}")
    exec_binary(binary, argv)


if __name__ == "__main__":
    main(sys.argv[1:])
