"""Generic mock for KeyboardOSAL (OS-agnostic).

This module provides a mock implementation of KeyboardOSAL that can be used
for testing without requiring OS-specific dependencies.
"""
from contextlib import contextmanager
from unittest.mock import MagicMock

from pyautogui2.osal.abstract_cls import AbstractKeyboard

from .base import MockOSALBase


class MockKeyboardOSAL(AbstractKeyboard, MockOSALBase):
    """Mock KeyboardOSAL for testing controllers without OS-specific code.

    Uses unittest.mock.MagicMock for automatic call tracking.
    Tracks pressed keys for is_pressed() state management.

    Attributes:
        get_layout: MagicMock wrapping get_layout implementation.
        key_is_mapped: MagicMock wrapping key_is_mapped implementation.
        key_down: MagicMock wrapping key_down implementation.
        key_up: MagicMock wrapping key_up implementation.
        codepoint_ctx: MagicMock wrapping codepoint_ctx implementation.

    Example:
        >>> mock = MockKeyboardOSAL()
        >>> mock.key_down("a")

        # Verify with MagicMock API
        >>> mock.key_down.assert_called_once_with("a")
    """

    # Method stubs to satisfy AbstractKeyboard
    def get_layout(self, **kw): pass
    def key_is_mapped(self, *a, **kw): pass
    def key_down(self, *a, **kw): pass
    def key_up(self, *a, **kw): pass

    def __init__(self):
        """Initialize mock."""
        AbstractKeyboard.__init__(self)
        MockOSALBase.__init__(self)

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "get_layout": {"return_value":"QWERTY"},
            "key_is_mapped": {"return_value":True},
            "key_down": {},
            "key_up": {},
            # Register codepoint type_codepoint_value tracking (for verification)
            # Note: codepoint_ctx is NOT registered because it's a real method
            # that returns a context manager, not a MagicMock
            "type_codepoint_value": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)

    # ========================================================================
    # Implementation methods (called by MagicMock.side_effect)
    # ========================================================================

    @contextmanager
    def codepoint_ctx(self, *_args, **_kwargs):
        """Provide a mock context manager for codepoint writing.

        This context manager yields a mock context object with a type_codepoint_value()
        method. The type_codepoint_value() method is tracked via self.mock_type_codepoint_value
        so tests can verify it was called correctly.

        Yields:
            MagicMock: Context object with type_codepoint_value() method.
                      Calls are tracked in self.mock_type_codepoint_value.

        Example:
            with mock.codepoint_ctx() as ctx:
                ctx.type_codepoint_value(0x41)  # 'A'

            # Verify
            mock.mock_type_codepoint_value.assert_called_once_with(0x41)
        """
        # Create a mock context object
        ctx = MagicMock()

        # Make write() calls delegate to our tracked mock
        ctx.type_codepoint_value = self.type_codepoint_value

        try:
            yield ctx
        finally:
            pass  # No cleanup needed for mock




__all__ = ["MockKeyboardOSAL"]

