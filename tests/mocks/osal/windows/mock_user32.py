"""Mock User32 for Windows OSAL layer."""

from unittest.mock import MagicMock


class MockUser32:
    """Reusable mock object simulating user32.dll behavior.
    Instances are safe to use as a direct replacement for the module-level `user32`.
    """

    def __init__(self) -> None:
        self._position = (10, 10)

        # Core function mocks used by _common.py
        self.SendInput = MagicMock(return_value=1)
        self.SetProcessDPIAware = MagicMock(return_value=None)

        # Core function mocks used by pointer.py
        self.GetCursorPos = MagicMock(side_effect=self._get_cursor_pos)
        self.SetCursorPos = MagicMock(side_effect=self._set_cursor_pos)
        self.GetSystemMetrics = MagicMock(side_effect=self._get_system_metrics)
        self.mouse_event = MagicMock(return_value=None)
        self.MessageBoxW = MagicMock(return_value=1)

        # Core function mocks used by keyboard.py
        self.GetForegroundWindow = MagicMock(return_value=0)
        self.GetWindowThreadProcessId = MagicMock(return_value=0)
        self.GetKeyboardLayout = MagicMock(return_value=0x0409)     # Default US layout
        self.keybd_event = MagicMock(return_value=None)
        self.MapVirtualKeyW = MagicMock(return_value=0)

        # Core function mocks used by screen.py
        self.EnumDisplayMonitors = MagicMock(return_value=True)
        self.MonitorFromWindow = MagicMock(return_value=True)
        self.GetDesktopWindow = MagicMock(return_value=True)
        self.GetMonitorInfoW = MagicMock(return_value=True)

    def _get_system_metrics(self, index: int) -> int:
        """Default fake screen metrics:
        - SM_CXSCREEN (0) -> 1920,
        - SM_CYSCREEN (1) -> 1080,
        - SM_SWAPBUTTON (23) -> 0 (left primary).
        """
        metrics = {
            0: 1920,    # SM_CXSCREEN
            1: 1080,    # SM_CYSCREEN
            23: 0,      # SM_SWAPBUTTON
        }
        return metrics.get(index, 0)

    def _get_cursor_pos(self, point):
        point.x = self._position[0]
        point.y = self._position[1]
        return True

    def _set_cursor_pos(self, x, y):
        self._position = (x, y)
        return True

    def mock_set_position(self, x, y):
        self._position = (x, y)

    def reset_mock(self, **kwargs):
        self.SendInput.reset_mock(**kwargs)
        self.SetProcessDPIAware.reset_mock(**kwargs)

        self.GetCursorPos.reset_mock(**kwargs)
        self.SetCursorPos.reset_mock(**kwargs)
        self.GetSystemMetrics.reset_mock(**kwargs)
        self.mouse_event.reset_mock(**kwargs)
        self.MessageBoxW.reset_mock(**kwargs)

        self.GetKeyboardLayout.reset_mock(**kwargs)
        self.keybd_event.reset_mock(**kwargs)
        self.MapVirtualKeyW.reset_mock(**kwargs)

        self.EnumDisplayMonitors.reset_mock(**kwargs)
        self.MonitorFromWindow.reset_mock(**kwargs)
        self.GetDesktopWindow.reset_mock(**kwargs)
        self.GetMonitorInfoW.reset_mock(**kwargs)
