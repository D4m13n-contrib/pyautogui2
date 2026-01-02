"""Fixtures for Gnome Desktop Environment Part tests.

Provides pre-configured OSAL instances for testing DE-specific behavior.
All fixtures use mocked backends (display server doesn't matter for isolation).
"""

import pytest

from tests.fixtures.osal.linux.osal_builder import clean_linux_osal_ctx


@pytest.fixture
def isolated_linux_gnome(isolated_linux):
    import sys

    original_modules = {
    }

    try:
        yield isolated_linux
    finally:
        # Restore modules
        for key, value in original_modules.items():
            sys.modules[key] = value


@pytest.fixture
def linux_de_gnome_pointer(isolated_linux_gnome, isolated_lib_mouseinfo):
    """LinuxPointer with GNOME Desktop Environment.

    Returns:
        LinuxPointer: Fully composed pointer with Wayland DS part.
    """
    from pyautogui2.osal.linux.desktops.gnome.pointer import GnomePointerPart
    from tests.mocks.osal.linux.mock_parts import MockBasePointerPart, MockDSPointerPart

    cls_parts = [MockBasePointerPart, GnomePointerPart, MockDSPointerPart]
    libs = {
        "mouseinfo": isolated_lib_mouseinfo,
    }

    with clean_linux_osal_ctx("pointer", cls_parts, isolated_linux_gnome._mocks | libs) as pointer:
        yield pointer


@pytest.fixture
def linux_de_gnome_keyboard(isolated_linux_gnome):
    """LinuxKeyboard with GNOME Desktop Environment.

    Returns:
        LinuxKeyboard: Fully composed pointer with Wayland DS part.
    """
    from pyautogui2.osal.linux.desktops.gnome.keyboard import GnomeKeyboardPart
    from tests.mocks.osal.linux.mock_parts import MockBaseKeyboardPart, MockDSKeyboardPart

    cls_parts = [MockBaseKeyboardPart, GnomeKeyboardPart, MockDSKeyboardPart]

    with clean_linux_osal_ctx("keyboard", cls_parts, isolated_linux_gnome._mocks) as keyboard:
        yield keyboard


@pytest.fixture
def linux_de_gnome_screen(isolated_linux_gnome, isolated_lib_pyscreeze, isolated_lib_pygetwindow):
    """LinuxScreen with GNOME Desktop Environment.

    Returns:
        LinuxScreen: Fully composed pointer with Wayland DS part.
    """
    from pyautogui2.osal.linux.desktops.gnome.screen import GnomeScreenPart
    from tests.mocks.osal.linux.mock_parts import MockBaseScreenPart, MockDSScreenPart

    cls_parts = [MockBaseScreenPart, GnomeScreenPart, MockDSScreenPart]
    libs = {
        "pyscreeze": isolated_lib_pyscreeze,
        "pygetwindow": isolated_lib_pygetwindow,
    }

    with clean_linux_osal_ctx("screen", cls_parts, isolated_linux_gnome._mocks | libs) as screen:
        yield screen


@pytest.fixture
def linux_de_gnome_dialogs(isolated_linux_gnome, isolated_lib_pymsgbox):
    """LinuxDialogs with GNOME Desktop Environment.

    Returns:
        LinuxDialogs: Fully composed pointer with Wayland DS part.
    """
    from pyautogui2.osal.linux.desktops.gnome.dialogs import GnomeDialogsPart
    from tests.mocks.osal.linux.mock_parts import MockBaseDialogsPart, MockDSDialogsPart

    cls_parts = [MockBaseDialogsPart, GnomeDialogsPart, MockDSDialogsPart]
    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_linux_osal_ctx("dialogs", cls_parts, isolated_linux_gnome._mocks | libs) as dialogs:
        yield dialogs


__all__ = [
    "isolated_linux_gnome",
    "linux_de_gnome_pointer",
    "linux_de_gnome_keyboard",
    "linux_de_gnome_screen",
    "linux_de_gnome_dialogs",
]
