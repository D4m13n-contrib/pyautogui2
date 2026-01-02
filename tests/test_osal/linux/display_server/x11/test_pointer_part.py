"""Tests for X11 Display Server Part providing pointer functions.

X11 Display Server Part uses Xlib (XTest extension) to:
- Move pointer (XTestFakeMotionEvent)
- Click buttons (XTestFakeButtonEvent)
- Scroll (XTestFakeButtonEvent with wheel buttons 4/5)
- Get position (XQueryPointer)

Test strategy:
- Mock _display object
- Verify correct Xlib functions called with correct parameters
- Test error handling
"""

from unittest.mock import call, patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException
from pyautogui2.utils.types import ButtonName, Point


class TestX11PointerPartSetupPostinit:
    """Tests for X11 setup_postinit() functions."""

    def test_setup_postinit_without_display_raise(self, linux_ds_x11_pointer):
        """setup_postinit() calls without display should raise PyAutoGUIException."""
        linux_ds_x11_pointer._xlib.display.Display = lambda *_a, **_kw: None
        with pytest.raises(PyAutoGUIException, match="Error: Cannot obtain Display"):
            linux_ds_x11_pointer.setup_postinit()

    def test_setup_postinit_left_handed(self, linux_ds_x11_pointer):
        """setup_postinit() with left-handed mode."""
        with patch.object(linux_ds_x11_pointer, "get_primary_button", return_value=ButtonName.LEFT):
            linux_ds_x11_pointer.setup_postinit()

        btn_mapping = linux_ds_x11_pointer.BUTTON_NAME_MAPPING
        assert btn_mapping[ButtonName.PRIMARY] == btn_mapping[ButtonName.LEFT]
        assert btn_mapping[ButtonName.SECONDARY] == btn_mapping[ButtonName.RIGHT]

    def test_setup_postinit_right_handed(self, linux_ds_x11_pointer):
        """setup_postinit() with right-handed mode."""
        with patch.object(linux_ds_x11_pointer, "get_primary_button", return_value=ButtonName.RIGHT):
            linux_ds_x11_pointer.setup_postinit()

        btn_mapping = linux_ds_x11_pointer.BUTTON_NAME_MAPPING
        assert btn_mapping[ButtonName.PRIMARY] == btn_mapping[ButtonName.RIGHT]
        assert btn_mapping[ButtonName.SECONDARY] == btn_mapping[ButtonName.LEFT]


class TestX11PointerPartMovement:
    """Tests for X11 pointer movement functions."""

    def test_move_to_calls_xlib_with_absolute_coords(self, linux_ds_x11_pointer):
        """move_to() calls Xlib XTestFakeMotionEvent with absolute coordinates."""
        linux_ds_x11_pointer.move_to(100, 200)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.MotionNotify, x=100, y=200),
        ])
        linux_ds_x11_pointer._display.sync.assert_called_once()

    def test_move_to_handles_negative_coords(self, linux_ds_x11_pointer):
        """move_to() handles negative coordinates."""
        linux_ds_x11_pointer.move_to(-10, -20)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.MotionNotify, x=-10, y=-20),
        ])
        linux_ds_x11_pointer._display.sync.assert_called_once()

    def test_move_to_handles_none_coords(self, linux_ds_x11_pointer):
        """move_to() with None coordinates should raise PyAutoGUIException."""
        with pytest.raises(PyAutoGUIException, match=r"Error: x/y values \(x:None, y:None\) are required"):
            linux_ds_x11_pointer.move_to(None, None)

        with pytest.raises(PyAutoGUIException, match=r"Error: x/y values \(x:42, y:None\) are required"):
            linux_ds_x11_pointer.move_to(42, None)

        with pytest.raises(PyAutoGUIException, match=r"Error: x/y values \(x:None, y:42\) are required"):
            linux_ds_x11_pointer.move_to(None, 42)

    def test_move_to_handles_large_coords(self, linux_ds_x11_pointer):
        """move_to() handles coordinates larger than screen."""
        linux_ds_x11_pointer.move_to(32767, 32767)
        linux_ds_x11_pointer._display.sync.assert_called_once()

    def test_get_pos_calls_xlib_query_pointer(self, linux_ds_x11_pointer):
        """get_pos() calls XQueryPointer to get current position."""
        linux_ds_x11_pointer._display.mock_set_position(x=150, y=250)

        position = linux_ds_x11_pointer.get_pos()

        assert position == Point(150, 250)
        linux_ds_x11_pointer._display.screen.return_value.root.query_pointer.assert_called_once()


class TestX11PointerPartButtons:
    """Tests for X11 pointer button functions."""

    def test_button_down_left_calls_xlib_with_button_1(self, linux_ds_x11_pointer):
        """button_down('left') calls XTestFakeButtonEvent with button=1."""
        linux_ds_x11_pointer.button_down(ButtonName.LEFT)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 1),
        ])
        linux_ds_x11_pointer._display.sync.assert_called_once()

    def test_button_down_middle_calls_xlib_with_button_2(self, linux_ds_x11_pointer):
        """button_down('middle') calls XTestFakeButtonEvent with button=2."""
        linux_ds_x11_pointer.button_down(ButtonName.MIDDLE)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 2),
        ])
        linux_ds_x11_pointer._display.sync.assert_called_once()

    def test_button_down_right_calls_xlib_with_button_3(self, linux_ds_x11_pointer):
        """button_down('right') calls XTestFakeButtonEvent with button=3."""
        linux_ds_x11_pointer.button_down(ButtonName.RIGHT)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 3),
        ])
        linux_ds_x11_pointer._display.sync.assert_called_once()

    def test_button_up_left_calls_xlib_with_button_1(self, linux_ds_x11_pointer):
        """button_up('left') calls XTestFakeButtonEvent with button=1, is_press=False."""
        linux_ds_x11_pointer.button_up(ButtonName.LEFT)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 1),
        ])
        linux_ds_x11_pointer._display.sync.assert_called_once()

    def test_button_down_invalid_button_raises(self, linux_ds_x11_pointer):
        """button_down() with invalid button name raises exception."""
        with pytest.raises(PyAutoGUIException):  # Adjust to specific exception type
            linux_ds_x11_pointer.button_down("invalid_button")

    def test_button_operations_sequence(self, linux_ds_x11_pointer):
        """Test sequence: button_down -> button_up calls sync twice."""
        linux_ds_x11_pointer.button_down(ButtonName.LEFT)
        linux_ds_x11_pointer.button_up(ButtonName.LEFT)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 1),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 1),
        ])
        assert linux_ds_x11_pointer._display.sync.call_count == 2


class TestX11PointerPartScroll:
    """Tests for X11 pointer scroll functions."""

    def test_scroll_up_calls_xlib_with_button_4(self, linux_ds_x11_pointer):
        """scroll(positive) calls XTestFakeButtonEvent with button=4 (scroll up)."""
        linux_ds_x11_pointer.scroll(dy=3)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            # Click 1
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 4),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 4),
            # Click 2
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 4),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 4),
            # Click 3
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 4),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 4),
        ])
        # Should call sync for each click (down + up per click)
        assert linux_ds_x11_pointer._display.sync.call_count == 3

    def test_scroll_down_calls_xlib_with_button_5(self, linux_ds_x11_pointer):
        """scroll(negative) calls XTestFakeButtonEvent with button=5 (scroll down)."""
        linux_ds_x11_pointer.scroll(dy=-3)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            # Click 1
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 5),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 5),
            # Click 2
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 5),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 5),
            # Click 3
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 5),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 5),
        ])
        assert linux_ds_x11_pointer._display.sync.call_count == 3

    def test_scroll_horizontal_calls_xlib_with_buttons_6(self, linux_ds_x11_pointer):
        """scroll(dx=positive) calls XTestFakeButtonEvent with button=6."""
        linux_ds_x11_pointer.scroll(dx=-2)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            # Click 1
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 6),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 6),
            # Click 2
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 6),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 6),
        ])
        assert linux_ds_x11_pointer._display.sync.call_count == 2

    def test_scroll_horizontal_calls_xlib_with_buttons_7(self, linux_ds_x11_pointer):
        """scroll(dx=positive) calls XTestFakeButtonEvent with button=7."""
        linux_ds_x11_pointer.scroll(dx=2)

        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_has_calls([
            # Click 1
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 7),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 7),
            # Click 2
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonPress, 7),
            call(linux_ds_x11_pointer._display, linux_ds_x11_pointer._xlib.X.ButtonRelease, 7),
        ])
        assert linux_ds_x11_pointer._display.sync.call_count == 2

    def test_scroll_zero_clicks_does_nothing(self, linux_ds_x11_pointer):
        """scroll(0) should not call any X events."""
        linux_ds_x11_pointer.scroll(dy=0)
        linux_ds_x11_pointer._xlib.ext.xtest.fake_input.assert_not_called()
        assert linux_ds_x11_pointer._display.sync.call_count == 0
