"""Tests for pyautogui2.osal.windows._common."""

from unittest.mock import MagicMock, patch


class TestIsLegacyWindows:

    def test_no_getwindowsversion(self, isolated_windows):
        from pyautogui2.osal.windows._common import is_legacy_windows

        with patch("pyautogui2.osal.windows._common.sys", spec=[]):
            assert is_legacy_windows() is True

    def test_major_less_than_6(self, isolated_windows):
        from pyautogui2.osal.windows._common import is_legacy_windows

        fake_ver = MagicMock(major=5, minor=1)
        with patch("pyautogui2.osal.windows._common.sys") as mock_sys:
            mock_sys.getwindowsversion.return_value = fake_ver
            assert is_legacy_windows() is True

    def test_major_greater_than_6(self, isolated_windows):
        from pyautogui2.osal.windows._common import is_legacy_windows

        fake_ver = MagicMock(major=6, minor=0)
        with patch("pyautogui2.osal.windows._common.sys") as mock_sys:
            mock_sys.getwindowsversion.return_value = fake_ver
            assert is_legacy_windows() is False

    def test_exception_returns_true(self, isolated_windows):
        from pyautogui2.osal.windows._common import is_legacy_windows

        with patch("pyautogui2.osal.windows._common.sys") as mock_sys:
            mock_sys.getwindowsversion.side_effect = RuntimeError("boom")
            assert is_legacy_windows() is True


class TestEnsureDpiAware:

    def test_success(self, isolated_windows):
        from pyautogui2.osal.windows._common import ensure_dpi_aware

        user32 = MagicMock()
        ensure_dpi_aware(user32)
        user32.SetProcessDPIAware.assert_called_once()

    def test_attribute_error(self, isolated_windows):
        from pyautogui2.osal.windows._common import ensure_dpi_aware

        user32 = MagicMock()
        user32.SetProcessDPIAware.side_effect = AttributeError
        ensure_dpi_aware(user32)  # should not raise


class TestSendInput:

    def test_success(self, isolated_windows):
        from pyautogui2.osal.windows._common import INPUT, send_input

        user32 = MagicMock()
        user32.SendInput.return_value = 1
        assert send_input(user32, INPUT()) is True

    def test_failure(self, isolated_windows):
        from pyautogui2.osal.windows._common import INPUT, send_input

        user32 = MagicMock()
        user32.SendInput.return_value = 0
        assert send_input(user32, INPUT()) is False


class TestGetLastError:

    def test_ctypes_get_last_error(self, isolated_windows):
        from pyautogui2.osal.windows._common import get_last_error

        kernel32 = MagicMock()
        with patch(
            "pyautogui2.osal.windows._common.ctypes"
        ) as mock_ct:
            mock_ct.get_last_error.return_value = 42
            assert get_last_error(kernel32) == 42

    def test_fallback_kernel32(self, isolated_windows):
        import ctypes

        from pyautogui2.osal.windows._common import get_last_error

        kernel32 = MagicMock()
        kernel32.GetLastError.return_value = 7
        with patch("pyautogui2.osal.windows._common.ctypes") as mock_ct:
            del mock_ct.get_last_error  # hasattr returns False
            mock_ct.sizeof = ctypes.sizeof
            mock_ct.byref = ctypes.byref
            # Provide real hasattr behavior for kernel32
            assert get_last_error(kernel32) == 7

    def test_no_method_available(self, isolated_windows):
        from pyautogui2.osal.windows._common import get_last_error

        kernel32 = MagicMock(spec=[])  # no GetLastError
        with patch("pyautogui2.osal.windows._common.ctypes") as mock_ct:
            del mock_ct.get_last_error
            assert get_last_error(kernel32) == 0
