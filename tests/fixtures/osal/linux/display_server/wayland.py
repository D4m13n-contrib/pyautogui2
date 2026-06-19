"""Fixtures for Wayland Display Server Part tests.

Provides pre-configured OSAL instances with mocked evdev backend.
Compositor variant doesn't matter here since we're testing Wayland DS Part.
"""

import pytest

from tests.fixtures.osal.linux.osal_builder import clean_linux_osal_ctx


@pytest.fixture
def isolated_linux_wayland(isolated_linux):
    """Mock evdev, DBus."""
    import sys

    original_modules = {
        "evdev": sys.modules.get("evdev"),
        "evdev.ecodes": sys.modules.get("evdev.ecodes"),
        "dbus": sys.modules.get("dbus"),
    }

    # Mock evdev
    from tests.mocks.osal.linux.mock_evdev import MockEcodes, MockEvdev

    mock_evdev = MockEvdev()
    mock_ecodes = MockEcodes()
    sys.modules["evdev"] = mock_evdev
    sys.modules["evdev.ecodes"] = mock_ecodes

    # Mock DBus
    from tests.mocks.osal.linux.mock_dbus import MockDBus

    mock_dbus = MockDBus()
    sys.modules["dbus"] = mock_dbus

    isolated_linux._mocks |= {
        "mock_evdev": mock_evdev,
        "mock_ecodes": mock_ecodes,
        "mock_dbus": mock_dbus,
    }

    try:
        yield isolated_linux
    finally:
        # Restore modules
        for key, value in original_modules.items():
            sys.modules[key] = value


@pytest.fixture
def linux_ds_wayland_pointer(isolated_linux_wayland, isolated_lib_mouseinfo):
    """LinuxPointer with Wayland Display Server (mocked evdev).

    Returns:
        LinuxPointer: Fully composed pointer with Wayland DS part.
    """
    from pyautogui2.osal.linux.display_servers.wayland import _make_wayland_part
    from pyautogui2.osal.linux.display_servers.wayland.pointer import WaylandPointerPart
    from tests.mocks.osal.linux.mock_parts import (
        MockBasePointerPart,
        MockDEPointerPart,
        MockWaylandCompositorPointerPart,
    )

    wayland_with_compositor = _make_wayland_part(
        WaylandPointerPart, MockWaylandCompositorPointerPart
    )
    cls_parts = [MockBasePointerPart, MockDEPointerPart, wayland_with_compositor]
    libs = {
        "mouseinfo": isolated_lib_mouseinfo,
    }

    with clean_linux_osal_ctx(
        "pointer", cls_parts, isolated_linux_wayland._mocks | libs
    ) as pointer:
        yield pointer


@pytest.fixture
def linux_ds_wayland_keyboard(isolated_linux_wayland):
    """LinuxKeyboard with Wayland Display Server (mocked evdev).

    Returns:
        LinuxKeyboard: Fully composed keyboard with Wayland DS part.
    """
    from pyautogui2.osal.linux.display_servers.wayland import _make_wayland_part
    from pyautogui2.osal.linux.display_servers.wayland.keyboard import WaylandKeyboardPart
    from tests.mocks.osal.linux.mock_parts import (
        MockBaseKeyboardPart,
        MockDEKeyboardPart,
        MockWaylandCompositorKeyboardPart,
    )

    wayland_with_compositor = _make_wayland_part(
        WaylandKeyboardPart, MockWaylandCompositorKeyboardPart
    )
    cls_parts = [MockBaseKeyboardPart, MockDEKeyboardPart, wayland_with_compositor]

    with clean_linux_osal_ctx("keyboard", cls_parts, isolated_linux_wayland._mocks) as keyboard:
        yield keyboard


@pytest.fixture
def linux_ds_wayland_screen(
    isolated_linux_wayland, isolated_lib_pyscreeze, isolated_lib_pygetwindow, isolated_lib_gi
):
    """LinuxScreen with Wayland Display Server (mocked evdev).

    Returns:
        LinuxScreen: Fully composed screen with Wayland DS part.
    """
    from pyautogui2.osal.linux.display_servers.wayland import _make_wayland_part
    from pyautogui2.osal.linux.display_servers.wayland.screen import WaylandScreenPart
    from tests.mocks.osal.linux.mock_parts import (
        MockBaseScreenPart,
        MockDEScreenPart,
        MockWaylandCompositorScreenPart,
    )

    wayland_with_compositor = _make_wayland_part(WaylandScreenPart, MockWaylandCompositorScreenPart)
    cls_parts = [MockBaseScreenPart, MockDEScreenPart, wayland_with_compositor]
    libs = {
        "pyscreeze": isolated_lib_pyscreeze,
        "pygetwindow": isolated_lib_pygetwindow,
        "gi": isolated_lib_gi,
    }

    with clean_linux_osal_ctx("screen", cls_parts, isolated_linux_wayland._mocks | libs) as screen:
        yield screen


@pytest.fixture
def linux_ds_wayland_dialogs(isolated_linux_wayland, isolated_lib_pymsgbox):
    """LinuxDialogs with Wayland Display Server (mocked evdev).

    Returns:
        LinuxDialogs: Fully composed dialogs with Wayland DS part.
    """
    from pyautogui2.osal.linux.display_servers.wayland import _make_wayland_part
    from pyautogui2.osal.linux.display_servers.wayland.dialogs import WaylandDialogsPart
    from tests.mocks.osal.linux.mock_parts import (
        MockBaseDialogsPart,
        MockDEDialogsPart,
        MockWaylandCompositorDialogsPart,
    )

    wayland_with_compositor = _make_wayland_part(
        WaylandDialogsPart, MockWaylandCompositorDialogsPart
    )
    cls_parts = [MockBaseDialogsPart, MockDEDialogsPart, wayland_with_compositor]
    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_linux_osal_ctx(
        "dialogs", cls_parts, isolated_linux_wayland._mocks | libs
    ) as dialogs:
        yield dialogs
