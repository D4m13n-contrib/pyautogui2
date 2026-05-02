"""Unit tests for pyautogui2.osal.windows.pointer.WindowsPointer."""
import math

from unittest.mock import patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException
from pyautogui2.utils.types import ButtonName, Point


def _helper_convert_pos(user32, x, y):
    """Converts position to 0-65535 coordinates range."""
    screen_w = user32.GetSystemMetrics(0)   # SM_CXSCREEN
    screen_h = user32.GetSystemMetrics(1)   # SM_CYSCREEN
    abs_x = min(65535, math.ceil(x * 65535 / (screen_w - 1)))
    abs_y = min(65535, math.ceil(y * 65535 / (screen_h - 1)))
    return (abs_x, abs_y)


class TestPointerSetupPostinit:
    """Tests for WindowsPointer.setup_postinit()."""

    def test_setup_postinit_normal(self, windows_pointer):
        """- ensure_dpi_aware() is called.
        - primary/secondary mapping uses GetSystemMetrics(SM_SWAPBUTTON) == 0.
        """
        with patch("pyautogui2.osal.windows.pointer.ensure_dpi_aware", return_value=True) as mock_ensure:
            windows_pointer.setup_postinit()
            mock_ensure.assert_called()
            # primary should map to left when SM_SWAPBUTTON == 0
            assert windows_pointer.BUTTON_NAME_MAPPING[ButtonName.PRIMARY] == windows_pointer.BUTTON_NAME_MAPPING[ButtonName.LEFT]

    def test_setup_postinit_left_handed(self, windows_pointer):
        """primary/secondary mapping uses GetSystemMetrics(SM_SWAPBUTTON) == 0."""
        windows_pointer._user32.GetSystemMetrics.side_effect = lambda _idx: 0
        windows_pointer.setup_postinit()
        btn_mapping = windows_pointer.BUTTON_NAME_MAPPING
        assert btn_mapping[ButtonName.PRIMARY] == btn_mapping[ButtonName.LEFT]
        assert btn_mapping[ButtonName.SECONDARY] == btn_mapping[ButtonName.RIGHT]

    def test_setup_postinit_right_handed(self, windows_pointer):
        """primary/secondary mapping uses GetSystemMetrics(SM_SWAPBUTTON) == 1."""
        windows_pointer._user32.GetSystemMetrics.side_effect = lambda _idx: 1
        windows_pointer.setup_postinit()
        btn_mapping = windows_pointer.BUTTON_NAME_MAPPING
        assert btn_mapping[ButtonName.PRIMARY] == btn_mapping[ButtonName.RIGHT]
        assert btn_mapping[ButtonName.SECONDARY] == btn_mapping[ButtonName.LEFT]


class TestPointerLegacy:
    """Tests for WindowsPointer._is_legacy()."""

    def test_is_legacy_true_warns(self, windows_pointer, caplog):
        import logging

        windows_pointer._legacy_mode = None
        with patch("pyautogui2.osal.windows.pointer.is_legacy_windows", return_value=True), \
            caplog.at_level(logging.WARNING):
                result = windows_pointer._is_legacy()

        assert "WindowsPointer: legacy mode enabled" in caplog.text
        assert result is True

    def test_is_legacy_false_not_warns(self, windows_pointer, caplog):
        import logging

        windows_pointer._legacy_mode = None
        with patch("pyautogui2.osal.windows.pointer.is_legacy_windows", return_value=False), \
            caplog.at_level(logging.WARNING):
                result = windows_pointer._is_legacy()

        assert "WindowsPointer: legacy mode enabled" not in caplog.text
        assert result is False


class TestPointerGetPrimaryButton:
    """Tests for WindowsPointer.get_primary_button()."""

    def test_get_primary_button_left(self, windows_pointer):
        """SM_SWAPBUTTON == 0 -> primary is LEFT."""
        # default MockUser32 returns 0 for SM_SWAPBUTTON -> Left primary
        assert windows_pointer.get_primary_button() == ButtonName.LEFT

    def test_get_primary_button_right_when_swapped(self, windows_pointer):
        """SM_SWAPBUTTON == 1 -> primary is RIGHT."""
        # use a custom user32 that returns 1 for index 23
        windows_pointer._user32.GetSystemMetrics.side_effect = lambda _idx: 1
        assert windows_pointer.get_primary_button() == ButtonName.RIGHT


class TestPointerGetPos:
    """Tests for WindowsPointer.get_pos()."""

    def test_get_pos_success(self, windows_pointer):
        """GetCursorPos returns position."""
        windows_pointer._user32.mock_set_position(12, 34)
        pt = windows_pointer.get_pos()
        assert pt == Point(12, 34)

    def test_get_pos_failure_raises(self, windows_pointer):
        """When GetCursorPos returns False, PyAutoGUIException is raised."""
        def fake_get_cursor_pos(_point):
            return False
        windows_pointer._user32.GetCursorPos.side_effect = fake_get_cursor_pos
        with pytest.raises(PyAutoGUIException):
            windows_pointer.get_pos()


class TestPointerMoveTo:
    """Tests for WindowsPointer.move_to()."""

    def test_move_to_modern_sendinput_success(self, windows_pointer):
        """When send_input returns True, SendInput path is used and no fallback called."""
        windows_pointer._user32.SendInput.return_value = True
        windows_pointer.move_to(100, 200)
        windows_pointer._user32.SendInput.assert_called_once()

        # --- Verify INPUT structure ---
        inp_obj = windows_pointer._user32.SendInput.call_args[0][1]
        pos_x, pos_y = _helper_convert_pos(windows_pointer._user32, 100, 200)
        assert isinstance(inp_obj.u.mi.dx, int)
        assert inp_obj.u.mi.dx == pos_x
        assert isinstance(inp_obj.u.mi.dy, int)
        assert inp_obj.u.mi.dy == pos_y
        expected_flags = windows_pointer.MOUSEEVENTF_MOVE | windows_pointer.MOUSEEVENTF_ABSOLUTE
        assert inp_obj.u.mi.dwFlags == expected_flags

    def test_move_to_legacy_mouse_event_success(self, windows_pointer):
        """In legacy mode should use mouse_event()."""
        windows_pointer._legacy_mode = True

        windows_pointer.move_to(10, 20)

        windows_pointer._user32.SetCursorPos.assert_called_once_with(10, 20)
        assert not windows_pointer._user32.mouse_event.called

    def test_move_to_fallback_to_legacy_mouse_event(self, windows_pointer):
        """When send_input fails in non-legacy mode, move_to should fall back to legacy path:
        since SetCursorPos in MockUser32 returns True, mouse_event should not be used.
        We test both transitions by forcing SetCursorPos to return False as well.
        """
        # Case A: SetCursorPos succeeds -> no mouse_event call
        windows_pointer._user32.SetCursorPos.side_effect = lambda _x, _y: True
        windows_pointer._user32.SendInput.return_value = False
        windows_pointer.move_to(100, 200)
        # send_input returned False -> fallback attempted; SetCursorPos succeeded
        windows_pointer._user32.SetCursorPos.assert_called_once_with(100, 200)
        assert not windows_pointer._user32.mouse_event.called

        windows_pointer._user32.SetCursorPos.reset_mock()   # reset Mock calls

        # Case B: SetCursorPos fails -> mouse_event must be called
        windows_pointer._user32.SetCursorPos.side_effect = lambda _x, _y: False
        windows_pointer._user32.SendInput.return_value = False
        windows_pointer.move_to(50, 60)
        windows_pointer._user32.SetCursorPos.assert_called_once_with(50, 60)

        pos_x, pos_y = _helper_convert_pos(windows_pointer._user32, 50, 60)
        ev = windows_pointer.MOUSEEVENTF_MOVE | windows_pointer.MOUSEEVENTF_ABSOLUTE

        windows_pointer._user32.mouse_event.assert_called_once_with(ev, pos_x, pos_y, 0, 0)

    def test_move_to_invalid_screen_metrics_raises(self, windows_pointer):
        """If GetSystemMetrics returns invalid values (<=1), move_to raises RuntimeError."""
        # Make user32.GetSystemMetrics return 1 as a small (invalid) screen size
        windows_pointer._user32.GetSystemMetrics.side_effect = lambda _idx: 1
        with pytest.raises(RuntimeError, match="Invalid screen size from GetSystemMetrics"):
            windows_pointer.move_to(10, 10)

    def test_move_to_legacy_fallback(self, windows_pointer, caplog):
        """If send_input() fails should fallback to SetCursorPos(), and mouse_event() legacy methods."""
        import logging

        windows_pointer._user32.SendInput.return_value = False

        with caplog.at_level(logging.WARNING):
            windows_pointer.move_to(50, 60)

        assert "SendInput failed in move_to -> falling back to legacy" in caplog.text
        windows_pointer._user32.SetCursorPos.assert_called_once()

    def test_move_to_legacy_mouse_event_raise(self, windows_pointer):
        """If legacy mouse_event() fails should raise PyAutoGUIException."""
        windows_pointer._user32.SetCursorPos.side_effect = lambda _x, _y: False
        windows_pointer._user32.mouse_event.side_effect = Exception("Error")
        windows_pointer._user32.SendInput.return_value = False

        with pytest.raises(PyAutoGUIException, match="Error: move_to fallback failed"):
            windows_pointer.move_to(50, 60)


class TestPointerDragTo:
    """Tests for WindowsPointer.drag_to()."""

    def test_drag_to_calls_down_move_up(self, windows_pointer):
        """drag_to should call button_down, move_to and button_up in order (implicitly)."""
        # We'll spy on the three methods by patching them on the instance
        called = []

        def spy_down(_button, **_kw):
            called.append("down")

        def spy_move(_x, _y, **_kw):
            called.append("move")

        def spy_up(_button, **_kw):
            called.append("up")

        # Replace instance methods
        windows_pointer.button_down = spy_down
        windows_pointer.move_to = spy_move
        windows_pointer.button_up = spy_up

        windows_pointer.drag_to(120, 130, button=ButtonName.PRIMARY)
        assert called == ["down", "move", "up"]


class TestPointerEmitButton:
    """Tests for WindowsPointer._emit_button()."""

    def test_emit_button_modern(self, windows_pointer):
        """In modern mode, send_input is used for button events when it succeeds."""
        # Use private method directly
        windows_pointer._user32.SendInput.return_value = True
        windows_pointer._emit_button(ButtonName.PRIMARY, press=True)
        windows_pointer._user32.SendInput.assert_called()

        # --- Verify INPUT structure flags for press ---
        inp_obj = windows_pointer._user32.SendInput.call_args[0][1]
        assert inp_obj.u.mi.dwFlags == windows_pointer.BUTTON_NAME_MAPPING[ButtonName.PRIMARY][0]  # DOWN flag

    def test_emit_button_legacy(self, windows_pointer, caplog):
        """In legacy mode, user32.mouse_event is used for button events when it succeeds."""
        windows_pointer._legacy_mode = True

        windows_pointer._emit_button(ButtonName.PRIMARY, press=True)

        windows_pointer._user32.mouse_event.assert_called_once()

    def test_emit_button_fallback_to_mouse_event(self, windows_pointer, caplog):
        """If send_input fails, user32.mouse_event should be used as fallback."""
        import logging

        windows_pointer._user32.SendInput.return_value = False

        with caplog.at_level(logging.WARNING):
            windows_pointer._emit_button(ButtonName.PRIMARY, press=True)

        assert "SendInput failed for button -> fallback to mouse_event" in caplog.text
        windows_pointer._user32.mouse_event.assert_called_once()


class TestPointerButtonDecorators:
    """Ensure button decorator prevents duplicate presses/releases and raises for invalid usage."""

    def test_button_down_and_up_honor_decorator(self, windows_pointer):
        """The decorator on button_down / button_up uses internal _button_pressed to avoid
        re-pressing a button already pressed. We verify the state updates and that underlying
        emission is invoked only on state transitions.
        """
        emission_calls = []

        def fake_emit(button, press):
            emission_calls.append((button, press))

        # Wire the low-level emitter to track calls
        windows_pointer._emit_button = lambda button, press: fake_emit(button, press)

        # First down should call emitter
        windows_pointer.button_down(ButtonName.PRIMARY)
        assert len(emission_calls) == 1

        # Second down should not call emitter (already pressed)
        windows_pointer.button_down(ButtonName.PRIMARY)
        assert len(emission_calls) == 1

        # First up should not call emitter (still pressed)
        windows_pointer.button_up(ButtonName.PRIMARY)
        assert len(emission_calls) == 1

        # Second up should call emitter
        windows_pointer.button_up(ButtonName.PRIMARY)
        assert len(emission_calls) == 2

    def test_decorator_raises_on_invalid_button(self, windows_pointer):
        """The decorator should raise PyAutoGUIException for unsupported button types."""
        with pytest.raises(PyAutoGUIException):
            windows_pointer.button_down("NOT_A_BUTTON")  # type: ignore[arg-type]


class TestPointerScroll:
    """Tests for WindowsPointer.scroll()."""

    def test_scroll_vertical_modern_uses_sendinput(self, windows_pointer):
        """Vertical scroll with send_input success should call send_input with WHEEL_DELTA applied."""
        windows_pointer._user32.SendInput.return_value = True
        windows_pointer.scroll(dx=0, dy=2)
        windows_pointer._user32.SendInput.assert_called()

        # --- Verify INPUT mouseData and flags ---
        inp_obj = windows_pointer._user32.SendInput.call_args[0][1]
        assert inp_obj.u.mi.dwFlags == windows_pointer.MOUSEEVENTF_WHEEL
        assert inp_obj.u.mi.mouseData == 2 * windows_pointer.WHEEL_DELTA

    def test_scroll_horizontal_legacy_uses_mouse_event(self, windows_pointer):
        """In legacy mode should use mouse_event()."""
        windows_pointer._legacy_mode = True

        windows_pointer.scroll(dx=2, dy=0)

        windows_pointer._user32.SendInput.assert_not_called()
        windows_pointer._user32.mouse_event.assert_called_once()

    def test_scroll_horizontal_fallback_to_mouse_event(self, windows_pointer, caplog):
        """If send_input fails for horizontal scroll, fallback mouse_event should be invoked with proper data."""
        import logging

        # Force send_input to fail
        windows_pointer._user32.SendInput.return_value = False

        with caplog.at_level(logging.WARNING):
            windows_pointer.scroll(dx=1, dy=0)

        assert "SendInput failed for scroll -> fallback" in caplog.text
        windows_pointer._user32.mouse_event.assert_called()
        args = windows_pointer._user32.mouse_event.call_args[0]
        # args[3] = mouseData, which should equal dx * WHEEL_DELTA
        assert args[3] == 1 * windows_pointer.WHEEL_DELTA


class TestPointerMouseInfo:
    """Tests for WindowsPointer.mouse_info()."""

    def test_mouse_info_delegate(self, windows_pointer):
        """mouse_info() delegates to mouseinfo library."""
        windows_pointer.mouse_info()
        windows_pointer._mocks["mouseinfo"].MouseInfoWindow.assert_called_once()
