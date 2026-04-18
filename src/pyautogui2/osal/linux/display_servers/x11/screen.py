"""X11ScreenPart - Display server part for all Linux screens."""
import os

from typing import TYPE_CHECKING, Any, Optional

from .....utils.exceptions import PyAutoGUIException
from .....utils.lazy_import import lazy_import
from .....utils.types import Size
from ....abstract_cls import AbstractScreen


if TYPE_CHECKING:
    from PIL import Image


class X11ScreenPart(AbstractScreen):
    """X11 display server screen implementation.

    Provides X11-specific implementations for screen dimension queries using
    the Xlib library. All other screen operations (screenshots, window management,
    image recognition) are inherited from LinuxScreenPart.

    Implementation Notes:
        - Uses python-xlib to query X11 display dimensions directly
        - Removes default decorators from get_size() and get_size_max() to
          provide X11-native implementations without overhead
        - Lazy loads Xlib to avoid dependency issues on non-X11 systems
    """

    _pyscreeze = lazy_import("pyscreeze")
    _xlib = lazy_import("Xlib")
    _xlib_display = lazy_import("Xlib.display")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._display: Optional[Any] = None

    def setup_postinit(self, *args, **kwargs) -> None:
        """Initialize X11 display connection.

        Raises:
            PyAutoGUIException: If cannot connect to X server.
        """
        super().setup_postinit(*args, **kwargs)

        self._display = self._xlib_display.Display(os.environ['DISPLAY'])
        if self._display is None:
           raise PyAutoGUIException("Error: Cannot obtain Display")

    def _take_screenshot(self) -> "Image.Image":
        pyscreeze = self._pyscreeze
        img: Image.Image = pyscreeze.screenshot()
        return img

    def get_size(self) -> Size:
        """Get the size of the primary X11 screen.

        Queries the X11 display server directly using python-xlib to retrieve
        the dimensions of the default screen.

        Returns:
            Size: Named tuple (width, height) in pixels.

        Implementation Notes:
            - Opens a connection to the X11 display
            - Queries the default screen object
            - Returns dimensions from screen.width_in_pixels and height_in_pixels
            - This is an X11-native implementation that bypasses pyscreeze
        """
        assert(self._display is not None), "Error: Display is None"
        return Size(self._display.screen().width_in_pixels,
                    self._display.screen().height_in_pixels)

    def get_size_max(self) -> Size:
        """Get the maximum screen size across all X11 screens.

        For X11, this typically returns the same value as get_size() since
        multi-monitor setups are handled differently than on other platforms.

        Returns:
            Size: Named tuple (width, height) in pixels.

        Implementation Notes:
            - Currently delegates to get_size()
            - X11 multi-monitor handling differs from Windows/MacOS
            - May return combined virtual screen dimensions in some configurations
        """
        return self.get_size()
