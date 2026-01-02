"""Tests for PyAutoGUI API Entrypoint.

These tests verify that:
  - The top-level import (`import pyautogui2`) works correctly
  - The module exposes expected constants, types, and methods
  - The legacy API delegates to the modern API correctly
  - The underlying `PyAutoGUI` instance is created lazily
"""
import datetime
import os
import sys
import types

from unittest.mock import MagicMock, call, patch

import pytest

from pyautogui2.utils.types import ButtonName, Point, Size


class TestModuleStructure:
    """Test the basic structure of the pyautogui2 module."""

    def test_module_is_lazy_proxy(self, pyautogui_mocked):
        """Ensure pyautogui2 module is replaced by a lazy proxy."""
        import pyautogui2

        assert isinstance(pyautogui2, types.ModuleType)
        assert sys.modules["pyautogui2"] is pyautogui2

    def test_constants_exposed(self, pyautogui_mocked):
        """Ensure button and key constants are available."""
        import pyautogui2

        # Mouse button constants
        assert hasattr(pyautogui2, "LEFT")
        assert hasattr(pyautogui2, "RIGHT")
        assert hasattr(pyautogui2, "MIDDLE")
        assert hasattr(pyautogui2, "PRIMARY")
        assert hasattr(pyautogui2, "SECONDARY")
        assert pyautogui2.LEFT.value == "left"
        assert pyautogui2.LEFT == ButtonName.LEFT
        assert pyautogui2.RIGHT.value == "right"
        assert pyautogui2.RIGHT == ButtonName.RIGHT
        assert pyautogui2.MIDDLE.value == "middle"
        assert pyautogui2.MIDDLE == ButtonName.MIDDLE
        assert pyautogui2.PRIMARY.value == "primary"
        assert pyautogui2.PRIMARY == ButtonName.PRIMARY
        assert pyautogui2.SECONDARY.value == "secondary"
        assert pyautogui2.SECONDARY == ButtonName.SECONDARY

        # Key names
        assert hasattr(pyautogui2, "KEY_NAMES")
        assert isinstance(pyautogui2.KEY_NAMES, (list, tuple))

    def test_types_exposed(self, pyautogui_mocked):
        """Ensure Point and Size types are exposed."""
        import pyautogui2

        assert hasattr(pyautogui2, "Point")
        assert hasattr(pyautogui2, "Size")
        assert pyautogui2.Point is Point
        assert pyautogui2.Size is Size

    def test_unknown_attribute_raise(self, pyautogui_mocked):
        """An unknown attribute should raise AttributeError."""
        import pyautogui2

        with pytest.raises(AttributeError, match="'_LazyPyAutoGUI' object has no attribute 'unexisting_attribute'"):
            _ = pyautogui2.unexisting_attribute

    def test_dir_includes_legacy_api(self, pyautogui_mocked):
        """Ensure dir(pyautogui2) includes legacy names and constants."""
        import pyautogui2

        names = dir(pyautogui2)

        # Legacy pointer methods
        for method in ["click", "doubleClick", "tripleClick", "rightClick",
                      "moveTo", "moveRel", "mouseDown", "mouseUp", "scroll",
                      "position"]:
            assert method in names, f"Missing legacy method: {method}"

        # Legacy keyboard methods
        for method in ["press", "keyDown", "keyUp", "write", "hotkey"]:
            assert method in names, f"Missing legacy method: {method}"

        # Legacy display methods
        for method in ["size", "screenshot"]:
            assert method in names, f"Missing legacy method: {method}"

        # Constants
        for constant in ["LEFT", "RIGHT", "MIDDLE", "PRIMARY", "SECONDARY", "KEY_NAMES"]:
            assert constant in names, f"Missing constant: {constant}"

        # Types
        for type_name in ["Point", "Size"]:
            assert type_name in names, f"Missing type: {type_name}"

        # Modern API controllers
        for controller in ["pointer", "keyboard", "screen", "dialogs"]:
            assert controller in names, f"Missing controller: {controller}"


class TestLazyLoading:
    """Test that PyAutoGUI instance is created lazily."""

    def test_instance_created_on_first_access(self, osal_mocked):
        """Verify that _instance is created only when first accessed."""
        import pyautogui2

        from pyautogui2.utils.singleton import Singleton

        # Full isolation: reset singleton + patch OSAL to avoid real platform detection
        pyautogui2._reset_instance()

        with patch("pyautogui2.controllers.get_osal", return_value=osal_mocked):
            # Before access, no instance should exist
            assert Singleton._instances.get("PyAutoGUI") is None

            # Access a controller — should trigger instantiation
            _ = pyautogui2.pointer

            # Now instance should exist
            assert Singleton._instances.get("PyAutoGUI") is not None

        # Cleanup
        pyautogui2._reset_instance()

    def test_instance_reused_on_subsequent_access(self, pyautogui_mocked):
        """Verify that the same instance is reused."""
        import pyautogui2

        from pyautogui2.utils.singleton import Singleton

        # Access twice
        _ = pyautogui2.pointer
        instance1 = Singleton._instances.get("PyAutoGUI")
        _ = pyautogui2.keyboard
        instance2 = Singleton._instances.get("PyAutoGUI")

        # Should be the same instance
        assert instance1 is instance2


class TestLegacyAPIDelegationPointer:
    """Test that legacy API methods delegate to modern pointer API correctly."""

    def test_click_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.click() calls pointer.click()."""
        import pyautogui2

        pyautogui2.click(x=100, y=200, clicks=2, button="right", interval=0.1)

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(100, 200),
            call.get_pos(),
            call.button_down(ButtonName.RIGHT),
            call.button_up(ButtonName.RIGHT),
            call.get_pos(),
            call.button_down(ButtonName.RIGHT),
            call.button_up(ButtonName.RIGHT),
        ])

        assert pyautogui_mocked.pointer.get_position() == Point(100, 200)

    def test_click_with_default_position(self, pyautogui_mocked):
        """Verify that click() without x/y uses current position."""
        import pyautogui2

        # Set current position
        pyautogui_mocked.pointer._osal._position = Point(500, 600)

        pyautogui2.click()

        # Should click at current position
        pyautogui_mocked.pointer._osal.button_down.assert_called_once()
        pyautogui_mocked.pointer._osal.button_up.assert_called_once()

    def test_doubleClick_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.doubleClick() calls pointer.click(clicks=2)."""
        import pyautogui2

        pyautogui2.doubleClick(x=100, y=200, button="left", interval=0.1)

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(100, 200),
            call.get_pos(),
            call.button_down(ButtonName.LEFT),
            call.button_up(ButtonName.LEFT),
            call.get_pos(),
            call.button_down(ButtonName.LEFT),
            call.button_up(ButtonName.LEFT),
        ])

    def test_tripleClick_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.tripleClick() calls pointer.click(clicks=3)."""
        import pyautogui2

        pyautogui2.tripleClick(x=50, y=60, button="left")

        # Should have 3 down/up pairs
        assert pyautogui_mocked.pointer._osal.button_down.call_count == 3
        assert pyautogui_mocked.pointer._osal.button_up.call_count == 3

    def test_leftClick_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.leftClick() calls pointer.click(button='left')."""
        import pyautogui2

        pyautogui2.leftClick(x=100, y=200)

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(100, 200),
            call.get_pos(),
            call.button_down(ButtonName.LEFT),
            call.button_up(ButtonName.LEFT),
        ])

    def test_rightClick_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.rightClick() calls pointer.click(button='right')."""
        import pyautogui2

        pyautogui2.rightClick(x=100, y=200)

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(100, 200),
            call.get_pos(),
            call.button_down(ButtonName.RIGHT),
            call.button_up(ButtonName.RIGHT),
        ])

    def test_middleClick_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.middleClick() calls pointer.click(button='middle')."""
        import pyautogui2

        pyautogui2.middleClick(x=100, y=200)

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(100, 200),
            call.get_pos(),
            call.button_down(ButtonName.MIDDLE),
            call.button_up(ButtonName.MIDDLE),
        ])

    def test_moveTo_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.moveTo() calls pointer.move_to()."""
        import pyautogui2

        # Set a known position first
        pyautogui_mocked.pointer._osal._position = Point(10, 10)

        pyautogui2.moveTo(100, 100, duration=0.2)

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(10, 10),
            call.move_to(32, 32),
            call.move_to(55, 55),
            call.move_to(78, 78),
            call.move_to(100, 100),
            call.get_pos(),
        ])
        assert pyautogui_mocked.pointer.get_position() == Point(100, 100)

    def test_moveRel_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.moveRel() calls pointer.move_to() relative to current position."""
        import pyautogui2

        # Set a known position first
        pyautogui_mocked.pointer._osal._position = Point(100, 100)

        pyautogui2.moveRel(10, -20, duration=0.2)

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(100, 100),
            call.move_to(102, 95),
            call.move_to(105, 90),
            call.move_to(108, 85),
            call.move_to(110, 80),
            call.get_pos(),
        ])
        assert pyautogui_mocked.pointer.get_position() == Point(110, 80)

    def test_mouseDown_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.mouseDown() calls pointer.mouse_down()."""
        import pyautogui2

        pyautogui2.mouseDown(x=150, y=250, button="middle")

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(150, 250),
            call.get_pos(),
            call.button_down(ButtonName.MIDDLE),
        ])

    def test_mouseUp_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.mouseUp() calls pointer.mouse_up()."""
        import pyautogui2

        pyautogui2.mouseUp(x=150, y=250, button="middle")

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(150, 250),
            call.get_pos(),
            call.button_up(ButtonName.MIDDLE),
        ])

    def test_dragTo_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.dragTo() performs drag operation."""
        import pyautogui2

        # Set initial position
        pyautogui_mocked.pointer._osal._position = Point(0, 0)

        pyautogui2.dragTo(100, 200, duration=0.2, button="left")

        # Should move with button held down
        pyautogui_mocked.pointer._osal.button_down.assert_called_once_with(ButtonName.LEFT)
        pyautogui_mocked.pointer._osal.button_up.assert_called_once_with(ButtonName.LEFT)
        assert pyautogui_mocked.pointer._osal.drag_to.call_count > 1  # Multiple moves

    def test_drag_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.drag() performs relative drag."""
        import pyautogui2

        # Set initial position
        pyautogui_mocked.pointer._osal._position = Point(100, 100)

        pyautogui2.drag(50, 50, duration=0.2, button="left")

        # Should drag from (100,100) to (150,150)
        pyautogui_mocked.pointer._osal.button_down.assert_called_once_with(ButtonName.LEFT)
        pyautogui_mocked.pointer._osal.button_up.assert_called_once_with(ButtonName.LEFT)
        assert pyautogui_mocked.pointer._osal.drag_to.call_count > 1  # Multiple moves

    def test_hscroll_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.hscroll() calls pointer.scroll() with dx."""
        import pyautogui2

        pyautogui2.hscroll(5, x=100, y=200)

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(100, 200),
            call.get_pos(),
            call.scroll(dx=5),
        ])

    def test_vscroll_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.vscroll() calls pointer.scroll() with dy."""
        import pyautogui2

        pyautogui2.vscroll(5, x=100, y=200)

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(100, 200),
            call.get_pos(),
            call.scroll(dy=5),
        ])

    def test_scroll_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.scroll() calls pointer.scroll()."""
        import pyautogui2

        pyautogui2.scroll(5, x=100, y=200)

        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(100, 200),
            call.get_pos(),
            call.scroll(dy=5),
        ])

    def test_scroll_without_position(self, pyautogui_mocked):
        """Verify that scroll() without x/y uses current position."""
        import pyautogui2

        pyautogui_mocked.pointer._osal._position = Point(300, 400)

        pyautogui2.scroll(3)

        pyautogui_mocked.pointer._osal.scroll.assert_called_once_with(dy=3)

    def test_position_delegates_to_pointer(self, pyautogui_mocked):
        """Verify that pyautogui2.position() calls pointer.position()."""
        import pyautogui2

        # Set a known position first
        pyautogui_mocked.pointer._osal._position = Point(333, 444)

        result = pyautogui2.position()

        pyautogui_mocked.pointer._osal.get_pos.assert_called_once()
        assert result == Point(333, 444)

    def test_multiple_calls_tracked(self, pyautogui_mocked):
        """Verify that multiple calls are tracked correctly."""
        import pyautogui2

        # Make multiple calls
        pyautogui2.click(10, 20)
        pyautogui2.click(30, 40)
        pyautogui2.click(50, 60)

        # Check call count
        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(10, 20),
            call.get_pos(),
            call.button_down(ButtonName.PRIMARY),
            call.button_up(ButtonName.PRIMARY),
            call.get_pos(),
            call.move_to(30, 40),
            call.get_pos(),
            call.button_down(ButtonName.PRIMARY),
            call.button_up(ButtonName.PRIMARY),
            call.get_pos(),
            call.move_to(50, 60),
            call.get_pos(),
            call.button_down(ButtonName.PRIMARY),
            call.button_up(ButtonName.PRIMARY),
        ])


class TestDisplayMousePosition:
    """Test the displayMousePosition() interactive utility."""

    @patch('sys.stdout')
    @patch('time.sleep')
    def test_displayMousePosition_basic(self, mock_sleep, mock_stdout, pyautogui_mocked):
        """Verify displayMousePosition() prints mouse coordinates."""
        import pyautogui2

        # Mock position
        pyautogui_mocked.pointer._osal._position = Point(100, 200)

        # Mock screenshot
        mock_screenshot = MagicMock()
        mock_screenshot.getpixel.return_value = (255, 128, 64)
        pyautogui_mocked.screen._osal.screenshot.return_value = mock_screenshot

        # Simulate Ctrl-C after 1 iteration
        pyautogui_mocked.pointer._osal.get_pos.side_effect = [
            Point(100, 200),
            KeyboardInterrupt()
        ]

        # Run
        pyautogui2.displayMousePosition()

        # Verify output was written
        assert mock_stdout.write.called

    @patch('sys.stdout')
    @patch('sys.stdin')
    def test_displayMousePosition_in_idle(self, mock_stdin, mock_stdout, pyautogui_mocked):
        """Verify displayMousePosition() handles IDLE environment."""
        import pyautogui2

        # Mock IDLE environment
        mock_stdin.__module__ = "idlelib.something"

        # Mock position
        pyautogui_mocked.pointer._osal._position = Point(50, 75)

        # Simulate Ctrl-C after 1 iteration
        pyautogui_mocked.pointer._osal.get_pos.side_effect = [
            Point(50, 75),
            KeyboardInterrupt()
        ]

        # Run
        pyautogui2.displayMousePosition()

        # In IDLE, should print newlines instead of backspaces
        newline_calls = [c for c in mock_stdout.write.call_args_list if c[0][0] == "\n"]
        assert len(newline_calls) == 3

    @patch('sys.stdout')
    def test_displayMousePosition_not_in_idle(self, mock_stdout, pyautogui_mocked):
        """Verify displayMousePosition() handles non IDLE environment."""
        import sys

        import pyautogui2

        class StdinRaisesOnModule:
            """Custom stdin that raises AttributeError on __module__ access."""
            def __getattribute__(self, name):
                if name == '__module__':
                    raise AttributeError("__module__ not available")
                return super().__getattribute__(name)

        # Mock IDLE environment
        original_stdin = sys.stdin
        sys.stdin = StdinRaisesOnModule()

        # Mock position
        pyautogui_mocked.pointer._osal._position = Point(50, 75)

        # Simulate Ctrl-C after 1 iteration
        pyautogui_mocked.pointer._osal.get_pos.side_effect = [
            Point(50, 75),
            KeyboardInterrupt()
        ]

        try:
            # Run
            pyautogui2.displayMousePosition()
        finally:
            sys.stdin = original_stdin

        # In non IDLE, should print backspaces instead of newlines
        printed_line = mock_stdout.write.call_args_list[2][0][0]
        backspace_calls = [c for c in mock_stdout.write.call_args_list if c[0][0] == ("\b" * len(printed_line))]
        assert len(backspace_calls) == 1


    @patch('sys.stdout')
    def test_displayMousePosition_with_offsets(self, mock_stdout, pyautogui_mocked):
        """Verify displayMousePosition() handles xOffset and yOffset."""
        import pyautogui2

        # Mock position
        pyautogui_mocked.pointer._osal._position = Point(100, 200)

        # Mock screenshot
        mock_screenshot = MagicMock()
        mock_screenshot.getpixel.return_value = (255, 128, 64)
        pyautogui_mocked.screen._osal.screenshot.return_value = mock_screenshot

        # Simulate Ctrl-C after 1 iteration
        pyautogui_mocked.pointer._osal.get_pos.side_effect = [
            Point(100, 200),
            KeyboardInterrupt()
        ]

        # Run with offsets
        pyautogui2.displayMousePosition(xOffset=10, yOffset=20)


    @patch('builtins.print')
    @patch('sys.stdout')
    def test_displayMousePosition_prints_offset_message(self, mock_stdout, mock_print, pyautogui_mocked):
        """Verify displayMousePosition() prints offset info when offsets are non-zero."""
        import pyautogui2

        pyautogui_mocked.pointer._osal._position = Point(100, 200)

        mock_screenshot = MagicMock()
        mock_screenshot.getpixel.return_value = (255, 128, 64)
        pyautogui_mocked.screen._osal.screenshot.return_value = mock_screenshot

        pyautogui_mocked.pointer._osal.get_pos.side_effect = [
            Point(100, 200),
            KeyboardInterrupt()
        ]

        pyautogui2.displayMousePosition(xOffset=5, yOffset=10)

        # Check that offset message was printed
        offset_printed = any("xOffset: 5 yOffset: 10" in str(c) for c in mock_print.call_args_list)
        assert offset_printed

    @patch('sys.platform', 'darwin')
    @patch('sys.stdout')
    def test_displayMousePosition_on_macos(self, mock_stdout, pyautogui_mocked):
        """Verify displayMousePosition() shows NaN pixel color on MacOS."""
        import pyautogui2

        pyautogui_mocked.pointer._osal._position = Point(100, 200)

        pyautogui_mocked.pointer._osal.get_pos.side_effect = [
            Point(100, 200),
            KeyboardInterrupt()
        ]

        pyautogui2.displayMousePosition()

        # On MacOS, pixel color should be NaN
        nan_printed = any("NaN" in str(c) for c in mock_stdout.write.call_args_list)
        assert nan_printed

    @patch('sys.stdin')
    @patch('sys.stdout')
    def test_displayMousePosition_handles_attribute_error(self, _mock_stdout, mock_stdin, pyautogui_mocked):
        """Verify displayMousePosition() handles AttributeError when checking IDLE."""
        import pyautogui2

        # Mock stdin without __module__ attribute
        delattr(mock_stdin, '__module__')

        pyautogui_mocked.pointer._osal._position = Point(100, 200)
        pyautogui_mocked.pointer._osal.get_pos.side_effect = KeyboardInterrupt()

        with patch.object(pyautogui_mocked.pointer, "on_screen", return_value=False):
            # Should not raise
            pyautogui2.displayMousePosition()


class TestLegacyAPIDelegationKeyboard:
    """Test that legacy API methods delegate to modern keyboard API correctly."""

    def test_typewrite_delegates_to_write(self, pyautogui_mocked):
        """Verify that pyautogui2.typewrite() is an alias for write()."""
        import pyautogui2

        pyautogui2.typewrite("test", interval=0.05)

        # Should call key_down/key_up for each character
        assert pyautogui_mocked.keyboard._osal.key_down.call_count == 4
        assert pyautogui_mocked.keyboard._osal.key_up.call_count == 4

    def test_press_delegates_to_keyboard(self, pyautogui_mocked):
        """Verify that pyautogui2.press() calls keyboard.key_down/key_up()."""
        import pyautogui2

        pyautogui2.press("a")

        pyautogui_mocked.keyboard._osal.mocks.assert_has_calls([
            call.key_down("a"),
            call.key_up("a"),
        ])

    def test_press_multiple_keys(self, pyautogui_mocked):
        """Verify that press() with list presses each key."""
        import pyautogui2

        pyautogui2.press(["a", "b", "c"])

        pyautogui_mocked.keyboard._osal.mocks.assert_has_calls([
            call.key_is_mapped("a"),
            call.key_down("a"),
            call.key_up("a"),
            call.key_is_mapped("b"),
            call.key_down("b"),
            call.key_up("b"),
            call.key_is_mapped("c"),
            call.key_down("c"),
            call.key_up("c"),
        ])

    def test_press_capital_letter(self, pyautogui_mocked):
        """Verify that pyautogui2.press() capital letter calls
        keyboard.key_down/key_up() with capital letter.
        """
        import pyautogui2

        pyautogui2.press("A")

        pyautogui_mocked.keyboard._osal.mocks.assert_has_calls([
            call.key_down("A"),
            call.key_up("A"),
        ])

    def test_keyDown_delegates_to_keyboard(self, pyautogui_mocked):
        """Verify that pyautogui2.keyDown() calls keyboard.key_down()."""
        import pyautogui2

        pyautogui2.keyDown("shift")

        pyautogui_mocked.keyboard._osal.key_down.assert_called_once_with("shift")

    def test_keyUp_delegates_to_keyboard(self, pyautogui_mocked):
        """Verify that pyautogui2.keyUp() calls keyboard.key_up()."""
        import pyautogui2

        pyautogui2.keyUp("shift")

        pyautogui_mocked.keyboard._osal.key_up.assert_called_once_with("shift")

    def test_write_delegates_to_keyboard(self, pyautogui_mocked):
        """Verify that pyautogui2.write() calls keyboard.write()."""
        import pyautogui2

        pyautogui2.write("hello", interval=0.05)

        pyautogui_mocked.keyboard._osal.mocks.assert_has_calls([
            call.key_is_mapped("h"),
            call.key_down("h"),
            call.key_up("h"),
            call.key_is_mapped("e"),
            call.key_down("e"),
            call.key_up("e"),
            call.key_is_mapped("l"),
            call.key_down("l"),
            call.key_up("l"),
            call.key_is_mapped("l"),
            call.key_down("l"),
            call.key_up("l"),
            call.key_is_mapped("o"),
            call.key_down("o"),
            call.key_up("o"),
        ])

    def test_hold_delegates_to_keyboard(self, pyautogui_mocked):
        """Verify that pyautogui2.hold() calls keyboard.hold()."""
        import pyautogui2

        with pyautogui2.hold("shift"):
            pyautogui2.press("enter")

        pyautogui_mocked.keyboard._osal.mocks.assert_has_calls([
            call.key_down("shift"),
            call.key_is_mapped("enter"),
            call.key_down("enter"),
            call.key_up("enter"),
            call.key_up("shift"),
        ])

    def test_hotkey_delegates_to_keyboard(self, pyautogui_mocked):
        """Verify that pyautogui2.hotkey() calls keyboard.hotkey()."""
        import pyautogui2

        pyautogui2.hotkey("ctrl", "c")

        pyautogui_mocked.keyboard._osal.mocks.assert_has_calls([
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_is_mapped("c"),
            call.key_down("c"),
            call.key_up("c"),
            call.key_up("ctrl"),
        ])

    def test_hotkey_with_many_keys(self, pyautogui_mocked):
        """Verify hotkey() with 3+ keys."""
        import pyautogui2

        pyautogui2.hotkey("ctrl", "shift", "s")

        pyautogui_mocked.keyboard._osal.mocks.assert_has_calls([
            call.key_is_mapped("ctrl"),
            call.key_down("ctrl"),
            call.key_is_mapped("shift"),
            call.key_down("shift"),
            call.key_is_mapped("s"),
            call.key_down("s"),
            call.key_up("s"),
            call.key_up("shift"),
            call.key_up("ctrl"),
        ])


class TestLegacyAPIDelegationScreen:
    """Test that legacy API methods delegate to modern screen API correctly."""

    def test_size_delegates_to_screen(self, pyautogui_mocked):
        """Verify that pyautogui2.size() calls screen.size()."""
        import pyautogui2

        result = pyautogui2.size()

        assert result.width == 1920  # Default mock size
        assert result.height == 1080

        pyautogui_mocked.screen._osal.get_size.assert_called_once()

    def test_screenshot_delegates_to_screen(self, pyautogui_mocked):
        """Verify that pyautogui2.screenshot() calls screen.screenshot()."""
        import pyautogui2

        result = pyautogui2.screenshot()

        # Should return a PIL Image
        from PIL import Image
        assert isinstance(result, Image.Image)

        pyautogui_mocked.screen._osal.screenshot.assert_called_once_with(None, None)

    def test_screenshot_with_region(self, pyautogui_mocked):
        """Verify that screenshot() with region passes correct params."""
        import pyautogui2

        pyautogui2.screenshot(region=(10, 20, 300, 400))

        pyautogui_mocked.screen._osal.screenshot.assert_called_once_with(
            None, (10, 20, 300, 400)
        )

    def test_screenshot_with_filename(self, pyautogui_mocked):
        """Verify that screenshot() with image filename saves file."""
        import pyautogui2

        pyautogui2.screenshot("test.png")

        pyautogui_mocked.screen._osal.screenshot.assert_called_once_with(
            "test.png", None
        )

    def test_locateOnScreen_delegates(self, pyautogui_mocked):
        """Verify that locateOnScreen() calls locate_on_screen()."""
        import pyautogui2

        pyautogui_mocked.screen._osal.locate_on_screen.return_value = (10, 20, 30, 40)

        result = pyautogui2.locateOnScreen("needle.png", confidence=0.9)

        pyautogui_mocked.screen._osal.locate_on_screen.assert_called_once()
        assert result == (10, 20, 30, 40)

    def test_locateAllOnScreen_delegates(self, pyautogui_mocked):
        """Verify that locateAllOnScreen() calls locate_all_on_screen()."""
        import pyautogui2

        pyautogui_mocked.screen._osal.locate_all_on_screen.return_value = [(10, 20, 30, 40), (50, 60, 70, 80)]

        result = list(pyautogui2.locateAllOnScreen("needle.png"))

        pyautogui_mocked.screen._osal.locate_all_on_screen.assert_called_once()
        assert len(result) == 2

    def test_locateCenterOnScreen_delegates(self, pyautogui_mocked):
        """Verify that locateCenterOnScreen() returns center point."""
        import pyautogui2

        pyautogui_mocked.screen._osal.locate_center_on_screen.return_value = Point(25, 40)

        result = pyautogui2.locateCenterOnScreen("needle.png")

        pyautogui_mocked.screen._osal.locate_center_on_screen.assert_called_once()
        assert result == Point(25, 40)

    def test_pixel_delegates_to_screen(self, pyautogui_mocked):
        """Verify that pixel() gets color at position."""
        import pyautogui2

        # Mock return RGB value
        pyautogui_mocked.screen._osal.pixel.return_value = (255, 128, 64)

        result = pyautogui2.pixel(100, 200)

        pyautogui_mocked.screen._osal.pixel.assert_called_once_with(100, 200)
        assert result == (255, 128, 64)

    def test_pixelMatchesColor_delegates_to_screen(self, pyautogui_mocked):
        """Verify pixelMatchesColor() calls pixel_matches_color()."""
        import pyautogui2

        pyautogui_mocked.screen._osal.pixel_matches_color.return_value = True

        result = pyautogui2.pixelMatchesColor(50, 60, (255, 0, 0), tolerance=10)

        pyautogui_mocked.screen._osal.pixel_matches_color.assert_called_once_with(50, 60, (255, 0, 0), 10)
        assert result is True


class TestSnapshot:
    """Test the snapshot() function."""

    @patch('os.getcwd', return_value='/home/user')
    @patch('datetime.datetime')
    def test_snapshot_creates_timestamped_file(self, mock_datetime, mock_getcwd, pyautogui_mocked):
        """Verify _snapshot() creates a file with timestamp."""
        import pyautogui2

        # Mock datetime
        mock_now = MagicMock()
        mock_now.year = 2026
        mock_now.month = 1
        mock_now.day = 15
        mock_now.hour = 10
        mock_now.minute = 30
        mock_now.second = 45
        mock_now.microsecond = 123456
        mock_datetime.now.return_value = mock_now

        pyautogui2._snapshot(tag="test")

        # Verify screenshot was called with correct path
        expected_filename = "2026-01-15_10-30-45-123_test.png"
        expected_path = os.path.join('/home/user', expected_filename)
        pyautogui_mocked.screen._osal.screenshot.assert_called_once_with(expected_path, None)

    @patch('datetime.datetime')
    def test_snapshot_with_custom_folder(self, mock_datetime, pyautogui_mocked, tmp_path):
        """Verify _snapshot() uses custom folder."""
        import pyautogui2

        mock_now = MagicMock()
        mock_now.year = 2026
        mock_now.month = 3
        mock_now.day = 7
        mock_now.hour = 14
        mock_now.minute = 22
        mock_now.second = 33
        mock_now.microsecond = 999999
        mock_datetime.now.return_value = mock_now

        screenshots_path = tmp_path / "screenshots"
        pyautogui2._snapshot(tag="custom", folder=str(screenshots_path))

        expected_filename = "2026-03-07_14-22-33-999_custom.png"
        expected_path = screenshots_path / expected_filename
        pyautogui_mocked.screen._osal.screenshot.assert_called_once_with(str(expected_path), None)

    def test_snapshot_raises_with_region_and_radius(self, pyautogui_mocked):
        """Verify _snapshot() raises when both region and radius are provided."""
        import pyautogui2

        with pytest.raises(Exception, match="Either region or radius"):
            pyautogui2._snapshot(tag="test", region=(0, 0, 100, 100), radius=50)

    @patch('datetime.datetime')
    def test_snapshot_with_radius(self, mock_datetime, pyautogui_mocked, tmp_path):
        """Verify _snapshot() with radius gets current pointer position."""
        import pyautogui2

        mock_now = MagicMock()
        mock_now.year = 2026
        mock_now.month = 12
        mock_now.day = 25
        mock_now.hour = 8
        mock_now.minute = 15
        mock_now.second = 0
        mock_now.microsecond = 0
        mock_datetime.now.return_value = mock_now

        pyautogui_mocked.pointer._osal._position = Point(500, 600)

        pyautogui2._snapshot(tag="radius_test", radius=100, folder=str(tmp_path))

        # Verify get_position was called when radius is provided
        pyautogui_mocked.pointer._osal.get_pos.assert_called()


class TestLegacyAPIDelegationDialogs:
    """Test that legacy API methods delegate to modern dialogs API correctly."""

    def test_alert_delegates_to_dialogs(self, pyautogui_mocked):
        """Verify that pyautogui2.alert() calls dialogs.alert()."""
        import pyautogui2

        pyautogui2.alert('Alert')

        pyautogui_mocked.dialogs._osal.alert.assert_called_once()

    def test_confirm_delegates_to_dialogs(self, pyautogui_mocked):
        """Verify that pyautogui2.confirm() calls dialogs.confirm()."""
        import pyautogui2

        pyautogui2.confirm('Confirm')

        pyautogui_mocked.dialogs._osal.confirm.assert_called_once()

    def test_prompt_delegates_to_dialogs(self, pyautogui_mocked):
        """Verify that pyautogui2.prompt() calls dialogs.prompt()."""
        import pyautogui2

        pyautogui2.prompt('Prompt')

        pyautogui_mocked.dialogs._osal.prompt.assert_called_once()

    def test_password_delegates_to_dialogs(self, pyautogui_mocked):
        """Verify that pyautogui2.password() calls dialogs.password()."""
        import pyautogui2

        pyautogui2.password('Password')

        pyautogui_mocked.dialogs._osal.password.assert_called_once()


class TestLegacyRun:
    """Test the legacy run() function."""

    def test_run_delegates_to_legacy_run(self, pyautogui_mocked):
        """Verify that run() calls legacy_run()."""
        import pyautogui2

        with pytest.raises(NotImplementedError, match=r"run\(\) method is no more supported"):
            pyautogui2.run("ccg-20,+0c", _ssCount=0)


class TestPrintInfo:
    """Test the printInfo() function."""

    @patch('builtins.print')
    def test_printInfo_returns_system_info(self, mock_print, pyautogui_mocked):
        """Verify printInfo() returns formatted system information."""
        import pyautogui2

        # Mock _legacy_get_info
        info = (
            "Linux",
            "3.10.0",
            "2.0.0",
            "/usr/bin/python3",
            "1920x1080",
            "2026-01-15 10:30:00"
        )
        with patch("pyautogui2._legacy_get_info", return_value=info):
            result = pyautogui2.printInfo()

            # Verify result contains expected fields
            assert "Platform: Linux" in result
            assert "Python Version: 3.10.0" in result
            assert "PyAutoGUI Version: 2.0.0" in result
            assert "Executable: /usr/bin/python3" in result
            assert "Resolution: 1920x1080" in result
            assert "Timestamp: 2026-01-15 10:30:00" in result

            # Verify it was printed by default
            mock_print.assert_called_once()

    @patch('builtins.print')
    def test_printInfo_with_dontPrint(self, mock_print, pyautogui_mocked):
        """Verify printInfo(dontPrint=True) doesn't print."""
        import pyautogui2

        info = (
            "Linux", "3.10", "2.0", "/usr/bin/python3", "1920x1080", "2026-01-15"
        )
        with patch("pyautogui2._legacy_get_info", return_value=info):
            result = pyautogui2.printInfo(dontPrint=True)

            # Should return the message but not print it
            assert isinstance(result, str)
            mock_print.assert_not_called()

    def test_getInfo(self, pyautogui_mocked):
        """Verify getInfo() returns info."""
        import pyautogui2
        result = pyautogui2.getInfo()
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)
        assert isinstance(result[2], str)
        assert isinstance(result[3], str)
        assert isinstance(result[4], Size)
        assert isinstance(result[5], datetime.datetime)


class TestUtilityFunctions:
    """Test utility functions in __init__.py."""

    @patch("time.sleep")
    def test_sleep_function(self, mock_sleep, pyautogui_mocked):
        """Verify that pyautogui2.sleep() calls time.sleep()."""
        import pyautogui2

        pyautogui2.sleep(1.5)

        mock_sleep.assert_called_once_with(1.5)

    @patch("time.sleep")
    @patch("sys.stdout")
    def test_countdown_function(self, mock_stdout, mock_sleep, pyautogui_mocked):
        """Verify that countdown() prints and sleeps."""
        import pyautogui2

        pyautogui2.countdown(3)

        # Should sleep 3 times
        assert mock_sleep.call_count == 3

    def test_getPointOnLine(self, pyautogui_mocked):
        """Verify getPointOnLine() calculates intermediate point correctly."""
        import pyautogui2

        result = pyautogui2.getPointOnLine(0, 0, 100, 100, 0.5)

        assert result == (50, 50)

    def test_getPointOnLine_at_start(self, pyautogui_mocked):
        """Verify getPointOnLine() at n=0 returns start point."""
        import pyautogui2

        result = pyautogui2.getPointOnLine(10, 20, 100, 200, 0.0)

        assert result == (10, 20)

    def test_getPointOnLine_at_end(self, pyautogui_mocked):
        """Verify getPointOnLine() at n=1 returns end point."""
        import pyautogui2

        result = pyautogui2.getPointOnLine(10, 20, 100, 200, 1.0)

        assert result == (100, 200)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_click_with_none_coordinates_uses_current(self, pyautogui_mocked):
        """Verify that None coordinates use current position."""
        import pyautogui2

        pyautogui_mocked.pointer._osal._position = Point(123, 456)

        pyautogui2.click(x=None, y=None)

        # Should not call move_to (stays at current position)
        pyautogui_mocked.pointer._osal.button_down.assert_called_once()

    def test_moveTo_with_zero_duration(self, pyautogui_mocked):
        """Verify that duration=0 moves instantly."""
        import pyautogui2

        pyautogui_mocked.pointer._osal._position = Point(0, 0)

        pyautogui2.moveTo(100, 100, duration=0)

        pyautogui_mocked.pointer._osal.move_to.assert_called_once_with(100, 100)

    def test_scroll_with_negative_amount(self, pyautogui_mocked):
        """Verify that negative scroll works (scroll down)."""
        import pyautogui2

        pyautogui2.scroll(-5)

        pyautogui_mocked.pointer._osal.scroll.assert_called_once_with(dy=-5)

    def test_write_empty_string(self, pyautogui_mocked):
        """Verify that write('') doesn't call any key presses."""
        import pyautogui2

        pyautogui2.write("")

        # Should not call key_down or key_up
        pyautogui_mocked.keyboard._osal.key_down.assert_not_called()
        pyautogui_mocked.keyboard._osal.key_up.assert_not_called()

    def test_hotkey_with_single_key(self, pyautogui_mocked):
        """Verify that hotkey() with single key works."""
        import pyautogui2

        pyautogui2.hotkey("a")

        pyautogui_mocked.keyboard._osal.mocks.assert_has_calls([
            call.key_down("a"),
            call.key_up("a"),
        ])


class TestModernAPIAccess:
    """Test that modern API controllers are accessible."""

    def test_pointer_controller_accessible(self, pyautogui_mocked):
        """Verify that pyautogui2.pointer is accessible."""
        import pyautogui2

        from pyautogui2.controllers.pointer import PointerController
        assert isinstance(pyautogui2.pointer, PointerController)

    def test_keyboard_controller_accessible(self, pyautogui_mocked):
        """Verify that pyautogui2.keyboard is accessible."""
        import pyautogui2

        from pyautogui2.controllers.keyboard import KeyboardController
        assert isinstance(pyautogui2.keyboard, KeyboardController)

    def test_screen_controller_accessible(self, pyautogui_mocked):
        """Verify that pyautogui2.screen is accessible."""
        import pyautogui2

        from pyautogui2.controllers.screen import ScreenController
        assert isinstance(pyautogui2.screen, ScreenController)

    def test_dialogs_controller_accessible(self, pyautogui_mocked):
        """Verify that pyautogui2.dialogs is accessible."""
        import pyautogui2

        from pyautogui2.controllers.dialogs import DialogsController
        assert isinstance(pyautogui2.dialogs, DialogsController)

    def test_modern_api_calls_work(self, pyautogui_mocked):
        """Verify that modern API calls work correctly."""
        import pyautogui2

        # Call modern API
        pyautogui2.pointer.click(x=777, y=888)

        # Verify
        pyautogui_mocked.pointer._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(777, 888),
            call.get_pos(),
            call.button_down(ButtonName.PRIMARY),
            call.button_up(ButtonName.PRIMARY),
        ])
