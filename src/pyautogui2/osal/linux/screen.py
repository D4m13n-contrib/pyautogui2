"""LinuxScreenPart - Base part for all Linux screens."""

from typing import TYPE_CHECKING, Optional

from ...utils.exceptions import PyAutoGUIException
from ...utils.lazy_import import lazy_import
from ...utils.types import Box
from ..abstract_cls import AbstractScreen, _wrap_pyscreeze


if TYPE_CHECKING:
    from PIL import Image


class LinuxScreenPart(AbstractScreen):
    """Common Linux-specific screen logic shared across desktops and display servers.

    Delegates most screen operations to the pyscreeze and pygetwindow libraries,
    which provide cross-platform screen capture and window management capabilities.
    This base implementation is inherited by all Linux desktop and display server
    combinations.

    Implementation Notes:
        - Uses pyscreeze for screenshots and image recognition (locate functions)
        - Uses pygetwindow for window management operations
        - Desktop/display server Parts typically only override get_size() and
          get_size_max() for platform-specific screen dimension queries
        - Lazy loading of dependencies to avoid import overhead
    """

    _pyscreeze = lazy_import("pyscreeze")
    _pygetwindow = lazy_import("pygetwindow")   # TODO: Not supported on Linux

    def setup_postinit(self, *args, **kwargs) -> None:
        """Implementation Notes:
        - Configures pyscreeze to use `ImageNotFoundException`.
        """
        super().setup_postinit(*args, **kwargs)

        pyscreeze = self._pyscreeze
        pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = True  # type: ignore[attr-defined]

    @_wrap_pyscreeze
    def locate(self, *args, **kwargs):
        pyscreeze = self._pyscreeze
        return pyscreeze.locate(*args, **kwargs)

    @_wrap_pyscreeze
    def locate_all(self, *args, **kwargs):
        pyscreeze = self._pyscreeze
        return pyscreeze.locateAll(*args, **kwargs)

    def locate_all_on_screen(self, *args, **kwargs):
        haystack = self.screenshot()
        return self.locate_all(*args, haystack=haystack, **kwargs)

    def locate_center_on_screen(self, *args, **kwargs):
        found = self.locate_on_screen(*args, **kwargs)
        return self.center(found)

    def locate_on_screen(self, *args, **kwargs):
        haystack = self.screenshot()
        return self.locate(*args, haystack=haystack, **kwargs)

    @_wrap_pyscreeze
    def locate_on_window(self, *args, **kwargs):
        pyscreeze = self._pyscreeze
        return pyscreeze.locateOnWindow(*args, **kwargs)

    @_wrap_pyscreeze
    def center(self, *args, **kwargs):
        pyscreeze = self._pyscreeze
        return pyscreeze.center(*args, **kwargs)

    @_wrap_pyscreeze
    def pixel(self, *args, **kwargs):
        pyscreeze = self._pyscreeze
        return pyscreeze.pixel(*args, **kwargs)

    @_wrap_pyscreeze
    def pixel_matches_color(self, *args, **kwargs):
        pyscreeze = self._pyscreeze
        return pyscreeze.pixelMatchesColor(*args, **kwargs)

    def screenshot(self,
                   image_filename: Optional[str] = None,
                   region: Optional[Box] = None) -> "Image.Image":
        try:
            img: Image.Image = self._take_screenshot()  # type: ignore[attr-defined]  # should be provided by DS Part
        except AttributeError as exc:
            raise PyAutoGUIException(
                "No display server implementation found for _take_screenshot(). "
                "Ensure your display server part defines this method."
            ) from exc

        if region is not None:
            left, top, width, height = region
            img = img.crop((left, top, left + width, top + height))

        if image_filename is not None:
            img.save(image_filename)

        return img

    def window(self, *args, **kwargs):
        pygetwindow = self._pygetwindow
        return pygetwindow.Window(*args, **kwargs)

    def get_active_window(self, *args, **kwargs):
        pygetwindow = self._pygetwindow
        return pygetwindow.getActiveWindow(*args, **kwargs)

    def get_active_window_title(self, *args, **kwargs):
        pygetwindow = self._pygetwindow
        return pygetwindow.getActiveWindowTitle(*args, **kwargs)

    def get_windows_at(self, *args, **kwargs):
        pygetwindow = self._pygetwindow
        return pygetwindow.getWindowAt(*args, **kwargs)

    def get_windows_with_title(self, *args, **kwargs):
        pygetwindow = self._pygetwindow
        return pygetwindow.getWindowsWithTitle(*args, **kwargs)

    def get_all_windows(self, *args, **kwargs):
        pygetwindow = self._pygetwindow
        return pygetwindow.getAllWindows(*args, **kwargs)

    def get_all_titles(self, *args, **kwargs):
        pygetwindow = self._pygetwindow
        return pygetwindow.getAllTitles(*args, **kwargs)
