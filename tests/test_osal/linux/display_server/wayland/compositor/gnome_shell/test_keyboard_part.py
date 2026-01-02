"""Tests for GNOME Shell Wayland Keyboard Part."""

from unittest.mock import patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException


class TestGnomeShellKeyboardPartInit:
    """Test GNOME Shell Keyboard Part initialization."""

    def test_fixture_provides_correct_type(self, linux_ds_wayland_co_gnome_shell_keyboard):
        """Fixture should provide GnomeShellKeyboardPart instance."""
        from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell.keyboard import (
            GnomeShellKeyboardPart,
        )
        assert isinstance(linux_ds_wayland_co_gnome_shell_keyboard, GnomeShellKeyboardPart)

    def test_inherits_from_wayland_keyboard(self, linux_ds_wayland_co_gnome_shell_keyboard):
        """Should inherit from WaylandKeyboardPart."""
        from pyautogui2.osal.linux.display_servers.wayland.keyboard import WaylandKeyboardPart
        assert isinstance(linux_ds_wayland_co_gnome_shell_keyboard, WaylandKeyboardPart)

    def test_backend_property_lazy_init(self, linux_ds_wayland_co_gnome_shell_keyboard):
        """Backend property instantiates GnomeShellBackend on first access."""
        linux_ds_wayland_co_gnome_shell_keyboard._backend = None  # Reset to None

        with patch("pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell._backend.GnomeShellBackend") as mock_cls:
            _ = linux_ds_wayland_co_gnome_shell_keyboard.backend
            mock_cls.assert_called_once()


class TestGnomeShellKeyboardPartLayoutDetection:
    """Test keyboard layout detection via gsettings."""

    def test_get_layout_us(self, linux_ds_wayland_co_gnome_shell_keyboard):
        """Should detect US layout."""
        linux_ds_wayland_co_gnome_shell_keyboard._backend.get_keyboard_layout.return_value = "us"
        assert linux_ds_wayland_co_gnome_shell_keyboard.get_layout() == "QWERTY"

    def test_get_layout_fr(self, linux_ds_wayland_co_gnome_shell_keyboard):
        """Should detect French layout."""
        linux_ds_wayland_co_gnome_shell_keyboard._backend.get_keyboard_layout.return_value = "fr"
        assert linux_ds_wayland_co_gnome_shell_keyboard.get_layout() == "AZERTY"

    def test_get_layout_ch(self, linux_ds_wayland_co_gnome_shell_keyboard):
        """Should detect French layout."""
        linux_ds_wayland_co_gnome_shell_keyboard._backend.get_keyboard_layout.return_value = "ch"
        assert linux_ds_wayland_co_gnome_shell_keyboard.get_layout() == "QWERTZ"

    def test_get_layout_invalid(self, linux_ds_wayland_co_gnome_shell_keyboard):
        """Should raises PyAutoGUIException."""
        linux_ds_wayland_co_gnome_shell_keyboard._backend.get_keyboard_layout.return_value = "Invalid_Value"
        with pytest.raises(PyAutoGUIException):
            linux_ds_wayland_co_gnome_shell_keyboard.get_layout()
