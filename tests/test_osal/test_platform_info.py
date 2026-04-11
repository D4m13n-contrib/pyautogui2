"""Tests for platform detection utilities."""

import io

from unittest.mock import MagicMock, patch

from pyautogui2.osal.platform_info import (
    get_darwin_info,
    get_linux_info,
    get_platform_info,
    get_win32_info,
    main,
)


class TestGetLinuxInfo:
    """Tests for get_linux_info() function."""

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {
        "XDG_SESSION_TYPE": "wayland",
        "XDG_SESSION_DESKTOP": "GNOME",
    })
    @patch("subprocess.run")
    def test_linux_with_gnome_shell(self, mock_run):
        """Detects GNOME Shell compositor on Linux."""
        # gnome-shell found
        mock_run.return_value = MagicMock(returncode=0)

        result = get_linux_info()

        assert result == {
            "linux_display_server": "wayland",
            "linux_desktop": "gnome",
            "linux_compositor": "gnome_shell",
        }
        mock_run.assert_called_with(
            ["pgrep", "-x", "gnome-shell"],
            capture_output=True
        )

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {
        "XDG_SESSION_TYPE": "wayland",
        "XDG_SESSION_DESKTOP": "KDE",
    })
    @patch("subprocess.run")
    def test_linux_with_kwin_wayland(self, mock_run):
        """Detects KWin Wayland compositor on Linux."""
        # kwin_wayland detection
        def _fake_detect(cmd, **_kw):
            if "kwin_wayland" in cmd:
                return MagicMock(returncode=0)
            return MagicMock(returncode=1)

        mock_run.side_effect = _fake_detect

        result = get_linux_info()

        assert result == {
            "linux_display_server": "wayland",
            "linux_desktop": "kde",
            "linux_compositor": "kwin",
        }
        mock_run.assert_called_with(
            ["pgrep", "-x", "kwin_wayland"],
            capture_output=True
        )

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {}, clear=True)
    @patch("subprocess.run")
    def test_linux_with_missing_environment(self, mock_run):
        """Returns 'unknown' for missing environment variables."""
        mock_run.return_value = MagicMock(returncode=1)

        result = get_linux_info()

        assert result == {
            "linux_display_server": "unknown",
            "linux_desktop": "unknown",
            "linux_compositor": "unknown",
        }

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"})
    @patch("subprocess.run")
    def test_linux_with_unknown_compositor(self, mock_run):
        """Returns 'unknown' when no known compositor found."""
        # All pgrep calls fail
        mock_run.return_value = MagicMock(returncode=1)

        result = get_linux_info()

        assert result["linux_compositor"] == "unknown"
        # Should have tried all compositors
        assert mock_run.call_count == 7  # 7 compositors in list

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"})
    @patch("subprocess.run")
    def test_linux_checks_compositors_in_order(self, mock_run):
        """Checks compositors in order, stops at first match."""
        def side_effect(cmd, **kwargs):
            # Only sway found (3rd in list)
            if "sway" in cmd:
                return MagicMock(returncode=0)
            return MagicMock(returncode=1)

        mock_run.side_effect = side_effect

        result = get_linux_info()

        assert result["linux_compositor"] == "sway"
        # Should have checked: gnome-shell, kwin_wayland, sway (stops here)
        assert mock_run.call_count == 3

    @patch("sys.platform", "win32")
    def test_non_linux_returns_empty(self):
        """Returns empty dict on non-Linux platforms."""
        result = get_linux_info()
        assert result == {}

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {
        "XDG_SESSION_DESKTOP": "xubuntu"
    })
    @patch("subprocess.run")
    def test_linux_de_specific_fallback(self, mock_run):
        """Returns fallback value for specific DE value (e.g. "xubuntu" => "xfce")."""
        # All pgrep calls fail
        mock_run.return_value = MagicMock(returncode=1)

        result = get_linux_info()

        assert result["linux_desktop"] == "xfce"


class TestGetWin32Info:
    """Tests for get_win32_info() function."""

    @patch("sys.platform", "win32")
    @patch("platform.win32_ver")
    @patch("platform.win32_edition")
    def test_win32_returns_version_and_edition(self, mock_edition, mock_ver):
        """Returns Windows version and edition on win32."""
        mock_ver.return_value = ("10", "10.0.19041", "SP0", "Multiprocessor Free")
        mock_edition.return_value = "Professional"

        result = get_win32_info()

        assert result == {
            "win32_version": "10",
            "win32_edition": "Professional",
        }

    @patch("sys.platform", "linux")
    def test_non_win32_returns_empty(self):
        """Returns empty dict on non-Windows platforms."""
        result = get_win32_info()
        assert result == {}


class TestGetDarwinInfo:
    """Tests for get_darwin_info() function."""

    @patch("sys.platform", "darwin")
    @patch("platform.mac_ver")
    def test_darwin_returns_version(self, mock_mac_ver):
        """Returns MacOS version on darwin."""
        mock_mac_ver.return_value = ("13.2.1", ("", "", ""), "arm64")

        result = get_darwin_info()

        assert result == {
            "darwin_version": "13.2.1",
        }

    @patch("sys.platform", "linux")
    def test_non_darwin_returns_empty(self):
        """Returns empty dict on non-MacOS platforms."""
        result = get_darwin_info()
        assert result == {}


class TestGetPlatformInfo:
    """Tests for get_platform_info() function."""

    @patch("sys.platform", "linux")
    @patch("platform.system")
    @patch("platform.release")
    @patch("platform.python_version")
    @patch("platform.machine")
    @patch("pyautogui2.osal.platform_info.get_linux_info")
    def test_linux_platform_integration(
        self, mock_linux, mock_machine, mock_py_ver, mock_release, mock_system
    ):
        """Integrates common info with Linux-specific info."""
        mock_system.return_value = "Linux"
        mock_release.return_value = "6.8.0-90-generic"
        mock_py_ver.return_value = "3.12.3"
        mock_machine.return_value = "x86_64"
        mock_linux.return_value = {
            "linux_display_server": "wayland",
            "linux_compositor": "gnome_shell",
        }

        result = get_platform_info()

        assert result["os"] == "Linux"
        assert result["os_id"] == "linux"
        assert result["os_release"] == "6.8.0-90-generic"
        assert result["python_version"] == "3.12.3"
        assert result["architecture"] == "x86_64"
        assert result["linux_display_server"] == "wayland"
        assert result["linux_compositor"] == "gnome_shell"

        mock_linux.assert_called_once()

    @patch("sys.platform", "win32")
    @patch("platform.system")
    @patch("pyautogui2.osal.platform_info.get_win32_info")
    def test_win32_platform_integration(self, mock_win32, mock_system):
        """Integrates common info with Windows-specific info."""
        mock_system.return_value = "Windows"
        mock_win32.return_value = {
            "win32_version": "11",
            "win32_edition": "Home",
        }

        result = get_platform_info()

        assert result["os"] == "Windows"
        assert result["os_id"] == "win32"
        assert result["win32_version"] == "11"
        assert result["win32_edition"] == "Home"

        mock_win32.assert_called_once()

    @patch("sys.platform", "darwin")
    @patch("platform.system")
    @patch("pyautogui2.osal.platform_info.get_darwin_info")
    def test_darwin_platform_integration(self, mock_darwin, mock_system):
        """Integrates common info with MacOS-specific info."""
        mock_system.return_value = "Darwin"
        mock_darwin.return_value = {
            "darwin_version": "13.2.1",
        }

        result = get_platform_info()

        assert result["os"] == "Darwin"
        assert result["os_id"] == "darwin"
        assert result["darwin_version"] == "13.2.1"

        mock_darwin.assert_called_once()

    @patch("sys.platform", "unknown_platform")
    @patch("platform.system")
    def test_unknown_platform_only_common_info(self, mock_system):
        """Returns only common info for unknown platforms."""
        mock_system.return_value = "Unknown"

        result = get_platform_info()

        # Should have common keys only
        assert "os" in result
        assert "os_id" in result
        # Should not have platform-specific keys
        assert "linux_display_server" not in result
        assert "win32_version" not in result
        assert "darwin_version" not in result


class TestMainCLI:
    """Tests for main() CLI function."""

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("pyautogui2.osal.platform_info.get_platform_info")
    def test_main_prints_formatted_output(self, mock_get_info, mock_stdout):
        """main() prints formatted platform information."""
        mock_get_info.return_value = {
            "os": "Linux",
            "os_id": "linux",
            "os_release": "6.8.0",
            "python_version": "3.12.3",
            "architecture": "x86_64",
            "linux_display_server": "wayland",
            "linux_desktop": "GNOME",
            "linux_compositor": "gnome_shell",
        }

        main()

        output = mock_stdout.getvalue()

        # Check header
        assert "PyAutoGUI Platform Detection" in output
        assert "=" * 50 in output

        # Check formatted keys
        assert "OS                  : Linux" in output
        assert "Display Server      : wayland" in output
        assert "Desktop Environment : GNOME" in output
        assert "Compositor          : gnome_shell" in output

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("pyautogui2.osal.platform_info.get_platform_info")
    def test_main_handles_minimal_info(self, mock_get_info, mock_stdout):
        """main() handles minimal platform info (unknown platform)."""
        mock_get_info.return_value = {
            "os": "Unknown",
            "os_id": "unknown",
            "os_release": "0.0",
            "python_version": "3.12.0",
            "architecture": "unknown",
        }

        main()

        output = mock_stdout.getvalue()

        assert "OS             : Unknown" in output
        assert "Python Version : 3.12.0" in output

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("pyautogui2.osal.platform_info.get_platform_info")
    def test_main_formats_all_label_types(self, mock_get_info, mock_stdout):
        """main() correctly formats all possible label types."""
        # Include all possible keys
        mock_get_info.return_value = {
            "os": "Linux",
            "os_id": "linux",
            "os_release": "6.8.0",
            "python_version": "3.12.3",
            "architecture": "x86_64",
            "linux_display_server": "wayland",
            "linux_desktop": "GNOME",
            "linux_compositor": "gnome_shell",
            "win32_version": "11",  # Will be ignored on Linux but tests label
            "win32_edition": "Pro",
            "darwin_version": "13.2",
        }

        main()

        output = mock_stdout.getvalue()

        # Verify all labels are present (even if values don't make sense together)
        assert "OS Identifier" in output
        assert "Architecture" in output
