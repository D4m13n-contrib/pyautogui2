"""Linux-specific pytest fixtures."""
from types import SimpleNamespace

import pytest

from tests.fixtures.osal.linux.osal_builder import clean_linux_osal_ctx


@pytest.fixture
def isolated_linux_environment():
    """Isolated Linux environment for testing.

    Sets os.environ["DISPLAY"] = ":0" and restores it after test.
    Sets sys.platform = "linux" and restores it after test.
    """
    import os
    import sys

    original_display = os.environ.get("DISPLAY")
    original_platform = sys.platform

    os.environ["DISPLAY"] = ":0"
    sys.platform = "linux"

    try:
        yield
    finally:
        if original_display is None:
            os.unsetenv("DISPLAY")
        else:
            os.environ["DISPLAY"] = original_display
        sys.platform = original_platform


@pytest.fixture
def mocked_linux_subprocess():
    """Mock subprocess external commands."""
    import subprocess

    original_subprocess = {
        "check_output": subprocess.check_output,
        "run": subprocess.run,
        "Popen": subprocess.Popen,
    }

    # Mock subprocess
    from tests.mocks.osal.linux.mock_subprocess import MockSubprocess
    mock_subprocess = MockSubprocess()
    subprocess.check_output = mock_subprocess.check_output
    subprocess.run = mock_subprocess.run
    subprocess.Popen = mock_subprocess.Popen

    try:
        yield mock_subprocess
    finally:
        # Restore subprocess
        for key, value in original_subprocess.items():
            setattr(subprocess, key, value)


@pytest.fixture
def isolated_linux(isolated_linux_environment, mocked_linux_subprocess):
    isolated = SimpleNamespace(_mocks={
        "mock_subprocess": mocked_linux_subprocess,
    })

    try:
        yield isolated
    finally:
        pass


@pytest.fixture
def linux_pointer(isolated_linux, isolated_lib_mouseinfo):
    """LinuxPointer (generic)."""
    from pyautogui2.osal.linux.pointer import LinuxPointerPart
    from tests.mocks.osal.linux.mock_parts import MockDEPointerPart, MockDSPointerPart

    cls_parts = [LinuxPointerPart, MockDEPointerPart, MockDSPointerPart]
    libs = {
        "mouseinfo": isolated_lib_mouseinfo,
    }

    with clean_linux_osal_ctx("pointer", cls_parts, isolated_linux._mocks | libs) as pointer:
        yield pointer


@pytest.fixture
def linux_keyboard(isolated_linux):
    """LinuxKeyboard (generic)."""
    from pyautogui2.osal.linux.keyboard import LinuxKeyboardPart
    from tests.mocks.osal.linux.mock_parts import MockDEKeyboardPart, MockDSKeyboardPart

    cls_parts = [LinuxKeyboardPart, MockDEKeyboardPart, MockDSKeyboardPart]

    with clean_linux_osal_ctx("keyboard", cls_parts, isolated_linux._mocks) as keyboard:
        yield keyboard


@pytest.fixture
def linux_screen(isolated_linux, isolated_lib_pyscreeze, isolated_lib_pygetwindow):
    """LinuxScreen (generic)."""
    from pyautogui2.osal.linux.screen import LinuxScreenPart
    from tests.mocks.osal.linux.mock_parts import MockDEScreenPart, MockDSScreenPart

    cls_parts = [LinuxScreenPart, MockDEScreenPart, MockDSScreenPart]
    libs = {
        "pyscreeze": isolated_lib_pyscreeze,
        "pygetwindow": isolated_lib_pygetwindow,
    }

    with clean_linux_osal_ctx("screen", cls_parts, isolated_linux._mocks | libs) as screen:
        yield screen


@pytest.fixture
def linux_dialogs(isolated_linux, isolated_lib_pymsgbox):
    """LinuxDialogs (generic)."""
    from pyautogui2.osal.linux.dialogs import LinuxDialogsPart
    from tests.mocks.osal.linux.mock_parts import MockDEDialogsPart, MockDSDialogsPart

    cls_parts = [LinuxDialogsPart, MockDEDialogsPart, MockDSDialogsPart]
    libs = {
        "pymsgbox": isolated_lib_pymsgbox,
    }

    with clean_linux_osal_ctx("dialogs", cls_parts, isolated_linux._mocks | libs) as dialogs:
        yield dialogs


__all__ = [
    "isolated_linux_environment",
    "mocked_linux_subprocess",
    "isolated_linux",
    "linux_pointer",
    "linux_keyboard",
    "linux_screen",
    "linux_dialogs",
]
