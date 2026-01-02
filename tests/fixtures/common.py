"""Common fixtures available to all tests.

This module provides base fixtures used across different test suites:
- Environment isolation (sys.platform, os.environ)
- Settings management (PAUSE, FAILSAFE)
- PyAutoGUI factory for custom instances
"""
import contextlib
import os

from itertools import chain

import pytest


@pytest.fixture()
def isolated_environment():
    """Isolated environment for a single test.

    Saves and restores:
        - os.environ: Environment variables

    Ensures tests don't pollute each other's environment.
    Uses function scope to guarantee isolation between tests.

    Yields:
        None: Context manager for test execution

    Example:
        def test_linux_specific(isolated_test_environment):
            os.environ["XXX"] = "value"
            # Test runs environment variable "XXX"
            # After test: original environment variables restored
    """
    # Save original state
    original_environ = os.environ.copy()

    # Set test mode
    os.environ["PYAUTOGUI_ENV"] = "testing"

    yield

    # Restore original state
    os.environ.clear()
    os.environ.update(original_environ)


@pytest.fixture()
def isolated_settings():
    """Isolated PyAutoGUI settings with automatic cleanup.

    Saves and restores settings values.
    Deactivates FAILSAFE, LOG_SCREENSHOTS, and PAUSE mecanisms.

    Yields:
        None: Context manager for test execution
    """
    import pyautogui2.settings as _settings

    # Save settings
    original_settings = {k:v for k,v in _settings.__dict__.items() if k == k.upper()}

    # Modify settings for tests
    data = {
        "FAILSAFE": False,
        "LOG_SCREENSHOTS": False,
        "PAUSE_DEBUG": False,
        "PAUSE_CONTROLLER_DURATION": 0.0,
        "PAUSE_OSAL_DURATION": 0.0,
    }
    for key, value in data.items():
        setattr(_settings, key, value)

    yield _settings

    # Restore settings
    for key, value in original_settings.items():
        setattr(_settings, key, value)


@pytest.fixture
def isolated_lazy_import():
    """Clear all lazy-loaded instance caches.

    This ensures that after mocking sys.modules, lazy descriptors
    will re-import from sys.modules instead of using stale caches.

    Auto-discovers all OSAL instances with lazy-loaded attributes.
    """
    from pyautogui2.utils.lazy_import import LazyImportDescriptor

    for instance in chain(LazyImportDescriptor._instance_registry):
        keys = [k for k in instance.__dict__ if k.startswith('_lazy_')]
        for k in keys:
            with contextlib.suppress(AttributeError):
                delattr(instance, k)

    try:
        yield
    finally:
        # No restoration needed: instances will re-import on next access
        pass


@pytest.fixture
def isolated_singleton():
    from pyautogui2.utils.singleton import Singleton

    Singleton._instances.clear()
    try:
        yield
    finally:
        Singleton._instances.clear()


@pytest.fixture(scope="function", autouse=True)
def isolated_test(isolated_environment, isolated_settings,
                  isolated_singleton, isolated_lazy_import):
    try:
        yield
    finally:
        pass


__all__ = [
    "isolated_environment",
    "isolated_settings",
    "isolated_lazy_import",
    "isolated_singleton",
    "isolated_test",
]
