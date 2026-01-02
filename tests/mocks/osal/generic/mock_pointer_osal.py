"""Generic mock for PointerOSAL (OS-agnostic).

This module provides a mock implementation of PointerOSAL that can be used
for testing without requiring OS-specific dependencies.
"""

from unittest.mock import MagicMock

from pyautogui2.osal.abstract_cls import AbstractPointer
from pyautogui2.utils.decorators import DEFAULTS as DECORATORS_TO_REMOVE
from pyautogui2.utils.types import ButtonName, Point

from .base import MockOSALBase


class MockPointerOSAL(AbstractPointer, MockOSALBase):
    """Mock PointerOSAL for testing controllers without OS-specific code.

    Uses unittest.mock.MagicMock for automatic call tracking.
    Only implements methods that need state management (e.g., position tracking).

    Attributes:
        _position: Current pointer position (Point).
        mouse_info: MagicMock wrapping mouse_info implementation.
        get_primary_button: MagicMock wrapping get_primary_button implementation.
        get_pos: MagicMock wrapping get_pos implementation.
        move_to: MagicMock wrapping move_to implementation.
        drag_to: MagicMock wrapping drag_to implementation.
        button_down: MagicMock wrapping button_down implementation.
        button_up: MagicMock wrapping button_up implementation.
        scroll: MagicMock wrapping scroll implementation.

    Example:
        >>> mock = MockPointerOSAL()
        >>> mock.click(100, 200)

        # Verify with MagicMock API
        >>> mock.click.assert_called_once_with(100, 200, clicks=1, interval=0.0, button="left")

        # Check position was updated
        >>> assert mock.position() == Point(100, 200)

        # Check multiple calls
        >>> mock.move_to(500, 300)
        >>> assert mock.move_to.call_count == 1
        >>> assert mock.position() == Point(500, 300)
    """

    __abstractmethod_remove_decorators__ = {
        "get_primary_button": DECORATORS_TO_REMOVE,
        "get_pos": DECORATORS_TO_REMOVE,    # Required to avoid RecursionError
    }

    # Method stubs to satisfy AbstractPointer
    def mouse_info(self, *a, **kw): pass
    def get_primary_button(self, *a, **kw): pass
    def get_pos(self, *a, **kw): pass
    def move_to(self, *a, **kw): pass
    def drag_to(self, *a, **kw): pass
    def button_down(self, *a, **kw): pass
    def button_up(self, *a, **kw): pass
    def scroll(self, *a, **kw): pass

    def __init__(self):
        """Initialize mock with position tracking at (10, 10)."""
        AbstractPointer.__init__(self)
        MockOSALBase.__init__(self)

        self._position = Point(10, 10)

        def temp():
            print(">>>>>>> GET_POS")
            import traceback
            traceback.print_stack()
            print("<<<<<<< GET_POS")
            return self._position

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "mouse_info": {},
            "get_primary_button": {"return_value":ButtonName.LEFT},
            "get_pos": {"side_effect":lambda: self._position},
            #"get_pos": {"side_effect":temp},
            "move_to": {"side_effect":self._move_to_impl},
            "drag_to": {"side_effect":self._drag_to_impl},
            "button_down": {},
            "button_up": {},
            "scroll": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)

    def mock_set_position(self, x: int, y: int) -> None:
        self._position = Point(x, y)

    # ========================================================================
    # Implementation methods (called by MagicMock.side_effect)
    # ========================================================================

    def _move_to_impl(self, x: int, y: int, **kwargs) -> None:
        self._position = Point(x, y)

    def _drag_to_impl(self, x: int, y: int, button: ButtonName, **kwargs) -> None:
        self._position = Point(x, y)


__all__ = ["MockPointerOSAL"]

