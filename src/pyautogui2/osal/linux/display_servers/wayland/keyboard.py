"""WaylandKeyboardPart - Display server part for all Linux keyboards."""
import time

from typing import Any, Optional

from .....utils.lazy_import import lazy_import
from ....abstract_cls import AbstractKeyboard
from ._common import ensure_device_not_exists


KeyCode = tuple[int, int]  # python-uinput key constants are tuples


class WaylandKeyboardPart(AbstractKeyboard):
    """Wayland display server keyboard implementation using uinput kernel interface.

    Provides low-level keyboard control via Linux uinput subsystem, which creates
    a virtual input device. Required on Wayland due to security restrictions that
    prevent direct key injection via display server protocols.

    Implementation Notes:
        - Uses python-uinput to create virtual keyboard device.
        - Requires write access to /dev/uinput (typically root or input group).
        - Maintains comprehensive Linux input keycode mapping (KEY_*).
        - Emits EV_KEY events with value 1 (press) and 0 (release).
        - Layout detection delegated to compositor-specific Parts.

    Dependencies:
        - python-uinput library.
        - /dev/uinput kernel interface access.
        - uinput kernel module loaded.

    Limitations:
        - Requires elevated permissions or group membership.
        - No built-in layout detection (compositor must provide).
    """

    _uinput = lazy_import("uinput")

    _device_name = "pyautogui-virtual-keyboard"

    def __init__(self, *args, **kwargs):
        """Initialize Wayland keyboard without creating uinput device.

        Defers uinput device creation until setup_postinit().
        """
        super().__init__(*args, **kwargs)

        self._device: Optional[Any] = None

        # Store modifier keycodes for internal use
        self._mods_keycodes: tuple = ()

        self._char_map: dict[str, tuple[KeyCode, str] | tuple[None, None]] = {}

    def setup_postinit(self, *args,
                       key_names: Optional[list[str]] = None,
                       all_keymapping: Optional[dict[str, dict[str, str]]] = None,
                       **kwargs) -> None:
        """Create virtual uinput keyboard device with full key support.

        Implementation Notes:
            - Removes controller decorators from key methods.
            - Initializes uinput.Device with all keys from KEYCODE_MAPPING.
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
            raise ValueError(f"Error: '{layout}' layout is not supported ({list(all_keymapping.keys())})")

        ensure_device_not_exists(self._device_name)

        # Create device with all KEY_* (ensures completeness)
        all_keycodes = [val for name, val in self._uinput.__dict__.items() if name.startswith("KEY_")]
        self._device = self._uinput.Device(all_keycodes, name=self._device_name)
        time.sleep(0.1)     # Let's give the OS some time to create the device

        self._mods_keycodes = (
            ('shift', self._uinput.KEY_LEFTSHIFT),
            ('altgr', self._uinput.KEY_RIGHTALT),
        )

        # ------------------------------------------------------------------
        # Build all_keys in physical order (rows of the keyboard)
        # ------------------------------------------------------------------
        kb_us = all_keymapping["QWERTY"]["_"]
        numbers   = kb_us[1:11]     # 1234567890
        letters_1 = kb_us[13:23]    # qwertyuiop
        letters_2 = kb_us[25:34]    # asdfghjkl
        letters_3 = kb_us[37:44]    # zxcvbnm

        def _chars_to_keys(chars):
            """Helper: convert a list of characters into self._uinput.KEY_* constants."""
            return [getattr(self._uinput, f"KEY_{c.upper()}") for c in chars]

        base_keys = (
            [self._uinput.KEY_GRAVE] + _chars_to_keys(numbers) + [self._uinput.KEY_MINUS, self._uinput.KEY_EQUAL] +
            _chars_to_keys(letters_1) + [self._uinput.KEY_LEFTBRACE, self._uinput.KEY_RIGHTBRACE] +
            _chars_to_keys(letters_2) + [self._uinput.KEY_SEMICOLON, self._uinput.KEY_APOSTROPHE, self._uinput.KEY_BACKSLASH] +
            _chars_to_keys(letters_3) + [self._uinput.KEY_COMMA, self._uinput.KEY_DOT, self._uinput.KEY_SLASH]
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
        key_decimal = self._uinput.KEY_KPDOT      # by default
        if layout in ('AZERTY', 'QWERTZ'):
            key_decimal = self._uinput.KEY_KPCOMMA

        self._char_map.update({

            # --- Control keys ---
            '\t':           (self._uinput.KEY_TAB, ""),
            '\n':           (self._uinput.KEY_ENTER, ""),
            '\r':           (self._uinput.KEY_ENTER, ""),
            '\b':           (self._uinput.KEY_BACKSPACE, ""),
            ' ':            (self._uinput.KEY_SPACE, ""),
            'alt':          (self._uinput.KEY_LEFTALT, ""),
            'altgr':        (self._uinput.KEY_RIGHTALT, ""),
            'altleft':      (self._uinput.KEY_LEFTALT, ""),
            'altright':     (self._uinput.KEY_RIGHTALT, ""),
            'backspace':    (self._uinput.KEY_BACKSPACE, ""),
            'capslock':     (self._uinput.KEY_CAPSLOCK, ""),
            'ctrl':         (self._uinput.KEY_LEFTCTRL, ""),
            'ctrlleft':     (self._uinput.KEY_LEFTCTRL, ""),
            'ctrlright':    (self._uinput.KEY_RIGHTCTRL, ""),
            'del':          (self._uinput.KEY_DELETE, ""),
            'delete':       (self._uinput.KEY_DELETE, ""),
            'enter':        (self._uinput.KEY_ENTER, ""),
            'esc':          (self._uinput.KEY_ESC, ""),
            'escape':       (self._uinput.KEY_ESC, ""),
            'fn':           (self._uinput.KEY_FN, ""),
            'help':         (self._uinput.KEY_HELP, ""),
            'return':       (self._uinput.KEY_ENTER, ""),
            'shift':        (self._uinput.KEY_LEFTSHIFT, ""),
            'shiftleft':    (self._uinput.KEY_LEFTSHIFT, ""),
            'shiftright':   (self._uinput.KEY_RIGHTSHIFT, ""),
            'space':        (self._uinput.KEY_SPACE, ""),
            'tab':          (self._uinput.KEY_TAB, ""),
            'win':          (self._uinput.KEY_LEFTMETA, ""),
            'winleft':      (self._uinput.KEY_LEFTMETA, ""),
            'winright':     (self._uinput.KEY_RIGHTMETA, ""),
            'option':       (self._uinput.KEY_LEFTALT, ""),       # alias for alt
            'optionleft':   (self._uinput.KEY_LEFTALT, ""),       # alias for altleft
            'optionright':  (self._uinput.KEY_RIGHTALT, ""),      # alias for altright

            # --- Navigation keys ---
            'down':      (self._uinput.KEY_DOWN, ""),
            'end':       (self._uinput.KEY_END, ""),
            'final':     (self._uinput.KEY_END, ""),
            'home':      (self._uinput.KEY_HOME, ""),
            'insert':    (self._uinput.KEY_INSERT, ""),
            'left':      (self._uinput.KEY_LEFT, ""),
            'pagedown':  (self._uinput.KEY_PAGEDOWN, ""),
            'pageup':    (self._uinput.KEY_PAGEUP, ""),
            'pgdn':      (self._uinput.KEY_PAGEDOWN, ""),
            'pgup':      (self._uinput.KEY_PAGEUP, ""),
            'right':     (self._uinput.KEY_RIGHT, ""),
            'select':    (self._uinput.KEY_SELECT, ""),
            'up':        (self._uinput.KEY_UP, ""),

            # --- Function keys ---
            'f1':   (self._uinput.KEY_F1, ""),
            'f2':   (self._uinput.KEY_F2, ""),
            'f3':   (self._uinput.KEY_F3, ""),
            'f4':   (self._uinput.KEY_F4, ""),
            'f5':   (self._uinput.KEY_F5, ""),
            'f6':   (self._uinput.KEY_F6, ""),
            'f7':   (self._uinput.KEY_F7, ""),
            'f8':   (self._uinput.KEY_F8, ""),
            'f9':   (self._uinput.KEY_F9, ""),
            'f10':  (self._uinput.KEY_F10, ""),
            'f11':  (self._uinput.KEY_F11, ""),
            'f12':  (self._uinput.KEY_F12, ""),
            'f13':  (self._uinput.KEY_F13, ""),
            'f14':  (self._uinput.KEY_F14, ""),
            'f15':  (self._uinput.KEY_F15, ""),
            'f16':  (self._uinput.KEY_F16, ""),
            'f17':  (self._uinput.KEY_F17, ""),
            'f18':  (self._uinput.KEY_F18, ""),
            'f19':  (self._uinput.KEY_F19, ""),
            'f20':  (self._uinput.KEY_F20, ""),
            'f21':  (self._uinput.KEY_F21, ""),
            'f22':  (self._uinput.KEY_F22, ""),
            'f23':  (self._uinput.KEY_F23, ""),
            'f24':  (self._uinput.KEY_F24, ""),

            # --- Numpad ---
            'add':       (self._uinput.KEY_KPPLUS, ""),
            'decimal':   (key_decimal, ""),
            'divide':    (self._uinput.KEY_KPSLASH, ""),
            'multiply':  (self._uinput.KEY_KPASTERISK, ""),
            'num0':      (self._uinput.KEY_KP0, ""),
            'num1':      (self._uinput.KEY_KP1, ""),
            'num2':      (self._uinput.KEY_KP2, ""),
            'num3':      (self._uinput.KEY_KP3, ""),
            'num4':      (self._uinput.KEY_KP4, ""),
            'num5':      (self._uinput.KEY_KP5, ""),
            'num6':      (self._uinput.KEY_KP6, ""),
            'num7':      (self._uinput.KEY_KP7, ""),
            'num8':      (self._uinput.KEY_KP8, ""),
            'num9':      (self._uinput.KEY_KP9, ""),
            'numlock':   (self._uinput.KEY_NUMLOCK, ""),
            'subtract':  (self._uinput.KEY_KPMINUS, ""),

            # --- Media / system keys ---
            'nexttrack':    (self._uinput.KEY_NEXTSONG, ""),
            'pause':        (self._uinput.KEY_PAUSE, ""),
            'playpause':    (self._uinput.KEY_PLAYPAUSE, ""),
            'prevtrack':    (self._uinput.KEY_PREVIOUSSONG, ""),
            'print':        (self._uinput.KEY_PRINT, ""),
            'printscreen':  (self._uinput.KEY_PRINT, ""),
            'prntscrn':     (self._uinput.KEY_PRINT, ""),
            'prtsc':        (self._uinput.KEY_PRINT, ""),
            'prtscr':       (self._uinput.KEY_PRINT, ""),
            'scrolllock':   (self._uinput.KEY_SCROLLLOCK, ""),
            'sleep':        (self._uinput.KEY_SLEEP, ""),
            'stop':         (self._uinput.KEY_STOP, ""),
            'volumedown':   (self._uinput.KEY_VOLUMEDOWN, ""),
            'volumemute':   (self._uinput.KEY_MUTE, ""),
            'volumeup':     (self._uinput.KEY_VOLUMEUP, ""),

            # --- Browser keys (not implemented) ---
            # 'browserback'
            # 'browserfavorites'
            # 'browserforward'
            # 'browserhome'
            # 'browserrefresh'
            # 'browsersearch'
            # 'browserstop'

            # --- Other specials (not implemented or rarely used) ---
            # 'hanguel'
            # 'hangeul'
            # 'hanja'
            # 'hiragana'
            # 'kana'
            # 'yen'
        })

    def teardown_postinit(self, *args: Any, **kwargs: Any) -> None:
        """Close the UInput virtual device if it was created."""
        super().teardown_postinit(*args, **kwargs)
        if self._device is not None:
            self._device.destroy()
            self._device = None

    def _emit_key(self, key: str, value: int) -> None:
        """Press (1) or release (0) a key, applying modifiers if necessary.
        """
        mapping = self._char_map.get(key)

        if mapping is None:
            raise NotImplementedError(f"Key '{key}' not implemented")

        phys, mod = mapping
        if phys is None:
            raise NotImplementedError(f"Key '{key}' mapped but not bound to a physical key")

        assert(self._device is not None), "Error: device is None"

        if mod:
            for mod_name, keycode in self._mods_keycodes:
                if mod_name in mod:
                    self._device.emit(keycode, 1 if value else 0)

        self._device.emit(phys, value)

        if mod:
            for mod_name, keycode in self._mods_keycodes:
                if mod_name in mod:
                    self._device.emit(keycode, 0)

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
        - Emits device.emit(keycode, 1) for press.
        - Key remains pressed until key_up() called.
        """
        return self._emit_key(key, 1)

    def key_up(self, key: str, **_kwargs) -> None:
        """Implementation Notes:
        - Looks up keycode from KEYCODE_MAPPING.
        - Emits device.emit(keycode, 0) for release.
        """
        return self._emit_key(key, 0)
