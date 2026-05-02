"""WindowsKeyboard."""

import ctypes
import logging
import time

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Optional

from ...utils.exceptions import PyAutoGUIException
from ...utils.keyboard_layouts import KEYBOARD_LAYOUTS
from ...utils.lazy_import import lazy_import, lazy_load_object
from ..abstract_cls import AbstractKeyboard
from ._common import INPUT, KEYBDINPUT, get_last_error, is_legacy_windows, send_input


ScanCode = int  # Windows scancode constants are int


class WindowsKeyboard(AbstractKeyboard):
    """Windows-specific keyboard operations implementation.

    Uses Windows API functions like SendInput, keybd_event, and VkKeyScan
    for keyboard control and monitoring.

    Implementation Notes:
        - Prefer SendInput for modern Windows versions (Vista+).
        - Falls back to legacy methods (keybd_event) when needed.
    """

    _user32 = lazy_load_object("user32", lambda: ctypes.WinDLL("user32", use_last_error=True))
    _kernel32 = lazy_load_object("kernel32", lambda: ctypes.WinDLL("kernel32", use_last_error=True))
    _winreg = lazy_import("winreg")

    # --- comprehensive Windows keys scancode (from winuser.h) ---
    SCANCODES_BASE: dict[str, int] = {
        # Control keys
        'BACK':                 0x0E,
        'TAB':                  0x0F,
        'CLEAR':                0x00,  # No standard scan code
        'RETURN':               0x1C,
        'SHIFT':                0x2A,
        'CONTROL':              0x1D,
        'MENU':                 0x38,  # Alt
        'PAUSE':                0x00,  # No standard scan code
        'CAPITAL':              0x3A,
        'KANA':                 0x00,
        'HANGUEL':              0x00,
        'HANGUL':               0x00,
        'JUNJA':                0x00,
        'FINAL':                0x00,
        'HANJA':                0x00,
        'KANJI':                0x00,
        'ESCAPE':               0x01,
        'CONVERT':              0x00,
        'NONCONVERT':           0x00,
        'ACCEPT':               0x00,
        'MODECHANGE':           0x00,
        'SPACE':                0x39,
        'PRIOR':                0x49,  # Page Up (extended)
        'NEXT':                 0x51,  # Page Down (extended)
        'END':                  0x4F,  # (extended)
        'HOME':                 0x47,  # (extended)
        'LEFT':                 0x4B,  # (extended)
        'UP':                   0x48,  # (extended)
        'RIGHT':                0x4D,  # (extended)
        'DOWN':                 0x50,  # (extended)
        'SELECT':               0x00,
        'PRINT':                0x00,
        'EXECUTE':              0x00,
        'SNAPSHOT':             0x54,  # Print Screen
        'INSERT':               0x52,  # (extended)
        'DELETE':               0x53,  # (extended)
        'HELP':                 0x00,

        # Number row
        '0':                    0x0B,
        '1':                    0x02,
        '2':                    0x03,
        '3':                    0x04,
        '4':                    0x05,
        '5':                    0x06,
        '6':                    0x07,
        '7':                    0x08,
        '8':                    0x09,
        '9':                    0x0A,

        # Letters (physical positions, QWERTY layout reference)
        'a':                    0x1E,
        'b':                    0x30,
        'c':                    0x2E,
        'd':                    0x20,
        'e':                    0x12,
        'f':                    0x21,
        'g':                    0x22,
        'h':                    0x23,
        'i':                    0x17,
        'j':                    0x24,
        'k':                    0x25,
        'l':                    0x26,
        'm':                    0x32,
        'n':                    0x31,
        'o':                    0x18,
        'p':                    0x19,
        'q':                    0x10,
        'r':                    0x13,
        's':                    0x1F,
        't':                    0x14,
        'u':                    0x16,
        'v':                    0x2F,
        'w':                    0x11,
        'x':                    0x2D,
        'y':                    0x15,
        'z':                    0x2C,

        # System / special
        'LWIN':                 0x5B,  # (extended)
        'RWIN':                 0x5C,  # (extended)
        'APPS':                 0x5D,  # (extended)
        'SLEEP':                0x5F,  # (extended)

        # Numpad
        'NUMPAD0':              0x52,
        'NUMPAD1':              0x4F,
        'NUMPAD2':              0x50,
        'NUMPAD3':              0x51,
        'NUMPAD4':              0x4B,
        'NUMPAD5':              0x4C,
        'NUMPAD6':              0x4D,
        'NUMPAD7':              0x47,
        'NUMPAD8':              0x48,
        'NUMPAD9':              0x49,
        'MULTIPLY':             0x37,
        'ADD':                  0x4E,
        'SEPARATOR':            0x00,
        'SUBTRACT':             0x4A,
        'DECIMAL':              0x53,
        'DIVIDE':               0x35,  # (extended)

        # Function keys
        'F1':                   0x3B,
        'F2':                   0x3C,
        'F3':                   0x3D,
        'F4':                   0x3E,
        'F5':                   0x3F,
        'F6':                   0x40,
        'F7':                   0x41,
        'F8':                   0x42,
        'F9':                   0x43,
        'F10':                  0x44,
        'F11':                  0x57,
        'F12':                  0x58,
        'F13':                  0x64,
        'F14':                  0x65,
        'F15':                  0x66,
        'F16':                  0x67,
        'F17':                  0x68,
        'F18':                  0x69,
        'F19':                  0x6A,
        'F20':                  0x6B,
        'F21':                  0x6C,
        'F22':                  0x6D,
        'F23':                  0x6E,
        'F24':                  0x76,

        # Lock keys
        'NUMLOCK':              0x45,
        'SCROLL':               0x46,

        # Modifier keys (left/right)
        'LSHIFT':               0x2A,
        'RSHIFT':               0x36,
        'LCONTROL':             0x1D,
        'RCONTROL':             0x1D,  # (extended)
        'LMENU':                0x38,
        'RMENU':                0x38,  # (extended)

        # Media / browser keys (all extended, no classic scan code)
        'BROWSER_BACK':         0x6A,
        'BROWSER_FORWARD':      0x69,
        'BROWSER_REFRESH':      0x67,
        'BROWSER_STOP':         0x68,
        'BROWSER_SEARCH':       0x65,
        'BROWSER_FAVORITES':    0x66,
        'BROWSER_HOME':         0x32,
        'VOLUME_MUTE':          0x20,
        'VOLUME_DOWN':          0x2E,
        'VOLUME_UP':            0x30,
        'MEDIA_NEXT_TRACK':     0x19,
        'MEDIA_PREV_TRACK':     0x10,
        'MEDIA_STOP':           0x24,
        'MEDIA_PLAY_PAUSE':     0x22,
        'LAUNCH_MAIL':          0x6C,
        'LAUNCH_MEDIA_SELECT':  0x6D,
        'LAUNCH_APP1':          0x6B,
        'LAUNCH_APP2':          0x21,

        # OEM keys
        'OEM_1_SEMICOLON':      0x27,
        'OEM_PLUS':             0x0D,
        'OEM_COMMA':            0x33,
        'OEM_MINUS':            0x0C,
        'OEM_PERIOD':           0x34,
        'OEM_2_SLASH':          0x35,
        'OEM_3_GRAVE':          0x29,
        'OEM_4_LBRACE':         0x1A,
        'OEM_5_BACKSLASH':      0x2B,
        'OEM_6_RBRACE':         0x1B,
        'OEM_7_QUOTE':          0x28,
        'OEM_8_RCTRL':          0x00,

        # Misc
        'PACKET':               0x00,
        'ATTN':                 0x00,
        'CRSEL':                0x00,
        'EXSEL':                0x00,
        'EREOF':                0x00,
        'PLAY':                 0x00,
        'ZOOM':                 0x00,
        'NONAME':               0x00,
        'PA1':                  0x00,
        'OEM_CLEAR':            0x00,
    }

    # Keys that require the KEYEVENTF_EXTENDEDKEY flag in SendInput
    EXTENDED_KEYS: set[str] = {
        'PRIOR', 'NEXT', 'END', 'HOME',
        'LEFT', 'UP', 'RIGHT', 'DOWN',
        'INSERT', 'DELETE', 'SNAPSHOT',
        'DIVIDE', 'NUMLOCK',
        'LWIN', 'RWIN', 'APPS', 'SLEEP',
        'RCONTROL', 'RMENU',
        'BROWSER_BACK', 'BROWSER_FORWARD', 'BROWSER_REFRESH', 'BROWSER_STOP',
        'BROWSER_SEARCH', 'BROWSER_FAVORITES', 'BROWSER_HOME',
        'VOLUME_MUTE', 'VOLUME_DOWN', 'VOLUME_UP',
        'MEDIA_NEXT_TRACK', 'MEDIA_PREV_TRACK', 'MEDIA_STOP', 'MEDIA_PLAY_PAUSE',
        'LAUNCH_MAIL', 'LAUNCH_MEDIA_SELECT', 'LAUNCH_APP1', 'LAUNCH_APP2',
    }

    INPUT_KEYBOARD = 1

    KEYEVENTF_KEYDOWN      = 0x0000   # logical convenience (no bits)
    KEYEVENTF_KEYUP        = 0x0002

    KEYEVENTF_UNICODE      = 0x0004

    KEYEVENTF_EXTENDEDKEY  = 0x0001
    KEYEVENTF_SCANCODE     = 0x0008

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._legacy_mode: Optional[bool] = None

        # Store modifier scancodes for internal use
        self._mods_scancodes: tuple = ()

        self._char_map: dict[str, tuple[tuple[ScanCode, bool], str] | tuple[tuple[None, bool], None]] = {}


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

        self._mods_scancodes = (
            ('shift', self._get_scancode('SHIFT')),
            ('altgr', self._get_scancode('RMENU')),
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
            return [self._get_scancode(c) for c in chars]

        base_keys = (
            _chars_to_keys(["OEM_3_GRAVE"]) + _chars_to_keys(numbers) + _chars_to_keys(["OEM_MINUS", "OEM_PLUS"]) +
            _chars_to_keys(letters_1) + _chars_to_keys(["OEM_4_LBRACE", "OEM_6_RBRACE"]) +
            _chars_to_keys(letters_2) + _chars_to_keys(["OEM_1_SEMICOLON", "OEM_7_QUOTE", "OEM_5_BACKSLASH"]) +
            _chars_to_keys(letters_3) + _chars_to_keys(["OEM_COMMA", "OEM_PERIOD", "OEM_2_SLASH"])
        )

        # ------------------------------------------------------------------
        # Build char_map dynamically for base/shift/altgr
        # ------------------------------------------------------------------
        undefined_key = ((None, False), None)
        self._char_map = dict.fromkeys(key_names, undefined_key)

        for modifier, kb_mod in all_keymapping[layout].items():
            if modifier == "shift_altgr":
                # SHIFT+ALTGR is not supported on Windows
                # Do not register these char to fallback to codepoint
                continue
            if len(kb_mod) == 0:
                continue
            for char, (scancode, is_ext) in zip(kb_mod, base_keys, strict=True):
                # Ensure char is valid and not already mapped
                if char and self._char_map.get(char, undefined_key) == undefined_key:
                    self._char_map[char] = ((scancode, is_ext), modifier)

        # ------------------------------------------------------------------
        # Extra mapping for keys not covered by all_keys (organized by category)
        # ------------------------------------------------------------------
        self._char_map.update({

            # --- Control keys ---
            '\t':            (self._get_scancode("TAB"), ""),
            '\n':            (self._get_scancode("RETURN"), ""),
            '\r':            (self._get_scancode("RETURN"), ""),
            '\b':            (self._get_scancode("BACK"), ""),
            ' ':             (self._get_scancode("SPACE"), ""),
            'alt':           (self._get_scancode("MENU"), ""),
            'altgr':         (self._get_scancode("RMENU"), ""),
            'altleft':       (self._get_scancode("LMENU"), ""),
            'altright':      (self._get_scancode("RMENU"), ""),
            'backspace':     (self._get_scancode("BACK"), ""),
            'capslock':      (self._get_scancode("CAPITAL"), ""),
            'ctrl':          (self._get_scancode("CONTROL"), ""),
            'ctrlleft':      (self._get_scancode("LCONTROL"), ""),
            'ctrlright':     (self._get_scancode("RCONTROL"), ""),
            'del':           (self._get_scancode("DELETE"), ""),
            'delete':        (self._get_scancode("DELETE"), ""),
            'enter':         (self._get_scancode("RETURN"), ""),
            'esc':           (self._get_scancode("ESCAPE"), ""),
            'escape':        (self._get_scancode("ESCAPE"), ""),
            'help':          (self._get_scancode("HELP"), ""),
            'return':        (self._get_scancode("RETURN"), ""),
            'shift':         (self._get_scancode("SHIFT"), ""),
            'shiftleft':     (self._get_scancode("LSHIFT"), ""),
            'shiftright':    (self._get_scancode("RSHIFT"), ""),
            'space':         (self._get_scancode("SPACE"), ""),
            'tab':           (self._get_scancode("TAB"), ""),
            'win':           (self._get_scancode("LWIN"), ""),
            'winleft':       (self._get_scancode("LWIN"), ""),
            'winright':      (self._get_scancode("RWIN"), ""),
            'option':        (self._get_scancode("MENU"), ""),   # alias for alt
            'optionleft':    (self._get_scancode("LMENU"), ""),  # alias for altleft
            'optionright':   (self._get_scancode("RMENU"), ""),  # alias for altright

            # --- Navigation keys ---
            'down':       (self._get_scancode("DOWN"), ""),
            'end':        (self._get_scancode("END"), ""),
            'final':      (self._get_scancode("END"), ""),
            'home':       (self._get_scancode("HOME"), ""),
            'left':       (self._get_scancode("LEFT"), ""),
            'pagedown':   (self._get_scancode("NEXT"), ""),
            'pageup':     (self._get_scancode("PRIOR"), ""),
            'pgdn':       (self._get_scancode("NEXT"), ""),
            'pgup':       (self._get_scancode("PRIOR"), ""),
            'right':      (self._get_scancode("RIGHT"), ""),
            'up':         (self._get_scancode("UP"), ""),

            # --- Function keys ---
            'f1':    (self._get_scancode("F1"), ""),
            'f2':    (self._get_scancode("F2"), ""),
            'f3':    (self._get_scancode("F3"), ""),
            'f4':    (self._get_scancode("F4"), ""),
            'f5':    (self._get_scancode("F5"), ""),
            'f6':    (self._get_scancode("F6"), ""),
            'f7':    (self._get_scancode("F7"), ""),
            'f8':    (self._get_scancode("F8"), ""),
            'f9':    (self._get_scancode("F9"), ""),
            'f10':   (self._get_scancode("F10"), ""),
            'f11':   (self._get_scancode("F11"), ""),
            'f12':   (self._get_scancode("F12"), ""),
            'f13':   (self._get_scancode("F13"), ""),
            'f14':   (self._get_scancode("F14"), ""),
            'f15':   (self._get_scancode("F15"), ""),
            'f16':   (self._get_scancode("F16"), ""),
            'f17':   (self._get_scancode("F17"), ""),
            'f18':   (self._get_scancode("F18"), ""),
            'f19':   (self._get_scancode("F19"), ""),
            'f20':   (self._get_scancode("F20"), ""),
            'f21':   (self._get_scancode("F21"), ""),
            'f22':   (self._get_scancode("F22"), ""),
            'f23':   (self._get_scancode("F23"), ""),
            'f24':   (self._get_scancode("F24"), ""),

            # --- Numpad ---
            'add':         (self._get_scancode("ADD"), ""),
            'decimal':     (self._get_scancode("DECIMAL"), ""),
            'divide':      (self._get_scancode("DIVIDE"), ""),
            'multiply':    (self._get_scancode("MULTIPLY"), ""),
            'num0':        (self._get_scancode("NUMPAD0"), ""),
            'num1':        (self._get_scancode("NUMPAD1"), ""),
            'num2':        (self._get_scancode("NUMPAD2"), ""),
            'num3':        (self._get_scancode("NUMPAD3"), ""),
            'num4':        (self._get_scancode("NUMPAD4"), ""),
            'num5':        (self._get_scancode("NUMPAD5"), ""),
            'num6':        (self._get_scancode("NUMPAD6"), ""),
            'num7':        (self._get_scancode("NUMPAD7"), ""),
            'num8':        (self._get_scancode("NUMPAD8"), ""),
            'num9':        (self._get_scancode("NUMPAD9"), ""),
            'numlock':     (self._get_scancode("NUMLOCK"), ""),
            'separator':   (self._get_scancode("SEPARATOR"), ""),
            'subtract':    (self._get_scancode("SUBTRACT"), ""),

            # --- Media / system keys ---
            'apps':         (self._get_scancode("APPS"), ""),
            'insert':       (self._get_scancode("INSERT"), ""),
            'select':       (self._get_scancode("SELECT"), ""),
            'pause':        (self._get_scancode("PAUSE"), ""),
            'print':        (self._get_scancode("SNAPSHOT"), ""),
            'printscreen':  (self._get_scancode("SNAPSHOT"), ""),
            'prntscrn':     (self._get_scancode("SNAPSHOT"), ""),
            'prtsc':        (self._get_scancode("SNAPSHOT"), ""),
            'prtscr':       (self._get_scancode("SNAPSHOT"), ""),
            'scrolllock':   (self._get_scancode("SCROLL"), ""),
            'execute':      (self._get_scancode("EXECUTE"), ""),

            # --- Browser keys (not implemented) ---
            'browserback':        (self._get_scancode("BROWSER_BACK"), ""),
            'browserfavorites':   (self._get_scancode("BROWSER_FAVORITES"), ""),
            'browserforward':     (self._get_scancode("BROWSER_FORWARD"), ""),
            'browserhome':        (self._get_scancode("BROWSER_HOME"), ""),
            'browserrefresh':     (self._get_scancode("BROWSER_REFRESH"), ""),
            'browsersearch':      (self._get_scancode("BROWSER_SEARCH"), ""),
            'browserstop':        (self._get_scancode("BROWSER_STOP"), ""),

            # --- Other specials (not implemented or rarely used) ---
            # "hanguel"
            # "hangeul"
            # "hanja"
            # "hiragana"
            # "kana"
            # "yen"
        })

    def _is_legacy(self):
        if self._legacy_mode is None:
            self._legacy_mode = is_legacy_windows()
            if self._legacy_mode:
                logging.warning("WindowsKeyboard: legacy mode enabled (Unicode injection may be limited)")

        return self._legacy_mode

    def _get_scancode(self, key: str) -> tuple[ScanCode, bool]:
        """Returns the Windows scan code for the given key name, and
        a boolean value to specify if KEYEVENTF_EXTENDEDKEY is required for this key.
        """
        sc = self.SCANCODES_BASE.get(key, None)
        if sc is not None:
            return (sc, key in self.EXTENDED_KEYS)

        # nothing found
        logging.debug(f"No keycode found for '{key}'")
        return (0, False)

    def _detect_layout(self) -> str:
        """Detect the active input layout (e.g., '0x0409' for 'US', '0x040C' for 'French', etc.).
        """
        try:
            with self._winreg.OpenKey(self._winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\Keyboard Layout\Preload") as key:
                klid, _ = self._winreg.QueryValueEx(key, "1")
                lid_hex = int(klid, 16)
        except Exception:
            logging.debug("Get layout from registry failed, so use User32 fallback")
            hwnd = self._user32.GetForegroundWindow()
            thread_id = self._user32.GetWindowThreadProcessId(hwnd, None)
            layout_id = self._user32.GetKeyboardLayout(thread_id)
            lid_hex = layout_id & 0xFFFF

        return f"0x{lid_hex:04x}"

    def _build_input(self, scancode: int = 0, flags: int = 0):
        """Builds an INPUT structure for keyboard events.

        Args:
            scancode: Hardware scan code.
            flags: KEYEVENTF flags.

        Returns:
            INPUT structure ready for SendInput.

        Implementation Notes:
            - Sets up the INPUT structure with proper fields.
            - Handles extended keys (like right arrow).
        """
        ki = KEYBDINPUT()
        ki.wVk = 0
        ki.wScan = scancode
        ki.dwFlags = flags
        ki.time = 0
        ki.dwExtraInfo = 0

        inp = INPUT()
        inp.type = self.INPUT_KEYBOARD
        inp.u.ki = ki

        return inp


    # ---------------------------------------------------------------------- #
    # Core key emission
    # ---------------------------------------------------------------------- #
    def _emit_key(self, key: str, press: bool) -> None:
        """Emit a key press/release via SendInput (or keybd_event legacy fallback)."""

        def _build_flags(press: bool, is_extended: bool) -> int:
            flags = self.KEYEVENTF_KEYDOWN if press else self.KEYEVENTF_KEYUP
            flags |= self.KEYEVENTF_SCANCODE
            if is_extended:
                flags |= self.KEYEVENTF_EXTENDEDKEY
            return flags

        def _send(scancode: int, is_extended: bool, press: bool) -> None:
            flags = _build_flags(press, is_extended)
            if self._is_legacy():
                try:
                    self._user32.keybd_event(0, scancode, flags, 0)
                except Exception as e:
                    logging.error(f"[keybd_event] scancode={scancode}: {e}")
            else:
                inp = self._build_input(scancode & 0xFFFF, flags)
                if not send_input(self._user32, inp):
                    err = get_last_error(self._kernel32)
                    logging.warning(f"[SendInput] scancode={scancode}, press={press}: GetLastError={err}")

        mapping = self._char_map.get(key)
        if mapping is None:
            raise PyAutoGUIException(f"Key '{key}' not implemented")

        (scancode, is_extended), mods = mapping
        if scancode is None:
            raise PyAutoGUIException(f"No scancode mapped for key '{key}'")

        logging.debug(f"emit_key: key={key!r} scancode={scancode:#x} mods={mods} press={press} extended={is_extended}")

        # Press modifiers if pressing the key
        if mods and press:
            for mod_name, (mod_sc, mod_ext) in self._mods_scancodes:
                if mod_name in mods:
                    _send(mod_sc, mod_ext, True)

        _send(scancode, is_extended, press)

        # Then release modifiers in reverse-ish order
        if mods and not press:
            for mod_name, (mod_sc, mod_ext) in reversed(self._mods_scancodes):
                if mod_name in mods:
                    _send(mod_sc, mod_ext, False)

    def _emit_unicode_char(self, char: str) -> None:
        """Send a Unicode character directly (if supported),
        or fallback to '?' for legacy systems.
        Handling surrogate pairs for codepoints > 0xFFFF.
        """
        if self._is_legacy():
            logging.warning(f"Unicode '{char}' not supported in legacy mode -> using '?' placeholder")
            self._emit_key("?", press=True)
            self._emit_key("?", press=False)
            return

        def _send_input(scancode: int, press: bool):
            flags = self.KEYEVENTF_KEYDOWN if press else self.KEYEVENTF_KEYUP
            flags |= self.KEYEVENTF_UNICODE
            inp = self._build_input(scancode & 0xFFFF, flags)
            if not send_input(self._user32, inp):
                err = get_last_error(self._kernel32)
                logging.warning(f"emit_unicode_char->SendInput(scancode={scancode}, press={press}) failed: GetLastError={err}")

        codepoint = ord(char)

        if codepoint <= 0xFFFF:
            # BMP character: single Unicode event
            scancodes = [codepoint]
        else:
            # Supplementary plane: encode as UTF-16 surrogate pair
            encoded = char.encode('utf-16-le')  # 4 bytes for surrogate pair
            high = int.from_bytes(encoded[0:2], 'little')  # high surrogate
            low  = int.from_bytes(encoded[2:4], 'little')  # low surrogate
            scancodes = [high, low]

        for sc in scancodes:
            _send_input(sc, press=True)
            _send_input(sc, press=False)

        if len(scancodes) > 1:
            # Surrogate pairs need a small delay to let Windows process
            # the pair completely before the next character
            time.sleep(0.01)

    class _CodepointCtx(AbstractKeyboard.AbstractCodepointCtx):
        def type_codepoint_value(self, hexstr: str) -> None:
            try:
                cp = int(hexstr, 16)
                ch = chr(cp)
                self._keyboard._emit_unicode_char(ch)   # type: ignore[attr-defined]
            except Exception as e:
                logging.error(f"Failed to type codepoint U+{hexstr} from {e}")
                # fallback placeholder
                self._keyboard._emit_key("?", press=True)   # type: ignore[attr-defined]
                self._keyboard._emit_key("?", press=False)  # type: ignore[attr-defined]


    # ---------------------------------------------------------------------- #
    # Public key operations
    # ---------------------------------------------------------------------- #
    def key_is_mapped(self, key: str) -> bool:
        return self._char_map.get(key, ((None, None), None)) != ((None, None), None)

    def get_layout(self) -> str:
        layout = self._detect_layout()

        if layout not in KEYBOARD_LAYOUTS['windows']:
            raise PyAutoGUIException(f"Layout '{layout}' is unsupported by PyAutoGUI")

        return KEYBOARD_LAYOUTS['windows'][layout]['layout']

    def key_down(self, key: str, **_kwargs: Any) -> None:
        self._emit_key(key, press=True)

    def key_up(self, key: str, **_kwargs: Any) -> None:
        self._emit_key(key, press=False)

    @contextmanager
    def codepoint_ctx(self) -> Generator["WindowsKeyboard._CodepointCtx", None, None]:
        """Context manager for Unicode codepoint typing."""
        ctx = self._CodepointCtx(self)
        try:
            yield ctx
        finally:
            # no cleanup required
            pass
