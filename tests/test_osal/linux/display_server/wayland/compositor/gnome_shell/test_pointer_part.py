"""Tests for GNOME Shell Wayland Pointer Part."""

from unittest.mock import patch

import pytest


class TestGnomeShellPointerPartInit:
    """Test GNOME Shell Pointer Part initialization."""

    def test_fixture_provides_correct_type(self, linux_ds_wayland_co_gnome_shell_pointer):
        """Fixture should provide GnomeShellPointerPart instance."""
        from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell.pointer import (
            GnomeShellPointerPart,
        )
        assert isinstance(linux_ds_wayland_co_gnome_shell_pointer, GnomeShellPointerPart)

    def test_inherits_from_wayland_pointer(self, linux_ds_wayland_co_gnome_shell_pointer):
        """Should inherit from WaylandPointerPart."""
        from pyautogui2.osal.linux.display_servers.wayland.pointer import WaylandPointerPart
        assert isinstance(linux_ds_wayland_co_gnome_shell_pointer, WaylandPointerPart)

    def test_backend_property_lazy_init(self, linux_ds_wayland_co_gnome_shell_pointer):
        """Backend property instantiates GnomeShellBackend on first access."""
        linux_ds_wayland_co_gnome_shell_pointer._backend = None  # Reset to None

        with patch("pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell._backend.GnomeShellBackend") as mock_cls:
            _ = linux_ds_wayland_co_gnome_shell_pointer.backend
            mock_cls.assert_called_once()


class TestGnomeShellPointerPartGetPos:
    """Test position tracking."""

    def test_get_pos_normal(self, linux_ds_wayland_co_gnome_shell_pointer):
        """get_pos should return backend get_pointer_position coordinates."""
        linux_ds_wayland_co_gnome_shell_pointer._backend.get_pointer_position.return_value = (750, 450)
        pos = linux_ds_wayland_co_gnome_shell_pointer.get_pos()
        assert pos == (750, 450)
        linux_ds_wayland_co_gnome_shell_pointer._backend.get_pointer_position.assert_called_once()

    def test_get_pos_negative(self, linux_ds_wayland_co_gnome_shell_pointer):
        """get_pos should return backend get_pointer_position coordinates."""
        linux_ds_wayland_co_gnome_shell_pointer._backend.get_pointer_position.return_value = (-100, -200)
        pos = linux_ds_wayland_co_gnome_shell_pointer.get_pos()
        assert pos == (-100, -200)

    def test_get_pos_handles_backend_error(self, linux_ds_wayland_co_gnome_shell_pointer):
        """get_pos() handles backend communication errors."""
        linux_ds_wayland_co_gnome_shell_pointer._backend.get_pointer_position.side_effect = Exception("D-Bus error")

        with pytest.raises(Exception, match="D-Bus error"):
            linux_ds_wayland_co_gnome_shell_pointer.get_pos()
