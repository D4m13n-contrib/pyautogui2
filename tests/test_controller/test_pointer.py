"""Tests for PointerController."""

from unittest.mock import MagicMock, call, patch

import pytest

from PIL import Image

from pyautogui2.utils.exceptions import ImageNotFoundException, PyAutoGUIException
from pyautogui2.utils.types import ButtonName, Point, Size


class TestPointerMouseInfo:
    """Test mouse_info() method."""

    def test_mouse_info_delegate(self, pointer_controller):
        """Test basic mouse_info delegate."""
        pointer_controller.mouse_info()
        pointer_controller._osal.mouse_info.assert_called_once()


class TestPointerGetPosition:
    """Test get_position() method."""

    def test_get_position_returns_expected(self, pointer_controller):
        """Test basic position retrieval."""
        pointer_controller._osal.mock_set_position(100, 200)

        result = pointer_controller.get_position()
        assert result == (100, 200)
        pointer_controller._osal.get_pos.assert_called_once()

    def test_get_position_returns_point_namedtuple(self, pointer_controller):
        """Test that get_position returns Point namedtuple with x, y attributes."""
        pointer_controller._osal.mock_set_position(150, 250)

        result = pointer_controller.get_position()

        # Should be Point namedtuple
        assert hasattr(result, 'x')
        assert hasattr(result, 'y')
        assert result.x == 150
        assert result.y == 250
        assert result == Point(150, 250)


class TestPointerOnScreen:
    """Test on_screen() method."""

    def test_on_screen_basic(self, pointer_controller):
        """Test basic on_screen() functionality."""
        pointer_controller._screen_controller._osal.get_size_max.side_effect = lambda: Size(1920, 1080)

        # Normal cases
        assert pointer_controller.on_screen(10, 10) is True

        # Edge cases
        assert pointer_controller.on_screen(0, 0) is True
        assert pointer_controller.on_screen(1920 - 1, 1080 - 1) is True

        # Out of bounds cases
        assert pointer_controller.on_screen(-1, -1) is False
        assert pointer_controller.on_screen(1920, 1080) is False
        assert pointer_controller.on_screen(1920 + 1, 1080 + 1) is False


class TestPointerMoveTo:
    """Test move_to() absolute positioning."""

    def test_move_to_calls_osal_and_updates_position(self, pointer_controller):
        """Test basic move_to() functionality."""
        pointer_controller.move_to(400, 300)
        pointer_controller._osal.move_to.assert_called_with(400, 300)
        assert pointer_controller.get_position() == Point(400, 300)

    def test_move_to_with_tuple(self, pointer_controller):
        """Test move_to() with tuple coordinates."""
        pointer_controller.move_to((500, 600))
        pointer_controller._osal.move_to.assert_called_with(500, 600)

    def test_move_to_with_point(self, pointer_controller):
        """Test move_to() with Point namedtuple."""
        point = Point(700, 800)
        pointer_controller.move_to(point)
        pointer_controller._osal.move_to.assert_called_with(700, 800)

    def test_move_to_with_duration_calls_tweening(self, pointer_controller):
        """Test move_to() with duration uses tweening."""
        with patch('time.sleep') as mock_sleep, \
             patch('pyautogui2.controllers.pointer.time.time', side_effect=[0, 0.1, 0.2, 0.3, 0.5]):

            pointer_controller._osal.mock_set_position(0, 0)
            pointer_controller.move_to(100, 100, duration=0.5)

            # Should have called sleep multiple times for animation
            assert mock_sleep.call_count > 0
            # Final position should be target
            final_call = pointer_controller._osal.move_to.call_args_list[-1]
            assert final_call == call(100, 100)

    def test_move_to_with_tween_function(self, pointer_controller):
        """Test move_to() with tween function."""
        with patch('time.sleep'):
            pointer_controller._osal.mock_set_position(0, 0)
            pointer_controller.move_to(100, 100, duration=0.1, tween="easeInQuad")

            # Should reach target
            assert pointer_controller.get_position() == Point(100, 100)

    def test_move_to_negative_duration_raises(self, pointer_controller):
        """Test that negative duration raises an error."""
        with pytest.raises(PyAutoGUIException, match="duration must be non-negative"):
            pointer_controller.move_to(100, 100, duration=-1)

    def test_move_to_zero_duration_is_instant(self, pointer_controller):
        """Test that duration=0 moves instantly without tweening but with MINIMUM_SLEEP."""
        with patch('time.sleep') as mock_sleep:
            pointer_controller.move_to(100, 100, duration=0)

            # Should sleep once (at the end of movment) for instant move
            mock_sleep.assert_called_once_with(pointer_controller.MINIMUM_SLEEP)
            pointer_controller._osal.move_to.assert_called_once_with(100, 100)

    def test_move_to_no_sleep_is_instant(self, pointer_controller):
        """Test that duration=0 and MINIMUM_SLEEP=0 too moves instantly without tweening."""
        pointer_controller.MINIMUM_SLEEP = 0.0

        with patch('time.sleep') as mock_sleep:
            pointer_controller.move_to(200, 200, duration=0)

            mock_sleep.assert_not_called()
            pointer_controller._osal.move_to.assert_called_once_with(200, 200)

    def test_move_to_not_efficient_raise(self, pointer_controller):
        """Test that non efficient move should raise PyAutoGUIException."""
        pointer_controller._osal.move_to.side_effect = lambda *_a: None
        with pytest.raises(PyAutoGUIException, match=r"Error: failed to move from Point\(x=10, y=10\) to Point\(x=100, y=100\), reached Point\(x=10, y=10\)."):
            pointer_controller.move_to(100, 100)


class TestPointerMoveRel:
    """Test move_rel() relative positioning."""

    def test_move_rel_adds_to_current_position(self, pointer_controller):
        """Test basic relative movement."""
        pointer_controller._osal.mock_set_position(100, 100)

        pointer_controller.move_rel(50, 30)

        # Should move to (150, 130)
        pointer_controller._osal.move_to.assert_called_with(150, 130)
        assert pointer_controller.get_position() == Point(150, 130)

    def test_move_rel_negative_values(self, pointer_controller):
        """Test relative movement with negative offsets."""
        pointer_controller._osal.mock_set_position(200, 200)

        pointer_controller.move_rel(-50, -100)

        # Should move to (150, 100)
        pointer_controller._osal.move_to.assert_called_with(150, 100)

    def test_move_rel_with_tuple(self, pointer_controller):
        """Test move_rel() with tuple offset."""
        pointer_controller._osal.mock_set_position(100, 100)

        pointer_controller.move_rel((20, 30))

        pointer_controller._osal.move_to.assert_called_with(120, 130)

    def test_move_rel_with_duration(self, pointer_controller):
        """Test relative movement with animation."""
        with patch('time.sleep'):
            pointer_controller._osal.mock_set_position(0, 0)

            pointer_controller.move_rel(100, 100, duration=0.1)

            # Should reach target (0+100, 0+100)
            assert pointer_controller.get_position() == Point(100, 100)

    def test_move_rel_zero_offset_does_nothing(self, pointer_controller):
        """Test that move_rel(0, 0) doesn't move."""
        pointer_controller._osal.mock_set_position(50, 50)

        pointer_controller.move_rel(0, 0)

        # Position should be unchanged
        assert pointer_controller.get_position() == Point(50, 50)


class TestPointerClick:
    """Test click() method with various parameters."""

    def test_click_with_invalid_clicks_raises(self, pointer_controller):
        """Test that clicks=0 raises an error."""
        with pytest.raises(PyAutoGUIException):
            pointer_controller.click(clicks=0)

    def test_click_calls_down_up_pair(self, pointer_controller):
        """Test basic click calls button_down and button_up."""
        pointer_controller.click(10, 20, button="left", clicks=2)

        pointer_controller._osal.mocks.assert_has_calls([
            call.get_pos(),
            call.move_to(10, 20),
            call.get_pos(),
            call.button_down(ButtonName.LEFT),
            call.button_up(ButtonName.LEFT),
            call.get_pos(),
            call.button_down(ButtonName.LEFT),
            call.button_up(ButtonName.LEFT),
        ])

    def test_click_negative_clicks_raises(self, pointer_controller):
        """Test that negative clicks raise an error."""
        with pytest.raises(PyAutoGUIException, match="clicks value must be >= 1"):
            pointer_controller.click(clicks=-1)

    def test_click_negative_interval_raises(self, pointer_controller):
        """Test that negative interval raises an error."""
        with pytest.raises(PyAutoGUIException, match="interval must be non-negative"):
            pointer_controller.click(interval=-0.1)

    def test_click_different_buttons(self, pointer_controller):
        """Test clicking with different mouse buttons."""
        # Left button
        pointer_controller.click(button="left")
        pointer_controller._osal.button_down.assert_called_with(ButtonName.LEFT)

        pointer_controller._osal.button_down.reset_mock()

        # Right button
        pointer_controller.click(button="right")
        pointer_controller._osal.button_down.assert_called_with(ButtonName.RIGHT)

        pointer_controller._osal.button_down.reset_mock()

        # Middle button
        pointer_controller.click(button="middle")
        pointer_controller._osal.button_down.assert_called_with(ButtonName.MIDDLE)

    def test_click_with_interval(self, pointer_controller):
        """Test clicking with interval between clicks."""
        with patch('time.sleep') as mock_sleep:
            pointer_controller.click(clicks=3, interval=0.1)

            # Should sleep between clicks (2 sleeps for 3 clicks)
            assert mock_sleep.call_count == 2
            mock_sleep.assert_called_with(0.1)

    def test_click_without_coordinates_uses_current_position(self, pointer_controller):
        """Test that click() without coordinates doesn't move."""
        pointer_controller._osal.mock_set_position(100, 100)

        pointer_controller.click()

        # Should not call move_to
        pointer_controller._osal.move_to.assert_not_called()
        # But should click
        pointer_controller._osal.button_down.assert_called()
        pointer_controller._osal.button_up.assert_called()

    def test_click_with_duration_moves_with_animation(self, pointer_controller):
        """Test click with duration animates movement."""
        with patch('time.sleep'):
            pointer_controller._osal.mock_set_position(0, 0)

            pointer_controller.click(100, 100, duration=0.1)

            # Should move to target
            assert pointer_controller.get_position() == Point(100, 100)
            # And should click
            pointer_controller._osal.button_down.assert_called()


class TestPointerDoubleClick:
    """Test double_click() convenience method."""

    def test_double_click_calls_click_twice(self, pointer_controller):
        """Test that double_click calls click with clicks=2."""
        pointer_controller.double_click(50, 50)

        # Should have 2 down/up pairs
        assert pointer_controller._osal.button_down.call_count == 2
        assert pointer_controller._osal.button_up.call_count == 2

    def test_double_click_with_interval(self, pointer_controller):
        """Test double_click with custom interval."""
        with patch('time.sleep') as mock_sleep:
            pointer_controller.double_click(interval=0.2)

            # Should sleep once between the 2 clicks
            mock_sleep.assert_called_with(0.2)


class TestPointerTripleClick:
    """Test triple_click() convenience method."""

    def test_triple_click_calls_click_three_times(self, pointer_controller):
        """Test that triple_click calls click with clicks=3."""
        pointer_controller.triple_click(100, 100)

        # Should have 3 down/up pairs
        assert pointer_controller._osal.button_down.call_count == 3
        assert pointer_controller._osal.button_up.call_count == 3


class TestPointerLeftClick:
    """Test left_click() convenience method."""

    def test_left_click_uses_left_button(self, pointer_controller):
        """Test that left_click uses LEFT button."""
        pointer_controller.left_click(200, 200)

        pointer_controller._osal.button_down.assert_called_with(ButtonName.LEFT)
        pointer_controller._osal.button_up.assert_called_with(ButtonName.LEFT)

    def test_left_click_single_click(self, pointer_controller):
        """Test that left_click does single click."""
        pointer_controller.left_click()

        # Should have 1 down/up pair
        assert pointer_controller._osal.button_down.call_count == 1
        assert pointer_controller._osal.button_up.call_count == 1


class TestPointerRightClick:
    """Test right_click() convenience method."""

    def test_right_click_uses_right_button(self, pointer_controller):
        """Test that right_click uses RIGHT button."""
        pointer_controller.right_click(200, 200)

        pointer_controller._osal.button_down.assert_called_with(ButtonName.RIGHT)
        pointer_controller._osal.button_up.assert_called_with(ButtonName.RIGHT)

    def test_right_click_single_click(self, pointer_controller):
        """Test that right_click does single click."""
        pointer_controller.right_click()

        # Should have 1 down/up pair
        assert pointer_controller._osal.button_down.call_count == 1
        assert pointer_controller._osal.button_up.call_count == 1


class TestPointerMiddleClick:
    """Test middle_click() convenience method."""

    def test_middle_click_uses_middle_button(self, pointer_controller):
        """Test that middle_click uses MIDDLE button."""
        pointer_controller.middle_click(300, 300)

        pointer_controller._osal.button_down.assert_called_with(ButtonName.MIDDLE)
        pointer_controller._osal.button_up.assert_called_with(ButtonName.MIDDLE)


class TestPointerButtonDownUp:
    """Test low-level button_down() and button_up() methods."""

    def test_button_down_delegates_to_osal(self, pointer_controller):
        """Test button_down calls OSAL."""
        pointer_controller.button_down(button="left")

        pointer_controller._osal.button_down.assert_called_once_with(ButtonName.LEFT)

    def test_button_up_delegates_to_osal(self, pointer_controller):
        """Test button_up calls OSAL."""
        pointer_controller.button_up(button="right")

        pointer_controller._osal.button_up.assert_called_once_with(ButtonName.RIGHT)

    def test_button_down_all_buttons(self, pointer_controller):
        """Test button_down with all button types."""
        for button_name in ["left", "right", "middle"]:
            pointer_controller._osal.button_down.reset_mock()
            pointer_controller.button_down(button=button_name)

            expected_button = getattr(ButtonName, button_name.upper())
            pointer_controller._osal.button_down.assert_called_with(expected_button)

    def test_button_invalid_name_raises(self, pointer_controller):
        """Test invalid button name raises error."""
        with pytest.raises(PyAutoGUIException, match="Invalid button: 'invalid_button'"):
            pointer_controller.button_down(button="invalid_button")


class TestPointerDragTo:
    """Test drag_to() method (click, move, release)."""

    def test_drag_to_holds_button_while_moving(self, pointer_controller):
        """Test drag_to holds button down during movement."""
        pointer_controller._osal.mock_set_position(0, 0)

        pointer_controller.drag_to(100, 100, button="left")

        # Should: button_down -> move_to -> button_up
        pointer_controller._osal.mocks.assert_has_calls([
            call.button_down(ButtonName.LEFT),
            call.get_pos(),
            call.drag_to(100, 100, ButtonName.LEFT),
            call.get_pos(),
            call.button_up(ButtonName.LEFT),
        ])

    def test_drag_to_with_different_buttons(self, pointer_controller):
        """Test dragging with different mouse buttons."""
        # Right button drag
        pointer_controller.drag_to(50, 50, button="right")
        pointer_controller._osal.button_down.assert_called_with(ButtonName.RIGHT)

        pointer_controller._osal.button_down.reset_mock()

        # Middle button drag
        pointer_controller.drag_to(50, 50, button="middle")
        pointer_controller._osal.button_down.assert_called_with(ButtonName.MIDDLE)

    def test_drag_to_with_duration(self, pointer_controller):
        """Test drag with animated movement."""
        with patch('time.sleep'):
            pointer_controller._osal.mock_set_position(0, 0)

            pointer_controller.drag_to(200, 200, duration=0.2)

            # Should animate to target
            assert pointer_controller.get_position() == Point(200, 200)
            # Button should be held during drag
            pointer_controller._osal.button_down.assert_called()
            pointer_controller._osal.button_up.assert_called()

    def test_drag_to_releases_button_on_exception(self, pointer_controller):
        """Test that button is released even if move fails."""
        pointer_controller._osal.drag_to.side_effect = RuntimeError("Drag failed")

        with pytest.raises(RuntimeError):
            pointer_controller.drag_to(100, 100)

        # Should still call button_up
        pointer_controller._osal.button_down.assert_called()
        pointer_controller._osal.button_up.assert_called()


class TestPointerDragRel:
    """Test drag_rel() relative dragging."""

    def test_drag_rel_adds_to_current_position(self, pointer_controller):
        """Test drag_rel moves relative to current position."""
        pointer_controller._osal.mock_set_position(50, 50)

        pointer_controller.drag_rel(100, 100)

        # Should drag to (150, 150)
        pointer_controller._osal.drag_to.assert_called_with(150, 150, ButtonName.PRIMARY)

    def test_drag_rel_holds_button(self, pointer_controller):
        """Test drag_rel holds button during drag."""
        pointer_controller._osal.mock_set_position(100, 100)

        pointer_controller.drag_rel(50, 50, button="left")

        pointer_controller._osal.mocks.assert_has_calls([
            call.button_down(ButtonName.LEFT),
            call.get_pos(),
            call.drag_to(150, 150, ButtonName.LEFT),
            call.get_pos(),
            call.button_up(ButtonName.LEFT),
        ])

    def test_drag_rel_negative_offset(self, pointer_controller):
        """Test dragging with negative relative offset."""
        pointer_controller._osal.mock_set_position(100, 100)

        pointer_controller.drag_rel(-50, -50)

        pointer_controller._osal.drag_to.assert_called_with(50, 50, ButtonName.PRIMARY)

    def test_drag_rel_tuple_list_offset(self, pointer_controller):
        """Test dragging with tuple/list offset."""
        pointer_controller._osal.mock_set_position(100, 100)

        pointer_controller.drag_rel((10, 10))
        pointer_controller._osal.drag_to.assert_called_with(110, 110, ButtonName.PRIMARY)

        pointer_controller.drag_rel([10, 10])
        pointer_controller._osal.drag_to.assert_called_with(120, 120, ButtonName.PRIMARY)


class TestPointerScroll:
    """Test scroll() methods."""

    def test_scroll_variants_delegate(self, pointer_controller):
        """Test basic scroll delegation."""
        pointer_controller.scroll(clicks=10, x=20, y=30)
        pointer_controller._osal.move_to.assert_called_with(20, 30)
        pointer_controller._osal.scroll.assert_called_with(dy=10)

        pointer_controller.hscroll(40)
        pointer_controller._osal.scroll.assert_called_with(dx=40)

        pointer_controller.vscroll(50)
        pointer_controller._osal.scroll.assert_called_with(dy=50)

    def test_scroll_vertical_positive(self, pointer_controller):
        """Test scrolling up (positive)."""
        pointer_controller.scroll(clicks=5)

        pointer_controller._osal.scroll.assert_called_with(dy=5)

    def test_scroll_vertical_negative(self, pointer_controller):
        """Test scrolling down (negative)."""
        pointer_controller.scroll(clicks=-5)

        pointer_controller._osal.scroll.assert_called_with(dy=-5)

    def test_scroll_at_position(self, pointer_controller):
        """Test scrolling at specific position."""
        pointer_controller.scroll(clicks=3, x=100, y=200)

        # Should move to position first
        pointer_controller._osal.move_to.assert_called_with(100, 200)
        # Then scroll
        pointer_controller._osal.scroll.assert_called_with(dy=3)

    def test_scroll_without_position_uses_current(self, pointer_controller):
        """Test scrolling without coordinates doesn't move."""
        pointer_controller._osal.mock_set_position(50, 50)

        pointer_controller.scroll(clicks=5)

        # Should not move
        pointer_controller._osal.move_to.assert_not_called()
        # But should scroll
        pointer_controller._osal.scroll.assert_called()

    def test_hscroll_horizontal_only(self, pointer_controller):
        """Test horizontal scroll (hscroll)."""
        pointer_controller.hscroll(clicks=10)

        # Should scroll horizontally only
        pointer_controller._osal.scroll.assert_called_with(dx=10)

    def test_vscroll_vertical_only(self, pointer_controller):
        """Test vertical scroll (vscroll)."""
        pointer_controller.vscroll(clicks=-10)

        # Should scroll vertically only
        pointer_controller._osal.scroll.assert_called_with(dy=-10)

    def test_scroll_zero_clicks_does_nothing(self, pointer_controller):
        """Test that scroll(0) does nothing."""
        pointer_controller.scroll(clicks=0)
        pointer_controller._osal.scroll.assert_not_called()

    def test_hscroll_zero_clicks_does_nothing(self, pointer_controller):
        """Test that hscroll(0) does nothing."""
        pointer_controller.hscroll(clicks=0)
        pointer_controller._osal.scroll.assert_not_called()

    def test_vscroll_zero_clicks_does_nothing(self, pointer_controller):
        """Test that vscroll(0) does nothing."""
        pointer_controller.vscroll(clicks=0)
        pointer_controller._osal.scroll.assert_not_called()


class TestNormalizeCoords:
    """Unit tests for PointerController._normalize_coords() singledispatch.

    This method is the entry point for all coordinate-accepting functions,
    so comprehensive testing is critical.
    """

    def test_normalize_coords_int_int(self, pointer_controller):
        """Test separate x, y integers."""
        result = pointer_controller._normalize_coords(10, 20)
        assert result == (10, 20)

    def test_normalize_coords_tuple_2(self, pointer_controller):
        """Test 2-tuple (x, y)."""
        result = pointer_controller._normalize_coords((100, 200))
        assert result == (100, 200)

    def test_normalize_coords_tuple_4_center(self, pointer_controller):
        """Test 4-tuple (x, y, w, h) returns center point."""
        result = pointer_controller._normalize_coords((10, 20, 100, 50))
        # Center: (10 + 100/2, 20 + 50/2) = (60, 45)
        assert result == (60, 45)

    def test_normalize_coords_point_namedtuple(self, pointer_controller):
        """Test Point namedtuple."""
        result = pointer_controller._normalize_coords(Point(150, 175))
        assert result == (150, 175)

    def test_normalize_coords_coords_namedtuple(self, pointer_controller):
        """Test Coords namedtuple (internal type)."""
        from pyautogui2.controllers.pointer import Coords
        result = pointer_controller._normalize_coords(Coords(200, 250))
        assert result == (200, 250)

    def test_normalize_coords_invalid_type_raises(self, pointer_controller):
        """Test invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Unsupported type for coords: <class 'list'>"):
            pointer_controller._normalize_coords([10, 20])  # List not supported

        with pytest.raises(TypeError, match="Unsupported type for coords: <class 'dict'>"):
            pointer_controller._normalize_coords({"x": 10, "y": 20})  # Dict not supported

    def test_normalize_coords_invalid_tuple_length_raises(self, pointer_controller):
        """Test tuple with wrong number of elements raises ValueError."""
        msg = r"Expected 2-tuple \(x, y\) or 4-tuple \(x, y, w, h\), got %d elements"
        with pytest.raises(ValueError, match=msg % (1, )):
            pointer_controller._normalize_coords((10,))  # 1 element

        with pytest.raises(ValueError, match=msg % (3, )):
            pointer_controller._normalize_coords((10, 20, 30))  # 3 elements

        with pytest.raises(ValueError, match=msg % (5, )):
            pointer_controller._normalize_coords((10, 20, 30, 40, 50))  # 5 elements

    def test_normalize_coords_single_arg_vs_two_args(self, pointer_controller):
        """Test dispatcher handles both call styles correctly."""
        # Two separate args: x=10, y=20
        result1 = pointer_controller._normalize_coords(10, 20)

        # Single tuple arg: (10, 20)
        result2 = pointer_controller._normalize_coords((10, 20))

        assert result1 == result2 == (10, 20)

    @pytest.mark.parametrize("coords, expected_result", [
        ((None, None, None), (123, 456)),
        ((None, 98, None), (98, 456)),
        ((None, None, 76), (123, 76)),
    ], ids=["XY-None", "Y-None", "X-None"])
    def test_normalize_coords_none_uses_current_position(self, coords, expected_result, pointer_controller):
        """Test that None returns current position."""
        pointer_controller._osal.mock_set_position(123, 456)

        result = pointer_controller._normalize_coords(*coords)

        assert result == expected_result

    def test_normalize_coords_float_values_are_rounded(self, pointer_controller):
        """Test that float coordinates are properly handled."""
        result = pointer_controller._normalize_coords(10.7, 20.3)

        # Should convert to int (exact behavior depends on implementation)
        assert isinstance(result[0], int)
        assert isinstance(result[1], int)

    def test_normalize_coords_negative_coordinates(self, pointer_controller):
        """Test negative coordinates are accepted."""
        result = pointer_controller._normalize_coords(-10, -20)

        assert result == (-10, -20)

    def test_normalize_coords_image_string(self, pointer_controller):
        """Test image path string."""
        pointer_controller._screen_controller._osal.locate_center_on_screen.return_value = Point(50, 60)

        result = pointer_controller._normalize_coords("test_icon.png")

        pointer_controller._screen_controller._osal.locate_center_on_screen.asssert_called_once_with("test_icon.png")
        assert result == (50, 60)

    def test_normalize_coords_pathlib_path(self, pointer_controller):
        """Test pathlib.Path for image files."""
        from pathlib import Path
        pointer_controller._screen_controller._osal.locate_center_on_screen.return_value = Point(90, 110)

        image_path = Path("test_image.png")
        result = pointer_controller._normalize_coords(image_path)

        pointer_controller._screen_controller._osal.locate_center_on_screen.asssert_called_once_with(image_path)
        assert result == (90, 110)

    def test_normalize_coords_pil_image(self, pointer_controller):
        """Test PIL Image object."""
        pointer_controller._screen_controller._osal.locate_center_on_screen.return_value = Point(75, 85)

        # Create fake PIL Image
        fake_image = Image.new('RGB', (10, 10))

        result = pointer_controller._normalize_coords(fake_image)

        pointer_controller._screen_controller._osal.locate_center_on_screen.asssert_called_once_with(fake_image)
        assert result == (75, 85)

    def test_normalize_coords_raise_image_not_found(self, pointer_controller):
        """Test raise image not found exception."""
        pointer_controller._screen_controller._osal.locate_center_on_screen.return_value = None

        with pytest.raises(ImageNotFoundException):
            _ = pointer_controller._normalize_coords("test_img_not_found.png")

        pointer_controller._screen_controller._osal.locate_center_on_screen.asssert_called_once_with("test_img_not_found.png")


class TestPointerControllerInitialization:
    """Test PointerController initialization."""

    def test_init_with_bad_backend_raises(self):
        """Test initialization with bad backend should raises."""
        from pyautogui2.controllers.pointer import PointerController

        mock_backend = MagicMock()  # not AbstractPointer subclass
        with pytest.raises(PyAutoGUIException):
            PointerController(osal=mock_backend)

    def test_init_with_explicit_backends(self):
        """Test initialization with explicit pointer backends."""
        from pyautogui2.controllers.pointer import PointerController
        from pyautogui2.osal.abstract_cls import AbstractPointer

        mock_backend = MagicMock(spec_set=AbstractPointer)
        pc = PointerController(osal=mock_backend)
        assert pc._osal is mock_backend


class TestPointerBackendErrors:
    """Test error handling when backend fails."""

    def test_move_to_backend_error(self, pointer_controller):
        """Test handling backend errors in move_to()."""
        pointer_controller._osal.move_to.side_effect = RuntimeError("Backend error")

        with pytest.raises(RuntimeError, match="Backend error"):
            pointer_controller.move_to(100, 100)

    def test_get_position_backend_error(self, pointer_controller):
        """Test handling backend errors in get_position()."""
        pointer_controller._osal.get_pos.side_effect = RuntimeError("Position error")

        with pytest.raises(RuntimeError, match="Position error"):
            pointer_controller.get_position()

    def test_click_backend_error_in_button_down(self, pointer_controller):
        """Test handling backend errors during button_down."""
        pointer_controller._osal.button_down.side_effect = RuntimeError("Click failed")

        with pytest.raises(RuntimeError, match="Click failed"):
            pointer_controller.click()

    def test_scroll_backend_error(self, pointer_controller):
        """Test handling backend errors in scroll()."""
        pointer_controller._osal.scroll.side_effect = RuntimeError("Scroll error")

        with pytest.raises(RuntimeError, match="Scroll error"):
            pointer_controller.scroll(10)


class TestPointerTweening:
    """Test tweening/animation with duration parameter."""

    def test_all_tween_functions_work(self, pointer_controller):
        """Test that all built-in tween functions work."""
        tween_functions = [
            "linear",
            "easeInQuad",
            "easeOutQuad",
            "easeInOutQuad",
            "easeInCubic",
            "easeOutCubic",
            "easeInOutCubic",
        ]

        with patch('time.sleep'):
            for tween_func in tween_functions:
                pointer_controller._osal.mock_set_position(0, 0)
                pointer_controller._osal.move_to.reset_mock()
                pointer_controller.move_to(100, 100, duration=0.05, tween=tween_func)

                # Should complete movement
                assert pointer_controller.get_position() == Point(100, 100)

    def test_invalid_tween_function_raises(self, pointer_controller):
        """Test that invalid tween function raises error."""
        with pytest.raises(PyAutoGUIException, match="Unknown tweening name"):
            pointer_controller.move_to(100, 100, duration=0.1, tween="invalid")

    def test_tween_reaches_intermediate_positions(self, pointer_controller):
        """Test that tweening actually creates intermediate positions."""
        with patch('time.sleep'):
            pointer_controller._osal.mock_set_position(0, 0)

            # Use a long duration to ensure multiple steps
            pointer_controller.move_to(1000, 1000, duration=1.0)

            # Should have called move_to multiple times
            call_count = pointer_controller._osal.move_to.call_count
            assert call_count > 2, "Should have intermediate positions"

            # Last call should be final position
            last_call = pointer_controller._osal.move_to.call_args_list[-1]
            assert last_call == call(1000, 1000)


class TestPointerEdgeCases:
    """Test various edge cases and corner scenarios."""

    def test_move_to_same_position(self, pointer_controller):
        """Test moving to current position."""
        pointer_controller._osal.mock_set_position(100, 100)

        pointer_controller.move_to(100, 100)

        # Should not call move_to
        pointer_controller._osal.move_to.assert_not_called()

    def test_move_rel_zero_offset(self, pointer_controller):
        """Test relative move with (0, 0) offset."""
        pointer_controller._osal.mock_set_position(50, 50)

        pointer_controller.move_rel(0, 0)

        # Position should be unchanged
        pointer_controller._osal.move_to.assert_not_called()
        assert pointer_controller.get_position() == Point(50, 50)

    def test_click_at_screen_edges(self, pointer_controller):
        """Test clicking at screen boundaries."""
        pointer_controller._osal.mock_set_position(50, 50)

        # Top-left corner
        pointer_controller.click(0, 0)
        pointer_controller._osal.move_to.assert_called_with(0, 0)

        # Large coordinates (bottom-right)
        pointer_controller.click(9999, 9999)
        w, h = pointer_controller._screen_controller.get_size_max()
        pointer_controller._osal.move_to.assert_called_with(w - 1, h - 1)

    def test_multiple_operations_in_sequence(self, pointer_controller):
        """Test multiple operations work correctly in sequence."""
        pointer_controller.move_to(100, 100)
        pointer_controller.click()
        pointer_controller.move_rel(50, 50)
        pointer_controller.double_click()
        pointer_controller.scroll(5)

        # Verify all operations completed without errors
        assert pointer_controller._osal.move_to.call_count > 0
        assert pointer_controller._osal.button_down.call_count > 0
        assert pointer_controller._osal.scroll.call_count > 0

    def test_rapid_successive_moves(self, pointer_controller):
        """Test rapid successive movements don't accumulate errors."""
        positions = [(10, 10), (20, 20), (30, 30), (40, 40), (50, 50)]

        for x, y in positions:
            pointer_controller.move_to(x, y)

        # Final position should be last target
        assert pointer_controller.get_position() == Point(50, 50)

    def test_alternating_button_clicks(self, pointer_controller):
        """Test alternating between different mouse buttons."""
        pointer_controller.click()
        pointer_controller.click(button="left")
        pointer_controller.click(button="right")
        pointer_controller.click(button="middle")
        pointer_controller.click(button="primary")
        pointer_controller.click(button="secondary")

        pointer_controller._osal.button_down.assert_has_calls([
            call(ButtonName.PRIMARY),
            call(ButtonName.LEFT),
            call(ButtonName.RIGHT),
            call(ButtonName.MIDDLE),
            call(ButtonName.PRIMARY),
            call(ButtonName.SECONDARY),
        ])


class TestPointerRepresentation:
    """Test string representations for debugging."""

    def test_repr_contains_class_name(self, pointer_controller):
        """Test that __repr__ contains class name."""
        rep = repr(pointer_controller)
        assert "PointerController" in rep

    def test_str_is_readable(self, pointer_controller):
        """Test that __str__ provides readable output."""
        string = str(pointer_controller)
        assert len(string) > 0
        # Should mention pointer or controller
        assert "pointer" in string.lower() or "controller" in string.lower()


class TestPointerScreenIntegration:
    """Test integration between PointerController and ScreenController."""

    def test_move_to_image_uses_screen_locate(self, pointer_controller):
        """Test that moving to image uses screen controller's locate."""
        mock_locate_called = False

        def mock_locate(image, **kwargs):
            nonlocal mock_locate_called
            mock_locate_called = True
            return Point(200, 300)

        screen_ctrl = pointer_controller._screen_controller
        with patch.object(screen_ctrl, "locate_center_on_screen", mock_locate):
            pointer_controller.move_to("icon.png")

        assert mock_locate_called
        assert pointer_controller.get_position() == Point(200, 300)

    def test_click_on_image_locates_and_clicks(self, pointer_controller):
        """Test clicking on image first locates it."""
        def mock_locate(image, **kwargs):
            return Point(150, 250)

        screen_ctrl = pointer_controller._screen_controller
        with patch.object(screen_ctrl, "locate_center_on_screen", mock_locate):
            pointer_controller.click("button.png")

        # Should move to image location and click
        pointer_controller._osal.move_to.assert_called_with(150, 250)
        pointer_controller._osal.button_down.assert_called()

    def test_image_not_found_raises(self, pointer_controller, monkeypatch):
        """Test that image not found raises appropriate error."""
        def mock_locate(image, **kwargs):
            raise PyAutoGUIException(f"Could not locate image: {image}")

        screen_ctrl = pointer_controller._screen_controller
        with patch.object(screen_ctrl, "locate_center_on_screen", mock_locate), \
             pytest.raises(PyAutoGUIException, match="Could not locate image"):
            pointer_controller.move_to("nonexistent.png")
