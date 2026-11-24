"""Read-only CPU/RAM diagnostics; no model imports or benchmark claims."""
from __future__ import annotations

import os
import sys


def memory_bytes() -> tuple[int | None, int | None]:
    try:
        if sys.platform == "win32":
            import ctypes
            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", ctypes.c_uint32), ("load", ctypes.c_uint32),
                            ("total", ctypes.c_uint64), ("available", ctypes.c_uint64),
                            ("page_total", ctypes.c_uint64), ("page_available", ctypes.c_uint64),
                            ("virtual_total", ctypes.c_uint64), ("virtual_available", ctypes.c_uint64),
                            ("extended_available", ctypes.c_uint64)]
            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.total), int(status.available)
        elif sys.platform.startswith("linux"):
            from pathlib import Path
            values = {}
            for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
                key, _, value = line.partition(":")
                if key in ("MemTotal", "MemAvailable"):
                    values[key] = int(value.split()[0]) * 1024
            return values.get("MemTotal"), values.get("MemAvailable")
    except (OSError, ValueError, AttributeError, IndexError):
        pass
    return None, None


def logical_cpus() -> int:
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except (AttributeError, OSError):
        return max(1, os.cpu_count() or 1)


def select_threads(requested: int | None = None) -> int:
    available = logical_cpus()
    if requested is None:
        return max(1, min(4, available - 1))
    if type(requested) is not int or not 1 <= requested <= available:
        raise ValueError("CPU threads must be an integer from 1 to " + str(available))
    return requested


def report() -> dict:
    total, free = memory_bytes()
    return {"logical_cpus_available": logical_cpus(),
            "physical_ram_gib": round(total / 1024**3, 2) if total else None,
            "available_ram_gib": round(free / 1024**3, 2) if free is not None else None,
            "suggested_cpu_threads": select_threads(),
            "low_available_ram_warning": free is not None and free < 4 * 1024**3,
            "actual_model_speed_measured": False,
            "model_memory_requirement_verified": False}
