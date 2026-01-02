"""Pytest fixtures for PauseManager utils tests."""
from contextlib import contextmanager
from unittest.mock import patch

import pytest


@contextmanager
def clean_pause_manager():
    """Context manager for clean PauseManager state."""
    from pyautogui2.utils.decorators.pause import PauseManager

    manager = PauseManager()

    original_manager = {
        "controller_duration": getattr(manager, "controller_duration", None),
        "osal_duration": getattr(manager, "osal_duration", None),
        "debug": getattr(manager, "debug", None),
    }

    try:
        yield manager
    finally:
        # Restore
        for k,v in original_manager.items():
            setattr(manager, k, v)


@pytest.fixture
def pause_manager_mocked():
    """Reset manager after each test."""
    with clean_pause_manager() as manager, patch("time.sleep") as mock_time_sleep:
        manager._mocks = {
            "time_sleep": mock_time_sleep,
        }

        yield manager


@pytest.fixture
def pause_manager_real():
    """Fresh PauseManager instance (real time.sleep)."""
    with clean_pause_manager() as manager:
        yield manager


__all__ = [
    "pause_manager_mocked",
    "pause_manager_real",
]
