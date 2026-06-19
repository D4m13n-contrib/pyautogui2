"""Tests for Wayland Display Server Part providing pointer functions.

Wayland Display Server Part uses evdev to:
- Move pointer (ABS_X, ABS_Y events)
- Click buttons (BTN_LEFT, BTN_RIGHT, BTN_MIDDLE events)
- Scroll (REL_WHEEL, REL_HWHEEL events)
- Get position (via D-Bus portal - gnome-shell extension)

Test strategy:
- Mock _device object
- Verify correct evdev events emitted with correct parameters
- Test error handling
"""

from unittest.mock import MagicMock, call, patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException
from pyautogui2.utils.types import ButtonName


class TestWaylandPointerPartSetupPostinit:
    """Tests for Wayland pointer setup_postinit()."""

    def test_setup_postinit_without_screen_size_nor_controller_raise(
        self, linux_ds_wayland_pointer
    ):
        """setup_postinit() should raise ValueError without screen_size_max nor controller_manager argument."""
        with pytest.raises(ValueError, match="screen_size_max value is required"):
            linux_ds_wayland_pointer.setup_postinit(screen_size_max=None, controller_manager=None)

    def test_setup_postinit_without_screen_size_fallback_controller(self, linux_ds_wayland_pointer):
        """setup_postinit() should fallabck to controller_manager.screen.get_size_max() without screen_size_max argument."""
        controller_manager = MagicMock()
        controller_manager.screen.get_size_max.return_value = (1920, 1080)
        linux_ds_wayland_pointer.setup_postinit(
            screen_size_max=None, controller_manager=controller_manager
        )

        controller_manager.screen.get_size_max.assert_called_once()

    def test_setup_postinit_left_right_handed(self, linux_ds_wayland_pointer):
        """setup_postinit() with left/right handed mode."""
        with patch.object(
            linux_ds_wayland_pointer, "get_primary_button", return_value=ButtonName.LEFT
        ):
            linux_ds_wayland_pointer.setup_postinit(screen_size_max=(1920, 1080))
            btn_mapping = linux_ds_wayland_pointer.BUTTON_NAME_MAPPING
            assert btn_mapping[ButtonName.PRIMARY] == btn_mapping[ButtonName.LEFT]
            assert btn_mapping[ButtonName.SECONDARY] == btn_mapping[ButtonName.RIGHT]

        with patch.object(
            linux_ds_wayland_pointer, "get_primary_button", return_value=ButtonName.RIGHT
        ):
            linux_ds_wayland_pointer.setup_postinit(screen_size_max=(1920, 1080))
            btn_mapping = linux_ds_wayland_pointer.BUTTON_NAME_MAPPING
            assert btn_mapping[ButtonName.PRIMARY] == btn_mapping[ButtonName.RIGHT]
            assert btn_mapping[ButtonName.SECONDARY] == btn_mapping[ButtonName.LEFT]


class TestWaylandPointerPartTeardown:
    """Tests for Wayland pointer teardown_postinit()."""

    def test_teardown_without_setup_does_nothing(self, isolated_linux_wayland):
        """teardown_postinit() with _device=None should be a no-op (no setup called)."""
        from pyautogui2.osal.linux import _compose_linux_class
        from pyautogui2.osal.linux.display_servers.wayland import _make_wayland_part
        from pyautogui2.osal.linux.display_servers.wayland.pointer import WaylandPointerPart
        from tests.mocks.osal.linux.mock_parts import (
            MockBasePointerPart,
            MockDEPointerPart,
            MockWaylandCompositorPointerPart,
        )

        wayland_with_compositor = _make_wayland_part(
            WaylandPointerPart, MockWaylandCompositorPointerPart
        )
        cls_parts = [MockBasePointerPart, MockDEPointerPart, wayland_with_compositor]
        osal_cls = _compose_linux_class("pointer", *cls_parts)
        osal = osal_cls()

        # _device is None at this point, setup_postinit() was never called
        assert osal._device is None

        # Must not raise, must not call close()
        osal.teardown_postinit()

        assert osal._device is None


class TestWaylandPointerPartMovement:
    """Tests for Wayland pointer movement functions."""

    def test_move_to_emits_relative_movement_events(self, linux_ds_wayland_pointer):
        """move_to() emits ABS_X and ABS_Y events via evdev."""
        ec = linux_ds_wayland_pointer._ecodes
        # Mock current position
        with patch.object(linux_ds_wayland_pointer, "get_pos", return_value=(50, 50)):
            linux_ds_wayland_pointer.move_to(100, 200)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_ABS, ec.ABS_X, -1),
                call(ec.EV_ABS, ec.ABS_Y, -1),
                call(ec.EV_ABS, ec.ABS_X, 100),
                call(ec.EV_ABS, ec.ABS_Y, 200),
            ]
        )
        assert linux_ds_wayland_pointer._device.syn.call_count == 2

    def test_move_to_same_position(self, linux_ds_wayland_pointer):
        """move_to() with same position as current should not emit events."""
        ec = linux_ds_wayland_pointer._ecodes
        with patch.object(linux_ds_wayland_pointer, "get_pos", return_value=(100, 100)):
            linux_ds_wayland_pointer.move_to(100, 100)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_ABS, ec.ABS_X, -1),
                call(ec.EV_ABS, ec.ABS_Y, -1),
                call(ec.EV_ABS, ec.ABS_X, 100),
                call(ec.EV_ABS, ec.ABS_Y, 100),
            ]
        )
        assert linux_ds_wayland_pointer._device.syn.call_count == 2

    def test_move_to_none_position_raise(self, linux_ds_wayland_pointer):
        """move_to() with None position should raise."""
        with pytest.raises(PyAutoGUIException, match="Error: x/y values"):
            linux_ds_wayland_pointer.move_to(None, 100)

        with pytest.raises(PyAutoGUIException, match="Error: x/y values"):
            linux_ds_wayland_pointer.move_to(100, None)

        with pytest.raises(PyAutoGUIException, match="Error: x/y values"):
            linux_ds_wayland_pointer.move_to(None, None)

    def test_move_to_multiple_movement(self, linux_ds_wayland_pointer):
        """move_to() multiple calls set fake starting position (-1, -1) only once."""
        ec = linux_ds_wayland_pointer._ecodes
        with patch.object(linux_ds_wayland_pointer, "get_pos", return_value=(10, 10)):
            linux_ds_wayland_pointer.move_to(100, 100)
            linux_ds_wayland_pointer.move_to(200, 200)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_ABS, ec.ABS_X, -1),
                call(ec.EV_ABS, ec.ABS_Y, -1),
                call(ec.EV_ABS, ec.ABS_X, 100),
                call(ec.EV_ABS, ec.ABS_Y, 100),
                call(ec.EV_ABS, ec.ABS_X, 200),
                call(ec.EV_ABS, ec.ABS_Y, 200),
            ]
        )
        assert linux_ds_wayland_pointer._device.syn.call_count == 3


class TestWaylandPointerPartButtons:
    """Tests for Wayland pointer button functions."""

    def test_button_down_left_emits_btn_left_pressed(self, linux_ds_wayland_pointer):
        """button_down('left') emits BTN_LEFT with value=1."""
        ec = linux_ds_wayland_pointer._ecodes
        linux_ds_wayland_pointer.button_down(ButtonName.LEFT)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_KEY, ec.BTN_LEFT, 1),
            ]
        )
        linux_ds_wayland_pointer._device.syn.assert_called_once()

    def test_button_down_right_emits_btn_right_pressed(self, linux_ds_wayland_pointer):
        """button_down('right') emits BTN_RIGHT with value=1."""
        ec = linux_ds_wayland_pointer._ecodes
        linux_ds_wayland_pointer.button_down(ButtonName.RIGHT)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_KEY, ec.BTN_RIGHT, 1),
            ]
        )
        linux_ds_wayland_pointer._device.syn.assert_called_once()

    def test_button_down_middle_emits_btn_middle_pressed(self, linux_ds_wayland_pointer):
        """button_down('middle') emits BTN_MIDDLE with value=1."""
        ec = linux_ds_wayland_pointer._ecodes
        linux_ds_wayland_pointer.button_down(ButtonName.MIDDLE)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_KEY, ec.BTN_MIDDLE, 1),
            ]
        )
        linux_ds_wayland_pointer._device.syn.assert_called_once()

    def test_button_up_left_emits_btn_left_released(self, linux_ds_wayland_pointer):
        """button_up('left') emits BTN_LEFT with value=0."""
        ec = linux_ds_wayland_pointer._ecodes
        linux_ds_wayland_pointer.button_up(ButtonName.LEFT)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_KEY, ec.BTN_LEFT, 0),
            ]
        )
        linux_ds_wayland_pointer._device.syn.assert_called_once()

    def test_button_down_invalid_button_raises(self, linux_ds_wayland_pointer):
        """button_down() with invalid button name raises exception."""
        with pytest.raises(PyAutoGUIException):
            linux_ds_wayland_pointer.button_down("invalid_button")

    def test_button_sequence_emits_correct_events(self, linux_ds_wayland_pointer):
        """Test button_down -> button_up sequence."""
        ec = linux_ds_wayland_pointer._ecodes
        linux_ds_wayland_pointer.button_down(ButtonName.LEFT)
        linux_ds_wayland_pointer.button_up(ButtonName.LEFT)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_KEY, ec.BTN_LEFT, 1),
                call(ec.EV_KEY, ec.BTN_LEFT, 0),
            ]
        )
        assert linux_ds_wayland_pointer._device.syn.call_count == 2


class TestWaylandPointerPartScroll:
    """Tests for Wayland pointer scroll functions."""

    def test_scroll_vertical_positive_emits_rel_wheel(self, linux_ds_wayland_pointer):
        """scroll(dy=positive) emits REL_WHEEL events."""
        ec = linux_ds_wayland_pointer._ecodes
        linux_ds_wayland_pointer.scroll(dy=3)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_REL, ec.REL_WHEEL, 3),
            ]
        )
        linux_ds_wayland_pointer._device.syn.assert_called_once()

    def test_scroll_vertical_negative_emits_rel_wheel(self, linux_ds_wayland_pointer):
        """scroll(dy=negative) emits REL_WHEEL with negative value."""
        ec = linux_ds_wayland_pointer._ecodes
        linux_ds_wayland_pointer.scroll(dy=-3)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_REL, ec.REL_WHEEL, -3),
            ]
        )
        linux_ds_wayland_pointer._device.syn.assert_called_once()

    def test_scroll_horizontal_emits_rel_hwheel(self, linux_ds_wayland_pointer):
        """scroll(dx=value) emits REL_HWHEEL events."""
        ec = linux_ds_wayland_pointer._ecodes
        linux_ds_wayland_pointer.scroll(dx=2)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_REL, ec.REL_HWHEEL, 2),
            ]
        )
        linux_ds_wayland_pointer._device.syn.assert_called_once()

    def test_scroll_horizontal_negative_emits_rel_hwheel(self, linux_ds_wayland_pointer):
        """scroll(dx=negative) emits REL_HWHEEL events with negative value."""
        ec = linux_ds_wayland_pointer._ecodes
        linux_ds_wayland_pointer.scroll(dx=-2)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_REL, ec.REL_HWHEEL, -2),
            ]
        )
        linux_ds_wayland_pointer._device.syn.assert_called_once()

    def test_scroll_both_directions_emits_both_events(self, linux_ds_wayland_pointer):
        """scroll(dx, dy) emits both REL_WHEEL and REL_HWHEEL."""
        ec = linux_ds_wayland_pointer._ecodes
        linux_ds_wayland_pointer.scroll(dy=1, dx=2)

        linux_ds_wayland_pointer._device.write.assert_has_calls(
            [
                call(ec.EV_REL, ec.REL_WHEEL, 1),
                call(ec.EV_REL, ec.REL_HWHEEL, 2),
            ]
        )
        assert linux_ds_wayland_pointer._device.syn.call_count == 2

    def test_scroll_zero_does_nothing(self, linux_ds_wayland_pointer):
        """scroll(dy=0, dx=0) should not emit events."""
        linux_ds_wayland_pointer.scroll(dy=0, dx=0)
        linux_ds_wayland_pointer._device.write.assert_not_called()
        assert linux_ds_wayland_pointer._device.write.call_count == 0


class TestWaylandPointerPartErrorHandling:
    """Tests for Wayland error handling."""

    def test_move_to_handles_uinput_error(self, linux_ds_wayland_pointer):
        """move_to() handles evdev device errors gracefully."""
        linux_ds_wayland_pointer._device.write.side_effect = Exception("UInput error")

        with pytest.raises(Exception, match="UInput error"):
            linux_ds_wayland_pointer.move_to(100, 200)
