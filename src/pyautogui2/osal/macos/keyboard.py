"""MacOS keyboard backend (OSAL layer).

Provides a multi-layout-capable keyboard primitive for MacOS using Quartz.
"""

import logging
import re
import time

from collections.abc import Generator
from contextlib import contextmanager
from typing import Optional

from ...settings import DARWIN_CATCH_UP_TIME
from ...utils.exceptions import PyAutoGUIException
from ...utils.keyboard_layouts import KEYBOARD_LAYOUTS
from ...utils.lazy_import import lazy_import
from ..abstract_cls import AbstractKeyboard


KeyCode = int  # MacOS kVK_* key constants are int


class MacOSKeyboard(AbstractKeyboard):
    """MacOS keyboard OSAL implementation.
    Uses Quartz to post keyboard events.
    """

    _quartz = lazy_import("Quartz")
    _launch_services = lazy_import("LaunchServices")

    # --- comprehensive MacOS virtual keycodes (kVK_*) ---
    # Source: common mappings from Carbon/HIToolbox headers (stable values).
    KEYCODES_BASE: dict[str, int] = {
        'a':                0x00, # kVK_ANSI_A
        's':                0x01, # kVK_ANSI_S
        'd':                0x02, # kVK_ANSI_D
        'f':                0x03, # kVK_ANSI_F
        'h':                0x04, # kVK_ANSI_H
        'g':                0x05, # kVK_ANSI_G
        'z':                0x06, # kVK_ANSI_Z
        'x':                0x07, # kVK_ANSI_X
        'c':                0x08, # kVK_ANSI_C
        'v':                0x09, # kVK_ANSI_V
        'b':                0x0b, # kVK_ANSI_B
        'q':                0x0c, # kVK_ANSI_Q
        'w':                0x0d, # kVK_ANSI_W
        'e':                0x0e, # kVK_ANSI_E
        'r':                0x0f, # kVK_ANSI_R
        'y':                0x10, # kVK_ANSI_Y
        't':                0x11, # kVK_ANSI_T
        '1':                0x12, # kVK_ANSI_1
        '2':                0x13, # kVK_ANSI_2
        '3':                0x14, # kVK_ANSI_3
        '4':                0x15, # kVK_ANSI_4
        '6':                0x16, # kVK_ANSI_6
        '5':                0x17, # kVK_ANSI_5
        'Equal':            0x18, # kVK_ANSI_Equal
        '9':                0x19, # kVK_ANSI_9
        '7':                0x1a, # kVK_ANSI_7
        'Minus':            0x1b, # kVK_ANSI_Minus
        '8':                0x1c, # kVK_ANSI_8
        '0':                0x1d, # kVK_ANSI_0
        'RightBracket':     0x1e, # kVK_ANSI_RightBracket
        'o':                0x1f, # kVK_ANSI_O
        'u':                0x20, # kVK_ANSI_U
        'LeftBracket':      0x21, # kVK_ANSI_LeftBracket
        'i':                0x22, # kVK_ANSI_I
        'p':                0x23, # kVK_ANSI_P
        'Return':           0x24, # kVK_Return
        'l':                0x25, # kVK_ANSI_L
        'j':                0x26, # kVK_ANSI_J
        'Quote':            0x27, # kVK_ANSI_Quote
        'k':                0x28, # kVK_ANSI_K
        'Semicolon':        0x29, # kVK_ANSI_Semicolon
        'Backslash':        0x2a, # kVK_ANSI_Backslash
        'Comma':            0x2b, # kVK_ANSI_Comma
        'Slash':            0x2c, # kVK_ANSI_Slash
        'n':                0x2d, # kVK_ANSI_N
        'm':                0x2e, # kVK_ANSI_M
        'Period':           0x2f, # kVK_ANSI_Period
        'Tab':              0x30, # kVK_Tab
        'Space':            0x31, # kVK_Space
        'Grave':            0x32, # kVK_ANSI_Grave
        'Delete':           0x33, # kVK_Delete
        'PB_KeypadEnter':   0x34, # kVK_Powerbook_KeypadEnter
        'Escape':           0x35, # kVK_Escape
        'RightCommand':     0x36, # kVK_RightCommand
        'Command':          0x37, # kVK_Command
        'Shift':            0x38, # kVK_Shift
        'CapsLock':         0x39, # kVK_CapsLock
        'Option':           0x3a, # kVK_Option
        'Control':          0x3b, # kVK_Control
        'RightShift':       0x3c, # kVK_RightShift
        'RightOption':      0x3d, # kVK_RightOption
        'RightControl':     0x3e, # kVK_RightControl
        'Function':         0x3f, # kVK_Function
        'F17':              0x40, # kVK_F17
        'KeypadDecimal':    0x41, # kvK_ANSI_KeypadDecimal
        'KeypadMultiply':   0x43, # kvK_ANSI_KeypadMultiply
        'KeypadPlus':       0x45, # kvK_ANSI_KeypadPlus
        'KeypadClear':      0x47, # kvK_ANSI_KeypadClear
        'VolumeUp':         0x48, # kVK_VolumeUp
        'VolumeDown':       0x49, # kvK_VolumeDown
        'Mute':             0x4a, # kvK_Mute
        'KeypadDivide':     0x4b, # kvK_ANSI_KeypadDivide
        'KeypadEnter':      0x4c, # kvK_ANSI_KeypadEnter
        'KeypadMinus':      0x4e, # kvK_ANSI_KeypadMinus
        'F18':              0x4f, # kvK_F18
        'F19':              0x50, # kvK_F19
        'KeypadEquals':     0x51, # kvK_ANSI_KeypadEquals
        'Keypad0':          0x52, # kvK_ANSI_Keypad0
        'Keypad1':          0x53, # kvK_ANSI_Keypad1
        'Keypad2':          0x54, # kvK_ANSI_Keypad2
        'Keypad3':          0x55, # kvK_ANSI_Keypad3
        'Keypad4':          0x56, # kvK_ANSI_Keypad4
        'Keypad5':          0x57, # kvK_ANSI_Keypad5
        'Keypad6':          0x58, # kvK_ANSI_Keypad6
        'Keypad7':          0x59, # kvK_ANSI_Keypad7
        'F20':              0x5a, # kvK_F20
        'Keypad8':          0x5b, # kvK_ANSI_Keypad8
        'Keypad9':          0x5c, # kvK_ANSI_Keypad9
        'JIS_Yen':          0x5d, # kvK_JIS_Yen
        'KeypadComma':      0x5f, # kvK_ANSI_KeypadComma
        'F5':               0x60, # kvK_F5
        'F6':               0x61, # kvK_F6
        'F7':               0x62, # kvK_F7
        'F3':               0x63, # kvK_F3
        'F8':               0x64, # kvK_F8
        'F9':               0x65, # kvK_F9
        'JIS_Eisu':         0x66, # kvK_JIS_Eisu
        'F11':              0x67, # kvK_F11
        'JIS_Kana':         0x68, # kvK_JIS_Kana
        'F13':              0x69, # kvK_F13
        'F16':              0x6a, # kvK_F16
        'F14':              0x6b, # kvK_F14
        'F10':              0x6d, # kvK_F10
        'ContextMenu':      0x6e, # kVK_PC_ContextMenu
        'F12':              0x6f, # kvK_F12
        'F15':              0x71, # kvK_F15
        'Help':             0x72, # kvK_Help
        'Home':             0x73, # kvK_Home
        'PageUp':           0x74, # kvK_PageUp
        'ForwardDelete':    0x75, # kvK_ForwardDelete
        'F4':               0x76, # kvK_F4
        'End':              0x77, # kvK_End
        'F2':               0x78, # kvK_F2
        'PageDown':         0x79, # kvK_PageDown
        'F1':               0x7a, # kvK_F1
        'LeftArrow':        0x7b, # kvK_LeftArrow
        'RightArrow':       0x7c, # kvK_RightArrow
        'DownArrow':        0x7d, # kvK_DownArrow
        'UpArrow':          0x7e, # kvK_UpArrow
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Store modifier keycodes for internal use
        self._mods_keycodes: tuple = ()

        self._char_map: dict[str, tuple[KeyCode, str] | tuple[None, None]] = {}

        # optional: we create a persistent event source to reduce per-event overhead
        try:
            self._event_source = self._quartz.CGEventSourceCreate(self._quartz.kCGEventSourceStateHIDSystemState)
        except Exception:
            self._event_source = None


    # --------------------------
    # Setup
    # --------------------------
    def setup_postinit(self, *args,
                       key_names: Optional[list[str]] = None,
                       all_keymapping: Optional[dict[str, dict[str, str]]] = None,
                       **kwargs) -> None:
        """Build internal char map from provided KEYBOARD_MAPPINGS-like dict."""
        super().setup_postinit(*args, **kwargs)

        if key_names is None:
            raise ValueError("key_names list is required")
        if all_keymapping is None:
            raise ValueError("all_keymapping dict is required")

        layout = self.get_layout()
        if layout not in all_keymapping:
            raise PyAutoGUIException(f"Error: unsupported layout '{layout}'. Expected one of {list(all_keymapping.keys())}")

        self._mods_keycodes = (
            ('shift', self._get_keycode('Shift')),
            ('altgr', self._get_keycode('RightOption')),
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
            return [self._get_keycode(c) for c in chars]

        base_keys = (
            _chars_to_keys(["Grave"]) + _chars_to_keys(numbers) + _chars_to_keys(["Minus", "Equal"]) +
            _chars_to_keys(letters_1) + _chars_to_keys(["LeftBracket", "RightBracket"]) +
            _chars_to_keys(letters_2) + _chars_to_keys(["Semicolon", "Quote", "Backslash"]) +
            _chars_to_keys(letters_3) + _chars_to_keys(["Comma", "Period", "Slash"])
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
        self._char_map.update({

            # --- Control keys ---
            '\t':            (self._get_keycode("Tab"), ""),
            '\n':            (self._get_keycode("Return"), ""),
            '\r':            (self._get_keycode("Return"), ""),
            '\b':            (self._get_keycode("Delete"), ""),     # Delete, which is "Backspace" on MacOS
            ' ':             (self._get_keycode("Space"), ""),
            'alt':           (self._get_keycode("Option"), ""),
            'altgr':         (self._get_keycode("RightOption"), ""),
            'altleft':       (self._get_keycode("Option"), ""),
            'altright':      (self._get_keycode("RightOption"), ""),
            'backspace':     (self._get_keycode("Delete"), ""),     # Delete, which is "Backspace" on MacOS
            'capslock':      (self._get_keycode("CapsLock"), ""),
            'ctrl':          (self._get_keycode("Control"), ""),
            'ctrlleft':      (self._get_keycode("Control"), ""),
            'ctrlright':     (self._get_keycode("RightControl"), ""),
            'del':           (self._get_keycode("ForwardDelete"), ""),
            'delete':        (self._get_keycode("ForwardDelete"), ""),
            'enter':         (self._get_keycode("Return"), ""),
            'esc':           (self._get_keycode("Escape"), ""),
            'escape':        (self._get_keycode("Escape"), ""),
            'help':          (self._get_keycode("Help"), ""),
            'return':        (self._get_keycode("Return"), ""),
            'shift':         (self._get_keycode("Shift"), ""),
            'shiftleft':     (self._get_keycode("Shift"), ""),
            'shiftright':    (self._get_keycode("RightShift"), ""),
            'space':         (self._get_keycode("Space"), ""),
            'tab':           (self._get_keycode("Tab"), ""),
            'command':       (self._get_keycode("Command"), ""),
            'commandleft':   (self._get_keycode("Command"), ""),
            'commandright':  (self._get_keycode("RightCommand"), ""),
            'win':           (self._get_keycode("Command"), ""),        # alias for command
            'winleft':       (self._get_keycode("Command"), ""),        # alias for commandleft
            'winright':      (self._get_keycode("RightCommand"), ""),   # alias for commandright
            'option':        (self._get_keycode("Option"), ""),
            'optionleft':    (self._get_keycode("Option"), ""),
            'optionright':   (self._get_keycode("RightOption"), ""),

            # --- Navigation keys ---
            'down':       (self._get_keycode("DownArrow"), ""),
            'end':        (self._get_keycode("End"), ""),
            'final':      (self._get_keycode("End"), ""),
            'home':       (self._get_keycode("Home"), ""),
            'left':       (self._get_keycode("LeftArrow"), ""),
            'pagedown':   (self._get_keycode("PageDown"), ""),
            'pageup':     (self._get_keycode("PageUp"), ""),
            'pgdn':       (self._get_keycode("PageDown"), ""),
            'pgup':       (self._get_keycode("PageUp"), ""),
            'right':      (self._get_keycode("RightArrow"), ""),
            'up':         (self._get_keycode("UpArrow"), ""),

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
            'add':         (self._get_keycode("KeypadPlus"), ""),
            'decimal':     (self._get_keycode("KeypadDecimal"), ""),
            'divide':      (self._get_keycode("KeypadDivide"), ""),
            'multiply':    (self._get_keycode("KeypadMultiply"), ""),
            'num0':        (self._get_keycode("Keypad0"), ""),
            'num1':        (self._get_keycode("Keypad1"), ""),
            'num2':        (self._get_keycode("Keypad2"), ""),
            'num3':        (self._get_keycode("Keypad3"), ""),
            'num4':        (self._get_keycode("Keypad4"), ""),
            'num5':        (self._get_keycode("Keypad5"), ""),
            'num6':        (self._get_keycode("Keypad6"), ""),
            'num7':        (self._get_keycode("Keypad7"), ""),
            'num8':        (self._get_keycode("Keypad8"), ""),
            'num9':        (self._get_keycode("Keypad9"), ""),
            'numlock':     (self._get_keycode("NumLock"), ""),
            'separator':   (self._get_keycode("KeypadComma"), ""),
            'subtract':    (self._get_keycode("KeypadMinus"), ""),

            # --- Media / system keys ---
            'apps':   (self._get_keycode("ContextMenu"), ""),

            # --- Not implemented on MacOS ---
            # "insert"
            # "select"
            # "pause"
            # "print"
            # "printscreen"
            # "prntscrn"
            # "prtsc"
            # "prtscr"
            # "scrolllock"
            # "execute"

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

    def _get_keycode(self, key: str) -> KeyCode:
        """Return the MacOS virtual keycode for the given key name or single character.
        """
        # direct named key first
        kc = self.KEYCODES_BASE.get(key, None)
        if kc is not None:
            return kc

        # nothing found
        logging.debug(f"No keycode found for '{key}'")
        return 0


    # --------------------------
    # low-level emit helpers
    # --------------------------
    def _emit_unicode_char(self, s: str) -> None:
        """Send a Unicode character or string using CGEventKeyboardSetUnicodeString.
        Supports all Unicode planes (including surrogate pairs, emoji, CJK, etc.).
        """
        utf16_units = s.encode("utf-16-le")
        n_units = len(utf16_units) // 2  # number of 16-bit code units

        def _post_unicode_event(utf16_str: bytes, utf16_str_len: int, down: bool) -> None:
            ev = self._quartz.CGEventCreateKeyboardEvent(self._event_source, 0, bool(down))
            self._quartz.CGEventKeyboardSetUnicodeString(ev, utf16_str_len, utf16_str)
            self._quartz.CGEventPost(self._quartz.kCGHIDEventTap, ev)
            # Tiny sleep to let OS X catch up on us pressing/releasing Unicode chars
            time.sleep(DARWIN_CATCH_UP_TIME)

        # Press/Release Unicode chars
        _post_unicode_event(utf16_units, n_units, True)
        _post_unicode_event(utf16_units, n_units, False)

    def _emit_key(self, key: str, press: bool) -> None:
        """Emit a single physical key event on MacOS.

        - `key` is expected to be a single key-name or a single-character that was
        already mapped in self._char_map by setup_postinit().
        - `press` True => key down; False => key up.
        - This method ONLY emits keycode events and modifier key events (shift/altgr).
        """
        mapping = self._char_map.get(key)
        if mapping is None:
            raise PyAutoGUIException(f"Error: key '{key}' not implemented")

        keycode, mods = mapping
        if keycode is None:
            raise PyAutoGUIException(f"Error: no keycode mapped for key '{key}'")

        # helper to create and post an event
        def _post_keycode_event(kc: int, down: bool) -> None:
            ev = self._quartz.CGEventCreateKeyboardEvent(self._event_source, kc, bool(down))
            self._quartz.CGEventPost(self._quartz.kCGHIDEventTap, ev)

        logging.debug(f"emit key: {key}, code={keycode}, mods={mods}, press={press}")

        # Press modifiers if pressing the key
        if mods and press:
            for mod_name, mod_keycode in self._mods_keycodes:
                if mod_name in mods:
                    _post_keycode_event(mod_keycode, True)
            # Tiny sleep to let OS X catch up on us pressing modifier
            time.sleep(DARWIN_CATCH_UP_TIME)

        _post_keycode_event(keycode, press)
        # Tiny sleep to let OS X catch up on us pressing/releasing keycode
        time.sleep(DARWIN_CATCH_UP_TIME)

        # Then release modifiers in reverse-ish order
        if mods and not press:
            for mod_name, mod_keycode in reversed(self._mods_keycodes):
                if mod_name in mods:
                    _post_keycode_event(mod_keycode, False)
            # Tiny sleep to let OS X catch up on us releasing modifier
            time.sleep(DARWIN_CATCH_UP_TIME)

    def _detect_layout(self) -> str:
        """Detect the current MacOS keyboard layout.

        Returns:
            str: canonical short layout id that should match keys in your
                KEYBOARD_LAYOUTS (for example "US", "French", "German", ...).
                Implementation logic:
                - Try TIS input source id (kTISPropertyInputSourceID), e.g.
                    "com.apple.keylayout.US" -> return "US"
                - Fallback to localized name (kTISPropertyLocalizedName) if id missing
        """
        try:
            src = self._launch_services.TISCopyCurrentKeyboardLayoutInputSource()
            if not src:
                raise PyAutoGUIException("Unable to get input source")
            srcid = self._launch_services.TISGetInputSourceProperty(
                src, self._launch_services.kTISPropertyInputSourceID
            )
            name = self._launch_services.TISGetInputSourceProperty(
                src, self._launch_services.kTISPropertyLocalizedName
            )
            if srcid:
                # "com.apple.keylayout.US" -> "US"
                # "com.apple.keylayout.SwissGerman" -> "Swiss German"
                raw = srcid.split(".")[-1]
                # Insert spaces before uppercase letters for camelCase,
                # and replace hyphens with " - "
                layout = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', raw).replace('-', ' - ')
            elif name:
                layout = name
            else:
                raise PyAutoGUIException(
                    f"Could not detect keyboard layout (from '{srcid}' or '{name}')"
                )
            return layout
        except PyAutoGUIException:
            raise
        except Exception as e:
            raise PyAutoGUIException("Unable to query TIS keyboard layout") from e

    class _CodepointCtx(AbstractKeyboard.AbstractCodepointCtx):
        def type_codepoint_value(self, hexstr: str) -> None:
            try:
                val = int(hexstr, 16)
            except ValueError as e:
                raise ValueError(f"Invalid hex codepoint: {hexstr}") from e

            ch = chr(val)
            self._keyboard._emit_unicode_char(ch)   # type: ignore[attr-defined]


    # --------------------------
    # public API expected by controller
    # --------------------------
    def key_is_mapped(self, key: str) -> bool:
        return self._char_map.get(key, (None, None)) != (None, None)

    def get_layout(self) -> str:
        layout = self._detect_layout()

        if layout not in KEYBOARD_LAYOUTS['macos']:
            raise PyAutoGUIException(f"Layout '{layout}' is unsupported by PyAutoGUI")

        return KEYBOARD_LAYOUTS['macos'][layout]['layout']

    def key_down(self, key: str, **_kwargs) -> None:
        self._emit_key(key, press=True)

    def key_up(self, key: str, **_kwargs) -> None:
        self._emit_key(key, press=False)

    @contextmanager
    def codepoint_ctx(self) -> Generator["MacOSKeyboard._CodepointCtx", None, None]:
        """Context manager used by the controller to type Unicode codepoints.
        """
        ctx = self._CodepointCtx(self)
        try:
            yield ctx
        finally:
            # no cleanup required
            pass
