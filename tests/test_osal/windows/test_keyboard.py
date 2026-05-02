"""Unit tests for WindowsKeyboard."""
from unittest.mock import call, patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException


def _helper_build_call_input(windows_keyboard, key, press=True, legacy=False):
    from pyautogui2.osal.windows._common import INPUT
    from tests.mocks.osal.windows.mock_ctypes import sizeof

    output_calls = []

    (scancode, is_ext), mods = windows_keyboard._char_map.get(key)

    if mods and press:
        for name, (mod_code, mod_ext) in windows_keyboard._mods_scancodes:
            if name in mods:
                mod_flags = windows_keyboard.KEYEVENTF_SCANCODE | windows_keyboard.KEYEVENTF_KEYDOWN
                if mod_ext:
                    mod_flags |= windows_keyboard.KEYEVENTF_EXTENDEDKEY

                if legacy:
                    c = call(0, mod_code, mod_flags, 0)
                else:
                    inp = windows_keyboard._build_input(mod_code, mod_flags)
                    c = call(1, inp, sizeof(INPUT))
                output_calls.append(c)

    flags = windows_keyboard.KEYEVENTF_KEYDOWN if press else windows_keyboard.KEYEVENTF_KEYUP
    flags |= windows_keyboard.KEYEVENTF_SCANCODE
    if is_ext:
        flags |= windows_keyboard.KEYEVENTF_EXTENDEDKEY

    if legacy:
        c = call(0, scancode, flags, 0)
    else:
        inp = windows_keyboard._build_input(scancode, flags)
        c = call(1, inp, sizeof(INPUT))

    output_calls.append(c)

    if mods and not press:
        for name, (mod_code, mod_ext) in reversed(windows_keyboard._mods_scancodes):
            if name in mods:
                mod_flags = windows_keyboard.KEYEVENTF_SCANCODE | windows_keyboard.KEYEVENTF_KEYUP
                if mod_ext:
                    mod_flags |= windows_keyboard.KEYEVENTF_EXTENDEDKEY

                if legacy:
                    c = call(0, mod_code, mod_flags, 0)
                else:
                    inp = windows_keyboard._build_input(mod_code, mod_flags)
                    c = call(1, inp, sizeof(INPUT))
                output_calls.append(c)

    return output_calls

def _helper_build_call_input_unicode(windows_keyboard, key):
    from pyautogui2.osal.windows._common import INPUT
    from tests.mocks.osal.windows.mock_ctypes import sizeof

    codepoint = ord(key)
    if codepoint > 0xFFFF:
        encoded = key.encode('utf-16-le')  # 4 bytes for surrogate pair
        high = int.from_bytes(encoded[0:2], 'little')  # high surrogate
        low  = int.from_bytes(encoded[2:4], 'little')  # low surrogate
        scancodes = [high, low]
    else:
        scancodes = [codepoint]

    flags = windows_keyboard.KEYEVENTF_UNICODE

    output_calls = []
    for sc in scancodes:
        inp_down = windows_keyboard._build_input(sc & 0xFFFF, flags | windows_keyboard.KEYEVENTF_KEYDOWN)
        output_calls.append(call(1, inp_down, sizeof(INPUT)))

        inp_up = windows_keyboard._build_input(sc & 0xFFFF, flags | windows_keyboard.KEYEVENTF_KEYUP)
        output_calls.append(call(1, inp_up, sizeof(INPUT)))

    return output_calls


class TestKeyboardSetupPostInit:
    """Tests for WindowsKeyboard.setup_postinit()."""

    def test_setup_postinit_success(self, windows_keyboard):
        """setup_postinit builds _char_map when valid inputs are provided."""
        assert isinstance(windows_keyboard._char_map, dict)
        assert len(windows_keyboard._char_map) > 0

    def test_setup_postinit_invalid_args_raise(self, windows_keyboard):
        """Missing key_names or all_keymapping raises ValueError."""
        with pytest.raises(ValueError):
            windows_keyboard.setup_postinit(key_names=None, all_keymapping={})
        with pytest.raises(ValueError):
            windows_keyboard.setup_postinit(key_names=[], all_keymapping=None)

    def test_setup_postinit_unsupported_layout(self, windows_keyboard):
        """Test unsupported layout raises PyAutoGUIException."""
        with patch.object(windows_keyboard, 'get_layout', return_value='unknown_layout'), \
             pytest.raises(PyAutoGUIException, match="unsupported layout 'unknown_layout'"):
            windows_keyboard.setup_postinit(
                all_keymapping={'fr': {}},
                key_names=[],
            )

    def test_setup_postinit_keymapping_with_doublon(self, windows_keyboard):
        """Test all_keymapping contains character twice, should ignore second mapping."""
        from pyautogui2.controllers.keyboard import KeyboardController as KC

        windows_keyboard.setup_postinit(
            all_keymapping={
                'QWERTY': {
                    "_": KC.KEYBOARD_MAPPINGS["QWERTY"]["_"],
                    "altgr": KC.KEYBOARD_MAPPINGS["QWERTY"]["_"],       # all chars are already mapped
                }
            },
            key_names=[],
        )

        # Mapping with "altgr" modified should be ignored, because already mapped with "_" modifier
        assert windows_keyboard._char_map["a"][1] == "_"


class TestKeyboardGetKeycode:
    """Tests for WindowsKeyboard._get_scancode()."""

    def test_get_scancode_known(self, windows_keyboard):
        # Known mapping present in SCANCODES_BASE -> e.g., "a" -> 0x1E
        scancode, is_extended = windows_keyboard._get_scancode("a")
        assert isinstance(scancode, int)
        assert scancode == 0x1E
        assert is_extended is False

    def test_get_scancode_unknown_returns_zero(self, windows_keyboard):
        scancode, is_extended = windows_keyboard._get_scancode("NON_EXISTENT_KEY")
        assert scancode == 0
        assert is_extended is False


class TestKeyboardDetectLayout:
    """Tests for WindowsKeyboard._detect_layout()."""

    def test_detect_layout_hex_string(self, windows_keyboard):
        windows_keyboard._winreg.QueryValueEx.side_effect = RuntimeError("failed")
        windows_keyboard._user32.GetKeyboardLayout.return_value = 0x040C  # sample French layout
        s = windows_keyboard._detect_layout()
        assert isinstance(s, str)
        assert s == "0x040c"


class TestKeyboardBuildInput:
    """Tests for WindowsKeyboard._build_input()."""

    def test_build_input_fields(self, windows_keyboard):
        inp = windows_keyboard._build_input(0x1E, windows_keyboard.KEYEVENTF_SCANCODE | windows_keyboard.KEYEVENTF_KEYDOWN)
        # The returned object must be an INPUT with u.ki fields present
        assert hasattr(inp, "u")
        assert hasattr(inp.u, "ki")
        assert inp.u.ki.wVk == 0
        assert inp.u.ki.wScan == 0x1E & 0xFFFF
        assert inp.u.ki.dwFlags == windows_keyboard.KEYEVENTF_SCANCODE | windows_keyboard.KEYEVENTF_KEYDOWN


class TestKeyboardEmitKey:
    """Tests for WindowsKeyboard._emit_key (modern and legacy paths)."""

    def test_emit_key_modern_sendinput_success(self, windows_keyboard):
        """Modern: send_input returns True -> no fallback to keybd_event."""
        windows_keyboard._user32.SendInput.return_value = True
        for press in [True, False]:
            windows_keyboard._emit_key("a", press=press)
            calls = _helper_build_call_input(windows_keyboard, "a", press=press)
            windows_keyboard._user32.SendInput.assert_has_calls(calls)
            windows_keyboard._user32.SendInput.reset_mocks()

    def test_emit_key_extended_flag_needed(self, windows_keyboard):
        """Extended keys (like LEFT, DELETE, etc.) need KEYEVENTF_EXTENDEDKEY flag."""
        windows_keyboard._user32.SendInput.return_value = True
        for press in [True, False]:
            windows_keyboard._emit_key("left", press=press)
            calls = _helper_build_call_input(windows_keyboard, "left", press=press)
            windows_keyboard._user32.SendInput.assert_has_calls(calls)
            windows_keyboard._user32.SendInput.reset_mocks()

    def test_emit_key_sendinput_failure_logs_and_no_exception(self, windows_keyboard):
        """If send_input returns False, a warning is logged but no exception thrown."""
        windows_keyboard._user32.SendInput.return_value = False
        with patch("pyautogui2.osal.windows.keyboard.get_last_error", return_value=123):
            # Should not raise, just log a warning internally
            windows_keyboard.key_down("b")

    def test_emit_key_legacy_fallback_uses_keybd_event(self, windows_keyboard):
        """When in legacy mode, keybd_event should be called (legacy path)."""
        windows_keyboard._legacy_mode = True
        windows_keyboard.key_down("c")
        windows_keyboard.key_up("c")

        calls_down = _helper_build_call_input(windows_keyboard, "c", press=True, legacy=True)
        calls_up = _helper_build_call_input(windows_keyboard, "c", press=False, legacy=True)

        windows_keyboard._user32.keybd_event.assert_has_calls(calls_down + calls_up)

    def test_emit_key_legacy_logs_error(self, windows_keyboard, caplog):
        import logging
        windows_keyboard._legacy_mode = True
        windows_keyboard._user32.keybd_event.side_effect = OSError("mock error")
        with caplog.at_level(logging.ERROR):
            windows_keyboard._emit_key("a", press=True)
        assert "[keybd_event]" in caplog.text
        assert "mock error" in caplog.text

    def test_emit_key_invalid_key_raises(self, windows_keyboard):
        """Emitting a key not present in _char_map raises PyAutoGUIException."""
        with pytest.raises(PyAutoGUIException, match="Key 'NOT_EXIST' not implemented"):
            windows_keyboard._emit_key("NOT_EXIST", press=True)

    def test_emit_key_unmapped_key_raises(self, windows_keyboard):
        """Emitting a key not mapped raises PyAutoGUIException."""
        windows_keyboard._char_map["NOT_MAPPED"] = ((None, None), None)
        with pytest.raises(PyAutoGUIException, match="No scancode mapped for key 'NOT_MAPPED'"):
            windows_keyboard._emit_key("NOT_MAPPED", press=True)

    def test_emit_key_with_modifiers_emits_modifier_keys(self, windows_keyboard):
        """If mapping requires modifiers, modifier keys are emitted around the key press."""
        windows_keyboard._user32.SendInput.return_value = True
        windows_keyboard.key_down("A")    # "shift" + "a"
        windows_keyboard.key_up("A")      # "a" + "shift"

        calls_down = _helper_build_call_input(windows_keyboard, "A", press=True)
        calls_up = _helper_build_call_input(windows_keyboard, "A", press=False)

        windows_keyboard._user32.SendInput.assert_has_calls(calls_down + calls_up)


class TestKeyboardEmitUnicodeChar:
    """Tests for WindowsKeyboard._emit_unicode_char()."""

    def test_emit_unicode_char_modern_uses_sendinput_twice(self, windows_keyboard):
        """Modern path: send_input called twice (press + release) with KEYEVENTF_UNICODE."""
        windows_keyboard._user32.SendInput.return_value = True
        windows_keyboard._emit_unicode_char("é")  # non-ascii char

        calls = _helper_build_call_input_unicode(windows_keyboard, "é")
        windows_keyboard._user32.SendInput.assert_has_calls(calls)

    def test_emit_unicode_char_legacy_uses_placeholder(self, windows_keyboard):
        """Legacy mode: unicode not supported -> fallback to "?" key emitted."""
        windows_keyboard._legacy_mode = True
        windows_keyboard._emit_unicode_char("Ω")  # fallback should generate two "?" emits

        calls_down = _helper_build_call_input(windows_keyboard, "?", press=True, legacy=True)
        calls_up = _helper_build_call_input(windows_keyboard, "?", press=False, legacy=True)
        windows_keyboard._user32.keybd_event.assert_has_calls(calls_down + calls_up)

    def test_emit_unicode_send_input_failure_warns(self, windows_keyboard, caplog):
        """Test _emit_unicode_char() warnings."""
        import logging
        with patch.object(windows_keyboard, '_is_legacy', return_value=False), \
             patch('pyautogui2.osal.windows.keyboard.send_input', return_value=False), \
             patch('pyautogui2.osal.windows.keyboard.get_last_error', return_value=42), \
             caplog.at_level(logging.WARNING):
            windows_keyboard._emit_unicode_char('A')

        assert "emit_unicode_char->SendInput" in caplog.text
        assert "GetLastError=42" in caplog.text


class TestKeyboardCodepointCtx:
    """Tests for the codepoint_ctx context manager."""

    def test_codepoint_ctx_calls_emit_unicode_char(self, windows_keyboard):
        """Calling type_codepoint_value should delegate to _emit_unicode_char."""
        with windows_keyboard.codepoint_ctx() as ctx:
            ctx.type_codepoint_value("00E9")  # é

        calls = _helper_build_call_input_unicode(windows_keyboard, "é")
        windows_keyboard._user32.SendInput.assert_has_calls(calls)

    @patch("time.sleep")
    def test_codepoint_surrogate_pair(self, mock_sleep, windows_keyboard):
        """Codepoint greater than 0xFFFF should use surrogate pair."""
        with windows_keyboard.codepoint_ctx() as ctx:
            ctx.type_codepoint_value("1F389")  # 🎉

        calls = _helper_build_call_input_unicode(windows_keyboard, "🎉")
        windows_keyboard._user32.SendInput.assert_has_calls(calls)

        mock_sleep.assert_called_once_with(0.01)

    def test_type_codepoint_value_error_logs_and_falls_back(self, windows_keyboard, caplog):
        """Test type_codepoint_value() fallback on error."""
        import logging
        with patch.object(windows_keyboard, '_emit_unicode_char', side_effect=RuntimeError("boom")), \
             caplog.at_level(logging.ERROR), \
             windows_keyboard.codepoint_ctx() as ctx:
            ctx.type_codepoint_value("00E9")  # é
        assert "Failed to type codepoint" in caplog.text


class TestKeyboardMappingsAndLayout:
    """Tests for key_is_mapped() and get_layout()."""

    def test_key_is_mapped_true_false(self, windows_keyboard):
        assert windows_keyboard.key_is_mapped("a")
        assert not windows_keyboard.key_is_mapped("z_not_mapped")

    def test_get_layout_success(self, windows_keyboard):
        windows_keyboard._winreg.QueryValueEx.return_value = ("00000040C", None)    # Force AZERTY layout
        assert windows_keyboard.get_layout() == "AZERTY"

    def test_get_layout_success_fallback(self, windows_keyboard):
        windows_keyboard._winreg.QueryValueEx.side_effect = RuntimeError("failed")
        windows_keyboard._user32.GetKeyboardLayout.return_value = 0x040C    # Force AZERTY layout
        assert windows_keyboard.get_layout() == "AZERTY"

    def test_get_layout_invalid_raise(self, windows_keyboard):
        # Unsupported layout -> raises PyAutoGUIException
        windows_keyboard._winreg.QueryValueEx.return_value = ("000001234", None)
        with pytest.raises(PyAutoGUIException):
            windows_keyboard.get_layout()


class TestKeyboardKeyDownUp:
    """Tests for key_down and key_up wrappers."""

    def test_key_down_and_key_up_delegate_to_emit(self, windows_keyboard):
        windows_keyboard.key_down("a")
        windows_keyboard.key_up("a")
        calls_down = _helper_build_call_input(windows_keyboard, "a", press=True)
        calls_up = _helper_build_call_input(windows_keyboard, "a", press=False)
        windows_keyboard._user32.SendInput.assert_has_calls(calls_down + calls_up)

        windows_keyboard.key_down("A")  # "shift" + "a"
        windows_keyboard.key_up("A")    # "a" + "shift"
        calls_down = _helper_build_call_input(windows_keyboard, "A", press=True)
        calls_up = _helper_build_call_input(windows_keyboard, "A", press=False)
        windows_keyboard._user32.SendInput.assert_has_calls(calls_down + calls_up)


class TestKeyboardLegacyMode:
    """Test legacy mode detection and warning."""

    def test_is_legacy_logs_warning(self, windows_keyboard, caplog):
        import logging
        with patch('pyautogui2.osal.windows.keyboard.is_legacy_windows', return_value=True):
            windows_keyboard._legacy_mode = None
            with caplog.at_level(logging.WARNING):
                result = windows_keyboard._is_legacy()
            assert result is True
            assert "legacy mode enabled" in caplog.text

    def test_is_legacy_no_warning_when_not_legacy(self, windows_keyboard, caplog):
        import logging
        with patch('pyautogui2.osal.windows.keyboard.is_legacy_windows', return_value=False):
            windows_keyboard._legacy_mode = None
            with caplog.at_level(logging.WARNING):
                result = windows_keyboard._is_legacy()
            assert result is False
            assert "legacy mode" not in caplog.text
