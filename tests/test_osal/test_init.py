"""Tests for OSAL (OS Abstraction Layer) initialization."""

from unittest.mock import MagicMock, patch

import pytest

from pyautogui2.osal import get_osal


class TestGetOsalSupportedPlatforms:
    """Tests for get_osal() with supported OS platforms."""

    @patch("pyautogui2.osal.get_platform_info")
    @patch("pyautogui2.osal.import_module")
    def test_get_osal_linux(self, mock_import, mock_platform_info):
        """get_osal() loads Linux backend when os_id is 'linux'."""
        mock_platform_info.return_value = {"os_id": "linux"}

        mock_linux_osal = MagicMock(name="LinuxOSAL")
        mock_linux_module = MagicMock()
        mock_linux_module.get_osal.return_value = mock_linux_osal
        mock_import.return_value = mock_linux_module

        result = get_osal()

        assert result is mock_linux_osal
        mock_import.assert_called_once_with(".linux", "pyautogui2.osal")
        mock_linux_module.get_osal.assert_called_once()

    @patch("pyautogui2.osal.get_platform_info")
    @patch("pyautogui2.osal.import_module")
    def test_get_osal_windows(self, mock_import, mock_platform_info):
        """get_osal() loads Windows backend when os_id is 'win32'."""
        mock_platform_info.return_value = {"os_id": "win32"}

        mock_windows_osal = MagicMock(name="WindowsOSAL")
        mock_windows_module = MagicMock()
        mock_windows_module.get_osal.return_value = mock_windows_osal
        mock_import.return_value = mock_windows_module

        result = get_osal()

        assert result is mock_windows_osal
        mock_import.assert_called_once_with(".windows", "pyautogui2.osal")
        mock_windows_module.get_osal.assert_called_once()

    @patch("pyautogui2.osal.get_platform_info")
    @patch("pyautogui2.osal.import_module")
    def test_get_osal_macos(self, mock_import, mock_platform_info):
        """get_osal() loads MacOS backend when os_id is 'darwin'."""
        mock_platform_info.return_value = {"os_id": "darwin"}

        mock_macos_osal = MagicMock(name="MacOSOSAL")
        mock_macos_module = MagicMock()
        mock_macos_module.get_osal.return_value = mock_macos_osal
        mock_import.return_value = mock_macos_module

        result = get_osal()

        assert result is mock_macos_osal
        mock_import.assert_called_once_with(".macos", "pyautogui2.osal")
        mock_macos_module.get_osal.assert_called_once()


class TestGetOsalUnsupportedPlatform:
    """Tests for get_osal() with unsupported OS platforms."""

    @patch("pyautogui2.osal.get_platform_info")
    def test_get_osal_unsupported_os_raises_runtime_error(self, mock_platform_info):
        """get_osal() raises RuntimeError for unsupported OS."""
        mock_platform_info.return_value = {"os_id": "freebsd"}

        with pytest.raises(RuntimeError) as exc_info:
            get_osal()

        assert "Unsupported OS: freebsd" in str(exc_info.value)

    @patch("pyautogui2.osal.get_platform_info")
    def test_get_osal_unknown_os_raises_runtime_error(self, mock_platform_info):
        """get_osal() raises RuntimeError for unknown OS."""
        mock_platform_info.return_value = {"os_id": "unknown"}

        with pytest.raises(RuntimeError) as exc_info:
            get_osal()

        assert "Unsupported OS: unknown" in str(exc_info.value)

    @patch("pyautogui2.osal.get_platform_info")
    def test_get_osal_aix_raises_runtime_error(self, mock_platform_info):
        """get_osal() raises RuntimeError for AIX."""
        mock_platform_info.return_value = {"os_id": "aix"}

        with pytest.raises(RuntimeError) as exc_info:
            get_osal()

        assert "Unsupported OS: aix" in str(exc_info.value)


class TestGetOsalBackendMapping:
    """Tests for backend module name mapping."""

    @patch("pyautogui2.osal.get_platform_info")
    @patch("pyautogui2.osal.import_module")
    def test_get_osal_uses_correct_backend_names(self, mock_import, mock_platform_info):
        """get_osal() maps os_id to correct backend module names."""
        test_cases = [
            ("darwin", ".macos"),
            ("linux", ".linux"),
            ("win32", ".windows"),
        ]

        for os_id, expected_module in test_cases:
            mock_platform_info.return_value = {"os_id": os_id}
            mock_module = MagicMock()
            mock_module.get_osal.return_value = MagicMock()
            mock_import.return_value = mock_module
            mock_import.reset_mock()

            get_osal()

            mock_import.assert_called_once_with(expected_module, "pyautogui2.osal")

    @patch("pyautogui2.osal.get_platform_info")
    @patch("pyautogui2.osal.import_module")
    def test_get_osal_calls_backend_get_osal_function(self, mock_import, mock_platform_info):
        """get_osal() calls get_osal() function from loaded backend module."""
        mock_platform_info.return_value = {"os_id": "linux"}

        mock_backend_osal = MagicMock(name="BackendOSAL")
        mock_module = MagicMock()
        mock_module.get_osal = MagicMock(return_value=mock_backend_osal)
        mock_import.return_value = mock_module

        result = get_osal()

        # Verify the backend's get_osal() was called
        mock_module.get_osal.assert_called_once_with()
        # Verify we got the backend's OSAL instance
        assert result is mock_backend_osal


class TestGetOsalIntegration:
    """Integration-style tests for get_osal()."""

    @patch("pyautogui2.osal.get_platform_info")
    @patch("pyautogui2.osal.import_module")
    def test_get_osal_returns_osal_instance(self, mock_import, mock_platform_info):
        """get_osal() returns an OSAL instance."""
        mock_platform_info.return_value = {"os_id": "linux"}

        mock_osal_instance = MagicMock()
        mock_module = MagicMock()
        mock_module.get_osal.return_value = mock_osal_instance
        mock_import.return_value = mock_module

        result = get_osal()

        assert result is not None
        assert result is mock_osal_instance

    @patch("pyautogui2.osal.get_platform_info")
    @patch("pyautogui2.osal.import_module")
    def test_get_osal_platform_info_called_once(self, mock_import, mock_platform_info):
        """get_osal() calls get_platform_info() exactly once."""
        mock_platform_info.return_value = {"os_id": "win32"}

        mock_module = MagicMock()
        mock_module.get_osal.return_value = MagicMock()
        mock_import.return_value = mock_module

        get_osal()

        mock_platform_info.assert_called_once()

    @patch("pyautogui2.osal.get_platform_info")
    def test_get_osal_error_message_includes_os_id(self, mock_platform_info):
        """RuntimeError message includes the unsupported os_id."""
        unsupported_os = "netbsd"
        mock_platform_info.return_value = {"os_id": unsupported_os}

        with pytest.raises(RuntimeError, match=rf"Unsupported OS: {unsupported_os}"):
            get_osal()
