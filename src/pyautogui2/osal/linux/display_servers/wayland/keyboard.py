"""WaylandKeyboardPart - Display server part for all Linux keyboards."""

import time

from typing import Any, Optional

from .....utils.lazy_import import lazy_import
from ....abstract_cls import AbstractKeyboard
from ._common import ensure_device_not_exists


KeyCode = int  # evdev key constants are plain integers


class WaylandKeyboardPart(AbstractKeyboard):
    """Wayland display server keyboard implementation using evdev kernel interface.

    Provides low-level keyboard control via Linux evdev uinput subsystem, which creates
    a virtual input device. Required on Wayland due to security restrictions that
    prevent direct key injection via display server protocols.

    Implementation Notes:
        - Uses python-evdev to create virtual keyboard device.
        - Requires write access to /dev/uinput (typically root or input group).
        - Maintains comprehensive Linux input keycode mapping (KEY_*).
        - Emits EV_KEY events with value 1 (press) and 0 (release).
        - Layout detection delegated to compositor-specific Parts.

    Dependencies:
        - python-evdev library.
        - /dev/uinput kernel interface access.
        - uinput kernel module loaded.

    Limitations:
        - Requires elevated permissions or group membership.
        - No built-in layout detection (compositor must provide).
    """

    _evdev = lazy_import("evdev")
    _ecodes = lazy_import("evdev.ecodes")

    _device_name = "pyautogui-virtual-keyboard"

    def __init__(self, *args, **kwargs):
        """Initialize Wayland keyboard without creating evdev uinput device.

        Defers uinput device creation until setup_postinit().
        """
        super().__init__(*args, **kwargs)

        self._device: Optional[Any] = None

        # Store modifier keycodes for internal use
        self._mods_keycodes: tuple = ()

        self._char_map: dict[str, tuple[KeyCode, str] | tuple[None, None]] = {}

    def setup_postinit(
        self,
        *args,
        key_names: Optional[list[str]] = None,
        all_keymapping: Optional[dict[str, dict[str, str]]] = None,
        **kwargs,
    ) -> None:
        """Create virtual evdev uinput keyboard device with full key support.

        Implementation Notes:
            - Removes controller decorators from key methods.
            - Initializes evdev.UInput with all keys from KEYCODE_MAPPING.
            - Device includes all standard keys, modifiers, and function keys.
            - Device persists until Python process exits.

        Raises:
            RuntimeError: If layout is not supported.
            PermissionError: If no write access to /dev/uinput.
            OSError: If uinput kernel module not loaded.
        """
        super().setup_postinit(*args, **kwargs)

        if key_names is None:
            raise ValueError("key_names list is required")
        if all_keymapping is None:
            raise ValueError("all_keymapping dict is required")

        layout = self.get_layout()
        if layout not in all_keymapping:
            raise ValueError(
                f"Error: '{layout}' layout is not supported ({list(all_keymapping.keys())})"
            )

        ensure_device_not_exists(self._device_name)

        # Create device with all KEY_* codes (excluding meta-constants)
        # KEY_CNT (768) is the bitmap size, not a valid keycode, and would cause
        # OSError: [Errno 22] Invalid argument from the kernel uinput ioctl.
        all_keys = [
            getattr(self._ecodes, name) for name in dir(self._ecodes) if name.startswith("KEY_")
            and isinstance(getattr(self._ecodes, name), int)
            and 0 < getattr(self._ecodes, name) < self._ecodes.KEY_CNT
        ]
        self._device = self._evdev.UInput({self._ecodes.EV_KEY: all_keys}, name=self._device_name)
        time.sleep(0.1)  # Let's give the OS some time to create the device

        self._mods_keycodes = (
            ("shift", self._ecodes.KEY_LEFTSHIFT),
            ("altgr", self._ecodes.KEY_RIGHTALT),
        )

        # ------------------------------------------------------------------
        # Build all_keys in physical order (rows of the keyboard)
        # ------------------------------------------------------------------
        kb_us = all_keymapping["QWERTY"]["_"]
        numbers = kb_us[1:11]  # 1234567890
        letters_1 = kb_us[13:23]  # qwertyuiop
        letters_2 = kb_us[25:34]  # asdfghjkl
        letters_3 = kb_us[37:44]  # zxcvbnm

        def _chars_to_keys(chars):
            """Helper: convert a list of characters into self._ecodes.KEY_* constants."""
            return [getattr(self._ecodes, f"KEY_{c.upper()}") for c in chars]

        base_keys = (
            [self._ecodes.KEY_GRAVE]
            + _chars_to_keys(numbers)
            + [self._ecodes.KEY_MINUS, self._ecodes.KEY_EQUAL]
            + _chars_to_keys(letters_1)
            + [self._ecodes.KEY_LEFTBRACE, self._ecodes.KEY_RIGHTBRACE]
            + _chars_to_keys(letters_2)
            + [self._ecodes.KEY_SEMICOLON, self._ecodes.KEY_APOSTROPHE, self._ecodes.KEY_BACKSLASH]
            + _chars_to_keys(letters_3)
            + [self._ecodes.KEY_COMMA, self._ecodes.KEY_DOT, self._ecodes.KEY_SLASH]
        )

        # ------------------------------------------------------------------
        # Build char_map dynamically for base/shift/altgr/shift+altgr
        # ------------------------------------------------------------------
        undefined_key = (None, None)
        self._char_map = dict.fromkeys(key_names, undefined_key)

        for modifier, kb_mod in all_keymapping[layout].items():
            if len(kb_mod) == 0:
                continue
            for char, key in zip(kb_mod, base_keys, strict=True):
                # Ensure char is valid and not already mapped
                if char and self._char_map.get(char, undefined_key) == undefined_key:
                    self._char_map[char] = (key, modifier)

        # ------------------------------------------------------------------
        # Extra mapping for keys not covered by all_keys (organized by category)
        # ------------------------------------------------------------------
        key_decimal = self._ecodes.KEY_KPDOT  # by default
        if layout in ("AZERTY", "QWERTZ"):
            key_decimal = self._ecodes.KEY_KPCOMMA

        self._char_map.update(
            {
                # --- Control keys ---
                "\t": (self._ecodes.KEY_TAB, ""),
                "\n": (self._ecodes.KEY_ENTER, ""),
                "\r": (self._ecodes.KEY_ENTER, ""),
                "\b": (self._ecodes.KEY_BACKSPACE, ""),
                " ": (self._ecodes.KEY_SPACE, ""),
                "alt": (self._ecodes.KEY_LEFTALT, ""),
                "altgr": (self._ecodes.KEY_RIGHTALT, ""),
                "altleft": (self._ecodes.KEY_LEFTALT, ""),
                "altright": (self._ecodes.KEY_RIGHTALT, ""),
                "backspace": (self._ecodes.KEY_BACKSPACE, ""),
                "capslock": (self._ecodes.KEY_CAPSLOCK, ""),
                "ctrl": (self._ecodes.KEY_LEFTCTRL, ""),
                "ctrlleft": (self._ecodes.KEY_LEFTCTRL, ""),
                "ctrlright": (self._ecodes.KEY_RIGHTCTRL, ""),
                "del": (self._ecodes.KEY_DELETE, ""),
                "delete": (self._ecodes.KEY_DELETE, ""),
                "enter": (self._ecodes.KEY_ENTER, ""),
                "esc": (self._ecodes.KEY_ESC, ""),
                "escape": (self._ecodes.KEY_ESC, ""),
                "fn": (self._ecodes.KEY_FN, ""),
                "help": (self._ecodes.KEY_HELP, ""),
                "return": (self._ecodes.KEY_ENTER, ""),
                "shift": (self._ecodes.KEY_LEFTSHIFT, ""),
                "shiftleft": (self._ecodes.KEY_LEFTSHIFT, ""),
                "shiftright": (self._ecodes.KEY_RIGHTSHIFT, ""),
                "space": (self._ecodes.KEY_SPACE, ""),
                "tab": (self._ecodes.KEY_TAB, ""),
                "win": (self._ecodes.KEY_LEFTMETA, ""),
                "winleft": (self._ecodes.KEY_LEFTMETA, ""),
                "winright": (self._ecodes.KEY_RIGHTMETA, ""),
                "option": (self._ecodes.KEY_LEFTALT, ""),  # alias for alt
                "optionleft": (self._ecodes.KEY_LEFTALT, ""),  # alias for altleft
                "optionright": (self._ecodes.KEY_RIGHTALT, ""),  # alias for altright
                # --- Navigation keys ---
                "down": (self._ecodes.KEY_DOWN, ""),
                "end": (self._ecodes.KEY_END, ""),
                "final": (self._ecodes.KEY_END, ""),
                "home": (self._ecodes.KEY_HOME, ""),
                "insert": (self._ecodes.KEY_INSERT, ""),
                "left": (self._ecodes.KEY_LEFT, ""),
                "pagedown": (self._ecodes.KEY_PAGEDOWN, ""),
                "pageup": (self._ecodes.KEY_PAGEUP, ""),
                "pgdn": (self._ecodes.KEY_PAGEDOWN, ""),
                "pgup": (self._ecodes.KEY_PAGEUP, ""),
                "right": (self._ecodes.KEY_RIGHT, ""),
                "select": (self._ecodes.KEY_SELECT, ""),
                "up": (self._ecodes.KEY_UP, ""),
                # --- Function keys ---
                "f1": (self._ecodes.KEY_F1, ""),
                "f2": (self._ecodes.KEY_F2, ""),
                "f3": (self._ecodes.KEY_F3, ""),
                "f4": (self._ecodes.KEY_F4, ""),
                "f5": (self._ecodes.KEY_F5, ""),
                "f6": (self._ecodes.KEY_F6, ""),
                "f7": (self._ecodes.KEY_F7, ""),
                "f8": (self._ecodes.KEY_F8, ""),
                "f9": (self._ecodes.KEY_F9, ""),
                "f10": (self._ecodes.KEY_F10, ""),
                "f11": (self._ecodes.KEY_F11, ""),
                "f12": (self._ecodes.KEY_F12, ""),
                "f13": (self._ecodes.KEY_F13, ""),
                "f14": (self._ecodes.KEY_F14, ""),
                "f15": (self._ecodes.KEY_F15, ""),
                "f16": (self._ecodes.KEY_F16, ""),
                "f17": (self._ecodes.KEY_F17, ""),
                "f18": (self._ecodes.KEY_F18, ""),
                "f19": (self._ecodes.KEY_F19, ""),
                "f20": (self._ecodes.KEY_F20, ""),
                "f21": (self._ecodes.KEY_F21, ""),
                "f22": (self._ecodes.KEY_F22, ""),
                "f23": (self._ecodes.KEY_F23, ""),
                "f24": (self._ecodes.KEY_F24, ""),
                # --- Numpad ---
                "add": (self._ecodes.KEY_KPPLUS, ""),
                "decimal": (key_decimal, ""),
                "divide": (self._ecodes.KEY_KPSLASH, ""),
                "multiply": (self._ecodes.KEY_KPASTERISK, ""),
                "num0": (self._ecodes.KEY_KP0, ""),
                "num1": (self._ecodes.KEY_KP1, ""),
                "num2": (self._ecodes.KEY_KP2, ""),
                "num3": (self._ecodes.KEY_KP3, ""),
                "num4": (self._ecodes.KEY_KP4, ""),
                "num5": (self._ecodes.KEY_KP5, ""),
                "num6": (self._ecodes.KEY_KP6, ""),
                "num7": (self._ecodes.KEY_KP7, ""),
                "num8": (self._ecodes.KEY_KP8, ""),
                "num9": (self._ecodes.KEY_KP9, ""),
                "numlock": (self._ecodes.KEY_NUMLOCK, ""),
                "subtract": (self._ecodes.KEY_KPMINUS, ""),
                # --- Media / system keys ---
                "nexttrack": (self._ecodes.KEY_NEXTSONG, ""),
                "pause": (self._ecodes.KEY_PAUSE, ""),
                "playpause": (self._ecodes.KEY_PLAYPAUSE, ""),
                "prevtrack": (self._ecodes.KEY_PREVIOUSSONG, ""),
                "print": (self._ecodes.KEY_PRINT, ""),
                "printscreen": (self._ecodes.KEY_PRINT, ""),
                "prntscrn": (self._ecodes.KEY_PRINT, ""),
                "prtsc": (self._ecodes.KEY_PRINT, ""),
                "prtscr": (self._ecodes.KEY_PRINT, ""),
                "scrolllock": (self._ecodes.KEY_SCROLLLOCK, ""),
                "sleep": (self._ecodes.KEY_SLEEP, ""),
                "stop": (self._ecodes.KEY_STOP, ""),
                "volumedown": (self._ecodes.KEY_VOLUMEDOWN, ""),
                "volumemute": (self._ecodes.KEY_MUTE, ""),
                "volumeup": (self._ecodes.KEY_VOLUMEUP, ""),
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
            }
        )

    def teardown_postinit(self, *args: Any, **kwargs: Any) -> None:
        """Close the UInput virtual device if it was created."""
        super().teardown_postinit(*args, **kwargs)
        if self._device is not None:
            self._device.close()
            self._device = None

    def _emit_key(self, key: str, value: int) -> None:
        """Press (1) or release (0) a key, applying modifiers if necessary."""
        mapping = self._char_map.get(key)

        if mapping is None:
            raise NotImplementedError(f"Key '{key}' not implemented")

        phys, mod = mapping
        if phys is None:
            raise NotImplementedError(f"Key '{key}' mapped but not bound to a physical key")

        assert self._device is not None, "Error: device is None"

        if mod:
            for mod_name, keycode in self._mods_keycodes:
                if mod_name in mod:
                    self._device.write(self._ecodes.EV_KEY, keycode, 1 if value else 0)

        self._device.write(self._ecodes.EV_KEY, phys, value)

        if mod:
            for mod_name, keycode in self._mods_keycodes:
                if mod_name in mod:
                    self._device.write(self._ecodes.EV_KEY, keycode, 0)

        self._device.syn()

    def key_is_mapped(self, key: str) -> bool:
        """Implementation Notes:
        - Queries KEYCODE_MAPPING dictionary.
        - Returns True if key string has valid Linux KEY_* constant.
        - Case-sensitive key name matching.
        """
        return self._char_map.get(key, (None, None)) != (None, None)

    def key_down(self, key: str, **_kwargs) -> None:
        """Implementation Notes:
        - Looks up keycode from KEYCODE_MAPPING.
        - Emits device.write(EV_KEY, keycode, 1) for press.
        - Key remains pressed until key_up() called.
        """
        return self._emit_key(key, 1)

    def key_up(self, key: str, **_kwargs) -> None:
        """Implementation Notes:
        - Looks up keycode from KEYCODE_MAPPING.
        - Emits device.write(EV_KEY, keycode, 0) for release.
        """
        return self._emit_key(key, 0)
