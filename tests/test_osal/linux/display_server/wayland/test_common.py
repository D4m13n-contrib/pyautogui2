"""Tests for pyautogui2.osal.linux.display_servers.wayland._common."""

from unittest.mock import MagicMock, patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException


class TestEnsureDeviceNotExists:
    """Tests for ensure_device_not_exists()."""

    def test_devices_file_missing_logs_warning_and_returns(self, isolated_linux_wayland, caplog):
        """If /proc/bus/input/devices does not exist, log a warning and return without raising."""
        import logging

        from pyautogui2.osal.linux.display_servers.wayland._common import ensure_device_not_exists

        with patch("pyautogui2.osal.linux.display_servers.wayland._common.Path.exists", return_value=False), \
             caplog.at_level(logging.WARNING):
            ensure_device_not_exists("my-device")

        assert any("device uniqueness could not be checked" in r.message for r in caplog.records)
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    def test_device_not_registered_does_not_raise(self, isolated_linux_wayland):
        """If grep returns non-zero (device not found), no exception is raised."""
        from pyautogui2.osal.linux.display_servers.wayland._common import ensure_device_not_exists

        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("pyautogui2.osal.linux.display_servers.wayland._common.Path.exists", return_value=True), \
             patch("pyautogui2.osal.linux.display_servers.wayland._common.subprocess.run", return_value=mock_result):
            ensure_device_not_exists("my-device")  # Must not raise

    def test_device_already_registered_raises(self, isolated_linux_wayland):
        """If grep returns 0 (device found), PyAutoGUIException is raised."""
        from pyautogui2.osal.linux.display_servers.wayland._common import ensure_device_not_exists

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("pyautogui2.osal.linux.display_servers.wayland._common.Path.exists", return_value=True), \
             patch("pyautogui2.osal.linux.display_servers.wayland._common.subprocess.run", return_value=mock_result), \
             pytest.raises(PyAutoGUIException, match="my-device"):
            ensure_device_not_exists("my-device")
