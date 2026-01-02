"""Generic mock for DialogsOSAL (OS-agnostic).

This module provides a mock implementation of DialogsOSAL that can be used
for testing without requiring OS-specific dependencies.
"""
from unittest.mock import MagicMock

from pyautogui2.osal.abstract_cls import AbstractDialogs

from .base import MockOSALBase


class MockDialogsOSAL(AbstractDialogs, MockOSALBase):
    """Mock DialogsOSAL for testing controllers without OS-specific code.

    Uses unittest.mock.MagicMock for automatic call tracking.

    Attributes:
        alert: MagicMock wrapping alert implementation.
        confirm: MagicMock wrapping confirm implementation.
        prompt: MagicMock wrapping prompt implementation.
        password: MagicMock wrapping password implementation.

    Example:
        >>> mock = MockDialogsOSAL()
        >>> mock.alert('Alert')

        # Verify with MagicMock API
        >>> mock.alert.assert_called_once()
    """

    # Method stubs to satisfy AbstractDialogs
    def alert(self, *a, **kw): pass
    def confirm(self, *a, **kw): pass
    def prompt(self, *a, **kw): pass
    def password(self, *a, **kw): pass

    def __init__(self):
        """Initialize mock."""
        AbstractDialogs.__init__(self)
        MockOSALBase.__init__(self)

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "alert": {"return_value":"Alert Ok"},
            "confirm": {"return_value":"Confirmed"},
            "prompt": {"return_value":"User Input"},
            "password": {"return_value":"P4ssw0rd"},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


__all__ = ["MockDialogsOSAL"]

