"""Platform auto-detection and backend entry point for PyAutoGUI.

Each supported platform must be implemented as a subpackage of
`pyautogui.platform/` (e.g. `windows/`, `macos/`, `linux/`).

Convention:
-----------
- Each platform subpackage (`windows`, `macos`, `linux`, ...) must expose
  a function `get_osal()` returning a `OSAL`.
"""
from importlib import import_module

from .abstract_cls import OSAL
from .platform_info import get_platform_info


def get_osal() -> OSAL:
    """Get the OSAL of the current OS."""
    os_id = get_platform_info()["os_id"]
    backends = {
        "darwin": "macos",
        "linux": "linux",
        "win32": "windows",
    }

    if os_id not in backends:
        raise RuntimeError(f"Unsupported OS: {os_id}")

    mod = import_module(f".{backends[os_id]}", __package__)
    result: OSAL = mod.get_osal()
    return result
