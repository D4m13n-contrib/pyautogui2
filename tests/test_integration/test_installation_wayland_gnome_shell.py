"""Wayland-specific installation tests."""

import subprocess

import pytest

from tests.fixtures.helpers import is_linux_compositor_gnome_shell


if not is_linux_compositor_gnome_shell():
    pytest.skip("Requires Wayland GNOME Shell compositor", allow_module_level=True)


@pytest.mark.linux
@pytest.mark.linux_wayland
@pytest.mark.linux_gnome_shell
class TestWaylandGnomeShell:
    """Tests specific to GNOME Shell on Wayland."""

    def test_extension_installed(self):
        """Test that GNOME Shell extension is installed."""
        result = subprocess.run(
            ['gnome-extensions', 'list'],
            capture_output=True,
            text=True
        )
        assert 'gnome-wayland@pyautogui.org' in result.stdout, \
            "GNOME Shell extension not installed (run: pyautogui2-install-wayland-gnomeshell-extension)"

    def test_extension_enabled(self):
        """Test that GNOME Shell extension is enabled."""
        result = subprocess.run(
            ['gnome-extensions', 'info', 'gnome-wayland@pyautogui.org'],
            capture_output=True,
            text=True
        )
        assert 'State: ACTIVE' in result.stdout or 'Enabled: Yes' in result.stdout, \
            "GNOME Shell extension not enabled (run: gnome-extensions enable gnome-wayland@pyautogui.org)"

    @pytest.mark.real
    def test_mouse_position(self):
        """Test mouse position retrieval (real system call - validates extension)."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()

        x, y = gui.pointer.get_position()
        assert isinstance(x, (int, float))
        assert isinstance(y, (int, float))
        assert x >= 0
        assert y >= 0

    @pytest.mark.real
    def test_screen_size(self):
        """Test screen size retrieval (real system call - validates extension)."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()

        size = gui.screen.get_size()
        assert size.width > 0
        assert size.height > 0
