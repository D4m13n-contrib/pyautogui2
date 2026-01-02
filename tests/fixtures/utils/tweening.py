"""Pytest fixtures for TweeningManager utils tests."""
from contextlib import contextmanager
from unittest.mock import patch

import pytest


@contextmanager
def clean_tweening_manager():
    """Context manager for clean TweeningManager state."""
    from pyautogui2.utils.tweening import TweeningManager

    manager = TweeningManager()

    try:
        yield manager
    finally:
        for k in manager._AVAILABLE_TWEENS:
            manager._AVAILABLE_TWEENS[k] = None


@pytest.fixture
def tweening_manager_mocked():
    """TweeningManager with pytweening available."""
    from tests.mocks.lib.mock_pytweening import MockPytweening

    with patch('pyautogui2.utils.tweening.import_module') as mock_import:
        mock_import.return_value = MockPytweening()
        with clean_tweening_manager() as manager:
            yield manager


@pytest.fixture
def tweening_manager_mocked_no_pytweening():
    """TweeningManager with pytweening NOT available (degraded mode)."""
    with patch('pyautogui2.utils.tweening.import_module') as mock_import:
        mock_import.side_effect = ModuleNotFoundError("No module named 'pytweening'")
        with clean_tweening_manager() as manager:
            yield manager


@pytest.fixture
def tweening_manager_real():
    """Fresh TweeningManager instance (real pytweening if available)."""
    with clean_tweening_manager() as manager:
        yield manager


__all__ = [
    "tweening_manager_mocked",
    "tweening_manager_mocked_no_pytweening",
    "tweening_manager_real",
]
