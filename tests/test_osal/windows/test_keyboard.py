"""Unit tests for WindowsKeyboard."""
from unittest.mock import call, patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException


def _helper_build_call_input(windows_keyboard, key, press=True, is_unicode=False, legacy=False):
    from pyautogui2.osal.windows._common import INPUT
    from tests.mocks.osal.windows.mock_ctypes import sizeof

    flags = windows_keyboard.KEYEVENTF_KEYDOWN if press else windows_keyboard.KEYEVENTF_KEYUP
    output_calls = []

    if is_unicode:
        codepoint = ord(key)
        flags |= windows_keyboard.KEYEVENTF_UNICODE
        # Use VK_PACKET with wScan=unicode codepoint
        inp = windows_keyboard._build_input(vk_code=windows_keyboard._get_keycode('PACKET'), scan_code=codepoint & 0xFFFF, flags=flags)
        return [call(1, inp, sizeof(INPUT))]

    keycode, mods = windows_keyboard._char_map.get(key)

    if mods and press:
        for name, code in windows_keyboard._mods_keycodes:
            if name in mods:
                if legacy:
                    c = call(code, 0, windows_keyboard.KEYEVENTF_KEYDOWN, 0)
                else:
                    inp = windows_keyboard._build_input(vk_code=code, flags=windows_keyboard.KEYEVENTF_KEYDOWN)
                    c = call(1, inp, sizeof(INPUT))
                output_calls.append(c)

    if legacy:
        c = call(keycode, 0, flags, 0)
    else:
        inp = windows_keyboard._build_input(vk_code=keycode, flags=flags)
        c = call(1, inp, sizeof(INPUT))

    output_calls.append(c)

    if mods and not press:
        for name, code in reversed(windows_keyboard._mods_keycodes):
            if name in mods:
                if legacy:
                    c = call(code, 0, windows_keyboard.KEYEVENTF_KEYUP, 0)
                else:
                    inp = windows_keyboard._build_input(vk_code=code, flags=windows_keyboard.KEYEVENTF_KEYUP)
                    c = call(1, inp, sizeof(INPUT))
                output_calls.append(c)

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
    """Tests for WindowsKeyboard._get_keycode()."""

    def test_get_keycode_known(self, windows_keyboard):
        # Known mapping present in KEYCODES_BASE -> e.g., "a" -> 0x41
        code = windows_keyboard._get_keycode("a")
        assert isinstance(code, int)
        assert code == 0x41

    def test_get_keycode_unknown_returns_zero(self, windows_keyboard):
        code = windows_keyboard._get_keycode("NON_EXISTENT_KEY")
        assert code == 0


class TestKeyboardDetectLayout:
    """Tests for WindowsKeyboard._detect_layout()."""

    def test_detect_layout_hex_string(self, windows_keyboard):
        windows_keyboard._user32.GetKeyboardLayout.return_value = 0x040C  # sample French layout
        s = windows_keyboard._detect_layout()
        assert isinstance(s, str)
        assert s == "0x040c"


class TestKeyboardBuildInput:
    """Tests for WindowsKeyboard._build_input()."""

    def test_build_input_fields(self, windows_keyboard):
        inp = windows_keyboard._build_input(vk_code=0x41, scan_code=0x1E, flags=windows_keyboard.KEYEVENTF_KEYDOWN)
        # The returned object must be an INPUT with u.ki fields present
        assert hasattr(inp, "u")
        assert hasattr(inp.u, "ki")
        assert inp.u.ki.wVk == 0x41
        assert inp.u.ki.wScan == 0x1E & 0xFFFF
        assert inp.u.ki.dwFlags == windows_keyboard.KEYEVENTF_KEYDOWN


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
        assert "[Legacy keybd_event]" in caplog.text
        assert "mock error" in caplog.text

    def test_emit_key_invalid_key_raises(self, windows_keyboard):
        """Emitting a key not present in _char_map raises PyAutoGUIException."""
        with pytest.raises(PyAutoGUIException, match="Error: key 'NOT_EXIST' not implemented"):
            windows_keyboard._emit_key("NOT_EXIST", press=True)

    def test_emit_key_unmapped_key_raises(self, windows_keyboard):
        """Emitting a key not mapped raises PyAutoGUIException."""
        windows_keyboard._char_map["NOT_MAPPED"] = (None, "mod")
        with pytest.raises(PyAutoGUIException, match="Error: no keycode mapped for key 'NOT_MAPPED'"):
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

        calls_down = _helper_build_call_input(windows_keyboard, "é", press=True, is_unicode=True)
        calls_up = _helper_build_call_input(windows_keyboard, "é", press=False, is_unicode=True)
        windows_keyboard._user32.SendInput.assert_has_calls(calls_down + calls_up)

    def test_emit_unicode_char_legacy_uses_placeholder(self, windows_keyboard):
        """Legacy mode: unicode not supported -> fallback to "?" key emitted."""
        windows_keyboard._legacy_mode = True
        windows_keyboard._emit_unicode_char("Ω")  # fallback should generate two "?" emits

        calls_down = _helper_build_call_input(windows_keyboard, "?", press=True, legacy=True)
        calls_up = _helper_build_call_input(windows_keyboard, "?", press=False, legacy=True)
        windows_keyboard._user32.keybd_event.assert_has_calls(calls_down + calls_up)

    def test_emit_unicode_large_codepoint_warns(self, windows_keyboard, caplog):
        """Test _emit_unicode_char() warnings."""
        import logging
        with patch.object(windows_keyboard, '_is_legacy', return_value=False), \
             caplog.at_level(logging.WARNING):
            windows_keyboard._emit_unicode_char(chr(0x1F600))  # emoji > 0xFFFF
        assert "0xFFFF" in caplog.text

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

        calls_down = _helper_build_call_input(windows_keyboard, "é", press=True, is_unicode=True)
        calls_up = _helper_build_call_input(windows_keyboard, "é", press=False, is_unicode=True)
        windows_keyboard._user32.SendInput.assert_has_calls(calls_down + calls_up)

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

    def test_get_layout_success_and_failure(self, windows_keyboard):
        windows_keyboard._user32.GetKeyboardLayout.return_value = 0x040C    # Force AZERTY layout
        assert windows_keyboard.get_layout() == "AZERTY"

        # Unsupported layout -> raises PyAutoGUIException
        windows_keyboard._user32.GetKeyboardLayout.return_value = 0x1234
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
