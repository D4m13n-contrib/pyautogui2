"""Display server detection layer for Linux.
Detects whether the system is running under Wayland or X11,
and imports the corresponding backend module.
"""
from pyautogui2.osal.platform_info import get_linux_info


def get_display_server_osal_parts() -> dict[str, type]:
    """Get the OSAL display server Part of the current Linux platform."""
    server = get_linux_info()["linux_display_server"]

    if server == "wayland":
        from .wayland import get_wayland_osal_parts as _get_osal_parts
    elif server == "x11":
        from .x11 import get_x11_osal_parts as _get_osal_parts
    else:
        raise RuntimeError(f"Unsupported display server: {server}")

    return _get_osal_parts()
