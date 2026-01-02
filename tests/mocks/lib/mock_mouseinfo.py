"""Mock for mouseinfo functions used by Pointer."""
from unittest.mock import MagicMock


class MockMouseInfo:

    def __init__(self):
        self.MouseInfoWindow = MagicMock()

    def reset_mock(self, **kwargs):
        self.MouseInfoWindow.reset_mock(**kwargs)
