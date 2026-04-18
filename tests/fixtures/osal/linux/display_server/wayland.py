"""Fixtures for Wayland Display Server Part tests.

Provides pre-configured OSAL instances with mocked UInput backend.
Compositor variant doesn't matter here since we're testing Wayland DS Part.
"""

import pytest

from pyautogui2.osal.platform_info import get_linux_info
from tests.fixtures.osal.linux.osal_builder import clean_linux_osal_ctx


@pytest.fixture
def isolated_linux_wayland(isolated_linux):
    """Mock UInput, DBus."""
    import sys

    original_modules = {
        "uinput": sys.modules.get("uinput"),
        "dbus": sys.modules.get("dbus"),
    }

    # Mock UInput
    from tests.mocks.osal.linux.mock_uinput import MockUInput
    mock_uinput = MockUInput
    sys.modules["uinput"] = mock_uinput

    # Mock DBus
    from tests.mocks.osal.linux.mock_dbus import MockDBus
    mock_dbus = MockDBus()
    sys.modules["dbus"] = mock_dbus

    isolated_linux._mocks |= {"mock_uinput": mock_uinput, "mock_dbus": mock_dbus}

    try:
        yield isolated_linux
    finally:
        # Restore modules
        for key, value in original_modules.items():
            sys.modules[key] = value


@pytest.fixture
def linux_ds_wayland_pointer(isolated_linux_wayland, isolated_lib_mouseinfo):
    """LinuxPointer with Wayland Display Server (mocked UInput).

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

    wayland_with_compositor = _make_wayland_part(WaylandPointerPart, MockWaylandCompositorPointerPart)
    cls_parts = [MockBasePointerPart, MockDEPointerPart, wayland_with_compositor]
    libs = {
        "mouseinfo": isolated_lib_mouseinfo,
    }

    with clean_linux_osal_ctx("pointer", cls_parts, isolated_linux_wayland._mocks | libs) as pointer:
        yield pointer


@pytest.fixture
def linux_ds_wayland_keyboard(isolated_linux_wayland):
    """LinuxKeyboard with Wayland Display Server (mocked UInput).

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

    wayland_with_compositor = _make_wayland_part(WaylandKeyboardPart, MockWaylandCompositorKeyboardPart)
    cls_parts = [MockBaseKeyboardPart, MockDEKeyboardPart, wayland_with_compositor]

    with clean_linux_osal_ctx("keyboard", cls_parts, isolated_linux_wayland._mocks) as keyboard:
        yield keyboard


@pytest.fixture
def linux_ds_wayland_screen(isolated_linux_wayland, isolated_lib_pyscreeze, isolated_lib_pygetwindow, isolated_lib_gi):
    """LinuxScreen with Wayland Display Server (mocked UInput).

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
    """LinuxDialogs with Wayland Display Server (mocked UInput).

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

    wayland_with_compositor = _make_wayland_part(WaylandDialogsPart, MockWaylandCompositorDialogsPart)
    cls_parts = [MockBaseDialogsPart, MockDEDialogsPart, wayland_with_compositor]
    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_linux_osal_ctx("dialogs", cls_parts, isolated_linux_wayland._mocks | libs) as dialogs:
        yield dialogs


@pytest.fixture
def linux_ds_wayland_backend_real(isolated_linux_wayland):
    """Current Wayland backend (auto-detected based on compositor).

    Automatically detects the running compositor and delegates to the
    appropriate specific fixture (gnome_shell_backend, etc.).

    Returns:
        Backend instance for the detected compositor.

    Raises:
        pytest.skip: If no backend is implemented for the detected compositor.
    """
    compositor = get_linux_info().get("linux_compositor", "unknown")

    if compositor == "gnome_shell":
        from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell._backend import (
            GnomeShellBackend as BackendCls,
        )
    else:
        pytest.skip(f"No backend implemented for compositor: {compositor}")

    backend = BackendCls()

    try:
        yield backend
    finally:
        if hasattr(backend, "cleanup"):
            backend.cleanup()


__all__ = [
    "isolated_linux_wayland",
    "linux_ds_wayland_pointer",
    "linux_ds_wayland_keyboard",
    "linux_ds_wayland_screen",
    "linux_ds_wayland_dialogs",
    "linux_ds_wayland_backend_real",
]
