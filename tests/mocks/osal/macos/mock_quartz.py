"""Mock for Quartz framework."""

from unittest.mock import MagicMock


class MockQuartz:
    """Reusable mock object simulating Quartz framework.
    Instances are safe to use as a direct replacement for the Quartz module.
    """

    def __init__(self) -> None:
        self._screen_width = 1920
        self._screen_height = 1080

        # Functions
        self.CGDisplayPixelsHigh = MagicMock(
            side_effect=lambda _: self._screen_height,
        )
        self.CGDisplayPixelsWide = MagicMock(
            side_effect=lambda _: self._screen_width,
        )
        self.CGMainDisplayID = MagicMock(return_value=0)

        self.CGEventCreateKeyboardEvent = MagicMock(return_value=None)
        self.CGEventCreateMouseEvent = MagicMock(return_value=None)
        self.CGEventCreateScrollWheelEvent = MagicMock(return_value=None)
        self.CGEventKeyboardSetUnicodeString = MagicMock(return_value=None)
        self.CGEventPost = MagicMock(return_value=None)
        self.CGEventSourceCreate = MagicMock(side_effect=Exception("Optional"))

        # Constants: event types
        self.kCGEventLeftMouseDown = 1
        self.kCGEventLeftMouseUp = 2
        self.kCGEventMouseMoved = 5
        self.kCGEventLeftMouseDragged = 6
        self.kCGEventRightMouseDown = 3
        self.kCGEventRightMouseUp = 4
        self.kCGEventRightMouseDragged = 7
        self.kCGEventOtherMouseDown = 25
        self.kCGEventOtherMouseUp = 26
        self.kCGEventOtherMouseDragged = 27

        # Constants: source / tap / buttons / scroll
        self.kCGEventSourceStateHIDSystemState = 1
        self.kCGHIDEventTap = 0
        self.kCGMouseButtonLeft = 0
        self.kCGMouseButtonRight = 1
        self.kCGMouseButtonCenter = 2
        self.kCGScrollEventUnitLine = 1

    def mock_set_screen_size(self, width: int, height: int) -> None:
        """Helper to change screen dimensions for testing."""
        self._screen_width = width
        self._screen_height = height

    def reset_mock(self, **kwargs):
        self.CGDisplayPixelsHigh.reset_mock(**kwargs)
        self.CGDisplayPixelsWide.reset_mock(**kwargs)
        self.CGMainDisplayID.reset_mock(**kwargs)
        self.CGEventCreateKeyboardEvent.reset_mock(**kwargs)
        self.CGEventCreateMouseEvent.reset_mock(**kwargs)
        self.CGEventCreateScrollWheelEvent.reset_mock(**kwargs)
        self.CGEventKeyboardSetUnicodeString.reset_mock(**kwargs)
        self.CGEventPost.reset_mock(**kwargs)
        self.CGEventSourceCreate.reset_mock(**kwargs)
