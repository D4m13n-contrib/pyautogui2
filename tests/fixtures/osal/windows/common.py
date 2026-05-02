"""Windows-specific pytest fixtures."""
from contextlib import contextmanager
from itertools import chain
from types import SimpleNamespace
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def isolated_windows_environment():
    """Isolated Windows environment for testing.

    Sets sys.platform = "win32" and restores it after test.

    Yields:
        None: Context manager for environment isolation
    """
    import sys

    original_platform = sys.platform

    sys.platform = "win32"

    try:
        yield
    finally:
        sys.platform = original_platform


@pytest.fixture
def isolated_windows(isolated_windows_environment):
    """Complete isolated Windows test environment with mocked ctypes."""
    import importlib
    import sys

    import tests.mocks.osal.windows.mock_ctypes as mock_ctypes

    from tests.mocks.osal.windows.mock_kernel32 import MockKernel32
    from tests.mocks.osal.windows.mock_user32 import MockUser32
    from tests.mocks.osal.windows.mock_winreg import MockWinreg

    original_modules = {
        "kernel32": sys.modules.get("kernel32"),
        "user32": sys.modules.get("user32"),
        "winreg": sys.modules.get("winreg"),
        "ctypes": sys.modules.get("ctypes"),
        "ctypes.wintypes": sys.modules.get("ctypes.wintypes"),
    }

    # Create mocks
    mock_kernel32 = MockKernel32()
    mock_user32 = MockUser32()
    mock_winreg = MockWinreg()

    sys.modules["ctypes"] = mock_ctypes
    sys.modules["ctypes.wintypes"] = mock_ctypes.wintypes
    sys.modules["winreg"] = mock_winreg

    # Install modules for WinDLL()
    sys.modules["kernel32"] = mock_kernel32
    sys.modules["user32"] = mock_user32

    # Create windll namespace
    mock_windll = MagicMock()
    mock_windll.kernel32 = mock_kernel32
    mock_windll.user32 = mock_user32
    mock_ctypes.windll = mock_windll

    # Force reload so all module-level `import ctypes` rebind to our mock
    windows_modules = [
        "pyautogui2.osal.windows._common",
        "pyautogui2.osal.windows.pointer",
        "pyautogui2.osal.windows.keyboard",
        "pyautogui2.osal.windows.screen",
        "pyautogui2.osal.windows.dialogs",
    ]
    for mod_name in windows_modules:
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])

    isolated = SimpleNamespace(_mocks={
        "mock_kernel32": mock_kernel32,
        "mock_user32": mock_user32,
        "mock_winreg": mock_winreg,
        "mock_ctypes": mock_ctypes,
        "mock_windll": mock_windll,
    })

    try:
        yield isolated
    finally:
        # Restore modules
        for name, original in original_modules.items():
            sys.modules.pop(name, None)
            if original is not None:
                sys.modules[name] = original
        # Reload again to restore real ctypes bindings
        for mod_name in windows_modules:
            if mod_name in sys.modules:
                importlib.reload(sys.modules[mod_name])


@contextmanager
def clean_windows_osal(osal_cls: type,
                       mocks: Optional[dict[str, Any]] = None, attr_mocks: Optional[dict[str, Any]] = None):
    from pyautogui2.controllers.keyboard import KeyboardController as KC

    mocks = {} if mocks is None else mocks
    attr_mocks = {} if attr_mocks is None else attr_mocks

    osal = osal_cls()

    osal._legacy_mode = False   # Enforce modern mode

    for attr_name, mock in attr_mocks.items():
        setattr(osal, attr_name, mock)

    setup_kwargs = {
        "screen_size_max": (1920, 1080),
        "key_names": KC.KEY_NAMES,
        "all_keymapping": KC.KEYBOARD_MAPPINGS,
    }
    osal.setup_postinit(**setup_kwargs)

    osal._mocks = mocks

    # Reset setup_postinit() mock calls
    for mock in chain(osal._mocks.values(), attr_mocks.values()):
        if mock is not None:
            mock.reset_mock()

    try:
        yield osal
    finally:
        # Cleanup mocks
        for mock in chain(osal._mocks.values(), attr_mocks.values()):
            if mock is not None:
                mock.reset_mock()


@pytest.fixture
def windows_pointer(isolated_windows, isolated_lib_mouseinfo):
    """Provides a real WindowsPointer OSAL instance for tests."""
    from pyautogui2.osal.windows.pointer import WindowsPointer

    attr_mocks = {
        "_user32": isolated_windows._mocks["mock_user32"],
        "_kernel32": isolated_windows._mocks["mock_kernel32"],
    }

    libs = {
        "mouseinfo": isolated_lib_mouseinfo,
    }

    with clean_windows_osal(WindowsPointer, isolated_windows._mocks | libs, attr_mocks) as pointer:
        yield pointer


@pytest.fixture
def windows_keyboard(isolated_windows):
    """Provides a real WindowsKeyboard OSAL instance for tests."""
    from pyautogui2.osal.windows.keyboard import WindowsKeyboard

    attr_mocks = {
        "_user32": isolated_windows._mocks["mock_user32"],
        "_kernel32": isolated_windows._mocks["mock_kernel32"],
        "_winreg": isolated_windows._mocks["mock_winreg"],
    }

    with clean_windows_osal(WindowsKeyboard, isolated_windows._mocks, attr_mocks) as keyboard:
        yield keyboard


@pytest.fixture
def windows_screen(isolated_windows, isolated_lib_pyscreeze, isolated_lib_pygetwindow):
    """Provides a real WindowsScreen OSAL instance for tests."""
    from pyautogui2.osal.windows.screen import WindowsScreen

    attr_mocks = {
        "_user32": isolated_windows._mocks["mock_user32"],
        "_kernel32": isolated_windows._mocks["mock_kernel32"],
    }

    libs = {
        "pyscreeze": isolated_lib_pyscreeze,
        "pygetwindow": isolated_lib_pygetwindow,
    }

    with clean_windows_osal(WindowsScreen, isolated_windows._mocks | libs, attr_mocks) as screen:
        yield screen


@pytest.fixture
def windows_dialogs(isolated_windows, isolated_lib_pymsgbox):
    """Provides a real WindowsDialogs OSAL instance for tests."""
    from pyautogui2.osal.windows.dialogs import WindowsDialogs

    attr_mocks = {
        "_user32": isolated_windows._mocks["mock_user32"],
        "_kernel32": isolated_windows._mocks["mock_kernel32"],
    }

    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_windows_osal(WindowsDialogs, isolated_windows._mocks | libs, attr_mocks) as dialogs:
        yield dialogs


__all__ = [
    "isolated_windows_environment",
    "isolated_windows",
    "windows_pointer",
    "windows_keyboard",
    "windows_screen",
    "windows_dialogs",
]
