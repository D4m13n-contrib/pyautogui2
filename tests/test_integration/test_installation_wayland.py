"""Wayland-specific installation tests."""

import subprocess

import pytest

from tests.fixtures.helpers import is_linux_ds_wayland


if not is_linux_ds_wayland():
    pytest.skip("Requires Wayland display server", allow_module_level=True)


@pytest.mark.linux
@pytest.mark.linux_wayland
class TestWaylandInstallation:
    """Tests specific to Wayland display server."""

    def test_uinput_installed(self):
        """Test that python-uinput is installed."""
        try:
            import uinput
            assert uinput is not None
        except ImportError:
            pytest.fail("python-uinput is not installed (required for Wayland)")

    def test_uinput_device_access(self):
        """Test that /dev/uinput is accessible."""
        import os
        assert os.path.exists('/dev/uinput'), "/dev/uinput device not found"
        assert os.access('/dev/uinput', os.W_OK), "No write permission to /dev/uinput (check udev rules and user groups)"

    def test_uinput_module_loaded(self):
        """Test that uinput kernel module is loaded."""
        modinfo_result = subprocess.run(['modinfo', 'uinput'], capture_output=True)
        modprobe_result = subprocess.run(['modprobe', '-n', '--first-time', 'uinput'], capture_output=True)
        assert modinfo_result.returncode == 0 and modprobe_result.returncode != 0, "uinput kernel module not loaded (run: sudo modprobe -i uinput)"

    def test_user_in_uinput_group(self):
        """Test that current user is in uinput group."""
        import grp
        import os

        try:
            uinput_gid = grp.getgrnam('uinput').gr_gid
            user_groups = os.getgroups()
            assert uinput_gid in user_groups, "User not in 'uinput' group (run: sudo usermod -a -G uinput $USER, then logout/login)"
        except KeyError:
            pytest.skip("uinput group doesn't exist (might not be required on this system)")

    @pytest.mark.real
    def test_mouse_move(self):
        """Test mouse movement (real system action - validates UInput)."""
        import time

        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()

        # Force stable position before test
        gui.pointer.move_to(100, 100)

        # Get current position
        x1, y1 = gui.pointer.get_position()

        # Move to new position
        target_x, target_y = x1 + 10, y1 + 10
        gui.pointer.move_to(target_x, target_y)

        # Wait movement is effective
        time.sleep(0.1)

        # Verify movement
        x2, y2 = gui.pointer.get_position()
        assert x2 == target_x
        assert y2 == target_y

        # Move back
        gui.pointer.move_to(x1, y1)
