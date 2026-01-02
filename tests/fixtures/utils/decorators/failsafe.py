"""Pytest fixtures for FailsafeManager utils tests."""
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest


@contextmanager
def clean_failsafe_manager():
    """Context manager for clean FailsafeManager state."""
    from pyautogui2.utils.decorators.failsafe import FailsafeManager

    manager = FailsafeManager()
    manager.reset_to_defaults()

    try:
        yield manager
    finally:
        manager.reset_to_defaults()


@pytest.fixture
def failsafe_manager_mocked():
    """FailsafeManager instance with mock for get_position()."""
    with clean_failsafe_manager() as manager:
        # Add mock for get_position()
        mock_get_pos = MagicMock(return_value=(100, 100))
        manager.register_get_position(mock_get_pos)

        manager._mocks = {
            "get_pos": mock_get_pos
        }

        try:
            yield manager
        finally:
            pass


@pytest.fixture
def failsafe_manager_real():
    """Fresh FailsafeManager instance."""
    with clean_failsafe_manager() as manager:
        yield manager


__all__ = [
    "failsafe_manager_mocked",
    "failsafe_manager_real",
]
