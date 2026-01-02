"""Generic mock for ScreenOSAL (OS-agnostic).

This module provides a mock implementation of ScreenOSAL that can be used
for testing without requiring OS-specific dependencies.
"""
from typing import Optional
from unittest.mock import MagicMock

from PIL import Image

from pyautogui2.osal.abstract_cls import AbstractScreen
from pyautogui2.utils.types import Box, Point, Size

from .base import MockOSALBase


class MockScreenOSAL(AbstractScreen, MockOSALBase):
    """Mock ScreenOSAL for testing controllers without OS-specific code.

    Uses unittest.mock.MagicMock for automatic call tracking.
    Allows configuring screen size for testing different resolutions.

    Attributes:
        _size: Current screen size (Size).
        locate: MagicMock wrapping locate implementation.
        locate_all: MagicMock wrapping locate_all implementation.
        locate_all_on_screen: MagicMock wrapping locate_all_on_screen implementation.
        locate_center_on_screen: MagicMock wrapping locate_center_on_screen implementation.
        locate_on_screen: MagicMock wrapping locate_on_screen implementation.
        locate_on_window: MagicMock wrapping locate_on_window implementation.
        center: MagicMock wrapping center implementation.
        pixel: MagicMock wrapping pixel implementation.
        pixel_matches_color: MagicMock wrapping pixel_matches_color implementation.
        screenshot: MagicMock wrapping screenshot implementation.
        get_size_max: MagicMock wrapping get_size_max implementation.
        get_size: MagicMock wrapping get_size implementation.
        window: MagicMock wrapping window implementation.
        get_active_window: MagicMock wrapping get_active_window implementation.
        get_active_window_title: MagicMock wrapping get_active_window_title implementation.
        get_windows_at: MagicMock wrapping get_windows_at implementation.
        get_windows_with_title: MagicMock wrapping get_windows_with_title implementation.
        get_all_windows: MagicMock wrapping get_all_windows implementation.
        get_all_titles: MagicMock wrapping get_all_titles implementation.

    Example:
        >>> mock = MockScreenOSAL(width=1920, height=1080)
        >>> size = mock.get_size()

        # Verify with MagicMock API
        >>> mock.size.assert_called_once()

        # Check result
        >>> assert size == Size(1920, 1080)

        # Change size for testing
        >>> mock.set_size(2560, 1440)
        >>> assert mock.get_size() == Size(2560, 1440)
    """

    # Method stubs to satisfy AbstractScreen
    def locate(self, *a, **kw): pass
    def locate_all(self, *a, **kw): pass
    def locate_all_on_screen(self, *a, **kw): pass
    def locate_center_on_screen(self, *a, **kw): pass
    def locate_on_screen(self, *a, **kw): pass
    def locate_on_window(self, *a, **kw): pass
    def center(self, *a, **kw): pass
    def pixel(self, *a, **kw): pass
    def pixel_matches_color(self, *a, **kw): pass
    def screenshot(self, *a, **kw): pass
    def get_size_max(self, *a, **kw): pass
    def get_size(self, *a, **kw): pass
    def window(self, *a, **kw): pass
    def get_active_window(self, *a, **kw): pass
    def get_active_window_title(self, *a, **kw): pass
    def get_windows_at(self, *a, **kw): pass
    def get_windows_with_title(self, *a, **kw): pass
    def get_all_windows(self, *a, **kw): pass
    def get_all_titles(self, *a, **kw): pass

    def __init__(self, width: int = 1920, height: int = 1080):
        """Initialize mock with default screen size.

        Args:
            width: Screen width in pixels (default: 1920).
            height: Screen height in pixels (default: 1080).

        Note:
            By default, size_max is equal to 2 * screen size.
        """
        AbstractScreen.__init__(self)
        MockOSALBase.__init__(self)

        self._size = Size(width, height)

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "locate": {"return_value":Box(5, 5, 5, 5)},
            "locate_all": {"return_value":[Box(6, 6, 6, 6)]},
            "locate_all_on_screen": {"return_value":[Box(0, 0, 50, 50)]},
            "locate_center_on_screen": {"return_value":Point(25, 25)},
            "locate_on_screen": {"return_value":Box(10, 10, 100, 100)},
            "locate_on_window": {"return_value":Box(20, 20, 200, 200)},
            "center": {"side_effect":lambda rect, **_kw: Point(rect[0] + (rect[2] // 2),
                                                               rect[1] + (rect[3] // 2))},
            "pixel": {"return_value":(10, 20, 30)},
            "pixel_matches_color": {"return_value":True},
            "screenshot": {"side_effect":self._screenshot_impl},
            "get_size_max": {"side_effect":lambda: Size(self._size.width * 2, self._size.height * 2)},
            "get_size": {"side_effect":lambda: self._size},
            "window": {"return_value":MagicMock()},
            "get_active_window": {"return_value":MagicMock()},
            "get_active_window_title": {"return_value":"Window Title"},
            "get_windows_at": {"return_value":[MagicMock()]},
            "get_windows_with_title": {"return_value":[MagicMock()]},
            "get_all_windows": {"return_value":[MagicMock()]},
            "get_all_titles": {"return_value":["Window Title"]},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)

    def mock_set_size(self, width: int, height: int):
        """Set the mocked screen size for testing.

        Useful for testing behavior with different screen resolutions.

        Args:
            width: New screen width in pixels.
            height: New screen height in pixels.

        Example:
            >>> mock = MockScreenOSAL()
            >>> mock.set_size(2560, 1440)
            >>> assert mock.size() == Size(2560, 1440)
        """
        self._size = Size(width, height)

    # ========================================================================
    # Implementation methods (called by MagicMock.side_effect)
    # ========================================================================

    def _screenshot_impl(self,
                         _image_path: Optional[str] = None,
                         region: Optional[Box | tuple] = None,
                         **_kwargs) -> Image:
        """Implementation of screenshot - returns dummy black image.

        Args:
            region: Optional region to capture (Box or tuple with x, y, width, height).
                   If None, captures full screen.

        Returns:
            PIL Image object (black dummy image).
        """
        if region:
            return Image.new("RGB", (region[2], region[3]), color="black")
        return Image.new("RGB", (self._size.width, self._size.height), color="black")


__all__ = ["MockScreenOSAL"]

