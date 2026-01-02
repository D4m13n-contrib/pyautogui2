"""Unit tests for MacOSKeyboard."""
from unittest.mock import call, patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException


class TestKeyboardSetupPostInit:
    """Tests for MacOSKeyboard.setup_postinit()."""

    def test_setup_postinit_success(self, macos_keyboard):
        """setup_postinit builds _char_map when valid inputs are provided."""
        assert isinstance(macos_keyboard._char_map, dict)
        assert len(macos_keyboard._char_map) > 0

    def test_setup_postinit_invalid_args_raise(self, macos_keyboard):
        """Missing key_names or all_keymapping raises ValueError."""
        with pytest.raises(ValueError):
            macos_keyboard.setup_postinit(key_names=None, all_keymapping={})
        with pytest.raises(ValueError):
            macos_keyboard.setup_postinit(key_names=[], all_keymapping=None)

    def test_setup_postinit_unsupported_layout(self, macos_keyboard):
        """Test unsupported layout raises PyAutoGUIException."""
        with patch.object(macos_keyboard, 'get_layout', return_value='unknown_layout'), \
             pytest.raises(PyAutoGUIException, match="unsupported layout 'unknown_layout'"):
            macos_keyboard.setup_postinit(
                all_keymapping={'fr': {}},
                key_names=[],
            )

    def test_setup_postinit_keymapping_with_doublon(self, macos_keyboard):
        """Test all_keymapping contains character twice, should ignore second mapping."""
        from pyautogui2.controllers.keyboard import KeyboardController as KC

        macos_keyboard.setup_postinit(
            all_keymapping={
                'QWERTY': {
                    "_": KC.KEYBOARD_MAPPINGS["QWERTY"]["_"],
                    "altgr": KC.KEYBOARD_MAPPINGS["QWERTY"]["_"],       # all chars are already mapped
                }
            },
            key_names=[],
        )

        # Mapping with "altgr" modified should be ignored, because already mapped with "_" modifier
        assert macos_keyboard._char_map["a"][1] == "_"


class TestKeyboardGetKeycode:
    """Tests for MacOSKeyboard._get_keycode()."""

    def test_get_keycode_known(self, macos_keyboard):
        # Known mapping present in KEYCODES_BASE -> e.g., "y" -> 0x10
        code = macos_keyboard._get_keycode("y")
        assert isinstance(code, int)
        assert code == 0x10

    def test_get_keycode_unknown_returns_zero(self, macos_keyboard, caplog):
        import logging

        with caplog.at_level(logging.DEBUG):
            code = macos_keyboard._get_keycode("NON_EXISTENT_KEY")

        assert code == 0
        assert "No keycode found for 'NON_EXISTENT_KEY'" in caplog.text


class TestKeyboardDetectLayout:
    """Tests for MacOSKeyboard._detect_layout()."""

    @pytest.mark.parametrize("param_id, param_name", [
        ("US", "US"),
        ("British", "British"),
        ("French-AZERTY", "French - AZERTY"),
        ("SwissGerman", "Swiss German"),
    ])
    def test_detect_layout_success(self, param_id, param_name, macos_keyboard):
        macos_keyboard._mocks["mock_launch_services"].mock_set_keyboard_layout(f"com.apple.keylayout.{param_id}", f"{param_name}")
        s = macos_keyboard._detect_layout()
        assert isinstance(s, str)
        assert s == param_name

        macos_keyboard._mocks["mock_launch_services"].mock_set_keyboard_layout(None, f"{param_name}")
        s = macos_keyboard._detect_layout()
        assert isinstance(s, str)
        assert s == param_name

    def test_detect_layout_no_layout_raise(self, macos_keyboard):
        macos_keyboard._mocks["mock_launch_services"].mock_set_keyboard_layout(None, None)
        with pytest.raises(PyAutoGUIException, match=r"Could not detect keyboard layout \(from 'None' or 'None'\)"):
            _ = macos_keyboard._detect_layout()

    def test_detect_layout_no_input_source_raise(self, macos_keyboard):
        macos_keyboard._mocks["mock_launch_services"].TISCopyCurrentKeyboardLayoutInputSource.return_value = None
        with pytest.raises(PyAutoGUIException, match="Unable to get input source"):
            _ = macos_keyboard._detect_layout()

    def test_detect_layout_exception_raise(self, macos_keyboard):
        macos_keyboard._mocks["mock_launch_services"].TISGetInputSourceProperty.side_effect = Exception("Error")
        with pytest.raises(PyAutoGUIException, match="Unable to query TIS keyboard layout"):
            _ = macos_keyboard._detect_layout()


class TestKeyboardEmitKey:
    """Tests for MacOSKeyboard._emit_key()."""

    def test_emit_key_success(self, macos_keyboard):
        """Modern: send_input returns True -> no fallback to keybd_event."""
        for press in [True, False]:
            macos_keyboard._emit_key("y", press=press)

        mock_quartz = macos_keyboard._mocks["mock_quartz"]
        mock_quartz.CGEventCreateKeyboardEvent.assert_has_calls([
            call(None, 0x10, True),
            call(None, 0x10, False),
        ])
        assert mock_quartz.CGEventPost.call_count == 2

    def test_emit_key_invalid_key_raises(self, macos_keyboard):
        """Emitting a key not present in _char_map raises PyAutoGUIException."""
        with pytest.raises(PyAutoGUIException, match="Error: key 'NOT_EXIST' not implemented"):
            macos_keyboard._emit_key("NOT_EXIST", press=True)

    def test_emit_key_unmapped_key_raises(self, macos_keyboard):
        """Emitting a key not mapped raises PyAutoGUIException."""
        macos_keyboard._char_map["NOT_MAPPED"] = (None, "mod")
        with pytest.raises(PyAutoGUIException, match="Error: no keycode mapped for key 'NOT_MAPPED'"):
            macos_keyboard._emit_key("NOT_MAPPED", press=True)

    def test_emit_key_with_modifiers_emits_modifier_keys(self, macos_keyboard):
        """If mapping requires modifiers, modifier keys are emitted around the key press."""
        macos_keyboard.key_down("Y")    # "shift" + "y"
        macos_keyboard.key_up("Y")      # "y" + "shift"

        mock_quartz = macos_keyboard._mocks["mock_quartz"]
        mock_quartz.CGEventCreateKeyboardEvent.assert_has_calls([
            call(None, 0x38, True),
            call(None, 0x10, True),
            call(None, 0x10, False),
            call(None, 0x38, False),
        ])
        assert mock_quartz.CGEventPost.call_count == 4


class TestKeyboardEmitUnicodeChar:
    """Tests for MacOSKeyboard._emit_unicode_char()."""

    @pytest.mark.parametrize("char, char_length", [
        ("é", 1),
        ("Ω", 1),
        ("🎉", 2),
    ])
    def test_emit_unicode_char_success(self, char, char_length, macos_keyboard):
        macos_keyboard._emit_unicode_char(char)  # non-ascii char

        mock_quartz = macos_keyboard._mocks["mock_quartz"]
        mock_quartz.CGEventCreateKeyboardEvent.assert_has_calls([
            call(None, 0, True),
            call(None, 0, False),
        ])
        mock_quartz.CGEventKeyboardSetUnicodeString.assert_has_calls([
            call(None, char_length, char.encode("utf-16-le")),
            call(None, char_length, char.encode("utf-16-le")),
        ])
        assert mock_quartz.CGEventPost.call_count == 2


class TestKeyboardCodepointCtx:
    """Tests for the codepoint_ctx context manager."""

    def test_codepoint_ctx_calls_emit_unicode_char(self, macos_keyboard):
        """Calling type_codepoint_value should delegate to _emit_unicode_char."""
        with macos_keyboard.codepoint_ctx() as ctx:
            ctx.type_codepoint_value("00E9")  # é

        mock_quartz = macos_keyboard._mocks["mock_quartz"]
        mock_quartz.CGEventCreateKeyboardEvent.assert_has_calls([
            call(None, 0, True),
            call(None, 0, False),
        ])
        mock_quartz.CGEventKeyboardSetUnicodeString.assert_has_calls([
            call(None, 1, b"\xe9\x00"),
            call(None, 1, b"\xe9\x00"),
        ])
        assert mock_quartz.CGEventPost.call_count == 2

    def test_codepoint_ctx_invalid_codepoint_raise(self, macos_keyboard):
        """Calling type_codepoint_value with invalid codepoint should raise ValueError."""
        with macos_keyboard.codepoint_ctx() as ctx, \
             pytest.raises(ValueError, match="Invalid hex codepoint: XXXX"):
            ctx.type_codepoint_value("XXXX")


class TestKeyboardMappingsAndLayout:
    """Tests for key_is_mapped() and get_layout()."""

    def test_key_is_mapped_true_false(self, macos_keyboard):
        assert macos_keyboard.key_is_mapped("a")
        assert not macos_keyboard.key_is_mapped("z_not_mapped")

    def test_get_layout_success_and_failure(self, macos_keyboard):
        macos_keyboard._mocks["mock_launch_services"].mock_set_keyboard_layout(None, "French")    # Force AZERTY layout
        assert macos_keyboard.get_layout() == "AZERTY"

        # Unsupported layout -> raises PyAutoGUIException
        macos_keyboard._mocks["mock_launch_services"].mock_set_keyboard_layout(None, "Unsupported")
        with pytest.raises(PyAutoGUIException, match="Layout 'Unsupported' is unsupported by PyAutoGUI"):
            macos_keyboard.get_layout()


class TestKeyboardKeyDownUp:
    """Tests for key_down and key_up wrappers."""

    def test_key_down_and_key_up_delegate_to_emit(self, macos_keyboard):
        macos_keyboard.key_down("y")
        macos_keyboard.key_up("y")
        mock_quartz = macos_keyboard._mocks["mock_quartz"]
        mock_quartz.CGEventCreateKeyboardEvent.assert_has_calls([
            call(None, 0x10, True),
            call(None, 0x10, False),
        ])
        assert mock_quartz.CGEventPost.call_count == 2

        mock_quartz.CGEventCreateKeyboardEvent.reset_mock()
        mock_quartz.CGEventPost.reset_mock()

        macos_keyboard.key_down("Y")  # "shift" + "a"
        macos_keyboard.key_up("Y")    # "a" + "shift"
        mock_quartz.CGEventCreateKeyboardEvent.assert_has_calls([
            call(None, 0x38, True),
            call(None, 0x10, True),
            call(None, 0x10, False),
            call(None, 0x38, False),
        ])
        assert mock_quartz.CGEventPost.call_count == 4
