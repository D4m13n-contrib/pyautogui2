"""X11PointerPart - Display server part for all Linux pointers."""
import os

from typing import Any, Optional

#from Xlib import X
#from Xlib.display import Display
#from Xlib.ext.xtest import fake_input
from .....utils.exceptions import PyAutoGUIException
from .....utils.lazy_import import lazy_import
from .....utils.types import ButtonName, Point
from ....abstract_cls import AbstractPointer


class X11PointerPart(AbstractPointer):
    """X11 display server pointer implementation using native Xlib bindings.

    Provides low-level pointer control via direct X11 protocol communication
    through python-xlib. Handles position queries, movement, button clicks,
    and scrolling using X11 events.

    Implementation Notes:
        - Uses python-xlib for all X server communication.
        - Requires X11 display connection (DISPLAY environment variable).
        - Button operations emit X11 ButtonPress/ButtonRelease events.
        - Scrolling uses X11 button 4/5 (vertical) and 6/7 (horizontal).
        - Lazy initialization of X display connection.

    Dependencies:
        - python-xlib (Xlib package).
        - X11 display server running.
    """

    _xlib = lazy_import("Xlib")

    BUTTON_NAME_MAPPING = {
        ButtonName.LEFT:      1,
        ButtonName.MIDDLE:    2,
        ButtonName.RIGHT:     3,
        ButtonName.PRIMARY:   None,      # set in setup_postinit()
        ButtonName.SECONDARY: None,      # set in setup_postinit()
    }

    def __init__(self, *args, **kwargs):
        """Initialize X11 pointer without establishing display connection.

        Defers X11 display connection until first use (lazy initialization).
        Connection is established in setup_postinit() when display is available.
        """
        super().__init__(*args, **kwargs)

        self._display: Optional[Any] = None

    def setup_postinit(self, *args, **kwargs):
        """Establish X11 display connection and query button mapping.

        Connects to the X server via $DISPLAY environment variable and retrieves
        the current pointer button mapping to respect user's left-handed configuration.

        Implementation Notes:
            - Creates Xlib Display object (stored in self._display).
            - Queries get_pointer_mapping() for button configuration.
            - Stores root window reference for event operations.
            - Called automatically by OSAL initialization system.

        Raises:
            Xlib.error.DisplayConnectionError: If cannot connect to X server.
        """
        super().setup_postinit(*args, **kwargs)

        self._display = self._xlib.display.Display(os.environ['DISPLAY'])
        if self._display is None:
           raise PyAutoGUIException("Error: Cannot obtain Display")

        if self.get_primary_button() == ButtonName.LEFT:
            self.BUTTON_NAME_MAPPING[ButtonName.PRIMARY] = self.BUTTON_NAME_MAPPING[ButtonName.LEFT]
            self.BUTTON_NAME_MAPPING[ButtonName.SECONDARY] = self.BUTTON_NAME_MAPPING[ButtonName.RIGHT]
        else:
            self.BUTTON_NAME_MAPPING[ButtonName.PRIMARY] = self.BUTTON_NAME_MAPPING[ButtonName.RIGHT]
            self.BUTTON_NAME_MAPPING[ButtonName.SECONDARY] = self.BUTTON_NAME_MAPPING[ButtonName.LEFT]

    def get_pos(self) -> Point:
        """Implementation Notes:
        - Uses Xlib query_pointer() on root window.
        - Returns root_x, root_y (absolute screen coordinates).
        - Works across all monitors in multi-monitor setups.
        """
        assert(self._display is not None), "Error: Display is None"
        ptr = self._display.screen().root.query_pointer()
        return Point(int(ptr.root_x), int(ptr.root_y))

    def move_to(self, x: int, y: int, **_kwargs: Any) -> None:
        """Implementation Notes:
            - Uses Xlib warp_pointer() with root window as destination.
            - Flushes display after warp to ensure immediate update.
            - No animation or interpolation (instant jump).
            - Coordinates relative to virtual screen origin.

        Raises:
            PyAutoGUIException: If x or y is None.
        """
        if x is None or y is None:
            raise PyAutoGUIException(f"Error: x/y values (x:{x}, y:{y}) are required")

        assert(self._display is not None), "Error: Display is None"

        self._xlib.ext.xtest.fake_input(self._display, self._xlib.X.MotionNotify, x=x, y=y)
        self._display.sync()

    @AbstractPointer.button_decorator
    def button_down(self, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Uses Xlib fake_input(ButtonPress, button_code).
        - Respects button mapping from get_pointer_mapping().
        - Flushes display to ensure immediate event delivery.
        - Decorated with @AbstractPointer.button_decorator.
        """
        assert(self._display is not None), "Error: Display is None"
        self._xlib.ext.xtest.fake_input(self._display, self._xlib.X.ButtonPress, self.BUTTON_NAME_MAPPING[button])
        self._display.sync()

    @AbstractPointer.button_decorator
    def button_up(self, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Uses Xlib fake_input(ButtonRelease, button_code).
        - Respects button mapping from get_pointer_mapping().
        - Flushes display to ensure immediate event delivery.
        - Decorated with @AbstractPointer.button_decorator.
        """
        assert(self._display is not None), "Error: Display is None"
        self._xlib.ext.xtest.fake_input(self._display, self._xlib.X.ButtonRelease, self.BUTTON_NAME_MAPPING[button])
        self._display.sync()

    def scroll(self, dx: Optional[int] = None, dy: Optional[int] = None, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Vertical: button 4 (up) and 5 (down).
        - Horizontal: button 6 (left) and 7 (right).
        - Each scroll unit triggers one button press+release pair.
        - Uses nested _do_scroll() helper for button event generation.
        """
        def _do_scroll(button):
            assert(self._display is not None), "Error: Display is None"
            self._xlib.ext.xtest.fake_input(self._display, self._xlib.X.ButtonPress, button)
            self._xlib.ext.xtest.fake_input(self._display, self._xlib.X.ButtonRelease, button)
            self._display.sync()

        if dy is not None and dy != 0:
            button = 4 if dy > 0 else 5     # scroll up (4) / scroll down (5)
            for _ in range(abs(dy)):
                _do_scroll(button)

        if dx is not None and dx != 0:
            button = 7 if dx > 0 else 6     # scroll right (7) / scroll left (6)
            for _ in range(abs(dx)):
                _do_scroll(button)
