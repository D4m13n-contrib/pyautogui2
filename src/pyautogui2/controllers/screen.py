"""ScreenController for PyAutoGUI.

See AbstractScreenController for documentation.
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional, Union

from ..osal.abstract_cls import AbstractScreen
from ..utils.decorators.failsafe import FailsafeManager
from ..utils.decorators.log_screenshot import LogScreenshotManager
from ..utils.exceptions import PyAutoGUIException
from ..utils.types import Box, Point, Size
from .abstract_cls import AbstractScreenController


if TYPE_CHECKING:
    from PIL import Image


class ScreenController(AbstractScreenController):
    """Concrete implementation of screen and window controller.

    This implementation delegates most operations to the OSAL layer, but adds
    important initialization logic for failsafe and screenshot features.
    See AbstractScreenController for detailed method documentation.

    Implementation Notes:
        - Registers screen corners as failsafe trigger points during setup
        - Provides screenshot capability to LogScreenshotManager
        - Pure OSAL delegation for all screen/window operations
    """

    def __init__(self, osal: AbstractScreen, *args, **kwargs):
        """Store OSAL backend reference for screen operations.

        Args:
            osal: Platform-specific screen OSAL implementation.
            *args: List arguments (internal usage).
            **kwargs: Keyword arguments (internal usage).

        Raises:
            ValueError: If osal is not an AbstractScreen subclass.

        Implementation Notes:
            - Validates OSAL type at instantiation
        """
        super().__init__(*args, **kwargs)

        if not isinstance(osal, AbstractScreen):
            raise PyAutoGUIException(f"Error: '{osal}' should be a subclass of AbstractScreen")
        self._osal = osal

    def setup_postinit(self, *args, **kwargs):
        """Initialize screen controller and register global features.

        This method performs critical setup operations:

        1. **Failsafe trigger points**: Registers all four screen corners as
           failsafe trigger points. Moving the pointer to any corner will
           trigger failsafe exception if enabled.

        2. **Screenshot provider**: Registers this controller's screenshot()
           method with LogScreenshotManager, enabling automatic screenshot
           capture on errors.

        Implementation Details:
            - Corners are calculated as: (0,0), (width-1,0), (0,height-1), (width-1,height-1)
            - Corner coordinates use (width-1, height-1) to stay within screen bounds
            - Must be called after controller_manager is available

        Warning:
            This method must be called during initialization for failsafe and
            screenshot features to work correctly.
        """
        super().setup_postinit(*args, **kwargs)  # No-op but maintains inheritance chain
        self._osal.setup_postinit(*args, **kwargs)

        # Add corners to FailsafeManager trigger points
        right, bottom = self.get_size_max()
        corners = [(0,          0), (right - 1,          0),
                   (0, bottom - 1), (right - 1, bottom - 1)]
        for corner in corners:
            FailsafeManager().add_trigger_point(corner)

        # Add screenshot function to LogScreenshotManager
        LogScreenshotManager().set_screenshot_func(self.screenshot)

    def locate(self,
               needle_image: Union[str, "Image.Image"],
               haystack_image: Union[str, "Image.Image"],
               **kwargs: Any) -> Optional[Box]:
        location = self._osal.locate(needle_image, haystack_image, **kwargs)
        if location:
            return Box(*location)
        return None

    def locate_all(self,
                   needle_image: Union[str, "Image.Image"],
                   haystack_image: Union[str, "Image.Image"],
                   **kwargs: Any) -> Iterable[Box]:
        locations = self._osal.locate_all(needle_image, haystack_image, **kwargs)
        if locations:
            return [Box(*location) for location in locations]
        return []

    def locate_all_on_screen(self,
                             image: Union[str, "Image.Image"],
                             **kwargs: Any) -> Iterable[Box]:
        locations = self._osal.locate_all_on_screen(image, **kwargs)
        if locations:
            return [Box(*location) for location in locations]
        return []

    def locate_center_on_screen(self,
                                image: Union[str, "Image.Image"],
                                **kwargs: Any) -> Optional[Point]:
        point = self._osal.locate_center_on_screen(image, **kwargs)
        if point:
            return Point(*point)
        return None

    def locate_on_screen(self,
                         image: Union[str, "Image.Image"],
                         min_search_time: int = 0,
                         **kwargs: Any) -> Optional[Box]:
        location = self._osal.locate_on_screen(image, min_search_time, **kwargs)
        if location:
            return Box(*location)
        return None

    def locate_on_window(self,
                         image: Union[str, "Image.Image"],
                         title: str,
                         **kwargs: Any) -> Optional[Box]:
        location = self._osal.locate_on_window(image, title, **kwargs)
        if location:
            return Box(*location)
        return None

    def center(self, region: Box, **_kwargs: Any) -> Point:
        point = self._osal.center(region)
        return Point(*point)

    def pixel(self, x: int, y: int, **_kwargs: Any) -> tuple[int, int, int]:
        return self._osal.pixel(x, y)

    def pixel_matches_color(self,
                            x: int, y: int,
                            expected_color: tuple[int, int, int],
                            tolerance: int = 0,
                            **kwargs: Any) -> bool:
        return self._osal.pixel_matches_color(x, y, expected_color, tolerance, **kwargs)

    def screenshot(self,
                   image_path: Optional[str] = None,
                   region: Optional[Box] = None,
                   **kwargs: Any) -> "Image.Image":
        return self._osal.screenshot(image_path, region, **kwargs)

    def get_size_max(self, **_kwargs: Any) -> Size:
        size = self._osal.get_size_max()
        return Size(*size)

    def get_size(self, **_kwargs: Any) -> Size:
        size = self._osal.get_size()
        return Size(*size)

    def window(self, handle: Any) -> Optional[Any]:
        return self._osal.window(handle)

    def get_active_window(self, **_kwargs: Any) -> Optional[Any]:
        return self._osal.get_active_window()

    def get_active_window_title(self, **_kwargs: Any) -> str:
        return self._osal.get_active_window_title()

    def get_windows_at(self, x: int, y: int, **_kwargs: Any) -> list:
        return self._osal.get_windows_at(x, y)

    def get_windows_with_title(self, title: str, **_kwargs: Any) -> list:
        return self._osal.get_windows_with_title(title)

    def get_all_windows(self, **_kwargs: Any) -> list:
        return self._osal.get_all_windows()

    def get_all_titles(self, **_kwargs: Any) -> list:
        return self._osal.get_all_titles()
