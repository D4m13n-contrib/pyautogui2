"""Pytest helpers for tests."""


from pyautogui2.osal.platform_info import get_platform_info


def is_linux():
    """Check if running on Linux."""
    return get_platform_info().get("os_id") == "linux"


def is_windows():
    """Check if running on Windows."""
    return get_platform_info().get("os_id") == "win32"


def is_macos():
    """Check if running on MacOS (Darwin)."""
    return get_platform_info().get("os_id") == "darwin"


def is_linux_ds_x11():
    """Check if running X11 display server."""
    return is_linux() and get_platform_info().get("linux_display_server") == "x11"


def is_linux_ds_wayland():
    """Check if running Wayland display server."""
    return is_linux() and get_platform_info().get("linux_display_server") == "wayland"


def is_linux_compositor_gnome_shell():
    """Check if running Wayland GNOME Shell compositor."""
    return is_linux_ds_wayland() and get_platform_info().get("linux_compositor") == "gnome_shell"


def is_linux_de_gnome():
    """Check if running GNOME desktop environment."""
    return is_linux() and get_platform_info().get("linux_desktop") == "gnome"
