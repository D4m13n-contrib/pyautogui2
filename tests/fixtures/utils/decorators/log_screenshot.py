"""Pytest fixtures for LogScreenshotManager utils tests."""
from contextlib import contextmanager

import pytest


@contextmanager
def clean_log_screenshot_manager():
    """Context manager for clean PauseManager state."""
    from pyautogui2.utils.decorators.log_screenshot import LogScreenshotManager

    manager = LogScreenshotManager()

    try:
        yield manager
    finally:
        pass


@pytest.fixture
def log_screenshot_manager_mocked(tmp_path, isolated_settings):
    """LogScreenshotManager instance for each test."""
    from tests.mocks.lib.mock_pyscreeze import MockPyscreeze

    with clean_log_screenshot_manager() as manager:
        # Mock screenshot function
        manager.set_screenshot_func(MockPyscreeze().screenshot)

        original_settings = {
            "LOG_SCREENSHOTS": getattr(isolated_settings, "LOG_SCREENSHOTS", None),
            "LOG_SCREENSHOTS_FOLDER": getattr(isolated_settings, "LOG_SCREENSHOTS_FOLDER", None),
        }

        # Activate LOG_SCREENSHOTS by default
        isolated_settings.LOG_SCREENSHOTS = True

        # Define a temporary screenshots folder
        folder = tmp_path / "screenshots"
        isolated_settings.LOG_SCREENSHOTS_FOLDER = str(folder)

        manager._mocks = {
            "log_screenshots_path": folder,
        }

        try:
            yield manager
        finally:
            # Restore
            for k,v in original_settings.items():
                setattr(isolated_settings, k, v)


@pytest.fixture
def log_screenshot_manager_real():
    """Fresh LogScreenshotManager instance for each test."""
    with clean_log_screenshot_manager() as manager:
        yield manager


__all__ = [
    "log_screenshot_manager_mocked",
    "log_screenshot_manager_real",
]
