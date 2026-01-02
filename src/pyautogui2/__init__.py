"""PyAutoGUI Public API Initialization.

Exposes both the modern class-based API (`PyAutoGUI`) and the legacy
flat API for backward compatibility.

This module exposes the top-level flat API (e.g. `pyautogui.click(x, y)`)
while internally delegating to the object-oriented implementation (`PyAutoGUI`).
"""

from __future__ import annotations

import datetime
import importlib
import os
import sys
import time

from contextlib import contextmanager
from types import ModuleType
from typing import Any

from .controllers.keyboard import KeyboardController
from .core import PyAutoGUI
from .utils.singleton import Singleton
from .utils.tweening import TweeningManager
from .utils.types import ButtonName, Point, Size


__version__ = "1.0.0"


# ---------------------------------------------------------------------------
# Lazy proxy implementation
# ---------------------------------------------------------------------------
class _LazyPyAutoGUI(ModuleType):
    """Lazily exposes PyAutoGUI's public methods and constants at the top-level.

    Lazily exposes Legacy API too.
    Users can still do: import pyautogui2; pyautogui.click(10, 10)
    while internally this delegates to PyAutoGUI.pointer.click().

    Example:
        >>> import pyautogui2
        >>> pyautogui.click(100, 200)
        >>> pyautogui.LEFT
    """

    PyAutoGUI = PyAutoGUI  # Expose the real class for explicit imports

    _legacy_mapping = {
        # --- Pointer ---
        "position":     ("pointer", "get_position"),
        "onScreen":     ("pointer", "on_screen"),
        "mouseInfo":    ("pointer", "mouse_info"),

        # --- Keyboard ---
        "hotkey":       ("keyboard", "hotkey"),
        "shortcut":     ("keyboard", "hotkey"),     # shortcut() is an alias for hotkey()
        "isValidKey":   ("keyboard", "is_valid_key"),

        # --- Screen ---
        "screenshot":               ("screen", "screenshot"),
        "locate":                   ("screen", "locate"),
        "locateAll":                ("screen", "locate_all"),
        "locateOnScreen":           ("screen", "locate_on_screen"),
        "locateAllOnScreen":        ("screen", "locate_all_on_screen"),
        "locateCenterOnScreen":     ("screen", "locate_center_on_screen"),
        "pixel":                    ("screen", "pixel"),
        "pixelMatchesColor":        ("screen", "pixel_matches_color"),
        "getAllWindows":            ("screen", "get_all_windows"),
        "getAllTitles":             ("screen", "get_all_titles"),
        "getActiveWindow":          ("screen", "get_active_window"),
        "getActiveWindowTitle":     ("screen", "get_active_window_title"),
        "center":                   ("screen", "center"),
        "size":                     ("screen", "get_size"),
        "resolution":               ("screen", "get_size"), # resolution() is an alias for size()

        # --- Dialogs ---
        "alert":        ("dialogs", "alert"),
        "confirm":      ("dialogs", "confirm"),
        "prompt":       ("dialogs", "prompt"),
        "password":     ("dialogs", "password"),
    }

    _legacy_locals = {
        # --- Keyboard ---
        "keyDown":      "_legacy_key_down",
        "keyUp":        "_legacy_key_up",
        "press":        "_legacy_press",
        "hold":         "_legacy_hold",
        "typewrite":    "_legacy_typewrite",
        "write":        "_legacy_typewrite",    # In PyAutoGUI 1.0, write() replaces typewrite().
        # --- Pointer ---
        "moveTo":       "_legacy_move_to",
        "moveRel":      "_legacy_move_rel",
        "move":         "_legacy_move_rel",   # For PyAutoGUI 1.0, move() replaces moveRel().
        "dragTo":       "_legacy_drag_to",
        "dragRel":      "_legacy_drag_rel",
        "drag":         "_legacy_drag_rel",   # For PyAutoGUI 1.0, we want drag() to replace dragRel().
        "click":        "_legacy_click",
        "doubleClick":  "_legacy_double_click",
        "tripleClick":  "_legacy_triple_click",
        "rightClick":   "_legacy_right_click",
        "leftClick":    "_legacy_left_click",
        "middleClick":  "_legacy_middle_click",
        "scroll":       "_legacy_scroll",
        "hscroll":      "_legacy_hscroll",
        "vscroll":      "_legacy_vscroll",
        "mouseDown":    "_legacy_mouse_down",
        "mouseUp":      "_legacy_mouse_up",
        # --- Misc ---
        "run":             "_legacy_run",
        "sleep":           "_legacy_sleep",
        "countdown":       "_legacy_countdown",
        "getPointOnLine":  "_legacy_get_point_on_line",
        # --- Debug ---
        "displayMousePosition":  "_legacy_display_mouse_position",
        "printInfo":             "_legacy_print_info",
        "getInfo":               "_legacy_get_info",
        "_snapshot":             "_legacy_snapshot",
    }

    _exposed_types = {"Point": Point, "Size": Size}

    _exposed_constants = {
        "KEY_NAMES": KeyboardController.KEY_NAMES,
        "KEYBOARD_KEYS": KeyboardController.KEY_NAMES,
        "LEFT": ButtonName.LEFT,
        "MIDDLE": ButtonName.MIDDLE,
        "RIGHT": ButtonName.RIGHT,
        "PRIMARY": ButtonName.PRIMARY,
        "SECONDARY": ButtonName.SECONDARY,
    }

    def __getattr__(self, name: str) -> Any:
        # Short-circuit submodule access - never instantiate PyAutoGUI for these
        _submodules = {"settings", "utils", "osal", "controllers", "core"}
        if name in _submodules:
            return importlib.import_module(f"pyautogui2.{name}")

        # Expose types
        if name in self._exposed_types:
            return self._exposed_types[name]

        # Expose constants
        if name in self._exposed_constants:
            return self._exposed_constants[name]

        # Instantiate PyAutoGUI only when first needed
        instance = PyAutoGUI()

        # Expose PyAutoGUI methods dynamically
        if hasattr(instance, name):
            return getattr(instance, name)

        # Expose Legacy API
        if name in self._legacy_mapping:
            controller_name, func_name = self._legacy_mapping[name]
            controller = getattr(instance, controller_name)
            return getattr(controller, func_name)

        # Expose old Legacy functions
        if name in self._legacy_locals:
            return getattr(self, self._legacy_locals[name])

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def _reset_instance(self):
        """Reset the internal instance so the next access creates a fresh one."""
        Singleton.remove_instance("PyAutoGUI")


    # --- Legacy Keyboard ---
    def _legacy_key_down(self, key, logScreenshot=None, _pause=True):
        """Perform a keyboard key press without the release. This will put that
        key in a held down state.

        NOTE: For some reason, this does not seem to cause key repeats like would
        happen if a keyboard key was held down on a text field.

        Args:
        key (str): The key to be pressed down. The valid names are listed in
        KEYBOARD_KEYS.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "key": key,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.keyboard.key_down(**kwargs)

    def _legacy_key_up(self, key, logScreenshot=None, _pause=True):
        """Perform a keyboard key release (without the press down beforehand).

        Args:
        key (str): The key to be released up. The valid names are listed in
        KEYBOARD_KEYS.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "key": key,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.keyboard.key_up(**kwargs)

    def _legacy_press(self, keys, presses=1, interval=0.0, logScreenshot=None, _pause=True):
        """Perform a keyboard key press down, followed by a release.

        Args:
        keys (str, list): The key to be pressed. The valid names are listed in
        KEYBOARD_KEYS. Can also be a list of such strings.
        presses (integer, optional): The number of press repetitions.
        1 by default, for just one press.
        interval (float, optional): How many seconds between each press.
        0.0 by default, for no pause between presses.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        if isinstance(keys, list):
            kwargs = {
                "text": keys,
                "interval": interval,
                "_log_screenshot": logScreenshot,
                "_pause": _pause,
            }
            return self.keyboard.write(**kwargs)

        # isinstance(keys, str)
        kwargs = {
            "key": keys,
            "presses": presses,
            "interval": interval,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.keyboard.press_key(**kwargs)

    @contextmanager
    def _legacy_hold(self, keys, logScreenshot=None, _pause=True):
        """Context manager that performs a keyboard key press down upon entry,
        followed by a release upon exit.

        Args:
        keys (str, list): The key to be pressed. The valid names are listed in
        KEYBOARD_KEYS. Can also be a list of such strings.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        with self.keyboard.hold(keys, **kwargs):
            yield

    def _legacy_typewrite(self, message, interval=0.0, logScreenshot=None, _pause=True):
        """Perform a keyboard key press down, followed by a release, for each of
        the characters in message.

        The message argument can also be list of strings, in which case any valid
        keyboard name can be used.

        Since this performs a sequence of keyboard presses and does not hold down
        keys, it cannot be used to perform keyboard shortcuts. Use the hotkey()
        function for that.

        Args:
        message (str, list): If a string, then the characters to be pressed. If a
            list, then the key names of the keys to press in order. The valid names
            are listed in KEYBOARD_KEYS.
        interval (float, optional): The number of seconds in between each press.
            0.0 by default, for no pause in between presses.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "text": message,
            "interval": interval,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.keyboard.write(**kwargs)


    # --- Legacy Pointer ---
    def _legacy_mouse_down(self, x=None, y=None, button=ButtonName.PRIMARY, duration=0.0, tween="linear", logScreenshot=None, _pause=True):
        """Perform pressing a mouse button down (but not up).

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        x (int, float, None, tuple, optional): The x position on the screen where the
            mouse down happens. None by default. If tuple, this is used for x and y.
            If x is a str, it's considered a filename of an image to find on
            the screen with locateOnScreen() and click the center of.
        y (int, float, None, optional): The y position on the screen where the
            mouse down happens. None by default.
        button (str, int, optional): The mouse button pressed down. TODO
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.

        Raises:
        PyAutoGUIException: If button is not one of 'left', 'middle', 'right', 1, 2, or 3.
        """
        kwargs = {
            "x": x,
            "y": y,
            "button": button,
            "duration": duration,
            "tween": tween,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.button_down(**kwargs)

    def _legacy_mouse_up(self, x=None, y=None, button=ButtonName.PRIMARY, duration=0.0, tween="linear", logScreenshot=None, _pause=True):
        """Perform releasing a mouse button up (but not down beforehand).

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        x (int, float, None, tuple, optional): The x position on the screen where the
            mouse up happens. None by default. If tuple, this is used for x and y.
            If x is a str, it's considered a filename of an image to find on
            the screen with locateOnScreen() and click the center of.
        y (int, float, None, optional): The y position on the screen where the
            mouse up happens. None by default.
        button (str, int, optional): The mouse button released. TODO
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.

        Raises:
        PyAutoGUIException: If button is not one of 'left', 'middle', 'right', 1, 2, or 3.
        """
        kwargs = {
            "x": x,
            "y": y,
            "button": button,
            "duration": duration,
            "tween": tween,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.button_up(**kwargs)

    def _legacy_click(self,
        x=None, y=None, clicks=1, interval=0.0, button=ButtonName.PRIMARY, duration=0.0, tween="linear", logScreenshot=None, _pause=True
    ):
        """Perform pressing a mouse button down and then immediately releasing it. Returns ``None``.

        When no arguments are passed, the primary mouse button is clicked at the mouse cursor's current location.

        If integers for ``x`` and ``y`` are passed, the click will happen at that XY coordinate. If ``x`` is a string, the
        string is an image filename that PyAutoGUI will attempt to locate on the screen and click the center of. If ``x``
        is a sequence of two coordinates, those coordinates will be used for the XY coordinate to click on.

        The ``clicks`` argument is an int of how many clicks to make, and defaults to ``1``.

        The ``interval`` argument is an int or float of how many seconds to wait in between each click, if ``clicks`` is
        greater than ``1``. It defaults to ``0.0`` for no pause in between clicks.

        The ``button`` argument is one of the constants ``LEFT``, ``MIDDLE``, ``RIGHT``, ``PRIMARY``, or ``SECONDARY``.
        It defaults to ``PRIMARY`` (which is the left mouse button, unless the operating system has been set for
        left-handed users.)

        If ``x`` and ``y`` are specified, and the click is not happening at the mouse cursor's current location, then
        the ``duration`` argument is an int or float of how many seconds it should take to move the mouse to the XY
        coordinates. It defaults to ``0`` for an instant move.

        If ``x`` and ``y`` are specified and ``duration`` is not ``0``, the ``tween`` argument is a tweening function
        that specifies the movement pattern of the mouse cursor as it moves to the XY coordinates. The default is a
        simple linear tween. See the PyTweening module documentation for more details.

        Raises:
        PyAutoGUIException: If button is not one of 'left', 'middle', 'right', 1, 2, 3.
        """
        kwargs = {
            "x": x,
            "y": y,
            "button": button,
            "clicks": clicks,
            "interval": interval,
            "duration": duration,
            "tween": tween,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.click(**kwargs)

    def _legacy_left_click(self, x=None, y=None, interval=0.0, duration=0.0, tween="linear", logScreenshot=None, _pause=True):
        """Perform a left mouse button click.

        This is a wrapper function for click('left', x, y).

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        x (int, float, None, tuple, optional): The x position on the screen where the
            click happens. None by default. If tuple, this is used for x and y.
            If x is a str, it's considered a filename of an image to find on
            the screen with locateOnScreen() and click the center of.
        y (int, float, None, optional): The y position on the screen where the
            click happens. None by default.
        interval (float, optional): The number of seconds in between each click,
            if the number of clicks is greater than 1. 0.0 by default, for no
            pause in between clicks.
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "x": x,
            "y": y,
            "interval": interval,
            "duration": duration,
            "tween": tween,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.left_click(**kwargs)

    def _legacy_right_click(self, x=None, y=None, interval=0.0, duration=0.0, tween="linear", logScreenshot=None, _pause=True):
        """Perform a right mouse button click.

        This is a wrapper function for click('right', x, y).

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        x (int, float, None, tuple, optional): The x position on the screen where the
            click happens. None by default. If tuple, this is used for x and y.
            If x is a str, it's considered a filename of an image to find on
            the screen with locateOnScreen() and click the center of.
        y (int, float, None, optional): The y position on the screen where the
            click happens. None by default.
        interval (float, optional): The number of seconds in between each click,
            if the number of clicks is greater than 1. 0.0 by default, for no
            pause in between clicks.
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "x": x,
            "y": y,
            "interval": interval,
            "duration": duration,
            "tween": tween,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.right_click(**kwargs)

    def _legacy_middle_click(self, x=None, y=None, interval=0.0, duration=0.0, tween="linear", logScreenshot=None, _pause=True):
        """Perform a middle mouse button click.

        This is a wrapper function for click('middle', x, y).

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        x (int, float, None, tuple, optional): The x position on the screen where the
            click happens. None by default. If tuple, this is used for x and y.
            If x is a str, it's considered a filename of an image to find on
            the screen with locateOnScreen() and click the center of.
        y (int, float, None, optional): The y position on the screen where the
            click happens. None by default.
        interval (float, optional): The number of seconds in between each click,
            if the number of clicks is greater than 1. 0.0 by default, for no
            pause in between clicks.
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "x": x,
            "y": y,
            "interval": interval,
            "duration": duration,
            "tween": tween,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.middle_click(**kwargs)

    def _legacy_double_click(self, x=None, y=None, interval=0.0, button=ButtonName.LEFT, duration=0.0, tween="linear", logScreenshot=None, _pause=True):
        """Perform a double click.

        This is a wrapper function for click('left', x, y, 2, interval).

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        x (int, float, None, tuple, optional): The x position on the screen where the
            click happens. None by default. If tuple, this is used for x and y.
            If x is a str, it's considered a filename of an image to find on
            the screen with locateOnScreen() and click the center of.
        y (int, float, None, optional): The y position on the screen where the
            click happens. None by default.
        interval (float, optional): The number of seconds in between each click,
            if the number of clicks is greater than 1. 0.0 by default, for no
            pause in between clicks.
        button (str, int, optional): The mouse button released. TODO
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.

        Raises:
        PyAutoGUIException: If button is not one of 'left', 'middle', 'right', 1, 2, 3, 4,
            5, 6, or 7.
        """
        kwargs = {
            "x": x,
            "y": y,
            "button": button,
            "interval": interval,
            "duration": duration,
            "tween": tween,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.double_click(**kwargs)

    def _legacy_triple_click(self, x=None, y=None, interval=0.0, button=ButtonName.LEFT, duration=0.0, tween="linear", logScreenshot=None, _pause=True):
        """Perform a triple click.

        This is a wrapper function for click('left', x, y, 3, interval).

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        x (int, float, None, tuple, optional): The x position on the screen where the
            click happens. None by default. If tuple, this is used for x and y.
            If x is a str, it's considered a filename of an image to find on
            the screen with locateOnScreen() and click the center of.
        y (int, float, None, optional): The y position on the screen where the
            click happens. None by default.
        interval (float, optional): The number of seconds in between each click,
            if the number of clicks is greater than 1. 0.0 by default, for no
            pause in between clicks.
        button (str, int, optional): The mouse button released. TODO
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.

        Raises:
        PyAutoGUIException: If button is not one of 'left', 'middle', 'right', 1, 2, 3, 4,
            5, 6, or 7.
        """
        kwargs = {
            "x": x,
            "y": y,
            "button": button,
            "interval": interval,
            "duration": duration,
            "tween": tween,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.triple_click(**kwargs)

    def _legacy_scroll(self, clicks, x=None, y=None, logScreenshot=None, _pause=True):
        """Perform a scroll of the mouse scroll wheel.

        Whether this is a vertical or horizontal scroll depends on the underlying
        operating system.

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        clicks (int, float): The amount of scrolling to perform.
        x (int, float, None, tuple, optional): The x position on the screen where the
            click happens. None by default. If tuple, this is used for x and y.
        y (int, float, None, optional): The y position on the screen where the
            click happens. None by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "clicks": clicks,
            "x": x,
            "y": y,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.scroll(**kwargs)

    def _legacy_hscroll(self, clicks, x=None, y=None, logScreenshot=None, _pause=True):
        """Perform an explicitly horizontal scroll of the mouse scroll wheel,
        if this is supported by the operating system (currently just Linux).

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        clicks (int, float): The amount of scrolling to perform.
        x (int, float, None, tuple, optional): The x position on the screen where the
            click happens. None by default. If tuple, this is used for x and y.
        y (int, float, None, optional): The y position on the screen where the
            click happens. None by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "clicks": clicks,
            "x": x,
            "y": y,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.hscroll(**kwargs)

    def _legacy_vscroll(self, clicks, x=None, y=None, logScreenshot=None, _pause=True):
        """Perform an explicitly vertical scroll of the mouse scroll wheel,
        if this is supported by the operating system (currently just Linux).

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        clicks (int, float): The amount of scrolling to perform.
        x (int, float, None, tuple, optional): The x position on the screen where the
            click happens. None by default. If tuple, this is used for x and y.
        y (int, float, None, optional): The y position on the screen where the
            click happens. None by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "clicks": clicks,
            "x": x,
            "y": y,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.vscroll(**kwargs)

    def _legacy_move_to(self, x=None, y=None, duration=0.0, tween="linear", logScreenshot=False, _pause=True):
        """Moves the mouse cursor to a point on the screen.

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        x (int, float, None, tuple, optional): The x position on the screen where the
            click happens. None by default. If tuple, this is used for x and y.
            If x is a str, it's considered a filename of an image to find on
            the screen with locateOnScreen() and click the center of.
        y (int, float, None, optional): The y position on the screen where the
            click happens. None by default.
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "x": x,
            "y": y,
            "duration": duration,
            "tween": tween,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.move_to(**kwargs)

    def _legacy_move_rel(self, xOffset=None, yOffset=None, duration=0.0, tween="linear", logScreenshot=False, _pause=True):
        """Moves the mouse cursor to a point on the screen, relative to its current
        position.

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        xOffset (int, float, None, tuple, optional): How far left (for negative values) or
            right (for positive values) to move the cursor. 0 by default. If tuple, this is used for x and y.
        yOffset (int, float, None, optional): How far up (for negative values) or
            down (for positive values) to move the cursor. 0 by default.
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the new xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "offset_x": xOffset,
            "offset_y": yOffset,
            "duration": duration,
            "tween": tween,
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.move_rel(**kwargs)

    def _legacy_drag_to(self,
        x=None, y=None, duration=0.0, tween="linear", button=ButtonName.PRIMARY, mouseDownUp=True, logScreenshot=None, _pause=True
    ):
        """Perform a mouse drag (mouse movement while a button is held down) to a
        point on the screen.

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        x (int, float, None, tuple, optional): How far left (for negative values) or
            right (for positive values) to move the cursor. 0 by default. If tuple, this is used for x and y.
            If x is a str, it's considered a filename of an image to find on
            the screen with locateOnScreen() and click the center of.
        y (int, float, None, optional): How far up (for negative values) or
            down (for positive values) to move the cursor. 0 by default.
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the new xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        button (str, int, optional): The mouse button released. TODO
        mouseDownUp (True, False): When true, the mouseUp/Down actions are not performed.
            Which allows dragging over multiple (small) actions. 'True' by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "x": x,
            "y": y,
            "duration": duration,
            "tween": tween,
            "button": button,
            "mouse_down_up": mouseDownUp,       # Legacy compatibility, not used in new implementation
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.drag_to(**kwargs)

    def _legacy_drag_rel(self,
        xOffset=0, yOffset=0, duration=0.0, tween="linear", button=ButtonName.PRIMARY, mouseDownUp=True, logScreenshot=None, _pause=True
    ):
        """Perform a mouse drag (mouse movement while a button is held down) to a
        point on the screen, relative to its current position.

        The x and y parameters detail where the mouse event happens. If None, the
        current mouse position is used. If a float value, it is rounded down. If
        outside the boundaries of the screen, the event happens at edge of the
        screen.

        Args:
        xOffset (int, float, None, tuple, optional): How far left (for negative values) or
            right (for positive values) to move the cursor. 0 by default. If tuple, this is used for xOffset and yOffset.
        yOffset (int, float, None, optional): How far up (for negative values) or
            down (for positive values) to move the cursor. 0 by default.
        duration (float, optional): The amount of time it takes to move the mouse
            cursor to the new xy coordinates. If 0, then the mouse cursor is moved
            instantaneously. 0.0 by default.
        tween (func, optional): The tweening function used if the duration is not
            0. A linear tween is used by default.
        button (str, int, optional): The mouse button released. TODO
        mouseDownUp (True, False): When true, the mouseUp/Down actions are not performed.
            Which allows dragging over multiple (small) actions. 'True' by default.
        logScreenshot: See utils/decorators/log_screenshot.py.
        _pause: See utils/decorators/pause.py.

        Returns:
        None.
        """
        kwargs = {
            "offset_x": xOffset,
            "offset_y": yOffset,
            "duration": duration,
            "tween": tween,
            "button": button,
            "mouse_down_up": mouseDownUp,       # Legacy compatibility, not used in new implementation
            "_log_screenshot": logScreenshot,
            "_pause": _pause,
        }
        return self.pointer.drag_rel(**kwargs)


    # --- Legacy Misc ---
    def _legacy_run(self, *_args, **_kwargs):
        raise NotImplementedError("run() method is no more supported. "
                                  "If you need it please consider to adapt previous "
                                  "version over PyAutoGUI class.")

    def _legacy_sleep(self, seconds):
        time.sleep(seconds)

    def _legacy_countdown(self, seconds):
        for i in range(seconds, 0, -1):
            print(str(i), end=" ", flush=True)
            time.sleep(1)
        print()

    def _legacy_get_point_on_line(self, x1, y1, x2, y2, n):
        return TweeningManager.get_point_on_line(x1, y1, x2, y2, n)


    # --- Legacy Debug ---
    def _legacy_display_mouse_position(self, xOffset=0, yOffset=0):
        """This function is meant to be run from the command line. It will
        automatically display the location and RGB of the mouse cursor.
        """
        try:
            runningIDLE = sys.stdin.__module__.startswith("idlelib")
        except AttributeError:
            runningIDLE = False

        print("Press Ctrl-C to quit.")
        if xOffset != 0 or yOffset != 0:
            print(f"xOffset: {xOffset} yOffset: {yOffset}")
        try:
            while True:
                # Get and print the mouse coordinates.
                x, y = self.pointer.get_position()
                positionStr = "X: " + str(x - xOffset).rjust(4) + " Y: " + str(y - yOffset).rjust(4)
                if not self.pointer.on_screen(x - xOffset, y - yOffset) or sys.platform == "darwin":
                    # Pixel color can only be found for the primary monitor, and also not on mac due to the screenshot having the mouse cursor in the way.
                    pixelColor = ("NaN", "NaN", "NaN")
                else:
                    pixelColor = self.screen.screenshot().getpixel(
                        (x, y)
                    )  # NOTE: On Windows & Linux, getpixel() returns a 3-integer tuple, but on MacOS it returns a 4-integer tuple.
                positionStr += " RGB: (" + str(pixelColor[0]).rjust(3)
                positionStr += ", " + str(pixelColor[1]).rjust(3)
                positionStr += ", " + str(pixelColor[2]).rjust(3) + ")"
                sys.stdout.write(positionStr)
                if not runningIDLE:
                    # If this is a terminal, than we can erase the text by printing \b backspaces.
                    sys.stdout.write("\b" * len(positionStr))
                else:
                    # If this isn't a terminal (i.e. IDLE) then we can only append more text. Print a newline instead and pause a second (so we don't send too much output).
                    sys.stdout.write("\n")
                    time.sleep(1)
                sys.stdout.flush()
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            sys.stdout.flush()

    def _legacy_print_info(self, dontPrint=False):
        platform, py_version, lib_version, executable, screen_size, now = self._legacy_get_info()
        msg = f"""
         Platform: {platform}
   Python Version: {py_version}
PyAutoGUI Version: {lib_version}
       Executable: {executable}
       Resolution: {screen_size}
        Timestamp: {now}"""
        if not dontPrint:
            print(msg)
        return msg

    def _legacy_get_info(self):
        return (sys.platform,
                sys.version,
                __version__,
                sys.executable,
                self.screen.get_size(),
                datetime.datetime.now())

    def _legacy_snapshot(self, tag, folder=None, region=None, radius=None):
        # TODO feature not finished
        if region is not None and radius is not None:
            raise Exception("Either region or radius arguments (or neither) can be passed to snapshot, but not both")

        if radius is not None:
            x, y = self.pointer.get_position()

        if folder is None:
            folder = os.getcwd()

        now = datetime.datetime.now()
        filename = (f"{now.year}-"
                    f"{str(now.month).rjust(2, '0')}-"
                    f"{str(now.day).rjust(2, '0')}_"
                    f"{now.hour}-"
                    f"{now.minute}-"
                    f"{now.second}-"
                    f"{str(now.microsecond)[:3]}_"
                    f"{tag}.png")
        filepath = os.path.join(folder, filename)
        self.screen.screenshot(filepath)

    def __dir__(self) -> list[str]:
        """Expose all available methods and constants for autocompletion."""
        base_dir = list(super().__dir__())
        base_dir += dir(PyAutoGUI())
        base_dir += list(self._legacy_mapping.keys())
        base_dir += list(self._legacy_locals.keys())
        base_dir += list(self._exposed_types.keys())
        base_dir += list(self._exposed_constants.keys())
        return sorted(set(base_dir))


# ---------------------------------------------------------------------------
# Replace this module by a lazy proxy instance in sys.modules
# ---------------------------------------------------------------------------
_lazy_module = _LazyPyAutoGUI(__name__)

sys.modules[__name__] = _lazy_module


__all__ = ["PyAutoGUI"]
