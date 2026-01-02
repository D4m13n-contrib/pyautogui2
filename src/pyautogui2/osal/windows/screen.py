"""WindowsScreen."""
import ctypes
import functools

from ctypes import wintypes

from ...utils.exceptions import ImageNotFoundException
from ...utils.lazy_import import lazy_import, lazy_load_object
from ...utils.types import Size
from ..abstract_cls import AbstractScreen
from ._common import MONITORINFO, RECT, ensure_dpi_aware, get_last_error


class WindowsScreen(AbstractScreen):
    """Common Windows-specific screen logic."""

    _pyscreeze = lazy_import("pyscreeze")
    _pygetwindow = lazy_import("pygetwindow")

    _user32 = lazy_load_object("user32", lambda: ctypes.WinDLL("user32", use_last_error=True))
    _kernel32 = lazy_load_object("kernel32", lambda: ctypes.WinDLL("kernel32", use_last_error=True))

    def setup_postinit(self, *args, **kwargs) -> None:
        """Implementation Notes:
        - Configures pyscreeze to use `ImageNotFoundException`.
        - Enables DPI awareness for the current process if supported.
        - Ensures APIs like `GetMonitorInfoW` and `EnumDisplayMonitors`
          return true pixel sizes instead of logical (scaled) coordinates.
        - Safe to call multiple times (ignored on unsupported systems like XP).
        """
        super().setup_postinit(*args, **kwargs)

        pyscreeze = self._pyscreeze
        setattr(pyscreeze, 'USE_IMAGE_NOT_FOUND_EXCEPTION', True)   # noqa: B010

        ensure_dpi_aware(self._kernel32)

    @staticmethod
    def _wrap_pyscreeze(wrapped_function):
        """A decorator that wraps PyScreeze's methods.

        Wraps:
          - PyAutoGUI argument name (snake_case) into PyScreeze argument name (camelCase).
          - PyScreeze's ImageNotFoundException into PyAutoGUI's ImageNotFoundException.
        """
        arg_names_case = {
            "needle_image": "needleImage",
            "haystack_image": "haystackImage",
            "min_search_time": "minSearchTime",
            "image_path": "imageFilename",
            "expected_color": "expectedRGBColor",
        }

        @functools.wraps(wrapped_function)
        def wrapper(self, *args, **kwargs):
            for arg_name, pyscreeze_arg_name in arg_names_case.items():
                if arg_name in kwargs:
                    kwargs[pyscreeze_arg_name] = kwargs[arg_name]
                    del kwargs[arg_name]

            pyscreeze = self._pyscreeze
            try:
                return wrapped_function(self, *args, **kwargs)
            except pyscreeze.ImageNotFoundException as e:
                raise ImageNotFoundException() from e

        return wrapper

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
        """Implementation Notes:
        - Uses `EnumDisplayMonitors` to enumerate all monitors.
        - Uses `GetMonitorInfo` to get monitor dimensions.
        """
        monitors = []

        def _callback(_hmonitor, _hdc, lprc, _lparam):
            r = lprc.contents
            monitors.append((r.left, r.top, r.right, r.bottom))
            return 1  # Continue enumeration

        monitor_enum_proc = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(RECT),
            wintypes.LPARAM,
        )

        if not self._user32.EnumDisplayMonitors(None, None, monitor_enum_proc(_callback), 0):
            err = get_last_error(self._kernel32)
            raise OSError(f"EnumDisplayMonitors failed (error={err})")

        if not monitors:
            raise RuntimeError("No monitors detected")

        left = min(r[0] for r in monitors)
        top = min(r[1] for r in monitors)
        right = max(r[2] for r in monitors)
        bottom = max(r[3] for r in monitors)

        return Size(right - left, bottom - top)

    def get_size(self) -> Size:
        """The 'primary' display is determined by the system (where the taskbar
        is located, by default).
        """
        monitor = self._user32.MonitorFromWindow(
            self._user32.GetDesktopWindow(), 1  # MONITOR_DEFAULTTOPRIMARY
        )
        info = MONITORINFO(cbSize=ctypes.sizeof(MONITORINFO))
        if not self._user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            err = get_last_error(self._kernel32)
            raise OSError(f"GetMonitorInfoW failed (error={err})")

        rect = info.rcMonitor
        return Size(rect.right - rect.left, rect.bottom - rect.top)

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
