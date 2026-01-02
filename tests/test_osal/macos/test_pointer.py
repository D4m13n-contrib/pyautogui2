"""Unit tests for pyautogui2.osal.macos.pointer.MacOSPointer."""
from unittest.mock import call, patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException
from pyautogui2.utils.types import ButtonName, Point


class TestPointerSetupPostinit:
    """Tests for MacOSPointer.setup_postinit()."""

    def test_setup_postinit_normal(self, macos_pointer):
        """- primary/secondary mapping set left-handed by default."""
        macos_pointer.setup_postinit()
        assert macos_pointer.BUTTON_NAME_MAPPING[ButtonName.PRIMARY] == macos_pointer.BUTTON_NAME_MAPPING[ButtonName.LEFT]

    def test_setup_postinit_left_handed(self, macos_pointer):
        """primary/secondary mapping uses swapLeftRightButton == 0."""
        macos_pointer._mocks["mock_subprocess"].set_primary_button_left()
        macos_pointer.setup_postinit()
        btn_mapping = macos_pointer.BUTTON_NAME_MAPPING
        assert btn_mapping[ButtonName.PRIMARY] == btn_mapping[ButtonName.LEFT]
        assert btn_mapping[ButtonName.SECONDARY] == btn_mapping[ButtonName.RIGHT]

    def test_setup_postinit_right_handed(self, macos_pointer):
        """primary/secondary mapping uses swapLeftRightButton == 1."""
        macos_pointer._mocks["mock_subprocess"].set_primary_button_right()
        macos_pointer.setup_postinit()
        btn_mapping = macos_pointer.BUTTON_NAME_MAPPING
        assert btn_mapping[ButtonName.PRIMARY] == btn_mapping[ButtonName.RIGHT]
        assert btn_mapping[ButtonName.SECONDARY] == btn_mapping[ButtonName.LEFT]


class TestPointerGetPrimaryButton:
    """Tests for MacOSPointer.get_primary_button()."""

    def test_get_primary_button_left(self, macos_pointer):
        """SwapLeftRightButton == 0 -> primary is LEFT."""
        macos_pointer._mocks["mock_subprocess"].set_primary_button_left()
        assert macos_pointer.get_primary_button() == ButtonName.LEFT

    def test_get_primary_button_right_when_swapped(self, macos_pointer):
        """SwapLeftRightButton == 1 -> primary is RIGHT."""
        macos_pointer._mocks["mock_subprocess"].set_primary_button_right()
        assert macos_pointer.get_primary_button() == ButtonName.RIGHT

    def test_get_primary_button_invalid_fallback_default(self, macos_pointer):
        """If cannot get pointer disposition fallback to default -> primary is LEFT."""
        macos_pointer._mocks["mock_subprocess"]._setup_default_responses(default_value="Invalid_value")
        assert macos_pointer.get_primary_button() == ButtonName.LEFT

    def test_get_primary_button_command_failed_fallback_default(self, macos_pointer):
        """If cannot get pointer disposition fallback to default -> primary is LEFT."""
        macos_pointer._mocks["mock_subprocess"].simulate_defaults_failure("com.apple.driver.AppleHIDMouse",
                                                                          "swapLeftRightButton")
        assert macos_pointer.get_primary_button() == ButtonName.LEFT


class TestPointerGetPos:
    """Tests for MacOSPointer.get_pos()."""

    def test_get_pos_success(self, macos_pointer):
        """GetCursorPos returns position."""
        macos_pointer._mocks["mock_appkit"].mock_set_pointer_position(12, 34)
        pt = macos_pointer.get_pos()
        assert pt == Point(12, 34)

    def test_get_pos_failure_raises(self, macos_pointer):
        """When GetCursorPos returns False, PyAutoGUIException is raised."""
        def fake_get_cursor_pos():
            return False
        macos_pointer._mocks["mock_appkit"].NSEvent.mouseLocation.side_effect = fake_get_cursor_pos
        with pytest.raises(PyAutoGUIException, match=r"Error: AppKit.NSEvent.mouseLocation\(\) failed"):
            macos_pointer.get_pos()


class TestPointerMoveTo:
    """Tests for MacOSPointer.move_to()."""

    def test_move_to_basic(self, macos_pointer):
        """Test basic mouse movement."""
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        macos_pointer.move_to(10, 20)
        mock_quartz.CGEventCreateMouseEvent.assert_called_once_with(
            None, mock_quartz.kCGEventMouseMoved, (10, 20), 0
        )
        mock_quartz.CGEventPost.assert_called_once()

    def test_move_to_origin(self, macos_pointer):
        """Test mouse movement to origin."""
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        macos_pointer.move_to(0, 0)
        mock_quartz.CGEventCreateMouseEvent.assert_called_once_with(
            None, mock_quartz.kCGEventMouseMoved, (0, 0), 0
        )

    def test_move_to_posts_to_hid_event_tap(self, macos_pointer):
        """Test that event is posted to kCGHIDEventTap."""
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        macos_pointer.move_to(50, 60)
        created_event = mock_quartz.CGEventCreateMouseEvent.return_value
        mock_quartz.CGEventPost.assert_called_once_with(
            mock_quartz.kCGHIDEventTap, created_event
        )

    def test_move_to_multiple(self, macos_pointer):
        """Test multiple successive movements."""
        macos_pointer.move_to(100, 200)
        macos_pointer.move_to(300, 400)

        ev = macos_pointer._MOUSE_EVENTS["move"]["_"]
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        mock_quartz.CGEventCreateMouseEvent.assert_has_calls([
            call(None, ev, (100, 200), 0),
            call(None, ev, (300, 400), 0),
        ])
        assert mock_quartz.CGEventPost.call_count == 2

    def test_move_to_ignores_extra_kwargs(self, macos_pointer):
        """Test that move_to ignores extra keyword arguments."""
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        macos_pointer.move_to(50, 60, duration=0.5, tween="linear")
        mock_quartz.CGEventCreateMouseEvent.assert_called_once_with(
            None, mock_quartz.kCGEventMouseMoved, (50, 60), 0
        )

    @patch("time.sleep")
    def test_move_to_temporize(self, mock_sleep, macos_pointer):
        """Test that move_to sleeps after execution for OS catch-up."""
        macos_pointer.move_to(10, 20)
        mock_sleep.assert_called_once()


class TestPointerDragTo:
    """Tests for MacOSPointer.drag_to()."""

    def test_drag_to_success(self, macos_pointer):
        """drag_to() should send drag event."""
        macos_pointer.drag_to(120, 130, button=ButtonName.PRIMARY)

        bt = macos_pointer.BUTTON_NAME_MAPPING[ButtonName.PRIMARY]
        ev = macos_pointer._MOUSE_EVENTS["drag"][bt]
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        mock_quartz.CGEventCreateMouseEvent.assert_has_calls([
            call(None, ev, (120, 130), bt),
        ])
        assert mock_quartz.CGEventPost.call_count == 1


class TestPointerEmitButton:
    """Tests for MacOSPointer._emit_button()."""

    def test_emit_button_success(self, macos_pointer):
        """_emit_button() should send press event with current position."""
        macos_pointer._mocks["mock_appkit"].mock_set_pointer_position(10, 20)

        bt = macos_pointer.BUTTON_NAME_MAPPING[ButtonName.PRIMARY]

        macos_pointer._emit_button(bt, action="press")

        ev = macos_pointer._MOUSE_EVENTS["press"][bt]
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        mock_quartz.CGEventCreateMouseEvent.assert_has_calls([
            call(None, ev, (10, 20), bt),
        ])
        assert mock_quartz.CGEventPost.call_count == 1


class TestPointerButtonDecorators:
    """Ensure button decorator prevents duplicate presses/releases and raises for invalid usage."""

    def test_button_down_and_up_honor_decorator(self, macos_pointer):
        """The decorator on button_down / button_up uses internal _button_pressed to avoid
        re-pressing a button already pressed. We verify the state updates and that underlying
        emission is invoked only on state transitions.
        """
        emission_calls = []

        def fake_emit(button, press):
            emission_calls.append((button, press))

        # Wire the low-level emitter to track calls
        macos_pointer._emit_button = lambda button, press: fake_emit(button, press)

        # First down should call emitter
        macos_pointer.button_down(ButtonName.PRIMARY)
        assert len(emission_calls) == 1

        # Second down should not call emitter (already pressed)
        macos_pointer.button_down(ButtonName.PRIMARY)
        assert len(emission_calls) == 1

        # First up should not call emitter (still pressed)
        macos_pointer.button_up(ButtonName.PRIMARY)
        assert len(emission_calls) == 1

        # Second up should call emitter
        macos_pointer.button_up(ButtonName.PRIMARY)
        assert len(emission_calls) == 2

    def test_decorator_raises_on_invalid_button(self, macos_pointer):
        """The decorator should raise PyAutoGUIException for unsupported button types."""
        with pytest.raises(PyAutoGUIException):
            macos_pointer.button_down("NOT_A_BUTTON")  # type: ignore[arg-type]


class TestPointerScroll:
    """Tests for MacOSPointer.scroll()."""

    def test_scroll_vertical_success(self, macos_pointer):
        """scroll() should send scroll event."""
        macos_pointer.scroll(dx=0, dy=5)

        ev = macos_pointer._quartz.kCGScrollEventUnitLine
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        mock_quartz.CGEventCreateScrollWheelEvent.assert_has_calls([
            call(None, ev, 2, 5, 0),
        ])
        assert mock_quartz.CGEventPost.call_count == 1

    def test_scroll_horizontal_success(self, macos_pointer):
        """scroll() should send scroll event."""
        macos_pointer.scroll(dx=5, dy=0)

        ev = macos_pointer._quartz.kCGScrollEventUnitLine
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        mock_quartz.CGEventCreateScrollWheelEvent.assert_has_calls([
            call(None, ev, 2, 0, 5),
        ])
        assert mock_quartz.CGEventPost.call_count == 1

    def test_scroll_both_success(self, macos_pointer):
        """scroll() should send scroll event."""
        macos_pointer.scroll(dx=5, dy=6)

        ev = macos_pointer._quartz.kCGScrollEventUnitLine
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        mock_quartz.CGEventCreateScrollWheelEvent.assert_has_calls([
            call(None, ev, 2, 6, 5),
        ])
        assert mock_quartz.CGEventPost.call_count == 1

    def test_scroll_steps_success(self, macos_pointer):
        """scroll() should send scroll event."""
        macos_pointer.scroll(dx=0, dy=50)

        ev = macos_pointer._quartz.kCGScrollEventUnitLine
        mock_quartz = macos_pointer._mocks["mock_quartz"]
        mock_quartz.CGEventCreateScrollWheelEvent.assert_has_calls([
            call(None, ev, 2, 10, 0),
            call(None, ev, 2, 10, 0),
            call(None, ev, 2, 10, 0),
            call(None, ev, 2, 10, 0),
            call(None, ev, 2, 10, 0),
        ])
        assert mock_quartz.CGEventPost.call_count == 5


class TestPointerMouseInfo:
    """Tests for MacOSPointer.mouse_info()."""

    def test_mouse_info_delegate(self, macos_pointer):
        """mouse_info() delegates to mouseinfo library."""
        macos_pointer.mouse_info()
        macos_pointer._mocks["mouseinfo"].MouseInfoWindow.assert_called_once()
