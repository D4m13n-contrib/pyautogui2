"""MacOSPointer."""

import functools
import subprocess
import time

from collections.abc import Callable
from typing import Any, Literal, Optional

from ...settings import DARWIN_CATCH_UP_TIME
from ...utils.exceptions import PyAutoGUIException
from ...utils.lazy_import import lazy_import
from ...utils.types import ButtonName, Point
from ..abstract_cls import AbstractPointer


class MacOSPointer(AbstractPointer):
    """Common MacOS-specific pointer logic."""

    BUTTON_NAME_MAPPING = {
        ButtonName.LEFT:      None,      # set in setup_postinit()
        ButtonName.MIDDLE:    None,      # set in setup_postinit()
        ButtonName.RIGHT:     None,      # set in setup_postinit()
        ButtonName.PRIMARY:   None,      # set in setup_postinit()
        ButtonName.SECONDARY: None,      # set in setup_postinit()
    }

    _MOUSE_EVENTS: dict[str, dict[str, Any]] = {
        "move": {},         # set in setup_postinit()
        "drag": {},         # set in setup_postinit()
        "press": {},        # set in setup_postinit()
        "release": {},      # set in setup_postinit()
    }

    _quartz = lazy_import("Quartz")
    _appkit = lazy_import("AppKit")

    _mouseinfo = lazy_import("mouseinfo")

    def setup_postinit(self, *args, **kwargs):
        super().setup_postinit(*args, **kwargs)

        self.BUTTON_NAME_MAPPING[ButtonName.LEFT] = self._quartz.kCGMouseButtonLeft
        self.BUTTON_NAME_MAPPING[ButtonName.MIDDLE] = self._quartz.kCGMouseButtonCenter
        self.BUTTON_NAME_MAPPING[ButtonName.RIGHT] = self._quartz.kCGMouseButtonRight

        if self.get_primary_button() == ButtonName.LEFT:
            self.BUTTON_NAME_MAPPING[ButtonName.PRIMARY] = self.BUTTON_NAME_MAPPING[ButtonName.LEFT]
            self.BUTTON_NAME_MAPPING[ButtonName.SECONDARY] = self.BUTTON_NAME_MAPPING[ButtonName.RIGHT]
        else:
            self.BUTTON_NAME_MAPPING[ButtonName.PRIMARY] = self.BUTTON_NAME_MAPPING[ButtonName.RIGHT]
            self.BUTTON_NAME_MAPPING[ButtonName.SECONDARY] = self.BUTTON_NAME_MAPPING[ButtonName.LEFT]

        self._MOUSE_EVENTS = {
            "move": {
                "_": self._quartz.kCGEventMouseMoved,
            },
            "drag": {
                self._quartz.kCGMouseButtonLeft:   self._quartz.kCGEventLeftMouseDragged,
                self._quartz.kCGMouseButtonCenter: self._quartz.kCGEventOtherMouseDragged,
                self._quartz.kCGMouseButtonRight:  self._quartz.kCGEventRightMouseDragged,
            },
            "press": {
                self._quartz.kCGMouseButtonLeft:   self._quartz.kCGEventLeftMouseDown,
                self._quartz.kCGMouseButtonCenter: self._quartz.kCGEventOtherMouseDown,
                self._quartz.kCGMouseButtonRight:  self._quartz.kCGEventRightMouseDown,
            },
            "release": {
                self._quartz.kCGMouseButtonLeft:   self._quartz.kCGEventLeftMouseUp,
                self._quartz.kCGMouseButtonCenter: self._quartz.kCGEventOtherMouseUp,
                self._quartz.kCGMouseButtonRight:  self._quartz.kCGEventRightMouseUp,
            },
        }

    def mouse_info(self):
        """Launches the MouseInfo app.
        This application provides mouse coordinate information which can be useful when
        planning GUI automation tasks. This function blocks until the application is closed.
        """
        self._mouseinfo.MouseInfoWindow()

    def get_primary_button(self) -> ButtonName:
        """Strategy:
        1. Try to read system preference via `defaults read`.
            We check several common preference domains where MacOS
            may store the "swap left/right button" setting.
        2. If no info found or error occurs, fallback to ButtonName.LEFT.
        """
        possible_domains = [
            "com.apple.driver.AppleHIDMouse",
            "com.apple.AppleMultitouchMouse",
            "com.apple.mouse",
        ]
        keys = ["swapLeftRightButton", "SwapMouseButtons"]

        for domain in possible_domains:
            for key in keys:
                try:
                    result = subprocess.check_output(
                        ["defaults", "read", domain, key],
                        text=True,
                        stderr=subprocess.DEVNULL
                    ).strip()

                    if result in ("1", "true", "YES"):
                        return ButtonName.RIGHT  # Buttons swapped -> primary is right
                    elif result in ("0", "false", "NO"):
                        return ButtonName.LEFT   # Normal configuration
                except subprocess.CalledProcessError:
                    # Key or domain not found -> continue checking next
                    continue

        # Default fallback
        return ButtonName.LEFT

    def get_pos(self) -> Point:
        loc = self._appkit.NSEvent.mouseLocation()
        if not loc:
            raise PyAutoGUIException("Error: AppKit.NSEvent.mouseLocation() failed")
        return Point(int(loc.x), int(self._quartz.CGDisplayPixelsHigh(0) - loc.y))

    def _send_event(self, ev, x, y, button = None):
        button = button if button is not None else 0
        mouse_event = self._quartz.CGEventCreateMouseEvent(None, ev, (x, y), button)
        self._quartz.CGEventPost(self._quartz.kCGHIDEventTap, mouse_event)

    @staticmethod
    def temporize(wrapped_function: Callable) -> Callable:
        """Decorator to add a sleep after call the wrapped_function.
        Useful to allow OS time to catch up the event (move, drag, etc.).
        """
        @functools.wraps(wrapped_function)
        def wrapper(self, *args, **kwargs):
            res = wrapped_function(self, *args, **kwargs)
            time.sleep(DARWIN_CATCH_UP_TIME)
            return res

        return wrapper

    @temporize
    def move_to(self, x: int, y: int, **_kwargs) -> None:
        ev = self._MOUSE_EVENTS["move"]["_"]
        self._send_event(ev, x, y)

    @temporize
    def drag_to(self, x: int, y: int, button: ButtonName = ButtonName.PRIMARY, **_kwargs):
        _button = self.BUTTON_NAME_MAPPING[button]
        ev = self._MOUSE_EVENTS["drag"][_button]
        self._send_event(ev, x, y, _button)

    def _emit_button(self, button, action: Literal["press", "release"]) -> None:
        ev = self._MOUSE_EVENTS[action][button]
        pos = self.get_pos()
        self._send_event(ev, pos.x, pos.y, button)

    @AbstractPointer.button_decorator
    def button_down(self, button: ButtonName = ButtonName.PRIMARY, **_kwargs) -> None:
        self._emit_button(self.BUTTON_NAME_MAPPING[button], "press")

    @AbstractPointer.button_decorator
    def button_up(self, button: ButtonName = ButtonName.PRIMARY, **_kwargs) -> None:
        self._emit_button(self.BUTTON_NAME_MAPPING[button], "release")

    def scroll(self, dx: Optional[int] = None, dy: Optional[int] = None, **_kwargs) -> None:
        """Implementation Notes:
        - Both dx (horizontal) and dy (vertical) can be nonzero: scrolls diagonally.
        - Large distances are split into chunks of +10/-10, as recommended by Apple:
            According to https://developer.apple.com/library/mac/documentation/Carbon/Reference/QuartzEventServicesRef/Reference/reference.html#//apple_ref/c/func/Quartz.CGEventCreateScrollWheelEvent
            "Scrolling movement is generally represented by small signed integer values, typically in a range from -10 to +10. Large values may have unexpected results, depending on the application that processes the event."
            The scrolling functions will create multiple events that scroll 10 each, and then scroll the remainder.
        """
        def _post_scroll_event(vx: int, vy: int):
            event = self._quartz.CGEventCreateScrollWheelEvent(
                None,   # no source
                self._quartz.kCGScrollEventUnitLine, # units
                2,      # wheelCount: vertical + horizontal
                vy,     # vertical movement
                vx,     # horizontal movement
            )
            self._quartz.CGEventPost(self._quartz.kCGHIDEventTap, event)

        dx = 0 if dx is None else dx
        dy = 0 if dy is None else dy

        # Determine number of full 10-unit steps
        steps = max(abs(dx), abs(dy)) // 10
        remaining_x = dx % 10
        remaining_y = dy % 10

        step_x = 10 if dx >= 0 else -10
        step_y = 10 if dy >= 0 else -10

        # Emit full steps
        for _ in range(steps):
            _post_scroll_event(step_x if dx else 0, step_y if dy else 0)

        # Emit remaining small step
        if remaining_x or remaining_y:
            _post_scroll_event(remaining_x, remaining_y)
