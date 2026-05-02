"""Mock Winreg for Windows OSAL layer."""

from unittest.mock import MagicMock


class MockWinreg:
    """Reusable mock object simulating winreg behavior.
    Instances are safe to use as a direct replacement for the module-level `winreg`.
    """

    def __init__(self) -> None:
        self.HKEY_LOCAL_MACHINE = 0x80000002
        self.OpenKey = MagicMock(return_value=MagicMock())
        self.QueryValueEx = MagicMock(return_value=("000000409", 1))

    def reset_mock(self, **kwargs):
        self.OpenKey.reset_mock(**kwargs)
        self.QueryValueEx.reset_mock(**kwargs)
