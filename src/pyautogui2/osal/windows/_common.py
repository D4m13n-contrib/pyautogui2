import contextlib
import ctypes
import logging
import sys

from ctypes import wintypes
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    # Type hints for MyPy
    ULONG_PTR = ctypes.c_uint64
else:
    # For Python compatibility
    if not hasattr(wintypes, "ULONG_PTR"):
        wintypes.ULONG_PTR = (
            ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8
            else ctypes.c_uint32
        )
    ULONG_PTR = wintypes.ULONG_PTR


# --- Win32 Structures ---

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUTUNION),
    ]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


# --- Utilities ---

def is_legacy_windows(user32) -> bool:
    """Decide whether to operate in legacy mode:
    - True if Windows version < 6 (XP and older).
    - else test SendInput with a harmless call.
    - if any error occurs, conservative fallback => True.
    """
    try:
        if not hasattr(sys, "getwindowsversion"):
            logging.debug("No sys.getwindowsversion -> assume legacy True")
            return True

        ver = sys.getwindowsversion()
        if ver.major < 6:
            logging.debug(f"Windows version {ver.major}.{ver.minor} -> legacy True")
            return True

        inp = INPUT()
        # SendInput with nInputs=0 is harmless, but some systems require a real check:
        n = user32.SendInput(0, ctypes.byref(inp), ctypes.sizeof(INPUT))
        if n == 0:
            logging.debug("SendInput test returned 0 -> legacy True")
            return True

    except Exception as e:
        logging.debug(f"is_legacy_windows: exception -> legacy True ({e})")
        return True

    return False

def ensure_dpi_aware(user32) -> None:
    """Enable DPI awareness if supported, to ensure correct coordinates.
    """
    try:
        user32.SetProcessDPIAware()
        logging.debug("DPI awareness enabled for current process.")
    except AttributeError:
        logging.debug("DPI awareness not supported on this Windows version.")

def send_input(user32, input_obj: INPUT) -> bool:
    """Send one INPUT via SendInput.
    Return True on success (SendInput returned 1), False on failure.
    Caller must perform fallback if necessary.
    """
    n = user32.SendInput(1, ctypes.byref(input_obj), ctypes.sizeof(INPUT))
    is_success: bool = (n == 1)
    return is_success

def get_last_error(kernel32) -> int:
    """Cross-platform safe wrapper for Win32 GetLastError().

    Returns:
        The last-error code (int), or 0 if not available.
    """
    last_error: int = 0

    # Preferred on real Windows with use_last_error=True
    if hasattr(ctypes, "get_last_error"):
        last_error = ctypes.get_last_error()

    # Fallback: try kernel32 if available (stub returns 0)
    elif hasattr(kernel32, "GetLastError"):
        with contextlib.suppress(Exception):
            last_error = kernel32.GetLastError()

    return last_error
