"""Tests for WindowsScreen."""

from types import SimpleNamespace

import pytest

from pyautogui2.utils.exceptions import ImageNotFoundException


class TestWindowsScreenDelegatesToPyScreeze:
    """Tests for methods delegates to pyscreeze."""

    def test_locate_delegate(self, windows_screen):
        """Call locate() delegates to pyscreeze library."""
        windows_screen.locate()
        windows_screen._mocks["pyscreeze"].locate.assert_called_once()

    def test_locate_all_delegate(self, windows_screen):
        """Call locate_all() delegates to pyscreeze library."""
        windows_screen.locate_all()
        windows_screen._mocks["pyscreeze"].locateAll.assert_called_once()

    def test_locate_all_on_screen_delegate(self, windows_screen):
        """Call locate_all_on_screen() delegates to pyscreeze library."""
        windows_screen.locate_all_on_screen()
        windows_screen._mocks["pyscreeze"].locateAllOnScreen.assert_called_once()

    def test_locate_center_on_screen_delegate(self, windows_screen):
        """Call locate_center_on_screen() delegates to pyscreeze library."""
        windows_screen.locate_center_on_screen()
        windows_screen._mocks["pyscreeze"].locateCenterOnScreen.assert_called_once()

    def test_locate_on_screen_delegate(self, windows_screen):
        """Call locate_on_screen() delegates to pyscreeze library."""
        windows_screen.locate_on_screen()
        windows_screen._mocks["pyscreeze"].locateOnScreen.assert_called_once()

    def test_locate_on_window_delegate(self, windows_screen):
        """Call locate_on_window() delegates to pyscreeze library."""
        windows_screen.locate_on_window()
        windows_screen._mocks["pyscreeze"].locateOnWindow.assert_called_once()

    def test_center_delegate(self, windows_screen):
        """Call center() delegates to pyscreeze library."""
        windows_screen.center((10, 20, 100, 200))
        windows_screen._mocks["pyscreeze"].center.assert_called_once()

    def test_pixel_delegate(self, windows_screen):
        """Call pixel() delegates to pyscreeze library."""
        windows_screen.pixel()
        windows_screen._mocks["pyscreeze"].pixel.assert_called_once()

    def test_pixel_matches_color_delegate(self, windows_screen):
        """Call pixel_matches_color() delegates to pyscreeze library."""
        windows_screen.pixel_matches_color()
        windows_screen._mocks["pyscreeze"].pixelMatchesColor.assert_called_once()

    def test_screenshot_delegate(self, windows_screen):
        """Call screenshot() delegates to pyscreeze library."""
        windows_screen.screenshot()
        windows_screen._mocks["pyscreeze"].screenshot.assert_called_once()

    @pytest.mark.parametrize("test_case", [
        SimpleNamespace(func_name="locate",
                        func_name_lib="locate",
                        input_kwargs={"needle_image": "a.png", "haystack_image": "b.png"},
                        expected_kwargs={"needleImage": "a.png", "haystackImage": "b.png"},
        ),
        SimpleNamespace(func_name="locate_all",
                        func_name_lib="locateAll",
                        input_kwargs={"needle_image": "a.png", "haystack_image": "b.png"},
                        expected_kwargs={"needleImage": "a.png", "haystackImage": "b.png"},
        ),
        SimpleNamespace(func_name="locate_all_on_screen",
                        func_name_lib="locateAllOnScreen",
                        input_kwargs={"image": "a.png"},
                        expected_kwargs={"image": "a.png"},
        ),
        SimpleNamespace(func_name="locate_center_on_screen",
                        func_name_lib="locateCenterOnScreen",
                        input_kwargs={"image": "a.png"},
                        expected_kwargs={"image": "a.png"},
        ),
        SimpleNamespace(func_name="locate_on_screen",
                        func_name_lib="locateOnScreen",
                        input_kwargs={"image": "a.png", "min_search_time": 4.2},
                        expected_kwargs={"image": "a.png", "minSearchTime": 4.2},
        ),
        SimpleNamespace(func_name="locate_on_window",
                        func_name_lib="locateOnWindow",
                        input_kwargs={"image": "a.png", "title": "Title"},
                        expected_kwargs={"image": "a.png", "title": "Title"},
        ),
        SimpleNamespace(func_name="pixel_matches_color",
                        func_name_lib="pixelMatchesColor",
                        input_kwargs={"x": 10, "y": 20, "expected_color": (1,2,3), "tolerance": 1},
                        expected_kwargs={"x": 10, "y": 20, "expectedRGBColor": (1,2,3), "tolerance": 1},
        ),
        SimpleNamespace(func_name="screenshot",
                        func_name_lib="screenshot",
                        input_kwargs={"image_path": "a.png", "region": (1,2,3,4)},
                        expected_kwargs={"imageFilename": "a.png", "region": (1,2,3,4)},
        ),
    ], ids=lambda test_case: test_case.func_name)
    def test_locate_kwargs(self, test_case, windows_screen):
        """Call locate() with kwargs should translate in pyscreeze arguments library."""
        func = getattr(windows_screen, test_case.func_name)
        func(**test_case.input_kwargs, unexist_but="should_be_passed")

        func_lib = getattr(windows_screen._mocks["pyscreeze"], test_case.func_name_lib)
        func_lib.assert_called_once_with(**test_case.expected_kwargs, unexist_but="should_be_passed")


class TestWindowsScreenImageNotFoundException:
    """Tests for pyscreeze.ImageNotFoundException wraps to pyautogui2.ImageNotFoundException."""

    def test_locate_raise(self, windows_screen):
        """Call locate() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = windows_screen._mocks["pyscreeze"].ImageNotFoundException
        windows_screen._mocks["pyscreeze"].locate.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            windows_screen.locate()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_all_raise(self, windows_screen):
        """Call locate_all() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = windows_screen._mocks["pyscreeze"].ImageNotFoundException
        windows_screen._mocks["pyscreeze"].locateAll.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            windows_screen.locate_all()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_all_on_screen_raise(self, windows_screen):
        """Call locate_all_on_screen() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = windows_screen._mocks["pyscreeze"].ImageNotFoundException
        windows_screen._mocks["pyscreeze"].locateAllOnScreen.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            windows_screen.locate_all_on_screen()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_center_on_screen_raise(self, windows_screen):
        """Call locate_center_on_screen() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = windows_screen._mocks["pyscreeze"].ImageNotFoundException
        windows_screen._mocks["pyscreeze"].locateCenterOnScreen.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            windows_screen.locate_center_on_screen()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_on_screen_raise(self, windows_screen):
        """Call locate_on_screen() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = windows_screen._mocks["pyscreeze"].ImageNotFoundException
        windows_screen._mocks["pyscreeze"].locateOnScreen.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            windows_screen.locate_on_screen()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_on_window_raise(self, windows_screen):
        """Call locate_on_window() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = windows_screen._mocks["pyscreeze"].ImageNotFoundException
        windows_screen._mocks["pyscreeze"].locateOnWindow.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            windows_screen.locate_on_window()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"


class TestWindowsScreenDelegatesToPyGetWindow:
    """Tests for methods delegates to pygetwindow."""

    def test_window_delegate(self, windows_screen):
        """Call window() delegates to pygetwindow library."""
        windows_screen.window()
        windows_screen._mocks["pygetwindow"].Window.assert_called_once()

    def test_get_active_window_delegate(self, windows_screen):
        """Call get_active_window() delegates to pygetwindow library."""
        windows_screen.get_active_window()
        windows_screen._mocks["pygetwindow"].getActiveWindow.assert_called_once()

    def test_get_active_window_title_delegate(self, windows_screen):
        """Call get_active_window_title() delegates to pygetwindow library."""
        windows_screen.get_active_window_title()
        windows_screen._mocks["pygetwindow"].getActiveWindowTitle.assert_called_once()

    def test_get_windows_at_delegate(self, windows_screen):
        """Call get_windows_at() delegates to pygetwindow library."""
        windows_screen.get_windows_at()
        windows_screen._mocks["pygetwindow"].getWindowAt.assert_called_once()

    def test_get_windows_with_title_delegate(self, windows_screen):
        """Call get_windows_with_title() delegates to pygetwindow library."""
        windows_screen.get_windows_with_title()
        windows_screen._mocks["pygetwindow"].getWindowsWithTitle.assert_called_once()

    def test_get_all_windows_delegate(self, windows_screen):
        """Call get_all_windows() delegates to pygetwindow library."""
        windows_screen.get_all_windows()
        windows_screen._mocks["pygetwindow"].getAllWindows.assert_called_once()

    def test_get_all_titles_delegate(self, windows_screen):
        """Call get_all_titles() delegates to pygetwindow library."""
        windows_screen.get_all_titles()
        windows_screen._mocks["pygetwindow"].getAllTitles.assert_called_once()


class TestScreenGetSizeMax:
    """Tests for get_size_max enumerating monitors."""

    def test_enum_display_monitors_failure_raises_oserror(self, windows_screen):
        # user32.EnumDisplayMonitors returns false -> OSError
        windows_screen._user32.EnumDisplayMonitors.return_value = False
        with pytest.raises(OSError):
            windows_screen.get_size_max()

    def test_enum_display_monitors_no_monitors_raises_runtime(self, windows_screen):
        # EnumDisplayMonitors returns true but callback never appends -> monitors empty
        windows_screen._user32.EnumDisplayMonitors.return_value = True
        with pytest.raises(RuntimeError):
            windows_screen.get_size_max()

    def test_enum_display_monitors_returns_combined_size(self, windows_screen):
        # Provide a working EnumDisplayMonitors that invokes callback with RECTs
        def enum_stub(_hdc, _hdc2, callback, lparam):
            from pyautogui2.osal.windows._common import RECT
            from tests.mocks.osal.windows.mock_ctypes import pointer
            # Create two RECTs and call callback for each
            r1 = RECT()
            r1.left, r1.top, r1.right, r1.bottom = 0, 0, 800, 600
            r2 = RECT()
            r2.left, r2.top, r2.right, r2.bottom = 800, 0, 1600, 900

            # callback signature: (hMonitor, hdc, lprc, lparam)
            callback(1, 0, pointer(r1), lparam)
            callback(2, 0, pointer(r2), lparam)
            return 1

        windows_screen._user32.EnumDisplayMonitors.side_effect = enum_stub

        size = windows_screen.get_size_max()
        # Combined width = 1600, height = max(600,900) => 900
        assert size.width == 1600
        assert size.height == 900


class TestScreenGetSize:
    """Tests for get_size using MonitorFromWindow / GetMonitorInfoW."""

    def test_get_size_monitor_info_failure_raises(self, windows_screen):
        # MonitorFromWindow returns a handle; GetMonitorInfoW returns False -> OSError
        windows_screen._user32.MonitorFromWindow.return_value = 123
        windows_screen._user32.GetDesktopWindow.return_value = 456
        windows_screen._user32.GetMonitorInfoW.return_value = False

        with pytest.raises(OSError):
            windows_screen.get_size()

    def test_get_size_success_returns_size(self, windows_screen):
        # Build MONITORINFO and set rcMonitor
        def get_monitor_info(_handle, info):
            info.rcMonitor.left = 0
            info.rcMonitor.top = 0
            info.rcMonitor.right = 1024
            info.rcMonitor.bottom = 768
            return 1

        windows_screen._user32.MonitorFromWindow.return_value = 123
        windows_screen._user32.GetDesktopWindow.return_value = 456
        windows_screen._user32.GetMonitorInfoW.side_effect = get_monitor_info

        size = windows_screen.get_size()
        assert size.width == 1024
        assert size.height == 768

