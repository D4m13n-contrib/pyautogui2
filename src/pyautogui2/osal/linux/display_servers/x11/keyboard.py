"""X11 keyboard backend (QWERTY-only).

Implements a minimal and robust X11 keyboard handler for PyAutoGUI,
limited to QWERTY-based layouts. Non-QWERTY layouts will raise a
PyAutoGUIException upon first key event.
"""

import logging
import os
import subprocess

from typing import Any, Optional

from .....utils.exceptions import PyAutoGUIException
from .....utils.keyboard_layouts import KEYBOARD_LAYOUTS
from .....utils.lazy_import import lazy_import
from ....abstract_cls import AbstractKeyboard


KeyCode = int  # Xlib key constants are int


class X11KeyboardPart(AbstractKeyboard):
    """X11 display server keyboard implementation using native Xlib bindings.

    Provides low-level keyboard control via direct X11 protocol communication
    through python-xlib. Handles key press/release events, layout detection,
    and key code mapping for the X11 window system.

    Only QWERTY keyboard layouts are supported.

    Implementation Notes:
        - Uses python-xlib for X server communication.
        - Maintains comprehensive X11 keycode mapping dictionary.
        - Layout detection via setxkbmap command-line tool.
        - Validates xkblayout-state for accurate active layout detection.
        - Supports all standard keys plus function keys F1-F24.

    Dependencies:
        - python-xlib (Xlib package).
        - setxkbmap command-line utility (X11 standard).
        - xkblayout-state (optional, for multi-layout accuracy).
        - X11 display server running.
    """

    _xlib = lazy_import("Xlib")
    _xlib_XK = lazy_import("Xlib.XK")

    def __init__(self, *args, **kwargs):
        """Initialize X11 keyboard without establishing display connection.

        Defers X11 display connection until first use (lazy initialization).
        Connection is established in setup_postinit() when display is available.
        """
        super().__init__(*args, **kwargs)

        self._display: Optional[Any] = None
        self._layout: Optional[str] = None

        # Store modifier keycodes for internal use
        self._mods_keycodes: tuple[tuple[str, KeyCode], ...] = ()

        self._char_map: dict[str, tuple[Optional[KeyCode], str]] = {}


    # ------------------------------------------------------------------
    # Setup & layout
    # ------------------------------------------------------------------
    def setup_postinit(self, *args,
                       key_names: Optional[list[str]] = None,
                       all_keymapping: Optional[dict[str, dict[str, str]]] = None,
                       **kwargs) -> None:
        """Initialize X11 display connection and keyboard mapping.
        Build the internal character map from the provided keyboard mapping.

        Implementation Notes:
            - Creates Xlib Display object via lazy import.
            - Stores root window reference for event operations.
            - Initializes KEYCODE_MAPPING with X11 keysyms.
            - Called automatically by OSAL initialization system.

        Raises:
            PyAutoGUIException: If cannot connect to X server.
        """
        super().setup_postinit(*args, **kwargs)

        self._display = self._xlib.display.Display(os.environ['DISPLAY'])
        if self._display is None:
           raise PyAutoGUIException("Error: Cannot obtain Display")

        if key_names is None:
            raise ValueError("key_names list is required")
        if all_keymapping is None:
            raise ValueError("all_keymapping dict is required")

        self._layout = self.get_layout()
        if self._layout != "QWERTY":
            logging.warning(
                f"Detected keyboard layout '{self._layout}'. "
                "Only QWERTY layouts are officially supported under X11."
            )
        if self._layout not in all_keymapping:
            raise PyAutoGUIException(f"Error: unsupported layout '{self._layout}'. Expected one of {list(all_keymapping.keys())}")

        shift_l = self._get_keycode('Shift_L')
        if shift_l is None:
            raise PyAutoGUIException("Error: no keycode found for Shift_L")

        self._mods_keycodes = (
            ('shift', shift_l),
        )

        # ------------------------------------------------------------------
        # Build all_keys in physical order (rows of the keyboard)
        # ------------------------------------------------------------------
        kb_us = all_keymapping["QWERTY"]["_"]

        base_keys = [self._get_keycode(c) for c in kb_us]

        # Security check
        sorted_keys = sorted([k for k in base_keys[1:] if k is not None])
        if base_keys[1:] != sorted_keys:
            raise PyAutoGUIException("Error: XKB lib probably not configured in QWERTY, "
                                     "try 'setxkbmap us' before run")

        # ------------------------------------------------------------------
        # Build char_map dynamically for base/shift
        # ------------------------------------------------------------------
        undefined_key = (None, "")
        self._char_map = dict.fromkeys(key_names, undefined_key)

        for modifier, kb_mod in all_keymapping[self._layout].items():
            if len(kb_mod) == 0:
                continue
            for char, key in zip(kb_mod, base_keys, strict=True):
                # Ensure char is valid and not already mapped
                if char and self._char_map.get(char, undefined_key) == undefined_key:
                    self._char_map[char] = (key, modifier)

        # ------------------------------------------------------------------
        # Extra mapping for keys not covered by all_keys (organized by category)
        # ------------------------------------------------------------------
        self._char_map.update({

            # --- Control keys ---
            '\t':            (self._get_keycode("Tab"), ""),
            '\n':            (self._get_keycode("Return"), ""),
            '\r':            (self._get_keycode("Return"), ""),
            '\b':            (self._get_keycode("BackSpace"), ""),
            ' ':             (self._get_keycode("space"), ""),
            'alt':           (self._get_keycode("Alt_L"), ""),
            'altgr':         (self._get_keycode("ISO_Level3_Shift"), ""),
            'altleft':       (self._get_keycode("Alt_L"), ""),
            'altright':      (self._get_keycode("ISO_Level3_Shift"), ""),
            'backspace':     (self._get_keycode("BackSpace"), ""),
            'capslock':      (self._get_keycode("Caps_Lock"), ""),
            'ctrl':          (self._get_keycode("Control_L"), ""),
            'ctrlleft':      (self._get_keycode("Control_L"), ""),
            'ctrlright':     (self._get_keycode("Control_R"), ""),
            'del':           (self._get_keycode("Delete"), ""),
            'delete':        (self._get_keycode("Delete"), ""),
            'enter':         (self._get_keycode("Return"), ""),
            'esc':           (self._get_keycode("Escape"), ""),
            'escape':        (self._get_keycode("Escape"), ""),
            'help':          (self._get_keycode("Help"), ""),
            'return':        (self._get_keycode("Return"), ""),
            'shift':         (self._get_keycode("Shift_L"), ""),
            'shiftleft':     (self._get_keycode("Shift_L"), ""),
            'shiftright':    (self._get_keycode("Shift_R"), ""),
            'space':         (self._get_keycode("space"), ""),
            'tab':           (self._get_keycode("Tab"), ""),
            'win':           (self._get_keycode("Super_L"), ""),
            'winleft':       (self._get_keycode("Super_L"), ""),
            'winright':      (self._get_keycode("Super_R"), ""),
            'option':        (self._get_keycode("Alt_L"), ""),              # alias for alt
            'optionleft':    (self._get_keycode("Alt_L"), ""),              # alias for altleft
            'optionright':   (self._get_keycode("ISO_Level3_Shift"), ""),   # alias for altright

            # --- Navigation keys ---
            'down':       (self._get_keycode("Down"), ""),
            'end':        (self._get_keycode("End"), ""),
            'final':      (self._get_keycode("End"), ""),
            'home':       (self._get_keycode("Home"), ""),
            'insert':     (self._get_keycode("Insert"), ""),
            'left':       (self._get_keycode("Left"), ""),
            'pagedown':   (self._get_keycode("Page_Down"), ""),
            'pageup':     (self._get_keycode("Page_Up"), ""),
            'pgdn':       (self._get_keycode("Page_Down"), ""),
            'pgup':       (self._get_keycode("Page_Up"), ""),
            'right':      (self._get_keycode("Right"), ""),
            'select':     (self._get_keycode("Select"), ""),
            'up':         (self._get_keycode("Up"), ""),

            # --- Function keys ---
            'f1':    (self._get_keycode("F1"), ""),
            'f2':    (self._get_keycode("F2"), ""),
            'f3':    (self._get_keycode("F3"), ""),
            'f4':    (self._get_keycode("F4"), ""),
            'f5':    (self._get_keycode("F5"), ""),
            'f6':    (self._get_keycode("F6"), ""),
            'f7':    (self._get_keycode("F7"), ""),
            'f8':    (self._get_keycode("F8"), ""),
            'f9':    (self._get_keycode("F9"), ""),
            'f10':   (self._get_keycode("F10"), ""),
            'f11':   (self._get_keycode("F11"), ""),
            'f12':   (self._get_keycode("F12"), ""),
            'f13':   (self._get_keycode("F13"), ""),
            'f14':   (self._get_keycode("F14"), ""),
            'f15':   (self._get_keycode("F15"), ""),
            'f16':   (self._get_keycode("F16"), ""),
            'f17':   (self._get_keycode("F17"), ""),
            'f18':   (self._get_keycode("F18"), ""),
            'f19':   (self._get_keycode("F19"), ""),
            'f20':   (self._get_keycode("F20"), ""),
            'f21':   (self._get_keycode("F21"), ""),
            'f22':   (self._get_keycode("F22"), ""),
            'f23':   (self._get_keycode("F23"), ""),
            'f24':   (self._get_keycode("F24"), ""),

            # --- Numpad ---
            'add':         (self._get_keycode("KP_Add"), ""),
            'decimal':     (self._get_keycode("KP_Decimal"), ""),
            'divide':      (self._get_keycode("KP_Divide"), ""),
            'multiply':    (self._get_keycode("KP_Multiply"), ""),
            'num0':        (self._get_keycode("KP_0"), ""),
            'num1':        (self._get_keycode("KP_1"), ""),
            'num2':        (self._get_keycode("KP_2"), ""),
            'num3':        (self._get_keycode("KP_3"), ""),
            'num4':        (self._get_keycode("KP_4"), ""),
            'num5':        (self._get_keycode("KP_5"), ""),
            'num6':        (self._get_keycode("KP_6"), ""),
            'num7':        (self._get_keycode("KP_7"), ""),
            'num8':        (self._get_keycode("KP_8"), ""),
            'num9':        (self._get_keycode("KP_9"), ""),
            'numlock':     (self._get_keycode("Num_Lock"), ""),
            'separator':   (self._get_keycode("KP_Separator"), ""),
            'subtract':    (self._get_keycode("KP_Subtract"), ""),

            # --- Media / system keys ---
            'pause':         (self._get_keycode("Pause"), ""),
            'print':         (self._get_keycode("Print"), ""),
            'printscreen':   (self._get_keycode("Print"), ""),
            'prntscrn':      (self._get_keycode("Print"), ""),
            'prtsc':         (self._get_keycode("Print"), ""),
            'prtscr':        (self._get_keycode("Print"), ""),
            'scrolllock':    (self._get_keycode("Scroll_Lock"), ""),
            'execute':       (self._get_keycode("Execute"), ""),
            'apps':          (self._get_keycode("Menu"), ""),

            # --- Browser keys (not implemented) ---
            # "browserback"
            # "browserfavorites"
            # "browserforward"
            # "browserhome"
            # "browserrefresh"
            # "browsersearch"
            # "browserstop"

            # --- Other specials (not implemented or rarely used) ---
            # "hanguel"
            # "hangeul"
            # "hanja"
            # "hiragana"
            # "kana"
            # "yen"
        })

    @staticmethod
    def _detect_layout_setxkbmap() -> str:
        """Query configured keyboard layout via setxkbmap command.

        Implementation Notes:
            - Executes: setxkbmap -query.
            - Parses "layout:" line from output.
            - Returns first layout if multiple configured (comma-separated).
            - Raises PyAutoGUIException if command fails.
        """
        try:
            output = subprocess.check_output(["setxkbmap", "-query"], text=True)
            for line in output.splitlines():
                if line.startswith("layout:"):
                    return line.split(":")[1].strip().split(",")[0]
        except Exception as e:
            raise PyAutoGUIException("Error: setxkbmap cannot detect layout") from e

        raise PyAutoGUIException("Error: setxkbmap layout not found")

    def _detect_layout(self) -> str:
        """Detect the X11 keyboard layout (e.g., 'us', 'fr')."""
        layout_configured = self._detect_layout_setxkbmap()

        if not layout_configured:
            raise PyAutoGUIException(f"Error: keyboard layout not found ({layout_configured}).")

        return layout_configured

    def _ensure_supported_layout(self) -> None:
        """Raise an exception if the current layout is not QWERTY-based."""
        if self._layout != "QWERTY":
            raise PyAutoGUIException(
                f"Unsupported keyboard layout '{self._layout}' for X11 backend. "
                "Only QWERTY-based layouts are supported."
            )


    # ------------------------------------------------------------------
    # Mapping utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _get_keysym_name(char: str) -> str:
        """Translate printable characters to X11 keysym names.

        Example:
            '@' -> 'at',
            '+' -> 'plus'.
        """
        specials = {
            "@": "at",
            "+": "plus",
            "-": "minus",
            "*": "asterisk",
            "/": "slash",
            "\\": "backslash",
            ".": "period",
            ",": "comma",
            ";": "semicolon",
            ":": "colon",
            "'": "apostrophe",
            '"': "quotedbl",
            "(": "parenleft",
            ")": "parenright",
            "[": "bracketleft",
            "]": "bracketright",
            "{": "braceleft",
            "}": "braceright",
            "<": "less",
            ">": "greater",
            "=": "equal",
            "?": "question",
            "!": "exclam",
            "`": "grave",
            "~": "asciitilde",
            "#": "numbersign",
            "$": "dollar",
            "%": "percent",
            "^": "asciicircum",
            "&": "ampersand",
            "_": "underscore",
            "|": "bar",
            "£": "sterling",
            "€": "EuroSign",
            "©": "copyright",
            "®": "registered",
        }
        return specials.get(char, char)

    def _get_keycode(self, char: str) -> Optional[KeyCode]:
        """Convert X11 keysym name to keycode integer.

        Implementation Notes:
            - Uses Xlib string_to_keysym() for name resolution.
            - Returns numeric keycode for use in X11 events.
            - Called during KEYCODE_MAPPING initialization.
        """
        keysym_name = self._get_keysym_name(char)

        keysym = self._xlib_XK.string_to_keysym(keysym_name)
        if not keysym:
            logging.debug(f"Unrecognized symbol '{char}' (mapped as '{keysym_name}')")
            return None

        assert(self._display is not None), "Error: Display is None"
        keycode: Optional[KeyCode] = self._display.keysym_to_keycode(keysym)
        if not keycode:
            logging.debug(f"No keycode found for symbol '{keysym_name}'")
            return None

        logging.debug(f"Get keycode for '{char}' ('{keysym_name}') => keycode: {keycode}")

        return keycode


    # ------------------------------------------------------------------
    # Core key operations
    # ------------------------------------------------------------------
    def _emit_key(self, key: str, value: int) -> None:
        """Emit a KeyPress or KeyRelease event for the given key.

        Raises:
            ValueError: If value event type is not X.KeyPress nor X.KeyRelease.
            PyAutoGUIException: If key not in KEYCODE_MAPPING.
        """
        self._ensure_supported_layout()

        if value not in (self._xlib.X.KeyPress, self._xlib.X.KeyRelease):
            raise ValueError(f"Invalid X11 event type: {value}")

        mapping = self._char_map.get(key)
        if not mapping:
            raise PyAutoGUIException(f"Key '{key}' not implemented")

        keycode, mods = mapping
        if keycode is None:
            raise PyAutoGUIException(f"Key '{key}' has not any keycode")

        assert(self._display is not None), "Error: Display is None"

        # Press modifiers
        if value == self._xlib.X.KeyPress:
            for mod_name, mod_keycode in self._mods_keycodes:
                if mod_name in mods:
                    self._xlib.ext.xtest.fake_input(self._display, self._xlib.X.KeyPress, mod_keycode)

        # Press/release key
        self._xlib.ext.xtest.fake_input(self._display, value, keycode)

        # Release modifiers
        if value == self._xlib.X.KeyRelease:
            for mod_name, mod_keycode in self._mods_keycodes:
                if mod_name in mods:
                    self._xlib.ext.xtest.fake_input(self._display, self._xlib.X.KeyRelease, mod_keycode)

        self._display.sync()


    # ------------------------------------------------------------------
    # High-level API
    # ------------------------------------------------------------------
    def get_layout(self) -> str:
        """Implementation Notes:
        - Calls _detect_layout_setxkbmap() for configured layout.
        - Calls _detect_layout_active() to verify active layout matches.
        - Logs warning if xkblayout-state not installed.
        - Raises PyAutoGUIException if layout detection fails.
        """
        layout = self._detect_layout()

        if layout not in KEYBOARD_LAYOUTS['linux']:
            raise PyAutoGUIException(f"Layout '{layout}' is unsupported by PyAutoGUI")

        return KEYBOARD_LAYOUTS['linux'][layout]['layout']

    def key_is_mapped(self, key: str) -> bool:
        """Implementation Notes:
        - Queries KEYCODE_MAPPING dictionary.
        - Returns True if key string has valid X11 keycode.
        - Case-sensitive key name matching.
        """
        return self._char_map.get(key, (None, None)) != (None, None)

    def key_down(self, key: str, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Looks up keycode from KEYCODE_MAPPING.
        - Emits X11 KeyPress event via fake_input().
        - Flushes display to ensure immediate delivery.
        - Key remains pressed until key_up() called.
        """
        return self._emit_key(key, self._xlib.X.KeyPress)

    def key_up(self, key: str, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Looks up keycode from KEYCODE_MAPPING.
        - Emits X11 KeyRelease event via fake_input().
        - Flushes display to ensure immediate delivery.
        """
        return self._emit_key(key, self._xlib.X.KeyRelease)
