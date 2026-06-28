#!/usr/bin/env python3
"""Choose parallel or sequential MaxTAC subagent spawning."""

from __future__ import annotations

import argparse
import ctypes
import os
import subprocess
import sys
from pathlib import Path


BYTES_PER_GIB = 1024**3
MIN_AVAILABLE_MEMORY_PER_SUBAGENT = 4 * BYTES_PER_GIB
MIN_MEMORY_HEADROOM = BYTES_PER_GIB
AUDITOR_MIN_TOTAL_MEMORY = 17 * BYTES_PER_GIB
SUBAGENT_KINDS = ("generic", "auditor", "debater")


def available_memory_bytes() -> int | None:
    if sys.platform.startswith("win"):
        return windows_available_memory()
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        return linux_available_memory(meminfo)
    return posix_available_memory()


def total_memory_bytes() -> int | None:
    if sys.platform.startswith("win"):
        return windows_total_memory()
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        return linux_total_memory(meminfo)
    total = posix_total_memory()
    if total is not None:
        return total
    return macos_total_memory()


def windows_available_memory() -> int | None:
    status = windows_memory_status()
    return int(status.ullAvailPhys) if status else None


def windows_total_memory() -> int | None:
    status = windows_memory_status()
    return int(status.ullTotalPhys) if status else None


def windows_memory_status() -> ctypes.Structure | None:
    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return status


def linux_available_memory(meminfo: Path) -> int | None:
    for line in meminfo.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("MemAvailable:"):
            parts = line.split()
            if len(parts) >= 2:
                return int(parts[1]) * 1024
    return None


def linux_total_memory(meminfo: Path) -> int | None:
    for line in meminfo.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("MemTotal:"):
            parts = line.split()
            if len(parts) >= 2:
                return int(parts[1]) * 1024
    return None


def posix_available_memory() -> int | None:
    if not hasattr(os, "sysconf"):
        return None
    try:
        pages = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError):
        return None
    if pages < 0 or page_size < 0:
        return None
    return int(pages * page_size)


def posix_total_memory() -> int | None:
    if not hasattr(os, "sysconf"):
        return None
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError):
        return None
    if pages < 0 or page_size < 0:
        return None
    return int(pages * page_size)


def macos_total_memory() -> int | None:
    if sys.platform != "darwin":
        return None
    try:
        completed = subprocess.run(
            ["sysctl", "-n", "hw.memsize"],
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    try:
        return int(completed.stdout.strip())
    except ValueError:
        return None


def can_spawn_parallel(subagents: int, kind: str = "generic") -> bool:
    if kind == "auditor":
        total = total_memory_bytes()
        if total is None or total < AUDITOR_MIN_TOTAL_MEMORY:
            return False
    if subagents <= 1:
        return True

    available = available_memory_bytes()
    if available is None:
        return False

    required = MIN_MEMORY_HEADROOM + (subagents * MIN_AVAILABLE_MEMORY_PER_SUBAGENT)
    if available < required:
        return False

    cpus = os.cpu_count() or 1
    return cpus >= min(subagents, 2)


def positive_int(value: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if result < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    if result > 6:
        raise argparse.ArgumentTypeError("must be 6 or lower")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Check MaxTAC subagent parallel readiness")
    parser.add_argument("--subagents", type=positive_int, required=True)
    parser.add_argument(
        "--kind",
        choices=SUBAGENT_KINDS,
        default="generic",
        help="Subagent kind; auditor adds a total-RAM gate before parallel spawning",
    )
    args = parser.parse_args()
    print("parallel" if can_spawn_parallel(args.subagents, args.kind) else "sequential")


if __name__ == "__main__":
    main()
