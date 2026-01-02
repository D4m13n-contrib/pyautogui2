"""Simple mock for pygetwindow used by Screen tests."""
from unittest.mock import MagicMock


class MockPyGetWindow:
    def __init__(self) -> None:

        self.Window = MagicMock(return_value={"window": "mock"})
        self.getActiveWindow = MagicMock(return_value={"active": "window"})
        self.getActiveWindowTitle = MagicMock(return_value="Mock Active Window Title")
        self.getWindowAt = MagicMock(return_value={"at": "window"})
        self.getWindowsWithTitle = MagicMock(return_value=[{"title": "Title"}])
        self.getAllWindows = MagicMock(return_value=[{"win": 1}, {"win": 2}])
        self.getAllTitles = MagicMock(return_value=["A", "B", "C"])

    def reset_mock(self, **kwargs):
        self.Window.reset_mock(**kwargs)
        self.getActiveWindow.reset_mock(**kwargs)
        self.getActiveWindowTitle.reset_mock(**kwargs)
        self.getWindowAt.reset_mock(**kwargs)
        self.getWindowsWithTitle.reset_mock(**kwargs)
        self.getAllWindows.reset_mock(**kwargs)
        self.getAllTitles.reset_mock(**kwargs)
