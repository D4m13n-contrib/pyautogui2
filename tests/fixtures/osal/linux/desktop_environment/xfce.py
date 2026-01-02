"""Fixtures for XFCE Desktop Environment Part tests.

Provides pre-configured OSAL instances for testing DE-specific behavior.
All fixtures use mocked backends (display server doesn't matter for isolation).
"""

import pytest

from tests.fixtures.osal.linux.osal_builder import clean_linux_osal_ctx


@pytest.fixture
def isolated_linux_xfce(isolated_linux):
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
def linux_de_xfce_pointer(isolated_linux_xfce, isolated_lib_mouseinfo):
    """LinuxPointer with XFCE Desktop Environment.

    Returns:
        LinuxPointer: Fully composed pointer with Wayland DS part.
    """
    from pyautogui2.osal.linux.desktops.xfce.pointer import XfcePointerPart
    from tests.mocks.osal.linux.mock_parts import MockBasePointerPart, MockDSPointerPart

    cls_parts = [MockBasePointerPart, XfcePointerPart, MockDSPointerPart]
    libs = {
        "mouseinfo": isolated_lib_mouseinfo,
    }

    with clean_linux_osal_ctx("pointer", cls_parts, isolated_linux_xfce._mocks | libs) as pointer:
        yield pointer


@pytest.fixture
def linux_de_xfce_keyboard(isolated_linux_xfce):
    """LinuxKeyboard with XFCE Desktop Environment.

    Returns:
        LinuxKeyboard: Fully composed pointer with Wayland DS part.
    """
    from pyautogui2.osal.linux.desktops.xfce.keyboard import XfceKeyboardPart
    from tests.mocks.osal.linux.mock_parts import MockBaseKeyboardPart, MockDSKeyboardPart

    cls_parts = [MockBaseKeyboardPart, XfceKeyboardPart, MockDSKeyboardPart]

    with clean_linux_osal_ctx("keyboard", cls_parts, isolated_linux_xfce._mocks) as keyboard:
        yield keyboard


@pytest.fixture
def linux_de_xfce_screen(isolated_linux_xfce, isolated_lib_pyscreeze, isolated_lib_pygetwindow):
    """LinuxScreen with XFCE Desktop Environment.

    Returns:
        LinuxScreen: Fully composed pointer with Wayland DS part.
    """
    from pyautogui2.osal.linux.desktops.xfce.screen import XfceScreenPart
    from tests.mocks.osal.linux.mock_parts import MockBaseScreenPart, MockDSScreenPart

    cls_parts = [MockBaseScreenPart, XfceScreenPart, MockDSScreenPart]
    libs = {
        "pyscreeze": isolated_lib_pyscreeze,
        "pygetwindow": isolated_lib_pygetwindow,
    }

    with clean_linux_osal_ctx("screen", cls_parts, isolated_linux_xfce._mocks | libs) as screen:
        yield screen


@pytest.fixture
def linux_de_xfce_dialogs(isolated_linux_xfce, isolated_lib_pymsgbox):
    """LinuxDialogs with XFCE Desktop Environment.

    Returns:
        LinuxDialogs: Fully composed pointer with Wayland DS part.
    """
    from pyautogui2.osal.linux.desktops.xfce.dialogs import XfceDialogsPart
    from tests.mocks.osal.linux.mock_parts import MockBaseDialogsPart, MockDSDialogsPart

    cls_parts = [MockBaseDialogsPart, XfceDialogsPart, MockDSDialogsPart]
    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_linux_osal_ctx("dialogs", cls_parts, isolated_linux_xfce._mocks | libs) as dialogs:
        yield dialogs


__all__ = [
    "isolated_linux_xfce",
    "linux_de_xfce_pointer",
    "linux_de_xfce_keyboard",
    "linux_de_xfce_screen",
    "linux_de_xfce_dialogs",
]
