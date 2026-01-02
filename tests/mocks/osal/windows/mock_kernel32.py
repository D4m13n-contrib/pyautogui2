"""Mock Kernel32 for Windows OSAL layer."""

from unittest.mock import MagicMock


class MockKernel32:
    """Reusable mock object simulating kernel32.dll behavior.
    Instances are safe to use as a direct replacement for the module-level `kernel32`.
    """

    def __init__(self) -> None:
        self.GetLastError = MagicMock(return_value=0)

    def reset_mock(self, **kwargs):
        self.GetLastError.reset_mock(**kwargs)
