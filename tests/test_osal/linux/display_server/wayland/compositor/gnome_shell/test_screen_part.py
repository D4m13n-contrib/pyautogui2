"""Tests for GNOME Shell Wayland Screen Part."""

from unittest.mock import patch

from pyautogui2.utils.types import Size


class TestGnomeShellScreenPartInit:
    """Test GNOME Shell Screen Part initialization."""

    def test_fixture_provides_correct_type(self, linux_ds_wayland_co_gnome_shell_screen):
        """Fixture should provide GnomeShellScreenPart instance."""
        from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell.screen import (
            GnomeShellScreenPart,
        )
        assert isinstance(linux_ds_wayland_co_gnome_shell_screen, GnomeShellScreenPart)

    def test_inherits_from_wayland_screen(self, linux_ds_wayland_co_gnome_shell_screen):
        """Should inherit from WaylandScreenPart."""
        from pyautogui2.osal.linux.display_servers.wayland.screen import WaylandScreenPart
        assert isinstance(linux_ds_wayland_co_gnome_shell_screen, WaylandScreenPart)

    def test_backend_property_lazy_init(self, linux_ds_wayland_co_gnome_shell_screen):
        """Backend property instantiates GnomeShellBackend on first access."""
        linux_ds_wayland_co_gnome_shell_screen._backend = None  # Reset to None

        with patch("pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell._backend.GnomeShellBackend") as mock_cls:
            _ = linux_ds_wayland_co_gnome_shell_screen.backend
            mock_cls.assert_called_once()


class TestGnomeShellScreenPartGetSize:
    """Test screen get_size() and get_size_max()."""

    def test_get_size_fallback(self, linux_ds_wayland_co_gnome_shell_screen):
        linux_ds_wayland_co_gnome_shell_screen._backend.get_screen_outputs.return_value = "[]"
        result = linux_ds_wayland_co_gnome_shell_screen.get_size()
        assert result == Size(0, 0)

    def test_get_size_normal(self, linux_ds_wayland_co_gnome_shell_screen):
        linux_ds_wayland_co_gnome_shell_screen._backend.get_screen_outputs.return_value = '[{"x":0,"y":0,"width":1234,"height":5678}]'
        result = linux_ds_wayland_co_gnome_shell_screen.get_size()
        assert result == Size(1234, 5678)

    def test_get_size_max_fallback(self, linux_ds_wayland_co_gnome_shell_screen):
        linux_ds_wayland_co_gnome_shell_screen._backend.get_screen_outputs.return_value = "[]"
        result = linux_ds_wayland_co_gnome_shell_screen.get_size_max()
        assert result == Size(0, 0)

    def test_get_size_max_normal(self, linux_ds_wayland_co_gnome_shell_screen):
        linux_ds_wayland_co_gnome_shell_screen._backend.get_screen_outputs.return_value = '[{"x":0,"y":0,"width":1000,"height":5000}, {"x":1000,"y":5000,"width":234,"height":678}]'
        result = linux_ds_wayland_co_gnome_shell_screen.get_size_max()
        assert result == Size(1234, 5678)
