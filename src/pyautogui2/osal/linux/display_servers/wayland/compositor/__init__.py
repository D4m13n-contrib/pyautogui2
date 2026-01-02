"""Wayland Compositor OSAL loader.

This module detects the active Wayland compositor (backend) such as GNOME Shell,
and make compositor-specific parts.
"""
from typing import Any

from pyautogui2.osal.platform_info import get_linux_info


def get_wayland_compositor_osal_parts() -> dict[str, type[Any]]:
    """Return all OSAL parts for Wayland Compositor.

    Returns:
        A dictionary mapping OSAL component names to their composed classes, e.g.:
        {
            "pointer": GnomeShellPointerPart,
            "keyboard": GnomeShellKeyboardPart,
            ...
        }
    """
    compositor = get_linux_info()["linux_compositor"]

    if compositor == "gnome_shell":
        from .gnome_shell import get_gnome_shell_osal_parts as _get_compositor_parts
    else:
        raise RuntimeError(f"Unsupported Wayland compositor: {compositor}")

    return _get_compositor_parts()
