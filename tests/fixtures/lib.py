"""Fixtures for Mocked external libraries (PyScreeze, PyMsgBox, etc.)."""

import pytest


@pytest.fixture
def isolated_lib_pyscreeze():
    """Mock PyScreeze."""
    import sys

    original_modules = {
        "pyscreeze": sys.modules.get("pyscreeze"),
    }

    # Mock MockPyscreeze
    from tests.mocks.lib.mock_pyscreeze import MockPyscreeze
    mock = MockPyscreeze()
    sys.modules["pyscreeze"] = mock

    try:
        yield mock
    finally:
        # Restore modules
        for key, value in original_modules.items():
            sys.modules[key] = value


@pytest.fixture
def isolated_lib_pymsgbox():
    """Mock PyMsgBox."""
    import sys

    original_modules = {
        "pymsgbox": sys.modules.get("pymsgbox"),
    }

    # Mock MockPyMsgBox
    from tests.mocks.lib.mock_pymsgbox import MockPyMsgBox
    mock = MockPyMsgBox()
    sys.modules["pymsgbox"] = mock

    try:
        yield mock
    finally:
        # Restore modules
        for key, value in original_modules.items():
            sys.modules[key] = value


@pytest.fixture
def isolated_lib_pygetwindow():
    """Mock PyGetWindow."""
    import sys

    original_modules = {
        "pygetwindow": sys.modules.get("pygetwindow"),
    }

    # Mock MockPyGetWindow
    from tests.mocks.lib.mock_pygetwindow import MockPyGetWindow
    mock = MockPyGetWindow()
    sys.modules["pygetwindow"] = mock

    try:
        yield mock
    finally:
        # Restore modules
        for key, value in original_modules.items():
            sys.modules[key] = value


@pytest.fixture
def isolated_lib_mouseinfo():
    """Mock MouseInfo."""
    import sys

    original_modules = {
        "mouseinfo": sys.modules.get("mouseinfo"),
    }

    # Mock MockMouseInfo
    from tests.mocks.lib.mock_mouseinfo import MockMouseInfo
    mock = MockMouseInfo()
    sys.modules["mouseinfo"] = mock

    try:
        yield mock
    finally:
        # Restore modules
        for key, value in original_modules.items():
            sys.modules[key] = value


__all__ = [
    "isolated_lib_pyscreeze",
    "isolated_lib_pymsgbox",
    "isolated_lib_pygetwindow",
    "isolated_lib_mouseinfo",
]
