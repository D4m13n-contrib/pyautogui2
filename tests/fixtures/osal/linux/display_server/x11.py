"""Fixtures for X11 Display Server Part tests.

Provides pre-configured OSAL instances with mocked Xlib backend.
Desktop environment doesn't matter here (mocked).
"""

import pytest

from tests.fixtures.osal.linux.osal_builder import clean_linux_osal_ctx


@pytest.fixture
def isolated_linux_x11(isolated_linux):
    """Mock Xlib."""
    import sys

    original_modules = {
        "Xlib": sys.modules.get("Xlib"),
        "Xlib.display": sys.modules.get("Xlib.display"),
        "Xlib.X": sys.modules.get("Xlib.X"),
        "Xlib.XK": sys.modules.get("Xlib.XK"),
        "Xlib.ext": sys.modules.get("Xlib.ext"),
        "Xlib.ext.xtest": sys.modules.get("Xlib.ext.xtest"),
    }

    # Mock Xlib
    from tests.mocks.osal.linux.mock_xlib import MockXlib
    mock_xlib = MockXlib()
    sys.modules["Xlib"] = mock_xlib
    sys.modules["Xlib.display"] = mock_xlib.display
    sys.modules["Xlib.X"] = mock_xlib.X
    sys.modules["Xlib.XK"] = mock_xlib.XK
    sys.modules["Xlib.ext"] = mock_xlib.ext
    sys.modules["Xlib.ext.xtest"] = mock_xlib.ext.xtest

    isolated_linux._mocks |= {"mock_xlib": mock_xlib}

    try:
        yield isolated_linux
    finally:
        # Restore modules
        for key, value in original_modules.items():
            sys.modules[key] = value


@pytest.fixture
def linux_ds_x11_pointer(isolated_linux_x11, isolated_lib_mouseinfo):
    """LinuxPointer with X11 Display Server (mocked Xlib).

    Desktop environment is set to 'gnome' but doesn't matter since we're
    testing X11 Display Server Part behavior in isolation.

    Returns:
        LinuxPointer: Fully composed pointer with X11 DS part.
    """
    from pyautogui2.osal.linux.display_servers.x11.pointer import X11PointerPart
    from tests.mocks.osal.linux.mock_parts import MockBasePointerPart, MockDEPointerPart

    cls_parts = [MockBasePointerPart, MockDEPointerPart, X11PointerPart]
    libs = {
        "mouseinfo": isolated_lib_mouseinfo,
    }

    with clean_linux_osal_ctx("pointer", cls_parts, isolated_linux_x11._mocks | libs) as pointer:
        yield pointer


@pytest.fixture
def linux_ds_x11_keyboard(isolated_linux_x11):
    """LinuxKeyboard with X11 Display Server (mocked Xlib).

    Desktop environment is set to 'gnome' but doesn't matter since we're
    testing X11 Display Server Part behavior in isolation.

    Returns:
        LinuxKeyboard: Fully composed keyboard with X11 DS part.
    """
    from pyautogui2.osal.linux.display_servers.x11.keyboard import X11KeyboardPart
    from tests.mocks.osal.linux.mock_parts import MockBaseKeyboardPart, MockDEKeyboardPart

    cls_parts = [MockBaseKeyboardPart, MockDEKeyboardPart, X11KeyboardPart]

    with clean_linux_osal_ctx("keyboard", cls_parts, isolated_linux_x11._mocks) as keyboard:
        yield keyboard


@pytest.fixture
def linux_ds_x11_screen(isolated_linux_x11, isolated_lib_pyscreeze, isolated_lib_pygetwindow):
    """LinuxScreen with X11 Display Server (mocked Xlib).

    Desktop environment is set to 'gnome' but doesn't matter since we're
    testing X11 Display Server Part behavior in isolation.

    Returns:
        LinuxScreen: Fully composed screen with X11 DS part.
    """
    from pyautogui2.osal.linux.display_servers.x11.screen import X11ScreenPart
    from tests.mocks.osal.linux.mock_parts import MockBaseScreenPart, MockDEScreenPart

    cls_parts = [MockBaseScreenPart, MockDEScreenPart, X11ScreenPart]
    libs = {
        "pyscreeze": isolated_lib_pyscreeze,
        "pygetwindow": isolated_lib_pygetwindow,
    }

    with clean_linux_osal_ctx("screen", cls_parts, isolated_linux_x11._mocks | libs) as screen:
        yield screen


@pytest.fixture
def linux_ds_x11_dialogs(isolated_linux_x11, isolated_lib_pymsgbox):
    """LinuxDialogs with X11 Display Server (mocked Xlib).

    Desktop environment is set to 'gnome' but doesn't matter since we're
    testing X11 Display Server Part behavior in isolation.

    Returns:
        LinuxDialogs: Fully composed dialogs with X11 DS part.
    """
    from pyautogui2.osal.linux.display_servers.x11.dialogs import X11DialogsPart
    from tests.mocks.osal.linux.mock_parts import MockBaseDialogsPart, MockDEDialogsPart

    cls_parts = [MockBaseDialogsPart, MockDEDialogsPart, X11DialogsPart]
    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_linux_osal_ctx("dialogs", cls_parts, isolated_linux_x11._mocks | libs) as dialogs:
        yield dialogs


__all__ = [
    "isolated_linux_x11",
    "linux_ds_x11_pointer",
    "linux_ds_x11_keyboard",
    "linux_ds_x11_screen",
    "linux_ds_x11_dialogs",
]
