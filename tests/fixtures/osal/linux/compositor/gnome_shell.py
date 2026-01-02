"""Fixtures for GNOME Shell compositor tests.

Provides pre-configured instances of GNOME Shell-specific Parts.
"""
import pytest

from tests.fixtures.osal.linux.osal_builder import clean_linux_osal_ctx
from tests.mocks.osal.linux.mock_backend_gnome_shell import MockGnomeShellBackend


@pytest.fixture
def isolated_gnome_shell(isolated_linux_wayland):
    """Isolated GNOME Shell environment."""
    try:
        yield isolated_linux_wayland
    finally:
        pass


@pytest.fixture
def linux_ds_wayland_co_gnome_shell_pointer(isolated_gnome_shell, isolated_lib_pymsgbox):
    """LinuxPointer with Wayland Display Server and GnomeShell compositor
        (mocked UInput, GnomeShellBackend).

    Returns:
        LinuxPointer: Fully composed pointer with Wayland DS part and GnomeShell compositor.
    """
    from pyautogui2.osal.linux.display_servers.wayland import _make_wayland_part
    from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell.pointer import (
        GnomeShellPointerPart,
    )
    from pyautogui2.osal.linux.display_servers.wayland.pointer import WaylandPointerPart
    from tests.mocks.osal.linux.mock_parts import MockBasePointerPart, MockDEPointerPart

    wayland_with_compositor = _make_wayland_part(WaylandPointerPart, GnomeShellPointerPart)
    cls_parts = [MockBasePointerPart, MockDEPointerPart, wayland_with_compositor]
    attr_mocks = {
        "_backend": MockGnomeShellBackend(),
    }
    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_linux_osal_ctx("pointer", cls_parts, isolated_gnome_shell._mocks | libs, attr_mocks) as pointer:
        yield pointer


@pytest.fixture
def linux_ds_wayland_co_gnome_shell_keyboard(isolated_gnome_shell, isolated_lib_pymsgbox):
    """LinuxKeyboard with Wayland Display Server and GnomeShell compositor
        (mocked UInput, GnomeShellBackend).

    Returns:
        LinuxKeyboard: Fully composed keyboard with Wayland DS part and GnomeShell compositor.
    """
    from pyautogui2.osal.linux.display_servers.wayland import _make_wayland_part
    from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell.keyboard import (
        GnomeShellKeyboardPart,
    )
    from pyautogui2.osal.linux.display_servers.wayland.keyboard import WaylandKeyboardPart
    from tests.mocks.osal.linux.mock_parts import MockBaseKeyboardPart, MockDEKeyboardPart

    wayland_with_compositor = _make_wayland_part(WaylandKeyboardPart, GnomeShellKeyboardPart)
    cls_parts = [MockBaseKeyboardPart, MockDEKeyboardPart, wayland_with_compositor]
    attr_mocks = {
        "_backend": MockGnomeShellBackend(),
    }
    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_linux_osal_ctx("keyboard", cls_parts, isolated_gnome_shell._mocks | libs, attr_mocks) as keyboard:
        yield keyboard


@pytest.fixture
def linux_ds_wayland_co_gnome_shell_screen(isolated_gnome_shell, isolated_lib_pymsgbox):
    """LinuxScreen with Wayland Display Server and GnomeShell compositor
        (mocked UInput, GnomeShellBackend).

    Returns:
        LinuxScreen: Fully composed screen with Wayland DS part and GnomeShell compositor.
    """
    from pyautogui2.osal.linux.display_servers.wayland import _make_wayland_part
    from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell.screen import (
        GnomeShellScreenPart,
    )
    from pyautogui2.osal.linux.display_servers.wayland.screen import WaylandScreenPart
    from tests.mocks.osal.linux.mock_parts import MockBaseScreenPart, MockDEScreenPart

    wayland_with_compositor = _make_wayland_part(WaylandScreenPart, GnomeShellScreenPart)
    cls_parts = [MockBaseScreenPart, MockDEScreenPart, wayland_with_compositor]
    attr_mocks = {
        "_backend": MockGnomeShellBackend(),
    }
    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_linux_osal_ctx("screen", cls_parts, isolated_gnome_shell._mocks | libs, attr_mocks) as screen:
        yield screen


@pytest.fixture
def linux_ds_wayland_co_gnome_shell_dialogs(isolated_gnome_shell, isolated_lib_pymsgbox):
    """LinuxDialogs with Wayland Display Server and GnomeShell compositor
        (mocked UInput, GnomeShellBackend).

    Returns:
        LinuxDialogs: Fully composed dialogs with Wayland DS part and GnomeShell compositor.
    """
    from pyautogui2.osal.linux.display_servers.wayland import _make_wayland_part
    from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell.dialogs import (
        GnomeShellDialogsPart,
    )
    from pyautogui2.osal.linux.display_servers.wayland.dialogs import WaylandDialogsPart
    from tests.mocks.osal.linux.mock_parts import MockBaseDialogsPart, MockDEDialogsPart

    wayland_with_compositor = _make_wayland_part(WaylandDialogsPart, GnomeShellDialogsPart)
    cls_parts = [MockBaseDialogsPart, MockDEDialogsPart, wayland_with_compositor]
    attr_mocks = {
        "_backend": MockGnomeShellBackend(),
    }
    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_linux_osal_ctx("dialogs", cls_parts, isolated_gnome_shell._mocks | libs, attr_mocks) as dialogs:
        yield dialogs


__all__ = [
    "isolated_gnome_shell",
    "linux_ds_wayland_co_gnome_shell_pointer",
    "linux_ds_wayland_co_gnome_shell_keyboard",
    "linux_ds_wayland_co_gnome_shell_screen",
    "linux_ds_wayland_co_gnome_shell_dialogs",
]
