"""MacOS-specific pytest fixtures."""
from contextlib import contextmanager
from itertools import chain
from types import SimpleNamespace
from typing import Any, Optional

import pytest


@pytest.fixture
def isolated_macos_environment():
    """Isolated MacOS environment for testing.

    Sets sys.platform = "darwin" and restores it after test.

    Yields:
        None: Context manager for environment isolation
    """
    import sys

    original_platform = sys.platform

    sys.platform = "darwin"

    try:
        yield
    finally:
        sys.platform = original_platform


@pytest.fixture
def mocked_macos_subprocess():
    """Mock subprocess external commands."""
    import subprocess

    original_subprocess = {
        "check_output": subprocess.check_output,
    }

    # Mock subprocess
    from tests.mocks.osal.macos.mock_subprocess import MockSubprocess
    mock_subprocess = MockSubprocess()
    subprocess.check_output = mock_subprocess.check_output

    try:
        yield mock_subprocess
    finally:
        # Restore subprocess
        for key, value in original_subprocess.items():
            setattr(subprocess, key, value)


@pytest.fixture
def isolated_macos(isolated_macos_environment, mocked_macos_subprocess):
    """Complete isolated MacOS test environment with mocked ctypes."""
    import sys

    from tests.mocks.osal.macos.mock_appkit import MockAppKit
    from tests.mocks.osal.macos.mock_launch_services import MockLaunchServices
    from tests.mocks.osal.macos.mock_quartz import MockQuartz

    original_modules = {
        "Quartz": sys.modules.get("Quartz"),
        "AppKit": sys.modules.get("AppKit"),
        "LaunchServices": sys.modules.get("LaunchServices"),
    }

    # Create mocks
    mock_quartz = MockQuartz()
    mock_appkit = MockAppKit()
    mock_launch_services = MockLaunchServices()

    sys.modules["Quartz"] = mock_quartz
    sys.modules["AppKit"] = mock_appkit
    sys.modules["LaunchServices"] = mock_launch_services

    isolated = SimpleNamespace(_mocks={
        "mock_subprocess": mocked_macos_subprocess,
        "mock_quartz": mock_quartz,
        "mock_appkit": mock_appkit,
        "mock_launch_services": mock_launch_services,
    })

    try:
        yield isolated
    finally:
        # Restore modules
        for name, original in original_modules.items():
            sys.modules.pop(name, None)
            if original is not None:
                sys.modules[name] = original


@contextmanager
def clean_macos_osal(osal_cls: type,
                     mocks: Optional[dict[str, Any]] = None, attr_mocks: Optional[dict[str, Any]] = None):
    from pyautogui2.controllers.keyboard import KeyboardController as KC

    mocks = {} if mocks is None else mocks
    attr_mocks = {} if attr_mocks is None else attr_mocks

    osal = osal_cls()

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
def macos_pointer(isolated_macos, isolated_lib_mouseinfo):
    """Provides a real MacOSPointer OSAL instance for tests."""
    from pyautogui2.osal.macos.pointer import MacOSPointer

    libs = {
        "mouseinfo": isolated_lib_mouseinfo,
    }

    with clean_macos_osal(MacOSPointer, isolated_macos._mocks | libs) as pointer:
        yield pointer


@pytest.fixture
def macos_keyboard(isolated_macos):
    """Provides a real MacOSKeyboard OSAL instance for tests."""
    from pyautogui2.osal.macos.keyboard import MacOSKeyboard
    with clean_macos_osal(MacOSKeyboard, isolated_macos._mocks) as keyboard:
        yield keyboard


@pytest.fixture
def macos_screen(isolated_macos, isolated_lib_pyscreeze, isolated_lib_pygetwindow):
    """Provides a real MacOSScreen OSAL instance for tests."""
    from pyautogui2.osal.macos.screen import MacOSScreen

    libs = {
        "pyscreeze": isolated_lib_pyscreeze,
        "pygetwindow": isolated_lib_pygetwindow,
    }

    with clean_macos_osal(MacOSScreen, isolated_macos._mocks | libs) as screen:
        yield screen


@pytest.fixture
def macos_dialogs(isolated_macos, isolated_lib_pymsgbox):
    """Provides a real MacOSDialogs OSAL instance for tests."""
    from pyautogui2.osal.macos.dialogs import MacOSDialogs

    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_macos_osal(MacOSDialogs, isolated_macos._mocks | libs) as dialogs:
        yield dialogs


__all__ = [
    "isolated_macos_environment",
    "mocked_macos_subprocess",
    "isolated_macos",
    "macos_pointer",
    "macos_keyboard",
    "macos_screen",
    "macos_dialogs",
]
