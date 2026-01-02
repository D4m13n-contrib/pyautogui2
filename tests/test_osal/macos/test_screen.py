"""Tests for MacOSScreen."""

from types import SimpleNamespace

import pytest

from pyautogui2.utils.exceptions import ImageNotFoundException


class TestMacOSScreenDelegatesToPyScreeze:
    """Tests for methods delegates to pyscreeze."""

    def test_locate_delegate(self, macos_screen):
        """Call locate() delegates to pyscreeze library."""
        macos_screen.locate()
        macos_screen._mocks["pyscreeze"].locate.assert_called_once()

    def test_locate_all_delegate(self, macos_screen):
        """Call locate_all() delegates to pyscreeze library."""
        macos_screen.locate_all()
        macos_screen._mocks["pyscreeze"].locateAll.assert_called_once()

    def test_locate_all_on_screen_delegate(self, macos_screen):
        """Call locate_all_on_screen() delegates to pyscreeze library."""
        macos_screen.locate_all_on_screen()
        macos_screen._mocks["pyscreeze"].locateAllOnScreen.assert_called_once()

    def test_locate_center_on_screen_delegate(self, macos_screen):
        """Call locate_center_on_screen() delegates to pyscreeze library."""
        macos_screen.locate_center_on_screen()
        macos_screen._mocks["pyscreeze"].locateCenterOnScreen.assert_called_once()

    def test_locate_on_screen_delegate(self, macos_screen):
        """Call locate_on_screen() delegates to pyscreeze library."""
        macos_screen.locate_on_screen()
        macos_screen._mocks["pyscreeze"].locateOnScreen.assert_called_once()

    def test_locate_on_window_delegate(self, macos_screen):
        """Call locate_on_window() delegates to pyscreeze library."""
        macos_screen.locate_on_window()
        macos_screen._mocks["pyscreeze"].locateOnWindow.assert_called_once()

    def test_center_delegate(self, macos_screen):
        """Call center() delegates to pyscreeze library."""
        macos_screen.center((10, 20, 100, 200))
        macos_screen._mocks["pyscreeze"].center.assert_called_once()

    def test_pixel_delegate(self, macos_screen):
        """Call pixel() delegates to pyscreeze library."""
        macos_screen.pixel()
        macos_screen._mocks["pyscreeze"].pixel.assert_called_once()

    def test_pixel_matches_color_delegate(self, macos_screen):
        """Call pixel_matches_color() delegates to pyscreeze library."""
        macos_screen.pixel_matches_color()
        macos_screen._mocks["pyscreeze"].pixelMatchesColor.assert_called_once()

    def test_screenshot_delegate(self, macos_screen):
        """Call screenshot() delegates to pyscreeze library."""
        macos_screen.screenshot()
        macos_screen._mocks["pyscreeze"].screenshot.assert_called_once()

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
    def test_locate_kwargs(self, test_case, macos_screen):
        """Call locate() with kwargs should translate in pyscreeze arguments library."""
        func = getattr(macos_screen, test_case.func_name)
        func(**test_case.input_kwargs, unexist_but="should_be_passed")

        func_lib = getattr(macos_screen._mocks["pyscreeze"], test_case.func_name_lib)
        func_lib.assert_called_once_with(**test_case.expected_kwargs, unexist_but="should_be_passed")


class TestMacOSScreenImageNotFoundException:
    """Tests for pyscreeze.ImageNotFoundException wraps to pyautogui2.ImageNotFoundException."""

    def test_locate_raise(self, macos_screen):
        """Call locate() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = macos_screen._mocks["pyscreeze"].ImageNotFoundException
        macos_screen._mocks["pyscreeze"].locate.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            macos_screen.locate()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_all_raise(self, macos_screen):
        """Call locate_all() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = macos_screen._mocks["pyscreeze"].ImageNotFoundException
        macos_screen._mocks["pyscreeze"].locateAll.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            macos_screen.locate_all()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_all_on_screen_raise(self, macos_screen):
        """Call locate_all_on_screen() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = macos_screen._mocks["pyscreeze"].ImageNotFoundException
        macos_screen._mocks["pyscreeze"].locateAllOnScreen.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            macos_screen.locate_all_on_screen()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_center_on_screen_raise(self, macos_screen):
        """Call locate_center_on_screen() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = macos_screen._mocks["pyscreeze"].ImageNotFoundException
        macos_screen._mocks["pyscreeze"].locateCenterOnScreen.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            macos_screen.locate_center_on_screen()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_on_screen_raise(self, macos_screen):
        """Call locate_on_screen() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = macos_screen._mocks["pyscreeze"].ImageNotFoundException
        macos_screen._mocks["pyscreeze"].locateOnScreen.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            macos_screen.locate_on_screen()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_on_window_raise(self, macos_screen):
        """Call locate_on_window() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = macos_screen._mocks["pyscreeze"].ImageNotFoundException
        macos_screen._mocks["pyscreeze"].locateOnWindow.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            macos_screen.locate_on_window()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"


class TestMacOSScreenDelegatesToPyGetWindow:
    """Tests for methods delegates to pygetwindow."""

    def test_window_delegate(self, macos_screen):
        """Call window() delegates to pygetwindow library."""
        macos_screen.window()
        macos_screen._mocks["pygetwindow"].Window.assert_called_once()

    def test_get_active_window_delegate(self, macos_screen):
        """Call get_active_window() delegates to pygetwindow library."""
        macos_screen.get_active_window()
        macos_screen._mocks["pygetwindow"].getActiveWindow.assert_called_once()

    def test_get_active_window_title_delegate(self, macos_screen):
        """Call get_active_window_title() delegates to pygetwindow library."""
        macos_screen.get_active_window_title()
        macos_screen._mocks["pygetwindow"].getActiveWindowTitle.assert_called_once()

    def test_get_windows_at_delegate(self, macos_screen):
        """Call get_windowq_at() delegates to pygetwindow library."""
        macos_screen.get_windows_at()
        macos_screen._mocks["pygetwindow"].getWindowAt.assert_called_once()

    def test_get_windows_with_title_delegate(self, macos_screen):
        """Call get_windows_with_title() delegates to pygetwindow library."""
        macos_screen.get_windows_with_title()
        macos_screen._mocks["pygetwindow"].getWindowsWithTitle.assert_called_once()

    def test_get_all_windows_delegate(self, macos_screen):
        """Call get_all_windows() delegates to pygetwindow library."""
        macos_screen.get_all_windows()
        macos_screen._mocks["pygetwindow"].getAllWindows.assert_called_once()

    def test_get_all_titles_delegate(self, macos_screen):
        """Call get_all_titles() delegates to pygetwindow library."""
        macos_screen.get_all_titles()
        macos_screen._mocks["pygetwindow"].getAllTitles.assert_called_once()


class TestScreenGetSizeMax:
    """Tests for get_size_max enumerating monitors."""

    def test_enum_display_monitors_returns_combined_size(self, macos_screen):
        # Provide a working EnumDisplayMonitors that invokes callback with RECTs
        macos_screen._mocks["mock_appkit"].mock_set_screen_size(2000, 1000)

        size = macos_screen.get_size_max()
        # Combined width = 2000 * 2, height = 1000 * 2
        assert size.width == 4000
        assert size.height == 2000


class TestScreenGetSize:
    """Tests for get_size using MonitorFromWindow / GetMonitorInfoW."""

    def test_get_size_success_returns_size(self, macos_screen):
        macos_screen._mocks["mock_quartz"].mock_set_screen_size(100, 200)

        size = macos_screen.get_size()
        assert size.width == 100
        assert size.height == 200

        macos_screen._mocks["mock_quartz"].CGDisplayPixelsWide.assert_called_once_with(0)
        macos_screen._mocks["mock_quartz"].CGDisplayPixelsHigh.assert_called_once_with(0)
