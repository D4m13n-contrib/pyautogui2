"""Pytest helpers for tests."""
import os
import pytest

from pyautogui2.controllers.pointer import PointerController

from pyautogui2.osal.platform_info import get_platform_info


# ==========
# Detect OS
# ==========
def is_linux():
    """Check if running on Linux."""
    return get_platform_info().get("os_id") == "linux"


def is_windows():
    """Check if running on Windows."""
    return get_platform_info().get("os_id") == "win32"


def is_macos():
    """Check if running on MacOS (Darwin)."""
    return get_platform_info().get("os_id") == "darwin"


# ============================
# Detect Linux Display Server
# ============================
def is_linux_ds_x11():
    """Check if running X11 display server."""
    return is_linux() and get_platform_info().get("linux_display_server") == "x11"


def is_linux_ds_wayland():
    """Check if running Wayland display server."""
    return is_linux() and get_platform_info().get("linux_display_server") == "wayland"


# ========================
# Detect Linux Compositor
# ========================
def is_linux_wayland_compositor_gnome_shell():
    """Check if running Wayland GNOME Shell compositor."""
    return is_linux_ds_wayland() and get_platform_info().get("linux_compositor") == "gnome_shell"

def is_linux_wayland_compositor_kwin():
    """Check if running Wayland KWin compositor."""
    return is_linux_ds_wayland() and get_platform_info().get("linux_compositor") == "kwin"


# =================================
# Detect Linux Desktop Environment
# =================================
def is_linux_de_cinnamon():
    """Check if running Cinnamon desktop environment."""
    return is_linux() and get_platform_info().get("linux_desktop") == "cinnamon"


def is_linux_de_gnome():
    """Check if running GNOME desktop environment."""
    return is_linux() and get_platform_info().get("linux_desktop") == "gnome"


def is_linux_de_kde():
    """Check if running KDE desktop environment."""
    return is_linux() and get_platform_info().get("linux_desktop") == "kde"


def is_linux_de_mate():
    """Check if running MATE desktop environment."""
    return is_linux() and get_platform_info().get("linux_desktop") == "mate"


def is_linux_de_xfce():
    """Check if running XFCE desktop environment."""
    return is_linux() and get_platform_info().get("linux_desktop") == "xfce"


# ===============================
# Detect XIM compatibility
# ===============================
def is_xim_compatible() -> bool:
    """Check if an XIM-compatible input method is active."""
    if is_linux():
        return "@im=" in os.environ.get("XMODIFIERS", "")
    return True


# =====================
# Unavailable features
# =====================
def skip_if_no_get_position(pointer: PointerController) -> None:
    """Skip the test if get_position() is not available on this platform."""
    try:
        pointer.get_position()
    except NotImplementedError:
        pytest.skip("get_position() not available on this platform")

def skip_if_no_screenshot() -> None:
    """Skip the test if screenshots are not supported by pyscreeze library.
    For now, platforms do not support screenshots are:
      - KDE/Wayland (need to use "spectacle" application).
    """
    unsupported_platforms = [
        is_linux_ds_wayland() and is_linux_de_kde(),
    ]

    if any(unsupported_platforms):
        pytest.skip("screenshot() not available on this platform")
