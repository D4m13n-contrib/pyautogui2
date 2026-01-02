"""Fixtures for GNOME Shell Backend tests.

Provides real backend for GNOME Shell-specific Parts.
"""

import pytest


@pytest.fixture
def gnome_shell_backend_real(isolated_linux_wayland):
    """GnomeShellBackend instance with automatic cleanup.

    Yields:
        GnomeShellBackend: Backend instance for GnomeShell compositor.

    Note:
        Automatically calls cleanup() if the method exists.
    """
    from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell._backend import (
        GnomeShellBackend,
    )

    backend = GnomeShellBackend()

    try:
        yield backend
    finally:
        backend.cleanup()


__all__ = [
    "gnome_shell_backend_real",
]
