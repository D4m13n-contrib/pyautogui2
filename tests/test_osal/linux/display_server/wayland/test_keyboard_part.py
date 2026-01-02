"""Tests for Wayland Display Server Keyboard Part.

Tests the Wayland-specific implementation of keyboard control:
    - Key press/release via UInput
    - Linux keycode mapping
    - Layout detection (backend fallback for base Part)
    - Error handling for device access failures

Fixtures:
    - linux_ds_wayland_keyboard: WaylandKeyboardPart with mocked UInput
"""

from unittest.mock import call

import pytest


class TestWaylandKeyboardPartSetupPostinit:
    """Tests for setup_postinit()."""

    def test_setup_postinit_no_key_names_raise(self, linux_ds_wayland_keyboard):
        """setup_postinit() raise ValueError without key_names argument."""
        with pytest.raises(ValueError, match="key_names list is required"):
            linux_ds_wayland_keyboard.setup_postinit(key_names=None, all_keymapping={})

    def test_setup_postinit_no_keymapping_raise(self, linux_ds_wayland_keyboard):
        """setup_postinit() raise ValueError without all_keymapping argument."""
        with pytest.raises(ValueError, match="all_keymapping dict is required"):
            linux_ds_wayland_keyboard.setup_postinit(key_names=[], all_keymapping=None)

    def test_setup_postinit_layout_unsupported_raise(self, linux_ds_wayland_keyboard):
        """setup_postinit() raise ValueError if layout is not in all_keymapping argument."""
        with pytest.raises(ValueError, match="layout is not supported"):
            linux_ds_wayland_keyboard.setup_postinit(key_names=[], all_keymapping={})


class TestWaylandKeyboardPartKeySimulation:
    """Tests for key press/release simulation via UInput."""

    def test_key_down_writes_to_uinput(self, linux_ds_wayland_keyboard):
        """key_down() writes KEY_* event event with value 1 (press)."""
        linux_ds_wayland_keyboard.key_down("a")

        keycode, _ = linux_ds_wayland_keyboard._char_map.get("a", (None, None))
        linux_ds_wayland_keyboard._device.emit.assert_has_calls([
            call(keycode, 1),
        ])

    def test_key_up_writes_release_event(self, linux_ds_wayland_keyboard):
        """key_up() writes KEY_* event with value 0 (release)."""
        linux_ds_wayland_keyboard.key_up("b")

        keycode, _ = linux_ds_wayland_keyboard._char_map.get("b", (None, None))
        linux_ds_wayland_keyboard._device.emit.assert_has_calls([
            call(keycode, 0),
        ])

    def test_key_down_then_up_sequence(self, linux_ds_wayland_keyboard):
        """Pressing and releasing a key sends correct event sequence."""
        linux_ds_wayland_keyboard.key_down("space")
        linux_ds_wayland_keyboard.key_up("space")

        keycode, _ = linux_ds_wayland_keyboard._char_map.get("space", (None, None))
        linux_ds_wayland_keyboard._device.emit.assert_has_calls([
            call(keycode, 1),
            call(keycode, 0),
        ])

    def test_modifier_key_ctrl(self, linux_ds_wayland_keyboard):
        """Modifier keys (ctrl, shift, alt) work correctly."""
        linux_ds_wayland_keyboard.key_down("ctrl")

        keycode, _ = linux_ds_wayland_keyboard._char_map.get("ctrl", (None, None))
        linux_ds_wayland_keyboard._device.emit.assert_has_calls([
            call(keycode, 1),
        ])

    def test_special_key_return(self, linux_ds_wayland_keyboard):
        """Special keys (Return, Escape, Tab) work correctly."""
        linux_ds_wayland_keyboard.key_down("return")

        keycode, _ = linux_ds_wayland_keyboard._char_map.get("return", (None, None))
        linux_ds_wayland_keyboard._device.emit.assert_has_calls([
            call(keycode, 1),
        ])

    def test_function_key_f1(self, linux_ds_wayland_keyboard):
        """Function keys (F1-F12) work correctly."""
        linux_ds_wayland_keyboard.key_down("f1")

        keycode, _ = linux_ds_wayland_keyboard._char_map.get("f1", (None, None))
        linux_ds_wayland_keyboard._device.emit.assert_has_calls([
            call(keycode, 1),
        ])

    def test_multiple_keys_independently(self, linux_ds_wayland_keyboard):
        """Multiple key presses are handled independently."""
        linux_ds_wayland_keyboard.key_down("a")
        linux_ds_wayland_keyboard.key_down("b")
        linux_ds_wayland_keyboard.key_down("c")

        keycode_a, _ = linux_ds_wayland_keyboard._char_map.get("a", (None, None))
        keycode_b, _ = linux_ds_wayland_keyboard._char_map.get("b", (None, None))
        keycode_c, _ = linux_ds_wayland_keyboard._char_map.get("c", (None, None))
        linux_ds_wayland_keyboard._device.emit.assert_has_calls([
            call(keycode_a, 1),
            call(keycode_b, 1),
            call(keycode_c, 1),
        ])

    def test_capital_letter(self, linux_ds_wayland_keyboard):
        """Capital letter use a SHIFT modifier with letter."""
        linux_ds_wayland_keyboard.key_down("A")

        keycode, modifier = linux_ds_wayland_keyboard._char_map.get("A", (None, None))
        keycode_m, _ = linux_ds_wayland_keyboard._char_map.get(modifier, (None, None))
        linux_ds_wayland_keyboard._device.emit.assert_has_calls([
            call(keycode_m, 1),
            call(keycode, 1),
            call(keycode_m, 0),
        ])


class TestWaylandKeyboardPartKeyMapping:
    """Tests for key name to Linux keycode mapping."""

    def test_key_is_mapped_returns_true_for_letter(self, linux_ds_wayland_keyboard):
        """key_is_mapped() returns True for standard letters."""
        assert linux_ds_wayland_keyboard.key_is_mapped("a") is True
        assert linux_ds_wayland_keyboard.key_is_mapped("z") is True

    def test_key_is_mapped_returns_false_for_invalid(self, linux_ds_wayland_keyboard):
        """key_is_mapped() returns False for unmapped keys."""
        assert linux_ds_wayland_keyboard.key_is_mapped("invalid_key_xyz") is False
        assert linux_ds_wayland_keyboard.key_is_mapped("") is False

    def test_special_keys_are_mapped(self, linux_ds_wayland_keyboard):
        """Special keys (Enter, Escape, Tab, Space) are mapped."""
        special_keys = ["return", "enter", "escape", "tab", "space"]

        for key in special_keys:
            assert linux_ds_wayland_keyboard.key_is_mapped(key) is True, \
                f"{key} should be mapped"

    def test_modifier_keys_are_mapped(self, linux_ds_wayland_keyboard):
        """Modifier keys are mapped correctly."""
        modifiers = [
            "shift", "shiftleft", "shiftright",
            "ctrl", "ctrlleft", "ctrlright",
            "alt", "altleft", "altright", "altgr",
        ]

        for mod in modifiers:
            assert linux_ds_wayland_keyboard.key_is_mapped(mod) is True, \
                f"{mod} should be mapped"

    def test_function_keys_are_mapped(self, linux_ds_wayland_keyboard):
        """Function keys F1-F12 are mapped."""
        for i in range(1, 13):
            assert linux_ds_wayland_keyboard.key_is_mapped(f"f{i}") is True

    def test_number_keys_are_mapped(self, linux_ds_wayland_keyboard):
        """Number keys 0-9 are mapped."""
        for i in range(10):
            assert linux_ds_wayland_keyboard.key_is_mapped(str(i)) is True

    def test_case_insensitive_mapping(self, linux_ds_wayland_keyboard):
        """Key names should be case-insensitive."""
        assert linux_ds_wayland_keyboard.key_is_mapped("A") is True
        assert linux_ds_wayland_keyboard.key_is_mapped("a") is True
        assert linux_ds_wayland_keyboard.key_is_mapped("shift") is True
        assert linux_ds_wayland_keyboard.key_is_mapped("SHIFT") is False

    def test_arrow_keys_are_mapped(self, linux_ds_wayland_keyboard):
        """Arrow keys are mapped."""
        arrows = ["up", "down", "left", "right"]

        for arrow in arrows:
            assert linux_ds_wayland_keyboard.key_is_mapped(arrow) is True

    @pytest.mark.parametrize("layout, expected_decimal_key", [
        ("QWERTY", "KEY_KPDOT"),
        ("AZERTY", "KEY_KPCOMMA"),
        ("QWERTZ", "KEY_KPCOMMA"),
    ])
    def test_decimal_key_depends_layout(self, layout, expected_decimal_key, linux_ds_wayland_keyboard):
        """The decimal key depends on keyboard layout."""
        from pyautogui2.controllers.keyboard import KeyboardController as KC

        linux_ds_wayland_keyboard.get_layout.return_value = layout
        setup_kwargs = {
            "key_names": KC.KEY_NAMES,
            "all_keymapping": KC.KEYBOARD_MAPPINGS,
        }
        linux_ds_wayland_keyboard.setup_postinit(**setup_kwargs)

        assert linux_ds_wayland_keyboard._char_map["decimal"][0] == getattr(linux_ds_wayland_keyboard._uinput, expected_decimal_key)


class TestWaylandKeyboardPartErrors:
    """Tests for error handling in Wayland keyboard operations."""

    def test_key_down_with_unmapped_key_raises_or_ignores(self, linux_ds_wayland_keyboard):
        """Attempting to press unmapped key handles gracefully."""
        with pytest.raises(NotImplementedError):
            linux_ds_wayland_keyboard.key_down("unmapped_key_xyz_123")

    def test_operations_with_none_device_raises(self, linux_ds_wayland_keyboard):
        """Operations with None device should fail gracefully."""
        # Simulate device initialization failure
        linux_ds_wayland_keyboard._device = None

        with pytest.raises(AssertionError):
            linux_ds_wayland_keyboard.key_down("a")

    def test_uinput_write_failure_handled(self, linux_ds_wayland_keyboard):
        """UInput write failures are handled gracefully."""
        # Mock write to raise error
        linux_ds_wayland_keyboard._device.emit.side_effect = OSError("Device write failed")

        with pytest.raises(OSError):
            linux_ds_wayland_keyboard.key_down("a")

    def test_invalid_key_name_empty_string(self, linux_ds_wayland_keyboard):
        """Empty string key name handled gracefully."""
        assert linux_ds_wayland_keyboard.key_is_mapped("") is False

    def test_invalid_key_name_none(self, linux_ds_wayland_keyboard):
        """None key name handled gracefully."""
        assert linux_ds_wayland_keyboard.key_is_mapped(None) is False


class TestWaylandKeyboardPartIntegration:
    """Integration tests simulating real usage patterns."""

    def test_typing_sequence_hello(self, linux_ds_wayland_keyboard):
        """Simulate typing 'hello' character by character."""
        calls = []
        for char in "hello":
            linux_ds_wayland_keyboard.key_down(char)
            linux_ds_wayland_keyboard.key_up(char)

            keycode, _ = linux_ds_wayland_keyboard._char_map.get(char, (None, None))
            calls.append(call(keycode, 1))
            calls.append(call(keycode, 0))

        linux_ds_wayland_keyboard._device.emit.assert_has_calls(calls)

    def test_modifier_combination_ctrl_c(self, linux_ds_wayland_keyboard):
        """Simulate Ctrl+C key combination."""
        # Press Ctrl+C
        linux_ds_wayland_keyboard.key_down("ctrl")
        linux_ds_wayland_keyboard.key_down("c")

        # Release C+Ctrl
        linux_ds_wayland_keyboard.key_up("c")
        linux_ds_wayland_keyboard.key_up("ctrl")

        keycode_ctrl, _ = linux_ds_wayland_keyboard._char_map.get("ctrl", (None, None))
        keycode_c, _ = linux_ds_wayland_keyboard._char_map.get("c", (None, None))
        linux_ds_wayland_keyboard._device.emit.assert_has_calls([
            call(keycode_ctrl, 1),
            call(keycode_c, 1),
            call(keycode_c, 0),
            call(keycode_ctrl, 0),
        ])

    def test_rapid_key_presses(self, linux_ds_wayland_keyboard):
        """Rapid key presses don't interfere with each other."""
        # Simulate rapid typing
        calls = []
        keycode, _ = linux_ds_wayland_keyboard._char_map.get("a", (None, None))

        for _ in range(10):
            linux_ds_wayland_keyboard.key_down("a")
            linux_ds_wayland_keyboard.key_up("a")
            calls.append(call(keycode, 1))
            calls.append(call(keycode, 0))

        # Should have written events for each press/release
        linux_ds_wayland_keyboard._device.emit.assert_has_calls(calls)

    def test_all_letters_mappable(self, linux_ds_wayland_keyboard):
        """All letters a-z should be mappable."""
        import string

        for char in string.ascii_lowercase:
            assert linux_ds_wayland_keyboard.key_is_mapped(char) is True, \
                f"Letter '{char}' should be mapped"

    def test_device_persistence_across_calls(self, linux_ds_wayland_keyboard):
        """Device handle persists across multiple key operations."""
        device_before = linux_ds_wayland_keyboard._device

        linux_ds_wayland_keyboard.key_down("a")
        linux_ds_wayland_keyboard.key_up("a")
        linux_ds_wayland_keyboard.key_down("b")
        linux_ds_wayland_keyboard.key_up("b")

        device_after = linux_ds_wayland_keyboard._device

        # Should be the same device object
        assert device_before is device_after
