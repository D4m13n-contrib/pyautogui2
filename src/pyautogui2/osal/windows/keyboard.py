"""WindowsKeyboard."""

import ctypes
import logging

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Optional

from ...utils.exceptions import PyAutoGUIException
from ...utils.keyboard_layouts import KEYBOARD_LAYOUTS
from ...utils.lazy_import import lazy_import, lazy_load_object
from ..abstract_cls import AbstractKeyboard
from ._common import INPUT, KEYBDINPUT, get_last_error, is_legacy_windows, send_input


KeyCode = int  # Windows VK_* key constants are int


class WindowsKeyboard(AbstractKeyboard):
    """Windows-specific keyboard operations implementation.

    Uses Windows API functions like SendInput, keybd_event, and VkKeyScan
    for keyboard control and monitoring.

    Implementation Notes:
        - Prefer SendInput for modern Windows versions (Vista+).
        - Falls back to legacy methods (keybd_event) when needed.
        - Uses virtual key codes (VK_*) for special keys.
    """

    _user32 = lazy_load_object("user32", lambda: ctypes.WinDLL("user32", use_last_error=True))
    _kernel32 = lazy_load_object("kernel32", lambda: ctypes.WinDLL("kernel32", use_last_error=True))
    _winreg = lazy_import("winreg")

    # --- comprehensive Windows virtual keycodes (VK_* from winuser.h) ---
    KEYCODES_BASE: dict[str, int] = {
        'BACK':                 0x08, # VK_BACK
        'TAB':                  0x09, # VK_TAB
        'CLEAR':                0x0c, # VK_CLEAR
        'RETURN':               0x0d, # VK_RETURN
        'SHIFT':                0x10, # VK_SHIFT
        'CONTROL':              0x11, # VK_CONTROL
        'MENU':                 0x12, # VK_MENU
        'PAUSE':                0x13, # VK_PAUSE
        'CAPITAL':              0x14, # VK_CAPITAL
        'KANA':                 0x15, # VK_KANA
        'HANGUEL':              0x15, # VK_HANGUEL
        'HANGUL':               0x15, # VK_HANGUL
        'JUNJA':                0x17, # VK_JUNJA
        'FINAL':                0x18, # VK_FINAL
        'HANJA':                0x19, # VK_HANJA
        'KANJI':                0x19, # VK_KANJI
        'ESCAPE':               0x1b, # VK_ESCAPE
        'CONVERT':              0x1c, # VK_CONVERT
        'NONCONVERT':           0x1d, # VK_NONCONVERT
        'ACCEPT':               0x1e, # VK_ACCEPT
        'MODECHANGE':           0x1f, # VK_MODECHANGE
        'SPACE':                0x20, # VK_SPACE
        'PRIOR':                0x21, # VK_PRIOR
        'NEXT':                 0x22, # VK_NEXT
        'END':                  0x23, # VK_END
        'HOME':                 0x24, # VK_HOME
        'LEFT':                 0x25, # VK_LEFT
        'UP':                   0x26, # VK_UP
        'RIGHT':                0x27, # VK_RIGHT
        'DOWN':                 0x28, # VK_DOWN
        'SELECT':               0x29, # VK_SELECT
        'PRINT':                0x2a, # VK_PRINT
        'EXECUTE':              0x2b, # VK_EXECUTE
        'SNAPSHOT':             0x2c, # VK_SNAPSHOT
        'INSERT':               0x2d, # VK_INSERT
        'DELETE':               0x2e, # VK_DELETE
        'HELP':                 0x2f, # VK_HELP
        '0':                    0x30,
        '1':                    0x31,
        '2':                    0x32,
        '3':                    0x33,
        '4':                    0x34,
        '5':                    0x35,
        '6':                    0x36,
        '7':                    0x37,
        '8':                    0x38,
        '9':                    0x39,
        'a':                    0x41,
        'b':                    0x42,
        'c':                    0x43,
        'd':                    0x44,
        'e':                    0x45,
        'f':                    0x46,
        'g':                    0x47,
        'h':                    0x48,
        'i':                    0x49,
        'j':                    0x4a,
        'k':                    0x4b,
        'l':                    0x4c,
        'm':                    0x4d,
        'n':                    0x4e,
        'o':                    0x4f,
        'p':                    0x50,
        'q':                    0x51,
        'r':                    0x52,
        's':                    0x53,
        't':                    0x54,
        'u':                    0x55,
        'v':                    0x56,
        'w':                    0x57,
        'x':                    0x58,
        'y':                    0x59,
        'z':                    0x5a,
        'LWIN':                 0x5b, # VK_LWIN
        'RWIN':                 0x5c, # VK_RWIN
        'APPS':                 0x5d, # VK_APPS
        'SLEEP':                0x5f, # VK_SLEEP
        'NUMPAD0':              0x60, # VK_NUMPAD0
        'NUMPAD1':              0x61, # VK_NUMPAD1
        'NUMPAD2':              0x62, # VK_NUMPAD2
        'NUMPAD3':              0x63, # VK_NUMPAD3
        'NUMPAD4':              0x64, # VK_NUMPAD4
        'NUMPAD5':              0x65, # VK_NUMPAD5
        'NUMPAD6':              0x66, # VK_NUMPAD6
        'NUMPAD7':              0x67, # VK_NUMPAD7
        'NUMPAD8':              0x68, # VK_NUMPAD8
        'NUMPAD9':              0x69, # VK_NUMPAD9
        'MULTIPLY':             0x6a, # VK_MULTIPLY
        'ADD':                  0x6b, # VK_ADD
        'SEPARATOR':            0x6c, # VK_SEPARATOR
        'SUBTRACT':             0x6d, # VK_SUBTRACT
        'DECIMAL':              0x6e, # VK_DECIMAL
        'DIVIDE':               0x6f, # VK_DIVIDE
        'F1':                   0x70, # VK_F1
        'F2':                   0x71, # VK_F2
        'F3':                   0x72, # VK_F3
        'F4':                   0x73, # VK_F4
        'F5':                   0x74, # VK_F5
        'F6':                   0x75, # VK_F6
        'F7':                   0x76, # VK_F7
        'F8':                   0x77, # VK_F8
        'F9':                   0x78, # VK_F9
        'F10':                  0x79, # VK_F10
        'F11':                  0x7a, # VK_F11
        'F12':                  0x7b, # VK_F12
        'F13':                  0x7c, # VK_F13
        'F14':                  0x7d, # VK_F14
        'F15':                  0x7e, # VK_F15
        'F16':                  0x7f, # VK_F16
        'F17':                  0x80, # VK_F17
        'F18':                  0x81, # VK_F18
        'F19':                  0x82, # VK_F19
        'F20':                  0x83, # VK_F20
        'F21':                  0x84, # VK_F21
        'F22':                  0x85, # VK_F22
        'F23':                  0x86, # VK_F23
        'F24':                  0x87, # VK_F24
        'NUMLOCK':              0x90, # VK_NUMLOCK
        'SCROLL':               0x91, # VK_SCROLL
        'LSHIFT':               0xa0, # VK_LSHIFT
        'RSHIFT':               0xa1, # VK_RSHIFT
        'LCONTROL':             0xa2, # VK_LCONTROL
        'RCONTROL':             0xa3, # VK_RCONTROL
        'LMENU':                0xa4, # VK_LMENU
        'RMENU':                0xa5, # VK_RMENU
        'BROWSER_BACK':         0xa6, # VK_BROWSER_BACK
        'BROWSER_FORWARD':      0xa7, # VK_BROWSER_FORWARD
        'BROWSER_REFRESH':      0xa8, # VK_BROWSER_REFRESH
        'BROWSER_STOP':         0xa9, # VK_BROWSER_STOP
        'BROWSER_SEARCH':       0xaa, # VK_BROWSER_SEARCH
        'BROWSER_FAVORITES':    0xab, # VK_BROWSER_FAVORITES
        'BROWSER_HOME':         0xac, # VK_BROWSER_HOME
        'VOLUME_MUTE':          0xad, # VK_VOLUME_MUTE
        'VOLUME_DOWN':          0xae, # VK_VOLUME_DOWN
        'VOLUME_UP':            0xaf, # VK_VOLUME_UP
        'MEDIA_NEXT_TRACK':     0xb0, # VK_MEDIA_NEXT_TRACK
        'MEDIA_PREV_TRACK':     0xb1, # VK_MEDIA_PREV_TRACK
        'MEDIA_STOP':           0xb2, # VK_MEDIA_STOP
        'MEDIA_PLAY_PAUSE':     0xb3, # VK_MEDIA_PLAY_PAUSE
        'LAUNCH_MAIL':          0xb4, # VK_LAUNCH_MAIL
        'LAUNCH_MEDIA_SELECT':  0xb5, # VK_LAUNCH_MEDIA_SELECT
        'LAUNCH_APP1':          0xb6, # VK_LAUNCH_APP1
        'LAUNCH_APP2':          0xb7, # VK_LAUNCH_APP2
        'OEM_1_SEMICOLON':      0xba, # VK_OEM_1 (Semicolon)
        'OEM_PLUS':             0xbb, # VK_OEM_PLUS
        'OEM_COMMA':            0xbc, # VK_OEM_COMMA
        'OEM_MINUS':            0xbd, # VK_OEM_MINUS
        'OEM_PERIOD':           0xbe, # VK_OEM_PERIOD
        'OEM_2_SLASH':          0xbf, # VK_OEM_2 (Slash)
        'OEM_3_GRAVE':          0xc0, # VK_OEM_3 (Grave)
        'OEM_4_LBRACE':         0xdb, # VK_OEM_4 (LeftBrace)
        'OEM_5_BACKSLASH':      0xdc, # VK_OEM_5 (Backslash)
        'OEM_6_RBRACE':         0xdd, # VK_OEM_6 (RightBrace)
        'OEM_7_QUOTE':          0xde, # VK_OEM_7 (Quote)
        'OEM_8_RCTRL':          0xdf, # VK_OEM_8 (RightCtrl for Canadian CSA keyboard)
        'PACKET':               0xe7, # VK_PACKET
        'ATTN':                 0xf6, # VK_ATTN
        'CRSEL':                0xf7, # VK_CRSEL
        'EXSEL':                0xf8, # VK_EXSEL
        'EREOF':                0xf9, # VK_EREOF
        'PLAY':                 0xfa, # VK_PLAY
        'ZOOM':                 0xfb, # VK_ZOOM
        'NONAME':               0xfc, # VK_NONAME
        'PA1':                  0xfd, # VK_PA1
        'OEM_CLEAR':            0xfe, # VK_OEM_CLEAR
    }

    INPUT_KEYBOARD = 1

    KEYEVENTF_KEYDOWN   = 0x0000   # logical convenience (no bits)
    KEYEVENTF_KEYUP     = 0x0002
    KEYEVENTF_UNICODE   = 0x0004
    KEYEVENTF_SCANCODE  = 0x0008

    MAPVK_VK_TO_VSC = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._legacy_mode: Optional[bool] = None

        # Store modifier keycodes for internal use
        self._mods_keycodes: tuple = ()

        self._char_map: dict[str, tuple[KeyCode, str] | tuple[None, None]] = {}


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
            ('shift', self._get_keycode('SHIFT')),
            ('altgr', self._get_keycode('RMENU')),
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
            _chars_to_keys(["OEM_3_GRAVE"]) + _chars_to_keys(numbers) + _chars_to_keys(["OEM_MINUS", "OEM_PLUS"]) +
            _chars_to_keys(letters_1) + _chars_to_keys(["OEM_4_LBRACE", "OEM_6_RBRACE"]) +
            _chars_to_keys(letters_2) + _chars_to_keys(["OEM_1_SEMICOLON", "OEM_7_QUOTE", "OEM_5_BACKSLASH"]) +
            _chars_to_keys(letters_3) + _chars_to_keys(["OEM_COMMA", "OEM_PERIOD", "OEM_2_SLASH"])
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
            '\t':            (self._get_keycode("TAB"), ""),
            '\n':            (self._get_keycode("RETURN"), ""),
            '\r':            (self._get_keycode("RETURN"), ""),
            '\b':            (self._get_keycode("BACK"), ""),
            ' ':             (self._get_keycode("SPACE"), ""),
            'alt':           (self._get_keycode("MENU"), ""),
            'altgr':         (self._get_keycode("RMENU"), ""),
            'altleft':       (self._get_keycode("LMENU"), ""),
            'altright':      (self._get_keycode("RMENU"), ""),
            'backspace':     (self._get_keycode("BACK"), ""),
            'capslock':      (self._get_keycode("CAPITAL"), ""),
            'ctrl':          (self._get_keycode("CONTROL"), ""),
            'ctrlleft':      (self._get_keycode("LCONTROL"), ""),
            'ctrlright':     (self._get_keycode("RCONTROL"), ""),
            'del':           (self._get_keycode("DELETE"), ""),
            'delete':        (self._get_keycode("DELETE"), ""),
            'enter':         (self._get_keycode("RETURN"), ""),
            'esc':           (self._get_keycode("ESCAPE"), ""),
            'escape':        (self._get_keycode("ESCAPE"), ""),
            'help':          (self._get_keycode("HELP"), ""),
            'return':        (self._get_keycode("RETURN"), ""),
            'shift':         (self._get_keycode("SHIFT"), ""),
            'shiftleft':     (self._get_keycode("LSHIFT"), ""),
            'shiftright':    (self._get_keycode("RSHIFT"), ""),
            'space':         (self._get_keycode("SPACE"), ""),
            'tab':           (self._get_keycode("TAB"), ""),
            'win':           (self._get_keycode("LWIN"), ""),
            'winleft':       (self._get_keycode("LWIN"), ""),
            'winright':      (self._get_keycode("RWIN"), ""),
            'option':        (self._get_keycode("MENU"), ""),   # alias for alt
            'optionleft':    (self._get_keycode("LMENU"), ""),  # alias for altleft
            'optionright':   (self._get_keycode("RMENU"), ""),  # alias for altright

            # --- Navigation keys ---
            'down':       (self._get_keycode("DOWN"), ""),
            'end':        (self._get_keycode("END"), ""),
            'final':      (self._get_keycode("END"), ""),
            'home':       (self._get_keycode("HOME"), ""),
            'left':       (self._get_keycode("LEFT"), ""),
            'pagedown':   (self._get_keycode("NEXT"), ""),
            'pageup':     (self._get_keycode("PRIOR"), ""),
            'pgdn':       (self._get_keycode("NEXT"), ""),
            'pgup':       (self._get_keycode("PRIOR"), ""),
            'right':      (self._get_keycode("RIGHT"), ""),
            'up':         (self._get_keycode("UP"), ""),

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
            'add':         (self._get_keycode("ADD"), ""),
            'decimal':     (self._get_keycode("DECIMAL"), ""),
            'divide':      (self._get_keycode("DIVIDE"), ""),
            'multiply':    (self._get_keycode("MULTIPLY"), ""),
            'num0':        (self._get_keycode("NUMPAD0"), ""),
            'num1':        (self._get_keycode("NUMPAD1"), ""),
            'num2':        (self._get_keycode("NUMPAD2"), ""),
            'num3':        (self._get_keycode("NUMPAD3"), ""),
            'num4':        (self._get_keycode("NUMPAD4"), ""),
            'num5':        (self._get_keycode("NUMPAD5"), ""),
            'num6':        (self._get_keycode("NUMPAD6"), ""),
            'num7':        (self._get_keycode("NUMPAD7"), ""),
            'num8':        (self._get_keycode("NUMPAD8"), ""),
            'num9':        (self._get_keycode("NUMPAD9"), ""),
            'numlock':     (self._get_keycode("NUMLOCK"), ""),
            'separator':   (self._get_keycode("SEPARATOR"), ""),
            'subtract':    (self._get_keycode("SUBTRACT"), ""),

            # --- Media / system keys ---
            'apps':         (self._get_keycode("APPS"), ""),
            'insert':       (self._get_keycode("INSERT"), ""),
            'select':       (self._get_keycode("SELECT"), ""),
            'pause':        (self._get_keycode("PAUSE"), ""),
            'print':        (self._get_keycode("SNAPSHOT"), ""),
            'printscreen':  (self._get_keycode("SNAPSHOT"), ""),
            'prntscrn':     (self._get_keycode("SNAPSHOT"), ""),
            'prtsc':        (self._get_keycode("SNAPSHOT"), ""),
            'prtscr':       (self._get_keycode("SNAPSHOT"), ""),
            'scrolllock':   (self._get_keycode("SCROLL"), ""),
            'execute':      (self._get_keycode("EXECUTE"), ""),

            # --- Browser keys (not implemented) ---
            'browserback':        (self._get_keycode("BROWSER_BACK"), ""),
            'browserfavorites':   (self._get_keycode("BROWSER_FAVORITES"), ""),
            'browserforward':     (self._get_keycode("BROWSER_FORWARD"), ""),
            'browserhome':        (self._get_keycode("BROWSER_HOME"), ""),
            'browserrefresh':     (self._get_keycode("BROWSER_REFRESH"), ""),
            'browsersearch':      (self._get_keycode("BROWSER_SEARCH"), ""),
            'browserstop':        (self._get_keycode("BROWSER_STOP"), ""),

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

    def _get_keycode(self, key: str) -> KeyCode:
        """Return the Windows virtual keycode for the given key name or single character.
        """
        # direct named key first
        kc = self.KEYCODES_BASE.get(key, None)
        if kc is not None:
            return kc

        # nothing found
        logging.debug(f"No keycode found for '{key}'")
        return 0

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

    def _build_input(self, vk_code: int = 0, scan_code: int = 0, flags: int = 0):
        """Builds an INPUT structure for keyboard events.

        Args:
            vk_code: Virtual key code (VK_*).
            scan_code: Hardware scan code.
            flags: KEYEVENTF flags.

        Returns:
            INPUT structure ready for SendInput.

        Implementation Notes:
            - Sets up the INPUT structure with proper fields.
            - Handles extended keys (like right arrow).
        """
        ki = KEYBDINPUT()
        ki.wVk = vk_code
        ki.wScan = scan_code
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
        """Emit a key press/release using SendInput (modern) or keybd_event (legacy fallback).
        We map vk -> scancode for wScan using MapVirtualKey.
        """
        def _send_input_legacy(keycode: int, scancode: int, press: bool):
            # Old Windows fallback
            try:
                flags = self.KEYEVENTF_KEYDOWN if press else self.KEYEVENTF_KEYUP
                self._user32.keybd_event(keycode, scancode, flags, 0)
            except Exception as e:
                logging.error(f"[Legacy keybd_event] Failed to emit keycode={keycode}: {e}")

        def _send_input(keycode: int, scancode: int, press: bool):
            flag = self.KEYEVENTF_KEYDOWN if press else self.KEYEVENTF_KEYUP
            inp = self._build_input(vk_code=keycode, scan_code=scancode & 0xFFFF, flags=flag)
            if not send_input(self._user32, inp):
                err = get_last_error(self._kernel32)
                logging.warning(f"emit_key->SendInput(keycode={keycode}, press={press}) failed: GetLastError={err}")

        mapping = self._char_map.get(key)
        if mapping is None:
            raise PyAutoGUIException(f"Error: key '{key}' not implemented")

        keycode, mods = mapping
        if keycode is None:
            raise PyAutoGUIException(f"Error: no keycode mapped for key '{key}'")

        scancode = self._user32.MapVirtualKeyW(keycode, self.MAPVK_VK_TO_VSC)

        logging.debug(f"emit key: {key}, code={keycode}, scancode={scancode}, mods={mods}, press={press}")

        send_input_func = _send_input_legacy if self._is_legacy() else _send_input

        # Press modifiers if pressing the key
        if mods and press:
            for mod_name, mod_keycode in self._mods_keycodes:
                if mod_name in mods:
                    send_input_func(mod_keycode, scancode, True)

        send_input_func(keycode, scancode, press)

        # Then release modifiers in reverse-ish order
        if mods and not press:
            for mod_name, mod_keycode in reversed(self._mods_keycodes):
                if mod_name in mods:
                    send_input_func(mod_keycode, scancode, False)

    def _emit_unicode_char(self, char: str) -> None:
        """Send a Unicode character directly (if supported),
        or fallback to '?' for legacy systems.
        Use VK_PACKET (0xE7) and KEYEVENTF_UNICODE. This is the recommended approach.
        """
        if self._is_legacy():
            logging.warning(f"Unicode '{char}' not supported in legacy mode -> using '?' placeholder")
            self._emit_key("?", press=True)
            self._emit_key("?", press=False)
            return

        def _send_input(codepoint: int, press: bool):
            if codepoint > 0xFFFF:
                logging.warning(f"Codepoint (0x{codepoint:04X}) > 0xFFFF may not render correctly on Windows SendInput()")
            flags = self.KEYEVENTF_KEYDOWN if press else self.KEYEVENTF_KEYUP
            flags |= self.KEYEVENTF_UNICODE
            # Use VK_PACKET with wScan=unicode codepoint
            inp = self._build_input(vk_code=self._get_keycode('PACKET'), scan_code=codepoint & 0xFFFF, flags=flags)
            if not send_input(self._user32, inp):
                err = get_last_error(self._kernel32)
                logging.warning(f"emit_unicode_char->SendInput(codepoint={codepoint}, press={press}) failed: GetLastError={err}")

        cp = ord(char)

        # Press / Release
        _send_input(cp, press=True)
        _send_input(cp, press=False)

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
        return self._char_map.get(key, (None, None)) != (None, None)

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
