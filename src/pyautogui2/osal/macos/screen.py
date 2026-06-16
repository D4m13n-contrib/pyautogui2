"""MacOSScreen."""

from ...utils.lazy_import import lazy_import
from ...utils.types import Size
from ..abstract_cls import AbstractScreen, _wrap_pyscreeze


class MacOSScreen(AbstractScreen):
    """Common MacOS-specific screen logic."""

    _quartz = lazy_import("Quartz")
    _appkit = lazy_import("AppKit")

    _pyscreeze = lazy_import("pyscreeze")
    _pygetwindow = lazy_import("pygetwindow")

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

    @_wrap_pyscreeze
    def locate_all_on_screen(self, *args, **kwargs):
        pyscreeze = self._pyscreeze
        return pyscreeze.locateAllOnScreen(*args, **kwargs)

    @_wrap_pyscreeze
    def locate_center_on_screen(self, *args, **kwargs):
        pyscreeze = self._pyscreeze
        return pyscreeze.locateCenterOnScreen(*args, **kwargs)

    @_wrap_pyscreeze
    def locate_on_screen(self, *args, **kwargs):
        pyscreeze = self._pyscreeze
        return pyscreeze.locateOnScreen(*args, **kwargs)

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

    @_wrap_pyscreeze
    def screenshot(self, *args, **kwargs):
        pyscreeze = self._pyscreeze
        return pyscreeze.screenshot(*args, **kwargs)

    def get_size_max(self) -> Size:
        out_w, out_h = (0, 0)
        for screen in self._appkit.NSScreen.screens():
            description = screen.deviceDescription()
            pw, ph = description[self._appkit.NSDeviceSize].sizeValue()
            scale_factor = screen.backingScaleFactor()
            out_w += pw * scale_factor
            out_h += ph * scale_factor

        return Size(int(out_w), int(out_h))

    def get_size(self) -> Size:
        w = self._quartz.CGDisplayPixelsWide(self._quartz.CGMainDisplayID())
        h = self._quartz.CGDisplayPixelsHigh(self._quartz.CGMainDisplayID())
        return Size(int(w), int(h))

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
