"""WindowsPointer."""

import ctypes
import logging
import math

from ctypes import wintypes
from typing import Any, Optional

from ...utils.exceptions import PyAutoGUIException
from ...utils.lazy_import import lazy_import, lazy_load_object
from ...utils.types import ButtonName, Point
from ..abstract_cls import AbstractPointer
from ._common import INPUT, MOUSEINPUT, ensure_dpi_aware, is_legacy_windows, send_input


class WindowsPointer(AbstractPointer):
    """Windows-specific pointer/mouse operations implementation.

    Uses Windows API functions like SendInput, SetCursorPos, and mouse_event
    for mouse control and monitoring.

    Implementation Notes:
        - Prefer SendInput for modern Windows versions (Vista+).
        - Falls back to legacy methods (mouse_event) when needed.
        - Handles DPI scaling through process-level DPI awareness.
    """

    _user32 = lazy_load_object("user32", lambda: ctypes.WinDLL("user32", use_last_error=True))
    _kernel32 = lazy_load_object("kernel32", lambda: ctypes.WinDLL("kernel32", use_last_error=True))

    # --- Constants ---
    INPUT_MOUSE = 0

    SM_CXSCREEN = 0
    SM_CYSCREEN = 1
    SM_SWAPBUTTON = 23

    WHEEL_DELTA = 120

    # Mouse event flags
    MOUSEEVENTF_MOVE        = 0x0001
    MOUSEEVENTF_LEFTDOWN    = 0x0002
    MOUSEEVENTF_LEFTUP      = 0x0004
    MOUSEEVENTF_RIGHTDOWN   = 0x0008
    MOUSEEVENTF_RIGHTUP     = 0x0010
    MOUSEEVENTF_MIDDLEDOWN  = 0x0020
    MOUSEEVENTF_MIDDLEUP    = 0x0040
    MOUSEEVENTF_WHEEL       = 0x0800
    MOUSEEVENTF_HWHEEL      = 0x1000
    MOUSEEVENTF_ABSOLUTE    = 0x8000

    BUTTON_NAME_MAPPING = {
        ButtonName.LEFT:      (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
        ButtonName.MIDDLE:    (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
        ButtonName.RIGHT:     (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
        ButtonName.PRIMARY:   None,      # set in setup_postinit()
        ButtonName.SECONDARY: None,      # set in setup_postinit()
    }

    _mouseinfo = lazy_import("mouseinfo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._legacy_mode: Optional[bool] = None

    def setup_postinit(self, *args, **kwargs):
        super().setup_postinit(*args, **kwargs)

        ensure_dpi_aware(self._kernel32)

        if self.get_primary_button() == ButtonName.LEFT:
            self.BUTTON_NAME_MAPPING[ButtonName.PRIMARY] = self.BUTTON_NAME_MAPPING[ButtonName.LEFT]
            self.BUTTON_NAME_MAPPING[ButtonName.SECONDARY] = self.BUTTON_NAME_MAPPING[ButtonName.RIGHT]
        else:
            self.BUTTON_NAME_MAPPING[ButtonName.PRIMARY] = self.BUTTON_NAME_MAPPING[ButtonName.RIGHT]
            self.BUTTON_NAME_MAPPING[ButtonName.SECONDARY] = self.BUTTON_NAME_MAPPING[ButtonName.LEFT]

    def _is_legacy(self):
        """Returns whether the system is in legacy mode."""
        if self._legacy_mode is None:
            self._legacy_mode = is_legacy_windows()
            if self._legacy_mode:
                logging.warning("WindowsPointer: legacy mode enabled")

        return self._legacy_mode

    def _build_input(self,
                     x: int = 0, y: int = 0,
                     data: int = 0, flags: int = 0):
        """Builds an INPUT structure for SendInput.

        Args:
            x: X coordinate (0-65535 for absolute coordinates).
            y: Y coordinate (0-65535 for absolute coordinates).
            data: mouse data.
            flags: MOUSEEVENTF flags.

        Returns:
            INPUT structure ready for SendInput.

        Implementation Notes:
            - Converts screen coordinates to absolute coordinates.
            - Sets up the INPUT structure with proper fields.
        """
        mi = MOUSEINPUT()
        mi.dx = x
        mi.dy = y
        mi.mouseData = data
        mi.dwFlags = flags
        mi.time = 0
        mi.dwExtraInfo = 0

        inp = INPUT()
        inp.type = self.INPUT_MOUSE
        inp.u.mi = mi

        return inp

    def mouse_info(self) -> None:
        self._mouseinfo.MouseInfoWindow()

    def get_primary_button(self) -> ButtonName:
        """Implementation Notes:
        - Uses GetSystemMetrics(SM_SWAPBUTTON):
            Nonzero if the meanings of the left and right mouse buttons are swapped; otherwise, 0.
        """
        swap = self._user32.GetSystemMetrics(self.SM_SWAPBUTTON)
        primary = ButtonName.RIGHT if swap else ButtonName.LEFT
        return primary

    def get_pos(self) -> Point:
        """Implementation Notes:
        - Uses GetCursorPos for screen coordinates.
        - Returns (0,0) for top-left corner of primary monitor.
        """
        pt = wintypes.POINT()
        if not self._user32.GetCursorPos(ctypes.byref(pt)):
            raise PyAutoGUIException("Error: GetCursorPos failed")
        return Point(pt.x, pt.y)

    def move_to(self, x: int, y: int, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Uses SendInput with absolute coordinates when available.
        - Falls back to SetCursorPos for legacy systems.
        - Converts screen coordinates to 0-65535 range.
        """
        screen_w = self._user32.GetSystemMetrics(self.SM_CXSCREEN)
        screen_h = self._user32.GetSystemMetrics(self.SM_CYSCREEN)
        if screen_w <= 1 or screen_h <= 1:
            raise RuntimeError("Invalid screen size from GetSystemMetrics")

        abs_x = min(65535, math.ceil(x * 65535 / (screen_w - 1)))
        abs_y = min(65535, math.ceil(y * 65535 / (screen_h - 1)))

        ev = self.MOUSEEVENTF_MOVE | self.MOUSEEVENTF_ABSOLUTE

        if not self._is_legacy():
            inp = self._build_input(x=abs_x, y=abs_y, flags=ev)
            if send_input(self._user32, inp):
                return
            logging.warning("SendInput failed in move_to -> falling back to legacy")

        # Legacy fallback
        try:
            # Prefer SetCursorPos for absolute movement
            if not self._user32.SetCursorPos(x, y):
                # Last resort: mouse_event absolute move
                self._user32.mouse_event(ev, abs_x, abs_y, 0, 0)
        except Exception as e:
            raise PyAutoGUIException("Error: move_to fallback failed") from e

    def drag_to(self, x: int, y: int, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any):
        """Implementation Notes:
        - Presses the button, moves, then releases.
        - Uses move_to with _pause=False to avoid delays.
        """
        self.button_down(button, _pause=False)
        self.move_to(x, y, _pause=False)
        self.button_up(button, _pause=False)

    def _emit_button(self, button: ButtonName, press: bool) -> None:
        """Low-level emitter for button press/release."""
        down_flag, up_flag = self.BUTTON_NAME_MAPPING[button]
        flag = down_flag if press else up_flag

        if not self._is_legacy():
            inp = self._build_input(flags=flag)
            if send_input(self._user32, inp):
                return
            logging.warning("SendInput failed for button -> fallback to mouse_event")

        self._user32.mouse_event(flag, 0, 0, 0, 0)

    @AbstractPointer.button_decorator
    def button_down(self, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Uses MOUSEEVENTF_LEFTDOWN/RIGHTDOWN.
        - Tracks button state to prevent multiple presses.
        - Uses SendInput when available.
        """
        self._emit_button(button, press=True)

    @AbstractPointer.button_decorator
    def button_up(self, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Uses MOUSEEVENTF_LEFTUP/RIGHTUP.
        - Uses SendInput when available.
        """
        self._emit_button(button, press=False)

    def scroll(self, dx: Optional[int] = None, dy: Optional[int] = None, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Uses MOUSEEVENTF_WHEEL for vertical scrolling.
        - Uses MOUSEEVENTF_HWHEEL for horizontal scrolling.
        - Each "click" is 120 units (Windows standard).
        """
        def _send_input(ev, value):
            value = int(value * self.WHEEL_DELTA)
            inp = self._build_input(data=value, flags=ev)

            if not self._is_legacy():
                if send_input(self._user32, inp):
                    return
                logging.warning("SendInput failed for scroll -> fallback")

            self._user32.mouse_event(ev, 0, 0, value, 0)

        if dy is not None and dy != 0:
            _send_input(self.MOUSEEVENTF_WHEEL, dy)

        if dx is not None and dx != 0:
            _send_input(self.MOUSEEVENTF_HWHEEL, dx)

