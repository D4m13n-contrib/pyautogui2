"""Tests for KDE Desktop Environment Parts."""

from unittest.mock import patch

from pyautogui2.utils.types import ButtonName


class TestKdePointerPart:
    """Tests for KdePointerPart."""

    def test_get_primary_button_returns_left_by_default(self, linux_de_kde_pointer):
        """get_primary_button() returns LEFT when kcminputrc does not exist."""
        linux_de_kde_pointer._cache_primary_button = None
        with patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.Path.exists",
            return_value=False,
        ):
            button = linux_de_kde_pointer.get_primary_button()

        assert button == ButtonName.LEFT

    def test_get_primary_button_returns_right_when_left_handed(self, linux_de_kde_pointer):
        """get_primary_button() returns RIGHT when kcminputrc has LeftHanded=true."""
        linux_de_kde_pointer._cache_primary_button = None
        with patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.Path.exists",
            return_value=True,
        ), patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.configparser.RawConfigParser.read"
        ), patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.configparser.RawConfigParser.sections",
            return_value=["Libinput"],
        ), patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.configparser.RawConfigParser.get",
            return_value="true",
        ):
            button = linux_de_kde_pointer.get_primary_button()

        assert button == ButtonName.RIGHT

    def test_get_primary_button_returns_left_when_not_left_handed(self, linux_de_kde_pointer):
        """get_primary_button() returns LEFT when kcminputrc has LeftHanded=false."""
        linux_de_kde_pointer._cache_primary_button = None
        with patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.Path.exists",
            return_value=True,
        ), patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.configparser.RawConfigParser.read"
        ), patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.configparser.RawConfigParser.sections",
            return_value=["Libinput"],
        ), patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.configparser.RawConfigParser.get",
            return_value="false",
        ):
            button = linux_de_kde_pointer.get_primary_button()

        assert button == ButtonName.LEFT

    def test_get_primary_button_cache(self, linux_de_kde_pointer):
        """get_primary_button() returns cached value on second call."""
        linux_de_kde_pointer._cache_primary_button = ButtonName.RIGHT

        button = linux_de_kde_pointer.get_primary_button()

        assert button == ButtonName.RIGHT

    def test_is_left_handed_no_libinput_section(self, linux_de_kde_pointer):
        """_is_left_handed() returns False when no Libinput section exists."""
        from pyautogui2.osal.linux.desktops.kde.pointer import KdePointerPart

        with patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.Path.exists",
            return_value=True,
        ), patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.configparser.RawConfigParser.read"
        ), patch(
            "pyautogui2.osal.linux.desktops.kde.pointer.configparser.RawConfigParser.sections",
            return_value=["Mouse"],  # not a libinput section
        ):
            result = KdePointerPart._is_left_handed()

        assert result is False
