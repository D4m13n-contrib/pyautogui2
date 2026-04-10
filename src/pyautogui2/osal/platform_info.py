#!/usr/bin/env python3
"""Detect and display current platform information for PyAutoGUI2."""

import os
import platform
import subprocess
import sys


def get_linux_info() -> dict[str, str]:
    """Linux-specific."""
    if not sys.platform.startswith("linux"):
        return {}

    def _get_compositor() -> str:
        compositors = {
            "gnome-shell": "gnome_shell",
            "kwin_wayland": "kwin",
            "sway": "sway",
            "weston": "weston",
            "wayfire": "wayfire",
            "hyprland": "hyprland",
            "river": "river",
        }

        for proc_name, compositor_name in compositors.items():
            result = subprocess.run(["pgrep", "-x", proc_name], capture_output=True)
            if result.returncode == 0:
                return compositor_name
        return "unknown"

    display_env = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()

    # Get Desktop Environment, in lower case, then :
    # - Remove prefix "x-" (e.g. "X-Cinnamon" => "cinnamon")
    # - Split on ":" and get the last part (e.g. "ubuntu:GNOME" => "gnome")
    desktop_env = (
        os.environ.get("XDG_SESSION_DESKTOP")
        or os.environ.get("XDG_CURRENT_DESKTOP")
        or os.environ.get("DESKTOP_SESSION")
        or "unknown"
    ).lower().removeprefix("x-").split(":")[-1]
    # Converts specific Desktop Environment to standrad name (e.g. "xubuntu" => "xfce")
    de_fallback = {
        "xubuntu": "xfce",
    }
    if desktop_env in de_fallback:
        desktop_env = de_fallback[desktop_env]

    return {
        "linux_display_server": display_env,
        "linux_desktop": desktop_env,
        "linux_compositor": _get_compositor(),
    }


def get_win32_info() -> dict[str, str]:
    """Windows-specific."""
    if not sys.platform.startswith("win32"):
        return {}

    return {    # type: ignore[unreachable]
        "win32_version": platform.win32_ver()[0],
        "win32_edition": platform.win32_edition(),
    }


def get_darwin_info() -> dict[str, str]:
    """MacOS-specific."""
    if not sys.platform.startswith("darwin"):
        return {}

    return {    # type: ignore[unreachable]
        "darwin_version": platform.mac_ver()[0],
    }


def get_platform_info() -> dict[str, str]:
    """Gather platform information."""
    info = {
        "os": platform.system(),
        "os_id": sys.platform,
        "os_release": platform.release(),
        "python_version": platform.python_version(),
        "architecture": platform.machine(),
    }

    d = {
        "linux": get_linux_info,
        "win32": get_win32_info,
        "darwin": get_darwin_info,
    }

    for platform_name, func_info in d.items():
        if info["os_id"].startswith(platform_name):
            info.update(func_info())
            break

    return info


def main():
    """Print platform information (entrypoint for CLI)."""
    print("PyAutoGUI Platform Detection")
    print("=" * 50)

    info = get_platform_info()
    labels = {
        "os": "OS",
        "os_id": "OS Identifier",
        "os_release": "OS Release",
        "python_version": "Python Version",
        "architecture": "Architecture",
        "linux_display_server": "Display Server",
        "linux_desktop": "Desktop Environment",
        "linux_compositor": "Compositor",
        "win32_version": "Windows Version",
        "win32_edition": "Windows Edition",
        "darwin_version": "MacOS Version",
    }
    max_key_len = max(len(labels.get(k, k)) for k in info)

    for key, value in info.items():
        print(f"{labels.get(key, key):<{max_key_len}} : {value}")

    print("=" * 50)


if __name__ == "__main__":
    main()
