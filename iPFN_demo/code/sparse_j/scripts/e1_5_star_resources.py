"""Native Windows process measurements; no extra package or model imports."""
import ctypes
from ctypes import wintypes
import os
import statistics


def physical_memory():
    class Status(ctypes.Structure):
        _fields_ = [("length", wintypes.DWORD), ("load_percent", wintypes.DWORD)] + [
            (name, ctypes.c_ulonglong) for name in ("total_bytes", "available_bytes", "total_pagefile",
                                                   "available_pagefile", "total_virtual", "available_virtual", "extended_virtual")]
    status = Status()
    status.length = ctypes.sizeof(status)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(Status)]
    kernel.GlobalMemoryStatusEx.restype = wintypes.BOOL
    if not kernel.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {name: int(getattr(status, name)) for name in ("total_bytes", "available_bytes", "load_percent")}


def memory_usage(handle=None):
    if os.name != "nt":
        raise RuntimeError("Resource measurement currently requires Windows")

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("page_faults", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "peak_working_set_bytes", "working_set_bytes", "peak_paged_pool", "paged_pool",
                "peak_nonpaged_pool", "nonpaged_pool", "pagefile_bytes", "peak_pagefile", "private_bytes")]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    process = kernel.GetCurrentProcess() if handle is None else wintypes.HANDLE(int(handle))
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {name: int(getattr(counters, name)) for name in
            ("peak_working_set_bytes", "working_set_bytes", "private_bytes")}


def cpu_seconds(handle):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)]*4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
    if not kernel.GetProcessTimes(wintypes.HANDLE(int(handle)), ctypes.byref(created), ctypes.byref(exited),
                                  ctypes.byref(system), ctypes.byref(user)):
        raise ctypes.WinError(ctypes.get_last_error())
    convert = lambda value: ((value.dwHighDateTime << 32) + value.dwLowDateTime) / 1e7
    return dict(cpu_seconds=convert(system)+convert(user), user_seconds=convert(user), kernel_seconds=convert(system))


def memory_trend(tasks):
    """Predefined diagnostic, not proof for/against a leak in a longer run."""
    values = [t["resources"]["private_bytes"] for t in tasks[4:]]
    if len(values) < 8:
        return dict(status="insufficient_tasks", warmup_tasks_excluded=4)
    quarter = max(2, len(values)//4)
    delta = statistics.median(values[-quarter:]) - statistics.median(values[:quarter])
    slope = statistics.linear_regression(range(len(values)), values).slope
    flag = delta > 32*1024**2 and slope > .5*1024**2
    return dict(status="investigate_growth" if flag else "no_sustained_growth_detected_at_this_scale",
                warmup_tasks_excluded=4, private_bytes_median_increase=delta,
                private_bytes_slope_per_task=slope,
                criterion="Flag if BOTH median last-vs-first-quarter increase >32 MiB and slope >0.5 MiB/task",
                limitation="A short 40-task pilot cannot exclude slow or later memory growth.")
