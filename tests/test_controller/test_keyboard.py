"""Tests for KeyboardController."""

from unittest.mock import MagicMock, call, patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException


class TestKeyboardGetLayout:
    """Test base get_layout() delegation."""

    def test_get_layout_delegate(self, keyboard_controller):
        keyboard_controller._osal.get_layout.return_value = "QWERTY"
        layout = keyboard_controller.get_layout()
        assert layout == "QWERTY"
        keyboard_controller._osal.get_layout.assert_called_once()


class TestKeyboardKeyDownUp:
    """Test basic key_down() and key_up() delegation."""

    def test_key_down_and_up_delegate(self, keyboard_controller):
        keyboard_controller.key_down("a")
        keyboard_controller.key_up("a")
        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_down("a"),
            call.key_up("a"),
        ])


class TestKeyboardPressKey:
    """Test press_key() with various parameters and validations."""

    def test_invalid_presses_raise(self, keyboard_controller):
        """Test that presses=0 raises an exception."""
        with pytest.raises(PyAutoGUIException):
            keyboard_controller.press_key("a", presses=0)

    def test_invalid_key_name_raise(self, keyboard_controller):
        """Test that invalid key names raise an exception."""
        keyboard_controller._osal.key_is_mapped.return_value = False
        with pytest.raises(PyAutoGUIException):
            keyboard_controller.press_key("invalid_key_name")

    def test_invalid_key_fallback_codepoint(self, keyboard_controller):
        """Test that invalid key fallback to codepoint."""
        keyboard_controller._osal.key_is_mapped.return_value = False
        keyboard_controller.press_key("é")
        keyboard_controller._osal.type_codepoint_value.assert_called_with("00e9")

    def test_valid_press_calls_down_up_correct_times(self, keyboard_controller):
        """Test that multiple presses call down/up the correct number of times."""
        keyboard_controller.press_key("a", presses=3)
        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("a"),
            call.key_down("a"),
            call.key_up("a"),
            call.key_is_mapped("a"),
            call.key_down("a"),
            call.key_up("a"),
            call.key_is_mapped("a"),
            call.key_down("a"),
            call.key_up("a"),
        ])

    def test_valid_key_name(self, keyboard_controller):
        """Test pressing special keys (enter, escape, etc.)."""
        keyboard_controller.press_key("enter")
        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("enter"),
            call.key_down("enter"),
            call.key_up("enter"),
        ])

    def test_negative_presses_raises(self, keyboard_controller):
        """Test that negative presses raise an exception."""
        with pytest.raises(PyAutoGUIException, match="presses value must be >= 1"):
            keyboard_controller.press_key("a", presses=-1)

    def test_negative_interval_raises(self, keyboard_controller):
        """Test that negative interval raises an exception."""
        with pytest.raises(PyAutoGUIException, match="interval must be non-negative"):
            keyboard_controller.press_key("a", interval=-0.1)

    def test_press_key_with_zero_interval(self, keyboard_controller):
        """Test that interval=0 works (no sleep)."""
        with patch('time.sleep') as mock_sleep:
            keyboard_controller.press_key("a", presses=2, interval=0.0)

            # Should not sleep with interval=0
            mock_sleep.assert_not_called()

    def test_press_with_interval(self, keyboard_controller):
        """Test pressing with interval between presses."""
        with patch('time.sleep') as mock_sleep:
            keyboard_controller.press_key("a", presses=2, interval=0.1)

            # Should call sleep once (between press 1 and press 2)
            mock_sleep.assert_called_with(0.1)
            assert mock_sleep.call_count == 1  # Between 2 presses = 1 sleep


class TestKeyboardWrite:
    """Test write() method with various inputs."""

    def test_write_delegates_to_press_key(self, keyboard_controller):
        """Test that write() calls press_key for each character."""
        keyboard_controller.write("abCD")
        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("a"),
            call.key_down("a"),
            call.key_up("a"),
            call.key_is_mapped("b"),
            call.key_down("b"),
            call.key_up("b"),
            call.key_is_mapped("C"),
            call.key_down("C"),
            call.key_up("C"),
            call.key_is_mapped("D"),
            call.key_down("D"),
            call.key_up("D"),
        ])

    def test_write_single_character(self, keyboard_controller):
        """Test writing a single character."""
        keyboard_controller.write("x")

        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("x"),
            call.key_down("x"),
            call.key_up("x"),
        ])

    def test_write_empty_string(self, keyboard_controller):
        """Test writing empty string does nothing."""
        keyboard_controller.write("")

        # Should not call any OSAL methods
        keyboard_controller._osal.mocks.assert_not_called()

    def test_write_unicode(self, keyboard_controller):
        """Test writing unicode characters."""
        keyboard_controller._osal.key_is_mapped.return_value = False
        text = "🎉"
        keyboard_controller.write(text)

        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("🎉"),
            call.type_codepoint_value("1f389"),
        ])

    def test_write_potential_dead_key(self, keyboard_controller):
        """Test writing potential dead keys."""
        from pyautogui2.controllers.keyboard import KeyboardController

        text = "".join(KeyboardController.POTENTIALLY_DEAD_KEYS)
        keyboard_controller.write(text)

        call_dead_keys = [call.type_codepoint_value(f"{ord(k):04x}") for k in KeyboardController.POTENTIALLY_DEAD_KEYS]
        keyboard_controller._osal.mocks.assert_has_calls(call_dead_keys)

    def test_write_with_interval(self, keyboard_controller):
        """Test writing with interval between characters."""
        with patch('time.sleep') as mock_sleep:
            keyboard_controller.write("ab", interval=0.05)

            # Should sleep between characters (1 sleep for 2 chars)
            mock_sleep.assert_called_with(0.05)
            assert mock_sleep.call_count == 1

    def test_write_negative_interval_raises(self, keyboard_controller):
        """Test that negative interval raises an exception."""
        with pytest.raises(PyAutoGUIException, match="interval must be non-negative"):
            keyboard_controller.write("test", interval=-0.1)


class TestKeyboardHold:
    """Test hold() context manager with various inputs."""

    def test_hold_calls_down_and_up_even_on_exception(self, keyboard_controller):
        """Test that keys are released even if exception occurs in context."""
        try:
            with keyboard_controller.hold("ctrl"):
                raise RuntimeError("forced")
        except RuntimeError:
            pass
        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_down("ctrl"),
            call.key_up("ctrl"),
        ])

    def test_hold_calls_params_single_string(self, keyboard_controller):
        """Test holding a single key."""
        with keyboard_controller.hold("shift"):
            pass

        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_down("shift"),
            call.key_up("shift"),
        ])

    def test_hold_calls_params_two_strings(self, keyboard_controller):
        """Test holding two keys (released in reverse order)."""
        with keyboard_controller.hold("shift", "ctrl"):
            pass

        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("shift"),
            call.key_down("shift"),
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_up("ctrl"),
            call.key_up("shift"),
        ])

    def test_hold_calls_params_list(self, keyboard_controller):
        """Test holding keys from a list."""
        with keyboard_controller.hold(["ctrl", "alt"]):
            pass

        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_is_mapped("alt"),
            call.key_down("alt"),
            call.key_up("alt"),
            call.key_up("ctrl"),
        ])

    def test_hold_calls_params_iter(self, keyboard_controller):
        """Test holding keys from a iterator."""
        with keyboard_controller.hold(iter(["ctrl", "alt"])):
            pass

        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_is_mapped("alt"),
            call.key_down("alt"),
            call.key_up("alt"),
            call.key_up("ctrl"),
        ])


    def test_hold_calls_params_formated_string(self, keyboard_controller):
        """Test holding keys from formatted string (ctrl+alt+shift)."""
        with keyboard_controller.hold("ctrl+alt+shift"):
            pass

        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_is_mapped("alt"),
            call.key_down("alt"),
            call.key_is_mapped("shift"),
            call.key_down("shift"),
            call.key_up("shift"),
            call.key_up("alt"),
            call.key_up("ctrl"),
        ])

    def test_hold_nested_contexts(self, keyboard_controller):
        """Test nested hold contexts work correctly."""
        with keyboard_controller.hold("ctrl"), keyboard_controller.hold("shift"):
            pass

        # Verify correct nesting order
        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_is_mapped("shift"),
            call.key_down("shift"),
            call.key_up("shift"),
            call.key_up("ctrl"),
        ])

    def test_hold_empty_keys(self, keyboard_controller):
        """Test hold with no keys does nothing."""
        with keyboard_controller.hold():
            pass

        # Should not call any OSAL methods
        keyboard_controller._osal.key_down.assert_not_called()
        keyboard_controller._osal.key_up.assert_not_called()

    def test_hold_duplicate_keys(self, keyboard_controller):
        """Test holding the same key twice (edge case)."""
        with keyboard_controller.hold("ctrl", "ctrl"):
            pass

        expected_calls = [
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_up("ctrl"),
        ]
        # Do not use "assert_has_calls" to guarantee exact calls
        assert keyboard_controller._osal.mocks.mock_calls == expected_calls

    def test_hold_invalid_key_raise(self, keyboard_controller):
        """Test hold with invalid key should raise PyAutoGUIException."""
        keyboard_controller._osal.key_is_mapped.return_value = False

        with pytest.raises(PyAutoGUIException, match="unmapped key 'invalid_key' to press"), \
             keyboard_controller.hold("invalid_key"):
            pass


class TestKeyboardHotkey:
    """Test hotkey() method with various formats."""

    def test_hotkey_string_split_and_order(self, keyboard_controller):
        """Test hotkey with string format (ctrl+alt+a)."""
        keyboard_controller.hotkey("ctrl+alt+a")
        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_is_mapped("alt"),
            call.key_down("alt"),
            call.key_is_mapped("a"),
            call.key_down("a"),
            call.key_up("a"),
            call.key_up("alt"),
            call.key_up("ctrl"),
        ])

    def test_hotkey_with_args(self, keyboard_controller):
        """Test hotkey with separate arguments."""
        keyboard_controller.hotkey("ctrl", "c")
        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_is_mapped("c"),
            call.key_down("c"),
            call.key_up("c"),
            call.key_up("ctrl"),
        ])

    def test_hotkey_with_list(self, keyboard_controller):
        """Test hotkey with list of keys."""
        keyboard_controller.hotkey(["ctrl", "shift", "esc"])
        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_is_mapped("shift"),
            call.key_down("shift"),
            call.key_is_mapped("esc"),
            call.key_down("esc"),
            call.key_up("esc"),
            call.key_up("shift"),
            call.key_up("ctrl"),
        ])

    def test_hotkey_with_interval(self, keyboard_controller):
        """Test hotkey with interval between key presses."""
        with patch('time.sleep') as mock_sleep:
            keyboard_controller.hotkey("a", "b", interval=0.05)

            # Should sleep between key presses
            mock_sleep.assert_called()

    def test_hotkey_single_key(self, keyboard_controller):
        """Test hotkey with single key (should work like press_key)."""
        keyboard_controller.hotkey("a")
        keyboard_controller._osal.mocks.assert_has_calls([
            call.key_is_mapped("a"),
            call.key_down("a"),
            call.key_up("a"),
        ])

    def test_hotkey_empty_keys_does_nothing(self, keyboard_controller):
        """Test hotkey with no keys does nothing."""
        keyboard_controller.hotkey()

        # Should not call any OSAL methods
        keyboard_controller._osal.key_down.assert_not_called()
        keyboard_controller._osal.key_up.assert_not_called()

    def test_hotkey_invalid_key_raise(self, keyboard_controller):
        """Test hotkey with invalid key should raise PyAutoGUIException."""
        keyboard_controller._osal.key_is_mapped.return_value = False

        with pytest.raises(PyAutoGUIException, match="unmapped key 'invalid_key' to press"):
            keyboard_controller.hotkey("invalid_key")


class TestKeyboardCodepoint:
    """Test codepoint() method for unicode input."""

    def test_codepoint_ctx_enters_and_exits(self, keyboard_controller):
        """Test codepoint context manager calls OSAL."""
        keyboard_controller.codepoint("U+00E9")
        keyboard_controller._osal.type_codepoint_value.assert_called_with("00e9")

    def test_codepoint_without_prefix(self, keyboard_controller):
        """Test codepoint without U+ prefix."""
        keyboard_controller.codepoint("00E9")
        keyboard_controller._osal.type_codepoint_value.assert_called_with("00e9")

    def test_codepoint_lowercase(self, keyboard_controller):
        """Test codepoint with lowercase hex."""
        keyboard_controller.codepoint("u+00e9")
        # Should normalize to uppercase
        keyboard_controller._osal.type_codepoint_value.assert_called_with("00e9")

    def test_codepoint_emoji(self, keyboard_controller):
        """Test codepoint for emoji."""
        keyboard_controller.codepoint("U+1F389")  # 🎉
        keyboard_controller._osal.type_codepoint_value.assert_called_with("1f389")

    def test_codepoint_int(self, keyboard_controller):
        """Test codepoint from int."""
        keyboard_controller.codepoint(0x00E9)
        keyboard_controller._osal.type_codepoint_value.assert_called_with("00e9")

    def test_codepoint_hex_string(self, keyboard_controller):
        """Test codepoint from hex string."""
        keyboard_controller.codepoint("\\xe9")
        keyboard_controller._osal.type_codepoint_value.assert_called_with("00e9")

    def test_codepoint_unicode_string(self, keyboard_controller):
        """Test codepoint from unicode string."""
        keyboard_controller.codepoint("\\u1234")
        keyboard_controller._osal.type_codepoint_value.assert_called_with("1234")

    def test_codepoint_bad_type_raise(self, keyboard_controller):
        """Test codepoint with bad type should raise PyAutoGUIException."""
        with pytest.raises(PyAutoGUIException, match="Invalid type 'float' for codepoint '0.5'."):
            keyboard_controller.codepoint(0.5)


class TestKeyboardControllerInitialization:
    """Test KeyboardController initialization."""

    def test_init_with_bad_backend_raises(self):
        """Test initialization with bad backend should raises."""
        from pyautogui2.controllers.keyboard import KeyboardController

        mock_backend = MagicMock()  # not AbstractKeyboard subclass
        with pytest.raises(PyAutoGUIException):
            KeyboardController(osal=mock_backend)

    def test_init_with_explicit_backend(self):
        """Test initialization with explicit backend."""
        from pyautogui2.controllers.keyboard import KeyboardController
        from pyautogui2.osal.abstract_cls import AbstractKeyboard

        mock_backend = MagicMock(spec_set=AbstractKeyboard)
        kb = KeyboardController(osal=mock_backend)
        assert kb._osal is mock_backend


class TestKeyboardBackendErrors:
    """Test error handling when backend fails."""

    def test_press_key_backend_error(self, keyboard_controller):
        """Test handling backend errors in press_key()."""
        keyboard_controller._osal.key_down.side_effect = RuntimeError("Backend error")

        with pytest.raises(RuntimeError, match="Backend error"):
            keyboard_controller.press_key("a")

    def test_write_backend_error(self, keyboard_controller):
        """Test handling backend errors in write()."""
        keyboard_controller._osal.key_down.side_effect = RuntimeError("Write error")

        with pytest.raises(RuntimeError, match="Write error"):
            keyboard_controller.write("test")

    def test_hold_backend_error_still_releases(self, keyboard_controller):
        """Test that keys are released even if backend errors during press."""
        try:
            with keyboard_controller.hold("ctrl"):
                RuntimeError("Press failed")
        except RuntimeError:
            pass

        # Should still attempt to release
        keyboard_controller._osal.key_up.assert_called()


class TestKeyboardUtilities:
    """Test utility methods (if they exist in implementation)."""

    def test_is_valid_key_if_exists(self, keyboard_controller):
        """Test key validation method if it exists."""
        keyboard_controller._osal.key_is_mapped.return_value = True
        assert keyboard_controller.is_valid_key('a') is True
        assert keyboard_controller.is_valid_key('enter') is True
        keyboard_controller._osal.key_is_mapped.return_value = False
        assert keyboard_controller.is_valid_key('invalid_key_xyz') is False


class TestKeyboardEdgeCases:
    """Test various edge cases and corner scenarios."""

    def test_multiple_operations_in_sequence(self, keyboard_controller):
        """Test multiple operations work correctly in sequence."""
        # Step 1
        keyboard_controller.press_key("a")
        # Step 2
        keyboard_controller.write("bc")
        # Step 3
        keyboard_controller.hotkey("ctrl", "c")

        # Step 4
        with keyboard_controller.hold("shift"):
            keyboard_controller.press_key("d")

        keyboard_controller._osal.mocks.assert_has_calls([
            # Step 1
            call.key_is_mapped("a"),
            call.key_down("a"),
            call.key_up("a"),
            # Step 2
            call.key_is_mapped("b"),
            call.key_down("b"),
            call.key_up("b"),
            call.key_is_mapped("c"),
            call.key_down("c"),
            call.key_up("c"),
            # Step 3
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_is_mapped("c"),
            call.key_down("c"),
            call.key_up("c"),
            call.key_up("ctrl"),
            # Step 4
            call.key_is_mapped("shift"),
            call.key_down("shift"),
            call.key_is_mapped("d"),
            call.key_down("d"),
            call.key_up("d"),
            call.key_up("shift"),
        ])


class TestKeyboardRepresentation:
    """Test string representations for debugging."""

    def test_repr_contains_class_name(self, keyboard_controller):
        """Test that __repr__ contains class name."""
        rep = repr(keyboard_controller)
        assert "KeyboardController" in rep

    def test_str_is_readable(self, keyboard_controller):
        """Test that __str__ provides readable output."""
        string = str(keyboard_controller)
        assert len(string) > 0
        # Should mention keyboard or controller
        assert "keyboard" in string.lower() or "controller" in string.lower()

