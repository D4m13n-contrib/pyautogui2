"""Mock for AppKit framework."""

from unittest.mock import MagicMock


class MockNSPoint:
    """Mock for NSPoint-like object returned by pointerLocation."""

    def __init__(self, x: float = 100, y: float = 200) -> None:
        self.x = x
        self.y = y

    def __str__(self):
        return f"{self.__class__.__name__}(x={self.x}, y={self.y})"


class MockNSSize:
    """Mock for NSSize-like object."""

    def __init__(self, width: float = 1920, height: float = 1080) -> None:
        self.width = width
        self.height = height

    def sizeValue(self) -> tuple:
        return (self.width, self.height)


class MockNSRect:
    """Mock for NSRect-like object returned by screen.frame()."""

    def __init__(self, x: float = 0, y: float = 0,
                 width: float = 1920, height: float = 1080) -> None:
        self.origin = MockNSPoint(x, y)
        self.size = MockNSSize(width, height)


class MockAppKit:
    """Reusable mock object simulating AppKit framework.
    Instances are safe to use as a direct replacement for the AppKit module.
    """

    def __init__(self) -> None:
        self._pointer_position = MockNSPoint(100, 200)
        self._screen_size = MockNSSize(1920, 1080)

        # NSDeviceSize constant
        self.NSDeviceSize = "NSDeviceSize"

        # NSScreen
        self.NSScreen = MagicMock()
        self.NSScreen.mainScreen.side_effect = self._main_screen
        self.NSScreen.screens.side_effect = self._screens

        # NSEvent
        self.NSEvent = MagicMock()
        self.NSEvent.mouseLocation.side_effect = self._mouse_location

    def _main_screen(self) -> MagicMock:
        screen = MagicMock()
        screen.deviceDescription.return_value = {
            self.NSDeviceSize: self._screen_size,
        }
        screen.frame.return_value = MockNSRect(
            width=self._screen_size.width,
            height=self._screen_size.height,
        )
        screen.backingScaleFactor.return_value = 1.0
        return screen

    def _screens(self) -> list:
        return [self._main_screen(), self._main_screen()]

    def _mouse_location(self) -> MockNSPoint:
        return self._pointer_position

    def mock_set_pointer_position(self, x: int, y: int) -> None:
        """Set the mock cursor position in standard (top-left origin) coordinates."""
        # Convert to MacOS bottom-left origin for mouseLocation()
        y_macos = self._screen_size.height - y
        self._pointer_position = MockNSPoint(x, y_macos)

    def mock_set_screen_size(self, width: float, height: float) -> None:
        """Helper to change screen dimensions for testing."""
        self._screen_size = MockNSSize(width, height)

    def reset_mock(self, **kwargs):
        self.NSScreen.reset_mock(**kwargs)
        self.NSScreen.mainScreen.reset_mock(**kwargs)
        self.NSScreen.screens.reset_mock(**kwargs)
        self.NSEvent.reset_mock(**kwargs)
        self.NSEvent.pointerLocation.reset_mock(**kwargs)
