"""Tests for GNOME Shell Wayland Dialogs Part."""



class TestGnomeShellDialogsPartInit:
    """Test GNOME Shell Dialogs Part initialization."""

    def test_fixture_provides_correct_type(self, linux_ds_wayland_co_gnome_shell_dialogs):
        """Fixture should provide GnomeShellDialogsPart instance."""
        from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell.dialogs import (
            GnomeShellDialogsPart,
        )
        assert isinstance(linux_ds_wayland_co_gnome_shell_dialogs, GnomeShellDialogsPart)

    def test_inherits_from_wayland_dialogs(self, linux_ds_wayland_co_gnome_shell_dialogs):
        """Should inherit from WaylandDialogsPart."""
        from pyautogui2.osal.linux.display_servers.wayland.dialogs import WaylandDialogsPart
        assert isinstance(linux_ds_wayland_co_gnome_shell_dialogs, WaylandDialogsPart)
