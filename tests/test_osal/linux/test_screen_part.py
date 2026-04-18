"""Tests for LinuxScreenPart."""

from types import SimpleNamespace

import pytest

from pyautogui2.utils.exceptions import ImageNotFoundException


class TestLinuxScreenDelegatesToPyScreeze:
    """Tests for methods delegates to pyscreeze."""

    def test_locate_delegate(self, linux_screen):
        """Call locate() delegates to pyscreeze library."""
        linux_screen.locate()
        linux_screen._mocks["pyscreeze"].locate.assert_called_once()

    def test_locate_all_delegate(self, linux_screen):
        """Call locate_all() delegates to pyscreeze library."""
        linux_screen.locate_all()
        linux_screen._mocks["pyscreeze"].locateAll.assert_called_once()

    def test_locate_all_on_screen_delegate(self, linux_screen):
        """Call locate_all_on_screen() delegates to pyscreeze library."""
        linux_screen.locate_all_on_screen()
        linux_screen._take_screenshot.assert_called_once()
        linux_screen._mocks["pyscreeze"].locateAll.assert_called_once()

        linux_screen._mocks["pyscreeze"].locateAllOnScreen.assert_not_called()

    def test_locate_center_on_screen_delegate(self, linux_screen):
        """Call locate_center_on_screen() delegates to locate pyscreeze library."""
        linux_screen.locate_center_on_screen()
        linux_screen._take_screenshot.assert_called_once()
        linux_screen._mocks["pyscreeze"].locate.assert_called_once()
        # linux_screen.center.assert_called_once()

        linux_screen._mocks["pyscreeze"].locateCenterOnScreen.assert_not_called()

    def test_locate_on_screen_delegate(self, linux_screen):
        """Call locate_on_screen() delegates to locate pyscreeze library."""
        linux_screen.locate_on_screen()
        linux_screen._take_screenshot.assert_called_once()
        linux_screen._mocks["pyscreeze"].locate.assert_called_once()

        linux_screen._mocks["pyscreeze"].locateOnScreen.assert_not_called()

    def test_locate_on_window_delegate(self, linux_screen):
        """Call locate_on_window() delegates to pyscreeze library."""
        linux_screen.locate_on_window()
        linux_screen._mocks["pyscreeze"].locateOnWindow.assert_called_once()

    def test_center_delegate(self, linux_screen):
        """Call center() delegates to pyscreeze library."""
        linux_screen.center((10, 20, 100, 200))
        linux_screen._mocks["pyscreeze"].center.assert_called_once()

    def test_pixel_delegate(self, linux_screen):
        """Call pixel() delegates to pyscreeze library."""
        linux_screen.pixel()
        linux_screen._mocks["pyscreeze"].pixel.assert_called_once()

    def test_pixel_matches_color_delegate(self, linux_screen):
        """Call pixel_matches_color() delegates to pyscreeze library."""
        linux_screen.pixel_matches_color()
        linux_screen._mocks["pyscreeze"].pixelMatchesColor.assert_called_once()

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
    ], ids=lambda test_case: test_case.func_name)
    def test_locate_kwargs(self, test_case, linux_screen):
        """Call locate() with kwargs should translate in pyscreeze arguments library."""
        func = getattr(linux_screen, test_case.func_name)
        func(**test_case.input_kwargs, unexist_but="should_be_passed")

        func_lib = getattr(linux_screen._mocks["pyscreeze"], test_case.func_name_lib)
        func_lib.assert_called_once_with(**test_case.expected_kwargs, unexist_but="should_be_passed")


class TestLinuxScreenScreenshot:
    """Tests for screenshot()."""

    def test_screenshot_raises_when_no_display_server_impl(self, linux_screen):
        """screenshot() raises PyAutoGUIException if _take_screenshot raises AttributeError."""
        from pyautogui2.utils.exceptions import PyAutoGUIException

        linux_screen._take_screenshot.side_effect = AttributeError("missing method")

        with pytest.raises(PyAutoGUIException, match="No display server implementation found"):
            linux_screen.screenshot()

    def test_screenshot_crops_when_region_provided(self, linux_screen):
        """screenshot() crops the image when a region is provided."""
        region = (10, 20, 100, 200)
        linux_screen.screenshot(region=region)

        img = linux_screen._take_screenshot.return_value
        img.crop.assert_called_once_with((10, 20, 110, 220))  # left+width, top+height

    def test_screenshot_saves_when_filename_provided(self, linux_screen):
        """screenshot() saves the image when image_filename is provided."""
        linux_screen.screenshot(image_filename="out.png")

        img = linux_screen._take_screenshot.return_value
        img.save.assert_called_once_with("out.png")


class TestLinuxScreenImageNotFoundException:
    """Tests for pyscreeze.ImageNotFoundException wraps to pyautogui2.ImageNotFoundException."""

    def test_locate_raise(self, linux_screen):
        """Call locate() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = linux_screen._mocks["pyscreeze"].ImageNotFoundException
        linux_screen._mocks["pyscreeze"].locate.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            linux_screen.locate()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_all_raise(self, linux_screen):
        """Call locate_all() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = linux_screen._mocks["pyscreeze"].ImageNotFoundException
        linux_screen._mocks["pyscreeze"].locateAll.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            linux_screen.locate_all()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_all_on_screen_raise(self, linux_screen):
        """Call locate_all_on_screen() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = linux_screen._mocks["pyscreeze"].ImageNotFoundException
        linux_screen._mocks["pyscreeze"].locateAll.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            linux_screen.locate_all_on_screen()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_center_on_screen_raise(self, linux_screen):
        """Call locate_center_on_screen() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = linux_screen._mocks["pyscreeze"].ImageNotFoundException
        linux_screen._mocks["pyscreeze"].locate.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            linux_screen.locate_center_on_screen()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_on_screen_raise(self, linux_screen):
        """Call locate_on_screen() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = linux_screen._mocks["pyscreeze"].ImageNotFoundException
        linux_screen._mocks["pyscreeze"].locate.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            linux_screen.locate_on_screen()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"

    def test_locate_on_window_raise(self, linux_screen):
        """Call locate_on_window() should delegates pyscreeze.ImageNotFoundException to pyautogui2.ImageNotFoundException."""
        pyscreeze_exception = linux_screen._mocks["pyscreeze"].ImageNotFoundException
        linux_screen._mocks["pyscreeze"].locateOnWindow.side_effect = pyscreeze_exception("Image not found")
        with pytest.raises(ImageNotFoundException, match="^$") as exc_info:
            linux_screen.locate_on_window()

        cause = exc_info.value.__cause__
        assert isinstance(cause, pyscreeze_exception)
        assert str(cause) == "Image not found"


class TestLinuxScreenDelegatesToPyGetWindow:
    """Tests for methods delegates to pygetwindow."""

    def test_window_delegate(self, linux_screen):
        """Call window() delegates to pygetwindow library."""
        linux_screen.window()
        linux_screen._mocks["pygetwindow"].Window.assert_called_once()

    def test_get_active_window_delegate(self, linux_screen):
        """Call get_active_window() delegates to pygetwindow library."""
        linux_screen.get_active_window()
        linux_screen._mocks["pygetwindow"].getActiveWindow.assert_called_once()

    def test_get_active_window_title_delegate(self, linux_screen):
        """Call get_active_window_title() delegates to pygetwindow library."""
        linux_screen.get_active_window_title()
        linux_screen._mocks["pygetwindow"].getActiveWindowTitle.assert_called_once()

    def test_get_windows_at_delegate(self, linux_screen):
        """Call get_windows_at() delegates to pygetwindow library."""
        linux_screen.get_windows_at()
        linux_screen._mocks["pygetwindow"].getWindowAt.assert_called_once()

    def test_get_windows_with_title_delegate(self, linux_screen):
        """Call get_windows_with_title() delegates to pygetwindow library."""
        linux_screen.get_windows_with_title()
        linux_screen._mocks["pygetwindow"].getWindowsWithTitle.assert_called_once()

    def test_get_all_windows_delegate(self, linux_screen):
        """Call get_all_windows() delegates to pygetwindow library."""
        linux_screen.get_all_windows()
        linux_screen._mocks["pygetwindow"].getAllWindows.assert_called_once()

    def test_get_all_titles_delegate(self, linux_screen):
        """Call get_all_titles() delegates to pygetwindow library."""
        linux_screen.get_all_titles()
        linux_screen._mocks["pygetwindow"].getAllTitles.assert_called_once()
