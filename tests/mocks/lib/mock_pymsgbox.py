"""Mock for pymsgbox functions used by Dialogs."""
from unittest.mock import MagicMock


class MockPyMsgBox:

    def __init__(self):
        self.alert = MagicMock()
        self.confirm = MagicMock()
        self.prompt = MagicMock()
        self.password = MagicMock()

    def reset_mock(self, **kwargs):
        self.alert.reset_mock(**kwargs)
        self.confirm.reset_mock(**kwargs)
        self.prompt.reset_mock(**kwargs)
        self.password.reset_mock(**kwargs)
