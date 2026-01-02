"""Tests for X11 Display Server Part providing keyboard functions.

Tests the X11KeyboardPart implementation which handles:
- Key press/release via XTest extension
- Layout detection via Xlib
- Key mapping verification

All tests use mocked Xlib (no real X11 server required).
"""

from unittest.mock import MagicMock, call, patch

import pytest

from pyautogui2.controllers.keyboard import KeyboardController as KC
from pyautogui2.utils.exceptions import PyAutoGUIException


class TestX11KeyboardPartSetupPostinit:
    """Tests for X11 setup_postinit() functions."""

    def test_setup_postinit_without_display_raise(self, linux_ds_x11_keyboard):
        """setup_postinit() calls without display should raise PyAutoGUIException."""
        linux_ds_x11_keyboard._xlib.display.Display = lambda *_a, **_kw: None
        with pytest.raises(PyAutoGUIException, match="Error: Cannot obtain Display"):
            kwargs = {
                "key_names": KC.KEY_NAMES,
                "all_keymapping": KC.KEYBOARD_MAPPINGS,
            }
            linux_ds_x11_keyboard.setup_postinit(**kwargs)

    def test_setup_postinit_without_key_names_raise(self, linux_ds_x11_keyboard):
        """setup_postinit() calls without key_names should raise ValueError."""
        with pytest.raises(ValueError, match="key_names list is required"):
            kwargs = {
                "key_names": None,
                "all_keymapping": KC.KEYBOARD_MAPPINGS,
            }
            linux_ds_x11_keyboard.setup_postinit(**kwargs)

    def test_setup_postinit_without_all_keymapping_raise(self, linux_ds_x11_keyboard):
        """setup_postinit() calls without all_keymapping should raise ValueError."""
        with pytest.raises(ValueError, match="all_keymapping dict is required"):
            kwargs = {
                "key_names": KC.KEY_NAMES,
                "all_keymapping": None,
            }
            linux_ds_x11_keyboard.setup_postinit(**kwargs)

    def test_setup_postinit_non_qwerty_xkb_raises(self, linux_ds_x11_keyboard):
        """setup_postinit() raises if XKB keycodes are not in ascending QWERTY order."""
        counter = {"val": 200}

        def descending_keycode(*_args, **_kwargs):
            counter["val"] -= 1
            return counter["val"]

        # Need a valid display and layout
        mock_display = MagicMock()
        mock_display.keysym_to_keycode = MagicMock(side_effect=descending_keycode)
        linux_ds_x11_keyboard._xlib.display.Display = MagicMock(return_value=mock_display)

        with patch.object(linux_ds_x11_keyboard, "get_layout", return_value="QWERTY"), \
             pytest.raises(PyAutoGUIException, match="XKB lib probably not configured in QWERTY"):
            linux_ds_x11_keyboard.setup_postinit(
                key_names=KC.KEY_NAMES,
                all_keymapping=KC.KEYBOARD_MAPPINGS,
            )

    def test_setup_postinit_non_qwerty_layout_warns(self, linux_ds_x11_keyboard, caplog):
        """setup_postinit() logs warning for non-QWERTY detected layout."""
        import logging

        mock_display = MagicMock()
        mock_display.keysym_to_keycode = MagicMock(return_value=42)
        linux_ds_x11_keyboard._xlib.display.Display = MagicMock(return_value=mock_display)

        with patch.object(linux_ds_x11_keyboard, "get_layout", return_value="AZERTY"):
            linux_ds_x11_keyboard.setup_postinit(
                key_names=KC.KEY_NAMES,
                all_keymapping=KC.KEYBOARD_MAPPINGS,
            )

        warnings = [x.message for x in caplog.get_records("call") if x.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert "Detected keyboard layout 'AZERTY'. Only QWERTY layouts are officially supported under X11." in warnings[0]

    def test_setup_postinit_layout_not_in_keymapping_raises(self, linux_ds_x11_keyboard):
        """setup_postinit() raises if detected layout not in all_keymapping keys."""
        mock_display = MagicMock()
        mock_display.keysym_to_keycode = MagicMock(return_value=42)
        linux_ds_x11_keyboard._xlib.display.Display = MagicMock(return_value=mock_display)

        with patch.object(linux_ds_x11_keyboard, "get_layout", return_value="DVORAK"), \
             pytest.raises(PyAutoGUIException, match="unsupported layout 'DVORAK'"):
            linux_ds_x11_keyboard.setup_postinit(
                key_names=KC.KEY_NAMES,
                all_keymapping=KC.KEYBOARD_MAPPINGS,
            )

    def test_setup_postinit_no_shift_keycode_raises(self, linux_ds_x11_keyboard):
        """setup_postinit() raises if Shift_L has no keycode."""
        mock_display = MagicMock()
        mock_display.keysym_to_keycode = MagicMock(return_value=42)
        linux_ds_x11_keyboard._xlib.display.Display = MagicMock(return_value=mock_display)
        linux_ds_x11_keyboard._xlib.XK.string_to_keysym = MagicMock(return_value=0)

        with patch.object(linux_ds_x11_keyboard, "get_layout", return_value="QWERTY"), \
             pytest.raises(PyAutoGUIException, match="no keycode found for Shift_L"):
            linux_ds_x11_keyboard.setup_postinit(
                key_names=KC.KEY_NAMES,
                all_keymapping=KC.KEYBOARD_MAPPINGS,
            )


class TestX11KeyboardPartKeyDownUp:
    """Tests for X11 key_down() and key_up() functions."""

    def test_key_down_calls_xtest_fake_input(self, linux_ds_x11_keyboard):
        """key_down() calls Xlib fake_input with KeyPress event."""
        linux_ds_x11_keyboard.key_down("a")

        linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.assert_called()
        args = linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_args
        assert args[0][1] == linux_ds_x11_keyboard._xlib.X.KeyPress

    def test_key_up_calls_xtest_fake_input(self, linux_ds_x11_keyboard):
        """key_up() calls Xlib fake_input with KeyRelease event."""
        linux_ds_x11_keyboard.key_up("a")

        linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.assert_called()
        args = linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_args
        assert args[0][1] == linux_ds_x11_keyboard._xlib.X.KeyRelease

    def test_key_down_syncs_display(self, linux_ds_x11_keyboard):
        """key_down() calls display.sync() after sending event."""
        linux_ds_x11_keyboard.key_down("a")

        linux_ds_x11_keyboard._display.sync.assert_called()

    def test_key_up_syncs_display(self, linux_ds_x11_keyboard):
        """key_up() calls display.sync() after sending event."""
        linux_ds_x11_keyboard.key_up("a")

        linux_ds_x11_keyboard._display.sync.assert_called()

    def test_key_down_with_special_keys(self, linux_ds_x11_keyboard):
        """key_down() works with special keys (enter, escape, etc.)."""
        special_keys = ["enter", "escape"]

        for key in special_keys:
            linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.reset_mock()
            linux_ds_x11_keyboard._display.sync.reset_mock()

            linux_ds_x11_keyboard.key_down(key)

            assert linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_count == 1
            assert linux_ds_x11_keyboard._display.sync.call_count == 1

    def test_key_down_multiple_calls_are_independent(self, linux_ds_x11_keyboard):
        """Multiple key_down() calls don't interfere with each other."""
        linux_ds_x11_keyboard.key_down("a")
        linux_ds_x11_keyboard.key_down("b")
        linux_ds_x11_keyboard.key_down("c")

        assert linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_count == 3
        assert linux_ds_x11_keyboard._display.sync.call_count == 3

    def test_key_up_without_key_down_works(self, linux_ds_x11_keyboard):
        """key_up() works even without corresponding key_down()."""
        linux_ds_x11_keyboard.key_up("a")

        assert linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_count == 1
        assert linux_ds_x11_keyboard._display.sync.call_count == 1


class TestX11KeyboardPartKeyMapping:
    """Tests for X11 keyboard key mapping verification."""

    def test_key_is_mapped_returns_true_for_common_keys(self, linux_ds_x11_keyboard):
        """key_is_mapped() returns True for common ASCII keys."""
        common_keys = ["a", "b", "z", "0", "1", "9", " "]

        for key in common_keys:
            assert linux_ds_x11_keyboard.key_is_mapped(key) is True

    def test_key_is_mapped_returns_true_for_special_keys(self, linux_ds_x11_keyboard):
        """key_is_mapped() returns True for special keys."""
        special_keys = ["enter", "shift", "ctrl", "alt", "escape", "tab"]

        for key in special_keys:
            assert linux_ds_x11_keyboard.key_is_mapped(key) is True

    def test_key_is_mapped_returns_false_for_unmapped_keys(self, linux_ds_x11_keyboard):
        """key_is_mapped() returns False for keys not in _char_map."""
        unmapped_keys = ["🚀", "nonexistent_key"]

        for key in unmapped_keys:
            assert linux_ds_x11_keyboard.key_is_mapped(key) is False

    def test_key_is_mapped_case_sensitive(self, linux_ds_x11_keyboard):
        """key_is_mapped() is case-sensitive for letter keys."""
        assert linux_ds_x11_keyboard.key_is_mapped("a") is True
        assert linux_ds_x11_keyboard.key_is_mapped("A") is True
        assert linux_ds_x11_keyboard.key_is_mapped("z") is True
        assert linux_ds_x11_keyboard.key_is_mapped("Z") is True


class TestX11KeyboardPartLayoutDetection:
    """Tests for X11 keyboard layout detection."""

    def test_get_layout_returns_string(self, linux_ds_x11_keyboard):
        """get_layout() returns a string identifier."""
        layout = linux_ds_x11_keyboard.get_layout()

        assert isinstance(layout, str)
        assert len(layout) > 0

    def test_get_layout_detects_common_layouts(self, linux_ds_x11_keyboard):
        """get_layout() can detect common keyboard layouts."""
        layout = linux_ds_x11_keyboard.get_layout()

        assert layout == "QWERTY"

    def test_get_layout_consistent_across_calls(self, linux_ds_x11_keyboard):
        """get_layout() returns same value on multiple calls."""
        layout1 = linux_ds_x11_keyboard.get_layout()
        layout2 = linux_ds_x11_keyboard.get_layout()
        layout3 = linux_ds_x11_keyboard.get_layout()

        assert layout1 == layout2 == layout3

    def test_get_layout_uses_xlib_apis(self, linux_ds_x11_keyboard):
        """get_layout() uses Xlib APIs for layout detection."""
        layout = linux_ds_x11_keyboard.get_layout()

        assert linux_ds_x11_keyboard._display is not None
        assert isinstance(layout, str)

    def test_get_layout_unsupported_layout_raises(self, linux_ds_x11_keyboard):
        """get_layout() raises for layout absent from KEYBOARD_LAYOUTS."""
        with patch.object(
            linux_ds_x11_keyboard,
            "_detect_layout",
            return_value="klingon",
        ), pytest.raises(
            PyAutoGUIException,
            match="Layout 'klingon' is unsupported",
        ):
            linux_ds_x11_keyboard.get_layout()


class TestX11KeyboardPartErrorHandling:
    """Tests for X11 error handling."""

    def test_key_down_handles_xlib_error(self, linux_ds_x11_keyboard):
        """key_down() handles Xlib errors gracefully."""
        linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.side_effect = Exception("Xlib error")

        with pytest.raises(Exception, match="Xlib error"):
            linux_ds_x11_keyboard.key_down("a")

    def test_key_up_handles_xlib_error(self, linux_ds_x11_keyboard):
        """key_up() handles Xlib errors gracefully."""
        linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.side_effect = Exception("Xlib error")

        with pytest.raises(Exception, match="Xlib error"):
            linux_ds_x11_keyboard.key_up("a")

    def test_key_down_handles_invalid_keysym(self, linux_ds_x11_keyboard):
        """key_down() handles invalid keysym (keycode=0)."""
        linux_ds_x11_keyboard._xlib.XK.string_to_keysym = MagicMock(return_value=0)

        with pytest.raises(PyAutoGUIException):
            linux_ds_x11_keyboard.key_down("invalid_key")

    def test_get_layout_handles_detection_failure(self, linux_ds_x11_keyboard):
        """get_layout() handles layout detection failures."""
        layout = linux_ds_x11_keyboard.get_layout()
        assert isinstance(layout, str)


class TestX11KeyboardPartDetectLayoutSetxkbmap:
    """Tests for _detect_layout_setxkbmap() static method."""

    def test_setxkbmap_subprocess_failure_raises(self, linux_ds_x11_keyboard):
        """Raises PyAutoGUIException when setxkbmap command fails."""
        with patch(
            "pyautogui2.osal.linux.display_servers.x11.keyboard.subprocess.check_output",
            side_effect=Exception("command failed"),
        ), pytest.raises(PyAutoGUIException, match="setxkbmap cannot detect layout"):
            linux_ds_x11_keyboard._detect_layout_setxkbmap()

    def test_setxkbmap_parses_layout_correctly(self, linux_ds_x11_keyboard):
        """Returns parsed layout string from setxkbmap output."""
        fake_output = "rules:      evdev\nmodel:      pc105\nlayout:     fr\n"
        with patch(
            "pyautogui2.osal.linux.display_servers.x11.keyboard.subprocess.check_output",
            return_value=fake_output,
        ):
            result = linux_ds_x11_keyboard._detect_layout_setxkbmap()
            assert result == "fr"

    def test_setxkbmap_multi_layout_returns_first(self, linux_ds_x11_keyboard):
        """Returns first layout when multiple are configured (e.g. 'us,fr')."""
        fake_output = "rules:      evdev\nmodel:      pc105\nlayout:     us,fr\n"
        with patch(
            "pyautogui2.osal.linux.display_servers.x11.keyboard.subprocess.check_output",
            return_value=fake_output,
        ):
            result = linux_ds_x11_keyboard._detect_layout_setxkbmap()
            assert result == "us"

    def test_setxkbmap_no_layout_line_raises(self, linux_ds_x11_keyboard):
        """Raises PyAutoGUIException when output has no layout line."""
        fake_output = "rules:      evdev\nmodel:      pc105\n"
        with patch(
            "pyautogui2.osal.linux.display_servers.x11.keyboard.subprocess.check_output",
            return_value=fake_output,
        ), pytest.raises(PyAutoGUIException, match="Error: setxkbmap layout not found"):
            linux_ds_x11_keyboard._detect_layout_setxkbmap()


class TestX11KeyboardPartDetectLayout:
    """Tests for _detect_layout() method."""

    def test_detect_layout_success(self, linux_ds_x11_keyboard):
        """_detect_layout() success."""
        with patch.object(linux_ds_x11_keyboard, "_detect_layout_setxkbmap", return_value="us"):
            result = linux_ds_x11_keyboard._detect_layout()

        assert result == "us"

    def test_detect_layout_raise(self, linux_ds_x11_keyboard):
        """_detect_layout() should raise if no layout detected."""
        with patch.object(linux_ds_x11_keyboard, "_detect_layout_setxkbmap", return_value=None), \
             pytest.raises(PyAutoGUIException, match="Error: keyboard layout not found"):
            linux_ds_x11_keyboard._detect_layout()


class TestX11KeyboardPartEnsureSupportedLayout:
    """Tests for _ensure_supported_layout() guard."""

    def test_non_qwerty_layout_raises(self, linux_ds_x11_keyboard):
        """Raises PyAutoGUIException for non-QWERTY layouts."""
        linux_ds_x11_keyboard._layout = "AZERTY"

        with pytest.raises(PyAutoGUIException, match="Unsupported keyboard layout 'AZERTY'"):
            linux_ds_x11_keyboard._ensure_supported_layout()

    def test_qwerty_layout_passes(self, linux_ds_x11_keyboard):
        """No exception raised for QWERTY layout."""
        linux_ds_x11_keyboard._layout = "QWERTY"
        linux_ds_x11_keyboard._ensure_supported_layout()


class TestX11KeyboardPartGetKeycode:
    """Tests for _get_keycode() keysym resolution."""

    def test_unknown_keysym_returns_none(self, linux_ds_x11_keyboard):
        """Returns None when keysym string resolves to NoSymbol (0)."""
        linux_ds_x11_keyboard._xlib.XK.string_to_keysym = MagicMock(
            return_value=0
        )

        result = linux_ds_x11_keyboard._get_keycode("totally_bogus_key")
        assert result is None

    def test_unknown_keycode_returns_none(self, linux_ds_x11_keyboard):
        """Returns None when keysym_to_keycode resolves to NoKeycode (0)."""
        linux_ds_x11_keyboard._display.keysym_to_keycode = MagicMock(
            return_value=0
        )

        result = linux_ds_x11_keyboard._get_keycode("another_bogus_key")
        assert result is None

    def test_valid_keysym_returns_keycode(self, linux_ds_x11_keyboard):
        """Returns keycode integer for valid keysym."""
        linux_ds_x11_keyboard._xlib.XK.string_to_keysym = MagicMock(
            return_value=42
        )
        linux_ds_x11_keyboard._display.keysym_to_keycode = MagicMock(
            return_value=38
        )

        result = linux_ds_x11_keyboard._get_keycode("a")
        assert result == 38


class TestX11KeyboardPartEmitKey:
    """Tests for _emit_key() low-level event emission."""

    def test_invalid_event_type_raises_value_error(self, linux_ds_x11_keyboard):
        """Raises ValueError for event types other than KeyPress/KeyRelease."""
        with pytest.raises(ValueError, match="Invalid X11 event type"):
            linux_ds_x11_keyboard._emit_key("a", 999)

    def test_unmapped_key_raises(self, linux_ds_x11_keyboard):
        """Raises PyAutoGUIException for key absent from _char_map."""
        with pytest.raises(PyAutoGUIException, match="not implemented"):
            linux_ds_x11_keyboard._emit_key(
                "nonexistent_key_xyz",
                linux_ds_x11_keyboard._xlib.X.KeyPress,
            )

    def test_key_with_none_keycode_raises(self, linux_ds_x11_keyboard):
        """Raises PyAutoGUIException when key maps to None keycode."""
        linux_ds_x11_keyboard._char_map["ghost_key"] = (None, "")

        with pytest.raises(PyAutoGUIException, match="has not any keycode"):
            linux_ds_x11_keyboard._emit_key(
                "ghost_key",
                linux_ds_x11_keyboard._xlib.X.KeyPress,
            )

    def test_key_press_with_shift_emits_modifier_before_key(self, linux_ds_x11_keyboard):
        """KeyPress with shift presses modifier before the target key."""
        shift_kc = 50
        a_kc = 38
        linux_ds_x11_keyboard._char_map["A"] = (a_kc, "shift")
        linux_ds_x11_keyboard._mods_keycodes = (("shift", shift_kc),)
        linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.reset_mock()
        linux_ds_x11_keyboard._display.sync.reset_mock()

        linux_ds_x11_keyboard._emit_key(
            "A", linux_ds_x11_keyboard._xlib.X.KeyPress
        )

        calls = linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_args_list
        assert len(calls) == 2
        assert calls[0] == call(
            linux_ds_x11_keyboard._display,
            linux_ds_x11_keyboard._xlib.X.KeyPress,
            shift_kc,
        )
        assert calls[1] == call(
            linux_ds_x11_keyboard._display,
            linux_ds_x11_keyboard._xlib.X.KeyPress,
            a_kc,
        )

    def test_key_release_with_shift_releases_modifier_after_key(self, linux_ds_x11_keyboard):
        """KeyRelease with shift releases target key before modifier."""
        shift_kc = 50
        a_kc = 38
        linux_ds_x11_keyboard._char_map["A"] = (a_kc, "shift")
        linux_ds_x11_keyboard._mods_keycodes = (("shift", shift_kc),)
        linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.reset_mock()
        linux_ds_x11_keyboard._display.sync.reset_mock()

        linux_ds_x11_keyboard._emit_key(
            "A", linux_ds_x11_keyboard._xlib.X.KeyRelease
        )

        calls = linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_args_list
        assert len(calls) == 2
        assert calls[0] == call(
            linux_ds_x11_keyboard._display,
            linux_ds_x11_keyboard._xlib.X.KeyRelease,
            a_kc,
        )
        assert calls[1] == call(
            linux_ds_x11_keyboard._display,
            linux_ds_x11_keyboard._xlib.X.KeyRelease,
            shift_kc,
        )

    def test_key_without_modifier_emits_only_key(self, linux_ds_x11_keyboard):
        """Key with empty modifier string skips modifier handling."""
        a_kc = 38
        linux_ds_x11_keyboard._char_map["a"] = (a_kc, "")
        linux_ds_x11_keyboard._mods_keycodes = (("shift", 50),)
        linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.reset_mock()

        linux_ds_x11_keyboard._emit_key(
            "a", linux_ds_x11_keyboard._xlib.X.KeyPress
        )

        assert linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_count == 1

    def test_display_sync_called_after_emit(self, linux_ds_x11_keyboard):
        """Display sync is always called after event emission."""
        linux_ds_x11_keyboard._char_map["x"] = (38, "")
        linux_ds_x11_keyboard._display.sync.reset_mock()

        linux_ds_x11_keyboard._emit_key(
            "x", linux_ds_x11_keyboard._xlib.X.KeyPress
        )

        linux_ds_x11_keyboard._display.sync.assert_called_once()


class TestX11KeyboardPartGetKeysymName:
    """Tests for _get_keysym_name() static character translation."""

    @pytest.mark.parametrize(
        "char, expected",
        [
            ("@", "at"),
            ("+", "plus"),
            ("-", "minus"),
            ("*", "asterisk"),
            ("/", "slash"),
            ("\\", "backslash"),
            (".", "period"),
            (",", "comma"),
            (";", "semicolon"),
            (":", "colon"),
            ("'", "apostrophe"),
            ('"', "quotedbl"),
            ("(", "parenleft"),
            (")", "parenright"),
            ("[", "bracketleft"),
            ("]", "bracketright"),
            ("{", "braceleft"),
            ("}", "braceright"),
            ("<", "less"),
            (">", "greater"),
            ("=", "equal"),
            ("?", "question"),
            ("!", "exclam"),
            ("`", "grave"),
            ("~", "asciitilde"),
            ("#", "numbersign"),
            ("$", "dollar"),
            ("%", "percent"),
            ("^", "asciicircum"),
            ("&", "ampersand"),
            ("_", "underscore"),
            ("|", "bar"),
            ("£", "sterling"),
            ("€", "EuroSign"),
            ("©", "copyright"),
            ("®", "registered"),
        ],
    )
    def test_special_character_translated(self, char, expected):
        """Each special character is translated to its X11 keysym name."""
        from pyautogui2.osal.linux.display_servers.x11.keyboard import X11KeyboardPart
        assert X11KeyboardPart._get_keysym_name(char) == expected

    @pytest.mark.parametrize("char", ["a", "Z", "5", "F1"])
    def test_regular_char_returned_unchanged(self, char):
        """Characters not in specials map are returned as-is."""
        from pyautogui2.osal.linux.display_servers.x11.keyboard import X11KeyboardPart
        assert X11KeyboardPart._get_keysym_name(char) == char


class TestX11KeyboardPartIntegration:
    """Integration tests for X11 keyboard operations."""

    def test_type_sequence_uses_key_down_and_key_up(self, linux_ds_x11_keyboard):
        """Typing a sequence calls key_down/key_up in correct order."""
        for char in "abc":
            linux_ds_x11_keyboard.key_down(char)
            linux_ds_x11_keyboard.key_up(char)

        assert linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_count == 6
        assert linux_ds_x11_keyboard._display.sync.call_count == 6

    def test_modifier_key_combo(self, linux_ds_x11_keyboard):
        """Modifier combinations work correctly (Ctrl+C)."""
        linux_ds_x11_keyboard.key_down("ctrl")
        linux_ds_x11_keyboard.key_down("c")
        linux_ds_x11_keyboard.key_up("c")
        linux_ds_x11_keyboard.key_up("ctrl")

        assert linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_count == 4

        calls = linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_args_list
        assert calls[0][0][1] == linux_ds_x11_keyboard._xlib.X.KeyPress  # Ctrl down
        assert calls[1][0][1] == linux_ds_x11_keyboard._xlib.X.KeyPress  # C down
        assert calls[2][0][1] == linux_ds_x11_keyboard._xlib.X.KeyRelease  # C up
        assert calls[3][0][1] == linux_ds_x11_keyboard._xlib.X.KeyRelease  # Ctrl up

    def test_all_printable_ascii_keys_are_mapped(self, linux_ds_x11_keyboard):
        """All printable ASCII characters should be mappable."""
        import string

        unmapped = []
        for char in string.printable:
            if not linux_ds_x11_keyboard.key_is_mapped(char):
                unmapped.append(char)

        mapped_ratio = 1.0 - (len(unmapped) / len(string.printable))
        assert mapped_ratio >= 0.9, f"Too many unmapped chars: {unmapped}"

    def test_rapid_key_presses_dont_interfere(self, linux_ds_x11_keyboard):
        """Rapid key presses are handled independently."""
        for _ in range(10):
            linux_ds_x11_keyboard.key_down("a")
            linux_ds_x11_keyboard.key_up("a")

        assert linux_ds_x11_keyboard._xlib.ext.xtest.fake_input.call_count == 20
        assert linux_ds_x11_keyboard._display.sync.call_count == 20
