"""Tests for X11 Display Server Part providing screen functions."""


import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException
from pyautogui2.utils.types import Size


class TestX11ScreenPartSetupPostinit:
    """Tests for X11 setup_postinit() functions."""

    def test_setup_postinit_without_display_raise(self, linux_ds_x11_screen):
        """setup_postinit() calls without display should raise PyAutoGUIException."""
        linux_ds_x11_screen._xlib.display.Display = lambda *_a, **_kw: None
        with pytest.raises(PyAutoGUIException, match="Error: Cannot obtain Display"):
            linux_ds_x11_screen.setup_postinit()


class TestX11ScreenPartGetsize:
    """Tests for X11 get_size() function."""

    def test_get_size_success(self, linux_ds_x11_screen):
        """get_size() calls should success."""
        result = linux_ds_x11_screen.get_size()

        assert isinstance(result, Size)
        assert result == Size(1920, 1080)


class TestX11ScreenPartGetsizeMax:
    """Tests for X11 get_size_max() function."""

    def test_get_size_max_success(self, linux_ds_x11_screen):
        """get_size_max() calls should success."""
        result = linux_ds_x11_screen.get_size_max()

        assert isinstance(result, Size)
        assert result == Size(1920, 1080)


class TestX11ScreenPartScreenshot:
    """Tests for X11 _take_screenshot() function."""

    def test_take_screenshot_success(self, linux_ds_x11_screen):
        """take_screenshot() calls should delegates to pyscreeze screenshot function."""
        _ = linux_ds_x11_screen._take_screenshot()
        linux_ds_x11_screen._mocks["pyscreeze"].screenshot.assert_called_once()
