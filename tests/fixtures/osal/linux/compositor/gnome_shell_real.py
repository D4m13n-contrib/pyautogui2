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


@pytest.fixture
def linux_ds_wayland_backend_real():
    """Alias for gnome_shell_backend_real for Wayland backend tests.

    Provides a real GnomeShellBackend instance for testing backend interface
    methods (get_keyboard_layout, get_pointer_position, get_screen_outputs).
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
    "linux_ds_wayland_backend_real",
]
