"""Tests for XFCE Desktop Environment Parts.

Desktop Environment Parts are responsible for detecting the primary mouse button
based on system settings (left-handed mode, accessibility, etc.).

Test strategy:
- Mock system calls (gsettings, kwriteconfig, etc.)
- Verify correct button returned based on system configuration
- Ensure error handling works correctly
"""

from unittest.mock import call, patch

from pyautogui2.utils.types import ButtonName


class TestXfcePointerPart:
    """Tests for XfceDesktopPart."""

    def test_get_primary_button_returns_left_when_touchpad_left_handed(self, linux_de_xfce_pointer):
        """get_primary_button() returns 'left' when touchpad is left-handed mode."""
        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = "left\n"

            button = linux_de_xfce_pointer.get_primary_button()

            assert button == ButtonName.LEFT
            mock_subprocess.assert_has_calls([
                call(["gsettings", "get", "org.gnome.desktop.peripherals.touchpad", "left-handed"], text=True),
            ])

    def test_get_primary_button_returns_right_when_touchpad_right_handed(self, linux_de_xfce_pointer):
        """get_primary_button() returns 'right' when touchpad is not left-handed mode."""
        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = "right\n"

            button = linux_de_xfce_pointer.get_primary_button()

            assert button == ButtonName.RIGHT
            mock_subprocess.assert_has_calls([
                call(["gsettings", "get", "org.gnome.desktop.peripherals.touchpad", "left-handed"], text=True),
            ])

    def test_get_primary_button_returns_left_when_not_left_handed(self, linux_de_xfce_pointer):
        """get_primary_button() returns 'left' when left-handed mode is disabled."""
        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = "false\n"

            button = linux_de_xfce_pointer.get_primary_button()

            assert button == ButtonName.LEFT
            mock_subprocess.assert_has_calls([
                call(["gsettings", "get", "org.gnome.desktop.peripherals.touchpad", "left-handed"], text=True),
                call(["gsettings", "get", "org.gnome.desktop.peripherals.mouse", "left-handed"], text=True),
            ])

    def test_get_primary_button_returns_right_when_left_handed(self, linux_de_xfce_pointer):
        """get_primary_button() returns 'right' when left-handed mode is enabled."""
        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = "true\n"

            button = linux_de_xfce_pointer.get_primary_button()

            assert button == ButtonName.RIGHT
            mock_subprocess.assert_has_calls([
                call(["gsettings", "get", "org.gnome.desktop.peripherals.touchpad", "left-handed"], text=True),
                call(["gsettings", "get", "org.gnome.desktop.peripherals.mouse", "left-handed"], text=True),
            ])

    def test_get_primary_button_handles_subprocess_error(self, linux_de_xfce_pointer):
        """get_primary_button() handles subprocess errors gracefully."""
        with patch("subprocess.check_output") as mock_subprocess:
            from subprocess import CalledProcessError
            mock_subprocess.side_effect = CalledProcessError(1, "gsettings")

            button = linux_de_xfce_pointer.get_primary_button()
            assert button == ButtonName.LEFT    # default is LEFT

    def test_get_primary_button_handles_invalid_output(self, linux_de_xfce_pointer):
        """get_primary_button() handles unexpected gsettings output."""
        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = "invalid_value\n"

            button = linux_de_xfce_pointer.get_primary_button()
            assert button == ButtonName.LEFT    # default is LEFT
